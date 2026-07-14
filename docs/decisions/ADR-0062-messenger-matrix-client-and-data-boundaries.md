# ADR-0062: Messenger Matrix Client, Clean-Room, And Data Boundaries

Status: accepted design for MSG-MX-001; no runtime authority or implementation.

## Context

UAA intends to provide a macOS-first Messenger workspace that interoperates
with Matrix and remains useful without AI assistance. The repository currently
has no Matrix SDK, homeserver connection, account session, sync loop, crypto
store, protected message cache, or Matrix-backed route. The fifteen
`communications-v1` images are target renders, not runtime evidence.

Element is an interoperability and behavioral reference. Its source, styles,
components, assets, branding, identifiers, and product copy are outside UAA's
implementation boundary.

## Decision

### Clean-room and license posture

UAA will implement original product, Python, TypeScript, CSS, fixture, and test
code against the public Matrix protocol and the public `matrix-js-sdk` API.
UAA will not fork, embed, reskin, transpile, translate, or transplant Element.
No Element source or build artifact may become an implementation input.

`matrix-js-sdk` is the selected future client library because it exposes the
current Matrix client surface and Rust-crypto integration needed by the plan.
This ADR does not install it or accept a package version. The dependency phase
must pin one exact release, verify its published license and transitive license
inventory, record its integrity value, generate the required dependency notice,
and pass repository supply-chain checks before use. A license, integrity, or
compatibility unknown fails closed.

Element Desktop may be used only as an independently installed
interoperability peer. Interoperability observations use content-free safe refs;
screenshots, logs, account identifiers, room identifiers, and message material
are not retained as evidence.

### Authority and process boundary

Python Core remains authoritative. A future `CommunicationsService` owns
normalized contracts, account and room posture, PolicyEngine evaluation, exact
LocalApprovalAuthority validation, AuthorityLease evaluation, budgets,
safe-disable, idempotency, receipts, audit, and redaction. React owns only
selection, disclosure, filters, draft text before handoff, and presentation.

The future TypeScript Matrix adapter owns protocol mechanics: discovery,
authentication exchange, sync, pagination, relations, local echo, retry,
media transport, and Rust-crypto calls. React cannot import the Matrix SDK,
receive credentials or recovery material, or invoke the adapter directly. Only
safe normalized projections and exact command envelopes may cross the
Python/API/TypeScript boundary.

The adapter has one injected entry point behind dispatcher-controlled,
authenticated local IPC. Static import guards deny Matrix SDK or adapter imports
from React and every TypeScript module outside the approved adapter package. The
entry point rejects an envelope unless it is bound to the current Python
request-scoped decision fingerprint; UI-supplied refs cannot satisfy that
binding.

Every future adapter call, including reconnect, sync, and retry, must
re-evaluate the current exact request immediately before start: policy; exact
approval scope when required; active AuthorityLease; capability, adapter,
provider, account, device, room, event, media, mission, run, and target; TTL and
deadline; operation, time, byte, cost, and concurrency budgets; compatibility,
configuration, health, freshness, and readiness; kill switch; safe-disable; and
idempotency, replay, and prior-start posture. No cached `connected`, `enabled`,
`authorized`, or `callable` state may grant authority. Approval refs are
identifiers only.

Operator-requested deletion, revocation, and remote cleanup remain exact
governed operations. Non-network cleanup of transient passwords, partial
credentials, parser output, incomplete bytes, and other operation-local residue
is different: failure and `finally` paths always attempt that bounded cleanup.
Lease revocation, kill switch, or safe-disable cannot prevent it, and cleanup
does not mint authority for another adapter or network start.

### Singleton client and crypto ownership

There is at most one live Matrix client for one exact
`account_ref` + `device_ref` + `crypto_store_ref` tuple. A future session
coordinator must provide atomic ownership, a fencing generation, bounded
heartbeat/liveness evidence, stale-owner recovery, graceful shutdown, and
exclusive migration/rekey ownership. A second window consumes projections from
the owner; it does not create another client. A durable start with unknown
terminal truth never permits duplicate session creation or message delivery.

The Matrix adapter uses the current Rust crypto API exposed by the selected SDK.
The legacy crypto API is rejected. Crypto implementation remains blocked until
MSG-MX-007 proves store isolation, verification, backup, recovery, corruption,
lost-key, restart, and migration behavior.

### Credential, crypto-store, cache, and backup separation

