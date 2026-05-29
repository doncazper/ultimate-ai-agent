# 35 — Execution Contract

Status: Foundation specification, v0.4.6  
Owner: Commander / Orchestrator  
Layer: Layer 0 Kernel and Layer 3 Orchestration  
Blocking: Required before implementation of scanners, companion proactivity, Skill Factory, self-improving code, or autopilot workflows.

## Purpose

The Execution Contract is the agent run agreement. It converts a user request into a typed, testable, auditable unit of work before the system starts acting.

The contract answers:

```text
What is the user asking for?
What project/workspace does it belong to?
What output must be delivered?
What assumptions are being made?
What context is allowed?
What tools, files, models, and subagents may be used?
What level of autonomy is allowed?
What risks or approvals apply?
How will we know the task is complete?
What must be logged, updated, or rolled back?
```

The Execution Contract is not a plan by itself. It is the binding envelope around the plan.

## Core rule

> No meaningful agent run may use tools, mutate files, write memory, execute code, call scanners, send notifications, or route to high-cost/high-risk models without an Execution Contract.

For very small conversational answers, a lightweight implicit contract may be created internally. For any project, tool, file, code, memory, external, proactive, or self-improving workflow, the contract must be persisted in the Event Ledger.

## Relationship to other foundation modules

```text
User message
  -> Orchestrator creates Execution Contract
  -> Context Pack Builder gathers allowed context
  -> Model Router chooses model/runtime per step
  -> Tool Broker authorizes actions
  -> Event Ledger records lifecycle
  -> QA/Evals check acceptance criteria
  -> Memory/File systems update only through approved pathways
```

The Execution Contract is upstream of:

```text
Context Pack
Model Route
Subagent Task Contract
Tool Call Request
Approval Request
Memory Write Request
File Operation Request
QA/Eval Run
Rollback Plan
```

## Contract lifecycle

```text
draft
  -> validated
  -> context_bound
  -> planned
  -> executing
  -> waiting_for_approval
  -> verifying
  -> completed
  -> failed
  -> cancelled
  -> superseded
```

### State definitions

| State | Meaning | Allowed transitions |
|---|---|---|
| draft | Contract extracted from request but not validated | validated, cancelled |
| validated | Required fields and policy checks pass | context_bound, cancelled |
| context_bound | Context Pack attached and source precedence checked | planned, failed |
| planned | Plan/subtasks/model routes prepared | executing, waiting_for_approval, cancelled |
| executing | Work is being done | waiting_for_approval, verifying, failed, cancelled |
| waiting_for_approval | Human approval required before continuing | executing, cancelled |
| verifying | QA/evals/acceptance checks are running | completed, failed |
| completed | Acceptance criteria met and updates recorded | archived |
| failed | Contract could not be completed | archived, superseded |
| cancelled | User/system stopped run | archived |
| superseded | A newer contract replaced this one | archived |

## Required fields

Every persisted Execution Contract must include:

```text
contract_id
run_id
workspace_id
user_id
project_id, if known
origin: user_request | scheduled_task | scanner_event | system_event | retry | replay
request_summary
goal
deliverable
mode
risk_level
autonomy_level
status
assumptions
unknowns
constraints
acceptance_criteria
required_context
forbidden_context
allowed_tools
forbidden_tools
required_models_or_model_classes
required_subagents
approval_policy
privacy_policy
cost_policy
rollback_policy
event_logging_policy
canonical_files_to_read
canonical_files_to_update
memory_scopes_to_read
memory_scopes_to_write
created_at
updated_at
schema_version
```

## Modes

The contract mode must be one of:

```text
answer
research
create
execute
manage
spec
code
review
monitor
notify
self_improve
```

Mode definitions:

| Mode | Meaning | Spec required? |
|---|---|---|
| answer | Direct answer, no durable mutation | no |
| research | Gather and synthesize information | maybe |
| create | Produce artifact | maybe |
| execute | Take action through tools | yes for external/mutating actions |
| manage | Maintain project/workflow state | yes |
| spec | Create/update requirements/design/tasks/tests | yes |
| code | Generate/modify/run code | yes |
| review | QA, critique, audit, eval, security review | maybe |
| monitor | Scanner/watchlist/digest activity | yes for recurring monitors |
| notify | Proactive alert or digest | yes for interrupt alerts |
| self_improve | Modify agent code/skills/prompts/policies | yes + high assurance |

## Autonomy levels

