# D2 data quality report

## Controlled test-scale evidence

The 2026-11-15 controlled run with seed `20261115` produced 2,000 cardholders, 2,593 cards, 500 merchants, 327,062 transactions, and 3,495 sparse label rows. Its aggregate QA summary reported 950 internal fraud events, 3,268 investigated transactions, and 376 observed positives. The corresponding true-fraud prevalence was 0.2905% and review coverage was 0.9992%. These are scenario outcomes, not external banking benchmarks.

The generator validation completed before output writing; its allowlist protects ordinary exports from latent variables and row-level truth. The clean CI run validates the schema/test/notebook path. Exact named scale profiles, scenario comparisons, peak-memory measurements, and a 1M benchmark remain NOT VERIFIED.

## Conditional exact-count evidence

Exact mode draws Gamma-mixed cardholder-day intensities and conditions independent Poisson arrivals on the requested total by a multinomial allocation. It therefore preserves the configured intensity heterogeneity but changes the unconditional daily-count distribution. In exact mode burst-labelled events retain mechanism-specific attributes but do not expand the fixed event budget; this is a documented conditioning compromise.

| Profile | Transactions | Cardholders | Cards | Merchants | Labels | Internal fraud | Investigated | Observed positives |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SMALL | 10,000 | 2,000 | not separately retained | 500 | 132 | 13 | 130 | 4 |
| BASELINE | 150,000 | 2,000 | 2,613 | 500 | 1,567 | 278 | 1,503 | 117 |

The BASELINE prevalence was 0.1853% and review coverage 1.0020%; rare-event variation is expected under the configured mechanism. STRESS, scenario experiments, peak-memory capture, and repeated-seed reproducibility are NOT VERIFIED.
