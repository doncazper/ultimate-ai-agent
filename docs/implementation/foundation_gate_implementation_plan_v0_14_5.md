# Foundation Gate Implementation Plan v0.14.5

v0.14.5 adds documentation integrity checks to the existing Foundation Gate and verifier stack.

Skill Package Security Rule:

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Gate addition:

- `documentation_integrity_current` verifies active documentation index, canonical document map, release docs, implementation plan, private mesh docs, mobile docs, and active version alignment.
- The criterion also checks active docs for obvious unsafe implementation claims about mobile, remote/private mesh, scanners, Skill Factory, and model/runtime features that remain planned, disabled, simulated, validation-only, dry-run-only, or blocked.

Gate continuations:

- no runtime feature implementation.
- no model/provider calls.
- no network calls.
- no mobile app code.
- no sensor APIs or OS permission integrations.
- no remote execution or tailnet/private mesh execution.
- no scanners, Skill Factory, self-improving code, production persistence, or external actions.
