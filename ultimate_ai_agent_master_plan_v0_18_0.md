# Ultimate AI Agent Master Plan v0.18.0

Status: Active baseline after M14 Web Control Center Local Backend Connection Stabilization.

## v0.18.0 Change Log

v0.18.0 implements M14 inside the existing local Web Control Center shell without expanding backend authority.

Changed:

- updated active version metadata to `0.18.0`.
- pointed README, documentation index, canonical map, import docs, master plan, and Foundation Gate plan at v0.18.0.
- added `docs/release_notes/v0_18_0.md`.
- added `docs/control_center/LOCAL_BACKEND_CONNECTION.md`.
- added a local-only frontend API base URL policy for relative, localhost, 127.0.0.1, and loopback IPv6 bases.
- added a Vite dev proxy pinned to `http://127.0.0.1:8000` for relative local backend reads.
- blocked external absolute API URLs and secret-like API base strings.
- added visible backend online, degraded, offline-safe, and mock fallback connection states.
- extended frontend tests, static frontend verification, and Foundation Gate checks for M14.

Current baseline reminders:

- Python Agent Core remains the brain.
- TypeScript Control Center remains a user control, status, approval, and preview surface only.
- M12 backend Control Center routes remain read-only/preview-only.
- M13 Web Control Center remains a local shell.
- M14 stabilizes local backend connection behavior only.
- M15 Approval Queue + Receipt/Event Viewer UI is not implemented in v0.18.0.
- Mock fallback data remains visibly mock and non-authoritative.
- Backend OpenAPI path count remains `74`.
- Parked branches or tags are not accepted baseline and must not be merged automatically.

No production Control Center authority, execution route, approval queue UI, receipt/event viewer UI, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, dependency, backend OpenAPI path, external API host, credential handling, cookie handling, Authorization header, API key, analytics/SaaS SDK, or external action is added by v0.18.0.
