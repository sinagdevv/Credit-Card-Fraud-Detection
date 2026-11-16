"""Day-by-day transaction simulation (spec 5.6-5.10, Eq 18 authorization only; 7.2 beta0; 10 steps 5-10).

Every model value comes from the config. Per day: states transition, opportunities are generated with NumPy
(vectorized), then a plain loop over compact per-card state computes the strictly-earlier features, p_k,
Y_true, retain/discard and authorization. Timestamps are naive local (Asia/Manila) wall-clock times.
"""
from __future__ import annotations

import copy
import hashlib
import math
from collections import deque

import numpy as np
import pandas as pd

from .entities import _draw
from .export import ALLOWLIST
from .validate import SD_DDOF

PILOT_ITERS = 2  # computational setting (not a model value): pilot->bisection refinements
_BIG = 1 << 40
_DAY = 86400


def _pv(cfg, name):
    return cfg["parameters"][name]["value"]


def _logit(x):
    return np.log(x / (1 - x))


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def _unique_secs(card, sec):
    """Order by (card, sec, arrival) and push colliding seconds forward by 1 s so (card, sec) is unique."""
    n = len(card)
    order = np.lexsort((np.arange(n), sec, card))
    c, s = card[order], sec[order]
    g = np.cumsum(np.r_[True, c[1:] != c[:-1]]) - 1
    i = np.arange(n)
    t = np.maximum.accumulate(s - i + g * _BIG) - g * _BIG + i
    return order, t