The first supported credential backend is device-only, non-synchronizing macOS
Keychain. Password authentication uses a future native macOS secure-entry helper
invoked by Python Core; password bytes cross one authenticated local handoff to
the adapter, remain transient for one exact login attempt, and are then zeroed
on a best-effort basis. The password never enters React or durable state. Until
that helper and handoff are implemented and tested, password login remains
blocked. SSO authorization codes, PKCE verifier material, state, and nonce are
likewise transient and excluded from durable state.

Access and refresh credentials exist only in the Keychain boundary and
transient adapter memory for the exact operation. They never enter React,
IndexedDB, local storage, configuration, environment values, API payloads,
receipts, logs, telemetry, tests, screenshots, or backups. Raw credential import
is rejected.

The crypto-store encryption key and protected conversation-cache key are
separate random keys stored behind separate Keychain item refs. Pending drafts
and outbox state use a third dedicated key item, and eligible local backups use
a fourth dedicated backup-wrapping key item; neither reuses a live crypto-store
or conversation-cache key. Each key has its own version ref, owning data-plane
ref, rotation generation, revocation posture, and loss state. The crypto store,
normalized message/search cache, draft/outbox store, and backup store are
separate encrypted data planes with separate schema versions and migrations.
Their database pages, indexes, WAL, journals, temporary data, drafts, outbox
state, and eligible backups must be encrypted. Operational receipts, metrics,
and audit are a separate content-free governance plane.

A future adapter may materialize a credential transiently only after Python Core
authorizes the exact credential operation and returns an opaque, short-lived
handle. React, CLI, and public API surfaces receive safe refs and posture only.
Key lookup failure, locked Keychain, unsupported key/schema version, corruption,
interrupted migration, or mismatched account/device/store binding fails closed.

Local encrypted backups exclude access credentials and recovery material. A
backup records exact store/schema/source-key-version/backup-key-version refs and
an integrity fingerprint. The dedicated backup-wrapping key rotates separately;
prior wrapped generations remain readable only for their bounded retention
window. Loss or revocation of that key produces an explicit unrecoverable-backup
posture and never silently generates a replacement that claims old backups are
restorable. Restore runs in a new bounded staging store, verifies integrity and
binding, then performs an atomic local replacement. Draft/outbox key loss locks
that store and makes its encrypted records explicitly unrecoverable; it cannot
fall back to a cache or credential key. Server-side Matrix secure backup is a
distinct crypto operation and never implies a local data backup succeeded.

### Migration, deletion, recovery, and safe-disable

Migrations are versioned, idempotent, resumable, integrity-checked, and bound to
one fenced store owner. The pre-migration encrypted store remains available for
rollback until the new store verifies. Failed migration locks the store and
produces content-free failure evidence; it never silently creates a fresh empty
identity.

Deletion is exact-scoped by account, room, event projection, draft, outbox,
cache, search index, or store. It removes matching live local material and
creates a content-free tombstone/receipt. UAA must not claim complete deletion
while an eligible encrypted backup remains. Remote redaction and local deletion
are distinct operations. Credential revocation, store deletion, identity reset,
and recovery-material destruction are separate destructive commands.

Recovery material is shown only in a one-time protected flow. It is excluded
from durable screenshots, clipboard persistence, analytics, receipts, logs,
fixtures, and API/CLI output. Identity reset requires a separate exact
confirmation and an irreversibility warning; it cannot be described as rollback.

Safe-disable blocks new operations, reconnect, and background sync before start,
closes transient sessions, and locks protected stores. It does not silently
revoke credentials, delete data, reset identity, or claim that an already-started
external operation was cancelled. It also cannot suppress the unconditional
non-network failure-path residue cleanup defined above.

## Rejected alternatives

- Embedding, white-labeling, forking, or copying Element.
- React-owned message truth, credentials, crypto, authority, or receipts.
- Multiple SDK clients sharing one account/device/crypto store.
- Raw token import, URL query credentials, environment-backed credentials, or
  credential material in browser storage.
- One shared key for credentials, crypto, cache, drafts, and backups.
- Treating Matrix events, model output, message content, UI state, or approval
  identifiers as authority.
- Treating external sends, redactions, invitations, room changes, or calls as
  locally atomic or universally reversible.

## Consequences

MSG-MX-001 accepts an architecture and clean-room boundary only. It adds no
dependency, route, SDK, process, credential access, store, network call,
message read, message write, call, public release, or production authority.
Later phases must implement and prove each exact lane independently under the
authority matrix and threat model.
