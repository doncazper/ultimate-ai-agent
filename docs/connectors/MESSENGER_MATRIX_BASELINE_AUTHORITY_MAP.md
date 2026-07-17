# Messenger Matrix Baseline Authority Map

Status: MSG-MX-000 planning audit accepted on merge; no runtime authority.

Historical audit baseline: `d1066c0cdc90a3d882114eab145e235cb8d1ae38`

This is the subordinate authority map for the desktop-only Messenger Matrix
program. It records what UAA understands at the historical baseline and the
evidence required for later promotion. It is not a capability registry,
availability snapshot, approval, lease, or execution receipt.

Canonical sources:

- `docs/design/UAA_MESSENGER_MATRIX_IMPLEMENTATION_PLAN.md`
- `docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md`
- `docs/prompts/messenger_matrix/README.md`
- `docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md`
- `docs/capability_registry.md`

## Baseline Evidence

At the historical baseline:

- no Matrix SDK, Synapse service configuration, Matrix session, crypto store,
  sync runtime, room model, or Matrix-backed Messenger route is implemented;
- `AuthorityDomain.messages` and generic message capabilities exist, but there
  is no Matrix-specific authority domain or exact Matrix capability mapping;
- `lane-ref:messages-live-send-adapter` is an unsupported future iMessage/SMS
  lane and is not Matrix implementation, readiness, or authority;
- the M124/M125 Messages contracts deny authentication, network access, reads,
  search, sends, thread/room mutation, attachments, raw-content storage, and
  account binding;
- `ApiRouteSideEffectClass` can express no effect, validation-only, local
  development workspace effects, and governed network reads only. It cannot
  yet truthfully classify authenticated connector mutation, credential/key
  mutation, crypto recovery/reset, media transfer/materialization, or local
  service lifecycle operations; and
- the existing `/control-center/trust-authority/matrix` route is a generic
  authority matrix, not a Matrix-protocol route.

Evidence refs:

- `evidence-ref:msg-mx-000:authority-taxonomy`
- `evidence-ref:msg-mx-000:route-taxonomy`
- `evidence-ref:msg-mx-000:matrix-runtime-absence`
- `evidence-ref:msg-mx-000:dependency-absence`
- `evidence-ref:msg-mx-000:messages-connector-denials`
- `evidence-ref:msg-mx-000:current-messages-lane`

| Evidence ref | Repository evidence |
|---|---|
| `evidence-ref:msg-mx-000:authority-taxonomy` | `src/ultimate_ai_agent/core/authority/contracts.py`, `src/ultimate_ai_agent/core/capabilities/models.py` |
| `evidence-ref:msg-mx-000:route-taxonomy` | `src/ultimate_ai_agent/api/contracts.py` |
| `evidence-ref:msg-mx-000:matrix-runtime-absence` | `docs/design/UAA_MESSENGER_MATRIX_IMPLEMENTATION_PLAN.md`, `docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md` |
| `evidence-ref:msg-mx-000:dependency-absence` | `pyproject.toml`, `uv.lock`, `apps/control-center/package.json`, `apps/control-center/package-lock.json` |
| `evidence-ref:msg-mx-000:messages-connector-denials` | `src/ultimate_ai_agent/core/connectors/messages_connector_contract_review.py`, `src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py`, `tests/test_m124_messages_connector_contract_review.py` |
| `evidence-ref:msg-mx-000:current-messages-lane` | `src/ultimate_ai_agent/core/authority/lane_registry.py` |

The canonical availability model remains
`src/ultimate_ai_agent/core/capability_availability/contracts.py`. This audit
reuses its explicit uncertainty dimensions and does not add another registry,
snapshot, readiness enum, or invocation decision.

## Four-Layer Truth Boundary

1. Capability declaration is a planned, inspectable description only.
2. Runtime availability must use the canonical capability-availability
   dimensions and preserve unknown, unsupported, unconfigured, stale, and
   blocked states.
3. Invocation authority is a fresh, exact, request-scoped decision immediately
   before every future call. It is never cached or inferred from declaration,
   availability, UI state, Full Machine Access, or an approval identifier.
4. Execution evidence is a content-free receipt for what actually happened. It
   is not authority and cannot repair an absent pre-start decision.

No Matrix-wide `authorized`, `callable`, `connected`, or `enabled` flag is
accepted. Unknown or stale compatibility, health, budget, lease, approval,
target, deadline, readiness, kill-switch, safe-disable, or replay posture fails
closed.

## Milestone Ledger

The ledger is ordered and subordinate to the canonical board. Target renders
are design evidence only.

