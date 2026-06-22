# Route Inventory

Current active baseline: **v0.102.3**

Current OpenAPI path count: `112`.

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
- `requires_auth_future`
- `blocked_from_production`

UAA-P1-080 classification adds a public/protected route inventory view using:

- `public_metadata`
- `local_readonly`
- `local_sensitive`
- `mutating_requires_authority`

This vocabulary is implemented in `/api/manifest` and the frozen route
inventory fixture. Current route metadata also exposes side-effect classes,
auth posture, and blocked-from-production posture.

Current route classification summary:

| Classification | Count |
|---|---:|
| `public_metadata` | 3 |
| `local_readonly` | 14 |
| `local_sensitive` | 82 |
| `mutating_requires_authority` | 13 |

Allowed current side-effect classes are:

- `none`
- `validation_only`
- `local_dev_workspace_only`
- `governed_network_read_only`

Production runtime side effects remain blocked unless an exact scoped milestone
grants reviewed authority and updates OpenAPI, route side-effect
classification, Foundation Gate checks, tests, docs, and rollback guidance.

Future UAA-P1-081 through UAA-P1-086 route inventory checks must record:
centralized security-header posture, explicit loopback CORS allowlist posture,
local bearer/session gate posture for sensitive routes, idempotency key or
scoped idempotency ref posture for mutating routes, targeted rate-limit posture
for expensive/sensitive paths, and enforcement coverage in OpenAPI/API manifest
tests. These checks are future work and add no middleware, auth, CORS, headers,
rate limits, dependencies, or runtime authority in this docs pass.

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
- `GET /control-center/morning-briefing/summary`
- `GET /control-center/storage/status`

These routes expose storage-backed Founder Loop v1 summaries for Today, Action
Inbox, Morning Briefing, and local storage status. They return safe refs,
bounded summaries, side-effect classes, evidence refs, blocked states, and
backup manifest refs only. They do not approve, run, send, install, enable,
dispatch, call providers, perform connector writes, read email/calendar data,
deliver notifications, or expose raw prompts, raw responses, raw paths, raw
logs, usernames, hostnames, environment dumps, credential material, or provider
payloads.

### Local model and runtime readiness

- local `/v1` model shell routes remain disabled by default and bearer-gated
- model-runtime validation and simulation routes remain validation/fallback only
- runtime readiness and smoke-report routes remain status/validation only

This is partial local auth coverage, not a general sensitive-route auth
boundary. UAA-P1-083 remains future work for logs/observability, task runs,
approvals, memory, file previews/proposals, model gateway behavior, action
previews, and sensitive runtime state.

### Task, file, tool, provider, memory, truth, approval, consent, cost, gate, and remote-worker groups

These groups keep their existing validation, preview, evaluate, dry-run,
summary, readiness, and local-dev scoped boundaries. Mutating local-dev paths
remain approval-bound and blocked from production authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
```
