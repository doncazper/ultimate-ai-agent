# 47 — Idempotency and Retry Policy

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

Retries are unavoidable. The agent will retry model calls, provider calls, tool calls, file operations, event writes, and later external actions. Without idempotency, a retry can create duplicate files, duplicate memory, duplicate notifications, or repeated external side effects.

## Core rule

> Any operation that mutates state, writes memory/files, sends notifications, charges cost, calls external providers, or can be retried must carry an `idempotency_key` and declare a retry policy.

## Required identifiers

```text
run_id
step_id
trace_id
correlation_id
causation_id
idempotency_key
attempt_number
dedupe_key
```

## Identifier meanings

- `run_id`: the full agent run.
- `step_id`: one step within the run.
- `trace_id`: cross-service trace identifier.
- `correlation_id`: groups related operations across services.
- `causation_id`: points to the event or action that caused this operation.
- `idempotency_key`: prevents duplicate effects for the same logical operation.
- `attempt_number`: increments on retry.
- `dedupe_key`: domain-level duplicate detector, especially for memory/news/provider results.

## Retry classes

```text
never_retry
safe_retry
retry_with_same_idempotency_key
retry_after_backoff
manual_review_required
```

## Rules by operation type

| Operation | Policy |
|---|---|
| Pure validation | safe_retry |
| Read-only local query | safe_retry |
| Read-only provider call | retry_after_backoff |
| File write | retry_with_same_idempotency_key |
| Memory write | retry_with_same_idempotency_key + dedupe_key |
| Notification send | retry_with_same_idempotency_key + external receipt check |
| Email/message send | manual_review_required after uncertain failure |
| Payment/destructive action | never_retry unless explicit external idempotency exists |

## Unknown outcome rule

If the agent cannot determine whether a mutable external action succeeded, it must not retry blindly. It should mark the operation `outcome_unknown`, create a review item, and ask for human confirmation or use provider-specific receipt lookup.

## Minimum implementation for M0/M1

- Define schema.
- Add helper for deterministic idempotency key creation from operation inputs.
- Add tests that repeated idempotency keys are recognized as duplicates.
- Do not implement external mutable retries yet.
