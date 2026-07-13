# UAA Communications Matrix North Star

Status: design and implementation-planning direction only.
Render set: `communications-v1`.
Current as of: 2026-07-11.

## Governing Statement

UAA Messenger is an independently implemented, Element-class Matrix client. It
preserves the familiarity and capability of a mature Matrix desktop client
while adding UAA's local intelligence, governed agent participation,
cross-surface context, approvals, and receipts. It is a separate primary tab
from Communications.

Element is a visual and behavioral reference. Matrix is the protocol. UAA owns
the implementation and product identity. Do not copy or transplant Element
source code, styles, components, assets, icons, illustrations, branding,
internal identifiers, or product copy.

## Product Truth

The current UAA repository does not contain a Matrix SDK, Matrix homeserver
configuration, Matrix account/session flow, encryption key store, sync runtime,
or Matrix-backed messaging UI. Existing Messages Connector and Mattermost work
does not constitute Matrix support. Every image in this set is a target render,
not runtime evidence.

## Desktop Structure

Communications keeps the accepted unified email, message-source, follow-up,
draft, and waiting-on-others design. Selecting Messenger changes the sidebar in
the same way Studio does. Messenger uses three compact regions:

1. an immersive Messenger rail containing a visible Back to Control Center
   command, Home / All Messages, exactly two Spaces, room/direct-message lists,
   and account/security access;
2. the dominant active conversation timeline and human message composer; and
3. an optional room-details or UAA-intelligence inspector.

The standard UAA status, decision-workload, privacy, and receipt posture remains
visible in compact Messenger chrome. The global UAA composer moves into
the intelligence inspector on this route so it cannot be confused with the
human message composer.

## Two-Space Model

Home / All Messages is a neutral aggregate for unread items, mentions,
invitations, and recent direct messages; it is not a Space. Exactly two primary
Spaces anchor the first product experience:

- **Founder HQ** contains work, client, project, UAA development, planning, and
  operational rooms.
- **Personal Circle** contains direct messages, friends, family, and private
  social groups.

Each Space has its own room list, ordering, unread and mention state, muted and
favorite sections, notification defaults, and room-level AI policy. Both share
the same Matrix account, device trust, encryption recovery, global search, and
local privacy posture.

## Control Semantics

- Space, room, tab, and settings choices are navigation or selectors.
- Send, invite, create, verify, retry, save, and review are commands.
- Unread, encrypted, verified, syncing, offline, failed, and approval-required
  states are explicit status treatments, not decorative controls.
- Human message sending and UAA action approval are separate flows.
- AI access is configured per room as Off, Ask each time, or Allowed for the
  currently scoped read operation. Autonomous sending remains Never.
- Message edits, redactions, reactions, attachments, and read markers preserve
  their Matrix event identity and visible pending/failed state.

## Rendered Surface Set

| ID | Surface | Primary evidence |
|---|---|---|
| `COMMS-MX-01` | Founder HQ | immersive Messenger rail; two Spaces; work rooms; active encrypted group room; UAA summary |
| `COMMS-MX-02` | Personal Circle | second Space selected; private rooms and DMs; room AI access Off |
| `COMMS-MX-03` | Direct message | encrypted one-to-one timeline; typing, receipts, reply/reaction controls; call actions |
| `COMMS-MX-04` | Group room | room topic, members, mentions, attachments, reactions, read markers, composer |
| `COMMS-MX-05` | Threads | main timeline plus thread inspector and thread composer |
| `COMMS-MX-06` | Search and attention | global/room search, mentions, unread, pinned, and saved results |
| `COMMS-MX-07` | Room information | people, roles, invite, files, links, pins, integrations, and receipts |
| `COMMS-MX-08` | Create and invite | start DM, create room, select Space, privacy, encryption, and invitation review |
| `COMMS-MX-09` | Room settings | general, security, permissions, notifications, history, and UAA room policy |
| `COMMS-MX-10` | Sessions and recovery | current/other sessions, verification, secure backup, and recovery posture |
| `COMMS-MX-11` | UAA intelligence | summary, questions, decisions, commitments, tasks, calendar proposal, and exact approval |
| `COMMS-MX-12` | Failure and recovery | offline/syncing/failed-send/decryption states with bounded recovery actions |
| `COMMS-MX-13` | Dark theme | approved communications structure in a polished dark appearance |
| `COMMS-MX-14` | Calling | availability and permission preflight for voice/video without implying a live call |
| `COMMS-MX-15` | Setup and sign in | homeserver discovery, account sign-in, SSO/password choice, storage, and exact connection review |

## Common Visual Rules

- Element-familiar panel hierarchy and desktop density, translated into UAA's
  navy, white, cobalt, semantic color, typography, icons, and receipts.
- The canonical light appearance uses a white or very pale Messenger rail. Do
  not mix a dark left rail with a light conversation surface. Dark styling is
  reserved for the explicit full-app dark-theme variation.
- The conversation remains visually dominant; UAA intelligence is secondary
  and collapsible.
- Rooms show clear favorite, low-priority, muted, unread, mention, invite, and
  encryption states without relying on color alone.
- Message controls appear on hover/focus in implementation but are shown on one
  selected message in renders to document their placement.
- No raw access tokens, recovery keys, device secrets, email addresses, phone
  numbers, local paths, private message dumps, or provider payloads.
- No image claims that a homeserver, account, provider, sync, encrypted session,
  call, or send is currently connected or implemented.

## Required Variations Beyond The North-Star Images

Implementation must cover loading, initial sync, empty room, no search results,
invite pending, join failed, local echo, queued send, failed send, retry,
edited, redacted, undecryptable, verification requested, verification failed,
backup unavailable, offline, reconnecting, rate limited, permission denied,
room archived/left, and inspector-collapsed states at normal and narrower
desktop widths.
