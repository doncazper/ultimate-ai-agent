# Ultimate AI Agent Master Plan v0.17.4

Status: Active baseline after the Web Control Center local browser smoke polish patch.

## v0.17.4 Change Log

v0.17.4 polishes the existing M13 Web Control Center shell without starting M14 or expanding backend/frontend authority.

Changed:

- updated active version metadata to `0.17.4`.
- pointed README, documentation index, canonical map, import docs, master plan, and Foundation Gate plan at v0.17.4.
- added `docs/release_notes/v0_17_4.md`.
- added `docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md`.
- improved local shell route headings for dashboard, runtime readiness, Foundation Gate, API routes, approvals, remote worker boundary, mobile planning, plugin governance, and action preview pages.
- improved accessible loading and empty states for local browser smoke review.
- exposed action preview risk level as preview metadata only.
- strengthened frontend tests for route headings, state copy, preview-only risk metadata, and sanitized backend preview errors.
- extended browser smoke readiness verification to require the safe smoke reporting doc.

Current baseline reminders:

- Python Agent Core remains the brain.
- TypeScript Control Center remains a user control, status, approval, and preview surface only.
- M12 backend Control Center routes remain read-only/preview-only.
- M13 Web Control Center remains a local shell.
- Browser smoke readiness and reporting remain manual, local-only, unauthenticated-profile-free, and non-authoritative.
- Chrome authenticated profile control, Computer Use, iOS/macOS build plugins, plugin enablement, mobile sensor access, remote dispatch, model/provider invocation, production persistence, and external actions remain off-limits.

No production Control Center authority, execution route, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, dependency, backend OpenAPI path, or external action is added by v0.17.4.
