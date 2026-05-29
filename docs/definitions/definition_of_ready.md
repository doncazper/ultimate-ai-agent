# Definition of Ready v0.5.0

A foundation item can enter Ready for Build only if:

```text
Execution Contract impact is understood.
Context Pack impact is understood.
Required schemas exist or are in the task.
Event Ledger events are defined.
Consent/permission implications are defined.
Tool Broker implications are defined.
Memory/File implications are defined.
Model Router and Cost Governor implications are defined.
Rollback story is defined for mutations.
Contract tests are listed.
Acceptance criteria are testable.
Canonical files affected are listed.
```

Advanced modules cannot enter Ready for Build until Foundation Gate passes.

## v0.5.2 Stack Readiness Addendum

A foundation implementation task is not ready unless it states:

```text
Which runtime owns it: Python Agent Core, TypeScript Control Center, OpenWebUI shell, worker, or tool server.
Which API boundary it uses.
Whether it mutates durable state.
Whether it requires Event Ledger logging.
Whether it can be triggered from UI clients.
Whether bypass-prevention tests are required.
```
