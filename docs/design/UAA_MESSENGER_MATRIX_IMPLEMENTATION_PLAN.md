# UAA Messenger Matrix End-to-End Implementation Plan

Status: MSG-MX-000 through MSG-MX-004 accepted; MSG-MX-005 implements exact
discovery and authentication-method read lanes while all credential, browser,
account, and session mutations remain blocked pending their authenticated
handoff or broker boundary.
Current as of: 2026-07-14.
Product surface: Messenger, separate from Communications.
Design contract: `control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md`.

## Outcome

Build a clean-room, Element-familiar Matrix client that is genuinely useful
without AI and materially better with governed UAA assistance. A friend using
Element must be able to exchange encrypted messages with a user operating only
through UAA Messenger.

Communications remains the existing unified email, message-source, draft,
follow-up, and waiting-on-others hub. Messenger is a new primary tab and an
immersive shell exception like Studio.

## Current Repository Truth

The repository pins `matrix-js-sdk` inside one approved adapter and implements
two exact AuthorityLease-governed read lanes: homeserver discovery and
authentication-method inspection. A successful discovery creates bounded,
content-free freshness evidence before the separately leased homeserver target
can be inspected. The repository still has no authenticated Matrix account or
session, sync loop, crypto store, Matrix room model, or Matrix-backed UI. The
MSG-MX-004 loopback Synapse harness remains development infrastructure, not a
product connector. The Messages Connector contracts and disabled Mattermost
bridge do not provide Matrix support.

## Product Decisions

1. **Client, not embedded Element.** Build original UAA code. Do not fork,
   embed, reskin, or transplant Element Web. Element is a behavioral and visual
   reference and an interoperability test client.
2. **Matrix is the first provider behind a UAA contract.** Matrix-specific
   event and room concepts stay inside the adapter. UAA surfaces consume
   normalized conversations, events, members, attachments, and capabilities.
3. **Bring-your-own homeserver first.** UAA connects to an existing account.
   Bundled production homeserver deployment is a separate infrastructure
   product decision.
4. **Local Synapse for deterministic development.** Use the official Synapse
   container locally with SQLite only for tests. Production self-hosting, if
   later selected, requires PostgreSQL, HTTPS, backups, abuse controls, and a
   separate federation review.
5. **One Matrix client per account/crypto store.** The SDK warns that multiple
   clients sharing one IndexedDB crypto store can corrupt data and break
   decryption. A singleton session coordinator owns lifecycle and locking.
6. **Rust crypto through `matrix-js-sdk`.** The JavaScript SDK uses the Rust
   crypto WebAssembly bindings and exposes the current `CryptoApi`. Do not use
   the legacy crypto API.
7. **Two Spaces are presentation plus optional Matrix mapping.** Home / All
   Messages is an aggregate, not a Space. Founder HQ and Personal Circle begin
   as local presentation mappings to existing rooms. Creating or changing
   server-side Matrix Spaces requires a separate reviewed write.
8. **Human send and AI send are different authority lanes.** A person pressing
   Send is an exact manual command and produces a receipt. A UAA-generated
   message remains a draft until the operator reviews the exact destination and
   content. Autonomous send is Never in the first useful release.
9. **No message content in operational evidence.** Receipts use room/event safe
   refs, timestamps, outcome, adapter, and redacted summaries. Tokens, recovery
   material, raw messages, attachments, and decrypted payloads never enter
   logs, analytics, evidence exports, or unrelated memory.

## Target Architecture

```text
Messenger React surfaces
        │ normalized projections and exact commands
        ▼
Python CommunicationsService / API / CLI
        │ policy, approval, receipts, redaction, UAA context grants
        ▼
MatrixAdapter boundary
        │ one singleton matrix-js-sdk client per account/crypto store
        ▼
Matrix Client-Server API / homeserver
```

### Ownership

- Python Core owns account posture, capability discovery results, normalized
  records, room AI policy, action intents, exact approvals, receipts, audit,
  safe refs, redaction, and CLI inspection.
- The Matrix adapter owns discovery, authentication protocol, sync, pagination,
  event relations, local echo, retry, media transport, and encryption mechanics.
- React owns selection, disclosure, draft text, pane state, filters, and
  presentation. It does not own durable message truth or execution authority.
- UAA intelligence receives decrypted content only through a time-bounded,
  room-scoped context grant. It does not automatically write Memory.

### Proposed Contracts

