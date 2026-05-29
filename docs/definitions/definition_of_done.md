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

## v0.5.2 Stack Completion Addendum

A foundation implementation task is not done unless:

```text
It respects the Agent API Boundary.
It does not allow UI clients to bypass policy.
Mutating paths produce Event Ledger records.
Contracts/schemas are updated.
Relevant stack/boundary tests pass.
Docs and ADRs are updated if the boundary changes.
```
