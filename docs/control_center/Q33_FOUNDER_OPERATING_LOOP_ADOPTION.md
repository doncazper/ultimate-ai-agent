# Q33 Founder Operating Loop Functional Adoption

Status: terminal at protected merge
`d6d5b97ac87b51e002d236f32a035739a74a4f38`, with green post-merge CI
`34715302806` and Supply Chain `34715302797` evidence.

## Implemented Chat workspace slice

The Control Center `/chat` surface now starts with a readable conversation
workspace before the existing readiness and redacted-probe diagnostics. A
clean install can create an unsent draft without credentials or a model. The
conversation rail supports local search, selection, archive, and recovery.

Python Agent Core owns the durable product state through:

- `GET /control-center/chat/workspace`
- `POST /control-center/chat/threads/{thread_ref}/approval`
- `POST /control-center/chat/threads/{thread_ref}/draft-checkpoint`
- `POST /control-center/chat/threads/{thread_ref}/lifecycle`

The read-only `python scripts/inspect_chat_workspace.py` command projects the
same content-free workspace contract without creating local state or printing
the inspected path.

The server stores only the thread ref, generated display name, lifecycle state,
revision, draft-present flag, character count, and an opaque random session
fingerprint that is not derived from the draft text. It
does not receive or store the draft body. The current browser tab may retain up
to 100 unsent drafts in memory, including while the operator navigates away
from and back to Chat, and keeps each non-empty local conversation reachable
from the rail. Draft bodies are discarded on reload. If a tab-local body is
missing or its fingerprint does not match the backend checkpoint, the UI
reports that re-entry is required instead of inventing a recovery.

Draft checkpoints and archive/recover requests require the existing Control
Center backend-truth binding, explicit operator confirmation, exact
`LocalApprovalAuthority` scope validation, expected current revision, exact
idempotency input, targeted local rate limits, bounded request size and JSON
depth, durable replay/conflict handling, private no-store responses, and
content-free receipt/audit refs. Creation stops at the same 100-thread bound
published by the read contract. A separate durable approval route captures the
exact operator-confirmed grant before the mutation request; approval capture
alone does not mutate the workspace. The Python mutation service can only load
and validate that already captured exact grant and cannot issue authority for
itself. Active approvals expire after five minutes and are capped at 512. Each
approval capture attempt is exact-idempotent and cannot renew its own expired
tombstone. An unused expired attempt may be replaced by one fresh, separately
identified approval attempt while the mutation keeps its original durable
idempotency identity. A completed exact mutation can still replay its immutable
receipt after the governing approval expires; this recovery path performs no
new state change. The combined approval history is capped at the same
10,000-record bound as workspace mutations. Every supplied idempotency alias
must be individually valid and equal.

The workspace accepts at most 10,000 unique mutation records. Once that bound
is reached, old keys still replay exactly while new keys fail before state is
changed. A transactional evidence outbox repairs a failed JSONL append on exact
replay. Fresh delivery appends directly; the full log is consulted only after
an ambiguous interrupted delivery, including legacy crash rows migrated as
already attempted. Stored replay receipts are reconstructed through the
governing contract before they can be returned. Each checkpoint overwrite
receipt also carries an exact, content-free snapshot and fingerprint of the
immediately prior thread revision, so the overwritten state remains reviewable
without retaining a draft body or granting a rollback mutation.

## Authority boundary

This slice adds no ordinary Chat send, provider or model call, second model
call, tool execution, memory write, context injection, connector read/write,
web access, shell execution, action execution, approval shortcut, public
release claim, or production authority. The Send control remains unavailable.
The existing separately governed redacted readiness probe remains unchanged.

## Implemented Setup readability slice

The Control Center `/setup` surface now reads only the backend-truth-bound
`GET /control-center/setup-assistant/summary` contract instead of waiting for
the unrelated Control Center read fan-out. Its first screen summarizes
backend-owned ready, missing, and blocked diagnostic counts, identifies one
priority attention item, and shows one next safe action. The complete lifecycle,
health, proof, model-recommendation, approval-envelope, receipt, rollback, and
blocked-authority detail remains available in a collapsed technical disclosure.
Optional provider posture remains on `/settings` rather than delaying Setup.

