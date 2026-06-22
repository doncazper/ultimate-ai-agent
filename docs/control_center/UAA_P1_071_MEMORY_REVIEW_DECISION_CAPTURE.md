# UAA-P1-071 Memory Review Decision Capture

Status: Done

Contract ref: `contract-ref:memory-review-decision:v1`

## Purpose

UAA-P1-071 defines the review-decision metadata envelope for Memory Review
candidates. It lets the product show the possible decisions and required refs
without turning a decision label into a memory write, delete, export, reviewed
recall record, context injection, connector runtime, account auth, model call,
public beta claim, or production authority.

## Decision States

- `accept`
- `correct`
- `reject`
- `defer`
- `merge`
- `supersede`
- `forget-request`

The code-level wire value for forget-request is `forget_request` so schemas and
typed payloads remain identifier-safe.

## Required Decision Refs

Every decision envelope requires:

- `actor_ref`
- `source_refs`
- `provenance_refs`
- `evidence_refs`
- `stale_state`
- `retention_posture`
- `audit_refs`
- `receipt_refs`
- `blocked_state_refs`

Decision envelopes also bind back to the UAA-P1-070 provenance contract with
`contract-ref:memory-source-provenance:v1`, a source kind, the
`untrusted_until_reviewed` source posture, and `redacted_summary_only` status.
Source refs and provenance refs must match the declared source-kind prefix, and
the no-write, no-delete, no-export, and no-context-injection blocked-state refs
are required minimums.

## Denied Authority

No memory writes, deletes, exports, retention execution, context injection,
connector runtime, account auth, provider/model authority, source truth
authority, reviewed recall creation, public beta claim, public distribution
claim, production readiness, or production authority is granted.

`forget_request` is a request posture only. It is not memory deletion.
`accept` is a review label only. It is not a write, recall eligibility grant, or
truth upgrade.

## Today Surface

`GET /control-center/today/summary` exposes:

- `memory_review_decision_contract_ref`
- `memory_review_decision_states`
- `memory_review_decision_required_ref_fields`
- `memory_review_decision_authority_posture`
- Per-memory-candidate decision metadata, audit refs, receipt refs, blocked
  state refs, source provenance binding, and decision labels

The Control Center renders this as read-only metadata. It does not add accept,
correct, reject, defer, merge, supersede, forget, delete, write, export, save,
learn, inject, sync, import-account, reveal-raw, or show-raw controls.

## Out Of Scope

No persisted memory write, memory delete, memory export, recall promotion,
retention execution, context injection, connector runtime/fetch/auth, account
import, model/provider call, browser import, external assistant import, CRM
sync, automatic memory write, public beta, public distribution, production
readiness, or production authority is included in UAA-P1-071.

UAA-P1-072 owns business memory and memory quality controls.

## Verification

- `tests/test_uaa_p1_071_memory_review_decision_capture.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `scripts/verify_uaa_p1_071_memory_review_decision_capture.py`
- `docs/schemas/memory_review_decision_capture.schema.json`
