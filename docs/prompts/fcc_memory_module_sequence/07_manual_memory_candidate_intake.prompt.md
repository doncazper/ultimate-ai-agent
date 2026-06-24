# Manual Memory Candidate Intake

Goal: add backend-owned route for creating a safe-summary memory candidate from a
manual note.

Scope:
- Route: `POST /control-center/memory/review/manual-candidate`.
- Creates a review candidate only, not a recall record.
- Requires idempotency.
- Requires provenance refs.
- Requires evidence refs or explicit missing-evidence posture.
- Stores bounded safe summary only.

Boundaries:
- No automatic memory write.
- No context injection.
- No source truth authority.
- No raw note storage.

Verification:
- Tests for success, idempotent replay, idempotency conflict, missing evidence
  posture, and raw-content denial.
