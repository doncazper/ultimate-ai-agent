# ADR-0034: Use Execution Contracts for All Meaningful Agent Runs

Status: Accepted in v0.4.6

## Context

The Ultimate AI Agent will use memory, files, code execution, web research, scanners, notifications, skills, and self-improving code. Without a typed contract, runs become hard to audit, approve, test, or rollback.

## Decision

Every meaningful agent run must create and validate an Execution Contract before acting. The contract defines goal, deliverable, mode, risk, autonomy, context, tools, models, approvals, costs, rollback policy, event logging, and acceptance criteria.

## Consequences

Positive:
- Makes agent behavior inspectable and testable.
- Allows Tool Broker, Consent Ledger, Model Router, and Event Ledger to enforce consistent policy.
- Supports replay, QA, rollback, and foundation contract testing.

Tradeoffs:
- Adds overhead for small tasks.
- Requires careful lightweight path for simple answers.

## Implementation note

Simple conversational answers may use implicit lightweight contracts. File, code, memory, tool, scanner, external, proactive, and self-improving workflows require persisted contracts.
