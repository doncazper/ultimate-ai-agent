# FCC-V1-006 Evidence Timeline Productization

Status: implemented for backend-owned Evidence Timeline productization.

Contract ref: `contract-ref:founder-loop-evidence-timeline-productization:v1`

Backend route:

- `GET /control-center/evidence/timeline`

FCC-V1-006 makes Evidence a real Founder Loop proof surface for the current
loop. It adds a read-only Evidence Timeline index that names the audit events,
groups them by product object, and keeps the original history grammar visible.

Event types:

- `action_envelope_created`
- `action_decision_recorded`
- `local_task_created`
- `chat_turn_receipt_recorded`
- `chat_handoff_created`
- `memory_review_decision_recorded`

Groups:

- Today item
- Action
- Chat turn
- Memory candidate

The Evidence Timeline shows receipt refs, approval refs as identifiers,
idempotency refs, blocked states, and rollback posture. Evidence remains
read-only and safe-ref-only. It does not grant approval authority, execute
rollback, execute actions, inject memory into context, treat memory recall as
truth, write connectors, call providers, make public beta claims, or grant
production authority.

Proof:

- `scripts/verify_fcc_v1_006_evidence_timeline_productization.py`
- `tests/test_fcc_v1_006_evidence_timeline_productization.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`

Next:

- `FCC-V1-007` Promotion And Proof Lane is implemented in
  `docs/control_center/FCC_V1_007_PROMOTION_AND_PROOF_LANE.md`.
