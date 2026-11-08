"""Cardholders, cards, merchants (spec §5.2-5.5, Eqs 1-9). All values come from the config."""
import numpy as np
import pandas as pd

HOLDER_COLS = ["cardholder_id", "age_band", "income_band", "home_region", "urbanicity",
               "account_open_date", "employment_segment"]
CARD_COLS = ["card_id", "cardholder_id", "card_brand", "issue_date", "expiry_date",
             "credit_limit_php", "card_status", "product_tier"]
MERCHANT_COLS = ["merchant_id", "merchant_category", "mcc", "country_code", "merchant_region",
                 "merchant_size_band", "online_capable"]


def _pv(cfg, name):
    return cfg["parameters"][name]["value"]


def _draw(rng, probs):
    """Categorical draw per row of an (n, k) probability matrix."""
    p = np.asarray(probs, dtype=float)
    p = p / p.sum(axis=1, keepdims=True)
    u = rng.random(len(p))[:, None]
    return np.minimum((u > np.cumsum(p, axis=1)).sum(axis=1), p.shape[1] - 1)


def _ids(rng, n):
    raw = rng.bytes(16 * n)
    ids = [raw[16 * i:16 * i + 16].hex() for i in range(n)]
    assert len(set(ids)) == n
    return np.array(ids, dtype=object)


def _cond(rng, parent_codes, cond_dict, parent_keys, child_keys):
    m = np.array([[cond_dict[p][c] for c in child_keys] for p in parent_keys])
    return _draw(rng, m[parent_codes])


def _logit(x):
    return np.log(x / (1 - x))


def _holders(cfg, rng, n):
    V = cfg["vocabularies"]
    reg, age, inc, emp, urb = (V[k]["values"] for k in
                               ("home_region", "age_band", "income_band", "employment_segment", "urbanicity"))
    h = {"cardholder_id": _ids(rng, n)}
    r = _draw(rng, np.tile([_pv(cfg, "home_region_weights")["pi_R"][k] for k in reg], (n, 1)))
    a = _cond(rng, r, _pv(cfg, "age_band_by_region")["pi_A_given_R"], reg, age)
    e = _cond(rng, a, _pv(cfg, "employment_by_age")["pi_E_given_A"], age, emp)
    il = _pv(cfg, "income_logit")
    j = np.arange(len(inc)) - 2
    slope = (np.array([il["age_slope"][k] for k in age])[a]
             + np.array([il["region_slope"][k] for k in reg])[r]
             + np.array([il["employment_slope"][k] for k in emp])[e])
    ii = _draw(rng, np.exp(np.array(il["alpha"])[None, :] + slope[:, None] * j[None, :]))
    u = _cond(rng, r, _pv(cfg, "urbanicity_by_region")["pi_U_given_R"], reg, urb)
    tn = _pv(cfg, "account_tenure")
    theta = np.array([tn["theta_T_days"][k] for k in inc])[ii]
    T = np.rint(np.clip(rng.gamma(tn["k_T"], theta), tn["min_days"], tn["max_days"])).astype(int)
    start = np.datetime64(cfg["simulation"]["start_date"], "D")
    sh = _pv(cfg, "spend_unfamiliarity_and_geography_shapes")
    h.update(age_band=np.array(age)[a], income_band=np.array(inc)[ii], home_region=np.array(reg)[r],
             urbanicity=np.array(urb)[u], account_open_date=(start - T.astype("timedelta64[D]")).astype("datetime64[ns]"),
             employment_segment=np.array(emp)[e])
    h["latent_spend_propensity"] = rng.beta(sh["S"]["a"], sh["S"]["b"], n)
    h["latent_ato_exposure"] = rng.beta(sh["U"]["a"], sh["U"]["b"], n)
    h["latent_travel_propensity"] = rng.beta(sh["G"]["a"], sh["G"]["b"], n)
    return pd.DataFrame(h), ii, T


