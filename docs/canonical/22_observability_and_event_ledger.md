# 22 — Observability and Event Ledger

Status: Foundation specification, v0.4.7  
Owner: Platform / Runtime  
Layer: Layer 0 Kernel; Layer 1 Truth/Data Ownership; Layer 3 Orchestration  
Blocking: Required before self-improving code, scanner alerts, external execution, or autopilot workflows.

## Purpose

The Event Ledger is the black-box recorder for the Ultimate AI Agent. It records what the agent did, why it did it, what context it used, what tools it called, what approvals it requested, what it changed, what it cost, and how it was verified.

Observability is the system that makes that ledger usable for debugging, audit, replay, cost control, safety review, and user trust.

## Core rule

> If the agent cannot produce a receipt for a meaningful action, the action is not allowed in production.

## What must be recorded

Every meaningful run must record:

```text
Run created
Execution Contract created/validated
Context Pack created
Model route selected
Subagent calls
Tool call requested/authorized/executed/failed
File operation proposed/applied
Memory read/write/supersede/delete
Approval requested/granted/denied/expired
External source read
Code execution started/completed/failed
Eval/test started/completed/failed
Notification decision
Cost estimate and actual cost
Rollback plan created/executed
Final delivery
Post-run memory/canonical updates
```

## Event model

The ledger is append-only. Corrections are new events, not overwritten history.

Required event fields:

```text
event_id
run_id
contract_id, optional but required for meaningful runs
event_type
actor_type: user | orchestrator | subagent | tool | model_router | system | evaluator
actor_id
timestamp
workspace_id
project_id
correlation_id
parent_event_id
input_refs
output_refs
policy_refs
risk_level
sensitivity
summary
payload
redaction_status
cost_estimate
actual_cost
latency_ms
status
schema_version
```

## Event categories

```text
contract
context
model_route
subagent
tool
file
memory
approval
web_or_scanner
code_execution
eval
notification
cost
rollback
error
delivery
```

## Run state

The run state is derived from ledger events, not manually mutated state.

```text
created
contracted
context_bound
planned
executing
waiting_for_approval
blocked
verifying
completed
failed
cancelled
rolled_back
archived
```

## Receipts

For user-facing trust, the system should create receipts for actions.

Receipt examples:

```text
I updated these files: ...
I used these sources: ...
I read these memories: ...
I requested approval for this reason: ...
I ran these tests and they passed/failed: ...
I did not perform external actions.
```

Receipts should be concise by default but expandable.

## Trace levels

| Level | Name | Contents | Use |
|---|---|---|---|
| 0 | minimal | run summary, final output | simple answers |
| 1 | standard | contract, context refs, tools, files, memory, costs | normal project work |
| 2 | detailed | model routes, subagents, eval steps, source refs | debugging/review |
| 3 | forensic | full structured payloads, redaction log, replay data | high-risk/security incidents |

Default: Level 1 for project/tool work. Level 2 for foundation modules, code execution, and approvals. Level 3 only when required because it may contain sensitive information.

## Privacy and redaction

The ledger must support:

```text
payload redaction
secret masking
sensitive-field hashing
raw-content avoidance
source references instead of full content
retention policies by event type
user export/delete where allowed
legal hold or audit lock where required
```

Sensitive raw email/message content should not be copied into general event payloads unless explicitly required and permitted.

## Replay and shadow mode

The ledger must support replay of prior runs against new foundation code.

Replay modes:

```text
dry_replay: no tools, compare decisions
shadow_replay: use sandbox tools/mock outputs
regression_replay: compare old vs new contract/context/tool decisions
incident_replay: reconstruct failure sequence
```

Replay is mandatory before changing foundation contracts.

## Storage recommendation

Start with Postgres tables:

```text
agent_runs
execution_contracts
context_packs
event_ledger_events
trace_spans
tool_call_logs
approval_events
cost_events
artifact_refs
redaction_logs
```

Large payloads should go to object storage with references in the ledger.

## Observability UI

The User Control Center should expose:

```text
Activity Log
Approvals Queue
Memory Changes
File Changes
Tool Calls
Scanner/Notification Decisions
Cost View
Errors and Retries
Rollback History
```

Developer/admin views should include:

```text
Trace explorer
Run replay
Event search
Cost by model/tool/project
Eval results
Foundation contract failures
```

## Error handling

Errors must be first-class events with:

```text
error_type
message
stack_or_tool_output_ref
retryable
retry_count
user_visible_summary
recovery_action
rollback_required
```

Do not hide tool/model failures behind polished final answers.

## Required contract tests

```text
event_ledger_records_contract_creation
event_ledger_records_context_pack_creation
event_ledger_records_model_route_decision
event_ledger_records_tool_authorization_and_result
event_ledger_records_memory_write_source
event_ledger_records_file_diff_and_apply
event_ledger_records_approval_decision
event_ledger_replay_reconstructs_run_state
event_ledger_redacts_secrets
event_ledger_costs_roll_up_by_project
```

## MVP implementation notes

Implement first:

```text
Postgres append-only event table
agent_runs table
trace span table
artifact reference table
redaction utility
run receipt generator
basic run replay harness
Event Ledger SDK used by Orchestrator, Model Router, Tool Broker, Memory Service, File Manager, and QA
```

Do not build a complex analytics dashboard before the ledger itself is correct and complete.
