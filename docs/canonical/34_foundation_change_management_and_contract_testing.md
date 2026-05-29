# 34 Foundation Change Management and Contract Testing

Status: Canonical draft, v0.4.1

## Purpose

Make it safe to change foundational code without toppling higher-level capabilities.

## Foundation capabilities

```text
Execution Contract
Context Pack
Run/Event Ledger
Memory Service
File Manager
Consent/Permission Ledger
Tool Broker
Capability Registry
Rollback primitives
Contract Test Runner
Shadow Replay Harness
```

## Foundation-first rule

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, tool broker, and contract tests work.

## Foundation change process

1. Create foundation change proposal.
2. Identify affected contracts.
3. Query capability dependency graph.
4. Produce blast-radius report.
5. Update schema/API versions.
6. Add or update contract tests.
7. Run regression evals.
8. Replay golden traces in shadow mode.
9. Ship behind feature flag if user-facing.
10. Canary if applicable.
11. Monitor traces, costs, failures, and user impact.
12. Keep rollback ready.
13. Update canonical files, ADRs, and memory.

## Contract tests required

```text
Execution Contract compatibility
Context Pack compatibility
Tool Broker permission enforcement
Consent Ledger deny-by-default behavior
Memory Service source citation and supersession
File Manager diff/patch behavior
Event Ledger trace completeness
Rollback metadata availability
Capability Registry dependency resolution
```

## Golden traces

At minimum, maintain traces for:

```text
Create Memory V1 spec
Update canonical file safely
Retrieve project memory and produce context pack
Use Tool Broker with approval required
Attempt blocked scanner before Foundation Gate
```

## No-go policy

A foundation change cannot release if:

```text
Contract tests fail
Shadow replay fails without accepted explanation
Capability dependency graph is not updated
Rollback plan is missing
Permission behavior changes without review
Trace completeness regresses
```
