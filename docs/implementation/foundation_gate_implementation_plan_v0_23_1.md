# Foundation Gate Implementation Plan v0.23.1

Status: Current Foundation Gate implementation plan for v0.23.1.

v0.23.1 keeps the M19 criterion:

- `m19_mobile_companion_contract_planning_safe`

The evaluator and verification suite verify:

- M19 mobile companion contract files exist.
- M19 mobile docs exist.
- default mobile companion manifest is contract-only.
- iOS and Android are planned/disabled only.
- contacts and calendar are planned/disabled and require a future Device
  Capability Broker.
- metadata refs reject secret-like values.
- external sends are not allowed.
- OS permission integration is not implemented.
- background services are not implemented.
- no mobile app is implemented.
- no native build workflow is added.
- no mobile sensor access is added.
- no mobile approval execution is implemented.
- Device Capability Broker is required before sensors.
- capture cannot silently become memory.
- mobile is not the agent brain.
- phone output is not trusted control input.
- OpenAPI path count remains `74`.
- v0.23.0 / M19 is implemented/released as contract/API planning only.
- M20 remains planned.
- M21-M40 remain planned/provisional.

Safety boundary:

- no M20 implementation.
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

v0.23.1 does not change the Skill Package Security Rule. It adds no plugin
enablement, tool installation, native build workflow, Computer Use automation,
Chrome authenticated profile control, or external action.

All skills are untrusted packages by default until a manifest with declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities exist.