<!-- MSG-MX-MILESTONE-LEDGER:START -->
| Milestone | Declaration | Program status | Implementation | Authority posture | Readiness | Evidence required to advance |
|---|---|---|---|---|---|---|
| MSG-MX-000 | declared | planning_audit_accepted_on_merge | implemented_planning_audit | not_applicable_audit_metadata | not_applicable_audit_metadata | authority map, board binding, verifier, focused tests |
| MSG-MX-001 | planned | planned_no_runtime_authority | missing | not_applicable_audit_metadata | not_applicable_audit_metadata | accepted clean-room ADR, render review, threat model, authority matrix |
| MSG-MX-002 | planned | planned_no_runtime_authority | missing | not_applicable_audit_metadata | not_applicable_audit_metadata | fixture-only desktop shell, all commands Preview/Planned/Blocked, frontend proof |
| MSG-MX-003 | planned | planned_no_runtime_authority | missing | not_applicable_audit_metadata | not_applicable_audit_metadata | Python contracts, read-only API/CLI inspection, disabled adapter, parity proof |
| MSG-MX-004 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted loopback/container/harness lanes and hostile lifecycle proof |
| MSG-MX-005 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted discovery/session/auth/credential/SSO/callback lanes and revocation proof |
| MSG-MX-006 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted read/sync/cache/key lanes and cross-scope isolation proof |
| MSG-MX-007 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted crypto/device/backup/recovery/reset lanes and loss/recovery proof |
| MSG-MX-008 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted exact human-commanded messaging/outbox/notification lanes and delivery proof |
| MSG-MX-009 | planned | blocked_pending_separate_exact_authority | unsupported_missing | blocked | unknown | accepted room/admin/media/search lanes and quarantine/cleanup proof |
| MSG-MX-010 | partial | partial_exact_local_lanes | context_policy_and_proposal_core_implemented | lease_required | request_scoped | six accepted local context/policy/proposal lanes; provider and attachment families remain blocked |
| MSG-MX-011 | planned | planned_no_new_lane_hardening | missing | not_applicable_audit_metadata | not_applicable_audit_metadata | hardening evidence under fresh exact authority for every exercised call |
| MSG-MX-012 | planned | planned_no_new_lane_acceptance | missing | not_applicable_audit_metadata | not_applicable_audit_metadata | integrated acceptance evidence for exact previously accepted lanes only |
<!-- MSG-MX-MILESTONE-LEDGER:END -->

## Shared Future Runtime Gate

Every future runtime call must re-evaluate, immediately before start:

- PolicyEngine and exact current policy decision;
- exact LocalApprovalAuthority scope where required;
- current exact AuthorityLease;
- exact capability, adapter, provider, target, mission, and run;
- TTL and deadline;
- operation, time, cost, byte, and concurrency budgets as applicable;
- compatibility, configuration, health, freshness, and derived readiness;
- kill switch and safe-disable;
- request fingerprint, idempotency, replay, and prior-start posture.

Approval refs are identifiers only. Missing, unknown, stale, expired, revoked,
degraded-without-explicit-policy, mismatched, or unresolved-cost state blocks
the call before start.

## Exact Planned Lane Ledger

Every row is a distinct planned lane or an exact family whose operations share
a complete conjunctive domain/capability set, target binding, side-effect
posture, rollback semantics, and promotion proof. All values are historical
baseline truth. `partial` means an existing generic domain/capability can
describe part of the request; it does not make the lane eligible or callable.

For each row, `self-bound-profile` is an immutable exact gate profile formed by
the row's lane, domain/capability set, adapter/target, side-effect posture,
canonical availability values, and promotion evidence together with the same
milestone section's policy/approval/lease, deadline/TTL, idempotency/replay,
rollback, receipt/redaction fields and the Shared Future Runtime Gate. It may
not be borrowed by another lane. Missing, unknown, or mismatched profile input
blocks the exact lane before start.

