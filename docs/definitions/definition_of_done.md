# Definition of Done v0.5.0

A foundation item is Done only when:

```text
Code or schema is implemented.
Schema validation passes.
Contract tests pass.
Event Ledger integration is present.
Permission/consent checks are present where applicable.
Tool Broker integration is present where applicable.
Rollback metadata exists for mutations.
Docs/canonical files are updated.
ADR is updated if architecture changed.
Eval or replay case is added.
Capability Registry and Dependency Graph are updated.
No blocked advanced module depends on unstable internals.
```

A feature is not Done just because it works once. It is Done when it is testable, logged, permissioned, and safe to build on.
