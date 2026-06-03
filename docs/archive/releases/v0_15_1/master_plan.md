Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.15.1

Status: Active baseline after the M11 Runtime Readiness Taxonomy Clarification patch.

## v0.15.1 Change Log

v0.15.1 clarifies two M11 readiness review notes without starting a new milestone.

Changed:

- clarified `local_loopback_policy` in the runtime capability matrix as a supported validation-only contract.
- stated that real local loopback smoke execution remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative.
- documented `fake_manual_loopback_smoke` as a fake/test manual smoke report origin only.
- tightened manual smoke report validation so production runtime/readiness/evidence claims are rejected.
- added focused regression tests for the taxonomy clarification.
- updated active version, release, import, API, runtime, roadmap, and Foundation Gate docs.

Current baseline reminders:

- M8 simulated runtime remains simulated only.
- M9 local loopback runtime remains dev/local policy validation and simulated fallback unless a manual library path is explicitly used.
- M10 manual loopback smoke remains manual-only, disabled by default, fixed-prompt-only, loopback-only, approval-gated, and non-authoritative.
- M10.5 remote workers remain foundation-only, validation/status/dry-run only, and not live remote execution.
- private mesh/tailnet/Headscale/WireGuard/Tailscale remain planned-disabled metadata.
- Mobile Companion and Device Capability Broker remain future planning only.
- Codex plugin governance remains docs/policy only.

No runtime features, plugin enablement, plugin installs, dependencies, provider/model calls, cloud calls, remote execution, live private mesh/tailnet, mobile sensors, native builds, browser automation, Computer Use automation, scanners, Skill Factory, self-improving code, production persistence, or external actions are added by v0.15.1.
