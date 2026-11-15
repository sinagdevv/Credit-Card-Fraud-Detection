# Synthetic realism scorecard

Reviewed: 2026-11-15. `PASS` means the stated diagnostic was observed in the controlled test-scale run; it is not evidence of equivalence to production Philippine banking data.

| Category | Diagnostic | Expected behavior | Result | Status / limitation |
| --- | --- | --- | --- | --- |
| Structural validity | Export allowlist, manifest, D1 validator | Five normalized tables and no latent columns | Observed in generated manifest and validation | PASS |
| Temporal consistency | Generator's prior-event feature validator | No future events in rolling features | Covered by generator validation/tests; no independent adversarial fixture rerun | NOT VERIFIED |
| Fraud mechanism coherence | Internal `mechanism` drives true fraud before observation | Fraud not produced by exported-label flipping | Implemented and test-scale run produced 950 internal events | PASS, model-based |
| Class imbalance | Aggregate gap summary | Rare fraud relative to all events | 950 / 327,062 = 0.2905% | PASS, scenario assumption |
| Label observation bias | Review and aggregate label gap | Sparse reviewed labels differ from population truth | 3,268 investigated and 376 observed positives | PASS, simulated |
| Latent exclusion | CSV headers and prohibited-name validation | No latent/internal state in analyst tables | Observed | PASS |
| Reproducibility | Same-seed byte hashes | Identical logical files | Test exists; independent repeat not yet completed | NOT VERIFIED |
| Scenario responsiveness | Baseline vs pressure vs review-budget run | Causal parameters change outcomes | Required scenarios absent | FAIL |
| Scalability | 10K, 150K, 1M benchmarks | Measured duration and memory | Only 327,062-row controlled run completed; no peak-memory capture | NOT VERIFIED |
| Analyst usefulness | Executed D3 notebook | Clear denominators and incomplete-label analysis | D3 notebook absent | FAIL |

The scorecard intentionally has no weighted composite score: its categories answer different questions and the available evidence does not justify a single number.
