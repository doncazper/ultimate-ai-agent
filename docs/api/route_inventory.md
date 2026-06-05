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

v0.40.0 M36 CCC File Review Surface, Review-Only adds no backend route.
`/files/review` is a frontend route inside CCC Web only. It displays redacted
review packets, redacted previews, redaction summaries, exact binding refs,
review-only decision status, approval gate contract status, and receipt plan
metadata. OpenAPI path count remains `74`.

v0.40.1 M36 CCC File Review Surface Read-Only Safety hardening adds no backend
route. It strengthens frontend-only safe-ref and no-mutating-request checks.
OpenAPI path count remains `74`.

v0.41.0 M37 Review Approval Capture, Review-Only Persistence adds exactly one
narrow backend mutation route:

- `POST /files/review/approvals/capture`

This route captures review-only approve/deny records for exact redacted review
packets. It stores safe refs only, requires exact review packet, preview
result, redaction summary, file, path, actor, and idempotency bindings, and
grants no raw file access, context proposal, context injection, memory write,
export, execution, tool use, or production authority. OpenAPI path count is
`75`. No raw-file, full-file, file write/delete, context, memory, export, tool
execution, or arbitrary filesystem route is added.

v0.42.0 M38 Safe Context Proposal From Approved Review adds no backend route.
Safe context proposal contracts are core validation objects only. They do not
expose `/context/propose`, `/context/inject`, `/context/handoff`,
`/openwebui/handoff`, `/memory/write`, raw-file, export, tool execution, or
model/provider routes. The M37 review approval capture route remains the only
post-M36 backend addition. OpenAPI path count remains `75`.

