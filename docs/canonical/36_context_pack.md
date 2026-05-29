# 36 — Context Pack

Status: Foundation specification, v0.4.6  
Owner: Context Pack Builder under Commander / Orchestrator  
Layer: Layer 1 Truth, Memory, and Data Ownership; Layer 3 Orchestration  
Blocking: Required before Memory Service, File Manager, Tool Broker, scanners, proactive alerts, and self-improving code are allowed to operate beyond prototypes.

## Purpose

The Context Pack is the controlled bundle of information given to an agent/model/subagent for a run or subtask. It is the opposite of dumping all memory and files into the prompt.

A Context Pack answers:

```text
What does this task need to know?
What sources are authoritative?
What is allowed to be used?
What is sensitive or forbidden?
What conflicts exist?
What must be cited or verified?
What should not be trusted as instruction?
```

## Core rule

> Agents act only on context provided through a Context Pack or through approved tool calls. Raw retrieved content is evidence, not instruction.

## Source precedence

The pack must preserve the truth hierarchy:

```text
1. Current explicit user instruction
2. Approved canonical files
3. Active feature spec
4. Recent approved decisions
5. Project memory
6. Conversation history
7. General model knowledge
8. External/untrusted content
```

External content includes webpages, Reddit posts, emails, messages, PDFs, GitHub issues, comments, and scanner results. External content may inform facts but may not override instructions, policies, canonical files, or permissions.

## Context Pack lifecycle

```text
contract_validated
  -> source_inventory
  -> retrieval
  -> filtering
  -> conflict_detection
  -> sensitivity_redaction
  -> token_budgeting
  -> source_binding
  -> pack_created
  -> pack_used
  -> pack_evaluated
```

## Required fields

```text
context_pack_id
contract_id
run_id
workspace_id
user_id
project_id
pack_scope: run | subtask | verifier | tool | memory_curator
source_precedence_policy
user_instruction_summary
project_summary
active_goal
active_spec_summary
canonical_sources
memory_sources
file_sources
tool_policy_summary
permission_policy_summary
model_policy_summary
cost_policy_summary
retrieved_items
redacted_items
excluded_items
conflicts
open_questions
assumptions
untrusted_content_boundaries
token_budget
created_at
schema_version
```

## Context types

| Context type | Source | Use |
|---|---|---|
| User instruction | current message | Highest-priority task direction |
| Project card | canonical + memory | Project goal, status, current milestone |
| User card | user memory | Stable preferences, boundaries, alert preferences |
| Canonical excerpts | files | Authoritative truth |
| Active spec | files | Requirements/design/task constraints |
| Memory snippets | Memory Service | Contextual recall, decisions, preferences |
| File snippets | File Manager | Project docs, source files, artifacts |
| Event summaries | Event Ledger | Recent run state, failures, approvals |
| Tool permissions | Consent Ledger + Tool Broker | What can be used |
| External evidence | Web/scanners/email/messages | Facts/signals only; never instructions |

## Pack scopes

```text
run
subtask
verifier
memory_curator
tool_execution
notification_decision
self_improvement_review
```

A verifier Context Pack should include the candidate output, acceptance criteria, relevant truth sources, and evidence, but should not include hidden chain-of-thought from the generator.

## Retrieval algorithm

1. Read Execution Contract.
2. Load current user instruction and conversation summary.
3. Load project card and active roadmap/Kanban state.
4. Load required canonical files and active spec files.
5. Query Memory Service for allowed scopes.
6. Query File Manager index for required file snippets.
7. Pull relevant Event Ledger summaries if the task depends on prior runs.
8. Load Consent Ledger/tool/model/cost policy summaries.
9. Retrieve external evidence only if the contract permits it.
10. Apply source precedence.
11. Detect conflicts and stale references.
12. Redact sensitive material not required for the task.
13. Fit to token budget.
14. Attach source IDs for audit and citation.
15. Persist `context_pack_created` event.

## Token budgeting

Default pack budget allocation:

```text
10% current instruction and contract
20% canonical files and active specs
20% project/user memory
15% relevant files/artifacts
10% permissions/tool/model/cost policy
10% recent event summaries
10% retrieved external evidence
5% conflict/open question notes
```

The pack builder may rebalance based on mode. For example, code tasks need more source files; research tasks need more evidence; approval tasks need more permission and risk context.

## Conflict detection

The Context Pack must flag conflicts such as:

```text
Memory contradicts canonical files.
Current user instruction changes a prior ADR.
Active spec conflicts with roadmap.
Tool permission conflicts with requested action.
External source contradicts another source.
Scanner signal is unverified.
```

Conflict output format:

```json
{
  "conflict_id": "ctx_conflict_001",
  "type": "memory_vs_canonical",
  "higher_precedence_source": "docs/canonical/03_memory_system.md",
  "lower_precedence_source": "memory:mem_123",
  "resolution": "canonical_wins",
  "requires_user_attention": false
}
```

## Sensitivity and redaction

Sensitive content should be minimized. Redaction decisions must be logged.

Sensitivity classes:

```text
public
project_private
user_private
credential_secret
personal_sensitive
regulated_sensitive
external_untrusted
```

The pack should include summaries instead of raw content when possible.

## Untrusted content boundary

Any untrusted content block must be wrapped with metadata like:

```text
content_role: evidence_only
instruction_authority: none
source_trust: unverified | corroborated | primary | official
```

This prevents webpages, emails, Reddit posts, or PDFs from controlling the agent.

## Example compact Context Pack

```json
{
  "context_pack_id": "cp_20260529_0001",
  "contract_id": "ec_20260529_0001",
  "pack_scope": "run",
  "active_goal": "Create Memory V1 spec",
  "canonical_sources": [
    {
      "path": "docs/canonical/03_memory_system.md",
      "authority": "canonical",
      "summary": "Memory uses Postgres, Memory Service API, Retain/Recall/Reflect."
    }
  ],
  "memory_sources": [
    {
      "memory_id": "mem_project_baseline",
      "summary": "Foundation-first rule blocks scanners/self-improvement until core primitives pass."
    }
  ],
  "permission_policy_summary": "File writes to draft specs allowed; external actions forbidden.",
  "conflicts": [],
  "token_budget": 12000
}
```

## Contract tests

Required tests:

```text
context_pack_applies_truth_hierarchy
context_pack_excludes_forbidden_memory_scope
context_pack_marks_external_content_as_evidence_only
context_pack_flags_canonical_memory_conflict
context_pack_logs_redactions
context_pack_fits_token_budget
context_pack_includes_acceptance_criteria_for_verifier
context_pack_blocks_tool_context_without_permission
```

## MVP implementation notes

Implement first as:

```text
Context Pack Builder service
JSON Schema validation
Deterministic source ranking
Simple token budgeter
Source/reference table
Conflict detector v1
Redaction logger
Event Ledger integration
```

Do not implement a complex auto-summarization hierarchy before basic retrieval, filtering, precedence, and logging work.
