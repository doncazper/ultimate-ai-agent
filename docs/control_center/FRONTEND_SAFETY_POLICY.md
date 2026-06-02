# Frontend Safety Policy

Status: Active for v0.17.5 roadmap projection; frontend safety behavior last changed in v0.17.4.

The Web Control Center shell is a display and preview surface. The Python Agent Core remains the brain and source of policy enforcement.

Frontend safety rules:

- UI controls may read status, route inventory, readiness reports, and summaries.
- The only POST from the frontend is `/control-center/actions/preview`.
- Action preview must never be treated as execution, approval, credential resolution, remote dispatch, model invocation, plugin enablement, or sensor access.
- Mock fixtures must be visibly marked mock and non-authoritative.
- Secret-like user input and backend errors must be sanitized before display.
- The frontend must not read cookies, local storage, session storage, credentials, keychains, files, mobile sensors, camera, microphone, location, browser profiles, or OS signing material.
- The frontend must not use browser credential APIs, service workers, IndexedDB, CacheStorage, notification/push APIs, or clipboard writes.
- The frontend must not include analytics, auth SDKs, payment SDKs, SaaS SDKs, model/provider SDKs, browser automation, native build tooling, mobile project files, or background services.
- `scripts/verify_control_center_frontend.py` is the canonical static frontend safety verifier and is run by `scripts/verify_all.py` and Foundation Gate.
- `scripts/verify_control_center_browser_smoke_readiness.py` verifies that local browser smoke readiness and reporting remain documented, static, manual, local-only, and non-authoritative.

Allowed local tooling:

- npm package management inside `apps/control-center`.
- Vite dev server on localhost.
- React rendering.
- TypeScript typechecking.
- Vitest and Testing Library.
- Browser verification against local dev targets when explicitly approved by the milestone prompt.
- CI frontend checks inside `apps/control-center`: `npm ci`, typecheck, lint, tests, and build.

Local browser smoke readiness:

- manual local browser smoke only.
- local-only targets: `localhost`, `127.0.0.1`, and `::1`.
- no authenticated browser profile.
- no Chrome authenticated profile control.
- no Computer Use.
- no external sites.
- no production backend.
- no screenshots with secrets.
- non-authoritative verification only.

Off-limits in M13/v0.17.x:

- Chrome authenticated profile control.
- Computer Use automation.
- Build iOS Apps and Build macOS Apps plugins.
- App Store Connect, signing identities, keychains, provisioning profiles, and entitlements.
- MCP/A2A runtime delegation.
- external network services.
- production persistence.

## v0.17.5 Roadmap Projection

v0.17.5 freezes future Control Center sequencing without changing frontend behavior:

- M14 is Web Control Center Local Backend Connection Stabilization.
- M15 is Approval Queue + Receipt/Event Viewer UI, read-only/preview-only.
- v0.17.4 remains local browser smoke / UX polish and is not M14.

M14/M15 frontend prompts must preserve these safety boundaries unless a reviewed milestone explicitly changes them:

- no execution.
- no approval authority bypass.
- no plugin enablement.
- no mobile sensor control.
- no remote dispatch.
- no model/provider invocation.
- no sensitive browser storage, cookies, credential APIs, camera, microphone, location, notification, push, service worker, IndexedDB, CacheStorage, or clipboard-write APIs.