<!-- MSG-MX-LANE-LEDGER:START -->
| Planned lane ref | Milestone | Domain / capability projection | Adapter / target binding | Route side-effect posture | Catalog | Compatibility | Configuration | Health | Authority | Resource | Cost | Readiness | Safe-disable | Freshness | Gate obligations | Promotion evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `planned-lane-ref:matrix:harness-inspect` | MSG-MX-004 | taxonomy_gap / read | disabled harness / exact service ref | gap: local service inspection | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-004:harness-inspect-proof` |
| `planned-lane-ref:matrix:harness-start` | MSG-MX-004 | taxonomy_gap / execute | pinned harness / exact loopback target | gap: local service lifecycle | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-004:harness-start-proof` |
| `planned-lane-ref:matrix:harness-smoke` | MSG-MX-004 | taxonomy_gap / read | pinned harness / exact loopback target | gap: loopback network read | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-004:harness-smoke-proof` |
| `planned-lane-ref:matrix:harness-stop` | MSG-MX-004 | taxonomy_gap / execute | pinned harness / exact service ref | gap: local service lifecycle | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-004:harness-stop-proof` |
| `planned-lane-ref:matrix:harness-reset-cleanup` | MSG-MX-004 | taxonomy_gap / destructive | pinned harness / exact disposable-state ref | gap: local service cleanup | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-004:harness-cleanup-proof` |
| `planned-lane-ref:matrix:discovery` | MSG-MX-005 | messages / observe (partial) | disabled session adapter / exact endpoint-class ref | governed network read-only after acceptance | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:discovery-proof` |
| `planned-lane-ref:matrix:auth-capability-discovery` | MSG-MX-005 | messages / read (partial) | disabled session adapter / exact homeserver ref | governed network read-only after acceptance | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:auth-capability-proof` |
| `planned-lane-ref:matrix:session-authenticate-create` | MSG-MX-005 | messages / mutate (partial) | disabled session adapter / exact account-session ref | gap: authenticated connector mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:session-create-proof` |
| `planned-lane-ref:matrix:session-refresh` | MSG-MX-005 | messages / mutate (partial) | disabled session adapter / exact session ref | gap: authenticated connector mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:session-refresh-proof` |
| `planned-lane-ref:matrix:session-logout-revoke` | MSG-MX-005 | messages / admin (partial) | disabled session adapter / exact session ref | gap: authenticated connector mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:session-revoke-proof` |
| `planned-lane-ref:matrix:credential-keychain-lifecycle` | MSG-MX-005 | system_settings / write (partial) | disabled credential adapter / exact key-item ref | gap: credential-store mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:keychain-proof` |
| `planned-lane-ref:matrix:sso-browser-launch` | MSG-MX-005 | browser / execute (partial) | disabled SSO adapter / exact launch target | gap: system-browser launch | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:sso-launch-proof` |
| `planned-lane-ref:matrix:sso-callback-consume` | MSG-MX-005 | messages / mutate (partial) | disabled SSO adapter / exact callback ref | gap: authenticated callback mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-005:sso-callback-proof` |
| `planned-lane-ref:matrix:sync-read` | MSG-MX-006 | messages / read (partial) | disabled sync adapter / exact account-room scope | governed network read-only after acceptance | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:sync-proof` |
| `planned-lane-ref:matrix:timeline-pagination` | MSG-MX-006 | messages / read (partial) | disabled sync adapter / exact room-window ref | governed network read-only after acceptance | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:pagination-proof` |
| `planned-lane-ref:matrix:room-state-read` | MSG-MX-006 | messages / read (partial) | disabled sync adapter / exact room-state class | governed network read-only after acceptance | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:room-state-proof` |
| `planned-lane-ref:matrix:encrypted-cache-read` | MSG-MX-006 | taxonomy_gap / read | disabled cache adapter / exact cache-record ref | gap: local encrypted sensitive-state read | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:cache-read-proof` |
| `planned-lane-ref:matrix:encrypted-cache-write` | MSG-MX-006 | taxonomy_gap / write | disabled cache adapter / exact cache-record ref | gap: local encrypted sensitive-state mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:cache-write-proof` |
| `planned-lane-ref:matrix:encrypted-cache-purge` | MSG-MX-006 | taxonomy_gap / destructive | disabled cache adapter / exact cache-scope ref | gap: local encrypted sensitive-state deletion | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:cache-purge-proof` |
| `planned-lane-ref:matrix:cache-key-lifecycle` | MSG-MX-006 | system_settings / admin (partial) | disabled key adapter / exact cache-key ref | gap: credential/key mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-006:cache-key-proof` |
| `planned-lane-ref:matrix:crypto-store-init` | MSG-MX-007 | taxonomy_gap / write | disabled crypto adapter / exact crypto-store ref | gap: crypto-store mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:crypto-store-proof` |
| `planned-lane-ref:matrix:device-verification` | MSG-MX-007 | messages / admin (partial) | disabled crypto adapter / exact device ref | gap: device-trust mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:device-proof` |
| `planned-lane-ref:matrix:cross-signing` | MSG-MX-007 | taxonomy_gap / admin | disabled crypto adapter / exact identity ref | gap: crypto trust mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:cross-signing-proof` |
| `planned-lane-ref:matrix:secure-backup-write` | MSG-MX-007 | taxonomy_gap / write | disabled crypto adapter / exact backup ref | gap: encrypted backup mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:backup-proof` |
| `planned-lane-ref:matrix:restore-recovery` | MSG-MX-007 | taxonomy_gap / admin | disabled crypto adapter / exact recovery target | gap: crypto recovery mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:recovery-proof` |
| `planned-lane-ref:matrix:identity-reset` | MSG-MX-007 | taxonomy_gap / destructive | disabled crypto adapter / exact identity ref | gap: destructive crypto reset | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-007:identity-reset-proof` |
| `planned-lane-ref:matrix:draft-persist` | MSG-MX-008 | messages / draft (partial) | disabled outbox adapter / exact draft ref | gap: local encrypted draft mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:draft-proof` |
| `planned-lane-ref:matrix:manual-send-reply-thread` | MSG-MX-008 | messages / send (partial) | disabled send adapter / exact room-transaction ref | gap: external message mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:send-proof` |
| `planned-lane-ref:matrix:manual-send-retry` | MSG-MX-008 | messages / send (partial) | disabled send adapter / exact prior-transaction ref | gap: external message mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:retry-proof` |
| `planned-lane-ref:matrix:reaction-write` | MSG-MX-008 | messages / write (partial) | disabled send adapter / exact event ref | gap: external message mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:reaction-proof` |
| `planned-lane-ref:matrix:edit-write` | MSG-MX-008 | messages / write (partial) | disabled send adapter / exact event-version ref | gap: external message mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:edit-proof` |
| `planned-lane-ref:matrix:redaction` | MSG-MX-008 | messages / destructive (partial) | disabled send adapter / exact event ref | gap: destructive external mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:redaction-proof` |
| `planned-lane-ref:matrix:typing-indicator` | MSG-MX-008 | messages / write (partial) | disabled send adapter / exact room-session ref | gap: ephemeral external mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:typing-proof` |
| `planned-lane-ref:matrix:read-receipt-write` | MSG-MX-008 | messages / write (partial) | disabled send adapter / exact event ref | gap: external receipt mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:read-receipt-proof` |
| `planned-lane-ref:matrix:outbox-persist` | MSG-MX-008 | taxonomy_gap / write | disabled outbox adapter / exact outbox-record ref | gap: local encrypted outbox mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:outbox-proof` |
| `planned-lane-ref:matrix:outbox-cleanup` | MSG-MX-008 | taxonomy_gap / destructive | disabled outbox adapter / exact outbox-scope ref | gap: local encrypted outbox deletion | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:outbox-cleanup-proof` |
| `planned-lane-ref:matrix:desktop-notification` | MSG-MX-008 | apps / execute (partial) | disabled notification adapter / exact notification target | gap: desktop notification effect | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-008:notification-proof` |
| `planned-lane-ref:matrix:dm-create` | MSG-MX-009 | messages / mutate (partial) | disabled room adapter / exact participant-set ref | gap: external room mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:dm-proof` |
| `planned-lane-ref:matrix:room-create` | MSG-MX-009 | messages / mutate (partial) | disabled room adapter / exact room-proposal ref | gap: external room mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:room-create-proof` |
| `planned-lane-ref:matrix:invite-send` | MSG-MX-009 | messages / send (partial) | disabled room adapter / exact member-room ref | gap: external invite mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:invite-proof` |
| `planned-lane-ref:matrix:room-join` | MSG-MX-009 | messages / mutate (partial) | disabled room adapter / exact room ref | gap: external membership mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:join-proof` |
| `planned-lane-ref:matrix:room-leave` | MSG-MX-009 | messages / destructive (partial) | disabled room adapter / exact room ref | gap: external membership mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:leave-proof` |
| `planned-lane-ref:matrix:role-power-admin` | MSG-MX-009 | messages / admin (partial) | disabled room adapter / exact member-role ref | gap: external privilege mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:role-proof` |
| `planned-lane-ref:matrix:space-mutate` | MSG-MX-009 | messages / mutate (partial) | disabled room adapter / exact Space ref | gap: external hierarchy mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:space-proof` |
| `planned-lane-ref:matrix:notification-settings` | MSG-MX-009 | messages / write (partial) | disabled room adapter / exact account-room ref | gap: external settings mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:notification-settings-proof` |
| `planned-lane-ref:matrix:history-visibility` | MSG-MX-009 | messages / admin (partial) | disabled room adapter / exact room-policy ref | gap: external policy mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:history-proof` |
| `planned-lane-ref:matrix:pin-favorite` | MSG-MX-009 | messages / write (partial) | disabled room adapter / exact room-event ref | gap: external account/room mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:pin-proof` |
| `planned-lane-ref:matrix:encrypted-search` | MSG-MX-009 | messages / read (partial) | disabled search adapter / exact account-room scope | gap: local encrypted search read | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:search-proof` |
| `planned-lane-ref:matrix:media-upload` | MSG-MX-009 | messages / upload + files / read (partial) | disabled media adapter / exact media-source ref | gap: authenticated media transfer | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:upload-proof` |
| `planned-lane-ref:matrix:media-download` | MSG-MX-009 | messages / download (partial) | disabled media adapter / exact media ref | gap: authenticated media transfer | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:download-proof` |
| `planned-lane-ref:matrix:media-materialize` | MSG-MX-009 | files / write (partial) | disabled media adapter / constrained destination ref | gap: local filesystem materialization | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:materialize-proof` |
| `planned-lane-ref:matrix:media-quarantine` | MSG-MX-009 | files / write (partial) | disabled media adapter / exact quarantine ref | gap: local quarantine mutation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:quarantine-proof` |
| `planned-lane-ref:matrix:media-preview` | MSG-MX-009 | files / read (partial) | disabled preview adapter / exact quarantined-media ref | gap: isolated preview parsing | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:preview-proof` |
| `planned-lane-ref:matrix:media-cleanup` | MSG-MX-009 | files / destructive (partial) | disabled media adapter / exact materialization scope | gap: local filesystem deletion | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | unknown | self-bound-profile | `evidence-ref:msg-mx-009:cleanup-proof` |
| `authority-lane-ref:matrix-intelligence-room-ai-policy-read` | MSG-MX-010 | messages / read (partial) | local policy store / exact account-room-policy ref | sensitive local policy inspection | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:policy-contract-tests` |
| `authority-lane-ref:matrix-intelligence-room-ai-policy-write` | MSG-MX-010 | messages / mutate (partial) | local policy store / exact account-room-policy-grant ref | sensitive local policy mutation | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:policy-contract-tests` |
| `authority-lane-ref:matrix-intelligence-context-materialize` | MSG-MX-010 | messages / read (partial) | transient local context owner / exact account-room-event-range ref | sensitive transient local content materialization | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:context-isolation-tests` |
| `planned-lane-ref:matrix:provider-invoke` | MSG-MX-010 | provider_model_calls / execute (partial) | absent provider adapter / exact model destination | gap: governed provider invocation | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | blocked | self-bound-profile | `blocked-reason-ref:msg-mx:model-provider-runtime-prohibited` |
| `authority-lane-ref:matrix-intelligence-proposal-read` | MSG-MX-010 | messages / read (partial) | redacted local proposal store / exact proposal ref | sensitive local proposal inspection | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:proposal-contract-tests` |
| `authority-lane-ref:matrix-intelligence-proposal-persist` | MSG-MX-010 | messages / mutate (partial) | redacted local proposal store / exact proposal fingerprint | sensitive local proposal mutation | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:proposal-contract-tests` |
| `authority-lane-ref:matrix-intelligence-proposal-delete` | MSG-MX-010 | messages / destructive (partial) | redacted local proposal store / exact proposal ref | destructive local proposal deletion | supported | supported | configured | available | lease_required | available | not_metered | inactive | current | request_scoped | self-bound-profile | `evidence-ref:msg-mx-010:proposal-delete-tests` |
| `planned-lane-ref:matrix:attachment-scan-analyze` | MSG-MX-010 | files plus taxonomy gap / execute | absent composite attachment owner / exact attachment-scanner-parser-cleanup refs | gap: conjunctive materialize/scan/analyze/cleanup authority | unsupported | unknown | not_configured | unknown | blocked | unknown | unknown | unknown | unknown | blocked | self-bound-profile | `blocked-reason-ref:msg-mx:attachment-composite-binding-not-proven` |
<!-- MSG-MX-LANE-LEDGER:END -->

