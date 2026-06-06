# Foundation Gate Implementation Plan v0.82.0

v0.82.0 adds Foundation Gate coverage for M78 Plugin Manifest Security Model.

Gate criteria verify:

- M78 plugin manifest security contracts, docs, tests, and builders exist.
- Disabled plugin manifest review requires declared permissions,
  source/provenance metadata, static review, sandbox test plan, Tool Broker
  permission mapping, Event Ledger logging, version pinning, revocation, and
  human approval for high-risk capabilities.
- Plugin refs and approval refs are identifiers only.
- `approval_test_*` is denied.
- Model output and OpenWebUI output cannot authorize plugin install,
  enablement, execution, runtime imports, or production authority.
- Evaluator boundaries revalidate safety-critical fields.
- No plugin install, plugin enablement, plugin execution, runtime import,
  network access, model/provider call, browser automation, shell execution,
  mobile device access, remote execution, credentials or cookies, raw prompt,
  raw provider payload, backend route, Control Center control, dependency, or
  production authority is added.
- M79 remains future.

The OpenAPI path count remains 75.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk
capabilities before it can be trusted.
