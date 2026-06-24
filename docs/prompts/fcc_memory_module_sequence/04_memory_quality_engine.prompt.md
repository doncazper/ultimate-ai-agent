# Memory Quality Engine

Goal: add deterministic quality detection for Memory Workbench items.

Scope:
- Duplicate detection by safe refs, candidate kind, tags, and related entity refs.
- Conflict detection by candidate kind plus related entity refs plus incompatible
  quality/state refs.
- Staleness detection by expiry/stale refs and last-reviewed posture.
- Missing evidence detection from empty evidence refs or explicit
  missing-evidence posture.
- Every item must include explainable `quality_reason_refs`.

Boundaries:
- No embeddings, vector DB, semantic similarity, model/provider calls, or hidden
  source-body inspection.

Verification:
- Focused tests for duplicate, conflict, stale, missing evidence, and raw-content
  denial.