```ts
interface CommunicationsProvider {
  discoverServer(input: ServerDiscoveryInput): Promise<ServerCapabilities>;
  connect(input: ApprovedSessionIntent): Promise<SessionReceipt>;
  listConversations(query: ConversationQuery): Promise<ConversationPage>;
  getTimeline(query: TimelineQuery): Promise<TimelinePage>;
  subscribe(listener: CommunicationsEventListener): Unsubscribe;
  proposeSend(input: MessageDraft): Promise<ActionEnvelope>;
  executeApprovedSend(input: ApprovedSendIntent): Promise<SendReceipt>;
  search(query: MessageSearchQuery): Promise<SearchPage>;
  inspectSecurity(): Promise<SecurityPosture>;
}
```

The concrete adapter is not exported to UI components. Static guards allow the
Matrix SDK import only in the approved adapter package.

## Delivery Sequence

### Phase 0 — Design, ADR, and threat model

Deliver:

- approve the 15 Messenger renders and shell exception;
- architecture decision record for `matrix-js-sdk`, singleton ownership,
  credential storage, crypto store, local cache, and Python/TypeScript boundary;
- clean-room implementation and license review;
- message/attachment/token/key/log/memory threat model;
- exact capability and authority matrix for discovery, login, sync, receipts,
  typing, send, edit, redact, reaction, media, room, invite, settings, and call.

Exit gate: reviewers can identify the owner, side effects, approval posture,
rollback/safe-disable behavior, and evidence contract for every lane.

### Phase 1 — Static shell and normalized fixture model

Implementation status: complete in MSG-MX-002 as a desktop-only synthetic
fixture surface. This status is presentation evidence only and grants no Matrix
runtime, connector, credential, network, read, write, crypto, media, or call
authority.

Deliver:

- new Messenger route and primary rail entry after Communications;
- immersive white Messenger rail with Back to Control Center;
- Home, Founder HQ, Personal Circle, room list, DM list, timeline, composers,
  inspectors, settings, security, setup, recovery, and dark appearance;
- typed fixture projections for all 15 renders and their empty/loading/error
  variations;
- no Matrix dependency and no network calls.

Exit gate: all fixture surfaces match approved renders at normal and narrower
desktop widths; every visible command is labeled Preview, Planned, or Blocked.

### Phase 2 — Python contracts, API, CLI, and adapter skeleton

Implementation status: complete in MSG-MX-003 as backend-owned normalized
contracts and protected read-only inspection only. The Matrix adapter is an
inspection-only disabled shell with catalog unsupported, compatibility and
health unknown, configuration not configured, authority blocked, budget and
safe-disable unknown, and derived readiness unknown. The six communications
GET routes and repo-local CLI expose the same safe-ref truth; TypeScript
bindings validate it but the fixture Messenger UI remains intentionally
disconnected. No SDK, network, account, authentication, sync/read, send/write,
crypto, media, raw-content persistence, or runtime authority is added.

Deliver:

- Python `CommunicationsService`, provider registry, normalized models, safe-ref
  factory, redaction, receipts, action envelopes, and room AI policy;
- OpenAPI/API manifest routes for read posture and exact proposals;
- CLI commands for server capability inspection, session posture, room list,
  failed sends, security posture, and receipt lookup;
- TypeScript client bindings generated or checked against OpenAPI;
- disabled Matrix adapter shell with no SDK and no network authority.

Exit gate: contract tests prove UI/API/CLI parity and Foundation Gate rejects
unclassified Matrix routes or raw-content evidence.

### Phase 3 — Local Matrix development harness

Implementation status: the six exact `matrix.harness.inspect`,
`matrix.harness.smoke`, `matrix.harness.start`,
`matrix.harness.fixture_seed`, `matrix.harness.stop`, and
`matrix.harness.reset` lanes are implemented through Python Core, dispatcher,
protected API, human-readable CLI, and digest-pinned local packaging. Live
lifecycle proof is recorded only when the exact image is pre-provisioned and
the bounded drill actually runs. This remains development infrastructure and
does not make Messenger usable or connected.

Deliver:

- opt-in repo-local Synapse test harness using the official image, loopback
  only, disposable data, closed registration, bounded lifetime, and no
  federation;
- deterministic test accounts, rooms, Spaces, messages, threads, reactions,
  media metadata, and encryption fixtures created outside durable repo files;
- Element Desktop interoperability checklist;
- local start/stop/reset scripts and explicit no-production warning.

Exit gate: the harness can be recreated locally and leaves no credentials,
message content, containers, or volumes after the documented cleanup command.

