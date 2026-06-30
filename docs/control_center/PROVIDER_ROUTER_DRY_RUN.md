# Provider Router Dry-Run

Status: proposal-only provider routing posture; no provider execution authority.

Provider Router Dry-Run adds a backend-owned proposal contract for explaining
which provider refs are exact-approval candidates, blocked, degraded, cost-risky,
validation-required, or missing authority for a future exact-approved provider
use lane. It reads local Provider Credential Readiness and CostGovernor posture
only.

The lane is inspectable through
`POST /control-center/providers/router/dry-run` and
`scripts/inspect_provider_router_dry_run.py`. Inputs are safe task/model refs
only. Outputs include safe provider refs, missing credential refs, cost-risky
refs, validation-required refs, no-authority refs, and a recommended exact
approval scope ref.

This lane does not invoke providers, execute fallback, perform network calls,
call provider SDKs, validate credentials, call models, grant billing authority,
run background work, persist raw prompts, persist raw responses, or persist raw
provider payloads. Visibility in the dashboard or API manifest is metadata and
proposal posture only; it is not callable runtime authority.

Broad and unbounded multi-provider fallback remains blocked. Exact-approved
two-provider fallback now lives in the separate
`docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md` lane, where each
attempt must carry its own approval, CostGovernor decision, budget scope,
idempotency ref, receipt refs, and safe-disable posture. Router dry-run
visibility remains proposal-only and cannot execute fallback by itself.
