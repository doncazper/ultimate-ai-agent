# UAA GoatCitadel Catch-Up Memory Learning

Status: Phase 05 implemented as backend-owned memory learning posture
hardening only.

## Full-Strength Version

UAA should make memory, learning, and context feel useful in the operator loop:
explicit intake, review, correction, rejection, feedback, provenance, quality
controls, staleness, conflict handling, context-pack previews, and
memory-to-loop binding. Memory should help future work while staying reviewable
and explainable.

## Repo-Safe Version

Phase 05 adds Python Core Memory Workbench field
`contract-ref:goatcitadel-catchup-memory-learning-posture:v1`:

- Core builder: `src/ultimate_ai_agent/core/memory/workbench.py`
- API embedding: `GET /control-center/memory/workbench`
- CLI: `scripts/dev/uaa_founder_loop.py memory-learning-posture`
- Control Center: Memory renders a read-only learning posture panel with
  lifecycle counts, feedback/correction/rejection/forget-request posture,
  context-pack proposal posture, quality controls, provenance requirements,
  receipt refs, reviewed recall refs, blocked authority refs, and next safe
  action.

Memory remains recall and reviewable context, not truth or authority. The
read model is derived from existing Memory Review candidates, decision receipts,
reviewed recall records, context-pack proposal refs, ranking diagnostics, and
safe-ref provenance. It does not add a new route or grant new write authority.

Reviewed accept/correct receipts may use the existing exact scoped Memory
Review write lane to create local recall-only records when the safe-disable
posture allows it. Reject, defer, merge, supersede, and forget-request remain
receipt/posture operations. Context packs remain proposal-only and cannot write
prompt context, inject hidden context, call a model/provider, execute actions,
or sync connectors.

All fields are safe refs, bounded summaries, counts, and explicit authority
booleans. The read model does not persist raw prompt content, raw response
content, provider payloads, raw local paths, raw logs, account material,
credentials, or private data.

## Blocked / Needs Authority

Memory remains recall and reviewable context; these capabilities remain blocked:

- broad memory-write authority
- automatic memory writes
- hidden context injection
- automatic context injection
- memory as truth or policy override
- action execution from retrieved memory
- connector writes or account sync
- model/provider calls
- live web fetching
- background autonomy
- hard delete execution
- export execution
- production authority
- public release or public beta claims

## Exact Promotion Path

Any future memory-learning promotion must define exact scope, approval binding,
idempotency, receipt/proof refs, rollback or safe-disable posture, redaction,
CLI/API/Core parity, route classification, focused tests, and Control Center
truth labels.

Automatic memory writes need a separate reviewed write policy, source
provenance, confidence/staleness thresholds, conflict handling, rejection and
correction flows, safe-disable, replay/idempotency checks, and evidence refs.

Context injection needs an exact context-pack approval envelope, prompt-context
preview, redaction proof, hidden-injection blocker removal through policy, and
proof that retrieved memory cannot authorize actions or override operator
decisions.

Delete/export lanes need retention policy binding, subject refs, explicit
approval, safe-disable, rollback/readiness posture, receipts, and proof that raw
content is not exposed.
