# UAA Parity Gap Closure Phase 01 Convergence Ledger

Status: current-main inventory; no runtime authority grant

- Inventory base: `commit:35d66a04680cbe6fa5356001dd90256bd36f9fd8`
- Active baseline: `v0.104.0`
- Inventory date: `2026-07-22`
- Execution posture: isolated clean phase worktree based on exact `origin/main`

This report records current implementation truth. Plans, previews, fixtures, open
pull requests, and protected local worktrees do not count as merged behavior.
All refs are repository-relative or opaque safe refs.

## Convergence Snapshot

| Ref | State | Owned scope | Disposition |
|---|---|---|---|
| `pr:344` | merged prerequisite at `commit:35d66a04680cbe6fa5356001dd90256bd36f9fd8` | stored parity prompt pack and verifier | foundation for this phase |
| `pr:319` | `open_pr_owned_elsewhere` at `commit:887465c163a46c629ee2fb0581434fded68a7f19` | authority capability implications and exact admin/destructive semantics | do not edit `src/ultimate_ai_agent/core/authority/contracts.py` or `tests/test_authority_capability_implications.py`; revisit after merge or handoff |
| `worktree:operator-owned:verification-recovery` | `in_flight_branch_owned_elsewhere` on `branch:codex/harden-verification-recovery-auth-ci-identity` | CI, Control Center, macOS packaging, runtime, verification, and documentation groups | preserve without mutation; current-main proof remains authoritative |

Task inspection found this queue task as the active UAA implementation owner and
no second active UAA implementation task. The protected operator worktree is
therefore recorded as local overlap, not as merged or active-task proof. Its
repo-relative owned path groups are `.github/workflows/ci.yml`,
`.github/workflows/supply-chain.yml`, `Makefile`, `README.md`, `SECURITY.md`,
`apps/control-center/src/`, `docs/`, `packaging/macos/`, `scripts/`,
`src/ultimate_ai_agent/core/`, `src/ultimate_ai_agent/distribution/`, and
`tests/`. Phase work remains isolated and does not modify that worktree.

## Recent Merge And Remote Ledger

| Ref | Exact merge | Relevance |
|---|---|---|
| `pr:344` | `commit:35d66a04680cbe6fa5356001dd90256bd36f9fd8` | verified parity prompt-pack prerequisite |
| `pr:343` | `commit:2073ae77651e43585d0448a513c104a9a5530fea` | exact-head CI evidence DAG; P10 proof |
| `pr:340` | `commit:0f3af03e382434bf13330bc35399d2994ee605b6` | governed prompt dependency compiler foundation |
| `pr:339` | `commit:5b5970a3e23c826a7c1e28b2fa00b41fc050a76f` | governed browser hardening prerequisite |

The only other open remote pull request is `pr:319` on
`branch:agent/exact-authority-capability-boundaries`. Remote `codex/*` branches
associated with already merged work are historical branch refs, not active
completion evidence; they are neither modified nor counted as current truth.

## Coverage Ledger