## Per-Milestone Contracts

<!-- MSG-MX-SECTIONS:START -->

### MSG-MX-000

- Declaration status: `declared`.
- Program status: `planning_audit_accepted_on_merge`.
- Implementation status: `implemented_planning_audit`.
- Availability snapshot posture: `not_created_no_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: none.
- Current domain/capability mapping: audit of canonical contracts only.
- Taxonomy gap: recorded for later phases; no enum is added here.
- Adapter/provider/target scope: none.
- Route/side-effect posture: no route or side effect.
- Policy/approval/lease gate: no runtime evaluation is performed.
- Deadline/TTL posture: not applicable.
- Idempotency/replay posture: document/verifier output is deterministic.
- Rollback posture: revert only through a later scoped PR; no runtime rollback.
- Receipt/evidence/redaction: repo-safe refs and hashes only; no raw content.
- Blocker refs: none for this planning audit.
- Promotion evidence: merged map, verifier, tests, docs checks, and Foundation Gate.

### MSG-MX-001

- Declaration status: `planned`.
- Program status: `planned_no_runtime_authority`.
- Implementation status: `missing`.
- Availability snapshot posture: `not_created_no_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: none; design and threat-model artifacts only.
- Current domain/capability mapping: canonical authority taxonomy is reviewed, not changed.
- Taxonomy gap: exact connector, credential, crypto, cache, media, and route classes must be designed.
- Adapter/provider/target scope: none.
- Route/side-effect posture: no route or side effect.
- Policy/approval/lease gate: no runtime evaluation is performed.
- Deadline/TTL posture: not applicable.
- Idempotency/replay posture: design bundle and render decisions are versioned.
- Rollback posture: doc-only PR rollback.
- Receipt/evidence/redaction: clean-room ADR, license review, safe threat refs, no secrets.
- Blocker refs: `blocked-reason-ref:msg-mx:design-not-accepted`.
- Promotion evidence: all render decisions, ADR, threat model, and exact authority matrix accepted.

