# Messenger Matrix Integrated Acceptance Packet

Status: `partial_acceptance_evidence`

Milestone: `MSG-MX-012`

Reviewed baseline: `c2113c1d022301b5abd174b3148f75cbb2513d05`

Evidence ref: `evidence-ref:msg-mx-012:integrated-acceptance-packet`

MSG-MX-012 grants no new runtime authority. This packet records a finite,
desktop-only integrated review of the exact Messenger Matrix lanes already
accepted through MSG-MX-011. It is not product, public-release, production,
hosted-service, universal-homeserver, or external-interoperability acceptance.

## State Vocabulary

- `implemented`: the stated bounded scope has current code and local evidence;
- `partial`: only the stated subset is implemented or evidenced;
- `blocked`: an exact required executor or authority is absent;
- `unsupported`: the capability is outside the accepted program authority;
- `configuration_required`: code exists, but no enrolled runtime target or
  credential/session binding was available for this review;
- `external_facility_required`: independent software, accounts, or devices were
  unavailable and acceptance evidence was not simulated.

These states are not interchangeable. A passing fixture, contract, or loopback
test does not promote a blocked or configuration-required runtime.

## Milestone Acceptance Matrix

| Milestone | State | Accepted evidence and remaining boundary |
|---|---|---|
| `MSG-MX-000` | `implemented` | Planning audit and immutable subordinate authority map only; no runtime lane. |
| `MSG-MX-001` | `implemented` | Desktop render contract, client/data boundary, threat model, and future-operation authority matrix only. |
| `MSG-MX-002` | `implemented` | Synthetic desktop shell covers fifteen surfaces and twenty-two deterministic states at both accepted desktop widths; fixture state is not runtime evidence. |
| `MSG-MX-003` | `implemented` | Backend-owned safe-ref communications inspection, protected no-store API, CLI parity, and disabled adapter declaration. |
| `MSG-MX-004` | `implemented` | Six exact disposable loopback harness lanes with teardown evidence; no general network or connector authority. |
| `MSG-MX-005` | `partial` | Homeserver discovery and authentication-method reads are implemented; eight credential, SSO, account, and session mutations remain blocked. |
| `MSG-MX-006` | `partial` | Two bounded GET transports and protected-cache/key primitives have loopback evidence; ten canonical dispatch executors remain uncomposed and live sync is configuration-required. |
| `MSG-MX-007` | `blocked` | Seventeen exact crypto/recovery authority contracts and posture/proposal projections exist; the persistent crypto adapter, live trust, backup, recovery, and reset executors remain blocked. |
| `MSG-MX-008` | `configuration_required` | Fifteen human-commanded messaging/outbox/notification lanes and a loopback-only broker have accepted local Synapse evidence; no enrolled account or remote target was available. |
| `MSG-MX-009` | `configuration_required` | Twenty exact room/admin/search/media lanes have bounded local evidence; no enrolled account or remote target was available. |
| `MSG-MX-010` | `partial` | Six exact local policy/context/proposal lanes are implemented; provider/model invocation and attachment analysis remain blocked. |
| `MSG-MX-011` | `partial` | Nine of twelve hardening categories have bounded local evidence; localization is partial, migration/multi-device ownership blocked, and Element external. |
| `MSG-MX-012` | `partial` | Integrated code, contract, operator-surface, authority, failure, and product-truth review is accepted only to the limits recorded in this packet. |

## Desktop Surface Acceptance Matrix

All fifteen surfaces have deterministic desktop render evidence. Runtime state
below describes the operator capability represented by each surface, not the
existence of the synthetic render.

