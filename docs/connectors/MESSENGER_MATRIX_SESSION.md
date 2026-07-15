# Messenger Matrix Discovery And Session Boundary

Status: MSG-MX-005 partial runtime implementation. Two exact read lanes are
implemented; eight credential, browser, account, and session mutations remain
blocked.

## Implemented Boundary

The pinned adapter uses `matrix-js-sdk` `41.9.0` and the locked Rust/WASM
dependency `18.3.1` inside `integrations/matrix-client-adapter` only. Python
Core remains authority. Every call enters `AuthorityDispatcher` and rechecks
the exact current policy, session-scoped AuthorityLease, target, deadline,
budget, readiness, kill switch, safe-disable, and replay posture immediately
before start.

- Implemented: discovery reads only `/.well-known/matrix/client`. It validates
  the delegated homeserver syntax without probing that second target and emits
  a content-free, ten-minute discovery observation.
- Implemented: authentication-method inspection uses a separate exact target
  lease and the current discovery observation. It permits only versions,
  legacy login-flow, and same-homeserver stable or unstable authentication
  metadata reads. Metadata is locally schema-checked; issuer and signing-key
  discovery are not performed.

Discovery evidence is stored as safe refs in a bounded, locked, no-follow
ledger. The next lane must match the observed target and freshness ref. Missing,
forged, corrupt, stale, or cross-target observations fail closed.

## Blocked Session Mutations

The following exact lanes are declared and AuthorityLease-eligible for future
request-scoped evaluation, but both Python and the Node adapter block them
before credentials or an SDK mutation can enter the process:

- credential authentication and account/session creation;
- system-browser SSO launch and callback consumption;
- refresh, logout, and revoke-all;
- credential-store rotation and credential deletion.

Credential-bearing calls require an authenticated one-use handoff. Browser SSO
requires a socket-owning SSO broker that binds callback state, loopback port,
redirect target, expiry, and one-use consumption. The native macOS helper is
version-only and imports no Keychain API. Approval refs identify records only
and cannot authorize these operations.

There is no sync, room read, message send, crypto, or media runtime in this
milestone. Messenger remains a desktop fixture surface and is not connected to
these backend read lanes.

## Network And Data Safety

The Node transport pins a validated address, denies redirects, rejects private
and metadata targets, bounds time and response size, and enforces exact
operation-specific GET path allowlists. It cannot call sync, room, message,
media, issuer-discovery, or mutation endpoints. Raw URLs are transient; raw
provider payloads, credentials, local paths, logs, and environment values never
enter receipts or the observation ledger.

The adapter lockfile, dependency licenses, runner modules, and required WASM
asset are covered by the runtime-integrity manifest and SBOM checks. Missing or
changed assets fail readiness and are revalidated inside the locked pre-start
boundary. Rollback means safe-disabling the adapter and restoring/removing the
exact package lock as one reviewed dependency change; the two read lanes have
no remote rollback action, while blocked mutations expose rollback-readiness
refs only.

## Operator Surfaces

Ten protected, rate-limited POST routes and the human-readable
`uaa_communications.py matrix-session` command use the same Python contracts.
The two read operations may execute only with exact current leases; the eight
mutation routes return truthful blocked receipts. `/api/manifest` remains
declaration metadata, not live health or global authorization.
