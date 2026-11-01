# SD-008 Credit Card Fraud Detection

SD-008 is an Eskwelabs Innovation Fellowship Data Innovation Track project that specifies, generates, and analyzes privacy-preserving synthetic credit-card transaction data. The intended user is a fraud analyst evaluating transaction behavior, fraud mechanisms, operational alerts, and incomplete investigation outcomes without exposing real cardholder records.

## Project objective

The project establishes a reproducible analytical dataset in a Philippine banking context. Philippine payment-adoption and cyber-fraud reports provide context, but the model does not treat retail-payment adoption, scam exposure, suspected digital fraud, or reported loss shares as direct credit-card fraud probabilities.

The synthetic system uses five normalized tables:

1. `cardholders`
2. `cards`
3. `merchants`
4. `transactions`
5. `fraud_labels`

The model generates latent spending, travel, compromise, and merchant-risk states before their observable descendants. Latent drivers are excluded from published tables. Fraud ground truth is kept distinct from investigation selection and delayed analyst-observed labels, and rolling behavioral features use only strictly prior transactions.

## Deliverables

- [Deliverable 1: Model Research and Specifications](deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx) — completed submission candidate with the research basis, schema, ERD, distributions, structural equations, calibration plan, and data dictionary.
- [Deliverable 2: Synthetic Dataset Generator](deliverables/D2_Synthetic_Dataset_Generator/README.md) — planned generator implementation and validation contract.
- [Deliverable 3: Exploratory Data Analysis](deliverables/D3_Exploratory_Data_Analysis/README.md) — planned descriptive and fraud-focused analysis.

The accessible source specification is available in [Markdown](docs/modeling/SD-008_MODEL_SPECIFICATION.md). Technical verification evidence is recorded in [Deliverable 1 QA](docs/qa/D1-TECHNICAL-QA.md).

## Privacy and analytical principles

- No real customer, card, merchant, or transaction records are used.
- Synthetic identifiers have no mapping to real identities.
- Latent variables guide generation but are not exported as analyst features.
- Ground truth and analyst-observed labels remain separate to represent selective review and delayed outcomes.
- Time-dependent features are computed without future information.
- Scenario parameters and research-backed evidence are explicitly distinguished.

## Repository structure

```text
deliverables/
  D1_Model_Research_and_Specifications/
  D2_Synthetic_Dataset_Generator/
  D3_Exploratory_Data_Analysis/
docs/
  handoff/
  modeling/
  project/
  qa/
  sprints/
tests/
tools/
```

Start with the [project scope](docs/project/PROJECT-SCOPE.md), [deliverables map](docs/project/DELIVERABLES.md), and [team workflow](docs/project/TEAM-WORKFLOW.md). Sprint status and planned work are documented under [`docs/sprints`](docs/sprints/).

## Progress

| Deliverable | Status | Current gate |
|---|---|---|
| D1 Model Research and Specifications | Ready for team review | Final peer acceptance is pending |
| D2 Synthetic Dataset Generator | Planned | Implementation has not started |
| D3 Exploratory Data Analysis | Planned | Requires an accepted D2 dataset |