| ID | Canonical outcome | Phase | Status | Current-main proof | Remaining delta / authority |
|---|---|---:|---|---|---|
| H01 | `outcome:persistent-goal-lifecycle` | 04 | `planned_only` | `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md` | durable goal store, lifecycle, API/CLI/UI, receipts |
| H02 | `outcome:durable-event-lifecycle` | 04 | `merged_partial` | `src/ultimate_ai_agent/core/execution/run_storage.py`; `tests/test_durable_run_lifecycle_read_model.py` | cursor replay, live bounded stream, backpressure |
| H03 | `outcome:memory-integrity` | 07 | `merged_partial` | `src/ultimate_ai_agent/core/memory`; `tests/test_memory_supersession.py` | atomic mutation audit, migration, ranking drift, concurrency |
| H04 | `outcome:briefing-worker` | 06 | `blocked_by_authority` | `docs/control_center/route_status_manifest.json`; `tests/test_morning_briefing_v1.py` | exact local background worker authority and lifecycle proof |
| H05 | `outcome:local-setup-lifecycle` | 03 | `merged_partial` | `src/ultimate_ai_agent/distribution/macos`; `tests/test_macos_first_class_installer.py` | shared Setup Core/API/CLI/UI state machine and approval binding |
| H06 | `outcome:cross-session-search` | 07 | `merged_partial` | `tests/test_hermes_runtime_session_search.py`; `docs/runtime/UAA_HERMES_RUNTIME_CODING_PROJECT_MODEL.md` | denser local index, operational corpus proof, storage budgets |
| O01 | `outcome:persistent-goal-lifecycle` | 04 | `planned_only` | `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md` | same canonical delta as H01/L06 |
| O02 | `outcome:backend-truth` | 02 | `merged_partial` | `docs/control_center/route_status_manifest.json`; `apps/control-center/src/hooks/useControlCenterData.ts` | all critical surfaces fail visibly on missing/stale/malformed backend data |
| O03 | `outcome:durable-event-lifecycle` | 04 | `merged_partial` | `src/ultimate_ai_agent/core/execution/run_storage.py`; `tests/test_durable_run_lifecycle_read_model.py` | same canonical delta as H02/L07 |
| O04 | `outcome:verified-backup-restore` | 07 | `merged_partial` | `scripts/verify_backup_restore.py`; `tests/test_backup_restore_verification.py` | production store coverage, archive safety, fresh-target restore proof |
| O05 | `outcome:work-board-reconciliation` | 05 | `merged_partial` | `src/ultimate_ai_agent/core/storage/founder_loop.py`; `tests/test_action_inbox_work_queue.py` | revisioned multi-client reconciliation and stale-write rejection |
| O06 | `outcome:connector-delivery-evidence` | 09 | `mock_or_contract_only` | `src/ultimate_ai_agent/core/execution/connector_delivery.py`; `tests/test_connector_delivery_semantics_contract.py` | delivery-attempt contract only; connector execution stays blocked |
| O07 | `outcome:session-ux` | 05 | `merged_partial` | `tests/test_hermes_runtime_session_continuity.py`; `tests/test_hermes_runtime_session_search.py` | readable durable session controls and recovery UX |
| O08 | `outcome:briefing-worker` | 06 | `blocked_by_authority` | `tests/test_morning_briefing_v1.py`; `docs/control_center/route_status_manifest.json` | same canonical delta as H04/L08/L10 |
| P01 | `outcome:startup-budgets` | 08 | `merged_partial` | `scripts/check_foundation_gate_latency.py`; `tests/test_foundation_gate_latency_scripts.py` | measured cold/warm budgets and lazy-import closure |
| P02 | `outcome:ordered-read-fanout` | 08 | `merged_partial` | `src/ultimate_ai_agent/core/costs/governor.py`; `tests/test_resource_governor.py` | subsystem-wide fanout inventory and serialized-write equivalence |
| P03 | `outcome:cross-session-search` | 07, 08 | `merged_partial` | `tests/test_hermes_runtime_session_search.py` | compact reads, denser search, before/after proof |
| P04 | `outcome:bounded-cache-policy` | 08 | `merged_partial` | `tests/test_resource_governor.py`; `tests/test_model_router_decisions.py` | complete cache inventory, TTL/invalidation/concurrency proof |
| P05 | `outcome:single-flight-provider-work` | 09 | `merged_partial` | `tests/test_model_runtime_no_real_calls.py`; `tests/test_exact_approved_provider_fallback.py` | cross-lane duplicate-call proof; provider authority stays exact-scoped |
| P06 | `outcome:abort-aware-io` | 08, 09 | `merged_partial` | `tests/test_governed_browser_queue02_hardening.py`; `tests/test_ci_fallback_execution.py` | inventory all polling/network adapters and prove prompt cancellation |
| P07 | `outcome:event-backpressure` | 04, 08 | `merged_partial` | `tests/test_durable_run_lifecycle_read_model.py`; `tests/test_kernel_event_trace.py` | bounded live replay and slow-consumer proof |
| P08 | `outcome:briefing-worker` | 06, 08 | `merged_partial` | `tests/test_authority_mission_worker_security.py`; `tests/test_hermes_runtime_background_jobs.py` | exact worker queue/claim efficiency plus H04 authority gate |
| P09 | `outcome:frontend-work-deduplication` | 08 | `merged_partial` | `apps/control-center/src/hooks/useControlCenterData.ts`; `apps/control-center/src/App.test.tsx` | route-loading and duplicate-refresh measurements |
| P10 | `outcome:exact-head-ci-budget` | 08 | `merged_proven` | `.github/workflows/ci.yml`; `scripts/verification/verify_ci_evidence_dag.py`; `tests/test_ci_workflow.py`; `tests/test_ci_command_manifest.py` | none; preserve eight shards, four workers, exact-head evidence DAG |
| B01 | `outcome:exact-approval-ownership` | 09 | `open_pr_owned_elsewhere` | `pr:319`; `commit:887465c163a46c629ee2fb0581434fded68a7f19` | wait for owned PR; do not duplicate authority-contract paths |
| B02 | `outcome:approval-fail-closed` | 09 | `merged_partial` | `src/ultimate_ai_agent/core/approvals/authority.py`; `tests/test_approval_authority.py` | adapter-wide fail-open audit |
| B03 | `outcome:connector-delivery-evidence` | 09 | `mock_or_contract_only` | `src/ultimate_ai_agent/core/execution/connector_delivery.py`; `tests/test_connector_delivery_semantics_contract.py` | typed delivery-attempt states; no connector send authority |
| B04 | `outcome:restart-admission-fence` | 04, 09 | `merged_partial` | `tests/test_hermes_runtime_background_jobs.py`; `tests/test_verification_execution_identity.py` | runtime-wide interrupted restart/admission proof |
| B05 | `outcome:backend-truth` | 02, 09 | `merged_partial` | `docs/control_center/route_status_manifest.json`; `apps/control-center/src/App.test.tsx` | stale UI and mock-masked loss proof across critical surfaces |
| B06 | `outcome:event-backpressure` | 04, 09 | `merged_partial` | `tests/test_kernel_event_trace.py`; `tests/test_session_logging.py` | arbitrary UTF-8 split and total ordering proof |
| B07 | `outcome:provider-side-effect-fence` | 09 | `merged_partial` | `tests/test_exact_approved_provider_fallback.py` | deny fallback retry after uncertain side effect |
| B08 | `outcome:memory-integrity` | 07, 09 | `merged_partial` | `tests/test_memory_supersession.py`; `tests/test_runtime_memory_learning.py` | same canonical delta as H03/L12 |
| B09 | `outcome:storage-budget-integrity` | 07, 09 | `merged_partial` | `src/ultimate_ai_agent/core/storage/founder_loop.py`; `tests/test_backup_restore_verification.py` | count sidecars, backups, partial archives, and retained receipts |
| B10 | `outcome:archive-path-safety` | 07, 09 | `merged_partial` | `tests/test_backup_restore_verification.py`; `tests/test_macos_first_class_installer.py` | export/archive/restore traversal and archive-bomb coverage |
| B11 | `outcome:chunk-redaction` | 09 | `merged_partial` | `tests/test_secret_broker_redaction.py`; `tests/test_session_logging.py` | adversarial split-secret coverage across all chunked outputs |
| B12 | `outcome:revisioned-autosave` | 05, 09 | `merged_partial` | `tests/test_action_inbox_work_queue.py`; `apps/control-center/src/App.test.tsx` | stale/invalid autosave conflict proof |
| B13 | `outcome:approval-wait-lifecycle` | 04, 09 | `merged_partial` | `tests/test_approval_expiration.py`; `tests/test_operator_run_timeline_enforcement.py` | orphan cleanup and durable expiry evidence |
| B14 | `outcome:backend-truth` | 02, 09 | `merged_partial` | `src/ultimate_ai_agent/core/control_center/proof.py`; `tests/test_claim_verification_decisions.py` | stale evidence must remove verified/completed language everywhere |
| L01 | `outcome:backend-truth` | 02 | `merged_partial` | `docs/control_center/route_status_manifest.json`; `apps/control-center/src/hooks/useControlCenterData.ts` | remove remaining critical production fallback success paths |
| L02 | `outcome:local-setup-lifecycle` | 03 | `merged_partial` | `src/ultimate_ai_agent/distribution/macos`; `scripts/macos/verify_installer_e2e.py` | same canonical delta as H05 |
| L03 | `outcome:backend-truth` | 02 | `merged_partial` | `tests/test_founder_loop_v1_product_proof.py`; `tests/test_operator_loop_p1_011.py` | real-backend rendered end-to-end readability proof |
| L04 | `outcome:backend-truth` | 02 | `merged_partial` | `tests/test_claim_verification_decisions.py`; `tests/test_evidence_memory_loop_binding.py` | stale/fallback evidence removal across all critical surfaces |
| L05 | `outcome:action-inbox-ux` | 05 | `merged_partial` | `tests/test_action_inbox_work_queue.py`; `apps/control-center/src/App.test.tsx` | approval envelope clarity, revision conflicts, two-client proof |
| L06 | `outcome:persistent-goal-lifecycle` | 04 | `planned_only` | `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md` | same canonical delta as H01/O01 |
| L07 | `outcome:durable-event-lifecycle` | 04 | `merged_partial` | `tests/test_durable_run_lifecycle_read_model.py` | same canonical delta as H02/O03 |
| L08 | `outcome:briefing-worker` | 06 | `blocked_by_authority` | `tests/test_morning_briefing_v1.py`; `docs/control_center/route_status_manifest.json` | source refresh and background authority require an exact accepted lane |
| L09 | `outcome:work-board-reconciliation` | 05 | `merged_partial` | `tests/test_action_inbox_work_queue.py`; `apps/control-center/src/App.test.tsx` | same canonical delta as O05 |
| L10 | `outcome:briefing-worker` | 04, 06 | `merged_partial` | `tests/test_authority_mission_worker_security.py`; `tests/test_hermes_runtime_background_jobs.py` | product worker lifecycle/recovery proof; execution remains authority-gated |
| L11 | `outcome:verified-backup-restore` | 07 | `merged_partial` | `tests/test_backup_restore_verification.py` | same canonical delta as O04 |
| L12 | `outcome:memory-integrity` | 07 | `merged_partial` | `tests/test_memory_supersession.py`; `tests/test_runtime_memory_learning.py` | same canonical delta as H03/B08 |
| L13 | `outcome:product-performance-budgets` | 08 | `merged_partial` | `scripts/check_foundation_gate_latency.py`; `tests/test_foundation_gate_latency_no_write.py` | product-journey cold/warm/steady budgets and regression gates |
| L14 | `outcome:locked-supply-chain` | 08 | `merged_proven` | `.github/workflows/supply-chain.yml`; `uv.lock`; `apps/control-center/package-lock.json`; `tests/test_supply_chain_workflow.py` | none; preserve frozen Python/Node installation and audit gates |
| L15 | `outcome:session-ux` | 05 | `merged_partial` | `tests/test_hermes_runtime_session_continuity.py`; `tests/test_hermes_runtime_session_search.py` | same canonical delta as O07 |
| L16 | `outcome:cross-session-search` | 07 | `merged_partial` | `tests/test_hermes_runtime_session_search.py` | same canonical delta as H06/P03 |

