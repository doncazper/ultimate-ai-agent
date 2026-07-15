# Messenger Matrix Read-Only Sync And Protected Cache

Status: MSG-MX-006 declares twelve exact backend authority lanes. Two GET
transports and protected-cache/key primitives are loopback-tested; ten exact
dispatch executors remain uncomposed and fail closed. Live account sync remains
`configuration_required`.

## Exact Runtime Boundary

Python Core declares twelve request-scoped lanes: initial/incremental sync,
timeline pagination, room-state read, local typing and receipt projection,
protected-cache read/write/migrate/purge, and cache-key create/rotate/delete.
Every lane binds the exact account, room set, event classes, homeserver,
adapter, credential generation, cache schema and generation, key item/version,
retention, backup exclusion, deadline, zero-cost budget, readiness, kill switch,
safe-disable, idempotency, and rollback posture. Reads require a current exact
session lease. Cache and key mutations also require a fresh exact
`LocalApprovalAuthority` validation. Approval refs alone grant nothing.

Only `sync_read` and `timeline_paginate_read` have concrete dispatch/transport
composition in this milestone. Room-state/projection and protected-cache/key
authority contracts remain non-callable through the dispatcher until their
canonical executors are composed. The cache and Keychain primitives are real
and directly tested, but primitive availability is not invocation authority.

The Node adapter permits only bounded authenticated `GET` sync and backwards
room-timeline pagination. A one-use credential crosses an inherited anonymous
file descriptor and is never placed in JSON, argv, or the environment. Raw
provider responses exist only in a bounded one-use transient registry. The
runner, imported adapter tree, package lock, and Rust/WASM dependency are bound
to the canonical runtime-integrity manifest.

## Protected Cache

The desktop cache is one whole-file encrypted container. Its normalized private
state includes message bodies and safe projections, so every byte after the
fixed non-sensitive container marker is AES-256-GCM ciphertext. There is no
SQLite database, WAL, journal, query temp file, or backup. Writes use private
O_EXCL/no-follow staging, fsync, atomic replacement, bounded size, account and
key-version AAD, exact generation replay checks, and substitution denial.

The macOS helper creates a random 256-bit key in the device-only Keychain and
performs AES-GCM operations without returning key material. The Python backend
hash-validates and privately copies the helper before each bounded invocation.
The helper compiles and its deterministic protocol is tested. This machine's
real Keychain lifecycle drill returned `MATRIX_CACHE_HELPER_KEYCHAIN_LOCKED`, so
the product does not claim an unlocked or configured protected cache.

## Normalization And Trust

Room, event, participant, media, sync-token, and Space identifiers are
HMAC-pseudonymized before cache storage. The normalizer covers membership,
invites/leaves, DMs, Space parents, names/topics/avatar refs, unread/highlight
counts, local notification decisions, typing and receipt projections, messages,
replies, edits, redactions, reactions, polls, file metadata, thread summaries,
and encrypted placeholders. Ordering and deduplication are deterministic;
cross-room scope, relation cycles/depth, conflicting duplicates, oversized
responses, schema downgrade, key loss, locked Keychain, and path substitution
fail closed.

All content is `content_untrusted=true` and
`not_instruction_authority=true`. It cannot grant authority, trigger tools,
write Memory, or become hidden model context. Encrypted event materialization
remains disabled until MSG-MX-007.

## Operator Truth

`GET /control-center/communications/matrix-sync/posture` and
`uaa_communications.py matrix-sync-status` expose the same content-free
backend truth. The macOS Messenger shell displays that posture while its room
and message content remains explicitly synthetic fixture data. No protected
message-content API is exposed before account enrollment, one-use credential
broker configuration, and a usable Keychain helper are proven.

Message sends, typing/receipt writes, room mutations, media transfer, browser
automation, connector writes, automatic Memory writes, public release, and
production authority remain blocked.
