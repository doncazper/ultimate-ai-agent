# Autonomy Risk Classifier Contracts

M68 defines deterministic risk classifier records for review only.

## Request Contract

An Autonomy Risk Classification request contains:

- `classification_request_ref`
- exact scoped approval bundle
- exact Revocation + Kill Switch record
- caller-declared risk
- explicit risk signals
- actor, resource, capability, allowlist, bundle, revocation-record, source
  scope, audit, and replay refs

The request is contract-only and review-only. It cannot activate policy, start
sessions, run autonomous actions, run background workers, execute, write memory,
inject context, call models/providers as authority, add routes, or grant
production authority.

## Decision Contract

An Autonomy Risk Classification decision contains:

- `classification_request_ref`
- declared risk class
- derived risk class
- stable reason codes
- safe summary
- exact binding refs copied from the validated request

The derived risk class is the highest risk from declared risk, scoped approval
bundle risk, and risk signals. Risk downgrade is denied. Approval refs are
identifiers only and cannot authorize classification, execution, activation, or
production authority. Risk downgrade denied is enforced at evaluator
boundaries.

Evaluator boundaries revalidate the current object fields and do not trust
constructor-time validation alone.
