# PR integration review

Reviewed: 2026-11-16. This is a technical review, not peer approval.

## Relevant pull requests

| PR | State | Author / branch | Scope | Recommendation |
| --- | --- | --- | --- | --- |
| [#9](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/9) | merged | John Ray / `docs/sprint-01-setup` | Original D1 publication and repository layout | Historical baseline only; its D1 artifact is superseded by the D1 updates in #13. |
| [#10](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/10) | closed | Jee Daguman / `jee-branch` | D1 close-out corrections | Superseded by #13; do not merge separately. |
| [#13](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/13) | open at last remote check | Jee Daguman / `jee-branch` | D1 corrections and D2 generator | Preserve contribution; final human review remains required. |
| [#14](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/14) | open at last remote check | John Ray / `integration/sd008-complete` | Dependent exact-count, validation, D3, and QA integration | Keep open for review; do not merge without approval. |

## PR #13 evidence

- Source head reviewed: `5d3da0d8beddf8b46003355d09ef051c631455fd`; base at review: `868c21f87afdac20302bc305e5da888047128d85`.
- GitHub reports a clean, mergeable PR, but no status checks or reviews.
- The PR changes 39 files: D1 specification/DOCX/ERD, a D2 Python generator, 96 tests, configuration, and documentation. No tracked generated CSV/Parquet data, private keys, or credential-like secrets were found in the reviewed text files.
- `tools/validate_d1.py` passed all six checks, including DOCX checks, in the review environment.
- A controlled test-scale run completed with seed `20261115`: 2,000 cardholders, 2,593 cards, 500 merchants, 327,062 transactions, and 3,495 sparse label rows. The aggregate diagnostic reports 950 internal fraud events, 3,268 investigated events, and 376 observed positives. These are simulation outputs, not external benchmarks.
- The run manifest contains SHA-256 hashes and the analyst CSV exports omit the prohibited internal columns. The aggregate `label_gap_summary.csv` is the documented ground-truth-derived exception and contains no row-level identifiers.

## Resolved integration gaps and remaining blockers

1. **Resolved:** #14 adds named 10K, 150K, and 1M exact profiles; all three were measured. The 1M run completed in about 96 seconds at about 1.22 GiB observed process working set.
2. **Resolved:** D3 executed against a fresh exact BASELINE export and the clean Python 3.12 smoke workflow executes it.
3. **Resolved:** QA reports, calibration artifacts, scenario evidence, and aggregate stochastic-versus-exact evidence are present under `docs/qa/`.
4. **Remaining limitation:** exact mode's eight-seed mean fraud prevalence is 0.18517%, below the provisional 0.3% reference. No unverified tuning was applied; external calibration is NOT VERIFIED.
5. **Remaining review gate:** CI on the final evidence commit and human peer approval are still required. #13's historical co-author trailers are retained; no history rewrite is proposed.

## D1 reconciliation

The reviewed source still has the five required tables, 38 exported non-key features, 20 numbered relationships, seven prohibited latent drivers, and the `Y_true` / `R` / `Y_observed` separation. Its exported-table allowlist and internal-frame design support leakage-safe analyst data. The D1 technical contract is substantially implemented in D2, but D1 is technically review-ready rather than peer-approved.

## Integration decision

Keep #13 intact to preserve Jee's contribution. Complete follow-up work on `integration/sd008-complete`, then open one dependent integration PR targeting `main`. Do not merge #13 or close/move project work to Done without human review and verified CI.
