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

Allowed side-effect classes in v0.22.0 are:

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

M11 runtime readiness route group:

- `/runtime/readiness`
- `/runtime/capability-matrix`
- `/runtime/smoke-reports/validate`

These routes expose readiness metadata, capability matrix metadata, and manual smoke report validation only. They do not execute runtimes, run manual smoke, connect to a mesh, dispatch workers, enable plugins, launch native builds, inspect live Codex tools, or claim production readiness.

v0.14.5 documentation integrity adds no route. v0.14.6 Codex plugin governance adds no route and no plugin enablement endpoint. v0.15.0 adds exactly the three M11 runtime readiness status/validation routes. v0.15.1 adds no route and only clarifies runtime readiness taxonomy.

v0.18.4 post-M20 roadmap projection adds no route. M21-M40 were planned/provisional at that milestone and did not add OpenWebUI bridge, local model execution, memory provider, truth/evidence expansion, sandbox/tool execution, MCP/Agent Skills/AGENTS.md runtime, CCC native, device pairing, Device Capability Broker, mobile capture, sensor, browser automation, observability export, eval harness, or M15 approval queue/receipt/event viewer routes.

v0.19.0 M15 Approval Queue + Receipt/Event Viewer UI adds no backend route. The new `/approvals`, `/receipts`, and `/events` routes are frontend routes inside CCC Web only. OpenAPI path count remains `74`.

v0.19.1 M15 Approval/Receipt UI safety hardening adds no backend route. It hardens frontend copy, static verification, tests, and Foundation Gate only. OpenAPI path count remains `74`.

v0.20.0 M16 Event Timeline + Run/Receipt Trace Viewer adds no backend route. The new `/events/timeline` route is a frontend route inside CCC Web only. It adds redacted timeline and trace summaries, safe refs, and Foundation Gate evidence summaries. OpenAPI path count remains `74`.

v0.20.1 M16 trace/redaction safety hardening adds no backend route. It strengthens frontend tests, static verification, docs, and Foundation Gate route-count/no-backend-timeline checks only. OpenAPI path count remains `74`.

v0.21.0 M17 Evidence/File/Memory Viewer adds no backend route. The new `/evidence`, `/files`, and `/memory` routes are frontend routes inside CCC Web only. They add redacted evidence ref, safe file ref, and recall-only memory ref summaries. OpenAPI path count remains `74`.

v0.21.1 M17 Evidence/File/Memory Viewer safety hardening adds no backend route. `/evidence`, `/files`, and `/memory` remain frontend routes inside CCC Web only. OpenAPI path count remains `74`.

v0.21.2 Developer Environment Command Normalization adds no backend route. It adds repo-local verification command wrappers and a developer environment verifier only. OpenAPI path count remains `74`.

v0.22.0 M18 Local Runtime Status + Manual Smoke Control Surface adds no backend route. `/runtime/local` and `/runtime/manual-smoke` are frontend routes inside CCC Web only. They surface existing runtime readiness, capability matrix, and manual smoke report validation metadata. OpenAPI path count remains `74`.

M12 Control Center route group:

- `/control-center/manifest`
- `/control-center/dashboard`
- `/control-center/status`
- `/control-center/routes`
- `/control-center/approvals/summary`
- `/control-center/runtime-readiness/summary`
- `/control-center/foundation-gate/summary`
- `/control-center/actions/preview`

These routes expose backend Control Center contracts, safe summaries, and action previews only. They never execute actions, grant approvals, enable plugins, run frontend tooling, start runtimes, call providers, dispatch remote workers, access mobile sensors, or mutate state.

M13 Web Control Center frontend shell:

- no backend route is added.
- OpenAPI path count remains `74`.
- the shell consumes existing read-only/preview-only API routes.
- the only action-preview frontend POST target is `/control-center/actions/preview`.
- M18 may reference the existing validation-only `/runtime/smoke-reports/validate` route.

v0.17.1 Web Control Center safety polish:

- no backend route is added.
- OpenAPI path count remains `74`.
- frontend endpoint allowlists remain limited to existing read-only routes plus `/control-center/actions/preview`.
- frontend safety verification blocks execute/plugin/mobile/remote/runtime endpoint strings in implementation files.

v0.17.2 Web Control Center verification hardening:

- no backend route is added.
- OpenAPI path count remains `74`.
- frontend CI runs local npm install/typecheck/lint/test/build checks only.
- local browser smoke readiness is manual, local-only, unauthenticated-profile-free, and non-authoritative.

v0.17.3 documentation cleanup, v0.17.4 local browser smoke polish, v0.17.5 roadmap charter freeze, v0.18.0 M14 local backend connection stabilization, v0.18.1 M14 connection safety hardening, v0.18.2 Open Design governance, and v0.18.3 OpenWebUI/CCC strategy clarification:

