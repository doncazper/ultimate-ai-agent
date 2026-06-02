# Foundation Gate Implementation Plan v0.24.0

Status: Current Foundation Gate implementation plan for v0.24.0.

v0.24.0 adds the M20 criterion:

- `m20_device_capability_broker_contract_safe`

The evaluator and verification suite verify:

- M20 device capability contract files exist.
- M20 device capability docs exist.
- default device capability manifest is contract-only.
- CCC iOS, CCC Android, CCC macOS, and mobile web/PWA are planned surfaces only.
- all device capabilities have `allowed_now=False`.
- all device capabilities have `implemented_now=False`.
- sensor capabilities require a future Device Capability Broker.
- silent capture is rejected.
- automatic memory writes are rejected.
- external sends are rejected.
- raw payloads are rejected.
- background capture is rejected.
- OS permission integration is rejected.
- background service runtime is rejected.
- mobile/device authority is rejected.
- metadata refs and metadata reject secret-like values.
- no native app directories or files exist.
- no sensor APIs exist in implementation.
- no backend mobile/device routes are added.
- OpenAPI path count remains `74`.
- M21 remains planned/provisional.

Safety boundary:

- no sensor implementation.
- no backend API route.
- no Android app.
- no iOS app.
- no macOS app.
- no native build workflow.
- no runtime execution.
- no model/provider calls.
- no remote execution.
- no plugin enablement.
- no mobile sensor access.
- no OS permission integration.
- no background service.
- no notification runtime.
- no dependency.
- no production Control Center authority.

## Skill Package Security Rule

v0.24.0 does not change the Skill Package Security Rule. It adds no plugin
enablement, tool installation, native build workflow, Computer Use automation,
Chrome authenticated profile control, or external action.

All skills are untrusted packages by default until a manifest with declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.
