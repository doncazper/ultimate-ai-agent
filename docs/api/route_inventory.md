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

Allowed side-effect classes in v0.14.2 are:

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

These routes validate remote worker metadata, return static planned status, or produce dry-run-only results. They never dispatch jobs, call live networking, call private transport services, start listeners, launch remote subagents, execute tools, transfer files, perform write/send behavior, or approve actions. Unsupported `remote_tailnet_enabled=true` and `remote_personal_data_enabled=true` policy inputs are rejected, and remote-worker API wrapper payloads reject unexpected top-level fields.

Invalid payload responses are sanitized and must not include raw invalid input values.
