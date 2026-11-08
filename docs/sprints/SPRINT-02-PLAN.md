# Sprint 2 Plan: Synthetic Dataset Generator

## Goal

Implement and validate the Deliverable 2 generator described in its [implementation contract](../../deliverables/D2_Synthetic_Dataset_Generator/README.md).

## Ownership

John Ray owns generator architecture, mathematical implementation, fraud-event simulation, performance, scalability, integration, and final technical review. Jee owns statistical QA, distribution tests, key integrity, missingness and outlier checks, imbalance verification, reproducibility tests, and validation documentation.

## Sequence

1. Freeze the D1 parameter registry and generator configuration.
2. Implement deterministic entities, states, transactions, fraud mechanisms, and labels.
3. Export the five-table schema without latent variables.
4. Add schema, integrity, reproducibility, leakage, and distribution tests.
5. Measure performance at the agreed scale.
6. Complete cross-review and document limitations.

Status: implemented and verified; ready for review (issue #12). Evidence is in [Deliverable 2 QA](../qa/D2-TECHNICAL-QA.md). Cross-review is pending.

