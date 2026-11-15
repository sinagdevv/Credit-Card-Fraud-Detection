# D2 data quality report

## Controlled test-scale evidence

The 2026-11-15 controlled run with seed `20261115` produced 2,000 cardholders, 2,593 cards, 500 merchants, 327,062 transactions, and 3,495 sparse label rows. Its aggregate QA summary reported 950 internal fraud events, 3,268 investigated transactions, and 376 observed positives. The corresponding true-fraud prevalence was 0.2905% and review coverage was 0.9992%. These are scenario outcomes, not external banking benchmarks.

The generator validation completed before output writing; its allowlist protects ordinary exports from latent variables and row-level truth. The clean CI run validates the schema/test/notebook path. Exact named scale profiles, scenario comparisons, peak-memory measurements, and a 1M benchmark remain NOT VERIFIED.
