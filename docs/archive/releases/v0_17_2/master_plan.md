Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.17.2

Status: Active baseline after the Web Control Center CI, static safety, and local browser smoke readiness hardening patch.

## v0.17.2 Change Log

v0.17.2 hardens the M13 Web Control Center shell verification path without starting M14 or expanding backend authority.

Changed:

- added frontend CI checks for `npm ci`, typecheck, lint, tests, and build inside `apps/control-center`.
- added `docs/control_center/LOCAL_BROWSER_SMOKE.md` for manual local-only browser smoke readiness.
- added `scripts/verify_control_center_browser_smoke_readiness.py`.
- wired the browser smoke readiness verifier into `scripts/verify_all.py`.
- strengthened `scripts/verify_control_center_frontend.py` for analytics and external SDK markers.
- extended Foundation Gate checks for frontend CI coverage and browser smoke readiness.
- expanded Python and frontend tests for CI/static/browser-readiness safety.
- updated active version, release, import, docs, and package metadata.

Current baseline reminders:

- Python Agent Core remains the brain.
- TypeScript Control Center remains a user control, status, approval, and preview surface only.
- M12 backend Control Center routes remain read-only/preview-only.
- M13 Web Control Center remains a local shell.
- Browser smoke readiness is manual, local-only, unauthenticated-profile-free, and non-authoritative.
- Browser plus Build Web Apps may be used only when a future prompt explicitly asks for local UI verification.
- Chrome authenticated profile control, Computer Use, iOS/macOS build plugins, plugin enablement, mobile sensor access, remote dispatch, model/provider invocation, production persistence, and external actions remain off-limits.

No production Control Center authority, execution route, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, or external action is added by v0.17.2.
