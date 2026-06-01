# Ultimate AI Agent Master Plan v0.17.1

Status: Active baseline after the Web Control Center Safety Polish and Frontend Contract Hardening patch.

## v0.17.1 Change Log

v0.17.1 hardens the M13 Web Control Center shell without starting M14 or expanding backend authority.

Changed:

- clarified the action preview UI as preview-only.
- added typed frontend endpoint allowlist helpers.
- preserved blocked preview decisions as safe non-execution results instead of generic UI failures.
- added a disabled blocked-action option so execute-like action kinds are visible as unavailable.
- added `scripts/verify_control_center_frontend.py`.
- wired the frontend safety verifier into `scripts/verify_all.py`.
- extended Foundation Gate checks for sensitive browser APIs and the standalone frontend verifier.
- expanded frontend tests for dangerous action labels, endpoint allowlists, blocked preview decisions, and frontend verifier behavior.
- updated active version, release, import, docs, and package metadata.

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

No production Control Center authority, execution route, plugin enablement, provider/model call, remote dispatch, live private mesh/tailnet, mobile sensor, native build, Chrome authenticated profile control, Computer Use automation, scanner, Skill Factory, self-improving code, production persistence, or external action is added by v0.17.1.
