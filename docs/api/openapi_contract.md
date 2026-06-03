# OpenAPI Contract

v0.28.0 preserves the FastAPI OpenAPI boundary and documents the current route contract without adding public real execution routes. M24 Memory Provider Abstraction + Local Memory Store adds no backend API route; OpenAPI path count remains `74`.

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
- v0.17.0 adds a local Web Control Center frontend shell only. v0.17.1 and v0.17.2 add frontend verification hardening only. v0.17.3 cleans up release documentation labels. v0.17.4 adds local browser smoke UX polish and reporting docs only. v0.17.5 freezes roadmap milestone charters only. v0.18.0 adds M14 frontend-only local backend connection stabilization. v0.18.1 hardens that frontend-only connection safety. v0.18.2 adds design governance docs only. v0.18.3 adds OpenWebUI/CCC strategy docs only. v0.18.4 adds post-M20 roadmap projection docs only. v0.19.0 adds M15 frontend-only approval, receipt, and event viewer UI. v0.19.1 hardens M15 frontend-only approval/receipt UI safety. v0.20.0 adds M16 frontend-only event timeline and run/receipt trace viewer UI. v0.20.1 hardens M16 trace/redaction safety only. v0.21.0 adds M17 frontend-only evidence, file ref, and memory ref summary viewers. v0.21.1 hardens M17 frontend-only safety only. v0.21.2 normalizes developer commands only. v0.22.0 adds M18 frontend-only local runtime status and manual smoke report validation surfaces only. v0.22.1 cleans roadmap labels only. v0.23.0 adds M19 Mobile Companion Contract/API Planning only, and v0.23.1 hardens that contract/docs boundary only. v0.24.0 adds M20 Device Capability Broker Contract only, and v0.24.1 hardens that contract/docs boundary only. v0.25.0 adds M21 OpenWebUI Bridge + Chat Shell Integration Contract only, and v0.25.1 hardens that contract boundary only. v0.26.0 adds M22 Local Model Runtime Activation Contract only, and v0.26.1 hardens that contract boundary only. v0.27.0 adds M23 manual/CLI-only fixed-prompt local call support, and v0.27.1 hardens that boundary only. v0.28.0 adds M24 memory provider/local store contracts and local-dev storage only. Backend path count remains `74`; only `info.version` changes to the active package version.

Verification:

```bash
.venv/bin/python scripts/verify_openapi_contract.py
```

Export:

```bash
.venv/bin/python scripts/export_openapi.py
.venv/bin/python scripts/export_openapi.py --output /tmp/openapi_v0_28_0.json
```

The second command is only for intentional versioned snapshots.
