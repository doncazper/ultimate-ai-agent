# Web Control Center Shell

Status: Active for v0.18.0 / M14 local backend connection stabilization.

M13 adds a local TypeScript React/Vite shell under `apps/control-center/` for reading existing backend Control Center and runtime readiness APIs. It is the first web UI surface for the future Control Center, but it is not a production Control Center and it has no authority to execute actions.

Implemented shell behavior:

- renders read-only dashboard, runtime readiness, Foundation Gate, API route, approval, remote worker, private mesh, mobile planning, and plugin governance summaries.
- submits exactly one preview-only request type to `/control-center/actions/preview`.
- labels action preview as preview-only and displays blocked decisions as non-executed safety results.
- exposes the action preview risk level as policy metadata only.
- provides route-level headings and accessible loading, empty, error, and mock fallback states for local browser smoke review.
- falls back to clearly marked mock data when the local backend is unavailable.
- displays backend online, degraded, offline-safe, and mock fallback connection states.
- sanitizes secret-like frontend errors before display.
- uses relative API URLs by default.
- may use `VITE_UAA_API_BASE_URL` for local development with a local backend only.
- allows only relative, localhost, 127.0.0.1, and loopback IPv6 API bases.
- blocks external absolute API bases and rejects secret-like API base strings.

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

v0.17.4 adds local browser smoke UX polish and safe reporting documentation only. Frontend CI still covers install, typecheck, lint, tests, and build; static verifiers cover frontend safety plus manual local browser smoke readiness/reporting; and Foundation Gate checks the CI/static/browser-readiness boundary. It does not add backend API paths, execution controls, sensitive browser storage, mobile sensor APIs, plugin enablement controls, browser automation, Chrome authenticated profile control, Computer Use automation, native build workflows, dependencies, or production Control Center authority.

## v0.18.0 M14 Connection Stabilization

v0.18.0 implements M14 local backend connection stabilization:

- API base URL policy is local-only.
- external absolute API URLs are blocked.
- secret-like API base URL strings are rejected and not displayed.
- live, degraded, and mock fallback states are visible.
- partial backend failures show degraded state and call out non-authoritative mock fallback panels.
- OpenAPI path count remains `74`; no backend route is added.

M15 Approval Queue + Receipt/Event Viewer UI remains future work. M14 must keep the shell read-only/preview-only and must not add execution, approval authority, plugin enablement, remote dispatch, mobile sensor control, model/provider calls, auth, credentials, cookies, analytics/SaaS SDKs, production persistence, external API hosts, dependencies, or production Control Center authority.
