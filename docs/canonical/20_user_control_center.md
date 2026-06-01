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

v0.16.0 adds backend Control Center contracts and read-only/preview-only API routes for a future UI. This is not the TypeScript Control Center implementation.

The M12 API may expose manifest, dashboard snapshot, status, route summary, approval summary, runtime-readiness summary, Foundation Gate summary, and action preview data. It must not execute actions, mutate files, grant approvals, resolve credentials, enable plugins, run frontend tooling, start runtimes, call models/providers, dispatch remote workers, access mobile sensors, or become a production Control Center.

Action preview decisions are policy previews only. They are not authority, approval, consent, execution, evidence, or proof of production readiness.