### Phase 4 — Server discovery and account session

Implementation status: partial in MSG-MX-005. Exact discovery and
authentication-method reads are implemented through Python Core and the pinned
adapter. Credential authentication, browser SSO/callback, refresh, logout,
revoke-all, credential rotation, and credential deletion remain blocked. The
missing authenticated one-use handoff and socket-owning SSO broker prevent an
account/session readiness claim.

Deliver exact lanes for:

- `/.well-known/matrix/client` and supported-version discovery;
- authentication API discovery for legacy login and current OAuth metadata;
- password and browser-based SSO/OAuth where the homeserver advertises them;
- access/refresh token handling through the macOS credential boundary;
- stable device ID, soft logout, refresh, logout, and revoke-all handling;
- one client/crypto-store lifecycle lock;
- capability report before connection.

Raw token import remains blocked. Access tokens use the Authorization header,
never query strings or logs.

Current evidence gate: Python dispatcher-to-real-Node integration proves the
two read lanes and content-free receipts against the bounded loopback fixture.
The full phase exit remains unmet until UAA can authenticate to the local test
server, refresh and revoke a session, restart without a duplicate device, and
fail safely on bad discovery, unsupported auth, rate limit, and soft logout.

### Phase 5 — Read-only sync and daily reading loop

Deliver:

- initial and incremental `/sync`, reconnect, pagination, room membership,
  invites, account data, spaces, DMs, room names/topics/avatars, unread and
  mention counts, typing and receipt projection, and notification decisions;
- normalized timelines for messages, replies, edits, redactions, reactions,
  polls, files, and thread summaries;
- Home aggregate and local two-Space mapping;
- cached/offline read state and explicit stale/fresh indicators;
- contained local search groundwork.

Exit gate: an encrypted-room placeholder is truthful until Phase 6; unencrypted
messages sent from Element appear once in UAA with stable ordering and no raw
content in logs or receipts.

### Phase 6 — Encryption, verification, backup, and recovery

Deliver:

- `initRustCrypto`, persistent crypto store, secret-storage callbacks, cross
  signing, device trust, verification requests, key backup status, restore
  progress, and decryption failure reasons;
- secure-backup setup and recovery-key display as a one-time protected flow;
- no screenshot, analytics, clipboard persistence, logs, or receipts containing
  recovery material;
- session verification, reset-identity consequence review, and recovery drills;
- key-request and undecryptable-event recovery UI.

Exit gate: Element sends an encrypted message that UAA decrypts; after a clean
reinstall UAA restores access using the approved recovery flow; losing all
recovery methods produces the documented destructive-reset warning.

### Phase 7 — Manual messaging MVP

Deliver:

- exact manual sends with stable transaction IDs, local echo, queued/sending,
  server-acknowledged, failed, retry, edit, discard, and remote-echo states;
- replies, threads, reactions, edits, redactions, mentions, formatting, drafts,
  typing settings, read-receipt settings, and desktop notifications;
- message context menus, keyboard navigation, accessibility, and focus return;
- truthful outcomes: opening a composer or pressing Retry never marks success;
  only adapter evidence does.

Exit gate: Element -> UAA encrypted message and UAA -> Element encrypted reply
works across restart, offline recovery, edit, reaction, thread, and receipt
tests. This is the first genuinely useful Messenger milestone.

### Phase 8 — Rooms, Spaces, people, search, and media

Deliver:

- start DM, create room, invite, join, leave, roles/power levels, notifications,
  history visibility, pins, favorites, low priority, and server-side Space
  mapping behind exact reviews;
- file/image upload and authenticated download, size/type limits, quarantine
  posture, progress, cancel, retry, safe preview, and local cleanup;
- room/global search with encrypted-room local-index rules and retention control;
- multi-account remains deferred until single-account device/crypto isolation is
  proven.

Exit gate: all room-management and media actions have exact scope, idempotency,
  Matrix event/transaction refs, error recovery, and redacted receipts.

### Phase 9 — UAA intelligence and cross-surface operations

Deliver:

- room policy Off / Ask each time / scoped Allow;
- unread and period summaries, reply drafts, open questions, decisions,
  commitments, task/date extraction, translation, and attachment analysis;
- related CRM, Calendar, Work Board, Knowledge, and Communications safe refs;
- exact proposals for messages, meetings, follow-ups, and tasks;
- visible sources, confidence, context manifest, expiry, and receipt outcome;
- no autonomous send and no automatic durable memory.

