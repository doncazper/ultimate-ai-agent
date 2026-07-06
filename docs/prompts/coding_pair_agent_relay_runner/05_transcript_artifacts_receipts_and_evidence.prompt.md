# Phase 05: Transcript Artifacts, Receipts, And Evidence

Goal: make paired-agent runs auditable without leaking raw prompts, responses,
provider payloads, logs, sensitive paths, credentials, or secret-like material
into durable evidence.

## Required Work

1. Define artifact kinds: outbound turn packet, inbound agent response,
   disagreement summary, candidate action list, validation plan, final
   synthesis, and blocked-state report.
2. Define receipt kinds: run created, approval bound, adapter started, turn
   completed, output redacted, stop condition reached, run completed, run
   blocked, and run failed.
3. Add portable receipt/evidence posture: canonical JSON, stable digest,
   optional local signature/verifier ref, safe refs only, bounded redacted
   preview, and raw content omitted by default.
4. If explicit local raw transcript artifacts are supported, require operator
   opt-in, local-only artifact ref, redaction scan, no durable raw evidence, and
   clear deletion/safe-disable posture.
5. Add tests for redaction, digest stability, replay/idempotency, receipt
   links, unsafe content rejection, and raw transcript disabled by default.

## Acceptance Criteria

- Durable evidence stores safe refs, hashes, summaries, and bounded previews.
- Raw transcripts are not durable evidence.
- Disagreements and candidate actions are reviewable artifacts, not authority.

## Verification

```bash
git diff --check
.venv/bin/python scripts/verify_operational_maturity.py
```

