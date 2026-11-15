# Final submission checklist

Current assessment: **TECHNICALLY READY FOR HUMAN REVIEW — not merged or peer-approved.**

- [x] D1 source and DOCX pass the six-check structural validator.
- [x] D2 generates five allowlisted analyst tables; PK/FK, chronology, and latent-exclusion checks run before export.
- [x] Exact SMALL (10K), BASELINE (150K), and STRESS (1M) profiles were measured.
- [x] STRESS completed in about 96s with about 1.22 GiB observed working set.
- [x] Eight-seed exact calibration is persisted; the mean is 0.18517%, below the provisional 0.3% reference.
- [x] High-fraud-pressure and strict-review-budget scenarios were measured; strict review preserves the transaction CSV.
- [x] D3 executed on a fresh exact 150K export and is included in clean CI smoke.
- [x] Aggregate-only stochastic-versus-exact comparison is persisted and documents the conditioning limitation.
- [x] CI passed through commit `75af477`; final evidence commit requires its own CI confirmation.
- [ ] Human technical/peer review, PR approval, and merge authorization.

Submission reviewers must retain the stated limits: internal fraud diagnostics are not analyst exports; exact mode is not distributionally identical to stochastic mode; the 0.3% reference is not achieved; and no external banking-data validation has been performed.
