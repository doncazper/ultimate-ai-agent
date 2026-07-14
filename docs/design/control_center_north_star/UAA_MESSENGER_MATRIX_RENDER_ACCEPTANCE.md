# UAA Messenger Matrix Desktop Render Acceptance

Status: MSG-MX-001 target design accepted; no runtime implementation evidence.
Baseline: `communications-v1`.
Product platform: macOS desktop only.

MSG-MX-002 implementation note: the accepted targets and required state
variations now have a synthetic desktop fixture route at `/messenger`. That
route is presentation evidence only; it does not change the runtime and
authority exclusions below.

## Acceptance meaning

The fifteen renders are accepted as desktop product targets for the fixture and
later runtime phases. Acceptance covers information architecture, hierarchy,
state language, and bounded desktop adaptation. It does not prove a route,
Matrix account, provider, connection, sync, encryption, search, local cache,
message send, room mutation, media transfer, call, or UAA model operation.

The normative app-shell and product-language documents override incidental
generated-image details. Every future visible command must be wired to the same
Python Core/API/CLI contract or be labeled `Preview`, `Planned`, or `Blocked`.
Rendered success, status, counts, messages, people, rooms, devices, receipts,
and timestamps remain synthetic design data.

## Desktop width contract

- Normal review viewport: 1440 x 900 CSS pixels or wider.
- Narrow desktop review viewport: 1180 x 800 CSS pixels.
- No mobile layout, mobile route, mobile capture, touch-only interaction, or
  mobile implementation is accepted by this phase.
- At the narrow desktop width the Messenger rail remains visible and the
  conversation remains primary. The room/UAA inspector becomes a deliberate
  drawer or collapsible pane; it does not cover the composer without an explicit
  close command.
- Long labels truncate with accessible full text; counts, encryption, unread,
  failed, pending, blocked, and approval-required states remain perceivable
  without color alone.
- The human composer and UAA prompt/proposal surface remain visually and
  semantically separate at every desktop width.
- A mobile device shown in the sessions table is account data inside a desktop
  view, not a mobile product surface.

## Render decisions

| ID | Decision | Normal desktop target | Narrow desktop target | Mandatory truth constraint |
|---|---|---|---|---|
| `COMMS-MX-01` | accepted | Founder HQ, room list, encrypted-target group timeline, bounded UAA inspector | collapse UAA inspector first; preserve both Messenger and room rails | target/preview data only; no connected account, encryption session, or send claim |
| `COMMS-MX-02` | accepted | Personal Circle with private rooms, DMs, and room AI policy Off | inspector becomes a drawer; room AI Off remains visible | no AI content access, send, memory write, or connected-account claim |
| `COMMS-MX-03` | accepted | one-to-one timeline with details, relations, typing, receipt, and call entry points | details collapse before timeline; call controls remain planned/blocked | encryption and verification are targets; no live send, call, file, or CRM mutation |
| `COMMS-MX-04` | accepted | dense group room, topic, members, poll, attachments, reactions, and room inspector | inspector collapses; message actions remain keyboard accessible | all events are synthetic; invite, file, poll, and room-setting writes remain blocked |
| `COMMS-MX-05` | accepted | room timeline plus thread list and focused thread | thread pane uses bounded drawer; main timeline context stays available | no synchronized threads, reply, send, or read-receipt claim |
| `COMMS-MX-06` | accepted | local/global search, attention modes, selected result, related refs, UAA proposal list | selected-result rail collapses; filters wrap without hiding scope | local index and Matrix reads remain planned; results and actions are fixture evidence only |
| `COMMS-MX-07` | accepted | room information, people, files, links, pins, integrations, and safe receipt refs | room-information pane becomes the primary bounded drawer | member/integration state is synthetic; management commands remain Preview/Planned/Blocked |
| `COMMS-MX-08` | accepted | create/DM choice with exact invitation review | review inspector moves below or into a drawer without losing recipients/scope | no directory query, invite, room creation, or external action occurs |
| `COMMS-MX-09` | accepted | room settings with explicit before/after change review | change inspector becomes a drawer; Save is relabeled Preview until wired | UI changes do not mutate Matrix state or grant approval/lease authority |
| `COMMS-MX-10` | accepted | desktop account-security view for sessions, verification, backup, and recovery | recovery rail collapses after recommendations and current-session posture | shown device types are data rows only; no device, key, backup, or recovery operation exists |
| `COMMS-MX-11` | accepted | source-bound UAA summary/proposal inspector separate from human composer | intelligence pane becomes a drawer; source/expiry/approval remain visible | message content is untrusted; proposal is not approval, send, calendar write, or memory truth |
| `COMMS-MX-12` | accepted | explicit offline, reconnecting, failed, rate-limited, undecryptable, and cached states | recovery pane becomes a drawer; state banner and failed-send truth stay fixed | Retry never implies execution or success; no cached-content authority or hidden send |
| `COMMS-MX-13` | accepted | full Messenger dark appearance with identical hierarchy and semantics | same collapse order as light appearance | appearance changes no capability, authority, evidence, or product status |
| `COMMS-MX-14` | accepted as blocked preflight | call availability, devices, permissions, authority, and external handoff posture | preflight is the primary pane; context rail collapses | no call, permission request, media capture, provider operation, or completion claim |
| `COMMS-MX-15` | accepted as blocked setup target | homeserver, authentication choice, secure storage, and exact connection review | step rail compresses but stays desktop; review becomes a drawer | no server contact, credential storage, discovery, session, or raw-token import |

## Required phase-two states

MSG-MX-002 must render deterministic, synthetic variations for loading, initial
sync, empty room, no search results, invite pending, join failed, local echo,
queued send, failed send, retry, edited, redacted, undecryptable, verification
requested, verification failed, backup unavailable, offline, reconnecting, rate
limited, permission denied, room archived/left, and inspector collapsed at both
accepted desktop widths. These are fixture states, not runtime outcomes.

## Rejected interpretations

- Pixel output overriding accessible behavior or truthful state language.
- A dark rail mixed with a light conversation except in the full dark variant.
- A hidden or merged human composer and UAA proposal surface.
- Any mobile implementation inference.
- Any claim that the image set is a current application screenshot or runtime
  acceptance result.
