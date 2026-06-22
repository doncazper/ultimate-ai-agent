# Route Inventory

Current active baseline: **v0.102.3**

Current OpenAPI path count: `126`.

The API route inventory is generated from FastAPI route metadata and exposed by
`/api/manifest`. The manifest route count is the authoritative current count.
Historical release notes may preserve older route counts for audit history.

Each route declares:

- `path`
- `method`
- `operation_id`
- `tags`
- `summary`
- `validation_only`
- `side_effect_class`
- `route_classification`
- `auth_posture`
- `approval_posture`
- `idempotency_required`
- `idempotency_posture`
- `idempotency_policy_ref`
- `requires_auth_future`
- `blocked_from_production`

UAA-P1-080 classification adds a public/protected route inventory view using:

- `public_metadata`
- `local_readonly`
- `local_sensitive`
- `mutating_requires_authority`

This vocabulary is implemented in `/api/manifest` and the frozen route
inventory fixture. Current route metadata also exposes side-effect classes,
auth posture, approval posture, idempotency posture, rate-limit posture, and
blocked-from-production posture.

Current route classification summary:

| Classification | Count |
|---|---:|
| `public_metadata` | 3 |
| `local_readonly` | 14 |
| `local_sensitive` | 85 |
| `mutating_requires_authority` | 23 |

Allowed current side-effect classes are:

- `none`
- `validation_only`
- `local_dev_workspace_only`
- `governed_network_read_only`

Production runtime side effects remain blocked unless an exact scoped milestone
grants reviewed authority and updates OpenAPI, route side-effect
classification, Foundation Gate checks, tests, docs, and rollback guidance.

UAA-P1-081 implements centralized security-header posture for handled FastAPI
responses: `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`,
`Content-Security-Policy`, `Permissions-Policy`, and HTTPS-only
`Strict-Transport-Security`.

UAA-P1-082 implements explicit loopback CORS allowlist posture for local Control
Center dev/preview origins only: `http://localhost:5173`,
`http://127.0.0.1:5173`, `http://[::1]:5173`,
`http://localhost:4173`, `http://127.0.0.1:4173`, and
`http://[::1]:4173`. Wildcard CORS and CORS credentials remain denied, and CORS
does not grant auth or route authority.

UAA-P1-083 implements local protected-route bearer gate posture for non-public
route classifications. `GET /health`, `GET /version`, `GET /api/manifest`, and
`GET /openapi.json` remain public metadata; `local_readonly`,
`local_sensitive`, and `mutating_requires_authority` routes require the
configured local bearer when the gate is enabled. This is not enterprise auth,
OAuth, a password flow, production authority, or a public beta claim.

UAA-P1-084 implements mutating-route idempotency enforcement audit posture.
Routes classified as `mutating_requires_authority` now require
`X-UAA-Idempotency-Key` or `X-UAA-Idempotency-Ref` before the mutating handler
can run. `/api/manifest` and the frozen route inventory expose
`idempotency_required`, `idempotency_posture`, and `idempotency_policy_ref`.
This is not durable dedupe storage, exactly-once execution, replay execution,
mutation authority, production authority, or a public beta claim.

UAA-P1-085 implements targeted local fixed-window rate-limit posture for
model/chat, task decomposition, action preview/proposal, Action Inbox decisions,
Today-to-Action envelope promotion, Chat durable receipts/handoffs, Memory
Review decision receipts, and local model validation route groups.
`/api/manifest` and the frozen route inventory expose
`rate_limit_targeted`, `rate_limit_posture`, `rate_limit_policy_ref`, and
`rate_limit_group`. This is not auth, distributed quota, billing, production
authority, or a public beta claim.

UAA-P1-086 implements route inventory enforcement checks across OpenAPI,
`/api/manifest`, the frozen fixture, and the Control Center route-status
manifest. These checks add no new runtime authority.

FCC-V1-001 updates the frozen route inventory fixture to
`uaa-api-route-inventory.v4` and makes `auth_posture` plus `approval_posture`
manifest-visible for every route. Mutating routes must expose local bearer
auth posture, approval-before-mutation posture, idempotency posture, and
rate-limit posture before real Founder Loop mutation routes can land.
Duplicate replay behavior remains a route-owner contract; FCC-V1-002 implements
it for Action Inbox decision routes, FCC-V1-004 implements it for Chat
receipt/handoff routes, and FCC-V1-005 implements it for Memory Review decision
receipt routes.