def _prepare(cfg, ent, rng):
    sim = cfg["simulation"]
    V = cfg["vocabularies"]
    H, C, M = ent["cardholders"], ent["cards"], ent["merchants"]
    nh, nm = len(H), len(M)
    cats = list(V["merchant_category"]["mcc"])
    chans = V["channel"]["values"]
    start = np.datetime64(sim["start_date"], "D")
    ndays = int((np.datetime64(sim["end_date"], "D") - start) / np.timedelta64(1, "D")) + 1
    h_of_card = pd.Index(H["cardholder_id"]).get_indexer(C["cardholder_id"])
    kmax = int(np.bincount(h_of_card).max())
    cm = np.full((nh, kmax), -1)
    slot = np.zeros(nh, int)
    for ci, hi in enumerate(h_of_card):               # one pass over cards (<= ~4 per holder)
        cm[hi, slot[hi]] = ci
        slot[hi] += 1
    exp_day = ((C["expiry_date"].to_numpy().astype("datetime64[D]") - start) / np.timedelta64(1, "D")).astype(int)
    cat_i = {k: i for i, k in enumerate(cats)}
    m_cat = M["merchant_category"].map(cat_i).to_numpy()
    m_ctry = M["country_code"].to_numpy()
    m_foreign = m_ctry != "PH"
    m_online = M["online_capable"].to_numpy(bool)
    # per-(holder, merchant) distance D_im from tier gamma (Eq 11); persistent pair property
    dt = _pv(cfg, "merchant_distance_by_tier")
    home = H["home_region"].to_numpy()
    near = (M["merchant_region"].to_numpy()[None, :] == home[:, None]) & ~m_foreign[None, :]
    tier = np.where(m_foreign[None, :], 2, np.where(near, 0, 1))
    D = np.empty((nh, nm), np.float32)
    for t, key in enumerate(("near", "far", "foreign")):
        s = tier == t
        D[s] = rng.gamma(dt[key]["shape_k"], dt[key]["mean_km"] / dt[key]["shape_k"], int(s.sum()))
    # candidate merchant sets: (category, foreign pool, online-restricted)
    cand = {(c, f, o): np.flatnonzero((m_cat == c) & (m_foreign == bool(f)) & (m_online if o else True))
            for c in range(len(cats)) for f in (0, 1) for o in (0, 1)}
    if any(not len(cand[(c, 0, 0)]) + len(cand[(c, 1, 0)]) for c in range(len(cats))):
        raise ValueError("a merchant category has no merchants")
    online_ok = np.array([len(cand[(c, 0, 1)]) + len(cand[(c, 1, 1)]) > 0 for c in range(len(cats))])
    ch = _pv(cfg, "channel_coefficients")
    tods = list(ch["delta_h_tod"]["contactless"])
    hp = _pv(cfg, "hourly_profile")
    tod_of_hour = np.zeros(24, int)
    for ti, name in enumerate(tods):
        a, b = hp["tod_buckets"][name]
        tod_of_hour[a:b + 1] = ti

    def per_chan(f):                                   # (n_channels, ...) matrix, reference channel row = 0
        return np.array([f(h) if h in ch["delta_h"] else f(None) for h in chans], float)

    zero_c, zero_t = np.zeros(len(cats)), np.zeros(len(tods))
    dh = per_chan(lambda h: ch["delta_h"][h] if h else 0.0)
    dcat = np.array([[ch["delta_h_category"][h][c] for c in cats] if h in ch["delta_h"] else zero_c for h in chans])
    dtod = np.array([[ch["delta_h_tod"][h][t] for t in tods] if h in ch["delta_h"] else zero_t for h in chans])
    dsl = per_chan(lambda h: ch["delta_h_spend_logit"][h] if h else 0.0)
    dB = per_chan(lambda h: ch["delta_h_state"]["B"][h] if h else 0.0)
    dC = per_chan(lambda h: ch["delta_h_state"]["C"][h] if h else 0.0)
    fc = _pv(cfg, "foreign_coefficients")
    phiH = np.array([fc["phi_H"][h] for h in chans])
    dv = _pv(cfg, "device_trust")
    mechs = V["fraud_type"]["internal_values"]
    pit = _pv(cfg, "fraud_type_mix")["pi_T_by_state"]
    rows = lambda k: [pit[k][m] for m in mechs]  # noqa: E731
    pi_rows = np.array([rows("neither"), rows("B_only"), rows("C_only"), rows("C_only"), rows("both"), rows("both")])
    ic, im = mechs.index("cnp"), mechs.index("merchant_compromise")
    for r, f in ((2, ic), (3, im), (4, ic), (5, im)):  # flavor receives the whole cnp+merchant_compromise mass
        mass = pi_rows[r, ic] + pi_rows[r, im]
        pi_rows[r, ic] = pi_rows[r, im] = 0.0
        pi_rows[r, f] = mass
    inc = V["income_band"]["values"]
    amt = _pv(cfg, "amount_log_scale")
    sh = _pv(cfg, "spend_unfamiliarity_and_geography_shapes")
    S = H["latent_spend_propensity"].to_numpy()
    wd0 = (start.astype("int64") + 3) % 7
    hol = {np.datetime64(d, "D") for d in cfg["simulation"]["holidays"]["dates"]}
    inten = _pv(cfg, "daily_intensity_covariate_effects")
    return dict(
        cfg=cfg, nh=nh, nc=len(C), nm=nm, ndays=ndays, start=start, cats=cats, chans=chans, mechs=mechs, tods=tods,
        h_of_card=h_of_card, cm=cm, exp_day=exp_day, share=C["latent_usage_share"].to_numpy(),
        limit=C["credit_limit_php"].to_numpy(float), S=S, lS=_logit(S), lU=_logit(H["latent_ato_exposure"].to_numpy()),
        lG=_logit(H["latent_travel_propensity"].to_numpy()), U=H["latent_ato_exposure"].to_numpy(),
        G=H["latent_travel_propensity"].to_numpy(), EG=sh["G"]["a"] / (sh["G"]["a"] + sh["G"]["b"]),
        b_i=rng.normal(0, _pv(cfg, "intensity_random_effect_sd"), nh), prefs=ent["holder_category_prefs"],
        mu_i=np.array([amt["mu_by_income"][k] for k in inc])[pd.Index(inc).get_indexer(H["income_band"])],
        m_cat=m_cat, m_foreign=m_foreign, m_online=m_online, V=M["latent_merchant_vulnerability"].to_numpy(float),
        logpop=np.log(M["latent_popularity"].to_numpy(float)), D=D, cand=cand, online_ok=online_ok,
        dh=dh, dcat=dcat, dtod=dtod, dsl=dsl, dB=dB, dC=dC, phiH=phiH, tod_of_hour=tod_of_hour,
        pi_hour=np.array(hp["pi_hour"], float), pi_rows=pi_rows,
        dv_base=np.array([[dv["pi_base_by_channel"][h][k] for k in ("trusted", "new", "unknown")] for h in chans]),
        lam_weekday=np.array(inten["rho_w_mon_to_sun"]),
        wd=np.array([(wd0 + d) % 7 for d in range(ndays)]),
        is_hol=np.array([(start + np.timedelta64(d, "D")) in hol for d in range(ndays)]),
    )


