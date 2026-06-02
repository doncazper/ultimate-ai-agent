# OpenAPI Contract

v0.18.0 preserves the FastAPI OpenAPI boundary and documents the current route contract without adding public real execution routes.

Contract rules:

- `info.version` must match `ultimate_ai_agent.__version__`.
- Every API operation must have a unique stable `operationId`.
- Routes must be grouped with tags.
- `/api/manifest` must be present.
- Forbidden runtime routes for cloud model invocation, provider invocation, web fetches, browser automation, scanner runtimes, direct tool execution, arbitrary URL execution, and runtime config loading must be absent.
- M9 local loopback routes may validate endpoints, validate execution policy, and produce simulated fallback responses only.
- M10 manual smoke routes may validate fixed-prompt smoke readiness only. Public smoke execution routes are forbidden.
- M10.5 remote worker routes may validate metadata, return static status, and produce dry-run results only. Public remote dispatch, execution, and subagent launch routes are forbidden.
- v0.14.4 mobile/device APIs are future planning only and no mobile/device routes are implemented.
- v0.14.5 documentation integrity adds no API route.
- v0.14.6 Codex plugin governance adds no API route and no plugin enablement route.
- v0.15.0 runtime readiness adds three status/validation routes only and no execute, run, connect, dispatch, provider-call, plugin-enable, native-build, or smoke-execute route.
- v0.15.1 adds no route and only clarifies runtime readiness taxonomy.
- v0.16.0 Control Center routes are read-only/preview-only and no `/control-center/actions/execute`, `/control-center/plugins/enable`, `/control-center/runtime/execute`, `/control-center/remote-workers/dispatch`, `/control-center/mobile/sensors`, or `/control-center/frontend` route exists.
- v0.17.0 adds a local Web Control Center frontend shell only. v0.17.1 and v0.17.2 add frontend verification hardening only. v0.17.3 cleans up release documentation labels. v0.17.4 adds local browser smoke UX polish and reporting docs only. v0.17.5 freezes roadmap milestone charters only. v0.18.0 adds M14 frontend-only local backend connection stabilization. Backend path count remains `74`; only `info.version` changes to the active package version.

Verification:

```bash
python scripts/verify_openapi_contract.py
```

Export:

```bash
python scripts/export_openapi.py
python scripts/export_openapi.py --output docs/api/openapi_v0_18_0.json
```

The second command is only for intentional versioned snapshots.
