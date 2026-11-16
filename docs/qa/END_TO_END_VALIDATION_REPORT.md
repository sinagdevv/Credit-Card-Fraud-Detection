# End-to-end validation report

## Clean CI

GitHub Actions run [43739572787](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/actions/runs/43739572787) passed on commit `4a3ba27897b31229689ff3f943212ec9e6637dce` with standard Python 3.12. The smoke job installed `requirements.txt`, passed all six D1 checks, passed `96` pytest tests in 8.07 seconds, generated a fresh D2 export, and executed `02_Fraud_Analytics_EDA.ipynb`.

Local verification with the portable Python 3.13 runtime passed D1 but reached 95 passed / 1 failed when its embedded interpreter ignored the subprocess `PYTHONPATH` in `test_cli_smoke`; an earlier run also encountered sandbox temp-directory permissions. Those are local harness limitations, not a clean-environment failure: the same complete suite passed in standard Python 3.12 CI.

## Exact BASELINE D3 execution

On 2026-11-16, `02_Fraud_Analytics_EDA.ipynb` executed successfully in 20.24 seconds against fresh exact BASELINE export `run_20261101_17101a81` (150,000 transactions, seed `20261101`). It loaded only the five analyst-facing CSV tables. The output held 1,567 label records, 1,516 resolved outcomes, and 117 observed positives; median transaction amount was PHP 680.59 and p95 was PHP 6,977.64. The notebook explicitly treats uninvestigated transactions as unknown rather than confirmed legitimate. Execution used Python 3.13.2 locally; CI is the Python 3.12 clean-environment evidence.

## Additional persisted evidence

- Exact SMALL, BASELINE, and STRESS profiles reached 10K, 150K, and 1M transactions respectively.
- The 1M STRESS profile completed in about 96 seconds using an observed 1.22 GiB process working set.
- Eight exact BASELINE calibration artifacts and three-seed stochastic-versus-exact artifacts are retained in `docs/qa/evidence/`.
- Exact mode's fraud prevalence is below the provisional 0.3% reference; this is a documented limitation rather than a hidden calibration change.
