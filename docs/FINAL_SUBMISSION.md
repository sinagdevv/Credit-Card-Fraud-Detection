# SD-008 Final Submission Manifest

This manifest points to canonical repository artifacts; it intentionally does not duplicate generated datasets.

| Submission item | Canonical path | Review note |
| --- | --- | --- |
| D1 model research and specifications | [`deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx`](../deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx) | Word deliverable; accessible Markdown and ERD assets are adjacent |
| D2 generator notebook | [`deliverables/D2_Synthetic_Dataset_Generator/D2_Synthetic_Dataset_Generator.ipynb`](../deliverables/D2_Synthetic_Dataset_Generator/D2_Synthetic_Dataset_Generator.ipynb) | Reuses the validated `sd008_gen` package and scenario config |
| D3 EDA notebook | [`deliverables/D3_Exploratory_Data_Analysis/02_Fraud_Analytics_EDA.ipynb`](../deliverables/D3_Exploratory_Data_Analysis/02_Fraud_Analytics_EDA.ipynb) | Executed on a fresh exact 150K BASELINE export; analyst-facing tables only |
| Fraud Intelligence dashboard | [`dashboard/`](../dashboard/) | Optional read-only Streamlit showcase |
| Statistical QA | [`docs/qa/`](qa/) | Technical QA, data-quality report, scorecard, end-to-end report, and persisted JSON evidence |
| Reproduction commands | [`README.md`](../README.md#reproduce-from-a-clean-clone) | Python 3.12 reference, environment setup, tests, D2, D3, and dashboard |

## Review order

1. Read the [root README](../README.md) for scope, limits, and architecture.
2. Review D1, then the D2 implementation and its [technical QA](qa/D2-TECHNICAL-QA.md).
3. Inspect the [D2 data-quality report](qa/D2_DATA_QUALITY_REPORT.md) and persisted evidence under `docs/qa/evidence/`.
4. Execute or inspect D3 with an exact BASELINE export.
5. Optionally launch the dashboard using the documented `SD008_DATA_DIR` command.

## Submission boundary

The repository contains source, notebooks, documentation, QA evidence, and lightweight screenshots. Generated transaction exports are deliberately excluded from Git. Internal row-level fraud truth and simulator latent state are not dashboard or D3 inputs; only aggregate QA evidence contains ground-truth-derived statistics.
