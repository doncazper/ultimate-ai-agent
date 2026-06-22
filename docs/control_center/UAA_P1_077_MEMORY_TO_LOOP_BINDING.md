# UAA-P1-077 Memory-To-Loop Binding

Status: implemented as a read-only Today-spine contract, Action Inbox proposal
surface, Memory Review visibility card, Evidence Timeline history item, schema,
verifier, and focused tests.

This milestone binds reviewed memory and cross-surface intake proposal state into
the daily loop without turning memory into hidden recall, context injection, or
execution authority. Today, Action Inbox, Evidence Timeline, and Weekly CEO
Review now expose safe refs for candidate memory, accepted-recall display
posture, correction refs, rejected refs, follow-up commitments, stale refs,
missing-evidence blockers, memory-derived Action proposals, and a weekly review
rollup.

## Contract Ref

`contract-ref:memory-to-loop-binding:v1`

## Required Surfaces

- Today
- Action Inbox
- Evidence Timeline
- Weekly CEO Review

## Loop Item Requirements

Each loop item requires:

- `loop_item_ref`
- `surface`
- `loop_binding_state`
- `memory_candidate_ref`
- `source_refs`
- `evidence_refs`
- `accepted_recall_refs`
- `correction_refs`
- `rejected_item_refs`
- `follow_up_commitment_refs`
- `stale_state`
- `missing_evidence_refs`
- `blocked_state_refs`
- `next_safe_action`

Supported `loop_binding_state` values are `candidate`, `accepted_recall`,
`correction`, `rejected`, `follow_up_commitment`, `stale`, and
`missing_evidence_blocker`. State-specific refs are required when a state claims
accepted recall, correction, rejection, follow-up commitment, or missing
evidence.

## Memory-Derived Action Requirements

Memory-derived Action proposals are reviewable Action metadata only. Each
proposal requires:

- `proposal_ref`
- `source_memory_ref`
- `source_loop_item_ref`
- `source_review_ref`
- `source_refs`
- `provenance_refs`
- `evidence_refs`
- `side_effect_class`
- `risk_class`
- `approval_required`
- `approval_posture`
- `approval_requirement_ref`
- `action_envelope_ref`
- `scope_ref`
- `review_posture_refs`
- `expected_receipt_refs`
- `next_safe_action`
- `blocked_state_refs`

They may carry `source_intake_proposal_ref` when the candidate comes from
UAA-P1-076 intake, but that ref is provenance only.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `memory_to_loop_binding_contract_ref`
- `memory_to_loop_binding_status`
- `memory_to_loop_required_surfaces`
- `memory_to_loop_required_ref_fields`
- `memory_derived_action_required_ref_fields`
- `memory_to_loop_required_blocked_refs`
- `memory_to_loop_item_count`
- `memory_to_loop_items`
- `memory_derived_action_proposal_count`
- `memory_derived_action_proposals`
- `memory_candidate_refs`
- `accepted_recall_refs`
- `correction_refs`
- `rejected_item_refs`
- `follow_up_commitment_refs`
- `stale_memory_refs`
- `missing_evidence_blocker_refs`
- `memory_derived_action_proposal_refs`
- `memory_to_loop_surface_bindings`
- `memory_to_loop_authority_posture`
- `memory_to_loop_weekly_review_refs`
- `weekly_ceo_review_summary`
- `memory_to_loop_blocked_state_refs`

The Memory module feed now includes `contract-ref:memory-to-loop-binding:v1`
and remains write-blocked. Action Inbox exposes memory-derived Action proposals
for review only. Memory Review shows the loop-binding refs so the operator can
inspect what will carry into Today, Actions, Evidence, and Weekly CEO Review.

## Authority Boundary

Required blocked refs:

- `blocked-state:no-memory-write`
- `blocked-state:no-automatic-recall`
- `blocked-state:no-context-injection`
- `blocked-state:no-approval-grant-capture`
- `blocked-state:no-action-execution`
- `blocked-state:no-connector-write`
- `blocked-state:no-account-sync`
- `blocked-state:no-source-truth-authority`
- `blocked-state:no-public-beta-or-distribution`
- `blocked-state:no-production-authority`

Required true flags are `safe_refs_only` and `review_required`.

Denied authority flags include `memory_write_authorized: false`,
`automatic_recall_enabled: false`, `context_injection_authorized: false`,
`approval_grant_capture_enabled: false`, `action_execution_enabled: false`,
`connector_write_enabled: false`, `account_sync_enabled: false`,
`source_truth_authority: false`, `public_beta_claim_enabled: false`,
`public_distribution_claim_enabled: false`, and
`production_authority_enabled: false`.

## Evidence History

Evidence Timeline now includes `memory_to_loop_binding_ref`.

The history answers stay concrete:

- Proposed: memory loop bindings and memory-derived Action proposals were
  proposed as review-only safe refs.
- Approved: no memory write, accepted recall, approval grant, action execution,
  context injection, connector write, or production authority is approved.
- Happened: only memory-to-loop binding metadata was produced for review
  surfaces.
- Changed: Today, Action Inbox, Evidence Timeline, and Weekly CEO Review gained
  safe loop refs; no memory record, action state, connector, account, context,
  repo, model, or task state changed.
- Undoable: there is no rollback execution because no memory mutation or Action
  execution happened.
- Stale: all memory refs must be rechecked before recall, context use, or later
  scoped action.
- Blocked: memory write, automatic recall, context injection, approval capture,
  action execution, connector write, account sync, and production authority
  remain blocked.

## Weekly CEO Review Rollup

`weekly_ceo_review_summary` carries:

- input refs
- decision refs
- commitment refs
- carry-forward task refs
- unresolved blocker refs
- memory correction refs
- rejected item refs
- stale memory refs
- missing-evidence blocker refs
- follow-up opportunity refs
- an authority boundary
- the next safe action

This summary is a review rollup only. It does not schedule work, sync accounts,
write CRM state, write memory, inject context, approve work, or execute actions.

## Verification

Required proof:

- `tests/test_uaa_p1_077_memory_to_loop_binding.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_077_memory_to_loop_binding.py`
- `docs/schemas/memory_to_loop_binding.schema.json`

## Next Milestone

UAA-P1-078 Private Beta-Readiness Gate is next unless hardening finds that
UAA-P1-077 needs an incremental follow-up such as UAA-P1-077.1.
