# UAA Messenger Matrix Threat Model

Status: MSG-MX-001 design threat model accepted; runtime remains unimplemented
and blocked.

## Security objective

Provide a future Matrix client without allowing remote content, credentials,
crypto material, UI state, provider state, evidence, or model output to become
authority. Protect message and attachment confidentiality while retaining exact
request-scoped policy, approval, AuthorityLease, budget, readiness,
safe-disable, idempotency, audit, and content-free receipt boundaries.

## Assets and data planes

Highest-sensitivity source material includes message bodies and relations,
attachments and thumbnails, room/account/device identifiers, search terms and
indexes, drafts/outbox data, access and refresh credentials, crypto-store
material, login passwords, SSO authorization codes, PKCE verifier material,
state/nonce values, cross-signing state, secure-backup state, and recovery
material.

The source plane is separate from the governance plane. Governance data may
contain only opaque safe refs, keyed fingerprints, bounded counts/statuses,
timestamps, policy/approval/lease refs, adapter/target refs, redaction status,
and content-free receipts. Raw source material, local paths, credentials,
provider payloads, logs, usernames, hostnames, device serials, and environment
values are forbidden in receipts, audit, telemetry, errors, fixtures, and
screenshots.

Search indexes inherit the exact account/room/workspace privacy, retention,
key, deletion, and AI-use scope of their sources. Excluded sources must not leak
through results, counts, snippets, or timing where practical.

macOS notifications are a local disclosure boundary. Their default lock-screen
projection contains no message body or participant identity, and exact
account/room exclusions and notification-disclosure policy are applied before
handoff. Body or participant disclosure requires a separately configured exact
policy and fresh request-scoped validation; notification receipts remain
content-free.

## Trust boundaries

1. Matrix homeservers, federation peers, bridges, room members, profile/state
   metadata, links, messages, formatted HTML, relations, receipts, typing,
   device claims, media, and thumbnails are untrusted external input.
2. React is an untrusted presentation boundary for authority and secrets. It
   receives safe projections only and cannot call the Matrix adapter.
3. Python Core is the authority boundary for policy, exact approval validation,
   AuthorityLease, budgets, target binding, kill switch, safe-disable,
   idempotency, receipts, and redaction.
4. The future TypeScript Matrix adapter is a narrow protocol boundary. It may
   transiently hold credentials and decrypted content only for an authorized
   exact operation.
5. macOS Keychain is the device-only credential/key boundary. Protected crypto
   and cache stores are separate encrypted filesystem boundaries.
6. The future loopback Synapse harness is test-only, disposable, bounded, and
   never a production or authority bypass.
7. Any future approved model is an external disclosure boundary. Message
   content is untrusted quoted data, not instruction authority.

End-to-end encryption protects eligible event content; it does not imply
metadata anonymity or universal encryption of membership, timestamps, routing,
state, receipts, typing, thumbnails, or every media path. Runtime encryption
labels must be derived from exact room/event evidence and may not be inferred
from a render, room name, or generic account posture.

## Threat and mitigation register

