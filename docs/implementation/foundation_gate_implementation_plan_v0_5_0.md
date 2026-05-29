# v0.5.0 — Foundation Gate Implementation Plan

Status: Implementation planning baseline  
Purpose: Convert v0.4.x foundation specs into a buildable sequence that proves the core before advanced modules begin.

## Core objective

Build the foundation so higher-order modules can safely depend on it.

The Foundation Gate passes only when the system can execute the first vertical slice end-to-end:

```text
User asks for Memory V1 spec
-> Orchestrator creates Execution Contract
-> Context Pack loads canonical/memory/file/project truth
-> Model Router selects model classes
-> File Manager creates feature spec files through patch/write APIs
-> Memory Service writes source-linked project memory
-> Event Ledger records every meaningful step
-> Consent Ledger and Tool Broker enforce permissions
-> QA/evals verify acceptance criteria
-> Receipt is generated
```

## Modules included in Foundation Gate

```text
Execution Contract
Context Pack
Event Ledger / Observability
Consent and Permissions Ledger
Tool Broker
Memory Service
File Manager
Model Router
Cost Governor minimal integration
Rollback primitives
Capability Registry / Dependency Graph
Contract Tests
Shadow Replay Harness
```

## Modules explicitly blocked until gate passes

```text
Reddit Scanner
News Scanner
Weather Module
Email Scanner
Message Scanner
Calendar Scanner
Proactive Intelligence
Companion Proactivity
Skill Factory
Self-Improving Coding Framework
Autopilot Workflows
External execution with high autonomy
```

## Build sequence

### M0 — Repository and canonical foundation

Deliverables:

```text
Repo initialized
Canonical docs committed
Schemas committed
ADR index committed
Kanban board committed
CI skeleton created
```

Acceptance:

```text
All foundation docs and schemas are in version control.
Schema validation runs in CI.
```

### M1 — Kernel contracts

Deliverables:

```text
Execution Contract model
Context Pack model
Policy enums for mode/risk/autonomy/status
Validation library
Contract creation tests
```

Acceptance:

```text
A user request can produce a valid Execution Contract.
Invalid high-risk contracts are blocked.
A Context Pack can be constructed from stubbed sources.
```

### M2 — Event Ledger

Deliverables:

```text
agent_runs table
event_ledger_events table
trace_spans table
Event SDK
Receipt generator v1
Replay harness v1
```

Acceptance:

```text
A run can be reconstructed from events.
Contract/context/model/tool/file/memory events are logged.
Secrets are redacted.
```

### M3 — Consent Ledger and Tool Broker

Deliverables:

```text
consent_grants table
approval_requests table
tool registry
tool manifest validation
mock file/memory/code/web tools
dry-run and rollback metadata interfaces
```

Acceptance:

```text
Tool request outside contract is blocked.
Tool request without consent is blocked.
External/high-risk action requires approval.
Mock tools log complete receipts.
```

### M4 — Memory Service and File Manager

Deliverables:

```text
memories table
memory_sources/versions tables
Memory Service API
workspace File Manager
patch proposal/apply
canonical/spec generators
file manifest/index v1
```

Acceptance:

```text
Project memory can be written/recalled with source links.
Canonical/spec files can be created through File Manager.
File changes are diffed, logged, and rollback-ready.
Canonical precedence eval passes.
```

### M5 — Orchestrator minimal vertical slice

Deliverables:

```text
Commander run loop
Contract creation
Context Pack creation
Model Router integration
Tool Broker integration
File/Memory operations
QA checklist
Final receipt
```

Acceptance:

```text
The Memory V1 spec generation demo runs end-to-end with logs, files, memory, and QA.
```

### M6 — Contract tests, shadow mode, and gate decision

Deliverables:

```text
Foundation contract test suite
Replay tests
Shadow mode with mock tools
Foundation Gate eval report
Known limitations list
Blocked-module review
```

Acceptance:

```text
Foundation Gate eval passes.
No blocked advanced module is marked Ready for Build.
Failure/rollback paths are demonstrated.
```

## Contract test matrix

The first implementation must include at least these tests:

```text
execution_contract_validation
context_pack_precedence_and_redaction
event_ledger_reconstructs_run
event_ledger_redacts_secret
tool_broker_blocks_forbidden_tool
tool_broker_requires_approval_for_external_action
consent_revocation_blocks_future_action
memory_write_requires_source
memory_supersession_excludes_old_memory
file_patch_is_hash_guarded
file_write_has_rollback_ref
model_router_respects_privacy_policy
cost_governor_blocks_over_budget_run
foundation_blocks_scanner_ready_state
shadow_replay_detects_changed_foundation_decision
```

## First vertical slice task

Create:

```text
docs/specs/feature-memory-v1/requirements.md
docs/specs/feature-memory-v1/design.md
docs/specs/feature-memory-v1/tasks.md
docs/specs/feature-memory-v1/test_plan.md
docs/specs/feature-memory-v1/acceptance.md
```

Required events:

```text
run_created
contract_created
contract_validated
context_pack_created
model_route_selected
file_patch_proposed
file_patch_applied
memory_write_requested
memory_written
qa_eval_started
qa_eval_completed
final_delivery_created
receipt_created
```

## Foundation Gate pass criteria

```text
100% of critical contract tests pass.
No high-risk action can bypass consent/tool broker.
Every mutating action has a logged rollback plan or explicit irreversible flag.
Context Pack eval shows no forbidden-scope leakage.
Event replay reconstructs at least one successful and one failed run.
Memory recall returns active source-linked memory and excludes superseded memory.
File Manager creates/updates canonical/spec files atomically.
Model Router logs route decisions and respects privacy/cost policies.
Blocked advanced modules remain blocked in Kanban/capability registry.
```

## Foundation Gate fail criteria

Fail the gate if:

```text
Any tool can bypass Tool Broker.
Any memory write can occur without source/event/consent.
Any file write can overwrite canonical files without diff/log.
Any external action can proceed without approval when required.
Any private context can be routed contrary to consent.
Event Ledger cannot reconstruct the run.
Advanced modules move to Ready for Build prematurely.
```

## Implementation philosophy

Build narrow but real. Do not fake the contracts.

The first implementation should be small, but every primitive should be real enough that advanced modules can later depend on it without rewriting the foundation.
