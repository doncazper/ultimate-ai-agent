# Foundation Gate Implementation Plan v0.14.6

v0.14.6 adds Codex plugin and external tooling governance documentation checks to the existing documentation integrity and Foundation Gate stack.

Skill Package Security Rule:

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Gate addition:

- `codex_plugin_governance_docs_present` verifies the Codex plugin capability inventory, Codex plugin risk policy, external tooling canonical governance doc, and plugin enablement backlog are present.
- The criterion checks that high-risk plugins remain disabled/future-only and that Browser + Build Web Apps are future Web Control Center tooling only with approval.
- The documentation integrity verifier also checks conservative policy phrases for iOS/macOS build plugins, Chrome authenticated profile control, Computer Use, and plugin/skill installers.

Gate continuations:

- no plugin enablement.
- no plugin installation.
- no runtime feature implementation.
- no model/provider calls.
- no network calls.
- no mobile app code.
- no desktop app code.
- no native builds, Xcode workflows, simulator/device workflows, signing/provisioning/keychain access, or App Store Connect access.
- no Chrome authenticated-profile control or Computer Use automation.
- no Hugging Face jobs, uploads, or training.
- no scanners, Skill Factory, self-improving code, production persistence, or external actions.
