# 39 — Verified Task Completion Framework

Status: Layer-0 foundation spec, v0.5.3
Owner: QA / Orchestrator

## Purpose

The North Star is Verified Task Completion Rate. This document defines what `verified` means.

A task is verified only when the task-class verification contract is satisfied and evidence is attached to the run receipt.

## Verification contract fields

```text
task_class
acceptance_criteria
required_evidence
allowed_evidence_sources
minimum_verification_level
reviewer
failure_modes
receipt_fields
```

## Task classes

| Task class | Required evidence |
|---|---|
| answer | Direct response satisfies question; uncertainty labeled. |
| research | Citations/sources, recency check when relevant, source-quality notes. |
| document/artifact | File/artifact exists, path recorded, content passes acceptance criteria. |
| code | Tests/lint/type/build result or explicit environment limitation. |
| file mutation | Diff, before/after refs, rollback metadata, file existence verification. |
| memory write | Source link, scope, type, confidence, supersession/conflict handling. |
| provider read | Provider envelope, freshness, attribution/terms metadata, normalization status. |
| external action | Confirmation from tool/provider plus approval record if required. |
| notification | Relevance rationale, confidence, source evidence, attention-budget decision. |

## Verified statuses

```text
not_started
unverified
partially_verified
verified
verified_with_limitations
failed_verification
blocked
```

## Foundation rule

Execution Contracts must include verification requirements. Event Ledger receipts must include verification status. QA cannot mark a task verified without evidence references.


## v0.5.6 truth-governance dependency

This module must integrate with `docs/canonical/59_truth_grounding_and_evidence_governance.md`. Factual verification requires the correct grounding route, Evidence Manifest references, conflict handling, and unsupported-claim behavior.