- no backend route is added.
- OpenAPI path count remains `74`.
- v0.17.4 improves frontend route headings, accessible loading/empty states, action preview risk metadata display, mock fallback reviewability, and safe local browser smoke reporting docs only.
- v0.17.5 freezes roadmap milestone charters and adds no backend route, frontend feature, execution path, dependency, or authority.
- v0.18.1 hardens local-only frontend API base policy and visible backend connection states, with no new backend route, dependency, execution path, external API host, or authority.
- v0.18.2 adds design governance docs, with no new backend route, dependency, execution path, design-tool integration, external API host, or authority.
- v0.18.3 adds OpenWebUI/CCC strategy docs, with no new backend route, OpenWebUI bridge route, native CCC route, dependency, execution path, mobile sensor route, OS permission route, external API host, or authority.
- v0.19.0 adds frontend-only M15 approval queue, receipt viewer, and event viewer routes, with no new backend route, OpenAPI path count change, execution path, mutation path, raw data route, dependency, external API host, or authority.
- v0.19.1 hardens frontend-only M15 approval/receipt UI safety, with no new backend route, OpenAPI path count change, execution path, mutation path, M16 timeline route, raw data route, dependency, external API host, or authority.
- v0.20.0 adds frontend-only M16 event timeline and run/receipt trace viewer UI, with no new backend route, OpenAPI path count change, execution path, mutation path, raw payload route, observability export route, dependency, external API host, or authority.
- v0.20.1 hardens frontend-only M16 trace/redaction safety, with no new backend route, OpenAPI path count change, M17 viewer, execution path, mutation path, raw payload route, observability export route, dependency, external API host, or authority.
- v0.21.0 adds frontend-only M17 evidence/file/memory summary viewers, with no new backend route, OpenAPI path count change, execution path, file mutation path, memory mutation path, filesystem browse path, raw payload route, dependency, external API host, or authority.
- v0.21.1 hardens frontend-only M17 evidence/file/memory summary viewers, with no new backend route, OpenAPI path count change, M18 runtime smoke surface, execution path, file mutation path, memory mutation path, filesystem browse path, raw payload route, dependency, external API host, auth, cookies, analytics, SaaS SDK, or authority.
- v0.21.2 normalizes developer environment commands, with no new backend route, OpenAPI path count change, M18 runtime smoke surface, runtime feature, frontend feature, execution path, dependency, network call, model/provider call, mobile/native/browser/computer-use functionality, plugin enablement, global tool install, or authority.
- v0.22.0 implements frontend-only M18 local runtime status and manual smoke report validation summaries, with no new backend route, OpenAPI path count change, runtime execution path, smoke execution path, model/provider call, remote execution, mobile sensor access, plugin enablement, OpenWebUI integration, raw smoke report route, raw prompt route, raw response route, credential route, dependency, or authority.
- v0.23.0 implements M19 Mobile Companion Contract/API Planning only, with no new backend route, OpenAPI path count change, mobile runtime route, sensor route, OS permission route, approval execution route, dependency, or authority.
- v0.23.1 hardens M19 roadmap and mobile contract safety only, with no new backend route, OpenAPI path count change, mobile runtime route, sensor route, OS permission route, dependency, or authority.
- v0.24.0 implements M20 Device Capability Broker Contract only, with no new backend route, OpenAPI path count change, device capability route, sensor route, pairing route, permission route, runtime execution route, dependency, or authority.
- v0.24.1 hardens M20 Device Capability Broker Contract safety only, with no new backend route, OpenAPI path count change, device capability route, sensor route, pairing route, permission route, dependency, or authority.
- v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration Contract as contract/planning/validation only, with no new backend route, OpenAPI path count change, OpenWebUI bridge route, chat run route, runtime execution route, model/provider route, deployment config, dependency, or authority.
- v0.25.1 hardens M21 OpenWebUI bridge contract safety only, with no new backend route, OpenAPI path count change, OpenWebUI bridge route, chat run route, runtime execution route, model/provider route, deployment config, dependency, or authority. OpenAPI path count remains `74`.
- v0.26.0 implements M22 Local Model Runtime Activation Contract as contract/planning/validation only, with no new backend route, OpenAPI path count change, runtime activation route, endpoint probe route, local model call route, model/provider route, dependency, or authority. OpenAPI path count remains `74`.
- v0.26.1 hardens M22 verifier precision and metadata validation only, with no new backend route, OpenAPI path count change, runtime activation route, endpoint probe route, local model call route, model/provider route, dependency, or authority. OpenAPI path count remains `74`.
- v0.27.0 implements M23 First Real Local LLM Call as manual/CLI-only, loopback-only, fixed-prompt-only, approval-gated, non-tool, and non-authoritative, with no new backend route, OpenAPI path count change, runtime activation route, endpoint probe route, arbitrary prompt route, user-content model call route, OpenWebUI runtime route, Control Center execution route, tool execution route, memory write route, file write route, dependency, or authority. OpenAPI path count remains `74`.
- v0.27.1 hardens M23 local call safety only, with no new backend route, OpenAPI path count change, runtime activation route, endpoint probe route, arbitrary prompt route, user-content model call route, OpenWebUI runtime route, Control Center execution route, tool execution route, memory write route, file write route, dependency, or authority. OpenAPI path count remains `74`.
- v0.28.0 implements M24 Memory Provider Abstraction + Local Memory Store as governed, reviewed-write-only local memory foundation, with no new backend route, OpenAPI path count change, backend memory mutation route, raw memory route, memory import/ingest route, vector-search route, embedding route, context injection route, runtime execution route, model/provider route, OpenWebUI memory write route, Control Center memory mutation route, mobile capture route, tool output write route, cloud memory provider route, dependency, production persistence, or M25 claim verification route. OpenAPI path count remains `74`.
- v0.28.1 repairs the M24 public memory request contract and hardens M24 safety tests/docs only, with no new backend route, OpenAPI path count change, backend memory mutation route, raw memory route, memory import/ingest route, vector-search route, embedding route, context injection route, runtime execution route, model/provider route, OpenWebUI memory write route, Control Center memory mutation route, mobile capture route, tool output write route, cloud memory provider route, dependency, production persistence, or M25 claim verification route. OpenAPI path count remains `74`.
- v0.28.2 removes a duplicate/conflicting roadmap row only, with no new backend route, OpenAPI path count change, backend memory mutation route, raw memory route, memory import/ingest route, vector-search route, embedding route, context injection route, runtime execution route, model/provider route, OpenWebUI memory write route, Control Center memory mutation route, mobile capture route, tool output write route, cloud memory provider route, dependency, production persistence, or M25 claim verification route. OpenAPI path count remains `74`.
- v0.29.0 implements M25 Truth Source Router + Evidence Claim Checker as deterministic local contracts only, with no new backend route, OpenAPI path count change, truth verification route, claim verification route, evidence verification route, web-search route, source-fetching route, model verification route, runtime execution route, model/provider route, memory write route, evidence mutation route, dependency, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.29.1 hardens M25 unknown/arbitrary truth ref denial in contracts, tests, docs, static verifiers, and Foundation Gate only, with no new backend route, OpenAPI path count change, truth verification route, claim verification route, evidence verification route, web-search route, source-fetching route, model verification route, runtime execution route, model/provider route, memory write route, evidence mutation route, dependency, M26 context-pack route, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.29.2 hardens local-dev API authority and raw preview safety in tests, docs, static verifiers, and Foundation Gate only, with no new backend route, OpenAPI path count change, truth verification route, claim verification route, evidence verification route, web-search route, source-fetching route, model verification route, runtime execution route, model/provider route, memory write route, evidence mutation route, dependency, M26 context-pack route, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.29.3 reorganizes documentation archives and active/historical classification only, with no new backend route, OpenAPI path count change, runtime behavior, frontend behavior, dependency, M26 route, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.29.4 repairs documentation archive references and self-maintaining docs policy coverage only, with no new backend route, OpenAPI path count change, runtime behavior, frontend behavior, dependency, M26 route, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.29.5 removes duplicated documentation organization policy wording only, with no backend route, OpenAPI path count change, runtime behavior, frontend behavior, dependency, M26 route, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.30.0 implements M26 Grounded Recall Router + Evidence-Linked Context Pack Builder as local contract logic only, with no new backend route, OpenAPI path count change, recall execution route, recall search route, context-pack injection route, vector-search route, embedding route, external retrieval route, model/provider route, memory write route, frontend feature, dependency, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.30.1 hardens M26 recall source_ref/source_kind consistency only, with no new backend route, OpenAPI path count change, recall execution route, recall search route, context-pack injection route, vector-search route, embedding route, external retrieval route, model/provider route, memory write route, frontend feature, dependency, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts as validation-only and preview-only contract logic, with no new backend route, OpenAPI path count change, tool execution route, tool run route, plugin enablement route, browser execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, or production authority. OpenAPI path count remains `74`.
- v0.31.1 normalizes the GitHub README polish commit into a docs-only baseline, with no new backend route, OpenAPI path count change, action execution route, approval execution route, tool execution route, tool run route, plugin enablement route, browser execution route, memory write route, context-pack injection route, frontend feature, dependency, production persistence, M28 work, or production authority. OpenAPI path count remains `74`.
- v0.32.0 implements M28 Approval Authority v2 + Action Policy Expansion as policy-only and decision-only contract logic, with no new backend route, OpenAPI path count change, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M29 work, or production authority. OpenAPI path count remains `74`.
- v0.32.1 hardens M28 evaluator revalidation for raw/secret action inputs and mutated approval grants only, with no new backend route, OpenAPI path count change, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M29 work, or production authority. OpenAPI path count remains `74`.
