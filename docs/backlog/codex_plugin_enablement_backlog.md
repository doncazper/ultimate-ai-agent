# Codex Plugin Enablement Backlog

Status: Future backlog, v0.14.6

This backlog tracks future work needed before Codex plugins, external build tools, or plugin installation workflows can be used beyond inventory and read-only review. It is not an implementation plan for v0.14.6 and does not enable any plugin.

## Milestone Mapping

Current:

- inventory only.
- no plugin activation.
- no dependency, build, simulator, keychain, signing, App Store Connect, Chrome authenticated profile, Computer Use, cloud job, upload, or deployment workflow.

M11 Runtime Foundation Readiness:

- no plugin activation required.
- use local shell verifiers/tests only.
- do not start Web Control Center, Mobile Companion, Desktop Companion, plugin installers, or native build workflows.

Future Web Control Center:

- Browser + Build Web Apps may be used with approval.
- Chrome authenticated profile control remains disabled unless separately approved.
- deployment and credential-bearing integrations remain out of scope unless explicitly approved.
- design tools such as Figma, Stitch, Framer, screenshot-to-code, design-to-code, and AI UI generators remain future-only and disabled unless explicitly approved.
- OpenWebUI deployment, admin/config, plugins, functions, pipelines, tools, and bridge tooling remain future-only and disabled unless a dedicated OpenWebUI integration milestone approves them.

Future OpenAPI client generation:

- shell-based generation may be considered after dependency approval.
- generated clients must be reviewed before becoming runtime dependencies.

Future Mobile Companion planning:

- docs tools only.
- no iOS or Android builds, native mobile packages, Xcode, Gradle, Android Studio, simulators, devices, sensors, OS permissions, signing, keystores, provisioning, App Store, or Play Store workflows.

Future Mobile Companion implementation:

- iOS plugin use only after dedicated approval.
- define signing, simulator, device, keychain, provisioning, App Store Connect, sensor, and entitlement boundaries first.
- Android build/tool use only after dedicated approval.
- define Gradle, Android Studio, signing, keystore, Play Store, Android permissions, background service, notification channel, sensor, and device boundaries first.

Future macOS/Desktop Companion:

- macOS plugin use only after dedicated approval.
- define signing, entitlement, keychain, local app automation, packaging, and notarization boundaries first.

Release/security audits:

- CodeRabbit/GitHub read-only review may be used with explicit review prompts.
- GitHub write, release, push, tag, or PR actions require explicit approval or direct-push rules.

## Backlog Tasks

- Define plugin approval manifest.
- Define build plugin capability firewall.
- Define signing/keychain policy.
- Define simulator/device access policy.
- Define app entitlements policy.
- Define App Store Connect no-secrets policy.
- Define Chrome profile access policy.
- Define Computer Use emergency-use policy.
- Define external review/data-sharing policy.
- Define cloud job, upload, and cost-control policy.
- Define plugin/skill installer provenance, sandbox, revocation, and disable policy.
- Define design tooling approval, import/export, artifact review, and no automatic design sync policy.
- Define OpenWebUI deployment/integration/plugin/function/pipeline/tool bridge approval policy.
- Define Android native build, signing, keystore, Play Store, permission, background service, and notification channel policy.
