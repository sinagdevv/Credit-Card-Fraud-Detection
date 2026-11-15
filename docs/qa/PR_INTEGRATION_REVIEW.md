# PR integration review

Reviewed: 2026-11-15. This is a technical review, not peer approval.

## Relevant pull requests

| PR | State | Author / branch | Scope | Recommendation |
| --- | --- | --- | --- | --- |
| [#9](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/9) | merged | John Ray / `docs/sprint-01-setup` | Original D1 publication and repository layout | Historical baseline only; its D1 artifact is superseded by the D1 updates in #13. |
| [#10](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/10) | closed | Jee Daguman / `jee-branch` | D1 close-out corrections | Superseded by #13; do not merge separately. |
| [#13](https://github.com/sinagdevv/Credit-Card-Fraud-Detection/pull/13) | open | Jee Daguman / `jee-branch` | D1 corrections and D2 generator | Preserve contribution; do not merge until the blockers below are resolved and D3 is supplied. |

## PR #13 evidence

- Source head reviewed: `5d3da0d8beddf8b46003355d09ef051c631455fd`; base at review: `868c21f87afdac20302bc305e5da888047128d85`.
- GitHub reports a clean, mergeable PR, but no status checks or reviews.
- The PR changes 39 files: D1 specification/DOCX/ERD, a D2 Python generator, 96 tests, configuration, and documentation. No tracked generated CSV/Parquet data, private keys, or credential-like secrets were found in the reviewed text files.
- `tools/validate_d1.py` passed all six checks, including DOCX checks, in the review environment.
- A controlled test-scale run completed with seed `20261115`: 2,000 cardholders, 2,593 cards, 500 merchants, 327,062 transactions, and 3,495 sparse label rows. The aggregate diagnostic reports 950 internal fraud events, 3,268 investigated events, and 376 observed positives. These are simulation outputs, not external benchmarks.
- The run manifest contains SHA-256 hashes and the analyst CSV exports omit the prohibited internal columns. The aggregate `label_gap_summary.csv` is the documented ground-truth-derived exception and contains no row-level identifiers.

## Problems and blockers

1. **D3 is missing.** The requested executable analyst-facing notebook, case studies, visualizations, and incomplete-label narrative are not present.
2. **The configured scales do not meet the requested contract.** #13 offers only `test` and `target`; it does not provide named 10K, 150K, and 1M transaction scenarios or evidence for a 1M run.
3. **The requested CI smoke workflow, end-to-end command, D2 report, realism scorecard, and final checklist are absent.**
4. **Cross-platform test issue found.** `tests/test_d2_labels_generate.py::test_cli_smoke` used a POSIX path split. The integration branch changes it to `Path(...).parent.parent`. On this isolated embedded-Python harness the subprocess additionally ignores its current working directory, so that one test remains environment-blocked; the preceding 95 tests pass with an explicit writable pytest base directory. A standard Python installation must run the full suite before merge.
5. **Claims require refresh.** The PR description's 96-pass and target-scale assertions were not reproduced here. The local validation above is a distinct test-scale run; peak-memory and 1M performance remain NOT VERIFIED.
6. **Process hygiene.** PR #13 carries AI co-author trailers from prior commits. No history rewrite is proposed; future commits in this integration branch will not add them.

## D1 reconciliation

The reviewed source still has the five required tables, 38 exported non-key features, 20 numbered relationships, seven prohibited latent drivers, and the `Y_true` / `R` / `Y_observed` separation. Its exported-table allowlist and internal-frame design support leakage-safe analyst data. The D1 technical contract is substantially implemented in D2, but D1 is technically review-ready rather than peer-approved.

## Integration decision

Keep #13 intact to preserve Jee's contribution. Complete follow-up work on `integration/sd008-complete`, then open one dependent integration PR targeting `main`. Do not merge #13 or close/move project work to Done without human review and verified CI.
