Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.5.3

Status: Active pre-coding foundation baseline.

## Purpose

The Ultimate AI Agent is a Commander-led, spec-driven, memory-backed, relationship-aware AI operating system that turns vague goals into verified completed outcomes while remaining inspectable, permissioned, reversible, modular, scalable, and user-controlled.

v0.5.3 is a remediation release. It addresses the legitimate findings from Claude's v0.4.1 review and recent provider/credential design discussions. It does not implement advanced features. It tightens the foundation before coding begins.

## Source-of-truth rule

Canonical files define active truth. Versioned master plans are historical planning records.

```text
1. Current explicit user instruction
2. Active canonical files
3. Active feature spec
4. Accepted ADRs
5. Project memory
6. Historical master plans
7. Conversation history
```

The active roadmap is `docs/canonical/09_roadmap.md`. This master plan intentionally does not duplicate milestone definitions.

## Remediated review issues

| Issue | v0.5.3 action |
|---|---|
| A1 Verified Task Completion undefined | Added `39_verified_task_completion_framework.md` and task verification schema. |
| A2 Durable execution undecided | Added ADR-0040: custom event ledger + deterministic state machine first. |
| A3 Cost attribution too coarse | Added event-level `cost_attribution` schema field. |
| A4 Secret storage unspecified | Added Secret Broker + Provider Registry module and ADR-0041. |
| A5 Memory retrieval underspecified | Added Memory Retrieval V1: pgvector + full-text + reranking. |
| A6 Autonomy tiers undefined | Added autonomy levels L0-L5 and standing approval rules. |
| A7 First slice too text-only | Added Minimum Lovable Kernel with real file mutation and rollback. |
| A8 Contracts frozen too early | Marked M1 contracts as v0/provisional until Foundation Gate. |
| A9 Self-improvement boundary vague | Added explicit Trusted Computing Base and ADR-0042. |
| A10 Scope too large | Added Minimum Lovable Kernel before broader M0-M6 commitment. |
| B1 Contradictory roadmaps | Active roadmap moved to canonical pointer; no duplicate roadmap in v0.5.3 plan. |
| B2 Template-like canonical docs | Filled foundation-critical canonical docs 20, 23-25, 27-30, and 33. |

## Foundation kernel

The Foundation Gate requires the following primitives before advanced modules:

```text
Execution Contract
Context Pack
Verified Task Completion contracts
Event Ledger and deterministic run state machine
Consent Ledger
Tool Broker
Secret Broker
Provider Registry
Model Router
Cost Governor
Memory Service and retrieval stack
File Manager
Rollback primitives
API boundary
Contract tests and shadow replay
Trusted Computing Base
```

## Free-first provider strategy

The system prefers free/no-key providers where practical, while supporting user-connected API keys through a Secret Broker.

```text
Free no-key provider
→ free provider requiring key
→ user-connected provider
→ paid provider within budget
→ enterprise/self-hosted provider
```

Secrets never enter chat, prompts, memory, logs, event payloads, canonical files, or source control.

Provider outputs are normalized into common result envelopes before any agent consumes them.

## Minimum Lovable Kernel

Before advanced modules, build one real end-to-end task:

```text
User asks the agent to create a project note/spec artifact.
Execution Contract is created.
Context Pack is assembled.
Consent is checked.
Tool Broker calls File Manager.
File is written to the project workspace.
Event Ledger records the mutation with event-level cost attribution.
Rollback plan is created.
QA verifies file existence and receipt validity.
Memory writes a source-linked summary.
User receives a receipt.
```

This proves the agent's operating system rather than merely generating text about itself.

## Advanced modules remain blocked

Do not build the following until the Foundation Gate passes:

```text
Reddit Scanner
News Scanner
Weather Module beyond safe provider-normalization prototype
Email Scanner
Message Scanner
Calendar Scanner
Companion proactivity
Skill Factory
Self-improving coding framework
Autopilot workflows
External high-autonomy execution
Provider-specific integrations that require credentials
```

## Implementation posture

Start with schemas, validators, event models, and contract tests. Avoid feature work. Preserve versioned contracts as provisional until at least the Minimum Lovable Kernel exercises them.
