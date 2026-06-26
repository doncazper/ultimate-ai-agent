# Provider Catalog + Cost Literacy

Status: active contract/read-model lane.

`GET /control-center/providers/setup-guide` exposes backend-owned provider setup
and cost-literacy metadata for Setup Assistant, Settings, and Models surfaces.
The first slice is read-only guidance only.

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

Product language rules:

- Provider guidance is not credential enrollment.
- Pricing guidance is not billing authority.
- Provider docs links are reviewed metadata, not runtime fetches.
- Provider output is never product truth or authority.
- Catalog visibility does not mean callable runtime authority.

Future UI milestones may render the same backend-owned read model in Setup
Assistant, Settings, and Models, but those surfaces must not add credential
inputs, key capture, provider validation, provider tests, provider connection
flows, or model calls without a separate scoped authority lane.

