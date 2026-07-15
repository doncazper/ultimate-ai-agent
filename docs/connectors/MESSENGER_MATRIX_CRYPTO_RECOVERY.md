# Messenger Matrix Crypto, Verification, Backup, And Recovery

Status: MSG-MX-007 accepts seventeen exact request-scoped authority lanes and
implements content-free proposal/readiness surfaces. The persistent crypto
executor is `adapter_required`; no device trust, key, backup, restore, or
identity mutation is callable.

## Exact Authority Boundary

Python Core defines separate lanes for crypto-store initialization, store-key
rotation/deletion, verification request/cancel/confirm, device revocation,
cross-signing bootstrap, backup status/configuration/rotation, recovery
restore, identity reset, and local backup create/restore/delete/expiry
reconciliation. Every command binds the exact account, local and peer devices,
store schema and generation, crypto-key item and version, verification
transaction/method/generation, transcript hash when confirming, cross-signing
generation, backup versions and integrity, dedicated backup-key refs, staged
restore target, recovery attempt, consequence review when resetting, deadline,
zero-cost budget, kill switch, safe-disable, readiness, rollback, lease,
idempotency, and complete request fingerprint.

Rollback posture is backend-owned, not caller-described. Destructive
operations receive an exact `irreversibility-ref`; every other operation
receives its operation-specific `rollback-readiness-ref`. A mismatched label is
rejected before authority evaluation, so identity reset, device revocation,
and deletion cannot be presented as reversible.

Mutation proposals require fresh exact `LocalApprovalAuthority` validation and
a short session-scoped `AuthorityLease`. Destructive operations use the
destructive capability and Full Machine Access mode, but that mode does not
make any lane callable. The read-only backup-status lane still requires an
exact current lease. Approval refs are identifiers only. Every authority action
is marked `unsupported_adapter=true` until the persistent broker is proven.

## Proven Runtime Limitation

The pinned `matrix-js-sdk` uses the Rust crypto implementation. In a browser,
durable Rust crypto requires IndexedDB. The currently approved Matrix adapter
is a bounded one-shot Node subprocess where IndexedDB is unavailable; the SDK's
Node posture is therefore ephemeral and would create a new device on restart.
Ephemeral crypto cannot satisfy UAA's persistent-store, singleton-owner,
restart, verification, backup, or recovery requirements.

UAA does not substitute an in-memory shim, serialize ephemeral state, export
room keys as a pseudo-store, or claim that fixture crypto is persistent. A live
executor requires a separate threat-reviewed persistent host with:

- an authenticated one-use session broker;
- one fenced, singleton crypto owner;
- a durable Rust-crypto store;
- a device-only macOS Keychain database key with versioned rotation;
- a distinct backup wrapping key and protected recovery ceremony;
- bounded content-free IPC and receipts;
- staged restore, rollback/irreversibility truth, kill switch, and safe-disable;
- restart, corruption, key-loss, downgrade, replay, and escape tests.

Element Desktop verification plus reinstall-and-restore proof remains
`external_facility_required`. No product claim treats that missing manual proof
as successful interoperability.

## Operator Truth

`GET /control-center/communications/matrix-crypto/posture` and
`uaa_communications.py matrix-crypto-status` expose the same backend-owned
content-free posture. `POST /control-center/communications/matrix-crypto/proposal`
and `uaa_communications.py matrix-crypto propose ...` validate one complete
fingerprinted request and return a non-executing proposal. The macOS Messenger
Sessions & Recovery surface shows accepted lane count, live executor count,
blocked operations, recovery posture, and the external interoperability gate.
React does not own or mint that truth.

No route or CLI returns seed phrases, recovery keys, private keys, store keys,
backup keys, crypto payloads, raw provider responses, message content, local
paths, usernames, hostnames, or credentials. Recovery material is structurally
absent from every public contract and content-free receipt plan.

## Remaining Deny Floor

Live encrypted-event materialization, device verification, cross-signing,
backup changes, restore, identity reset, Matrix sends, room mutations, media,
browser automation, hidden context injection, automatic Memory writes, public
release, and production authority remain blocked. Inspectable and
exact-authority-scoped never mean callable.