### MSG-MX-002

- Declaration status: `planned`.
- Program status: `planned_no_runtime_authority`.
- Implementation status: `missing`.
- Availability snapshot posture: `not_created_no_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: fixture-only desktop rendering; no command capability.
- Current domain/capability mapping: none; UI commands remain Preview, Planned, or Blocked.
- Taxonomy gap: none may be solved in this phase.
- Adapter/provider/target scope: fixtures only; no adapter or account target.
- Route/side-effect posture: no new route; presentation-only state.
- Policy/approval/lease gate: UI state cannot mint authority.
- Deadline/TTL posture: not applicable.
- Idempotency/replay posture: deterministic fixtures and visual baselines.
- Rollback posture: frontend PR rollback.
- Receipt/evidence/redaction: synthetic refs and bounded fixture summaries only.
- Blocker refs: `blocked-reason-ref:msg-mx:matrix-adapter-not-implemented`.
- Promotion evidence: desktop render, state, accessibility, product-language, and frontend checks.

### MSG-MX-003

- Declaration status: `planned`.
- Program status: `planned_no_runtime_authority`.
- Implementation status: `missing`.
- Availability snapshot posture: `not_created_no_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: contract and read-only inspection refs only.
- Current domain/capability mapping: generic `messages` semantics may inform contracts but grant nothing.
- Taxonomy gap: exact Matrix lane/domain and mutation side-effect classes remain absent.
- Adapter/provider/target scope: `adapter-ref:matrix:disabled-not-implemented`; safe refs only.
- Route/side-effect posture: read-only inspection may use `none`; no live network or mutation route.
- Policy/approval/lease gate: disabled adapter refuses every execution attempt.
- Deadline/TTL posture: inspection snapshots require explicit freshness posture.
- Idempotency/replay posture: deterministic contract projection only.
- Rollback posture: schema/version rollback-readiness documented before runtime.
- Receipt/evidence/redaction: safe contract refs; no raw bodies, accounts, rooms, tokens, or paths.
- Blocker refs: `blocked-reason-ref:msg-mx:matrix-sdk-not-installed`.
- Promotion evidence: Python/API/CLI parity, disabled-adapter tests, manifest/OpenAPI truth.

