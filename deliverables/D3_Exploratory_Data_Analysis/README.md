# Deliverable 3: Exploratory Data Analysis

## Objective

Produce a reproducible Jupyter notebook that explains the accepted synthetic dataset, its quality, fraud patterns, operational labels, and analytical limitations. Implementation must wait for the validated Deliverable 2 output.

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

