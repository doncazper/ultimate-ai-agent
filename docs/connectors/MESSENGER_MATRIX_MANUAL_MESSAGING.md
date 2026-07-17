# Messenger Matrix Manual Messaging

Status: MSG-MX-008 implements fifteen exact request-scoped manual-messaging,
encrypted-outbox, and generic desktop-notification operations. The default
product posture remains `configuration_required`: the native artifact, an
unlocked non-synchronizing macOS login Keychain, an exact account session, and
fresh command-scoped authority must all be enrolled before any operation can
start. Remote homeservers and autonomous or AI-generated sends remain denied.

## Exact Authority Boundary

Python Core owns separate operations for send, reply, thread, reaction, edit,
redaction, typing, read receipt, draft write/read, outbox enqueue/read/transition/
discard, and generic desktop notification. Every operation is bound to its
exact account, loopback homeserver, device, room, event when applicable,
stable transaction, keyed content fingerprint, encrypted outbox record and
generation, notification policy/target/disclosure generation, adapter,
deadline, zero-cost budget, readiness, kill switch, safe-disable,
idempotency, and compensation or rollback-readiness ref.

Every operation requires a fresh exact `LocalApprovalAuthority` decision and
current session-scoped `AuthorityLease`. Approval refs are identifiers only.
The dispatcher rechecks policy, approval scope, lease, cost, deadline, adapter
binding, readiness, target, kill switch, safe-disable, and replay posture
immediately before its atomic start. Stable approval actor timestamps make an
identical terminal retry replay the prior receipt; a changed content, room,
event, transaction, or authority field conflicts instead of executing.

## Native Broker And Secret Boundary

`integrations/matrix-rust-broker` pins Rust 1.93.0 and `matrix-sdk` 0.18.0 to
the reviewed upstream source commit recorded in `runtime-integrity.json`.
Python opens and hashes the enrolled executable, copies the verified bytes to
a private one-use directory, starts one process group, and passes a random IPC
authentication key plus the private state root over inherited anonymous file
descriptors. The broker binds a random IPv4 loopback port, accepts one request,
HMAC-authenticates the bounded frame and response, validates operation-specific
secret/target scope, and exits. Python rejects a response unless operation,
request, complete fingerprint, and transaction match the initiating command.

The broker accepts only `localhost`, `127.0.0.1`, or `::1` homeservers in this
milestone. Matrix session material and the encrypted SQLite crypto-store key
use standard non-synchronizing macOS Keychain items; the SDK store and content-
free replay ledgers are private, singleton-locked, bounded, and substitution-
checked. Native failures return safe codes only. Raw credentials, session JSON,
store keys, room/event identifiers, message bodies, and provider payloads are
not written to receipts or logs.

## Encrypted Draft And Outbox Truth

Drafts and pending messages use a distinct TTL-bounded encrypted store and a
dedicated protected-cache Keychain item. Authenticated encryption binds the
account, room, outbox ref, schema, and key version. State transitions are
compare-and-swap operations under a process lock and require the exact current
record generation. Fresh writes cannot overwrite an existing record.

The state machine covers `draft`, `queued` (the local echo), `sending`,
`server_acknowledged`, `remote_echo`, `failed`, `outcome_uncertain`, and
`discarded`. Failed records may be explicitly requeued. An uncertain result
cannot return to queued: reconciliation must prove the prior transaction's
truth or the operator may discard it. The same transaction and complete
request fingerprint drive both Python and native replay ledgers, preventing an
automatic duplicate send after restart.

Message bodies, formatted bodies, mentions, reaction keys, raw room/event IDs,
usernames, passwords, and homeserver URLs remain transient inputs. Durable
outbox files are bounded encrypted containers. Plaintext scanning uses private
directory descriptors, no-follow opens, and bounded reads. Receipts contain
only safe refs, state, fingerprints, and explicit uncertainty.

## API, CLI, And Desktop Truth

The protected no-store API exposes one posture route, one validation-only
proposal route, and fifteen operation-specific POST routes. Every operation
route has a stable unique OpenAPI operation ID, exact side-effect class,
authority-required classification, idempotency-header binding, and redacted
failure envelope. The default handler deliberately binds a blocked runtime; it
cannot turn a caller-supplied confirmation or approval ref into execution.

`scripts/dev/uaa_communications.py matrix-messaging-status` exposes the same
backend posture. `matrix-messaging propose --command-file ...` validates one
safe-ref-only command without mutation. `matrix-messaging dispatch` runs the
same Core authority/receipt path but remains configuration-blocked until an
enrolled runtime is composed. The existing communications receipt inspection
surface remains content-free.

The macOS Messenger shell loads the strict posture contract. Synthetic room
content remains clearly labeled and is never treated as an exact authorized
target. The human composer stays separate from UAA proposal UI and disabled
for the synthetic fixture. Existing deterministic variants show local echo,
queued, failed, retry-preview, edited, redacted, offline, reconnecting, and
rate-limited truth without claiming a send or connection.

## Verification And Remaining Deny Floor

A disposable two-user local Synapse drill proved session login, fresh-process
session restore, Keychain-backed encrypted outbox persistence, plaintext
absence, server-acknowledged encrypted send/reply/thread/reaction/edit/
redaction, typing and read-receipt writes, remote-echo transition, terminal
duplicate replay, and a second client observing an `m.room.encrypted` event.
The drill also caught and fixed operation-field smuggling in reaction/redaction
frames and remote-event loss during acknowledgement-to-echo transition. The
harness was stopped and reset through its exact governed lanes; zero containers,
temporary Keychains, and disposable state remained. Element Desktop was not
installed, so unmodified Element interoperability remains
`external_facility_required` and is not simulated.

Remote/federated homeservers, account enrollment UI, background queue workers,
automatic retry, AI sending, room administration, search, media, calls, public
hosting, public distribution, and production authority remain blocked. An
implemented executor is not a callable default and does not grant standing
Matrix, network, connector, filesystem, browser, or shell authority.

Canonical verifier:
`scripts/verify_msg_mx_008_manual_messaging.py`.
