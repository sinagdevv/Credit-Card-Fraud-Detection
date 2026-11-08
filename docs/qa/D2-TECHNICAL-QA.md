# SD-008 Deliverable 2 Technical QA

Verified on 8 November 2026 (issue #12) on the generator in `deliverables/D2_Synthetic_Dataset_Generator/`. Target scale: 5,000 cardholders, 1,250 merchants, 2026-01-01 to 2026-06-30, seed 20261101.

| Test | Result | Evidence or limitation |
|---|---|---|
| Unit and integration tests | PASS | `pytest tests -q`: 96 passed, also 96 in reverse file order, with DeprecationWarnings as errors |
| Target-scale run | PASS | 6,566 cards, 814,118 transactions, 8,704 fraud_labels; runtime about 75 s |
| True fraud rate vs r_f = 0.003 | PASS | 0.002928, inside the binomial 95% interval [0.002881, 0.003119]; seeds 20261101-03 were all inside before the alert-weight change |
| Review share | PASS | Investigated share 0.010006 against the 1% cap |
| Review yield and coverage | INFO | Investigated-fraud yield 5.24%; 17.9% of true fraud investigated; observed-label recall 932/2384 = 0.391 |
| Label gap | INFO | 28 false confirmations; 282 pending |
| End-of-window effect | INFO | Observed fraud by month 179, 178, 170, 154, 157, 122; last month is lower as expected |
| Validation rules (Section 8.1) | PASS | All 8 checks: keys, temporal, vocabularies, amounts, labels, no_prohibited, nulls, rolling_features |
| Exported features | PASS | 38 non-key features; no prohibited (latent) columns |
| Manifest | PASS | sha256 hashes match the files |
| Same-seed reproducibility | PASS | Byte-identical files |
| Different-seed behavior | PASS | Files differ |
| Fraud requires a mechanism | PASS | No y_true with mechanism none |
| Notebook | PASS | Executes headless (about 33 s at test size); committed notebook has no outputs |

## Limitations and open items

- Alert-signal ceiling of about 7% investigated-fraud yield with the current observable signals.
- Distance is concentrated on the nearest far or foreign merchant.
- Card blocking and reissue are not simulated.
- OPEN vocabularies (age and income bands, regions, MCC mapping, holidays) are placeholders.
- `requirements.txt` is not version-pinned.
- Config values are approved v0 scenario assumptions, not calibration evidence. Alert weights were changed with user approval: theta_z 0.25, theta_v 1.2, theta_F 1.6, theta_d 1.6, logistic noise s 0.25 (s is not in the registry).
- Microsoft Word check of the D1 DOCX not done (see [Deliverable 1 QA](D1-TECHNICAL-QA.md)).
