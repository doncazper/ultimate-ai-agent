# Foundation Gate Eval v0.5.0

Status: Active gate for moving beyond foundation work.

## Purpose

Prevent advanced modules from being built on unstable foundations.

## Gate prerequisites

```text
Execution Contract schema and validation
Context Pack schema and builder
Event Ledger and replay harness
Consent Ledger
Tool Broker
Memory Service
File Manager
Model Router
Cost Governor minimal policy
Rollback metadata interface
Capability Registry and Dependency Graph
Contract test matrix
Shadow replay fixtures
```

## Required demo

The system must complete the Memory V1 spec generation vertical slice end-to-end with:

```text
valid Execution Contract
valid Context Pack
logged model route
File Manager-created spec files
Memory Service source-linked memory write
Tool Broker-controlled file/memory operations
Event Ledger receipt
QA/eval pass
rollback metadata for file writes
```

## Pass criteria

```text
All critical tests pass.
No direct tool/file/memory writes bypass brokers/services.
No private context routes contrary to consent.
No advanced modules in Ready for Build.
Run replay reconstructs success and failure cases.
User-facing receipt accurately summarizes actions taken.
```

## Gate decision states

```text
not_started
in_progress
blocked
failed
passed_with_limitations
passed
```

`passed_with_limitations` may allow low-risk advanced shaping work, but not high-autonomy implementation.
