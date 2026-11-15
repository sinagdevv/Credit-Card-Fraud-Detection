# End-to-end validation report

## Clean CI

GitHub Actions run [43738123280](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/actions/runs/43738123280) passed on commit `75af47716aac0da2cd646da5dee0cae9eb9a8ea6` with standard Python 3.12. The smoke job installed `requirements.txt`, ran `python tools/validate_d1.py`, ran `python -m pytest tests -q`, generated a fresh D2 export, and executed `02_Fraud_Analytics_EDA.ipynb`. This remains the clean-environment authority until the evidence-only commit from this report receives CI.

## Exact BASELINE D3 execution

On 2026-11-16, `02_Fraud_Analytics_EDA.ipynb` executed successfully in 20.24 seconds against fresh exact BASELINE export `run_20261101_17101a81` (150,000 transactions, seed `20261101`). It loaded only the five analyst-facing CSV tables. The output held 1,567 label records, 1,516 resolved outcomes, and 117 observed positives; median transaction amount was PHP 680.59 and p95 was PHP 6,977.64. The notebook explicitly treats uninvestigated transactions as unknown rather than confirmed legitimate. Execution used Python 3.13.2 locally; CI is the Python 3.12 clean-environment evidence.

## Additional persisted evidence

- Exact SMALL, BASELINE, and STRESS profiles reached 10K, 150K, and 1M transactions respectively.
- The 1M STRESS profile completed in about 96 seconds using an observed 1.22 GiB process working set.
- Eight exact BASELINE calibration artifacts and three-seed stochastic-versus-exact artifacts are retained in `docs/qa/evidence/`.
- Exact mode's fraud prevalence is below the provisional 0.3% reference; this is a documented limitation rather than a hidden calibration change.
