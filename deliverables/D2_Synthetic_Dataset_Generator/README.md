# Deliverable 2: Synthetic Dataset Generator

## Objective

Convert the approved Deliverable 1 mathematical specification into a scalable synthetic credit-card dataset for fraud analysis, through a reproducible Python package driven by a Jupyter notebook.

Status: implemented and verified; ready for review (issue #12). Evidence is in [Deliverable 2 QA](../../docs/qa/D2-TECHNICAL-QA.md).

## Required output

The generator must export the five normalized tables defined in Deliverable 1: `cardholders`, `cards`, `merchants`, `transactions`, and `fraud_labels`. Dataset size must be configurable without changing the model, and a deterministic master seed must reproduce the same output under the documented runtime and configuration. In addition, it must write the aggregate `label_gap_summary.csv` defined in Section 6.1 of the D1 specification; D3 uses it for ground-truth comparisons and never loads row-level ground truth.

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

## Contents

- `sd008_gen/` package: `config` (refuses unapproved values; named RNG streams entities, events, fraud, review, pilot), `entities`, `events` (daily states, arrivals, per-card chronological loop, beta0 bisection on a full-window pilot, 2 refinements, common random numbers), `labels` (daily top-score review capped at 1%, noisy outcomes, customer reports, end-of-window), `export` (allowlist, prohibited-name check, atomic write, manifest with sha256), `validate` (Section 8.1 rules including rolling-feature recomputation), `generate` (single entry point and CLI; validates before writing).
- `config/scenario_v0.yaml`: 70 parameters. All are user-approved v0 scenario assumptions, not calibration evidence. Vocabularies that the specification leaves OPEN (age and income bands, regions, MCC mapping, holidays) are placeholder proposals marked OPEN.
- `D2_Synthetic_Dataset_Generator.ipynb`: thin driver, saved without outputs. Set `SCALE` to exactly `"test"` or `"target"` (nothing else is accepted) and run all. It reuses an existing run folder.

## How to run

Setup from the repository root (Python 3.13 was used):

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

Notebook: open `D2_Synthetic_Dataset_Generator.ipynb`, set `SCALE` to exactly `"test"` or `"target"`, run all.

CLI, from this directory:

```bash
../../.venv/bin/python -m sd008_gen.generate --config config/scenario_v0.yaml --out outputs --scale target
```

Options: `--scale test|target`, `--seed N`, `--out DIR`. The CLI refuses to overwrite an existing run.

Outputs go to the gitignored `outputs/run_<seed>_<config-hash>/`: `cardholders`, `cards`, `merchants`, `transactions`, `fraud_labels`, `label_gap_summary.csv`, and `manifest.json`.

To change values, edit the YAML. Any `approved: false` entry blocks the run. A validation failure writes nothing.

Tests, from the repository root: `.venv/bin/python -m pytest tests -q`.

## Known limitations

- Alert-signal ceiling: about 7% investigated-fraud yield with the current observable signals (5.24% at target scale).
- Distance is concentrated on the nearest far or foreign merchant.
- Card blocking and reissue are not simulated.
- OPEN vocabularies are placeholders; `requirements.txt` is not version-pinned yet.
- Logistic noise s (0.25) is not in the parameter registry.

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

