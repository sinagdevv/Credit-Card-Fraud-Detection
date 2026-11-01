# SD-008 Team Workflow and Responsibilities

This workflow allocates substantial, reviewable contributions to both team members without starting Deliverables 2 or 3.

## Sprint 2 Deliverable 2 Synthetic Dataset Generator

### John Ray

- Generator architecture and configuration contract
- Mathematical model implementation
- Fraud episode and observation-process simulation
- Batch scalability and deterministic random streams
- Component integration and final technical review

### Jee

- Statistical distribution QA against the Deliverable 1 registry
- Synthetic data quality and conditional-dependence tests
- Primary-key, foreign-key, schema, and cardinality validation
- Missingness, extreme-value, timestamp, and outlier verification
- Fraud imbalance, concentration, and observed-label-gap verification
- Reproducibility tests across seeds and batch sizes
- Validation report and acceptance evidence

### Mutual review

Jee reviews the statistical behavior of John's generator. John reviews validation code and resolves integration defects. Neither member approves their own major contribution alone.

## Sprint 3 Deliverable 3 Exploratory Data Analysis

### Jee

- Primary EDA notebook development
- Descriptive statistics and data-quality summaries
- Transaction amount, time, velocity, and channel visualizations
- Fraud, merchant, geography, and review-status segmentation
- Feature-level analysis and written interpretation

### John Ray

- Advanced fraud-mechanism analysis
- Interpretation of selective-review and label-observation bias
- Optional predictive modeling if scope and time permit
- Chronological evaluation methodology and leakage review
- Final technical integration and review

### Mutual review

John reviews the EDA for leakage and unsupported causal claims. Jee reviews any predictive-model outputs for statistical validity and reproducibility.

## Planning constraints

- Deliverable 2 and 3 implementation has not started.
- Assignees are named here without inventing a GitHub username for Jee.
- Existing GitHub issues should be updated rather than duplicated when project access is restored.