| Surface | State | Integrated truth |
|---|---|---|
| `COMMS-MX-01` | `partial` | Founder HQ shell, backend posture, and governed local primitives exist; rooms and messages remain synthetic without enrollment. |
| `COMMS-MX-02` | `partial` | Personal Circle and room-AI-Off presentation is implemented; connected private rooms and DMs are not claimed. |
| `COMMS-MX-03` | `configuration_required` | Exact DM messaging primitives exist, but no enrolled live account was available; calls remain unsupported. |
| `COMMS-MX-04` | `configuration_required` | Exact group-room operations exist within accepted lanes; displayed members, polls, attachments, and events remain synthetic. |
| `COMMS-MX-05` | `configuration_required` | Exact thread send/reply primitives exist; no enrolled synchronized thread runtime was available. |
| `COMMS-MX-06` | `partial` | Encrypted local search is implemented; global/remote search remains configuration-required and fixture results grant no authority. |
| `COMMS-MX-07` | `partial` | Exact room/member/pin/history operations exist; the inspector is synthetic unless an enrolled target passes every gate. |
| `COMMS-MX-08` | `configuration_required` | Exact DM/room/invite lanes exist, but the setup surface remains preview-only and did not contact a directory or server. |
| `COMMS-MX-09` | `partial` | Exact room-setting and room-AI-policy lanes exist; desktop controls remain preview/review projections, not authority. |
| `COMMS-MX-10` | `blocked` | Content-free crypto posture exists; live session verification, secure backup, recovery, and identity-reset executors are blocked. |
| `COMMS-MX-11` | `partial` | Local policy, transient context manifest, and redacted proposal records exist; generation, execution, send, and automatic Memory are blocked. |
| `COMMS-MX-12` | `partial` | Failure/recovery states and bounded local recovery defenses are evidenced; no remote outage or independent device acceptance is claimed. |
| `COMMS-MX-13` | `implemented` | Full desktop dark appearance preserves the accepted hierarchy and semantics; appearance grants no capability. |
| `COMMS-MX-14` | `unsupported` | Calling, media capture, permission requests, provider calls, and external call completion are outside accepted authority. |
| `COMMS-MX-15` | `partial` | Discovery/auth-method reads exist; credential import, SSO handoff, session enrollment, and secure account setup remain blocked. |

## Required Failure And Recovery Scenarios

| Scenario | State | Bounded evidence and limit |
|---|---|---|
| restart | `implemented` | Protected cache and encrypted outbox persistence/recovery tests plus previously accepted disposable local Synapse evidence; no remote account claim. |
| offline | `partial` | Cached/offline/reconnecting UI truth, protected cache, and queued-send defenses are tested; no remote outage facility was used. |
| rate-limit | `implemented` | Route groups, bounded retry truth, and malicious/rate-limit hardening checks fail closed locally. |
| revocation | `partial` | Prestart approval/lease/readiness revocation fails closed; live account-wide session/device revocation remains blocked. |
| decryption | `partial` | Undecryptable and decryption-failure paths fail closed without unsafe retry; persistent multi-device decryption remains blocked. |
| backup | `blocked` | Exact backup/status/rotation/recovery contracts exist, but live persistent backup and restore executors are absent. |
| retry | `implemented` | Uncertain outcomes cannot retry automatically; manual retry must retain exact idempotency and reconciliation scope. |
| duplicate | `implemented` | Duplicate declarations, lifecycle owners, events, idempotency keys, and terminal replays reject or deduplicate deterministically. |
| malicious-event | `implemented` | Room/event/size/relation bounds, hostile queue/schema handling, cross-room redaction denial, and content-free errors are tested. |
| redaction | `implemented` | Local sync tombstones prevent rehydration and the exact messaging redaction lane has accepted disposable Synapse evidence. |
| rollback | `partial` | Every accepted mutation binds rollback, compensation, or explicit irreversibility posture; no blanket rollback claim is made. |
| safe-disable | `implemented` | Harness, session, sync, messaging, room/media, and intelligence boundaries recheck safe-disable and fail closed before adapter start. |
| Element interoperability | `external_facility_required` | Element Desktop and the required independent accounts/devices were unavailable; evidence was not simulated. |

