# 20 — User Control Center

Status: Canonical product/control-plane spec, v0.5.3
Owner: User Trust / Product
Layer: Cross-layer user-facing control surface

## Purpose

The User Control Center is the user's command center for inspecting, tuning, pausing, revoking, and auditing the assistant.

It answers:

```text
What does the agent know about me?
What is it allowed to access?
What is it monitoring?
What can it do without asking?
What did it do recently?
What did it learn?
What can I revoke, export, delete, or pause?
```

## Required views

```text
Memory review and edit
Consent and permissions
Connected providers and credentials
Approvals queue
Watchlists and notification settings
Scanner controls
Skill registry
Automations
Cost and usage
Activity/event receipts
Data export/delete
Model routing preferences
Foundation gate status
```

## Non-negotiable controls

The user must be able to:

```text
Pause learning
Pause scanners
Pause proactive notifications
Revoke provider access
Delete a memory
Export memory and event receipts
View active standing approvals
Cancel standing approvals
See why an alert was sent
See what files/tools/providers were touched by a run
```

## Dependencies

```text
Consent Ledger
Secret Broker
Provider Registry
Memory Service
Event Ledger
Cost Governor
Tool Broker
Notification policy
Data lifecycle controls
```

## Risks

```text
UI bypassing Agent Core
Confusing consent with credentials
Hiding too much automation from the user
Exposing secrets in activity views
Creating notification fatigue
```

## Foundation rule

The Control Center may show and configure the agent, but it must not directly mutate memory, files, tools, providers, or credentials. All mutating calls go through the Agent API Boundary, Consent Ledger, Tool Broker, and Event Ledger.

## Future Mobile Companion Extension

The Mobile Companion is a future extension of the Control Center. The phone is not the agent brain. It may become an approval, status, receipt, capture, and emergency-stop surface only after the web Control Center and API contracts are stable.

Mobile approval queues must use Approval Authority. Mobile notifications must be receipt-backed. Mobile actions must be revocable and auditable. Mobile sensors must route through the future Device Capability Broker.

Mobile capture cannot silently become memory, cannot approve actions, and cannot trigger external sends without governed approval. Web Control Center foundation comes before mobile sensor work.

## Future UI Tooling Boundary

Future Web Control Center implementation may use Browser + Build Web Apps with explicit approval. Chrome authenticated profile control remains disabled unless separately approved. Computer Use remains disabled except explicit last-resort manual QA approval.

iOS and macOS build plugins are not part of the web Control Center boundary. Build iOS Apps / XcodeBuildMCP remains disabled until a dedicated Mobile Companion implementation milestone. Build macOS Apps remains disabled until a dedicated Desktop/macOS Companion milestone.

## M12 Backend Contract Boundary

v0.16.0 adds backend Control Center contracts and read-only/preview-only API routes for a future UI.

The M12 API may expose manifest, dashboard snapshot, status, route summary, approval summary, runtime-readiness summary, Foundation Gate summary, and action preview data. It must not execute actions, mutate files, grant approvals, resolve credentials, enable plugins, run frontend tooling, start runtimes, call models/providers, dispatch remote workers, access mobile sensors, or become a production Control Center.

v0.17.0 adds the first local Web Control Center shell. It is a React/Vite/TypeScript app under `apps/control-center` that reads existing backend summaries, renders mock fallback data when the backend is unavailable, and submits only action previews. It is still not the agent brain, not production authority, and not a path around Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, or Foundation Gate.

Action preview decisions are policy previews only. They are not authority, approval, consent, execution, evidence, or proof of production readiness.

## v0.18.0 M14 Local Backend Connection

v0.18.0 implements M14 local backend connection stabilization in the existing Web Control Center shell.

```text
M14 — Web Control Center Local Backend Connection Stabilization, implemented
M15 — Approval Queue + Receipt/Event Viewer UI, implemented read-only/preview-only milestone
```

M14 is about reliable local backend connection states, typed API-client hardening, backend unavailable states, mock-to-live clarity, local-only API base policy, and safe error handling. M14 adds no backend route, execution, new authority, model/provider call, remote dispatch, mobile sensor control, plugin enablement, auth, credentials, cookies, analytics/SaaS SDK, external API host, or approval/receipt UI expansion beyond already-existing read-only summaries.

