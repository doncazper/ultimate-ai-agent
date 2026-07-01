# Provider Catalog + Cost Literacy

Status: active contract/read-model lane.

`GET /control-center/providers/setup-guide` exposes backend-owned provider setup
and cost-literacy metadata for Setup Assistant, Settings, and Models surfaces.
The first slice is read-only guidance only.

Provider Credential Readiness + Cost Governor Binding extends this posture in
the existing Control Center dashboard read model and through
`scripts/inspect_provider_credential_readiness.py`. It does not add a new
provider route, credential form, validation call, provider SDK call, model
invocation, billing authority, or runtime pricing fetch.

Implemented posture:

- `ProviderCatalog`, `ProviderSetupCard`, `ProviderKeyInstruction`,
  `ProviderCostProfile`, `ProviderSourceRef`, `ProviderAuthorityPosture`,
  `TokenCostExample`, and `BudgetPosture` are typed Python/Pydantic contracts.
- Provider entries include provider class, reviewed setup/docs/pricing links,
  env-var style labels, billing prerequisite, token/cost notes, authority
  posture, `last_verified_at`, `pricing_may_change: true`, and
  `not_billing_authority: true`.
- Metadata is reviewed, static, timestamped, and inspectable through
  `scripts/inspect_provider_setup_guide.py`.
- Unknown paid provider cost requires explicit approval, cost estimate refs,
  budget decision refs, provider/model refs, max approved USD, and receipt refs
  before any later provider use.
- Credential readiness rows can show `configured`, `not_configured`, `revoked`,
  `blocked`, `validation_blocked`, `invocation_blocked`, `vault_blocked`,
  `cost_blocked`, and `unknown_paid_cost_requires_approval`, but those states
  are metadata and blockers only.
- CostGovernor binding refs are safe refs for cost estimate, budget decision,
  max-approved USD, future receipt, provider/model, and CostGovernor
  decision/posture scope. They do not authorize spend or provider invocation.

Blocked by this lane:

- credential input
- raw key storage
- credential vault storage
- provider credential validation
- provider SDK calls
- model invocation
- automatic pricing fetch
- runtime web fetching for provider docs
- provider response or exchange persistence
- provider output as product truth or authority
- provider setup guidance as billing authority
- credential readiness as provider authority
- CostGovernor binding as billing authority
- unknown paid provider cost without explicit approval
- provider usage claims without usage and cost receipt refs

Product language rules:

- Provider guidance is not credential enrollment.
- Pricing guidance is not billing authority.
- Provider docs links are reviewed metadata, not runtime fetches.
- Provider output is never product truth or authority.
- Catalog visibility does not mean callable runtime authority.
- Credential readiness visibility does not mean secret entry, credential
  validation, provider connection, or provider invocation authority.
- Cost posture belongs inside approval scope; it is not side metadata and does
  not grant authority merely by existing as a ref.

Future UI milestones may render the same backend-owned read model in Setup
Assistant, Settings, and Models, but those surfaces must not add credential
inputs, key capture, provider validation, provider tests, provider connection
flows, or model calls without a separate scoped authority lane.
