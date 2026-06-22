# UAA-P1-073 Plans To Reviewable Action Envelopes

Status: implemented as a contract, test, verifier, Today-spine, Action Inbox,
Evidence Timeline, and read-only Control Center metadata slice.

This milestone makes Plans produce reviewable Action envelope metadata with
approve/edit/reject/defer posture. It does not add action execution, approval
grant capture, connector writes, shell/subprocess execution, model/provider
authority, public beta, public distribution, or production authority.

## Contract Ref

`contract-ref:plans-action-envelope:v1`

## Envelope Requirements

Each reviewable Action envelope requires:

- `action_envelope_ref`
- `source_plan_ref`
- `scope_ref`
- `side_effect_class`
- `risk_class`
- `approval_requirement_ref`
- `review_posture_refs`
- `evidence_refs`
- `expected_receipt_refs`
- `idempotency_key_ref`
- `expires_at`
- `rollback_ref`
- `safe_disable_ref`
- `blocked_state_refs`

Review postures are `approve`, `edit`, `reject`, and `defer`. These are posture
refs only. No UI or route in this milestone grants approval, captures approval,
or executes a state change.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `plans_action_envelope_contract_ref`
- `plans_action_envelope_review_postures`
- `plans_action_envelope_required_ref_fields`
- `plans_action_envelope_required_blocked_refs`
- `plans_action_envelope_surface_bindings`
- `plans_action_envelope_authority_posture`
- `plans_action_envelope_status`
- per-plan Action envelope refs on `plans`
- per-action envelope refs on `actions`

The Plans module feed now includes `contract-ref:plans-action-envelope:v1`.
`plan_action_state.action_envelope_contract_status` is
`implemented_today_to_action_envelope_vertical_slice_execution_blocked`.

## Surface Binding

Plans Action envelopes feed these surfaces as safe refs only:

- Today: plan/action state, blockers, and next safe actions.
- Plans: reviewable envelope metadata generated from plan summaries.
- Actions: Action Inbox cards show scope, approval requirement, expected receipt,
  idempotency, rollback, and safe-disable posture.
- Evidence: history entries describe what was proposed, what was not approved,
  what metadata was produced, what did not change, what can be undone, stale
  posture, and blocked states.
- Memory: envelope refs remain blocked from memory recall until cross-surface
  memory intake is scoped later.

## Authority Boundary

Denied states remain explicit:

- `blocked-state:no-action-execution`: no action execution.
- `blocked-state:no-approval-grant-capture`: no approval grant capture.
- `blocked-state:approval-refs-identifiers-only`: approval refs are
  identifiers only.
- `blocked-state:no-connector-write`: no connector write.
- `blocked-state:no-shell-subprocess-execution`: no shell/subprocess
  execution.
- `blocked-state:no-model-provider-authority`: no model/provider authority.
- `blocked-state:no-public-beta-or-distribution`: no public beta or public
  distribution claim.
- `blocked-state:no-production-authority`: no production authority.

Denied authority flags include `approval_grant_capture_enabled: false` and
`action_execution_enabled: false` on Today, Plans, and Action Inbox envelope
metadata.

Plan and Action envelope data is redacted safe-ref metadata only. Raw prompts,
raw responses, raw provider payloads, raw local paths, raw logs, account
identifiers, usernames, hostnames, credential material, and full transcripts are
denied in durable evidence.

## Verification

Required proof:

- `tests/test_uaa_p1_073_plans_action_envelopes.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_073_plans_action_envelopes.py`
- `docs/schemas/plans_action_envelopes.schema.json`

## Next Milestone

UAA-P1-074 First-Party Control Center Chat Local Operator Surface is next unless
hardening finds that UAA-P1-073 needs an incremental follow-up such as
UAA-P1-073.1.