Malformed or fallback-derived Setup responses fail closed. Opening or expanding
the surface performs no checks, probes, installs, downloads, provider/model
calls, credential work, settings changes, or lifecycle mutations.

## Implemented review-to-local-task slice

The North Star `/workspace/decisions` surface now continues an exact
`local_task_create` approval into the existing governed local-task commit lane.
The route loads only the backend-truth envelope and bounded Action Inbox
contract needed for this surface, instead of waiting for the unrelated full
Control Center read fan-out. Unrelated shell posture stays visibly unverified.
The control appears only after the refreshed Python Core Action Inbox proves
the exact item is in `approved_local_task_lane`, binds the approval envelope,
scope, idempotency, rollback, safe-disable, route, and approved cost posture,
and reports every broader authority flag disabled.

The UI validates the returned receipt against the exact item and approval,
requires the content-free local-task contract, and rejects any receipt that
claims connector, shell, provider/model, memory, context-injection, raw-content,
external side effects, local paths, account identifiers, or hostname-shaped
values. Authority previews initiated by the browser are accepted only while
their exact backend revision, process instance, and issued truth envelope remain
current; repo-local preview callers without browser binding retain CLI parity.
Denied previews remain visible with a Settings recovery path and never expose
the commit control. The UI then refreshes the backend Action Inbox, propagates
that authoritative snapshot to sibling Action Inbox controls, and does not
claim reconciliation until the canonical backend-owned receipt projection
binds both the exact item-derived task ref and local-task receipt ref.

This completes the bounded Decision -> approved local Task handoff on the
North Star surface. It does not add broad action execution or make the Work
Board and Calendar adoption work terminal.

## Implemented Work Board adoption slice

The primary `/work-board` surface now starts with a Python/API-owned
founder-private workspace for normal create, inspect, edit, move, archive,
recover, and undo work. The browser presents readable lanes, private item
detail, explicit preview, confirmation, receipt, backup, restore, and recovery
states. The earlier diagnostic Kanban remains available as supporting detail;
it is no longer the primary operator workflow.

Python Agent Core owns the durable product state through:

- `GET /control-center/work-board/adoption`
- `POST /control-center/work-board/adoption/preview`
- `POST /control-center/work-board/adoption/approval`
- `POST /control-center/work-board/adoption/commit`
- `POST /control-center/work-board/adoption/backup`
- `POST /control-center/work-board/adoption/restore-preview`
- `POST /control-center/work-board/adoption/restore-approval`
- `POST /control-center/work-board/adoption/restore-commit`

Every state change is revision-bound, exact-preview-bound, exact-approval-bound,
idempotent, receipt-producing, and limited to one `workspace/write` operation by
a short-lived AuthorityLease. Reusing an idempotency ref with a different
payload fails closed. Restore replay is bound to the exact encrypted backup,
preview, and approval. Corrupt, malformed, oversized, duplicate-identity, and
symlinked state fails into an explicit recovery posture rather than being
treated as an empty board.

Local board state is founder-private JSON restricted to the current account by
directory mode `0700` and file mode `0600`; it is not claimed to be encrypted at
rest, so host disk encryption remains the device boundary. Portable backups use
Scrypt-derived AES-GCM encryption and never include key material or raw paths.
Moving an encrypted backup between the founder's computers provides manual
continuity. Automatic sync, concurrent multi-device merging, connector storage,
and cloud authority are not included.

`python scripts/dev/uaa_work_board.py inspect-adoption` inspects the same state
through the Core contract. Its safe default returns counts, refs, readiness, and
blocked-authority flags without private titles or descriptions; the operator
must explicitly pass `--include-private` to print local private values.

The Work Board remains planning state only. A card does not execute a task or
grant provider/model, connector, shell, browser, background, public-release, or
production authority.

## Implemented Calendar adoption slice

The primary `/workspace/calendar` surface now starts with a Python/API-owned,
founder-private Calendar for ordinary local event planning. It supports
multiple local calendars, readable day, week, month, and agenda views, search,
conflict visibility, create, edit, archive, recover, recurrence, undo, encrypted
backup, and exact restore. The earlier synthetic Calendar fixture remains
collapsed as supporting diagnostics and is not product truth.

