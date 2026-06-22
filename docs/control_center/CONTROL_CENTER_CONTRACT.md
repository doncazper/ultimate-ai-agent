# Control Center Contract

Status: Active M12 backend contract, v0.16.0.

M12 adds the backend/API contract for a future TypeScript Control Center. It does not implement a frontend, TypeScript app, React, Next.js, Vite, shadcn, Tailwind, Browser automation, Chrome profile control, Computer Use, native app build workflow, plugin enablement, runtime execution, model calls, provider calls, network calls, remote execution, mobile sensor access, production persistence, or production Control Center.

The Control Center is a future user control, approval, status, receipt, and preview surface. It is not the agent brain. Python Agent Core remains the brain, and authority remains with Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Foundation Gate, and governed source systems.

Implemented surfaces are read-only, preview-only, validation-only, planned-disabled, blocked, or not implemented. The manifest blocks runtime execution, model execution, provider invocation, remote dispatch, mobile sensor access, plugin enablement, and frontend build tooling.

Public routes:

```text
GET /control-center/manifest
GET /control-center/dashboard
GET /control-center/status
GET /control-center/routes
GET /control-center/approvals/summary
GET /control-center/runtime-readiness/summary
GET /control-center/foundation-gate/summary
POST /control-center/actions/preview
```

No `/control-center/actions/execute`, `/control-center/plugins/enable`, `/control-center/runtime/execute`, `/control-center/remote-workers/dispatch`, `/control-center/mobile/sensors`, or `/control-center/frontend` route exists.

## v0.18.2 Design Governance

Open Design System and UI Design Governance docs apply to future Control Center UI work, including M15 approval, receipt, and event viewer surfaces. They add no backend route and no frontend behavior. Design tools are not enabled and are not authority.

## v0.18.3 OpenWebUI and CCC Strategy

v0.18.3 clarifies that CCC means Control Center Clients across CCC Web, CCC iOS,
CCC Android, and CCC macOS. This contract still covers the current backend
Control Center API only. Current product direction keeps Control Center /
Founder Command Center as the first-party product UI; OpenWebUI remains a
supported local/dev conversational shell and is not the agent brain.

No OpenWebUI bridge route, native CCC route, Android route, iOS route, macOS route, mobile sensor route, OS permission route, native build workflow, or production authority is added.
