# Web Control Center Shell

Status: Active for v0.17.0 / M13.

M13 adds a local TypeScript React/Vite shell under `apps/control-center/` for reading existing backend Control Center and runtime readiness APIs. It is the first web UI surface for the future Control Center, but it is not a production Control Center and it has no authority to execute actions.

Implemented shell behavior:

- renders read-only dashboard, runtime readiness, Foundation Gate, API route, approval, remote worker, private mesh, mobile planning, and plugin governance summaries.
- submits exactly one preview-only request type to `/control-center/actions/preview`.
- falls back to clearly marked mock data when the local backend is unavailable.
- sanitizes secret-like frontend errors before display.
- uses relative API URLs by default.
- may use `VITE_UAA_API_BASE_URL` for local development with a localhost backend only.

Non-goals:

- no backend route changes beyond version metadata.
- no public execution API.
- no runtime/model/provider call.
- no remote dispatch.
- no mobile/native app.
- no sensor access.
- no plugin enablement.
- no Chrome authenticated profile control.
- no Computer Use automation.
- no iOS/macOS build workflow.
- no production authority.

The shell is allowed to use local npm dependencies for React, Vite, TypeScript, Vitest, and Testing Library only. `node_modules`, `dist`, coverage output, `.env` files, and native/mobile build files are not release artifacts.
