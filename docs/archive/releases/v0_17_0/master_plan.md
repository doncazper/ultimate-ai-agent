Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.17.0

Status: Active baseline after the M13 Web Control Center Read-Only Frontend Shell milestone.

## v0.17.0 Change Log

v0.17.0 adds the first local web shell for the future Control Center without expanding backend authority.

Changed:

- added `apps/control-center/` React/Vite/TypeScript application.
- added typed frontend API client for existing read-only/preview-only backend routes.
- added mock fallback fixtures for local frontend development.
- added dashboard, runtime, Foundation Gate, API route, approval, remote worker, mobile planning, plugin governance, and action preview pages.
- added frontend tests and M13 Python gate integration tests.
- added Web Control Center shell docs and safety policy docs.
- updated active version, release, import, API, roadmap, documentation integrity, verifier, and Foundation Gate docs.

Current baseline reminders:

- Python Agent Core remains the brain.
- The Web Control Center shell is a user visibility and preview surface only.
- M12 backend Control Center routes remain read-only/preview-only.
- M11 runtime readiness remains report/validation only.
- M10 manual local loopback smoke remains CLI-only, manual-only, fixed-prompt-only, loopback-only, approval-gated, and non-authoritative.
- M10.5 remote workers remain foundation-only, validation/status/dry-run only, and not live remote execution.
- private mesh/tailnet/Headscale/WireGuard/Tailscale remain planned-disabled metadata.
- Mobile Companion and Device Capability Broker remain future planning only.
- Codex plugin governance remains docs/policy only.

No production Control Center authority, execution route, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, or external action is added by v0.17.0.