Historical disposable Synapse drills cited above are accepted milestone evidence,
not a claim that this review re-ran live external interoperability. Cleanup
proof for those drills remains in their milestone artifacts.

## API, CLI, And macOS Desktop Parity

| Capability family | API | CLI | macOS desktop | Acceptance |
|---|---|---|---|---|
| provider/session inspection | protected no-store snapshot/read routes | communications provider and Matrix session status/command projections | setup and posture surfaces retain blocked/configuration truth | `partial` |
| sync posture | protected no-store posture and exact proposal/dispatch routes | `matrix-sync-status` and exact command projection | backend-owned sync banner; fixture timeline remains labeled | `partial` |
| crypto/recovery posture | protected no-store posture and exact proposal routes | `matrix-crypto-status` and exact command projection | sessions/recovery inspector shows the same blocked adapter truth | `blocked` |
| messaging | protected no-store posture plus exact command routes | `matrix-messaging-status` and exact command projection | composer/actions remain preview unless backend enrollment and gates pass | `configuration_required` |
| rooms/search/media | protected no-store posture plus exact command routes | `matrix-rooms-media-status` and exact command projection | room/search/media controls preserve configuration and failure truth | `configuration_required` |
| governed intelligence | protected no-store posture plus six exact local lanes | `matrix-intelligence-status` and exact command projection | separate UAA inspector; no hidden composer or execution authority | `partial` |
| hardening | protected no-store read-only posture | `matrix-hardening-status` | recovery inspector projects the same twelve categories and budgets | `partial` |

The disposable local Synapse harness is a development facility with protected
API and CLI inspection/control, not an accepted end-user desktop capability.
Its omission from desktop controls is therefore not a parity claim or gap.
No behavior lives only in React state except presentation state.

## Integrated Verification Evidence

The pre-acceptance integrated review completed these content-free lanes on the
reviewed baseline:

- 676 focused Python Messenger tests passed across MSG-MX-000 through
  MSG-MX-012 and the shared Matrix runtime tests;
- 21 pinned Matrix client-adapter Node tests passed with zero audit findings;
- 13 Messenger milestone verifier entrypoints passed;
- 242 focused Control Center API/Messenger/application tests passed;
- 33 Messenger visual-regression cases passed across all fifteen surfaces,
  both accepted desktop widths, accepted state variations, and workspace
  representation;
- TypeScript typecheck and the production frontend build passed.

Repository-wide documentation, OpenAPI, route/API, frontend, Foundation Gate,
and hosted CI closeout results belong to the exact MSG-MX-012 commit and PR
evidence. This document does not embed raw logs, machine identity, local paths,
credentials, messages, attachments, provider payloads, or recovery material.

## Repairs And Residual Risk

No safe in-scope runtime defect was found during the integrated review. The
first focused pass added this finite packet, its verifier, and active truth
cross-links. The second and final focused pass advanced the baseline verifier's
mutable accepted-current-phase map and its phase-binding tamper test from
MSG-MX-011 to MSG-MX-012. The immutable historical baseline and its hashes did
not change. No mutation, dependency, route, schema, authority lane, or product
surface changed.

Residual risks remain explicit:

- no persistent crypto adapter or durable multi-device ownership/migration;
- no live backup, restore, verification, recovery, reset, or account/session
  revocation executor;
- no enrolled remote account or universal homeserver evidence;
- no independent Element interoperability evidence;
- no production localization catalog;
- no provider/model invocation, attachment analysis, autonomous send, automatic
  Memory truth, calls, agent room participants, hosted infrastructure, public
  federation, public release, or production deployment authority.

Every future call remains exact-scope, request-scoped, approval-bound where
required, AuthorityLease-bound, deadline/budget/readiness checked,
idempotency/replay checked, redacted, content-free in durable evidence,
rollback-aware, and safe-disable guarded. Unknown, stale, expired, or mismatched
state fails closed before a call starts; an approval ref alone authorizes
nothing.
