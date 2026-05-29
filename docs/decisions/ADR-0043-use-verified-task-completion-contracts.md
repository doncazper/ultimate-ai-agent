# ADR-0043: Use Verified Task Completion Contracts

Status: Accepted.
Date: 2026-05-29.

## Context

Verified Task Completion Rate was the North Star metric, but verification was not task-class specific.

## Decision

Every meaningful Execution Contract must reference a task-class Verification Contract defining acceptance criteria, required evidence, and receipt fields.

## Consequences

The agent may not mark work verified without evidence. Different task classes use different evidence: tests for code, citations for research, receipts for external actions, diffs/rollback for file mutations, and normalized envelopes for provider calls.

