# M0-M2 Build Order v0.5.1

## M0 — Repository and Canonical Foundation

Goal: Get the project into version control with validation.

Tasks:

```text
M0-001 Initialize repository
M0-002 Import canonical bundle
M0-003 Add schema validation script
M0-004 Add prompt registry validation script
M0-005 Add CI skeleton
M0-006 Add .env.example
M0-007 Add ADR index
M0-008 Create initial README for developers
```

Acceptance:

```text
All JSON files parse.
All prompt registry paths exist.
CI can run validation scripts.
Foundation-first policy is documented.
```

## M1 — Kernel Contracts

Goal: Implement Execution Contract and Context Pack primitives.

Tasks:

```text
M1-001 Create ExecutionContract model
M1-002 Create ContextPack model
M1-003 Create enums for mode/risk/autonomy/status
M1-004 Implement contract validator
M1-005 Implement context pack validator
M1-006 Implement lightweight contract creator for simple runs
M1-007 Implement persisted contract requirement checks
M1-008 Add unit tests for blocked advanced modules
```

Acceptance:

```text
A user request can produce a valid Execution Contract.
Invalid or unsafe contracts are rejected.
Context Pack can be created from stub sources.
Advanced modules are blocked until Foundation Gate.
```

## M2 — Event Ledger

Goal: Implement receipts and replayable run history.

Tasks:

```text
M2-001 Create AgentRun model
M2-002 Create EventLedgerEvent model
M2-003 Create TraceSpan model
M2-004 Implement append-only event writer
M2-005 Implement redaction helper
M2-006 Implement receipt generator
M2-007 Implement simple replay from events
M2-008 Add tests for missing-event failure cases
```

Acceptance:

```text
A run can be reconstructed from events.
Contract/context/model/tool/file/memory event stubs can be logged.
Receipts omit secrets and excluded sensitive content.
```
