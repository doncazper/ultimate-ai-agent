# Foundation Gate Implementation Plan v0.37.3

Status: active Foundation Gate plan.
Current active baseline: **v0.37.3**

v0.37.3 adds documentation-integrity coverage for active roadmap label
consistency. It is a docs/verifier-only repair.

Gate-adjacent coverage includes:

- active roadmap/currentness docs agree that planned `v0.38.0 / M34` is
  `Broader File Capability Review`.
- stale active M34 labels such as macOS Local Companion or Safe File Review
  Workflow are rejected by documentation integrity verification.
- archived roadmap snapshots remain historical and are excluded from active
  currentness checks.
- M34 remains planned/provisional.
- M35 remains future.
- OpenAPI path count remains `74`.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.

v0.37.3 adds no runtime behavior change, M34 implementation, backend route,
frontend feature, raw file read, context injection, memory write, execution,
dependency, generated artifact, or production authority.
