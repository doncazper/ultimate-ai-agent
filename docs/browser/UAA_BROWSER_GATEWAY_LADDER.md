# UAA Browser Gateway Ladder

Status: Browser Gateway Ladder plus injected observe-only adapter, no live browser authority

This ladder defines how UAA can talk about future browser capability promotion
without turning browser metadata, model output, provider output, or Control
Center state into authority. The current implemented slice is only an injected
observe-only adapter that converts an already-supplied local/test observation
into redacted safe refs through `WebAccessGateway`.

It adds no live web fetching, no browser execution, no browser observe runtime,
no dry-run execution, no clicks, no forms, no authentication, no cookies, no
downloads, no uploads, no POST/PUT/PATCH/DELETE behavior, no connector writes,
no provider/model calls, no runtime activation, no public beta, and no
production authority.

## Ladder States

| State | Meaning | Current posture |
|---|---|---|
| `declared` | Browser capability is named as a future boundary. | Metadata only. |
| `discovered` | Browser capability metadata can be inspected as untrusted data. | Metadata only. |
| `metadata_only` | Imported browser capability candidates remain UAA-owned metadata. | Metadata only. |
| `observe_planned` | Live observe posture can be described for a later scoped milestone. | Planned, not live. |
| `observe_blocked` | Live observe remains blocked until a later accepted promotion. | Blocked. Injected local/test observations can be redacted into safe refs only. |
| `action_dry_run_planned` | A browser action dry-run can be represented as a reviewable plan. | Planned, not executable. |
| `action_dry_run_blocked` | Dry-run cannot execute clicks, forms, auth, uploads, or downloads. | Blocked. |
| `exact_approved_low_risk_action_planned` | Low-risk browser action execution is future work after exact approval proof. | Planned, not executable. |
| `high_risk_action_blocked` | High-risk browser actions remain blocked. | Blocked. |
| `auth_cookie_download_upload_blocked` | Auth, cookies, downloads, and uploads remain blocked. | Blocked. |
| `mutation_blocked` | Public-web mutations and non-GET style actions remain blocked. | Blocked. |
| `runtime_disabled` | Browser runtime activation is disabled by default. | Blocked. |

Unknown browser capability metadata is blocked and review-required. Unknown does not mean read-only.

## Required Contract Shape

Every browser capability record must stay behind the Python Agent Core and
WebAccessGateway boundary. A valid record uses safe refs for:

- browser intent metadata
- observe posture
- action dry-run posture
- risk class
- blocked authority refs
- audit refs
- replay refs
- redacted evidence refs
- page/source refs
- policy decision refs
- future exact approval refs
- revocation refs
- safe-disable refs

The contract lives in
`src/ultimate_ai_agent/core/web_access/browser_gateway_ladder.py`.

## Approval Binding Is Not Execution

The Browser Gateway Ladder includes an exact approval-binding contract so a
future lane can prove that an approval ref matches the exact browser intent,
action plan, policy decision, scope, receipt, expiry, and revocation refs.

That match still does not authorize live browser execution in this lane.
Execution remains blocked until a later accepted milestone adds a UAA-owned
broker, exact policy gates, durable receipts, rollback/safe-disable posture,
and focused tests for the precise browser operation.

Model output, provider output, remote metadata, memory recall, plugin metadata,
or Control Center React state cannot authorize browser work.

## Blocked Authority

These authority categories remain blocked:

- live web fetch outside WebAccessGateway
- live browser observe runtime
- live browser execution
- browser clicks
- form filling or submission
- auth, cookies, and authenticated profiles
- downloads and uploads
- non-GET public-web mutations
- raw page, raw DOM, raw HTML, screenshot, or provider payload persistence
- direct browser automation imports or calls
- provider/model calls
- connector writes
- runtime activation from UI, model output, provider output, or metadata

Blocked attempts must record safe refs and redacted summaries only. They must
not persist raw page payloads or treat page content as instructions.

## Promotion Relationship

The Browser Gateway Ladder uses the shared Capability Promotion Ladder in
`docs/tooling/CAPABILITY_PROMOTION_LADDER.md` model:

Declared -> Discovered -> Imported as UAA Capability Candidate -> Classified
-> Preview/Dry-run -> Policy checked -> Exact approval bound -> Broker-invoked
-> Receipted -> Replayable -> Revocable

The current PR covers declared, discovered, metadata-only, planned, and blocked
contract posture. It does not promote broker invocation.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_browser_gateway_ladder.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_access_gateway.py tests/test_web_access_static_guards.py tests/test_web_runtime_authority_contract.py
.venv/bin/python scripts/verify_browser_gateway_ladder.py
```

These checks fail if the ladder states drift, browser observe or dry-run become
execution, clicks/forms/auth/cookies/downloads/uploads/mutations become
allowed, raw page payloads are accepted, direct browser automation source
fragments appear in the new contract module, or model/provider/UI state is
treated as browser authority.
