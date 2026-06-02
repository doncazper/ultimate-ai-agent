# Ultimate AI Agent Master Plan v0.18.1

Status: Active baseline after M14 Web Control Center Local Backend Connection Safety hardening.

## v0.18.1 Change Log

v0.18.1 hardens M14 inside the existing local Web Control Center shell without expanding backend authority.

Changed:

- updated active version metadata to `0.18.1`.
- pointed README, documentation index, canonical map, import docs, master plan, and Foundation Gate plan at v0.18.1.
- added `docs/release_notes/v0_18_1.md`.
- broadened frontend API base URL tests for public IPs, private LAN IPs, non-loopback hostnames, URL credentials, and secret-like query parameter names.
- strengthened frontend redaction/secret-like detection for API base URL query parameters.
- made unknown/checking backend connection states explicit in frontend types, loading copy, and Foundation Gate evidence.
- extended static frontend verification for Vite proxy URL credentials, external proxy targets, and secret-like API base env examples.
- kept M14 Foundation Gate criteria scoped to local backend connection safety.

Current baseline reminders:

- Python Agent Core remains the brain.
- TypeScript Control Center remains a user control, status, approval, and preview surface only.
- M12 backend Control Center routes remain read-only/preview-only.
- M13 Web Control Center remains a local shell.
- M14 stabilizes and hardens local backend connection behavior only.
- M15 Approval Queue + Receipt/Event Viewer UI is not implemented in v0.18.1.
- Mock fallback data remains visibly mock and non-authoritative.
- Backend OpenAPI path count remains `74`.
- Parked branches or tags are not accepted baseline and must not be merged automatically.

No production Control Center authority, execution route, approval queue UI, receipt/event viewer UI, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, dependency, backend OpenAPI path, external API host, credential handling, cookie handling, Authorization header, API key, analytics/SaaS SDK, or external action is added by v0.18.1.
