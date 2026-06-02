# Frontend Safety Policy

Status: Active for v0.18.2 / Open Design System and UI Design Governance.

The Web Control Center shell is a display and preview surface. The Python Agent Core remains the brain and source of policy enforcement.

Frontend safety rules:

- UI controls may read status, route inventory, readiness reports, and summaries.
- The only POST from the frontend is `/control-center/actions/preview`.
- Action preview must never be treated as execution, approval, credential resolution, remote dispatch, model invocation, plugin enablement, or sensor access.
- Mock fixtures must be visibly marked mock and non-authoritative.
- API base URLs must be local-only: relative path, localhost, 127.0.0.1, or loopback IPv6.
- External absolute API URLs, public/private non-loopback hosts, URL credentials, and secret-like API base strings must be blocked or rejected.
- Unknown/checking, live, degraded, offline-safe, and mock fallback connection states must be visible and safe.
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

Off-limits in M14/v0.18.1:

- Chrome authenticated profile control.
- Computer Use automation.
- Build iOS Apps and Build macOS Apps plugins.
- App Store Connect, signing identities, keychains, provisioning profiles, and entitlements.
- MCP/A2A runtime delegation.
- external network services.
- external API hosts.
- auth, credentials, cookies, Authorization headers, or API keys.
- analytics/SaaS SDKs.
- production persistence.

## v0.18.0 M14 Connection Safety

v0.18.0 implements local backend connection stabilization only:

- relative API bases are allowed.
- localhost, 127.0.0.1, and loopback IPv6 API bases are allowed.
- external absolute API bases are unsupported.
- secret-like query strings or credentials in an API base are rejected.
- mock fallback remains non-authoritative.
- partial backend failures show degraded state.
- OpenAPI path count remains `74`.

## v0.18.1 M14 Connection Safety Hardening

v0.18.1 strengthens the same M14 boundary:

- public IPs, private LAN IPs, and non-loopback hostnames are blocked as API bases.
- URL credentials in API bases are rejected.
- broad secret-like query parameter names are rejected.
- Vite proxy targets and env examples are statically checked for unsafe API base values.
- unknown/checking connection states are explicit.

M15 Approval Queue + Receipt/Event Viewer UI remains future work. Future frontend prompts must preserve these safety boundaries unless a reviewed milestone explicitly changes them:

- no execution.
- no approval authority bypass.
- no plugin enablement.
- no mobile sensor control.
- no remote dispatch.
- no model/provider invocation.
- no sensitive browser storage, cookies, credential APIs, camera, microphone, location, notification, push, service worker, IndexedDB, CacheStorage, or clipboard-write APIs.

## v0.18.2 Design Governance Boundary

Control Center UI changes must follow:

- `docs/design/OPEN_DESIGN_SYSTEM.md`
- `docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md`
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`
- `docs/design/ACCESSIBILITY_BASELINE.md`
- `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`
- `docs/design/COMPONENT_TAXONOMY.md`
- `docs/design/RESPONSIVE_LAYOUT_BASELINE.md`

Design governance does not add frontend behavior, dependencies, Tailwind, shadcn, design system packages, icon packs, analytics, auth, payment SDKs, design tool integration, Chrome authenticated profile control, Computer Use, plugin enablement, mobile sensor access, remote dispatch, model/provider calls, or production authority.
