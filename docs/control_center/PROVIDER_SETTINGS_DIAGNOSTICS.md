# Provider And Settings Diagnostics

Status: implemented readable diagnostics, local/dev read-only

Provider and Settings diagnostics make provider failure states readable in
Control Center without granting provider/model, billing, credential, router, or
Settings mutation authority.

The backend-owned read model lives in
`ProviderCredentialReadinessSummary.provider_settings_diagnostics`, exposed
through `GET /control-center/dashboard` and inspected through:

- `scripts/inspect_settings_authority_posture.py`
- `scripts/inspect_provider_credential_readiness.py`
- `scripts/inspect_provider_credential_validation_lane.py`
- `scripts/inspect_provider_router_dry_run.py`
- `scripts/inspect_tiny_provider_invocation_lane.py`

The diagnostic state vocabulary is:

- `configured`
- `missing`
- `blocked`
- `degraded`
- `revoked`
- `expired`
- `cost_blocked`
- `disabled`
- `future_scoped`

Current default provider rows are missing credential refs. CostGovernor posture
is cost-blocked. Credential enrollment, provider credential validation, and the
tiny exact-approved provider lane are disabled by default. Credential vault and
provider router dry-run remain future-scoped. These labels are readable
operator posture only.

Non-goals:

- No provider SDK calls.
- No provider/model invocation.
- No credential collection or secret reveal.
- No broad provider router execution.
- No billing authority toggle.
- No background or autonomous provider calls.
- No Settings mutation or authority toggle.
- No raw prompt, response, provider payload, credential, log, or path
  persistence.
- No public beta, public release, production readiness, or production
  authority claim.

Any future promotion must add exact provider/model refs, exact credential refs,
CostGovernor hard limits, exact approval binding, redacted receipts, actual
usage/cost receipt handling, revocation, audit/replay, UI/CLI parity, and
safe-disable or rollback posture before runtime authority is considered.
