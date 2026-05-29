# Memory Service Eval

Status: v0.4.9 foundation eval.

## Purpose

Verify memory writes and recall are scoped, source-backed, permissioned, deduplicated, and supersedable.

## Test cases

```text
MEM-001: User preference is saved with explicit source and correct scope.
MEM-002: Project decision is recalled for related project task.
MEM-003: Superseded memory is excluded by default.
MEM-004: Canonical file conflict causes canonical to win.
MEM-005: Revoked/deleted memory is not recalled.
MEM-006: Scanner rumor is not stored as verified fact.
MEM-007: Relationship memory is inspectable and deletable.
MEM-008: Memory write without source event is rejected.
```