def _run(cx, ev, fr, days, beta0, collect=False):
    """Simulate `days` day indices. beta0=None -> first pilot pass: nothing is discarded, only scores q_k are kept.
    collect=True with a beta0 -> pilot pass under the real retain/discard rule; scores q_k are kept for every opportunity."""
    cfg = cx["cfg"]
    P = lambda n: _pv(cfg, n)  # noqa: E731
    pilot = beta0 is None
    collect = collect or pilot
    nh, nc = cx["nh"], cx["nc"]
    cats, chans, mechs = cx["cats"], cx["chans"], cx["mechs"]
    lam0, rN, rho_S = P("daily_arrival_baseline"), P("count_dispersion"), P("daily_intensity_covariate_effects")["rho_S"]
    rho_h = P("daily_intensity_covariate_effects")["rho_h"]["holiday"]
    om, omc = P("compromise_covariate_effects"), P("cnp_state_transition")
    qrec, qtr = P("recovery_probability"), P("travel_state_transition")
    zf = P("merchant_compromise_flavor")
    bt, gm, ps = P("fraud_effect_coefficients"), P("authorization_coefficients"), P("pre_authorization_risk_weights")
    sd = P("spend_deviation_settings")
    floor, clipz, min_n = sd["sigma_floor"], sd["clip_abs"], sd["min_prior_transactions"]
    bsett, gap_rate = P("burst_mean"), P("burst_gap_rate")["rate_per_hour"]
    dsc = P("discard_rule_for_nonfraud_opportunities")
    discard_mech = np.array([dsc[m] == "discard" for m in mechs])
    dv, dg = P("device_trust"), P("distance_gamma")
    amt, bnd = P("amount_log_scale"), P("amount_bounds")
    tau, p_token = P("distance_decay"), P("ecommerce_tokenization_share")
    ent_modes = cfg["vocabularies"]["entry_mode"]["channel_lookup"]
    sig_c, sig_i = P("amount_category_sigma"), P("amount_dispersion")
    mu_c = np.array([P("amount_category_offsets")[c] for c in cats])
    mu_h = np.array([P("amount_channel_offsets")[h] for h in chans])
    mu_t = np.array([P("amount_tod_offsets")[t] for t in cx["tods"]])
    sg_c = np.array([sig_c[c] for c in cats])
    d_T = np.array([P("mechanism_amount_shifts")[m] for m in mechs])
    e_T = np.array([P("mechanism_amount_noise_sd")[m] for m in mechs])
    fc = P("foreign_coefficients")
    shiftB = np.array([dv["logit_shift_B_active"][k] for k in ("new", "unknown")])
    shiftC = np.array([dv["logit_shift_C_active"][k] for k in ("new", "unknown")])
    shiftU = np.array([dv["logit_shift_per_logit_U"][k] for k in ("new", "unknown")])
    shiftM = np.array([[dv["logit_shift_mechanism"][m][k] for k in ("new", "unknown")] for m in mechs])
    dvb = np.log(cx["dv_base"][:, 1:] / cx["dv_base"][:, :1])        # (channel, 2) log odds vs trusted
    cum_hour = np.cumsum(cx["pi_hour"] / cx["pi_hour"].sum())
    ib = mechs.index("burst")
    i_none = mechs.index("none")
    B, X = np.zeros(nh, bool), np.zeros(nh, bool)
    Cs, flav = np.zeros(nc, bool), np.zeros(nc, np.int8)
    vbar = np.zeros(nh)
    # per-card compact state for the sequential loop
    dq1, dq24 = [None] * nc, [None] * nc
    s24, cnt, mean, m2, last = [0] * nc, [0] * nc, [0.0] * nc, [0.0] * nc, [None] * nc
    seq0 = 0
    cnts = dict(no_active_card=0, time_overflow=0, pool_fallback=0, nonfraud_burst_discarded=0, opportunities=0)
    out, qs, qd = [], [], []
    for d in days:
        # ---- state transitions (all draws always made so the stream does not depend on state) ----
        u1, u2, u3, u4, u5, u6 = (ev.random(nh), ev.random(nc), ev.random(nc), ev.random(nh), ev.random(nh), ev.random(nc))
        startB = _sig(P("compromise_initiation") + om["omega_U"] * cx["lU"] + om["omega_V"] * vbar)
        B = np.where(B, ~(u1 < qrec), u1 < startB)
        hc = cx["h_of_card"]
        startC = _sig(omc["omega_C0"] + omc["omega_CU"] * cx["lU"][hc] + omc["omega_CV"] * vbar[hc])
        new_c = ~Cs & (u2 < startC)
        flav = np.where(new_c, np.where(u3 < _sig(zf["zeta_0"] + zf["zeta_V"] * vbar[hc]), 2, 1), flav).astype(np.int8)
        Cs = np.where(Cs, ~(u2 < omc["q_recover_C"]), new_c)
        X = np.where(X, ~(u5 < qtr["q_travel_off"]), u4 < np.minimum(1.0, qtr["q_travel_on"] * cx["G"] / cx["EG"]))
        # ---- arrivals (Eq 10) ----
        lam = lam0 * np.exp(rho_S * cx["lS"] + cx["lam_weekday"][cx["wd"][d]] + (rho_h if cx["is_hol"][d] else 0.0) + cx["b_i"])
        n = ev.poisson(ev.gamma(rN, lam / rN))
        h = np.repeat(np.arange(nh), n)
        w = cx["share"][np.maximum(cx["cm"][h], 0)] * ((cx["cm"][h] >= 0) & (cx["exp_day"][np.maximum(cx["cm"][h], 0)] > d))
        tot = w.sum(1)
        u = ev.random(len(h)) * tot
        slot = np.minimum((u[:, None] >= np.cumsum(w, 1)).sum(1), w.shape[1] - 1)
        card = cx["cm"][h, slot]
        ok = tot > 0
        cnts["no_active_card"] += int((~ok).sum())
        h, card = h[ok], card[ok]
        hour = np.minimum((ev.random(len(h))[:, None] > cum_hour).sum(1), 23)
        sec = hour * 3600 + ev.integers(0, 3600, len(h))
        # ---- mechanism (Eq 17) and burst expansion ----
        sidx = np.where(Cs[card], np.where(B[h], 4, 2) + (flav[card] == 2), np.where(B[h], 1, 0))
        mech = _draw(ev, cx["pi_rows"][sidx])
        nb = np.where(mech == ib, 1 + ev.poisson(bsett, len(h)), 1)
        par = np.repeat(np.arange(len(h)), nb)
        first = np.r_[True, par[1:] != par[:-1]]
        gap = np.where(first, 0.0, ev.exponential(3600.0 / gap_rate, len(par)))
        cg = np.cumsum(gap)
        cg = cg - cg[np.maximum.accumulate(np.where(first, np.arange(len(par)), 0))]
        h, card, mech = h[par], card[par], mech[par]
        sec = sec[par] + np.rint(cg).astype(np.int64)
        cnts["opportunities"] += len(h)
        order, sec = _unique_secs(card, sec)
        h, card, mech = h[order], card[order], mech[order]
        seq = seq0 + order
        seq0 += len(order)
        keep = sec < _DAY
        cnts["time_overflow"] += int((~keep).sum())
        h, card, mech, sec, seq = h[keep], card[keep], mech[keep], sec[keep], seq[keep]
        m = len(h)
        hour = sec // 3600
        tod = cx["tod_of_hour"][hour]
        Bv, Cv, Xv = B[h], Cs[card], X[h]
        # ---- category, channel (Eq 11), pool (Eq 12) ----
        cat = _draw(ev, cx["prefs"][h])
        z = (cx["dh"][None, :] + cx["dcat"][:, cat].T + cx["dtod"][:, tod].T + cx["dsl"][None, :] * cx["lS"][h][:, None]
             + cx["dB"][None, :] * Bv[:, None] + cx["dC"][None, :] * Cv[:, None])
        z = np.where(cx["online_ok"][cat][:, None] | np.array([c in ("POS", "contactless") for c in chans])[None, :], z, -np.inf)
        chn = _draw(ev, np.exp(z - z.max(1, keepdims=True)))
        pf = _sig(fc["phi_0"] + fc["phi_G_logit"] * cx["lG"][h] + cx["phiH"][chn] + fc["phi_X"] * Xv
                  + fc["phi_Z"]["B"] * Bv + fc["phi_Z"]["C"] * Cv)
        pool = (ev.random(m) < pf).astype(int)
        online = np.isin(np.array(chans)[chn], ("ecommerce", "mail-phone")).astype(int)
        # ---- merchant within category + pool ----
        mid = np.full(m, -1)
        uu = ev.random(m)
        vuln = mech != i_none
        for key in {(int(a), int(b), int(c)) for a, b, c in zip(cat, pool, online)}:
            sel = np.flatnonzero((cat == key[0]) & (pool == key[1]) & (online == key[2]))
            c_ = cx["cand"][key]
            if not len(c_):
                cnts["pool_fallback"] += len(sel)
                c_ = cx["cand"][(key[0], 1 - key[1], key[2])]
            lw = cx["logpop"][c_][None, :] + np.where(vuln[sel][:, None], np.log(cx["V"][c_])[None, :], 0.0)
            if not key[2]:
                lw = lw - tau * cx["D"][h[sel][:, None], c_[None, :]]
            pw = np.exp(lw - lw.max(1, keepdims=True))
            pw = np.cumsum(pw / pw.sum(1, keepdims=True), 1)
            mid[sel] = c_[np.minimum((uu[sel][:, None] > pw).sum(1), len(c_) - 1)]
        F = cx["m_foreign"][mid]
        Vm = cx["V"][mid]
        # ---- device, distance, entry mode ----
        lg = (dvb[chn] + shiftB[None, :] * Bv[:, None] + shiftC[None, :] * Cv[:, None]
              + shiftU[None, :] * cx["lU"][h][:, None] + shiftM[mech])
        dev = _draw(ev, np.exp(np.c_[np.zeros(m), lg]))
        dist = ev.gamma(dg["shape_k"], dg["mean_base_km"] * np.exp(dg["log_mean_slope_travel_state"] * Xv
                        + dg["log_mean_slope_foreign"] * F) / dg["shape_k"])
        dist = np.where(online == 1, np.nan, dist)
        tok = ev.random(m) < p_token
        # ---- amount (Eq 13) ----
        mu = cx["mu_i"][h] + amt["spend_logit_slope"] * cx["lS"][h] + mu_c[cat] + mu_h[chn] + mu_t[tod]
        la = ev.normal(mu, np.sqrt(sig_i ** 2 + sg_c[cat] ** 2)) + d_T[mech] + ev.normal(0.0, 1.0, m) * e_T[mech]
        a = np.round(np.clip(np.exp(la), bnd["min_php"], bnd["max_php"]), 2)
        # ---- sequential per-card pass ----
        uy, ua = fr.random(m), fr.random(m)
        isdev_unk = dev == 2
        cnp = online == 1
        qbase = (bt["beta_B"] * Bv + bt["beta_C"] * Cv + bt["beta_V"] * Vm + bt["beta_F"] * F + bt["beta_H"] * cnp
                 + bt["beta_d"] * isdev_unk + bt["beta_BV"] * Bv * Vm)
        rstat = ps["psi_F"] * F + ps["psi_d"] * isdev_unk
        glim = gm["gamma_L"] * a / cx["limit"][card]
        lga = np.log(a)
        cents = np.rint(a * 100).astype(np.int64)
        t_abs = (d * _DAY + sec).tolist()
        cl, ql, rl, gl_, la_, ce, uyl, ual, ml = (x.tolist() for x in (card, qbase, rstat, glim, lga, cents, uy, ua, mech))
        n1o, s24o, zo, hso = [0] * m, [0.0] * m, [np.nan] * m, [np.nan] * m
        po, yo, apo, rko = [0.0] * m, [False] * m, [True] * m, [0.0] * m
        ret = [True] * m
        for i in range(m):
            c, t = cl[i], t_abs[i]
            q1, q24 = dq1[c], dq24[c]
            if q1 is None:
                q1, q24 = dq1[c], dq24[c] = deque(), deque()
            lim = t - 3600
            while q1 and q1[0] <= lim:
                q1.popleft()
            lim = t - _DAY
            while q24 and q24[0][0] <= lim:
                s24[c] -= q24.popleft()[1]
            n1 = len(q1)
            zz = None
            k = cnt[c]
            if k >= min_n:
                zz = (la_[i] - mean[c]) / max(math.sqrt(m2[c] / (k - SD_DDOF)), floor)
                zz = max(-clipz, min(clipz, zz))
                zo[i] = zz
            az = abs(zz) if zz is not None else 0.0
            if last[c] is not None:
                hso[i] = (t - last[c]) / 3600.0
            n1o[i], s24o[i] = n1, s24[c] / 100.0
            lq = ql[i] + bt["beta_z"] * az + bt["beta_v"] * math.log1p(n1)
            if collect:
                qs.append(lq if ml[i] != i_none else -np.inf)  # T_k=none -> p_k=0 (Eq 16)
                qd.append(discard_mech[ml[i]])
            if pilot:
                y = False
            else:
                p = 1.0 / (1.0 + math.exp(-(beta0 + lq))) if ml[i] != i_none else 0.0
                po[i] = p
                y = yo[i] = uyl[i] < p
                if not y and discard_mech[ml[i]]:
                    ret[i] = False
                    continue
            rk = rko[i] = rl[i] + ps["psi_z"] * az
            pa = 1.0 / (1.0 + math.exp(-(gm["gamma_0"] - gl_[i] - gm["gamma_v"] * math.log1p(n1) - gm["gamma_r"] * rk)))
            appr = apo[i] = ual[i] < pa
            q1.append(t)
            cnt[c] = k + 1
            dl = la_[i] - mean[c]
            mean[c] += dl / (k + 1)
            m2[c] += dl * (la_[i] - mean[c])
            last[c] = t
            if appr:
                q24.append((t, ce[i]))
                s24[c] += ce[i]
        ret = np.array(ret)
        cnts["nonfraud_burst_discarded"] += int((~ret).sum())
        # mean vulnerability of retained merchants per holder on this day (for day d+1)
        vs = np.bincount(h[ret], Vm[ret], nh)
        vn = np.bincount(h[ret], minlength=nh)
        vbar = np.where(vn > 0, vs / np.maximum(vn, 1), 0.0)
        if collect:
            continue
        r = np.flatnonzero(ret)
        out.append(dict(
            seq=seq[r], card=card[r], mid=mid[r], sec=d * _DAY + sec[r], amount=a[r], chn=chn[r], foreign=F[r],
            appr=np.array(apo)[r], tok=tok[r],
            dev=dev[r], dist=dist[r], n1=np.array(n1o)[r], s24=np.array(s24o)[r], z=np.array(zo)[r],
            hour=hour[r], hs=np.array(hso)[r], y=np.array(yo)[r], mech=mech[r], B=Bv[r], C=Cv[r], X=Xv[r],
            p=np.array(po)[r], risk=np.array(rko)[r]))
    if collect:
        return np.array(qs), np.array(qd, bool), cnts
    return {k: np.concatenate([o[k] for o in out]) for k in out[0]}, cnts