## Current route groups

### System and API metadata

- `GET /health`
- `GET /version`
- `GET /api/manifest`

These routes expose status and route metadata only.

### Governed web evidence

- `GET /web-evidence/status`
- `POST /web-evidence/request`

UAA-P1-063 exposes operator-visible governed web evidence status and a bounded
request envelope for allowlisted HTTPS GET evidence. The request path returns
receipt refs and bounded redacted previews only. It does not add unrestricted
browsing, browser automation, request bodies, caller-supplied headers, session
state, credential material, redirects, downloads, raw page/body storage, raw
header storage, provider calls, context injection, memory writes,
shell/subprocess behavior, plugin execution, hidden network access, or
production authority. OpenWebUI remains a shell; UAA owns the guardrail.

### Observability

- `GET /observability/session-events`
- `POST /observability/client-errors`

These routes expose bounded redacted summaries only. They do not expose raw log
records, request bodies, response bodies, prompts, provider payloads, terminal
output, credential material, external telemetry, production authority,
background monitoring, or process control.

### Extension catalog

- `GET /extensions/catalog`

This route returns read-only inspectable extension catalog metadata with safe
refs. It is separate from any callable catalog and does not install, import,
enable, activate, revoke, execute, fetch, or mutate extensions.

### Mattermost agent rooms

- `GET /integrations/mattermost/status`
- `GET /integrations/mattermost/roles/catalog`
- `POST /integrations/mattermost/roles/suggest`
- `POST /integrations/mattermost/roles/bind`
- `POST /integrations/mattermost/roles/unbind`
- `POST /integrations/mattermost/events/message`
- `GET /integrations/mattermost/audit`
- `GET /integrations/mattermost/receipts`

These routes are disabled-by-default local bridge surfaces for UAA-managed
Mattermost agent room roles. They expose safe refs, bounded previews, receipt
refs, audit summaries, and reply-command proposals only. They do not persist raw
transcripts, manage credentials or cookies, treat model output as authority, or
perform unapproved connector writes.

### Control Center setup assistant

- `GET /control-center/setup-assistant/summary`

This route returns the existing deterministic macOS Setup Assistant dry-run
plan and approval-envelope metadata for read-only inspection. Dry-run
approval-envelope hardening validates proposed setup action metadata only. It
does not capture approval grants, create receipts or audit records, run
installer actions, execute shell commands, download models, install/load/start
LaunchAgents, install/load/start background services, handle credentials, claim
signed installer readiness, claim public distribution, claim production
readiness, or execute rollback.

### Control Center Founder Loop summaries

- `GET /control-center/today/summary`
- `GET /control-center/actions/inbox`
- `POST /control-center/actions/{action_id}/approve`
- `POST /control-center/actions/{action_id}/edit`
- `POST /control-center/actions/{action_id}/reject`
- `POST /control-center/actions/{action_id}/defer`
- `GET /control-center/actions/{action_id}/receipt`
- `GET /control-center/morning-briefing/summary`
- `GET /control-center/storage/status`

These routes expose storage-backed Founder Loop v1 summaries for Today, Action
Inbox, Morning Briefing, local storage status, and Action Inbox decision
receipts. The decision routes record backend-owned approve/edit/reject/defer
state, validate exact approval scope for approve where required, handle
idempotency replay/conflict locally, and return safe receipt refs. They do not
execute the underlying action, run, send, install, enable, dispatch, call
providers, perform connector writes, read email/calendar data, write memory,
run shell/subprocess work, deliver notifications, or expose raw prompts, raw
responses, raw paths, raw logs, usernames, hostnames, environment dumps,
credential material, or provider payloads.

### Local model and runtime readiness

- local `/v1` model shell routes remain disabled by default and bearer-gated
- model-runtime validation and simulation routes remain validation/fallback only
- runtime readiness and smoke-report routes remain status/validation only

UAA-P1-083 adds the general local protected-route bearer gate around the
current non-public route classifications. Local `/v1` and task-decomposition
routes can still keep their narrower disabled-by-default bearer gates; P1-083
does not grant execution, provider, connector, or production authority.

### Task, file, tool, provider, memory, truth, approval, consent, cost, gate, and remote-worker groups

These groups keep their existing validation, preview, evaluate, dry-run,
summary, readiness, and local-dev scoped boundaries. Mutating local-dev paths
remain approval-bound and blocked from production authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_boundary_enforcement.py
.venv/bin/python scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
```
