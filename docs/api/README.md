# API Boundary

The v0.29.1 API boundary is metadata-first, validation-first, approval-aware for local/dev policy checks, simulated/fallback-first for model runtime behavior, readiness/status-only for M11 runtime readiness, read-only/preview-only for M12/M13 Control Center contracts, and unchanged in backend path count through M25 Truth Source Router + Evidence Claim Checker hardening. It publishes the current OpenAPI schema and `/api/manifest` route inventory without adding cloud model calls, provider SDK calls, web fetching, source fetching, browser automation, tokenizers, billing APIs, production auth, OAuth, private mesh networking, mobile sensor access, plugin enablement, backend frontend-tool control routes, runtime execution, manual smoke execution, OpenWebUI integration, native CCC routes, design-tool integration, post-M20 execution routes, approval execution routes, receipt/event mutation routes, timeline backend routes, trace backend routes, evidence raw routes, truth verification routes, claim verification routes, file content/write/delete routes, memory raw/write/delete/learn/forget/import/ingest/vector-search/embed/inject routes, filesystem browse routes, observability export routes, context injection, vector DB, embeddings, cloud memory providers, or production persistence.

Use:

```bash
.venv/bin/python scripts/export_openapi.py
.venv/bin/python scripts/verify_openapi_contract.py
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

v0.16.0 adds `/control-center/*` backend contract routes for manifest, dashboard, status, route inventory summary, approval summary, runtime-readiness summary, Foundation Gate summary, and action preview. These routes are read-only or preview-only. They do not execute actions, grant approvals, enable plugins, start runtimes, call models/providers, dispatch remote workers, access mobile sensors, run frontend tooling, or create a production Control Center.

v0.17.0 adds a local Web Control Center frontend shell only. It adds no backend API route. v0.17.1 and v0.17.2 harden the frontend safety and verification path only. v0.17.3 cleans up release documentation labels. v0.17.4 polishes local browser smoke reviewability and reporting only. v0.17.5 freezes roadmap milestone charters only.

v0.18.1 hardens M14 local backend connection safety in the frontend shell only. It keeps local-only API base validation, visible live/degraded/mock fallback states, and explicit unknown/checking state copy. It adds no backend API route and no M15 approval queue, receipt, or event viewer route. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.18.2 adds Open Design System and UI Design Governance documentation only. It adds no backend API route and no M15 approval queue, receipt, or event viewer route.

v0.18.3 adds OpenWebUI and CCC Client Strategy documentation only. It adds no backend API route, OpenWebUI bridge route, native CCC route, Android route, iOS route, macOS route, mobile sensor route, OS permission route, or M15 approval queue, receipt, or event viewer route. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.18.4 adds post-M20 roadmap projection and M21-M40 capability-layer charters only. It adds no backend API route, OpenWebUI bridge route, local model execution route, memory provider route, truth/evidence expansion route, sandbox/tool execution route, MCP/Agent Skills/AGENTS.md runtime route, CCC native route, device pairing route, Device Capability Broker route, mobile capture route, sensor route, browser automation route, observability export route, eval harness route, or M15 approval queue, receipt, or event viewer route. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.19.0 implements M15 Approval Queue + Receipt/Event Viewer UI in the frontend only. It adds no backend API route, approval execution route, approval grant/reject mutation route, receipt mutation route, event mutation route, raw event route, raw memory route, raw file route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.19.1 hardens M15 Approval/Receipt UI safety in the frontend, static verifier, tests, and Foundation Gate only. It adds no backend API route, approval execution route, approval grant/reject mutation route, receipt mutation route, event mutation route, M16 Event Timeline + Run/Receipt Trace Viewer route, raw event route, raw memory route, raw file route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.20.0 implements M16 Event Timeline + Run/Receipt Trace Viewer in the frontend only. It adds no backend API route, timeline route, trace route, observability export route, OpenTelemetry export route, approval execution route, tool execution route, raw event route, raw memory route, raw file route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.20.1 hardens M16 trace/redaction safety in frontend tests, static verifiers, docs, and Foundation Gate only. It adds no backend API route, timeline route, trace route, raw event route, telemetry export route, observability export route, approval execution route, tool execution route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, M17 Evidence/File/Memory Viewer route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.21.0 implements M17 Evidence/File/Memory Viewer in the frontend only. It adds no backend API route, evidence raw route, file content route, file write/delete route, filesystem browse route, memory raw route, memory write/delete/learn/forget route, approval execution route, tool execution route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, vector DB route, embedding route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.21.1 hardens M17 Evidence/File/Memory Viewer safety in frontend tests, static verifiers, docs, browser-smoke reviewability, and Foundation Gate only. It adds no M18 route, backend API route, evidence raw route, file content/write/delete route, filesystem browse route, memory raw/write/delete/learn/forget route, embedding route, vector DB route, memory provider route, runtime execution route, model/provider route, remote dispatch route, mobile sensor route, plugin enablement route, native build route, auth route, analytics route, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.21.2 normalizes developer environment commands in repo-local tooling and docs only. It adds no backend API route, M18 route, runtime route, frontend behavior route, model/provider route, network route, mobile/native route, browser/computer-use route, plugin route, dependency, or production capability. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.22.0 implements M18 Local Runtime Status + Manual Smoke Control Surface in the frontend only. It adds no backend API route, runtime execution route, manual smoke execution route, model/provider route, remote execution route, mobile sensor route, plugin enablement route, OpenWebUI integration route, raw smoke report route, raw prompt route, raw response route, credential route, local runtime provider route, dependency, or production Control Center authority. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.23.0 implements M19 Mobile Companion Contract/API Planning only, and v0.23.1 hardens M19 roadmap/mobile contract safety only. These releases add no backend API route, mobile app route, sensor route, OS permission route, device pairing runtime route, approval execution route, runtime execution route, dependency, or production authority. OpenAPI path count remains `74`; only `info.version` changes.

v0.24.0 implements M20 Device Capability Broker Contract only, and v0.24.1 hardens M20 safety only. These releases add no backend API route, sensor route, native client route, OS permission route, pairing route, runtime execution route, model/provider route, dependency, or production authority. OpenAPI path count remains `74`; only `info.version` changes.

v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration Contract only, and v0.25.1 hardens M21 safety only. These releases add no OpenWebUI integration route, deployment/config route, plugin/function/tool route, backend API route, frontend behavior route, runtime execution route, model/provider route, memory write route, file access route, dependency, or production authority. OpenAPI path count remains `74`; only `info.version` changes.

v0.26.0 implements M22 Local Model Runtime Activation Contract only, and v0.26.1 hardens M22 safety only. These releases add no backend API route, runtime activation route, endpoint probe route, local LLM call route, model/provider route, tool execution route, memory write route, file write route, dependency, or production authority. OpenAPI path count remains `74`; only `info.version` changes.

v0.27.0 implements M23 First Real Local LLM Call as manual/CLI-only, loopback-only, fixed-prompt-only, approval-gated, non-tool, and non-authoritative, and v0.27.1 hardens M23 safety only. These releases add no backend API route, runtime activation route, endpoint probe route, arbitrary prompt route, user-content model call route, OpenWebUI runtime route, Control Center execution route, tool execution route, memory write route, file write route, dependency, or production authority. OpenAPI path count remains `74`; only `info.version` changes.

v0.28.0 implements M24 Memory Provider Abstraction + Local Memory Store as governed, reviewed-write-only local memory foundation. It adds no backend API route, memory mutation route, raw memory route, memory import/ingest route, vector-search route, embedding route, context injection route, runtime execution route, model/provider route, OpenWebUI memory write route, Control Center memory mutation route, mobile capture route, tool output write route, cloud memory provider route, dependency, production persistence, or M25 claim verification route. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.28.1 repairs the M24 public memory request contract and hardens M24 safety tests/docs only. v0.28.2 removes a duplicate/conflicting roadmap row only. It adds no backend API route, memory mutation route, raw memory route, memory import/ingest route, vector-search route, embedding route, context injection route, runtime execution route, model/provider route, OpenWebUI memory write route, Control Center memory mutation route, mobile capture route, tool output write route, cloud memory provider route, dependency, production persistence, or M25 claim verification route. OpenAPI path count remains `74`; only `info.version` changes to the active package version.

v0.29.0 implements M25 Truth Source Router + Evidence Claim Checker as
deterministic local contracts over explicitly provided refs only. It adds no
backend API route, truth verification route, claim verification route, evidence
verification route, web-search route, source-fetching route, model verification
route, runtime execution route, model/provider route, memory write route,
evidence mutation route, dependency, production persistence, or production
authority. OpenAPI path count remains `74`; only `info.version` changes to the
active package version.

v0.29.1 hardens M25 unknown/arbitrary truth ref denial in contracts, tests,
verifiers, docs, and Foundation Gate only. It adds no backend API route, truth
verification route, claim verification route, evidence verification route,
web-search route, source-fetching route, model verification route, runtime
execution route, model/provider route, memory write route, evidence mutation
route, dependency, M26 context-pack route, production persistence, or
production authority. OpenAPI path count remains `74`; only `info.version`
changes to the active package version.

API validation errors are sanitized before they are returned. FastAPI/Pydantic validation failures must not echo raw invalid input values or secret-like field values.
