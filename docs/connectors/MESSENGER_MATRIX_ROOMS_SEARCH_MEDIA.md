# Messenger Matrix Rooms, Encrypted Search, And Bounded Media

Status: MSG-MX-009 exact Python Core and native broker implementation. The
default runtime remains `configuration_required`; this is not standing Matrix,
connector, network, room-administration, filesystem, or search authority.

## Exact lanes

Python Core owns twenty separately evaluated operations:

- direct-message and room create, join, and leave;
- invite send, accept, reject, and withdraw;
- room power-role, Space mapping, notification, history-visibility, pin, and
  account-room preference writes;
- encrypted local search;
- media upload, authenticated download into quarantine, materialization,
  metadata-only preview, and cleanup.

Every operation binds the exact request, task, mission, run, dispatch,
idempotency, account, loopback homeserver, device, target, capability, adapter,
provider, readiness, deadline, zero-cost budget, kill switch, safe-disable,
rollback or compensation posture, and complete request fingerprint. Relevant
room, member, event, transaction, Space, media, source-file, quarantine,
materialization, filesystem-root, search-index, query, allowlist, prior-state,
desired-state, media-type, and parser refs are required per operation and are
forbidden everywhere else.

Media upload requires the exact composite `messages/upload + files/read`
lease. Authenticated download requires `messages/download + files/write`.
Substituting, omitting, or adding a domain or capability fails closed. Every
lane requires a fresh exact LocalApprovalAuthority result and current exact
AuthorityLease; an approval ref is only an identifier.

The dispatcher re-evaluates PolicyEngine, approval scope, the entire lease
domain map, request fingerprint, adapter/executor binding, readiness,
deadline, budget, kill switch, safe-disable, and replay posture immediately
before the one operation starts. Unknown, stale, expired, revoked, or
mismatched state does not reach the broker, encrypted index, or filesystem.

## Room and membership safety

The one-use HMAC-authenticated loopback Rust broker extends the pinned
`matrix-sdk` 0.18.0 boundary from MSG-MX-008. The Python boundary binds raw
transient room/member/event/transaction/state values to their approved safe
refs before constructing a broker frame, and the Rust protocol rejects every
irrelevant safe or transient field.

Join, leave, invite, room-admin, Space, notification, history, pin, and
account-room preference mutations compare the caller-bound prior state with
fresh synchronized Matrix state. Power writes additionally reject stale
levels, values outside `-100..100`, and elevation above the current operator's
own power. Restoring prior state is a separate approved operation; receipts do
not claim rollback of an already acknowledged Matrix event. A stable
idempotency/request-fingerprint fence prevents a terminal replay from invoking
the SDK again. An uncertain outcome remains uncertain and cannot be retried
automatically.

## Encrypted local search

Search uses an app-owned AES-GCM cache backend and HMAC-hashed query tokens.
Raw message bodies and raw queries are not written to the index. Rebuild binds
the exact account, index generation, room allowlist, and bounded document set;
search binds the same account/index plus a query ref, optional exact room, and
result cap. Cross-room results are filtered before return. Rebuild replaces
deleted-event refs, purge proves path absence, and no plaintext WAL, journal,
or query cache is created.

The implementation caps a document body at 16 KiB, one rebuild at 10,000
documents and 4 MiB of source text, one document at 256 unique index tokens,
the encrypted index at 2 MiB, a query at
4 KiB, the room allowlist at 256 refs, and a result set at 100 refs. Index and
directory identity, ownership, permissions, single-link regular-file posture,
bounded reads/writes, and FIFO/symlink substitution are checked on every use.

## Media lifecycle

Media is limited to 24,576 bytes and the exact allowlist `image/png`,
`image/jpeg`, `image/gif`, and UTF-8 `text/plain`. Upload reads only a private
app-owned staging directory through a verified directory descriptor. Download
writes only the exact per-account broker scope and exact quarantine ref.
Quarantined bytes are re-opened, bounded, and re-inspected before
materialization or preview.

The boundary rejects `..` traversal, external or device paths, symlinks,
FIFOs, multiple-link files, directory substitution, permissive or foreign
ownership, ambiguous extensions, signature/type mismatches, executable or
script content, and ZIP/RAR/7z/gzip signatures. Rejecting compressed and
archive containers before parsing also denies archive traversal and
decompression bombs. Preview accepts only
`parser-ref:matrix-media:metadata-only-v1`; it returns byte count and media
type refs, never decoded content or an external handler invocation.

Transfers publish content-free progress phases only. Cancellation before
broker send performs no network operation; cancellation after send terminates
the broker process and records `outcome_uncertain` because the server outcome
cannot be inferred. The exact retry policy is manual, same-idempotency only,
and never automatic after uncertainty. Cleanup uses verified directory
descriptors, removes only hash-derived quarantine/materialization names, proves
path absence, and explicitly does not claim physical-block erasure.

## API, CLI, and desktop parity

The protected no-store API exposes one posture route, one validation-only
proposal route, and twenty exact operation routes. Every operation route is
idempotency-gated and classified by its real effect, including destructive
external leave, destructive local cleanup, authenticated connector mutations,
and local-sensitive search/materialization/preview.

`scripts/dev/uaa_communications.py matrix-rooms-media-status`, proposal, and
dispatch commands use the same Core contracts. The macOS Messenger shell reads
the strict content-free posture and labels room/search/media core behavior as
implemented but enrollment-required. Synthetic rooms, messages, search
results, and controls remain presentation fixtures and cannot mint authority.

## Verification truth

Focused contract, authority, replay, redaction, API, CLI, OpenAPI, frontend,
search, index, and hostile-media tests cover all twenty lanes. A disposable
two-user local Synapse drill exercised all sixteen native network lanes,
including membership transitions, power/settings/pin/Space writes, bounded
upload, and authenticated quarantine download. The same drill exercised
materialization, metadata-only preview, cleanup, content-free progress, and
manual/no-automatic-retry posture; encrypted local search is covered by the
dispatcher and adversarial index tests.

The governed harness was stopped and reset after the drill. Final inspection
proved zero containers, networks, volumes, and residual resources; temporary
broker state and Keychain entries were removed. Element Desktop was not used,
so unmodified Element interoperability remains
`external_facility_required` and is not simulated.

Remote homeservers, multi-account product enrollment, calls, autonomous or AI
actions, automatic retry, broad filesystem access, raw-content evidence,
public federation, public distribution, and production authority remain
blocked.
