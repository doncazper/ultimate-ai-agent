# UAA-P1-076 Cross-Surface Memory Intake

Status: implemented as a review-only contract, Today-spine payload, Memory
surface UI, Evidence Timeline history item, schema, verifier, and focused tests.

This milestone lets Today, Chat, Plans, Actions, Evidence, local coding, and
manual external-assistant review imports produce memory intake proposals with
bounded safe summaries, source refs, provenance refs, evidence refs, confidence
posture, missing-evidence posture, stale-state posture, and next-safe-action
labels. It does not write memory, accept recall, inject context, call providers,
fetch accounts, import browser state, import shell history, import source
payloads, enable connector runtime, claim public beta, claim public
distribution, or grant production authority.

## Contract Ref

`contract-ref:cross-surface-memory-intake:v1`

## Required Surfaces

- Today
- Chat
- Plans
- Actions
- Evidence
- Local Coding
- External Assistant Review

## Proposal Requirements

Each intake proposal requires:

- `proposal_ref`
- `candidate_ref`
- `review_queue_ref`
- `surface`
- `source_kind`
- `candidate_kind`
- `source_refs`
- `provenance_refs`
- `evidence_refs`
- `quality_state_refs`
- `missing_evidence_refs`
- `stale_state`
- `next_safe_action`
- `blocked_state_refs`

Every proposal binds to `contract-ref:memory-source-provenance:v1`,
`contract-ref:memory-review-decision:v1`, and
`contract-ref:business-memory-quality-controls:v1`.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `cross_surface_memory_intake_contract_ref`
- `cross_surface_memory_intake_status`
- `cross_surface_memory_intake_required_surfaces`
- `cross_surface_memory_intake_required_ref_fields`
- `cross_surface_memory_intake_required_blocked_refs`
- `cross_surface_memory_intake_proposal_count`
- `cross_surface_memory_intake_proposals`
- `cross_surface_memory_intake_surface_bindings`
- `cross_surface_memory_intake_authority_posture`
- `cross_surface_memory_intake_blocked_state_refs`

The Memory module feed now includes
`contract-ref:cross-surface-memory-intake:v1` and remains write-blocked.
Chat, Plans, and Code Memory bindings now feed reviewed intake proposal refs
only.

## Authority Boundary

Required blocked refs:

- `blocked-state:no-automatic-memory-write`
- `blocked-state:no-memory-write`
- `blocked-state:no-context-injection`
- `blocked-state:no-provider-call`
- `blocked-state:no-account-fetch`
- `blocked-state:no-browser-import`
- `blocked-state:no-shell-history-import`
- `blocked-state:no-raw-file-import`
- `blocked-state:no-connector-runtime`
- `blocked-state:no-source-truth-authority`
- `blocked-state:no-public-beta-or-distribution`
- `blocked-state:no-production-authority`

Required true flags are `safe_refs_only`, `review_required`, and
`safe_summary_only`.

Denied authority flags include `memory_write_authorized: false`,
`automatic_memory_write_authorized: false`,
`context_injection_authorized: false`, `provider_call_enabled: false`,
`account_fetch_enabled: false`, `browser_import_enabled: false`,
`shell_history_import_enabled: false`, `raw_file_import_enabled: false`,
`connector_runtime_enabled: false`, `source_truth_authority: false`,
`accepted_as_recall: false`, `public_beta_claim_enabled: false`,
`public_distribution_claim_enabled: false`, and
`production_authority_enabled: false`.

## Evidence History

Evidence Timeline now includes `cross_surface_memory_intake_proposal_ref`.

The history answers stay concrete:

- Proposed: seven review-only memory candidates were proposed from bounded
  surface summaries and safe refs.
- Approved: no memory write, automatic intake, context injection, provider
  call, account fetch, browser import, or shell-history import is approved.
- Happened: only safe memory intake proposal metadata was produced.
- Changed: no memory record, context pack, source account, connector, repo,
  shell, model, or task state changed.
- Undoable: there is no rollback execution because no memory mutation happened.
- Stale: each intake proposal must be rechecked before a later review decision.
- Blocked: automatic writes, accepted recall, context injection, provider calls,
  account fetch, browser import, shell-history import, source import, connector
  runtime, and production authority remain blocked.

## Verification

Required proof:

- `tests/test_uaa_p1_076_cross_surface_memory_intake.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_076_cross_surface_memory_intake.py`
- `docs/schemas/cross_surface_memory_intake.schema.json`

## Next Milestone

UAA-P1-077 Memory-To-Loop Binding is next unless hardening finds that
UAA-P1-076 needs an incremental follow-up such as UAA-P1-076.1.
