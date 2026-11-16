# SD-008 Deliverable 1 Team Review Record

## Review objective

John Ray owns completion and technical QA of Deliverable 1. Jee performs a bounded team review rather than carrying the remaining drafting workload. Philippine card-specific parameters remain explicit open calibration items for Deliverable 2; they do not block submitting this specification as a documented scenario model.

## D1 literature verification

- [ ] Spot-check the reference metadata and contextual limits recorded in the evidence matrix.
- [ ] Check author order, year, title, venue, pages, DOI, and URL in APA 7 style.
- [ ] Confirm the BSP digital-payment shares (57.4% volume, 59.0% value for 2024; 64.7% volume for 2025) are described only as retail-payment digitalization.
- [ ] Seek Philippine credit-card evidence for amount, channel, MCC, fraud-type, and label-delay distributions.
- [ ] Mark each evidence-matrix row SUPPORTED, CALIBRATED, ASSUMED, or OPEN.

## D1 distribution review

- [ ] Review gamma-Poisson arrivals, lognormal mixtures, beta propensities, Markov compromise states, and logistic outcomes.
- [ ] Check whether provisional ranges can generate impossible or implausible combinations.
- [ ] Approve or replace the PHP 5,000-2,000,000 credit-limit and PHP 500,000 transaction caps.
- [ ] Review the sensitivity ranges and recommend calibration benchmarks.

## D1 schema review

- [ ] Confirm the five tables, keys, cardinalities, nullable rules, and closed vocabularies.
- [ ] Recount 38 exported non-key analytical features.
- [ ] Trace each feature through the ERD, equations, dictionary, and generation contract.
- [x] Verify latent variables and true fraud are absent from analyst-facing exports.
- [x] Decide the negative-label maturation policy and whether declined attempts are learner-visible.

## D1 final team review

- [x] Confirm every OPEN item is either resolved or explicitly deferred to D2 calibration.
- [ ] Review all 20 formal relationships for causal ordering and ambiguity.
- [x] Confirm rolling features use only prior events.
- [ ] Inspect the rendered Word document for equations, tables, ERD readability, and page breaks. (Not done in Word; a LibreOffice render was inspected. See D1-TECHNICAL-QA.md.)
- [x] Record approval, requested revisions, or rejection with reasons.
- [x] Only after acceptance, authorize issue completion and final submission.

## Issue status

Issues #1 to #8 and the close-out issue #11 were closed by Jee on 2026-11-08. D1-08 (peer review) was closed in solo mode. Latent-variable absence and prior-only rolling features were also verified on generated data in D2 (see [Deliverable 2 QA](../qa/D2-TECHNICAL-QA.md)).

## Next-deliverable responsibilities

The detailed division for Deliverables 2 and 3 is maintained in `docs/project/TEAM-WORKFLOW.md`. D2 is implemented and ready for review (issue #12); D3 has not started.

## Sign-off record

Reviewer: Jee  
Decision: Accepted (D1 issues closed on the board, solo review)  
Date: 2026-11-08  
Required revisions: None blocking; cosmetic DOCX items listed in D1-TECHNICAL-QA.md
