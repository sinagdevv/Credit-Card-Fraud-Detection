# Final submission checklist

Current assessment: **HOLD — D2 is reviewable; the project is not yet submission-ready.**

- [x] D1 source and DOCX have an automated consistency check.
- [x] D2 produces five allowlisted analyst tables in a controlled run.
- [x] Internal fraud state is excluded from ordinary analyst CSV exports.
- [x] PR #13 and its predecessor PR #10 were audited.
- [x] D2 exact 10K, 150K, and 1M profiles measured; calibration limitation documented.
- [x] Baseline, high-fraud-pressure, and strict-review-budget single-seed comparison recorded.
- [ ] D3 notebook exists and is wired into CI; execution against a fresh export still needs recorded evidence.
- [ ] End-to-end smoke command and CI workflow.
- [ ] `D2_DATA_QUALITY_REPORT.md` and `END_TO_END_VALIDATION_REPORT.md` with current evidence.
- [ ] Human technical/peer review and merge authorization.

Before submission, run the suite in a normal clean Python environment, execute both notebooks from top to bottom, record the actual runtime/memory results, and attach those results to the integration PR. Do not infer a review approval from this checklist.