### MSG-MX-004

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: `matrix.harness.start`, `matrix.harness.inspect`, `matrix.harness.smoke`, `matrix.harness.stop`, `matrix.harness.reset`.
- Current domain/capability mapping: no exact mapping; broad apps/shell authority is not acceptable.
- Taxonomy gap: loopback network, pinned dependency/container, and local service lifecycle.
- Adapter/provider/target scope: digest-pinned Synapse, allowlisted loopback endpoints, disposable data, bounded lifetime.
- Route/side-effect posture: no runtime entry point exists until a truthful side-effect class and exact Python Core lane are separately accepted; any repo-local harness script is test-only and cannot bypass policy, approval, lease, budget, readiness, kill-switch, safe-disable, idempotency, or receipt gates.
- Policy/approval/lease gate: exact per-command policy, approval where mutating, mission lease, target, and cleanup binding.
- Deadline/TTL posture: bounded startup, smoke, shutdown, and residual-resource deadlines.
- Idempotency/replay posture: exact lifecycle request fingerprint; duplicate start/reset fails or replays terminal receipt.
- Rollback posture: stop, delete disposable state, prove no residual service or volume.
- Receipt/evidence/redaction: content-free lifecycle receipts; no secrets, logs, host identity, or local paths.
- Blocker refs: `blocked-reason-ref:msg-mx:local-network-authority-not-accepted`, `blocked-reason-ref:msg-mx:route-side-effect-taxonomy-incomplete`.
- Promotion evidence: hostile public-bind/target/stale-lease/residual-data/cleanup tests and exact authority acceptance.

### MSG-MX-005

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: discovery/read, session create/refresh/logout/revoke, account auth, Keychain lifecycle, SSO launch, loopback callback.
- Current domain/capability mapping: `messages/observe|read`, `messages/mutate|admin`, `system_settings/write|admin`, and browser scope are only partial semantics.
- Taxonomy gap: connector session/auth, credential backend, exact redirect/callback, and authenticated mutation route classes.
- Adapter/provider/target scope: `adapter-ref:matrix-session:not-implemented`; exact homeserver, account, endpoint class, redirect, and credential backend refs.
- Route/side-effect posture: discovery may later be governed network read-only; auth/session/credential mutations remain unclassifiable and blocked.
- Policy/approval/lease gate: separate exact evaluation for discovery, auth, session mutation, browser launch, callback, and credential mutation.
- Deadline/TTL posture: short discovery/callback deadlines plus bounded session and credential TTLs.
- Idempotency/replay posture: callback nonce, singleton session ownership, and request-fingerprint-bound refresh/logout/revoke.
- Rollback posture: revoke session, delete exact credential item, disable adapter, and prove terminal receipt.
- Receipt/evidence/redaction: refs and hashes only; no credentials, tokens, raw account or endpoint values.
- Blocker refs: `blocked-reason-ref:msg-mx:credential-authority-not-accepted`, `blocked-reason-ref:msg-mx:route-side-effect-taxonomy-incomplete`.
- Promotion evidence: SSRF, redirect substitution, callback replay, credential fallback, stale lease, and duplicate ownership proofs.

### MSG-MX-006

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: connector read/sync/pagination, scoped room/account observation, encrypted cache lifecycle, cache-key lifecycle.
- Current domain/capability mapping: `messages/read` partially describes remote reads; it does not authorize Matrix sync or cache mutation.
- Taxonomy gap: connector transport, encrypted sensitive-state mutation, key lifecycle, and multi-scope binding.
- Adapter/provider/target scope: `adapter-ref:matrix-sync:not-implemented`; exact account, room set, event classes, cache schema, key item, and retention refs.
- Route/side-effect posture: remote reads may later be governed network read-only; cache/key mutation needs a new exact class.
- Policy/approval/lease gate: exact connector-read and separate cache/key mutation decisions; no connector-write scope.
- Deadline/TTL posture: bounded sync window, pagination, snapshot freshness, retention, and cache expiry.
- Idempotency/replay posture: sync-token and event-fingerprint replay with cross-account/room rejection.
- Rollback posture: stop sync, lock/delete cache by exact scope, exclude backups, retain content-free receipt.
- Receipt/evidence/redaction: safe source/event refs and counts only; no bodies, room/account values, tokens, or cache paths.
- Blocker refs: `blocked-reason-ref:msg-mx:connector-read-authority-not-accepted`, `blocked-reason-ref:msg-mx:credential-authority-not-accepted`.
- Promotion evidence: restart/idempotency, exclusion, key-loss, locked-store, downgrade, deletion-residue, and scope-isolation tests.

