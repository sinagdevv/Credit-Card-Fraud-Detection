# Deliverable 3: Exploratory Data Analysis

## Objective

Produce a reproducible Jupyter notebook that explains the accepted synthetic dataset, its quality, fraud patterns, operational labels, and analytical limitations. Status: implemented and executed against a fresh exact 150K BASELINE export; the clean Python 3.12 CI smoke workflow also executes it. D3 loads only the five exported tables and the aggregate `label_gap_summary.csv`.

## Reproduce

From the repository root, create and activate a Python 3.12 environment, then install `requirements.txt` as documented in the [root README](../../README.md#reproduce-from-a-clean-clone). Generate a D2 run first, then point `DATA_DIR` at either that `run_*` directory or a parent containing exactly one run:

```powershell
$env:DATA_DIR = "deliverables/D2_Synthetic_Dataset_Generator/outputs"
jupyter nbconvert --to notebook --execute --inplace deliverables/D3_Exploratory_Data_Analysis/02_Fraud_Analytics_EDA.ipynb --ExecutePreprocessor.timeout=180
```

The notebook fails closed when it cannot resolve a manifest. It reads the five analyst-facing tables and `label_gap_summary.csv`; it does not read simulator latent state or row-level ground truth.

## Required analysis

- Table dimensions, data types, missingness, uniqueness, and key integrity
- Descriptive statistics for cardholders, cards, merchants, transactions, and fraud labels
- Transaction amount and spending-distribution charts, including robust or log-scaled views
- Time-of-day, day-of-week, and transaction-velocity analysis
- Fraud class imbalance and fraud-rate comparisons with suitable denominators
- Merchant category, channel, geography, and merchant-risk segmentation
- Fraud-type and compromise-mechanism analysis
- Ground-truth, investigation-selection, and observed-label comparisons, using only the aggregate `label_gap_summary.csv` (no row-level ground truth)
- Feature distributions and relationships relevant to fraud analysis
- Written interpretations for every material table or chart

Optional predictive modeling is permitted only after the descriptive work is complete. Any model must use a chronological split, avoid future leakage, report imbalance-aware metrics, and state that performance on synthetic data is not evidence of production effectiveness.

## Responsibilities

### Jee

- Primary EDA notebook
- Descriptive statistics and data-quality summaries
- Data visualization, merchant segmentation, and feature analysis
- Interpretation and findings

### John Ray

- Advanced fraud-mechanism analysis
- Label-selection bias and observed-label limitations
- Optional predictive modeling and evaluation methodology
- Leakage review, integration, and final technical review

## Definition of Done

- The notebook runs end to end against the approved D2 dataset.
- Required descriptive tables and charts are complete, readable, and use correct denominators.
- Fraud imbalance, merchant risk, spending, velocity, fraud type, and observed-label limitations are interpreted.
- Claims distinguish synthetic behavior from real-world evidence and avoid unsupported causal conclusions.
- Optional modeling, if included, is chronologically evaluated and reproducible.
- John and Jee complete cross-review and document limitations and follow-up questions.

