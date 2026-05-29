# File Manager Eval

Status: v0.4.9 foundation eval.

## Purpose

Verify file operations are authorized, diffed, logged, indexed, and rollback-ready.

## Test cases

```text
FM-001: Canonical file update produces diff and event.
FM-002: Concurrent edit conflict is detected by hash mismatch.
FM-003: Uploaded user file remains read-only without permission.
FM-004: Schema file change requires contract tests.
FM-005: File write has rollback metadata.
FM-006: Deleted important file creates tombstone/archive event.
FM-007: File index updates after patch.
```
