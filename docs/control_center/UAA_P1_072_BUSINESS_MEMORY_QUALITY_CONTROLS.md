# UAA-P1-072 Business Memory And Memory Quality Controls

Status: implemented as a contract, test, verifier, Today-spine, and read-only
Control Center metadata slice.

This milestone adds the first CRM-lite business memory quality model for the
Founder Command Center loop. It does not add memory writes, external CRM
writes, account sync, connector runtime, automatic recall, hidden context
injection, provider/model authority, public beta, public distribution, or
production authority.

## Contract Ref

`contract-ref:business-memory-quality-controls:v1`

## Candidate Kinds

Business memory candidates are limited to these safe-review kinds:

- `profile`
- `project`
- `relationship`
- `organization`
- `deal`
- `opportunity`
- `promise`
- `follow_up`
- `preference`
- `decision`
- `commitment`

Every candidate kind requires safe source refs, provenance refs, evidence refs,
quality posture, correction posture, retention/delete/export posture, and
operator review before recall can be treated as useful.

Each candidate is also bound to `contract-ref:memory-source-provenance:v1`,
`untrusted_until_reviewed`, and `redacted_summary_only` posture. Source refs and
provenance refs must match the declared source kind; source refs do not become
truth, write, recall, connector, account, or context authority.

## Quality States

The contract exposes these quality states:

- `duplicate`
- `conflict`
- `stale_expired`
- `low_confidence`
- `source_missing`
- `evidence_missing`
- `blocked`
- `reviewed`

The states are metadata and review posture only. They do not authorize memory
writes, CRM writes, account sync, context injection, or recall as truth.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `business_memory_quality_contract_ref`
- `business_memory_candidate_kinds`
- `business_memory_quality_states`
- `business_memory_required_ref_fields`
- `business_memory_surface_bindings`
- `business_memory_authority_posture`
- `business_memory_status`
- per-candidate business memory quality refs on `memory_review_queue`

The Memory module feed now includes both
`contract-ref:memory-review-decision:v1` and
`contract-ref:business-memory-quality-controls:v1`.

## Surface Binding

Business memory quality feeds these surfaces as safe refs only:

- Today: priorities, blockers, review count, and next safe actions.
- Action Inbox: follow-up and promise candidates only; no execution tasks.
- Evidence Timeline: quality posture history refs only.
- Weekly CEO Review: carry-forward decisions and blockers only.

## Authority Boundary

Denied states remain explicit:

- No memory write.
- No memory delete.
- No memory export.
- No context injection.
- No external CRM write.
- No account sync.
- No automatic recall.
- No connector runtime.
- No account auth.
- No provider/model authority.
- No source truth authority.
- No raw source display.
- No public beta, public distribution, or production authority.

## Verification

Required proof:

- `tests/test_uaa_p1_072_business_memory_quality_controls.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_072_business_memory_quality_controls.py`
- `docs/schemas/business_memory_quality_controls.schema.json`

## Next Milestone

UAA-P1-073 Plans To Reviewable Action Envelopes is next unless hardening finds
that UAA-P1-072 needs an incremental follow-up such as UAA-P1-072.1.