def solve_beta0(q, r_f, dis=None, lo=-30.0, hi=5.0, iters=200):
    """Bisection on g(b)=R(b)-r_f (spec 7.2), q=-inf marks T_k=none (p_k=0).

    R(b) is the expected rate of the main process, which keeps every Y=1 row and drops non-fraud rows of discard
    mechanisms (`dis`): R = sum(p) / (n - sum_dis(1-p)). With dis=None nothing is discarded and R = mean(p).
    Calibration note: the pilot spans the full window (states reach their long-run share, unlike a 60-day pilot) and
    applies this expected retain/discard rule. An earlier 60-day pilot with R = mean(p) over all opportunities gave
    realized rates ~0.0027-0.0028 because discards turn burst mass p into p^2 and states were still ramping up.
    """
    dis = np.zeros(len(q), bool) if dis is None else dis
    def g(b):
        p = _sig(b + q)
        return p.sum() / (len(q) - (1 - p[dis]).sum()) - r_f
    if not (g(lo) < 0 < g(hi)):
        raise ValueError(f"beta0 has no root in [{lo}, {hi}]: active-mechanism share of pilot opportunities "
                         f"{np.isfinite(q).mean():.4f} must exceed r_f={r_f}")
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if g(mid) < 0 else (lo, mid)
    return 0.5 * (lo + hi), g(0.5 * (lo + hi)) + r_f


