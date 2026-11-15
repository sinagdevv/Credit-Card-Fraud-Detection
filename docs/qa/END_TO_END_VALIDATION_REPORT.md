# End-to-end validation report

## 2026-11-15 CI evidence

GitHub Actions run [43731973372](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/actions/runs/43731973372) passed on Python 3.12.16. It installed `requirements.txt`, ran `python tools/validate_d1.py`, ran `python -m pytest tests -q`, generated a fresh D2 test export, and executed `02_Fraud_Analytics_EDA.ipynb` against that export. The job completed successfully at 15:50:11 UTC.

This proves the small clean-environment path. It does not benchmark named 10K, 150K, or 1M exact-count profiles.

## Exact BASELINE D3 execution

On 2026-11-16, `02_Fraud_Analytics_EDA.ipynb` executed successfully in 20.24 seconds against fresh exact BASELINE export `run_20261101_17101a81` (150,000 transactions). It loaded only the five analyst-facing CSV tables. The output held 1,567 label records, 1,516 resolved outcomes, and 117 observed positives; the transaction median was PHP 680.59 and p95 was PHP 6,977.64. The notebook's explicit narrative preserves the unknown status of uninvestigated transactions. The execution used Python 3.13.2 locally; CI remains the Python 3.12 clean-environment authority.
