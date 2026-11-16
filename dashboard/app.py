"""SD-008 Fraud Intelligence: read-only synthetic fraud analytics workspace."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard.services.data import analyst_transactions, kpis, load_dataset, scenario_evidence

st.set_page_config(page_title="SD-008 | Fraud Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT / 'dashboard' / 'styles' / 'theme.css').read_text()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading analyst-facing exports…")
def cached_load(path: str):
    return load_dataset(path)


def fmt_php(value: float) -> str:
    return f"PHP {value:,.2f}"


def metric_grid(values: dict):
    labels = [("Total transactions", f"{values['transactions']:,}"), ("Transaction value", fmt_php(values['value'])),
              ("Average amount", fmt_php(values['average'])), ("Observed positives", f"{values['observed_positives']:,}"),
              ("Investigation coverage", f"{values['review_coverage']:.2%}"), ("Cardholders", f"{values['cardholders']:,}"),
              ("Merchants", f"{values['merchants']:,}")]
    for row in range(0, len(labels), 4):
        cols = st.columns(4)
        for col, (label, value) in zip(cols, labels[row:row + 4]):
            col.markdown(f'<div class="metric-card"><p>{label}</p><strong>{value}</strong></div>', unsafe_allow_html=True)


def filters(tx: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("### Transaction filters")
    lo, hi = tx.transaction_ts.min().date(), tx.transaction_ts.max().date()
    dates = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    amount = st.sidebar.slider("Amount (PHP)", 0.0, float(tx.amount_php.quantile(.995)), (0.0, float(tx.amount_php.quantile(.995))))
    categories = st.sidebar.multiselect("Merchant category", sorted(tx.merchant_category.dropna().unique()))
    channels = st.sidebar.multiselect("Payment channel", sorted(tx.channel.dropna().unique()))
    status = st.sidebar.multiselect("Label status", sorted(tx.label_status.dropna().unique()))
    out = tx[(tx.transaction_ts.dt.date >= dates[0]) & (tx.transaction_ts.dt.date <= dates[-1]) & tx.amount_php.between(*amount)]
    for column, selected in (("merchant_category", categories), ("channel", channels), ("label_status", status)):
        if selected:
            out = out[out[column].isin(selected)]
    return out


def overview(tx: pd.DataFrame, frames: dict, manifest: dict):
    st.title("Fraud Intelligence")
    st.markdown("<p class='eyeline'>SYNTHETIC TRANSACTION ANALYTICS · READ ONLY</p>", unsafe_allow_html=True)
    st.markdown(f"Dataset profile: analyst-facing export · seed `{manifest['seed']}` · configuration `{manifest['config_sha256'][:8]}`")
    metric_grid(kpis(tx, frames))
    st.markdown("<div class='notice'>Observed outcomes are available only for selected review or customer-report records. Uninvestigated transactions are unknown, not confirmed legitimate.</div>", unsafe_allow_html=True)
    daily = tx.set_index("transaction_ts").resample("D").agg(transactions=("transaction_id", "size"), value=("amount_php", "sum")).reset_index()
    c1, c2 = st.columns((1.2, 1))
    c1.plotly_chart(px.line(daily, x="transaction_ts", y="transactions", title="Transaction volume over time", template="plotly_dark"), width="stretch")
    c2.plotly_chart(px.histogram(tx, x="amount_php", nbins=70, log_y=True, title="Amount distribution · log count", template="plotly_dark"), width="stretch")
    c3, c4 = st.columns(2)
    c3.plotly_chart(px.bar(tx.groupby("merchant_category", as_index=False).amount_php.sum().sort_values("amount_php", ascending=False).head(12), x="merchant_category", y="amount_php", title="Spend by merchant category", template="plotly_dark"), width="stretch")
    c4.plotly_chart(px.bar(tx.groupby("country_code", as_index=False).transaction_id.count().sort_values("transaction_id", ascending=False), x="country_code", y="transaction_id", title="Geographic transaction breakdown", template="plotly_dark"), width="stretch")


def explorer(tx: pd.DataFrame):
    st.title("Transaction Explorer")
    visible = filters(tx)
    query = st.text_input("Search transaction, card, or merchant ID")
    if query:
        visible = visible[visible[["transaction_id", "card_id", "merchant_id"]].astype(str).apply(lambda c: c.str.contains(query, case=False)).any(axis=1)]
    page_size = st.selectbox("Rows per page", [25, 50, 100], index=1)
    pages = max(1, (len(visible) + page_size - 1) // page_size)
    page = st.number_input("Page", 1, pages, 1)
    cols = ["transaction_id", "transaction_ts", "amount_php", "merchant_category", "country_code", "channel", "tx_count_prev_1h", "spend_deviation_z", "label_status"]
    st.caption(f"{len(visible):,} matching records · pagination prevents a full dataset table payload.")
    st.dataframe(visible.iloc[(page - 1) * page_size:page * page_size][cols], width="stretch", hide_index=True)
    selected = st.selectbox("Inspect transaction", visible.transaction_id.head(1000).tolist() if len(visible) else [])
    if selected:
        row = visible.loc[visible.transaction_id.eq(selected)].iloc[0]
        st.json({k: (str(v) if isinstance(v, pd.Timestamp) else v) for k, v in row[cols + ["distance_from_home_km", "amount_sum_prev_24h_php", "investigation_status", "label_source"]].items()})
        st.info("Velocity and spending-deviation fields are historical, observable indicators—not calibrated fraud predictions.")


def investigation(tx: pd.DataFrame):
    st.title("Investigation Workspace")
    q = tx.assign(heuristic=(tx.tx_count_prev_1h.clip(upper=12) * .6 + tx.spend_deviation_z.abs().fillna(0) * .25 + tx.foreign_transaction.astype(int) * .8 + tx.device_trust_level.eq("unknown").astype(int) * .7))
    st.markdown("Heuristic queue score is an interpretable triage aid from observable indicators; it is not a trained fraud model.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investigated", int(q.label_source.eq("analyst").sum()))
    c2.metric("Customer reported", int(q.label_source.eq("customer").sum()))
    c3.metric("Observed positive", int(q.observed_fraud.fillna(False).sum()))
    c4.metric("Unknown / unlabeled", int(q.label_status.eq("unresolved / unlabeled").sum()))
    queue = q.sort_values("heuristic", ascending=False).head(100)
    st.dataframe(queue[["transaction_id", "transaction_ts", "amount_php", "tx_count_prev_1h", "spend_deviation_z", "foreign_transaction", "device_trust_level", "heuristic", "label_status"]], width="stretch", hide_index=True)
    st.caption("A positive observed label is an observed outcome; cleared, pending, and unlabeled records are not interchangeable.")


def scenario_lab():
    st.title("Scenario Lab")
    st.markdown("Verified 150K / seed 20261101 reference evidence. Internal fraud counts below are aggregate simulator QA statistics, never row-level analyst labels.")
    evidence = scenario_evidence(ROOT)
    st.dataframe(evidence, width="stretch", hide_index=True)
    m = evidence.melt(id_vars=["Scenario"], value_vars=["Internal QA fraud", "Investigations", "Observed positives"], var_name="Metric", value_name="Count")
    st.plotly_chart(px.bar(m, x="Scenario", y="Count", color="Metric", barmode="group", title="Scenario comparison", template="plotly_dark"), width="stretch")
    st.info("To generate a new scenario, use the validated D2 CLI explicitly. The dashboard does not start expensive simulations automatically.")


def quality():
    st.title("Simulation Quality")
    st.metric("Exact BASELINE mean fraud prevalence", "0.18517%", "8 independent seeds")
    st.caption("Seed-level 95% t interval: 0.17614%–0.19419% · provisional reference assumption: 0.3%.")
    st.warning("The exact-count configuration is below the provisional reference. This is not external banking-data calibration.")
    st.dataframe(pd.DataFrame({"Mode": ["Stochastic", "Exact"], "Mean prevalence": ["0.28208%", "0.19356%"], "Mean transactions": [319706, 150000]}), width="stretch", hide_index=True)
    st.caption("Mode comparison has different total exposure. Conditioning on an exact total changes arrival distributions and caps burst expansion; the difference is descriptive, not causal proof.")


def methodology():
    st.title("Methodology")
    st.markdown("""**SD-008 is a synthetic fraud simulation and analysis workflow—not a production banking fraud system.**

