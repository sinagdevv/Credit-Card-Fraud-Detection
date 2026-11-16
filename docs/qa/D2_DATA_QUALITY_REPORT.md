# D2 data quality report

Reviewed: 2026-11-16. Results below are simulation diagnostics, not validation against Philippine banking data.

## Exact-count method

The original generator retains its stochastic Gamma--Poisson arrival process. Named profiles condition a sampled Gamma-mixed cardholder-day intensity field on a requested global count and allocate events with a multinomial draw. Ineligible cardholder-days have zero allocation probability. This preserves intensity heterogeneity and the requested total, but changes unconditional daily-count dependence. Fraud states and mechanism attributes are still generated before labels; exact mode deliberately prevents a fraud burst from expanding beyond the allocated event budget. That is a limitation, not a claim of equivalence to stochastic mode.

## Measured profile evidence

| Profile | Transactions | Cardholders | Cards | Merchants | Labels | Internal fraud | Investigated | Observed positives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SMALL | 10,000 | 2,000 | not retained separately | 500 | 132 | 13 | 130 | 4 |
| BASELINE | 150,000 | 2,000 | 2,613 | 500 | 1,567 | 278 | 1,503 | 117 |
| STRESS | 1,000,000 | 2,000 | 2,613 | 500 | 10,438 | 1,947 | 9,990 | 755 |

All three completed generator validation before export, including five-table schema checks, PK/FK integrity, timestamp bounds, category validation, and latent/internal-column exclusion. The 1M run used Windows 11 / Python 3.13.2, completed in about 96 seconds, had a peak external process working set of 1,306,980,352 bytes (about 1.22 GiB), and wrote 220,617,588 bytes (about 210 MiB). Working set is a process-memory measure, not full-system memory.

## Calibration and scenarios

Persisted aggregate-only artifacts in `docs/qa/evidence/calibration/` cover eight independent exact BASELINE seeds (`20261101`--`20261108`). Mean internal fraud prevalence was 0.18517%, median 0.18633%, SD 0.01080 percentage points, range 0.16733%--0.20133%, and the seed-level 95% t interval was 0.17614%--0.19419%. This is 0.11483 percentage points below the provisional 0.3% reference. Eight seeds are the Monte Carlo units; transaction-level binomial intervals would be inappropriate because fraud is clustered. The evidence supports undercalibration relative to that configured reference, but does not isolate its cause or justify parameter tuning.

Matched exact-150K scenarios (seed `20261101`) were:

| Scenario | Parameter change | Internal fraud | Investigated | Observed positives | Label rows |
| --- | --- | ---: | ---: | ---: | ---: |
| BASELINE | none | 278 | 1,503 | 117 | 1,567 |
| HIGH_FRAUD_PRESSURE | `compromise_initiation`: -5.5 to -4.5 | 318 | 1,503 | 146 | 1,575 |
| STRICT_REVIEW_BUDGET | `review_coverage`: 1% to 0.5% | 278 | 772 | 104 | 840 |

The strict-budget transaction CSV SHA-256 matched the baseline transaction CSV exactly, so the review policy did not alter analyst-facing transactions. Labels may exceed investigations because D1 permits customer reports independent of analyst review. Per-transaction internal-state equality was not separately persisted and is therefore **NOT VERIFIED**. These are single-seed scenario demonstrations, not uncertainty-qualified effect estimates.

## Stochastic versus exact evidence

Three seeds (`20261101`--`20261103`) are persisted under `docs/qa/evidence/mode_comparison/`. Mean stochastic output was 319,706 transactions with 0.28208% internal fraud, 1.0000% review coverage, daily variance 33,903, and card activity CV 0.7998. Exact BASELINE output was 150,000 transactions with 0.19356% internal fraud, 1.0024% review coverage, daily variance 7,434, and card activity CV 0.8060. Stochastic burst events totalled 1,217 of 2,705 fraud events; exact bursts totalled 124 of 871. The modes also differ in total exposure, so this descriptive comparison associates fixed-count conditioning and the burst budget with lower prevalence; it does not prove either is the sole cause. Amount-distribution comparison is **NOT VERIFIED** by this aggregate-only runner.

## Remaining limitations

- The provisional 0.3% reference is not achieved by exact mode and is not externally calibrated.
- Exact conditioning changes the unconditional arrival distribution and limits burst expansion.
- Analyst exports intentionally omit `Y_true`; internal rates above are QA-only.
- Synthetic plausibility and successful internal checks do not establish production or geographic realism.