def _cards(cfg, rng, hold, ii, T):
    V = cfg["vocabularies"]
    inc, tiers, brands = V["income_band"]["values"], V["product_tier"]["values"], V["card_brand"]["values"]
    n = len(hold)
    cc = _pv(cfg, "card_count_coefficients")
    lt = np.log1p(T)
    lam = np.exp(cc["eta_0"] + np.array([cc["eta_I"][k] for k in inc])[ii] + cc["eta_T"] * lt)
    nc = 1 + np.minimum(3, rng.poisson(lam))
    own = np.repeat(np.arange(n), nc)                      # holder row per card
    m = len(own)
    # product tier: categorical logit, reference tier has logit 0 (Sec 5.8 14a)
    pt = _pv(cfg, "product_tier_logit")
    ref = pt["reference"]
    S = hold["latent_spend_propensity"].to_numpy()[own]
    lg = _logit(S)
    z = np.zeros((m, len(tiers)))
    for t, name in enumerate(tiers):
        if name != ref:
            z[:, t] = pt["intercept"][name] + pt["income_slope"][name] * (ii[own] - 2) + pt["spend_logit_slope"][name] * lg
    q = _draw(rng, np.exp(z - z.max(axis=1, keepdims=True)))
    brand = _cond(rng, q, _pv(cfg, "card_brand_weights")["pi_brand_given_tier"], tiers, brands)
    # credit limit (Eq 8)
    le, bnd = _pv(cfg, "credit_limit_effects"), _pv(cfg, "credit_limit_bounds")
    mean = (_pv(cfg, "credit_limit_location") + np.array([le["lambda_I"][k] for k in inc])[ii[own]]
            + np.array([le["lambda_Q"][k] for k in tiers])[q] + le["lambda_T"] * lt[own])
    lim = np.round(np.clip(np.exp(mean + rng.normal(0, le["sigma_L"], m)), bnd["min_php"], bnd["max_php"]), 2)
    # issue date: discrete uniform on [max(start-3y+1d, open), start]; +1d so expiry (>=issue+3y) > start
    start = pd.Timestamp(cfg["simulation"]["start_date"])
    lo = np.maximum((start - pd.DateOffset(years=3) + pd.Timedelta(days=1)).to_datetime64(),
                    hold["account_open_date"].to_numpy()[own])
    span = (start.to_datetime64() - lo) // np.timedelta64(1, "D") + 1
    issue = lo + np.floor(rng.random(m) * span).astype("timedelta64[D]").astype("timedelta64[ns]")
    yrs = rng.choice(_pv(cfg, "card_tenor_and_issue")["expiry_years_choices"], m)
    expiry = np.empty(m, dtype="datetime64[ns]")
    for y in np.unique(yrs):                                # one offset op per distinct tenor
        s = yrs == y
        expiry[s] = (pd.DatetimeIndex(issue[s]) + pd.DateOffset(years=int(y))).to_numpy()
    # usage share: normalised symmetric gammas per holder == Dirichlet(alpha)
    g = rng.gamma(_pv(cfg, "card_usage_share_dirichlet")["alpha"], size=m)
    share = g / np.bincount(own, g)[own]
    return pd.DataFrame({
        "card_id": _ids(rng, m), "cardholder_id": hold["cardholder_id"].to_numpy()[own],
        "card_brand": np.array(brands)[brand], "issue_date": issue, "expiry_date": expiry,
        "credit_limit_php": lim, "card_status": "active", "product_tier": np.array(tiers)[q],
        "latent_usage_share": share})


def _merchants(cfg, rng, n):
    V = cfg["vocabularies"]
    mcc = V["merchant_category"]["mcc"]
    cats, ctry, sizes = list(mcc), V["country_code"]["values"], V["merchant_size_band"]["values"]
    c = _draw(rng, np.tile([_pv(cfg, "merchant_category_weights")["pi_C"][k] for k in cats], (n, 1)))
    k = _draw(rng, np.tile([_pv(cfg, "merchant_country_weights")["pi_K"][k] for k in ctry], (n, 1)))
    z = _cond(rng, c, _pv(cfg, "merchant_size_by_category")["pi_Z_given_C"], cats, sizes)
    region = np.empty(n, dtype=object)
    rm = _pv(cfg, "merchant_region_by_country")["pi_Rm_given_K"]
    for ki, kn in enumerate(ctry):                          # <= 5 countries
        s = k == ki
        regs = list(rm[kn])
        region[s] = np.array(regs)[_draw(rng, np.tile([rm[kn][r] for r in regs], (s.sum(), 1)))]
    vs = _pv(cfg, "merchant_vulnerability_shape")
    a = np.array([vs[x]["a"] for x in cats])[c]
    b = np.array([vs[x]["b"] for x in cats])[c]
    po = np.array([_pv(cfg, "merchant_online_capable_prob")["p_online_capable"][x] for x in cats])[c]
    pop = _pv(cfg, "merchant_popularity_by_size")
    return pd.DataFrame({
        "merchant_id": _ids(rng, n), "merchant_category": np.array(cats)[c],
        "mcc": np.array([mcc[x] for x in cats])[c], "country_code": np.array(ctry)[k],
        "merchant_region": region, "merchant_size_band": np.array(sizes)[z],
        "online_capable": rng.random(n) < po,
        "latent_merchant_vulnerability": rng.beta(a, b),
        "latent_popularity": np.array([pop[x] for x in sizes])[z].astype(float)})


def make_entities(cfg: dict, rng: np.random.Generator) -> dict:
    sim = cfg["simulation"]
    hold, ii, T = _holders(cfg, rng, sim["n_cardholders"])
    cards = _cards(cfg, rng, hold, ii, T)
    merchants = _merchants(cfg, rng, sim["n_merchants"])
    pi_c = np.array([_pv(cfg, "merchant_category_weights")["pi_C"][k]
                     for k in cfg["vocabularies"]["merchant_category"]["mcc"]])
    prefs = rng.dirichlet(_pv(cfg, "category_preference_concentration") * pi_c, size=len(hold))
    return {"cardholders": hold, "cards": cards, "merchants": merchants, "holder_category_prefs": prefs}
