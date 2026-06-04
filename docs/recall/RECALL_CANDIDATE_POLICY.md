# Recall Candidate Policy

Status: active
Current through: v0.32.1
Purpose: Define safe M26 recall candidate eligibility.

Recall candidates must be structured refs with safe summaries. M26 accepts only
provided candidate metadata; it does not fetch, crawl, scan, or infer new source
content.

Eligible candidates need:

- a structured candidate ref.
- a structured source ref.
- a recognized source kind.
- source_ref/source_kind consistency for recognized prefixes.
- a redacted safe summary.
- optional evidence, event, receipt, memory, file, and metadata refs.

Excluded candidates include:

- unknown or arbitrary refs.
- source_ref/source_kind mismatches.
- memory refs declared as canonical, evidence, receipt, event, or user-reviewed
  sources.
- unreviewed memory by default.
- stale, conflicted, revoked, deleted, superseded, or blocked sources.
- model, runtime, or OpenWebUI output, regardless of declared source_kind.
- raw content or secret-like summaries/metadata.

M26 performs no automatic memory write and no evidence mutation.