The generator produces five normalized tables: cardholders, cards, merchants, transactions, and sparse fraud labels. Gamma-mixed cardholder-day activity drives stochastic arrivals; exact profiles condition that intensity field with multinomial allocation to meet a requested total. Compromise episodes generate mechanism-specific activity before investigation selection. Analyst review and customer reports create delayed, incomplete observed labels. Latent states and row-level truth remain internal and are excluded from this application.

Read the full [model specification](../docs/modeling/SD-008_MODEL_SPECIFICATION.md), [D2 QA report](../docs/qa/D2_DATA_QUALITY_REPORT.md), and [realism scorecard](../docs/qa/SYNTHETIC_REALISM_SCORECARD.md) in the repository.
""")


def main():
    with st.sidebar:
        st.markdown("## SD-008")
        st.caption("FRAUD INTELLIGENCE")
        source = st.text_input("Dataset directory", os.getenv("SD008_DATA_DIR", "outputs"))
        page = st.radio("Workspace", ["Overview", "Transaction Explorer", "Investigation Workspace", "Scenario Lab", "Simulation Quality", "Methodology"])
    if page in {"Scenario Lab", "Simulation Quality", "Methodology"}:
        {"Scenario Lab": scenario_lab, "Simulation Quality": quality, "Methodology": methodology}[page](); return
    try:
        frames, manifest, _ = cached_load(source)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        st.title("Fraud Intelligence")
        st.error(str(exc))
        st.code("python -m sd008_gen.generate --config config/scenario_v0.yaml --out ../../outputs --profile BASELINE --seed 20261101", language="powershell")
        st.caption("Generate a local analyst-facing export, then set its parent directory above. No data is bundled or generated automatically.")
        return
    tx = analyst_transactions(frames)
    {"Overview": lambda: overview(tx, frames, manifest), "Transaction Explorer": lambda: explorer(tx), "Investigation Workspace": lambda: investigation(tx)}[page]()


if __name__ == "__main__":
    main()
