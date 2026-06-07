# Foundation Gate Implementation Plan v1.0.0

v1.0.0 adds M96 Foundation Gate coverage for Plugin Execution Sandbox, No External Plugins.

Gate coverage requires:

- M96 contract package exists
- built-in test plugin only
- sandbox required
- manifest permission checks
- audit receipt
- revocation
- deterministic safe output
- safe refs only
- no external plugin loading
- no marketplace plugin
- no arbitrary plugin code
- no runtime import
- no networked plugin fetch
- no plugin secret access
- no raw plugin payload
- no shell execution
- no network access
- no browser automation
- no filesystem mutation
- no model provider call
- no memory write
- no context injection
- no backend route
- no Control Center control
- no dependency
- no production authority
- M97 remains future

## Skill Package Security Rule

M96 does not weaken the Skill Package Security Rule. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future enablement.
