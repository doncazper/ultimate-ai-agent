# 53 — Structured World State

Status: Active foundation contract in v0.5.5.

## Purpose

Structured World State is the compact, exact, current state of a run or workflow. It survives transcript trimming and records what the agent has actually done, with parameters and outcomes, without relying on prose summaries.

## Relationship to nearby systems

```text
Event Ledger
  append-only full audit trail

Memory Service
  long-term recall and learning

Context Pack
  selected information for a run

World State
  compact exact state of the current run/workflow
```

The transcript is not truth. It is useful context. World State and Event Ledger are durable truth for a run.

## Requirements

- Every completed tool step that matters must append or update a World State entry.
- Entries must include step ID, actor context, tool/action, exact normalized parameters, outcome, artifact references, evidence references, rollback references, and verification status.
- World State must stay compact enough to inject into the model prompt or context pack.
- Raw large outputs do not belong in World State; store them as artifacts/event payload references.
- World State must be reproducible from Event Ledger events.
- User intent, acceptance criteria, active constraints, approvals, and open decisions must be preserved.

## Non-goals

World State is not a replacement for memory, event logging, file storage, or raw artifacts. It is the durable task-state summary needed for the agent to continue safely after context trimming or session resumption.

## Foundation rule

No long-running loop may depend on conversation history as the only record of completed steps.