### MSG-MX-007

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: crypto-store lifecycle, device verification, cross-signing, backup, restore, recovery, destructive identity reset.
- Current domain/capability mapping: broad `messages/admin` or `system_settings/admin|destructive` is insufficient without exact lanes and targets.
- Taxonomy gap: crypto store, device trust, key lifecycle, recovery material, backup, and destructive reset.
- Adapter/provider/target scope: `adapter-ref:matrix-crypto:not-implemented`; exact account, device, store, backup, and recovery refs.
- Route/side-effect posture: no truthful crypto/key mutation or destructive-reset side-effect class exists.
- Policy/approval/lease gate: every crypto operation separately evaluated; identity reset requires separate exact confirmation.
- Deadline/TTL posture: freshness-bound device/backup evidence and bounded recovery/reset windows.
- Idempotency/replay posture: operation and key/version fingerprints; stale verification and recovery replay rejected.
- Rollback posture: explicit irreversibility where applicable; safe backup/restore rollback-readiness only when proven.
- Receipt/evidence/redaction: content-free refs/hashes only; recovery material and keys remain transient and never logged.
- Blocker refs: `blocked-reason-ref:msg-mx:crypto-authority-not-accepted`, `blocked-reason-ref:msg-mx:route-side-effect-taxonomy-incomplete`.
- Promotion evidence: key substitution, device confusion, stale trust, backup rollback, replay, loss, restore, and destructive mismatch tests.

### MSG-MX-008

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: draft, human send/reply/thread/retry, reaction/edit/redaction, typing/read receipt, encrypted outbox, cleanup, desktop notification.
- Current domain/capability mapping: `messages/draft|send|write|mutate|destructive` is partial; the existing live-send lane is not Matrix proof.
- Taxonomy gap: exact Matrix transaction, encrypted draft/outbox, notification target, external mutation, and destructive redaction.
- Adapter/provider/target scope: `adapter-ref:matrix-send:not-implemented`; exact account, room, event/transaction, content fingerprint, outbox, and notification refs.
- Route/side-effect posture: no truthful external message mutation class exists; UI commands remain blocked until added.
- Policy/approval/lease gate: exact human command, target/content fingerprint, approval, mission lease, and current pre-start evaluation.
- Deadline/TTL posture: bounded draft/outbox TTL, send deadline, retry window, and notification freshness.
- Idempotency/replay posture: stable transaction/idempotency ref; changed target/content and cross-room replay rejected.
- Rollback posture: draft/outbox delete and compensation/readiness refs; no false unsend claim.
- Receipt/evidence/redaction: content-free delivery/uncertainty receipts; message content is never durable evidence.
- Blocker refs: `blocked-reason-ref:msg-mx:connector-write-authority-not-accepted`, `blocked-reason-ref:msg-mx:route-side-effect-taxonomy-incomplete`.
- Promotion evidence: manual encrypted send/restart/failure/duplicate/uncertainty proof and Element interoperability where genuinely available.

### MSG-MX-009

- Declaration status: `planned`.
- Program status: `blocked_pending_separate_exact_authority`.
- Implementation status: `unsupported_missing`.
- Availability snapshot posture: `baseline_fail_closed_projection_not_persisted`.
- Catalog status: `unsupported`.
- Compatibility status: `unknown`.
- Configuration status: `not_configured`.
- Health status: `unknown`.
- Authority posture: `blocked`.
- Resource/budget status: `unknown`.
- Cost posture: `unknown`.
- Safe-disable status: `unknown`.
- Freshness status: `unknown`.
- Derived readiness: `unknown`.
- Planned exact capability refs: DM/room/invite/join/leave/roles/Spaces/notifications, encrypted search, media upload/download/materialize/quarantine/preview/cleanup.
- Current domain/capability mapping: `messages/read|mutate|admin|upload|download` and `files/read|write` are partial and must be conjunctively exact.
- Taxonomy gap: composite multi-domain authority, room administration, authenticated transfer, quarantine, preview parser, cleanup, and external mutations.
- Adapter/provider/target scope: `adapter-ref:matrix-media:not-implemented`; exact account, room/member, media, constrained filesystem root, and search scope refs.
- Route/side-effect posture: no truthful room/admin/media-transfer/materialization classes exist; read-only class cannot be reused.
- Policy/approval/lease gate: separate exact decisions for each room/admin/media/search operation and every required domain.
- Deadline/TTL posture: bounded invite/admin/search/transfer/quarantine/preview/cleanup deadlines and retention.
- Idempotency/replay posture: exact target and media fingerprints; duplicate mutation/transfer and path substitution rejected.
- Rollback posture: compensation for room/admin changes where possible; exact cleanup and quarantine residue proof.
- Receipt/evidence/redaction: safe media/search/result refs and counts only; no bytes, room/member values, or filesystem paths.
- Blocker refs: `blocked-reason-ref:msg-mx:media-authority-not-accepted`, `blocked-reason-ref:msg-mx:composite-authority-binding-not-proven`.
- Promotion evidence: escalation, traversal, symlink/FIFO/device, decompression, MIME, quarantine, parser, cross-room, and cleanup hostile tests.

### MSG-MX-010

