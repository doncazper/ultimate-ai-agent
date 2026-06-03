# Recall Candidate Policy

Status: active
Current through: v0.30.0
Purpose: Define safe M26 recall candidate eligibility.

Recall candidates must be structured refs with safe summaries. M26 accepts only
provided candidate metadata; it does not fetch, crawl, scan, or infer new source
content.

Eligible candidates need:

- a structured candidate ref.
- a structured source ref.
- a recognized source kind.
- a redacted safe summary.
- optional evidence, event, receipt, memory, file, and metadata refs.

Excluded candidates include:

- unknown or arbitrary refs.
- unreviewed memory by default.
- stale, conflicted, revoked, deleted, superseded, or blocked sources.
- model, runtime, or OpenWebUI output.
- raw content or secret-like summaries/metadata.

M26 performs no automatic memory write and no evidence mutation.