M15 is the first approval queue plus receipt/event viewer UI milestone. It is implemented in v0.19.0 as read-only/preview-only CCC Web inspection panels. It adds no backend API route and remains read-only/preview-only unless a separate reviewed backend contract explicitly adds authority. The Control Center must not execute actions, approve actions, bypass Approval Authority, write files, mutate memory, resolve credentials, enable plugins, access mobile sensors, or dispatch remote workers.

v0.19.1 hardens M15 Approval/Receipt UI safety. CCC Web must state that it cannot grant, deny, execute, or bypass approvals. Approval refs are identifiers only and never authority. Python Agent Core remains the only approval authority. Receipt and event detail views must state that they are redacted summary metadata only.

v0.20.0 implements M16 Event Timeline + Run/Receipt Trace Viewer. CCC Web may show redacted timeline summaries, safe event refs, run refs, correlation refs, receipt refs, relation refs, and Foundation Gate evidence summaries. It must not show raw prompts, secrets, file contents, memory contents, credentials, provider payloads, event payload dumps, receipt payload dumps, or unreviewed tool arguments.

## v0.18.2 Open Design Governance

v0.18.2 adds repo-owned Open Design System and UI Design Governance documentation before M15. Control Center UI work must follow:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

Design docs, reviewed components, and future repo-owned tokens are the design source of truth. Design tools, design SaaS, UI generators, screenshot-to-code, and design-to-code tools are not authority and are not enabled by v0.18.2.

M15 approval, receipt, and event viewer UI must read the design governance docs before implementation. Future Mobile Companion UI should inherit these principles while remaining a control, approval, capture, receipt, and status surface, not the agent brain.

## v0.18.3 OpenWebUI and CCC Client Strategy

v0.18.3 clarifies the long-term UI/client split:

- Python Agent Core remains the brain and authority layer.
- OpenWebUI is the preferred conversational web shell and is not the agent brain.
- CCC means Control Center Clients.
- CCC is the governance/control client family.
- CCC Web is the current TypeScript web Control Center.
- CCC iOS is a future native mobile control client.
- CCC Android is a future native mobile control client.
- CCC macOS is a future desktop/local companion client.
- Open Design governs custom CCC surfaces and does not replace OpenWebUI.

All CCC clients must respect Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, and Foundation Gate. All CCC clients must use stable API/OpenAPI contracts, avoid secrets in local/browser/mobile storage, remain auditable and receipt-backed, and must not bypass approvals or execute actions locally.

v0.18.3 adds no M15 Approval Queue + Receipt/Event Viewer UI, OpenWebUI integration, OpenWebUI deployment config, frontend feature, backend API route, native CCC implementation, Android app, iOS app, macOS app, native build workflow, mobile sensor access, OS permission integration, signing, keystore, provisioning, App Store workflow, Play Store workflow, dependency, plugin enablement, runtime execution, model/provider call, network call, remote execution, or production authority.

## v0.18.4 Post-M20 CCC Roadmap Projection

v0.18.4 points future client work to `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md` and `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`.

Relevant future milestones:

- M21 - OpenWebUI Bridge + Chat Shell Integration Contract.
- M31 - CCC Native Client Contract: iOS / Android / macOS.
- M32 - Device Pairing + Trust Handshake Contract.
- M33 - Mobile Approval Surface Prototype, No Sensors.
- M34 - macOS Local Companion Contract / Prototype.

These are planned/provisional only. v0.18.4 adds no OpenWebUI integration, M15 UI, native CCC implementation, device pairing, mobile app, macOS app, sensor access, browser automation, or production Control Center authority.

## v0.19.0 M15 Approval Receipt Event Viewer

v0.19.0 adds frontend-only CCC Web routes for approval, receipt, and event inspection:

- `/approvals`: Approval Queue summaries and selected details.
- `/receipts`: Receipt Viewer summaries and selected details.
- `/events`: Event Viewer summaries and selected details.

