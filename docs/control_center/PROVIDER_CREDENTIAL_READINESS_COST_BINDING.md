# Provider Credential Readiness + Cost Governor Binding

Status: active contract/read-model lane.

Provider credential readiness is backend-owned posture metadata in the Control
Center dashboard read model. It is inspectable through
`scripts/inspect_provider_credential_readiness.py` and rendered in Setup,
Settings, Models, and Action Inbox only as safe refs and blockers.

This lane grants no credential validation, no provider SDK calls, no model
invocation, no billing authority, no spend authority, and no callable runtime
authority.
Non-goal summary: no billing authority and no callable runtime authority.

Implemented posture:

- `ProviderCredentialReadinessPosture` defines `configured`,
  `not_configured`, `revoked`, `blocked`, `validation_blocked`,
  `invocation_blocked`, `vault_blocked`, `cost_blocked`, and
  `unknown_paid_cost_requires_approval`.
- `ProviderCostGovernorBinding` binds provider/model safe refs to cost estimate
  refs, budget decision refs, max-approved USD refs, future receipt refs, and
  `core.costs.CostGovernor` posture/decision refs.
- Unknown paid cost requires explicit approval. Estimated cost above budget
  blocks use. Missing provider/model refs block use. No route or surface may
  claim provider usage without future usage and cost receipt refs.
- Provider rows are `not_configured` by default and carry blocked posture for
  validation, invocation, vault storage, CostGovernor binding, and unknown paid
  cost approval.

Blocked by this lane:

- secret entry
- recoverable credential storage
- secret resolution
- credential validation from readiness posture
- provider SDK calls
- model invocation (no model invocation from readiness posture)
- runtime pricing fetch
- billing authority
- provider output authority
- callable runtime authority

Product language rules:

- A configured/not-configured/revoked provider posture is metadata only.
- CostGovernor binding refs are blockers and review scope, not spend authority.
- A max-approved USD ref is a future approval-scope ref, not a payment grant.
- Receipt refs are required before any future provider usage claim.
- Provider catalog visibility, credential readiness visibility, and provider
  diagnostics do not make providers callable.

Credential Vault Contract Shell is a metadata-only contract layer. Credential
Vault Backend V1 adds only a local safe-ref ledger for enroll/revoke/rotation
posture. It still must not expose secret resolution, validate provider
credentials, call provider SDKs, invoke models, or make providers callable.
The exact-approved provider credential validation lane is a separate,
AuthorityLease-gated one-provider redacted-receipt validation boundary and still
does not make providers callable. The Exact-Approved Provider Invocation
Promotion Plan does not make providers callable.
