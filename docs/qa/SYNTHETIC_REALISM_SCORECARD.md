# Synthetic realism scorecard

Reviewed: 2026-11-16. `PASS` means the stated simulation diagnostic was measured; it does not establish equivalence to production banking data.

| Category | Measured diagnostic | Result | Status / limitation |
| --- | --- | --- | --- |
| Structural validity | Five exports passed generator validation; latent/internal columns excluded | PK/FK and schema checks pass before export | PASS |
| Temporal consistency | Existing chronological-feature tests and CI smoke | History features are prior-event only | PASS, implementation/test evidence |
| Fraud mechanism coherence | Fraud created internally before review labels | High-pressure scenario increased fraud 278 to 318 through `compromise_initiation` | PASS |
| Class imbalance | Eight exact 150K seeds | Mean internal prevalence 0.18517% | PASS as configured outcome; below provisional 0.3% reference |
| Label observation bias | Exact BASELINE | 1,503 investigations and 117 observed positives among 150,000 transactions | PASS, simulated selection process |
| Latent exclusion | Export allowlist and validation | No row-level truth or latent columns in analyst exports | PASS |
| Reproducibility | Fixed seed, hashes, CI smoke | Exact profile output and strict-review transaction hash reproduced | PASS; internal-state digest not persisted |
| Scenario responsiveness | Matched 150K seed | High pressure and review budget changed intended mechanisms/policy | PASS; one-seed evidence |
| Scalability | Default STRESS profile | 1M transactions in about 96s; 1.22 GiB working set | PASS on measured Windows environment |
| Analyst usefulness | Executed D3 exact BASELINE | 20.24s, analyst-facing tables only, incomplete-label narrative retained | PASS |
| External realism | Comparison to real banking data | No such calibration dataset or benchmark was used | NOT VERIFIED |

The scorecard intentionally has no weighted composite score: structural correctness, internal plausibility, and external realism are different claims.