```text
0 answer_only
1 draft_only
2 recommend
3 prepare_and_request_approval
4 execute_reversible_trusted_action
5 execute_approved_recurring_workflow
```

The contract must never grant higher autonomy than the current Consent Ledger and project policy allow.

## Risk levels

```text
low
medium
high
critical
```

Critical risk examples:

```text
external sending/publishing
financial transactions
production changes
credential/permission changes
self-modifying code
user data deletion/export
scanner-derived interruption alerts
security-sensitive code or infrastructure
```

Critical contracts require explicit approval, QA/eval verification, Event Ledger completeness, and rollback strategy.

## Acceptance criteria

Acceptance criteria must be concrete and testable.

Bad:

```text
Make it good.
```

Good:

```text
- A requirements.md, design.md, tasks.md, test_plan.md, and acceptance.md file exist.
- Each requirement has a stable ID.
- The spec references affected canonical files.
- QA checklist passes with no high-severity gaps.
```

Every contract should distinguish:

```text
Definition of Done for this run
Quality checks
Non-goals
Known limitations
Follow-up tasks
```

## Contract creation algorithm

1. Parse user request.
2. Identify project/workspace.
3. Classify mode and risk.
4. Determine whether explicit spec is required.
5. Determine autonomy ceiling from Consent Ledger and project policy.
6. Identify canonical files, memory scopes, files, tools, models, and subagents needed.
7. Identify assumptions, unknowns, and blockers.
8. Produce acceptance criteria.
9. Validate contract against schemas and policy.
10. Persist contract and `contract_created` event.
11. Build Context Pack.

## Clarification policy

The agent may ask a clarifying question only when:

```text
The missing detail materially changes the outcome;
The task cannot be completed safely without it;
The user explicitly asked for a precise output that cannot be inferred;
Or approval/consent is required.
```

Otherwise, the contract should record assumptions and proceed.

## Contract validation rules

A contract is invalid if:

```text
It lacks an acceptance criterion.
It requests a forbidden tool or context scope.
It exceeds the user's autonomy consent.
It omits approval for high/critical risk actions.
It allows external action based only on untrusted scanner/web/email content.
It conflicts with canonical files without flagging the conflict.
It proposes self-improving code without branch/test/approval gates.
It has no rollback policy for mutating actions.
It has no event logging policy.
```

## Output contract for subagents

When the Orchestrator delegates to a specialist, the subagent gets a smaller Subtask Contract:

```text
parent_contract_id
subtask_id
role
objective
inputs
constraints
allowed_tools
forbidden_tools
required_output_schema
acceptance_criteria
risk_level
return_expected_by_step
```

Subagents should not receive broad global context unless needed.

## Example: Memory V1 spec creation

```json
{
  "contract_id": "ec_20260529_0001",
  "mode": "spec",
  "risk_level": "medium",
  "autonomy_level": 2,
  "goal": "Create the Memory V1 feature spec for the Ultimate AI Agent.",
  "deliverable": "Feature spec folder with requirements, design, tasks, test plan, and acceptance criteria.",
  "canonical_files_to_read": [
    "docs/canonical/03_memory_system.md",
    "docs/canonical/31_layered_brain_architecture.md",
    "docs/canonical/34_foundation_change_management_and_contract_testing.md"
  ],
  "canonical_files_to_update": [],
  "allowed_tools": ["file.read", "file.write", "memory.read", "memory.write"],
  "approval_policy": "no external or destructive action; no human approval required for draft files",
  "acceptance_criteria": [
    "requirements.md exists and uses requirement IDs",
    "design.md describes Memory Service API and storage model",
    "tasks.md maps to implementation sequence",
    "test_plan.md includes memory recall and supersession tests",
    "acceptance.md states Foundation Gate criteria"
  ]
}
```

## Contract tests

Required tests:

```text
contract_requires_acceptance_criteria
contract_blocks_high_risk_without_approval
contract_respects_consent_autonomy_ceiling
contract_requires_rollback_for_mutating_actions
contract_flags_canonical_memory_conflict
contract_requires_spec_for_foundation_change
contract_blocks_scanner_ready_before_foundation_gate
contract_blocks_self_improvement_without_tests_and_branch
```

## MVP implementation notes

Implement first as:

```text
TypeScript or Python dataclass/Pydantic model
JSON Schema validation
Postgres table: execution_contracts
Event Ledger records contract lifecycle
Simple policy engine for risk/autonomy validation
Contract test suite in CI
```

Do not start with a complex workflow engine. Start with typed contracts, validation, persistence, and tests.