- Declaration status: `partial`.
- Program status: `partial_exact_local_lanes`.
- Implementation status: `context_policy_and_proposal_core_implemented`.
- Availability snapshot posture: `backend_owned_request_scoped_current`.
- Catalog/compatibility/configuration/health: accepted six local lanes are `supported` / `supported` / `configured` / `available`; provider and attachment families remain `unsupported` / `unknown` / `not_configured` / `unknown`.
- Authority posture: `lease_required` for each accepted lane; blocked families have no binding or executor.
- Resource/budget and cost: exact local operations are bounded and zero-cost/not-metered.
- Safe-disable/freshness/readiness: re-evaluated immediately before every start; unknown, stale, killed, or disabled state fails closed.
- Accepted exact capability refs: policy read/write, transient context materialize, and redacted proposal read/persist/delete.
- Blocked capability refs: provider invocation and attachment materialize/scan/analyze/cleanup.
- Current domain/capability mapping: six accepted local lanes use exact `messages/read|mutate|destructive`; provider and attachment taxonomy/composite authority remain absent.
- Adapter/provider/target scope: exact account, room/event range, task/mission/run, local model-destination-blocked ref, local-only disclosure, policy/grant, proposal, budgets, deadline, readiness, lease, idempotency, and rollback refs.
- Route/side-effect posture: eight protected no-store routes exist; six operations require authority and idempotency. No provider or attachment execution route exists.
- Deadline/TTL posture: context grants/manifests expire within 900 seconds and proposals within 1,800 seconds.
- Idempotency/replay posture: complete request/content/proposal fingerprints reject cross-room/account, changed-content, and same-key substitution.
- Rollback posture: context is transient; policy compensation needs a new exact write; proposal persist has exact deletion; deletion makes no restore claim.
- Receipt/evidence/redaction: refs, fingerprints, counts, bounded safe summaries, expiry, and content-free receipts only; no raw bodies, prompts, responses, provider payloads, attachments, or paths.
- Blocker refs: `blocked-reason-ref:msg-mx:model-provider-runtime-prohibited`, `blocked-reason-ref:msg-mx:model-context-authority-not-accepted`, `blocked-reason-ref:msg-mx:attachment-scanner-adapter-missing`, `blocked-reason-ref:msg-mx:attachment-composite-binding-not-proven`.
- Evidence: `docs/connectors/MESSENGER_MATRIX_INTELLIGENCE_PROPOSALS.md`, `scripts/verify_msg_mx_010_intelligence_proposals.py`, focused injection/isolation/stale-grant/disclosure/replay/Memory-denial tests.

### MSG-MX-011

- Declaration status: `planned`.
- Program status: `planned_no_new_lane_hardening`.
- Implementation status: `missing`.
- Availability snapshot posture: `not_created_no_new_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: none; hardening only.
- Current domain/capability mapping: only exact previously accepted mappings may be exercised.
- Taxonomy gap: unresolved gaps remain blockers, not hardening exceptions.
- Adapter/provider/target scope: exact accepted refs only.
- Route/side-effect posture: existing exact accepted classification only.
- Policy/approval/lease gate: the full shared future runtime gate applies before every exercised call.
- Deadline/TTL posture: current exact lane deadlines and freshness apply.
- Idempotency/replay posture: current exact lane proof applies; no retry broadening.
- Rollback posture: current exact lane rollback/safe-disable proof applies.
- Receipt/evidence/redaction: content-free hardening evidence only.
- Blocker refs: `blocked-reason-ref:msg-mx:unaccepted-lane-cannot-be-exercised`.
- Promotion evidence: bounded performance/security/recovery/accessibility drills without new authority.

### MSG-MX-012

- Declaration status: `planned`.
- Program status: `planned_no_new_lane_acceptance`.
- Implementation status: `missing`.
- Availability snapshot posture: `not_created_no_new_runtime_lane`.
- Catalog status: `not_applicable_audit_metadata`.
- Compatibility status: `not_applicable_audit_metadata`.
- Configuration status: `not_applicable_audit_metadata`.
- Health status: `not_applicable_audit_metadata`.
- Authority posture: `not_applicable_audit_metadata`.
- Resource/budget status: `not_applicable_audit_metadata`.
- Cost posture: `not_applicable_audit_metadata`.
- Safe-disable status: `not_applicable_audit_metadata`.
- Freshness status: `not_applicable_audit_metadata`.
- Derived readiness: `not_applicable_audit_metadata`.
- Planned exact capability refs: none; integrated review and acceptance only.
- Current domain/capability mapping: exact previously accepted mappings only.
- Taxonomy gap: any unresolved gap is reported blocked or external-facility-required.
- Adapter/provider/target scope: exact accepted refs only.
- Route/side-effect posture: existing exact accepted classification only.
- Policy/approval/lease gate: the full shared future runtime gate applies before every exercised call.
- Deadline/TTL posture: current exact lane deadlines and freshness apply.
- Idempotency/replay posture: current exact lane proof applies; no synthetic pass.
- Rollback posture: acceptance verifies real rollback/readiness evidence only.
- Receipt/evidence/redaction: redacted packet with refs/hashes/counts; no raw messages, keys, attachments, logs, identities, or paths.
- Blocker refs: `blocked-reason-ref:msg-mx:unaccepted-lane-cannot-be-exercised`.
- Promotion evidence: code, tests, runtime evidence, operator visibility, and genuine interoperability where available.

<!-- MSG-MX-SECTIONS:END -->

## Program-Wide Deny Floor

Calls, agent room participants, hosted infrastructure, public federation,
autonomous sends, hidden context injection, automatic Memory truth/writes,
broad connector authority, public release, and production authority are not
granted by this program. Linux, Windows, and mobile implementation are outside
this desktop-only baseline.

Every status change requires a scoped PR with implementation, adversarial tests,
accepted exact authority, current availability and budget truth, API/CLI parity
when operator-relevant, truthful route classification, redaction, content-free
receipts, rollback or rollback-readiness, safe-disable, and post-merge evidence.