Python Agent Core owns the durable product state through:

- `GET /control-center/calendar/adoption`
- `POST /control-center/calendar/adoption/preview`
- `POST /control-center/calendar/adoption/approval`
- `POST /control-center/calendar/adoption/commit`
- `POST /control-center/calendar/adoption/backup`
- `POST /control-center/calendar/adoption/restore-preview`
- `POST /control-center/calendar/adoption/restore-approval`
- `POST /control-center/calendar/adoption/restore-commit`

Every local change binds the current revision, exact payload fingerprint,
preview, approval, backend-truth envelope, idempotency ref, authority decision,
short-lived operation-budget-one `workspace/write` AuthorityLease, durable
receipt, and rollback ref. A durable content-free checkpoint is recorded before
the canonical Calendar transaction so an interrupted response can recover the
exact receipt without a duplicate event write. A completed checkpoint is
revalidated against the encrypted repository transaction before replay.

Calendar state uses the canonical ECO-004 encrypted local repository. Portable
backups use Scrypt-derived AES-GCM encryption and bind the encrypted bundle to
its exact source revision and creation timestamp. Restore is bounded,
fingerprint-checked, revision-aware, exact-idempotent, and fail-closed for a
wrong passphrase, substituted metadata, corrupt state, unsafe links, or an
ambiguous current target. Manual encrypted export/import provides continuity
between the founder's own computers; automatic or concurrent sync is not
included.

When the current SQLite database is corrupt but remains an exact, readable,
owner-only regular file, restore binds the database and SQLite sidecar bytes to
the reviewed preview, builds and integrity-checks a complete replacement in a
private staging directory, then atomically publishes it only after the same
approval and AuthorityLease checks. The confirmation reports unknown current
impact and no rollback rather than calling the damaged target empty. Unsafe,
changed, or unbindable state remains blocked.

`python scripts/dev/uaa_calendar.py inspect-adoption` reads the same Core
contract. Its safe default prints only counts, refs, readiness, and blocked
authority flags; `--include-private` is required to print event values.

This slice adds no account adapter, external calendar read/write, connector,
background scheduler, notification delivery, provider/model call, browser or
shell execution, automatic sync, public release, or production authority.

## Verification

- `tests/test_q33_chat_content_free_workspace.py`
- `tests/test_q33_work_board_adoption.py`
- `tests/test_q33_work_board_adoption_api.py`
- `tests/test_q33_work_board_adoption_cli.py`
- `tests/test_queue_v2_q33_work_board_adoption.py`
- `tests/test_q33_calendar_adoption.py`
- `tests/test_q33_calendar_adoption_api.py`
- `tests/test_q33_calendar_adoption_cli.py`
- `tests/test_queue_v2_q33_calendar_adoption.py`
- `tests/test_control_center_mutation_backend_truth_binding.py`
- `apps/control-center/src/components/ChatWorkspacePanel.test.tsx`
- `apps/control-center/src/api/client.setupRoute.test.ts`
- `apps/control-center/src/components/MacOSSetupAssistantPanel.test.tsx`
- `apps/control-center/src/northstar/WiredSurfaces.test.tsx`
- `apps/control-center/src/App.backendTruth.test.tsx`
- `apps/control-center/src/api/client.calendar-adoption.test.ts`
- `apps/control-center/src/components/CalendarAdoptionWorkspace.test.tsx`
- `python scripts/inspect_chat_workspace.py --state-dir <local-state-dir>`
- `python scripts/dev/uaa_work_board.py inspect-adoption --state-dir <local-state-dir>`
- `python scripts/dev/uaa_calendar.py inspect-adoption --state-dir <local-state-dir>`
- `python scripts/verify_queue_v2_q33_work_board_adoption.py`
- `python scripts/verify_queue_v2_q33_calendar_adoption.py`
- OpenAPI/API manifest snapshot and documentation-integrity verification

Together these accepted slices close the bounded founder-private Q33 Operating
Loop adoption contract. Ordinary Chat send/model execution, external calendar
or task connectors, automatic multi-device sync, public release, and production
authority remain separately gated rather than becoming hidden Q33 scope.
