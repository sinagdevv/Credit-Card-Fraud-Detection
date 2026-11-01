# Deliverable 2: Synthetic Dataset Generator

## Objective

Implement a reproducible Jupyter notebook that converts the approved Deliverable 1 mathematical specification into a scalable synthetic credit-card dataset for fraud analysis. Implementation has not started.

## Required output

The generator must export the five normalized tables defined in Deliverable 1: `cardholders`, `cards`, `merchants`, `transactions`, and `fraud_labels`. Dataset size must be configurable without changing the model, and a deterministic master seed must reproduce the same output under the documented runtime and configuration.

The notebook must implement the registered distributions, structural equations, fraud episodes, selective investigation process, delayed observed labels, and strictly prior rolling features. Account takeover, card-not-present compromise, travel, merchant vulnerability, transaction velocity, geography, and amount effects must follow the documented causal sampling order.

Latent spending propensity, exposure, travel propensity, merchant vulnerability, compromise states, and travel states must never appear in exported analytical tables. Exported features may contain only permitted observable descendants and documented labels.

## Validation requirements

- Schema, type, nullability, uniqueness, range, and category validation
- Primary-key uniqueness and foreign-key integrity across all five tables
- Deterministic same-seed tests and documented different-seed behavior
- Distribution and conditional-dependence checks against the parameter registry
- Missingness, timestamp ordering, extreme-value, and outlier checks
- Fraud imbalance, concentration, mechanism, and observed-label-gap checks
- Leakage tests for every rolling or historical feature
- Batch-size and runtime measurements for the agreed target scale

## Responsibilities

### John Ray

- Generator architecture and configuration contract
- Mathematical implementation and deterministic random streams
- Fraud-event and observation-process simulation
- Performance, scalability, integration, and final technical review

### Jee

- Statistical distribution and synthetic-data quality assurance
- Primary-key, foreign-key, schema, and cardinality validation
- Missingness, outlier, timestamp, and fraud-imbalance checks
- Reproducibility testing and validation documentation

## Definition of Done

- The notebook runs from a clean documented environment without manual cell repair.
- A configuration controls scale and seed.
- All five tables are generated with the approved schema and no exported latent variables.
- Automated checks pass for schema, relationships, reproducibility, leakage, and required distributions.
- Performance at the agreed dataset size is measured and acceptable.
- John and Jee complete cross-review, with limitations and unresolved calibration decisions documented.

