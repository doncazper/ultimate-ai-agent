Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.14.6

Status: Active baseline after the Codex plugin and external build tool governance inventory patch.

## v0.14.6 Change Log

This is a docs/governance patch on top of the accepted v0.14.5 foundation. It does not start M11.

Documentation and policy changes:

- Codex plugin capability inventory added under `docs/tooling/`.
- Codex plugin risk policy added under `docs/tooling/`.
- external tooling and Codex plugin governance canonical doc added.
- Codex plugin enablement backlog added.
- documentation integrity verifier extended to check the governance docs.
- Foundation Gate documentation criterion extended for Codex plugin governance docs.
- active README, import, master plan, roadmap, API docs, mobile docs, documentation index, canonical map, release notes, and Foundation Gate plan are synchronized.

Current baseline reminders:

- M10 manual local loopback smoke remains manual-only, disabled by default, approval-gated, loopback-only, and fixed-prompt-only.
- M10.5 remote workers remain foundation-only, validation/status/dry-run only, and not live remote execution.
- v0.14.3 private mesh taxonomy remains planned/disabled metadata only, with Headscale and generic WireGuard evaluated before proprietary control-plane assumptions.
- v0.14.4 mobile companion and Device Capability Broker work remains future planning only.
- v0.14.5 documentation integrity remains active.
- v0.14.6 plugin governance is docs/policy-only.

Tooling policy:

- Browser + Build Web Apps may be considered for future Web Control Center work with explicit approval.
- Chrome authenticated profile control remains disabled unless explicitly approved.
- Build iOS Apps / XcodeBuildMCP remains disabled until a dedicated Mobile Companion implementation milestone.
- Build macOS Apps remains disabled until a dedicated Desktop/macOS Companion milestone.
- CodeRabbit/GitHub read-only review can be used for release readiness with explicit review prompts.
- GitHub write/release actions require explicit approval or direct-push rules.
- Computer Use remains disabled except explicit last-resort manual QA approval.
- Hugging Face Jobs, uploads, training, and Spaces deployment remain disabled.
- Plugin/skill installers remain disabled until Skill lifecycle security exists.
- Shell/exec commands are allowed narrowly for local verifier, test, grep, git, and script workflows only.

No runtime features, plugin enablement, plugin installs, dependencies, model/provider calls, network calls, mobile app code, desktop app code, native builds, Xcode/macOS/iOS workflows, simulator/device code, keychain/signing/provisioning access, App Store Connect access, Chrome authenticated-profile use, Computer Use automation, cloud jobs/uploads/training, scanners, Skill Factory, self-improving code, production persistence, or external actions are added by v0.14.6.