Exit gate: UAA proposes a reply and meeting from an encrypted conversation, the
operator reviews the exact content/destination/time, approved actions execute
through their existing governed lanes, and both produce understandable redacted
receipts.

### Phase 10 — Hardening and later capabilities

Deliver:

- large-room performance, sync backpressure, cache bounds, migration, multi-
  device conflict, rate-limit, abuse/reporting, retention, accessibility,
  localization, telemetry redaction, update/rollback, and safe-disable tests;
- calls as a separate lane after messaging reliability. Self-hosted calls need
  a reviewed MatrixRTC/Element Call decision and TURN for reliable VoIP;
- agents as visibly non-human room participants only after room policy, context,
  action, pause/remove, and receipt contracts are separately approved;
- production homeserver deployment and federation remain separate operations
  work, never silently provisioned by the client.

Exit gate: security review, migration/recovery drill, performance budgets,
rollback, safe-disable, and end-to-end acceptance packet pass.

## Acceptance Matrix

Minimum evidence before calling Messenger fully useful:

- existing Matrix account connects through discovered supported auth;
- UAA and Element exchange encrypted DMs and group-room messages;
- rooms, two local Spaces, unread, mentions, replies, threads, reactions, edits,
  redactions, files, search, notifications, typing, and receipts work;
- offline queue, retry, rate limit, soft logout, undecryptable event, key request,
  backup restore, verification, and device revocation recover correctly;
- manual sends and AI-proposed sends have distinct authority and UI;
- UAA summaries/drafts show sources and confidence and cannot silently send or
  persist Memory;
- no tokens, keys, raw messages, attachments, provider payloads, or local paths
  appear in logs, receipts, fixtures, screenshots, or diagnostics;
- every mutation has CLI/API inspection parity, idempotency, exact refs,
  rollback/safe-disable posture, and focused tests.

## Testing Strategy

- Python unit/contract tests for models, policy, approvals, redaction, receipts,
  safe refs, API manifest, and CLI parity.
- TypeScript unit tests for projection, ordering, local echo, retry, relations,
  room mapping, selectors, and accessibility.
- Local Synapse integration tests for discovery, login, sync, encrypted events,
  devices, backup, rooms, invites, media, rate limits, and logout.
- Playwright desktop tests for every rendered surface at 1440x900 and a narrower
  desktop width, including keyboard and screen-reader semantics.
- Interoperability tests with an independently installed Element Desktop client.
- Adversarial tests for malicious message content, oversized media, malformed
  events, spoofed receipts, untrusted homeserver discovery, token leakage,
  replayed approvals, cross-room context leakage, and AI prompt injection.

## Deployment And Cost Posture

- `LOCAL — no GitHub metered usage`: design approval, contracts, fixture UI,
  local Synapse harness, local Element interoperability, unit/integration/E2E
  tests, threat model, and implementation work.
- `INCLUDED — within an existing allowance or allowed by the Actions-specific
  safe-run rule`: one bounded standard-runner CI job for contract/unit tests,
  only if the repository's existing free/included Actions posture remains safe;
  no matrix, schedule, artifact, cache, deployment, or repeated rerun.
- `BLOCKED — could create a charge`: automatically provisioning a hosted Matrix
  provider, public Synapse host, TURN service, domain, certificate service,
  external object store, monitoring service, or hosted database.
- `REQUIRES HUMAN RESOLUTION`: selecting and funding any production homeserver,
  federation domain, TURN/calling infrastructure, or paid Element license.

The client must always retain a fully local fixture and local-Synapse test path.

## Authoritative References

- [Matrix Client-Server API](https://spec.matrix.org/latest/client-server-api/)
- [`matrix-js-sdk` documentation](https://matrix-org.github.io/matrix-js-sdk/)
- [`CryptoApi` documentation](https://matrix-org.github.io/matrix-js-sdk/interfaces/crypto-api.CryptoApi.html)
- [Element user guide](https://element.io/user-guide)
- [Element room middle-panel behavior](https://docs.element.io/latest/element-support/quick-start-guide/the-middle-panel/)
- [Element room right-panel behavior](https://docs.element.io/latest/element-support/quick-start-guide/the-right-panel/)
- [Synapse installation](https://element-hq.github.io/synapse/latest/setup/installation.html)
- [Synapse federation](https://element-hq.github.io/synapse/latest/federate.html)
- [Element Web licensing repository](https://github.com/element-hq/element-web)