| Threat ref | Threat | Required mitigation and failure posture | Promotion proof |
|---|---|---|---|
| `threat-ref:matrix:authority-confusion` | UI, message, evidence, approval ref, Full Machine Access, or cached connection state is treated as authority | fresh exact pre-start evaluation of all gates; unknown/stale/mismatched fails closed; no global callable/authorized state | adversarial cross-account/room/event and expired/revoked lease tests |
| `threat-ref:matrix:discovery-ssrf` | malicious discovery, redirect, DNS rebinding, private-network pivot, oversized response | HTTPS except exact loopback harness; endpoint class and origin binding; redirect/DNS revalidation; bounded redirects, time, bytes, and body; private targets denied | hostile discovery/redirect/rebinding tests |
| `threat-ref:matrix:sso-substitution` | callback interception, login CSRF, replay, wrong account, token in URL/log, embedded-webview capture | system browser only; exact allowlisted loopback callback; state, nonce, PKCE, one-use TTL; cross-account and replay denial; no raw-token import | callback replay, mismatch, expiry, and leakage tests |
| `threat-ref:matrix:credential-exposure` | password, SSO secret, or credential reaches React, storage, config, environment, API, log, receipt, backup, or error | native secure-entry helper; authenticated one-use handoff; device-only non-synchronizing Keychain; opaque handle; transient adapter use; independent credential operations; fail closed on missing helper or locked/missing key | plaintext scan, handoff replay, and locked/revoked Keychain tests |
| `threat-ref:matrix:duplicate-client` | multiple windows/processes share one crypto store or repeat unknown-start work | one fenced owner per account/device/store tuple; stale-owner proof; second clients consume projections; unknown terminal start is recovery-required | concurrent owner, crash, restart, and migration fencing tests |
| `threat-ref:matrix:malicious-event` | malformed, deeply nested, cyclic, duplicate, out-of-order, redacted-before-original, forged-state, Unicode/bidi, or oversized event | schema/type/size/depth/count limits; deterministic ordering/dedup; relation-cycle guard; visible bidi posture; state/power validation; safe rejection | hostile event corpus and resource-bound tests |
| `threat-ref:matrix:formatted-content` | HTML/script, dangerous URI, link spoofing, instruction injection | sanitize to an allowlist; deny active content and dangerous schemes; clear external-link boundary; content is quoted untrusted data | sanitizer, URI, bidi, and prompt-injection tests |
| `threat-ref:matrix:receipt-typing-spoof` | forged receipt/typing state implies identity, delivery, approval, or action success | treat as ephemeral untrusted presence; bind exact room/event/user safe refs; never map to authority or terminal send success | spoofed/cross-room receipt and typing tests |
| `threat-ref:matrix:message-replay` | changed target/content reuses transaction, approval, lease, or receipt | bind account, room, event/transaction, content fingerprint, request fingerprint, TTL, and idempotency key; cross-scope replay denied | duplicate/concurrent/changed-content/changed-target tests |
| `threat-ref:matrix:unknown-delivery` | crash after remote start causes duplicate send or false cancellation/success | durable pre-start/start boundary; remote terminal evidence alone marks delivery; unknown remains uncertain/recovery-required; no automatic non-idempotent replay | crash-before/after-start and remote-echo reconciliation tests |
| `threat-ref:matrix:media-hostile` | traversal, symlink/FIFO/device, MIME polyglot, archive bomb, parser exploit, auto-download, residue | no auto-download/preview; exact byte/type/time budgets; quarantine; generated filename; descriptor-safe paths; isolated parsing; explicit cleanup proof | hostile file/type/archive/path and residue tests |
| `threat-ref:matrix:cache-leak` | plaintext database, index, WAL, journal, temp, backup, draft, or outbox | separate encrypted stores/keys; temp in memory where possible; integrity/schema/key-version checks; locked failure; bounded retention | plaintext scans, corruption, key-loss, backup/restore tests |
| `threat-ref:matrix:cross-room-context` | excluded or wrong-room content reaches AI, action, or memory | exact room/event-range/purpose/model-destination context grant; short expiry; byte/token budget; exclusions and citations; content-free manifest/receipt | exclusion, expiry, cross-room, and prompt-injection tests |
| `threat-ref:matrix:model-authority` | fetched message instruction or model output sends, mutates, grants tools, or becomes Memory truth | quoted-data boundary; output is proposal/evidence only; separate exact action approval and lease; memory candidate remains review-only | injection-shaped content cannot invoke actions or memory writes |
| `threat-ref:matrix:verification-downgrade` | key substitution, stale trust, SAS/QR confusion, cross-signing downgrade | exact device/identity binding, fresh trust state, explicit human ceremony, downgrade warning, no verification inference from event text | substitution, stale, replay, and user-cancel tests |
| `threat-ref:matrix:backup-rollback` | stale backup, wrong account/store, recovery replay, key loss | fingerprinted backup metadata, account/device/store binding, monotonic version posture, staged integrity verify, explicit lost-key state | stale/wrong-scope/corrupt/lost-key restore tests |
| `threat-ref:matrix:identity-reset` | destructive reset is disguised as recovery or rollback | separate destructive capability, exact confirmation, irreversibility warning, no claim of data recovery, content-free terminal receipt | denial, expiry, mismatch, and consequence-review tests |
| `threat-ref:matrix:deletion-overclaim` | remote redaction is called local deletion or backup residue is ignored | exact local purge of source/index/cache/draft/outbox; content-free tombstone; backup-expiry-pending state; remote action is distinct | scope, restart, index, backup-expiry, and residual plaintext tests |
| `threat-ref:matrix:log-evidence-leak` | exception, telemetry, receipt, notification, lock-screen projection, screenshot, fixture, or diagnostic captures sensitive material | structured allowlisted fields; safe refs/keyed fingerprints; bounded summaries; response-body/log tracing disabled; lock-screen notifications omit body and participant identity by default; exact account/room exclusions; redaction verifier | secret/path/content/notification corpus and screenshot/fixture scans |
| `threat-ref:matrix:safe-disable-gap` | reconnect, sync, retry, queue, or new command starts after kill/safe-disable | re-check inside atomic pre-start boundary; stop new claims/reconnects; close transient session and lock stores; no silent delete/revoke | kill/safe-disable race and queued-operation tests |
| `threat-ref:matrix:resource-exhaustion` | sync flood, large room, media storm, relation fan-out, rate limit | bounded pages/events/relations/media/output; backpressure; operation/time/byte/concurrency budgets; explicit degraded/blocked state | large-room/flood/rate-limit/timing tests |
| `threat-ref:matrix:harness-escape` | local Synapse test lane exposes network, persists data, or becomes production | loopback-only, no federation, disposable credentials/data, bounded lifetime, pinned dependency, complete cleanup, explicit test-only gate | hostile lifecycle, port, residue, and cleanup tests |

## Mutation and rollback truth

All external Matrix operations are externally compensating, not local atomic
transactions. Local drafts/cache/outbox data may support exact-scope deletion or
restore. A message send, edit, redaction, invitation, membership change, room
setting, verification, recovery, or call cannot be labeled reverted without
remote terminal evidence. Compensation is a new exact governed operation with
its own approval, lease, idempotency, budget, and receipt.

Success is derived only from adapter terminal evidence. Pending, failed,
uncertain, recovery-required, partially complete, and dependency-blocked states
remain distinct. Retry is default-denied for unknown execution truth and for
non-idempotent work without exact replay proof.

## Deny floor

MSG-MX-001 grants no runtime lane. Calls, agent room participants, autonomous
sends, hidden context injection, automatic Memory writes/truth, public
federation or hosting, broad connector authority, public release, production
authority, mobile implementation, and arbitrary browser/shell/provider work
remain denied.
