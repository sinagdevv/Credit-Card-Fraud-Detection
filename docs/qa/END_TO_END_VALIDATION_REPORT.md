# End-to-end validation report

## 2026-11-15 CI evidence

GitHub Actions run [43731973372](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/actions/runs/43731973372) passed on Python 3.12.16. It installed `requirements.txt`, ran `python tools/validate_d1.py`, ran `python -m pytest tests -q`, generated a fresh D2 test export, and executed `02_Fraud_Analytics_EDA.ipynb` against that export. The job completed successfully at 15:50:11 UTC.

This proves the small clean-environment path. It does not benchmark named 10K, 150K, or 1M exact-count profiles.