def simulate_events(cfg: dict, entities: dict, streams: dict) -> tuple[pd.DataFrame, dict]:
    cx = _prepare(cfg, entities, streams["events"])
    r_f = _pv(cfg, "underlying_fraud_target")
    pdays = range(cx["ndays"])
    def pil(b0):
        g = copy.deepcopy(streams["pilot"])
        return _run(cx, g, g, pdays, b0, collect=True)
    q, qd, pc = pil(None)                       # same pilot draws every pass (common random numbers)
    beta0, exp_rate = solve_beta0(q, r_f, qd)
    for _ in range(PILOT_ITERS):  # re-run the pilot under the real retain/discard rule at the current beta0
        q, qd, pc = pil(beta0)
        beta0, exp_rate = solve_beta0(q, r_f, qd)
    res, mc = _run(cx, streams["events"], streams["fraud"], range(cx["ndays"]), beta0)
    cats, chans, mechs = cx["cats"], cx["chans"], cx["mechs"]
    mer = entities["merchants"]
    cards = entities["cards"]
    n = len(res["seq"])
    o = np.lexsort((res["seq"], res["sec"]))                     # (transaction_ts, sequence)
    g = lambda k: res[k][o]  # noqa: E731
    tag = hashlib.sha256(str(cfg["simulation"]["seed"]).encode()).hexdigest()[:8]
    ids = np.array([f"{tag}{i:012x}" for i in range(n)], dtype=object)
    ts = (cx["start"].astype("datetime64[s]") + g("sec").astype("timedelta64[s]")).astype("datetime64[ns]")
    chn = g("chn")
    entry = np.empty(n, dtype=object)
    lookup = cfg["vocabularies"]["entry_mode"]["channel_lookup"]
    for ci, cn in enumerate(chans):
        s = chn == ci
        entry[s] = lookup[cn] if cn != "ecommerce" else np.where(g("tok")[s], "tokenized", "manual")
    hr = g("hour")
    df = pd.DataFrame({
        "transaction_id": ids,
        "card_id": cards["card_id"].to_numpy()[g("card")],
        "merchant_id": mer["merchant_id"].to_numpy()[g("mid")],
        "transaction_ts": ts, "amount_php": g("amount"), "channel": np.array(chans, dtype=object)[chn],
        "foreign_transaction": g("foreign"),
        "authorization_status": np.where(g("appr"), "approved", "declined"), "entry_mode": entry,
        "device_trust_level": np.array(["trusted", "new", "unknown"], dtype=object)[g("dev")],
        "distance_from_home_km": g("dist"), "tx_count_prev_1h": g("n1"), "amount_sum_prev_24h_php": g("s24"),
        "spend_deviation_z": g("z"), "local_hour_sin": np.sin(2 * np.pi * hr / 24), "local_hour_cos": np.cos(2 * np.pi * hr / 24),
        "hours_since_prev_tx": g("hs"),
        "y_true": g("y"), "mechanism": np.array(mechs, dtype=object)[g("mech")],
        "latent_ato_state": g("B"), "latent_cnp_compromise_state": g("C"), "latent_travel_state": g("X"),
        "latent_fraud_p": g("p"), "latent_risk_score": g("risk"),
    })
    assert list(df.columns[:len(ALLOWLIST["transactions"])]) == ALLOWLIST["transactions"]
    info = dict(beta0=beta0, pilot_days=len(pdays), pilot_n=len(q), pilot_expected_rate=exp_rate, pilot_counts=pc,
                main_expected_rate=float(df["latent_fraud_p"].mean()), main_realized_rate=float(df["y_true"].mean()),
                n_rows=n, discarded=mc)
    return df, info