## Canonical Alias Graph

- `outcome:persistent-goal-lifecycle`: H01, O01, L06
- `outcome:durable-event-lifecycle`: H02, O03, L07
- `outcome:memory-integrity`: H03, B08, L12
- `outcome:briefing-worker`: H04, O08, P08, L08, L10
- `outcome:local-setup-lifecycle`: H05, L02
- `outcome:cross-session-search`: H06, P03, L16
- `outcome:backend-truth`: O02, B05, B14, L01, L03, L04
- `outcome:verified-backup-restore`: O04, L11
- `outcome:work-board-reconciliation`: O05, L09
- `outcome:connector-delivery-evidence`: O06, B03
- `outcome:session-ux`: O07, L15

## Phase Dependency Graph

- Phase 01 precedes Phases 02–10.
- Phase 02 precedes Phases 04, 05, 06, and 10.
- Phase 03 precedes Phase 10.
- Phase 04 precedes Phases 05, 06, 08, 09, and 10.
- Phase 05 precedes Phases 06 and 10.
- Phase 06 precedes Phases 08, 09, and 10.
- Phase 07 precedes Phases 08, 09, and 10.
- Phase 08 precedes Phases 09 and 10.
- Phase 09 precedes Phase 10.

## Visible Surface Truth

| Surface | Current posture | Live-data gap |
|---|---|---|
| Start Here | backend-owned, partial | proof/detail completion and full failure-state walkthrough |
| Today | storage-backed, partial | complete readable loop and source adapters |
| Inbox | backend source status only | live email/calendar ingestion absent |
| Action Inbox | backend-owned, proofed exact local decision lane | broader actions remain blocked; UX/revision hardening remains |
| Morning Briefing | storage-backed, partial | live sources and exact refresh worker absent |
| Plans / Work Board | backend-owned, partial | durable goals and multi-client reconciliation incomplete |
| Memory | reviewed local state, partial | integrity/ranking/migration hardening incomplete |
| Evidence / Proof | backend-owned, partial | stale-evidence end-to-end truth proof incomplete |
| Setup | real installer core, partial product integration | shared Setup API/UI lifecycle incomplete |
| Chat / Sessions | backend-owned local state, partial | session UX and compact cross-session search remain |
| Runtime | backend status only | broad execution stays blocked |
| Settings | backend status and authority cockpit only | no authority-minting toggles or unsupported writes |

## Authority Prerequisites

- The exact Morning Briefing source-refresh/background-worker lane remains
  `blocked_by_authority`; Phase 06 may implement independent contracts and tests
  but cannot claim execution without a separately accepted exact lane.
- Connector account reads, sends, writes, notifications, provider/model calls,
  browser execution, unrestricted shell execution, and production authority
  remain blocked.
- `pr:319` owns its exact approval/admin/destructive semantics paths until merge
  or explicit handoff.

## Phase Execution Ledger

| Phase | State after Phase 01 | Required action |
|---:|---|---|
| 02 | ready | backend truth and real rendered founder-loop proof |
| 03 | ready | integrate existing installer core into shared governed Setup lifecycle |
| 04 | ready after 02 | persistent goals and durable event lifecycle |
| 05 | ready after 02/04 | Action Inbox, Work Board, session UX |
| 06 | independent code ready after 02/04/05; execution authority blocked | sources and exact worker lane |
| 07 | ready | memory/search/backup integrity |
| 08 | ready after 04/06/07 | performance; preserve proven P10/L14 |
| 09 | ready after 04/06/07/08 except B01 overlap | reliability and future-lane proofs |
| 10 | ready after 02–09 | terminal acceptance and honest residual ledger |
