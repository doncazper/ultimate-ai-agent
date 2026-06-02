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
M15 — Approval Queue + Receipt/Event Viewer UI, future read-only/preview-only milestone
```

M14 is about reliable local backend connection states, typed API-client hardening, backend unavailable states, mock-to-live clarity, local-only API base policy, and safe error handling. M14 adds no backend route, execution, new authority, model/provider call, remote dispatch, mobile sensor control, plugin enablement, auth, credentials, cookies, analytics/SaaS SDK, external API host, or approval/receipt UI expansion beyond already-existing read-only summaries.

M15 is the first planned approval queue plus receipt/event viewer UI milestone. It remains read-only/preview-only unless a separate reviewed backend contract explicitly adds authority. The Control Center must not execute actions, approve actions, bypass Approval Authority, write files, mutate memory, resolve credentials, enable plugins, access mobile sensors, or dispatch remote workers.

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