The views show redacted summary-only data and visibly mock, non-authoritative fallback records. Approval Authority remains in Python Agent Core. M15 adds no backend route, approval execution, approve/reject mutation, receipt/event mutation, raw secret/prompt/file/memory display, runtime execution, model/provider call, remote dispatch, mobile sensor access, plugin enablement, native build workflow, or production Control Center authority.

## v0.19.1 M15 Approval Receipt UI Safety Hardening

v0.19.1 hardens the v0.19.0 M15 UI without changing authority or route scope:

- approval refs are identifiers only and never approval authority.
- Python Agent Core remains the only approval authority.
- Approval Queue and detail surfaces must not imply grant, deny, execute, or bypass power.
- receipt detail remains redacted summary metadata only.
- event detail remains redacted summary metadata only.
- static frontend verification and Foundation Gate checks reject active approve/deny/execute/send/write/run/deploy/enable controls, mutation endpoints, authority-bypass copy, raw M15 review fields, credential-like review fields, and raw sensitive payload display.

v0.19.1 adds no M16 Event Timeline + Run/Receipt Trace Viewer, backend API route, approval execution, approve/deny mutation, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, or production Control Center authority.

## v0.20.0 M16 Event Timeline Trace Viewer

v0.20.0 adds frontend-only CCC Web route `/events/timeline`:

- Event Timeline: redacted event summaries with safe refs.
- Run/Receipt Trace Viewer: selected trace detail as summary metadata only.
- Relation refs: parent/child event refs and receipt/evidence relationship summaries.
- Foundation Gate evidence summary: safe evidence refs and criterion/status summaries.

M16 remains read-only. It adds no backend API route, OpenAPI path count change, approval execution, tool execution, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, external telemetry export, OpenTelemetry export, cloud traces, raw payload display, or production Control Center authority.

## v0.20.1 M16 Trace Redaction Safety Hardening

v0.20.1 hardens M16 without adding new authority or feature surfaces:

- selecting `View trace` changes visible selected trace detail only.
- selected timeline cards expose accessible selected-state metadata.
- Foundation Gate checks OpenAPI path count remains `74`.
- Foundation Gate rejects backend timeline, trace, raw event, and telemetry export route expansion.
- static frontend verification rejects tracked Control Center build and log artifacts.
- review builds should prefer temporary output paths such as `/tmp/uaa-control-center-review-dist`.

v0.20.1 adds no M17 Evidence/File/Memory Viewer, backend API route, OpenAPI path count change, approval execution, tool execution, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, native build workflow, external telemetry export, OpenTelemetry export, cloud traces, raw payload display, or production Control Center authority.

## v0.21.0 M17 Evidence File Memory Viewer

v0.21.0 adds frontend-only CCC Web routes for evidence, file ref, and memory ref inspection:

- `/evidence`: Evidence Viewer summaries and selected details.
- `/files`: File Reference Viewer summaries and selected details.
- `/memory`: Memory Viewer summaries and selected details.

The views show redacted summary-only data and visibly mock, non-authoritative fallback records. Memory is recall, not authority. Canonical files and governed source systems outrank memory.

M17 adds no backend API route, OpenAPI path count change, file mutation, memory mutation, filesystem browsing, raw secret/prompt/file/memory/evidence/credential/provider payload display, embeddings, vector DB, memory provider implementation, runtime execution, model/provider call, remote dispatch, mobile sensor access, plugin enablement, dependency, native build workflow, or production Control Center authority.

## v0.21.1 M17 Evidence File Memory Viewer Safety Hardening

v0.21.1 hardens the existing frontend-only M17 surfaces. `/evidence`, `/files`, and `/memory` remain read-only, visibly mock, non-authoritative, and redacted summary-only.

The patch adds alternate safe mock refs, accessible selected-card reviewability, frontend tests, static verifier checks, browser smoke reviewability, docs, and Foundation Gate criteria. OpenAPI path count remains `74`, and no backend API route is added.

v0.21.1 adds no M18 local runtime smoke control surface, file mutation, memory mutation, filesystem browsing, raw secret/prompt/file/memory/evidence/credential/provider payload display, embeddings, vector DB, memory provider implementation, runtime execution, model/provider call, remote dispatch, mobile sensor access, plugin enablement, dependency, auth, cookies, analytics, SaaS SDK, native build workflow, or production Control Center authority.