v0.43.0 M39 CCC Context Proposal Surface adds no backend route. It adds the
frontend-only `/context/proposals` Control Center surface for safe context
proposal display. It does not expose context handoff, context injection,
OpenWebUI handoff, memory write, raw-file, export, execution, tool execution,
or model/provider routes. OpenAPI path count remains `75`.

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
- v0.33.0 implements M29 Agent Task Planning Engine as deterministic local review-only contract logic, with no new backend route, OpenAPI path count change, task execution route, task run route, plan execution route, plan run route, scheduler route, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M30 work, or production authority. OpenAPI path count remains `74`.
- v0.33.1 hardens M29 dependency graph, derived risk, hidden side-effect, authority-boundary, evaluator revalidation, and no-execution checks only, with no new backend route, OpenAPI path count change, task execution route, task run route, plan execution route, plan run route, scheduler route, background worker route, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M30 work, or production authority. OpenAPI path count remains `74`.
- v0.34.0 implements M30 Multi-Step Execution Framework as deterministic local state-machine-only contract logic, with no new backend route, OpenAPI path count change, execution run route, task execution route, plan execution route, workflow route, scheduler route, background worker route, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M31 work, or production authority. OpenAPI path count remains `74`.
- v0.34.1 hardens M30 state transition, replay, hidden side-effect, evaluator revalidation, and no-side-effect checks only, with no new backend route, OpenAPI path count change, execution run route, task execution route, plan execution route, workflow route, scheduler route, background worker route, action execution route, approval execution route, action-policy execution route, tool execution route, tool run route, plugin enablement route, browser execution route, mobile execution route, remote execution route, shell execution route, memory write route, context-pack injection route, frontend execution control, dependency, production persistence, M31 work, or production authority. OpenAPI path count remains `74`.
- v0.35.0 implements M31 Real Tool Runtime Adapter, Single Safe No-Op Tool as no-op-only local runtime adapter logic, with no new backend route, OpenAPI path count change, arbitrary tool execution route, tool run route, tool-runtime execute route, tool-broker execute route, action execution route, plugin enablement route, shell execution route, file mutation route, memory write route, network tool route, model/provider tool route, browser/mobile/remote/plugin tool route, frontend execution control, dependency, production persistence, M32 work, or production authority. OpenAPI path count remains `74`.
- v0.35.1 hardens M31 no-op runtime adapter safety only, with no new backend route, OpenAPI path count change, arbitrary tool execution route, tool run route, tool-runtime execute route, tool-broker execute route, action execution route, plugin enablement route, shell execution route, file mutation route, memory write route, network tool route, model/provider tool route, browser/mobile/remote/plugin tool route, frontend execution control, dependency, production persistence, M32 work, or production authority. OpenAPI path count remains `74`.
- v0.36.0 implements M32 Safe Local Filesystem Metadata Tool as governed local runtime adapter metadata logic only, with no new backend route, OpenAPI path count change, file content route, raw file route, file write/delete route, filesystem read/write/delete route, tool execute route, tool-runtime execute route, plugin enablement route, frontend execution control, dependency, production persistence, M33 work, or production authority. OpenAPI path count remains `74`.
- v0.36.1 hardens M32 Filesystem Metadata Path Safety only, with no new backend route, OpenAPI path count change, file content route, raw file route, file write/delete route, filesystem read/write/delete route, tool execute route, tool-runtime execute route, plugin enablement route, frontend execution/raw-preview control, dependency, production persistence, M33 work, or production authority. OpenAPI path count remains `74`.
- v0.37.0 implements M33 First Safe Local File Read Proposal, Redacted Preview Only, through the governed tool runtime adapter only. It adds no backend raw-file/read/write/delete/execute route, no OpenAPI path count change, no Control Center raw-preview/execute control, no dependency, no context injection route, and no production authority. OpenAPI path count remains `74`.
- v0.37.1 hardens M33 redacted file preview safety only, with no new backend route, OpenAPI path count change, raw file route, full-file route, content hash route, directory listing route, context injection route, memory write route, tool execution route, dependency, M34 work, or production authority. OpenAPI path count remains `74`.
- v0.37.2 adds local developer launcher tooling only, with no new backend route, OpenAPI path count change, raw file route, context injection route, memory write route, tool execution route, dependency, M34 work, or production authority. OpenAPI path count remains `74`.
- v0.37.3 repairs active roadmap label alignment and documentation-integrity coverage only, with no new backend route, OpenAPI path count change, raw file route, context injection route, memory write route, tool execution route, dependency, M34 work, or production authority. OpenAPI path count remains `74`.
- v0.37.4 supersedes the old active M35-M40 roadmap projection with the active M34-M60 roadmap sequence and documentation-integrity guard only, with no new backend route, OpenAPI path count change, raw file route, file-review route, review-approval route, context injection route, memory write route, tool execution route, dependency, M34 implementation, mobile/TestFlight implementation, or production authority. OpenAPI path count remains `74`.
- v0.38.0 implements M34 Broader File Capability Review as planning/docs/verifier/Foundation Gate work only, with no new backend route, OpenAPI path count change, raw file route, file-review route, review-approval route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M35 implementation, frontend runtime feature, or production authority. OpenAPI path count remains `74`.
- v0.38.1 hardens M34 boundary clarity in docs/verifiers/Foundation Gate only, with no new backend route, OpenAPI path count change, raw file route, file-review route, review-approval route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M35 implementation, frontend runtime feature, or production authority. OpenAPI path count remains `74`.
- v0.38.2 repairs active M34 current-baseline labels and documentation-integrity coverage only, with no new backend route, OpenAPI path count change, raw file route, file-review route, review-approval route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M35 implementation, frontend runtime feature, or production authority. OpenAPI path count remains `74`.
- v0.39.0 implements M35 Safe File Review Workflow Contracts as contract-only, review-only core logic, with no new backend route, OpenAPI path count change, raw file route, full-file route, file-review approval capture route, file-review persistence route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M36 implementation, frontend runtime feature, or production authority. OpenAPI path count remains `74`.
- v0.39.1 hardens M35 exact file/path binding only, with no new backend route, OpenAPI path count change, raw file route, full-file route, file-review approval capture route, file-review persistence route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M36 implementation, frontend runtime feature, or production authority. OpenAPI path count remains `74`.
- v0.40.0 implements M36 CCC File Review Surface, Review-Only as frontend-only display, with no backend route, OpenAPI path count change, approval capture route, approval persistence route, raw file route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M37 implementation, or production authority. OpenAPI path count remains `74`.
- v0.40.1 hardens M36 CCC File Review Surface Read-Only Safety only, with no backend route, OpenAPI path count change, approval capture route, approval persistence route, raw file route, context proposal route, context injection route, memory write route, export route, tool execution route, dependency, M37 implementation, or production authority. OpenAPI path count remains `74`.
- v0.41.0 implements M37 Review Approval Capture, Review-Only Persistence with exactly one backend route, `POST /files/review/approvals/capture`, for safe-ref-only review approval/denial capture bound to exact redacted review packets. It adds no raw-file route, full-file route, file write/delete route, context proposal route, context injection route, memory write route, export route, tool execution route, arbitrary filesystem route, dependency, M38 work, or production authority. OpenAPI path count is `75`.
- v0.42.0 implements M38 Safe Context Proposal From Approved Review as contract-only core logic, with no backend route, OpenAPI path count change, context proposal route, context injection route, OpenWebUI handoff route, memory write route, export route, tool execution route, dependency, M39 work, or production authority. OpenAPI path count remains `75`.
- v0.43.0 implements M39 CCC Context Proposal Surface as frontend-only display, with no backend route, OpenAPI path count change, context proposal route, context injection route, OpenWebUI handoff route, memory write route, export route, tool execution route, dependency, M40 work, or production authority. OpenAPI path count remains `75`.
- v0.44.0 implements M40 Context Handoff Approval, No Injection as contract-only core logic, with no backend route, OpenAPI path count change, context handoff route, context injection route, OpenWebUI handoff route, memory write route, export route, tool execution route, dependency, M41 work, or production authority. OpenAPI path count remains `75`.
- v0.45.0 implements M41 Local Prototype Safety Freeze as docs/verifier/Foundation Gate hardening only, with no backend route, OpenAPI path count change, raw file route, context route, memory write route, mobile route, browser execution route, remote execution route, plugin route, tool execution route, dependency, M42 work, or production authority. OpenAPI path count remains `75`.
- v0.46.0 implements M42 Mobile Companion Product Contract Refresh as planning/docs/contracts/verifier work only, with no backend route, mobile API route, mobile app, native build route, sensor route, approval execution route, context injection route, memory write route, export route, tool execution route, dependency, M43 implementation, or production authority. OpenAPI path count remains `75`.
- v0.47.0 implements M43 Mobile API Boundary, Read-Only as contract-only planned endpoint refs, with no backend route, mobile API route runtime, mobile mutation route, mobile sensor route, mobile approval capture route, mobile approval execution route, raw data route, raw payload route, raw absolute path route, credential/cookie route, context injection route, memory write route, export route, execution route, dependency, M44 implementation, or production authority. OpenAPI path count remains `75`.
- v0.48.0 implements M44 CCC iOS Skeleton, No Authority as source-only skeleton work, with no backend route, mobile API route runtime, native build route, signing/store route, TestFlight route, mobile network route, mobile sensor route, OS permission route, approval capture route, approval execution route, context injection route, memory write route, file mutation route, export route, execution route, credential/cookie route, background task route, dependency, M45 implementation, or production authority. OpenAPI path count remains `75`.
- v0.49.0 implements M45 CCC iOS Local Read-Only Connection as local-only, loopback-only, read-only contract/status work, with no runtime network call, backend route, mobile API route runtime, approval capture route, approval execution route, raw data route, context injection route, memory write route, file mutation route, export route, execution route, mobile sensor route, background collection route, credential/cookie route, native build route, signing/store route, TestFlight route, dependency, M46 implementation, or production authority. OpenAPI path count remains `75`.
- v0.50.0 implements M46 iOS Review/Receipt Read-Only Surfaces as source-only, read-only redacted summary display work, with no runtime network call, backend route, mobile API route runtime, approval capture route, approval execution route, raw data route, context injection route, memory write route, file mutation route, export route, execution route, mobile sensor route, background collection route, credential/cookie route, native build route, signing/store route, TestFlight route, dependency, M47 implementation, or production authority. OpenAPI path count remains `75`.
- v0.51.0 implements M47 TestFlight Pipeline, Internal Only as internal-only, contract/checklist-only pipeline planning work, with no backend route, mobile TestFlight route, build execution route, upload execution route, signing asset route, provisioning profile route, certificate/private-key route, App Store Connect route, external beta route, public distribution route, production route, mobile sensor route, background collection route, approval execution route, context injection route, memory write route, raw data route, export route, execution route, dependency, M48 implementation, or production authority. OpenAPI path count remains `75`.
- v0.52.0 implements M48 First Internal TestFlight Build as an internal-only, review-only build candidate record, with no backend route, mobile build route, TestFlight upload route, signing asset route, provisioning profile route, certificate/private-key route, App Store Connect upload route, external beta route, public distribution route, production route, mobile approval capture route, mobile sensor route, background collection route, approval execution route, context injection route, memory write route, raw data export route, export route, execution route, dependency, M49 implementation, or production authority. OpenAPI path count remains `75`.
- v0.53.0 implements M49 Mobile Review Approval Capture as exact-scope, review-only, safe-ref-only core contracts, with no backend route, mobile approval capture route, mobile approval execution route, native approval capture UI, raw file route, raw content route, full-file route, unredacted preview route, raw path route, context proposal route, context injection route, memory write route, export route, tool execution route, action execution route, mobile sensor route, background collection route, dependency, M50 implementation, or production authority. OpenAPI path count remains `75`.
- v0.54.0 implements M50 Mobile Approval Audit Hardening as deterministic, review-only, safe-ref-only audit reports over mobile review approval records, with no backend route, mobile audit route, mobile audit export route, native audit UI, raw file route, raw content route, full-file route, unredacted preview route, raw path route, context proposal route, context injection route, memory write route, export route, tool execution route, action execution route, mobile sensor route, background collection route, dependency, M51 implementation, or production authority. OpenAPI path count remains `75`.
