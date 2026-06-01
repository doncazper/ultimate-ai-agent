# Route Inventory

The API route inventory is generated from FastAPI route metadata and exposed by `/api/manifest`.

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

Allowed side-effect classes in v0.14.4 are:

- `none`
- `validation_only`
- `local_dev_workspace_only`

Production runtime side effects are not allowed in this milestone.

M8 route group:

- `/model-runtime/manifests/validate`
- `/model-runtime/requests/validate`
- `/model-runtime/responses/validate`
- `/model-runtime/simulate`

These routes validate metadata and produce simulated responses only.

M8.5 approval route group:

- `/approvals/requests/validate`
- `/approvals/grants/validate`
- `/approvals/validate`
- `/approvals/receipts/validate`

These routes validate local/dev approval authority contracts only. They do not provide production auth, OAuth, persistence, or external execution.

M9 local loopback route group:

- `/model-runtime/local/endpoints/validate`
- `/model-runtime/local/execution/validate`
- `/model-runtime/local/simulate-fallback`

These routes validate local loopback policy and provide simulated fallback only. They do not expose a public real loopback execution endpoint and must not accept arbitrary local or remote URLs.

M10 manual smoke validation route:

- `/model-runtime/local/smoke/validate`

This route validates manual smoke readiness only. It never sends HTTP requests and there is no public smoke execute route.

M10.5 remote worker foundation route group:

- `/remote-workers/nodes/validate`
- `/remote-workers/transports/validate`
- `/remote-workers/policy/validate`
- `/remote-workers/jobs/validate`
- `/remote-workers/dry-run`
- `/remote-workers/status`
- `/remote-workers/tailnet/status`
- `/remote-workers/mesh/status`

These routes validate remote worker metadata, return static planned status, or produce dry-run-only results. They never dispatch jobs, call live networking, call private transport services, start listeners, launch remote subagents, execute tools, transfer files, perform write/send behavior, or approve actions. v0.14.3 route metadata treats Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN as planned/disabled metadata only; no connect, login, config, dispatch, or execute endpoint exists.

Invalid payload responses are sanitized and must not include raw invalid input values.

Future mobile API planning:

- future mobile control APIs.
- future approval queue APIs.
- future receipt viewer APIs.
- future mobile capture inbox APIs.
- future device registry APIs.
- future device capability manifest APIs.

These routes are not implemented in v0.14.4. Future mobile routes are subject to Device Capability Broker, Consent Ledger, Approval Authority, Event Ledger, Redaction, and Receipt rules. No current route performs mobile pairing, sensor access, OS permission integration, background service work, mobile network calls, or autonomous mobile actions.

v0.14.5 documentation integrity adds no route. v0.14.6 Codex plugin governance adds no route and no plugin enablement endpoint. The OpenAPI path count should remain unchanged except for `info.version`.
