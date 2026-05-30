# 43 — Minimum Lovable Kernel

Status: Foundation build target, v0.5.3
Owner: Product / Runtime

## Purpose

The Minimum Lovable Kernel is the smallest real agent operating system that proves the foundation works without building the ambitious modules too early.

It is smaller than the full M0-M6 foundation but stronger than a text-only spec-generation demo.

## Required slice

```text
User asks agent to create a local project note/spec artifact.
Execution Contract is created.
Context Pack is assembled.
Consent is checked.
Tool Broker routes the File Manager call.
File Manager writes a real file.
Event Ledger records every meaningful step.
Cost attribution exists at event level.
Rollback metadata is generated.
QA verifies file exists and receipt is valid.
Memory Service writes a source-linked summary.
User receives a receipt.
```

## Why this slice

It exercises:

```text
contracts
context
permissions
tool execution
file mutation
observability
rollback
verification
memory write
receipt generation
```

## Explicitly excluded

```text
scanners
proactive alerts
Skill Factory
self-improving code
email/message access
paid providers
browser automation
external sends/publishes
```

## Success criteria

```text
A real file changes.
The mutation is logged.
The mutation can be rolled back.
The receipt contains enough evidence to verify the task.
No advanced module is implemented.
```


## v0.5.6 truth-governance dependency

This module must integrate with `docs/canonical/59_truth_grounding_and_evidence_governance.md`. Factual verification requires the correct grounding route, Evidence Manifest references, conflict handling, and unsupported-claim behavior.
