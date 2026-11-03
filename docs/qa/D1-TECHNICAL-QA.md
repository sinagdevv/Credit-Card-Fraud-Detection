# SD-008 Deliverable 1 Technical QA

Validated on 1 November 2026 against the Markdown source and the Microsoft Word rendering.

| Test | Result | Evidence or limitation |
|---|---|---|
| Required Sections 1-12 | PASS | All numbered sections present in source and DOCX |
| Appendices A-G | PASS | All seven appendices present |
| Five normalized tables | PASS | cardholders, cards, merchants, transactions, fraud_labels |
| At least 20 meaningful features | PASS | 38 non-key exported features |
| Every exported feature documented | PASS | 38 rows include type, constraints, nullability, generation, dependencies, and evidence |
| Formal equations defined | PASS | 20 numbered structural relationships |
| Parameter registry | PASS | Scenario, calibration, state, mechanism, review, and reproducibility parameters registered |
| Seven latent drivers | PASS | Distribution, level, lifetime, descendants, role, and exclusion rule documented |
| Primary/foreign-key design | PASS | PK/FK fields, relationships, and cardinalities are consistent across ERD and dictionary |
| Row-level foreign-key integrity | NOT VERIFIED | Deliverable 2 has not generated data |
| ERD consistency | PASS | Five entities and four relationships match schema |
| Sampling order | PASS (revised 3 Nov 2026) | Category, channel, merchant order fixed; Y_true retention precedes rolling features, authorization, review and Y_observed |
| Future-feature leakage controls | PASS | Rolling fields use j less than k and update after event finalization |
| Ground truth versus observed labels | PASS (revised 3 Nov 2026) | Separate definitions and export rules; D3 comparison uses the aggregate `label_gap_summary.csv` only |
| Unsupported statistics classified | PASS | Philippine contextual statistics are excluded from prevalence calibration |
| APA reference/citation audit | PASS | 18 used references; metadata and DOI/URL fields checked against available sources |
| DOCX opens | PASS | Opened and exported through Microsoft Word |
| Visual QA | PASS | 27 rendered pages inspected; no clipping, overlap, broken tables, orphaned headings, or unreadable ERD |
| Same-seed dataset reproducibility | NOT VERIFIED | Requires Deliverable 2 implementation |
| Distributional plausibility on generated data | NOT VERIFIED | Requires Deliverable 2 output |
| Spec revision consistency checks | PASS | `tools/validate_d1.py`: counts, citations, equation numbering, dictionary rows, parameter registry |
| DOCX rebuilt from revised spec | PARTIAL | Rebuilt 3 Nov with `tools/build_d1_document.py`; `validate_d1.py` docx checks pass. Word open and page-by-page visual QA have not been re-run on the rebuilt file |

The document is a submission candidate. Remaining open parameters are declared calibration work, not unreported evidence gaps.
