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
| STRESS | 1,000,000 | 2,000 | 2,613 | 500 | 10,438 | 1,947 | 9,990 | 755 |

The BASELINE prevalence was 0.1853% and review coverage 1.0020%; the STRESS prevalence was 0.1947% and review coverage 0.9990%. Rare-event and clustered-mechanism variation is expected, but the apparent undercalibration needs repeated-seed analysis before any parameter change.

The default-population STRESS run completed on Windows 11 with Python 3.13.2 in approximately 96 seconds (wall-clock inferred from process start and atomic output completion). Peak process working set observed externally was 1,306,980,352 bytes (about 1.22 GiB); all CSV/manifest output totalled 220,617,588 bytes (about 210 MiB). The monitor captures process working set rather than a full-system memory profile. Scenario experiments, repeated-seed calibration, and exact-profile D3 execution remain NOT VERIFIED.
