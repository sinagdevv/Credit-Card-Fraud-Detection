# SD-008 Deliverable 1 Technical QA

First validated on 1 November 2026; revised for the close-out on 8 November 2026 (issue #11, commit b54744f) against the Markdown source and a LibreOffice rendering of the rebuilt DOCX. The rebuilt DOCX has not been opened in Microsoft Word.

| Test | Result | Evidence or limitation |
|---|---|---|
| Required Sections 1-12 | PASS | All numbered sections present in source and DOCX |
| Appendices A-G | PASS | All seven appendices present |
| Five normalized tables | PASS | cardholders, cards, merchants, transactions, fraud_labels |
| At least 20 meaningful features | PASS | 38 non-key exported features |
| Every exported feature documented | PASS | 38 rows include type, constraints, nullability, generation, dependencies, and evidence |
| Formal equations defined | PASS | 20 numbered structural relationships; literal equation numbers in the DOCX |
| Parameter registry | PASS | Scenario, calibration, state, mechanism, review, and reproducibility parameters registered |
| Seven latent drivers | PASS | Distribution, level, lifetime, descendants, role, and exclusion rule documented |
| Primary/foreign-key design | PASS | PK/FK fields, relationships, and cardinalities are consistent across ERD and dictionary |
| Row-level foreign-key integrity | PASS (D2) | Verified on generated data; see [Deliverable 2 QA](D2-TECHNICAL-QA.md) |
| ERD consistency | PASS | Five entities and four relationships match schema |
| Sampling order | PASS (revised 3 Nov 2026) | Category, channel, merchant order fixed; Y_true retention precedes rolling features, authorization, review and Y_observed |
| Future-feature leakage controls | PASS | Rolling fields use j less than k and update after event finalization |
| Ground truth versus observed labels | PASS (revised 3 Nov 2026) | Separate definitions and export rules; D3 comparison uses the aggregate `label_gap_summary.csv` only |
| Unsupported statistics classified | PASS | Philippine contextual statistics are excluded from prevalence calibration |
| APA reference/citation audit | PASS | 18 used references; metadata and DOI/URL fields checked against available sources |
| DOCX opens | PARTIAL | Opens and renders in LibreOffice (8 Nov). Microsoft Word check not done |
| Visual QA | PARTIAL | Rebuilt DOCX is 23 pages; inspected in a LibreOffice render only. Known cosmetic leftovers: equation 14a prints before 14; a few plain underscores or stray ^ in formulas; some half-empty pages |
| Same-seed dataset reproducibility | PASS (D2) | Byte-identical files; see [Deliverable 2 QA](D2-TECHNICAL-QA.md) |
| Distributional plausibility on generated data | PARTIAL (D2) | Fraud rate, review share and label gap checked; OPEN vocabularies remain placeholders. See [Deliverable 2 QA](D2-TECHNICAL-QA.md) |
| Spec revision consistency checks | PASS | `tools/validate_d1.py`: counts, citations, equation numbering, dictionary rows, parameter registry |
| DOCX rebuilt from revised spec | PASS | Rebuilt 8 Nov with `tools/build_d1_document.py`; `tools/validate_d1.py` 6/6 PASS including docx checks, with regression checks for equation numbers and leftover markup. Word open not re-run |
| Close-out spec decisions (#11) | PASS | Per-card sampling order; declined attempts exported; negative-label maturation deferred to D3; alert_ts at 23:59:59 of the transaction day; card_status constant `active`; label_source analyst/customer; entry_mode lookup with p_token; fraud_type cnp/ato/burst/merchant_compromise |
| D2-driven spec changes (#12) | PASS | Employment depends on age only; fraud requires an active mechanism (Eq 16, bisection over all opportunities); region-tier distances; merchant_compromise flavor at CNP-episode start; non-fraud bursts discarded; card validity; review capacity round(r_r x daily count); end-of-window rule; false-confirmation fraud_type by channel; Gamma shape/scale; delays in log-hours; spend_deviation_z null with fewer than 3 prior; missingness rules |

D1 is complete and closed on the board (2026-11-08). Remaining open parameters are declared calibration work, not unreported evidence gaps. Open: Word check of the DOCX and the cosmetic items above.
