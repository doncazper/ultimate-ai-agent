# API Boundary

The v0.15.1 API boundary is metadata-first, validation-first, approval-aware for local/dev policy checks, simulated/fallback-first for model runtime behavior, and readiness/status-only for M11 runtime readiness. It publishes the current OpenAPI schema and `/api/manifest` route inventory without adding cloud model calls, provider SDK calls, web fetching, browser automation, tokenizers, billing APIs, production auth, OAuth, private mesh networking, mobile sensor access, plugin enablement, or production persistence.

Use:

```bash
python scripts/export_openapi.py
python scripts/verify_openapi_contract.py
```

The export script writes JSON to stdout by default. Use `--output` only when an intentional artifact is needed.

M8 adds `/model-runtime/*` routes for manifest validation, request validation, response validation, and simulation. `/model-runtime/simulate` is a deterministic dry-run endpoint and must not call a live runtime.

M8.5 adds `/approvals/*` validation routes for local/dev approval request, grant, decision, and receipt contracts. These routes do not authenticate users, persist approvals, or perform external actions.

M9 adds `/model-runtime/local/*` validation and simulated fallback routes for local loopback endpoint policy checks. The public API does not expose default real loopback execution. Real local loopback execution remains a library-level dev-only path requiring explicit opt-in policy, validated approval, loopback endpoint policy, and injected transport. The current policy rejects hostile payloads such as non-loopback `allowed_hosts` or `deny_non_loopback=false` before adapter validation, while adapter-level non-loopback denial remains in depth.

M10 adds `/model-runtime/local/smoke/validate` for validation-only manual smoke readiness checks. The public API does not expose `/model-runtime/local/smoke/execute` or any other route that sends HTTP requests. The manual smoke script remains CLI-only, disabled by default, approval-gated, loopback-only, and fixed-prompt-only.

M10.5 adds `/remote-workers/*` validation, status, and dry-run routes for remote worker foundation metadata only. These routes do not dispatch jobs, open network connections, call private transport services, start listeners, launch remote subagents, execute remote tools, transfer files, approve actions, or perform write/send behavior. v0.14.3 keeps private mesh/tailnet taxonomy vendor-neutral and open-source-first: Headscale, generic WireGuard, Tailscale, private mesh, tailnet, and LAN transports are planned/disabled metadata only.

v0.14.4 adds future mobile API planning only. Future mobile control APIs, approval queue APIs, receipt viewer APIs, mobile capture inbox APIs, device registry APIs, and device capability manifest APIs are not implemented. Any future routes are subject to Device Capability Broker, Consent Ledger, Approval Authority, Event Ledger, Redaction, and Receipt rules.

v0.14.5 adds documentation integrity verification only. v0.14.6 adds Codex plugin/external tooling governance documentation only.

v0.15.0 adds `/runtime/readiness`, `/runtime/capability-matrix`, and `/runtime/smoke-reports/validate` as status/validation routes only. These routes do not execute, connect, dispatch, run provider calls, enable plugins, launch native builds, inspect live tool state, or make production readiness claims.

v0.15.1 adds no API routes. It clarifies that `local_loopback_policy` is supported validation-only and that `fake_manual_loopback_smoke` is an allowed fake/test report origin only.

API validation errors are sanitized before they are returned. FastAPI/Pydantic validation failures must not echo raw invalid input values or secret-like field values.
