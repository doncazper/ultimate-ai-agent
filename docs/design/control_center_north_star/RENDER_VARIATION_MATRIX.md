# Control Center Render Variation Matrix

Status: render production queue, documentation only  
Specification: `CC-UIUX-2026-07-11`  
Input baseline: `CC-NS-2026-07-06`  
Current as of: 2026-07-13
Repository baseline: `v0.104.0` / package `0.104.0`

This matrix defines the complete set of coherent render deliverables required
before the real Control Center fidelity implementation begins. It adds no UI
behavior or runtime authority.

## Artifact Naming

`CC-R2-<group>-<surface>-<viewport>-<scenario>.png`

Viewports:

- `desktop`: 1440x900;
- `compact`: 1280x800;
- `mobile`: 390x844;
- `board`: component/state reference board at 1440x900.

Approval states: `draft`, `review`, `approved`, `superseded`.

## Shared Render Boards

These boards prevent every route from inventing its own shell or common state.

| ID | Board | Required content |
|---|---|---|
| `SHELL-01` | Standard shell | full rail, collapsed groups, top strip, workspace, bottom band |
| `SHELL-02` | Compact shell | collapsed rail, inspector drawer, compact top strip |
| `SHELL-03` | Mobile shell | navigation drawer, one-pane workspace, sheet inspector, sticky action bar |
| `STATE-01` | Route data states | loading, empty, partial, blocked, error, success, mock fallback |
| `STATE-02` | Mutation states | default, dirty, confirm, busy, validation error, rejected, saved receipt, reloaded |
| `STATE-03` | Authority states | read-only, proposal-only, approval required, receipt-backed, denied, planned |
| `CONTROL-01` | Control semantics | buttons, links, selects, segmented controls, toggles, status rows, disabled reason |
| `OVERLAY-01` | Command palette | default results, filtered results, disabled result reason, empty results |
| `OVERLAY-02` | Dialogs and notices | confirmation, cancellation, error, success, drawer, tooltip |
| `A11Y-01` | Keyboard/focus | focus order, focused controls, selected rows, board keyboard move |
| `ASSIST-01` | Persistent UAA composer | collapsed, focused, context attached/removed, search, ask, proposal handoff |
| `ASSIST-02` | UAA sidecar | answer, cross-surface context, navigation result, proposal preview, blocked request |
| `NAV-01` | Sidebar customization | pin/unpin, reorder, collapsed groups, density, cancel, reset defaults |

## Locked Target Product Render Set

The route queue below remains the coverage ledger for the current 40-route
implementation. The following target renders establish the approved
consolidated shell before route-by-route fidelity work. Their information
architecture is defined by
`../CONTROL_CENTER_PRODUCT_IA_AND_CALENDAR_CONTRACT.md`.

| ID | Target surface | Required content |
|---|---|---|
| `TARGET-NAV-01` | Today in target shell | Today-first rail; Communications, Messenger, Work Board, CRM, Calendar, News, Studio; Knowledge; Activity & Trust; six Today panels; receipt activity rail; `Review N decisions`; weather; UAA composer |
| `COMM-01` | Communications | unified queue/detail/inspector; Email, Messages, Follow-ups, Drafts, Waiting; CRM context; `Propose event`; proposal-only and blocked-send states |
| `COMMS-MX-01`–`15` | Messenger | immersive light shell; Home plus exactly two Spaces; rooms/DMs; threads; search; room info; create/invite; settings; sessions/recovery; UAA approval; failure recovery; full dark theme; calling preflight; setup/sign-in |
| `BOARD-01` | Work Board | Board/List/Timeline/Plans/Completed; shared task truth; CRM/Calendar/Communications links; receipt-backed completion |
| `CRM-01` | CRM | People/Organizations/Opportunities/Pipeline/Follow-ups/Reports tabs; six compact KPIs; smart views; dense sortable relationship table; persistent record inspector; pipeline analytics; governed availability-backed Call chooser; source-backed next action; v1/v2/v3 gallery history |
| `CAL-01` | Calendar week | color-coded schedule; tasks and commitments; source-backed candidate; duplicate/conflict/timezone posture; shared refs; proposal-only external posture |
| `NEWS-01` | News | curated For You/Business/Technology/Markets/Saved/Sources; visible provenance, freshness, and selection rationale |
| `DECISIONS-01` | Decision Review | exact source, time, participants, location, CRM/work links, conflicts, confidence, authority, expiry, edit/approve/reject/defer outcomes |
| `STUDIO-01` | Agent Studio | immersive coding-agent workbench; Back to Control Center; fixed project rail; dominant transcript/editor; fixed inspector; docked governed composer; Terminal; clean shared pane edges |
| `CREATIVE-STUDIO-01` | Creative Studio | presentations, documents, spreadsheets, media, and brand assets; fixed project rail; slide/page/sheet canvas; versions; references; rights; linked work; governed review and blocked-until-promoted export |
| `KNOWLEDGE-01` | Knowledge | memory/files/context/sources; provenance; conflicts; corrections; reviewed-context decisions |
| `ACTIVITY-01` | Activity & Trust | receipts, evidence, proof, history, approvals, authority, safe refs, and correction/rollback paths |
| `CUSTOMIZE-01` | Customize | order, visibility, groups, density, preview, cancel, reset; no capability language |
| `SETTINGS-01` | Settings | search-first preferences; semantic controls; current posture; blocked/planned explanations |
| `DEVTOOLS-01` | Developer Tools | runtime/models/storage/API/gate/plugins/diagnostics; exact lanes and truthful blocked states |
| `TERMINAL-01` | Terminal | Developer Tools terminal tab; exact command lanes; redacted output; exit/receipt state; pop-out without authority escalation |
| `ONBOARDING-01` | Onboarding | first-run local setup; optional read-only sources; safety defaults; skip path |
| `UAA-SIDECAR-01` | UAA Sidecar | safe context; cross-surface answer; citations; proposal handoff; blocked direct mutation |
| `TRUST-01` | Trust cockpit | mode/domain matrix; exact lease; policy decisions; receipts/audit; revoke/pause/kill; safe-disable |
| `SHELL-COMPACT-01` | Compact shell | icon-only rail; tooltips; accessible names; badges; active state; fixed bottom utilities |

## Route Render Queue

Every route requires a default desktop and compact render. `Mobile` means a
route-specific mobile render is required in addition to the shared mobile
shell. The variations column names only route-specific variants; generic
states come from the shared boards above.

Unless a blocking confirmation dialog temporarily owns focus, every default
route render shows the shared UAA composer. At least one route-specific render
for each workspace template shows the expanded sidecar.

| Group | Route | Surface | Template | Route-specific variations | Mobile |
|---|---|---|---|---|---|
| Founder Loop | `/start` | Start Here | Daily command deck | first run; partial setup; ready return visit | yes |
| Founder Loop | `/today` | Today | Daily command deck | exactly six information-rich panels on aligned three-column tracks; full-width receipt activity rail; workload-aware `Review N decisions`; title-line weather; non-redundant synthesized briefing; cross-surface attention queue; universal selected-item inspector/drawer; Day Plan with Now/Next; truth-safe queue/complete confirmation; reported-complete review; sourced news with mixed article/email-bulletin sources; Business pulse; morning/midday/end-of-day; calm/overloaded; stale or blocked news/weather; CRM follow-up selected; Work Board blocker selected; no decisions with demoted CTA; high-risk blocked item; degraded sources; persistent privacy/authority posture; UAA sidecar asking about board/CRM | yes |
| Founder Loop | `/inbox` | Source Inbox | Queue/detail/inspector | ready sources; missing source; connector draft-only; all sources blocked | yes |
| Founder Loop | `/plans` | Plans | Board/planning | plan selected; no plan; proposal dirty; action-envelope handoff | yes |
| Founder Loop | `/work-board` | Work Board | Board/planning | backend order; unsaved preview; persist confirmation; receipt saved; blocked external lane; UAA board question/task proposal | yes |
| Founder Loop | `/actions` | Action Inbox | Queue/detail/inspector | ready for decision; edited envelope; reject/defer; approved receipt; ineligible/blocked | yes |
| Founder Loop | `/proof` | Proof | Queue/detail/inspector | proof selected; no selection; stale proof; rollback/safe-disable ready | yes |
| Founder Loop | `/trust` | Trust | Matrix/settings | no lease; active exact lease; denied scope; revoke confirmation; safe-disable | yes |
| Founder Loop | `/memory` | Memory | Queue/detail/inspector | candidate; correction dirty; conflict/stale; accepted receipt; empty review queue | yes |
| Founder Loop | `/evidence` | Evidence | Ledger/inventory | narrative timeline; event selected; stale/blocked event; empty; degraded proof refs | yes |
| Founder Loop | `/settings` | Settings | Matrix/settings | search-first UAA results; read-only posture; mode dirty; confirm; saved receipt; unsupported adapter/blocked request | yes |
| Founder Loop support | `/briefing` | Briefing | Daily command deck | assembled; missing evidence; no source refs; proposed actions ready | yes |
| Founder Loop support | `/crm` | CRM | Board/planning | relationship selected; follow-up queue; pipeline; smart lists/reports; local mutation confirm/receipt; connector-read blocked; UAA relationship/follow-up question | yes |
| Founder Loop support | `/private-trial` | Trial Packet | Setup/readiness | overview; selected acceptance item; blocked item; completed private review | no |
| Review | `/operator-loop` | Operator Loop | Daily command deck | normal partial loop; blocked act stage; fully proofed local loop | no |
| Review | `/setup` | Setup | Setup/readiness | first run; partial prerequisites; ready; blocker detail; safe command copy | yes |
| Review | `/coding` | Coding | Queue/detail/inspector | context; patch proposal; validation ready/running/receipt; apply blocked; pair-agent preview | yes |
| Review | `/chat` | Chat | Conversation/handoff | empty thread; local reply; tool denied; plan handoff; action/memory/evidence proposal | yes |
| Review | `/models` | Models | Matrix/settings | no local models; local ready; model selected; provider blocked; credential/cost partial | no |
| Review | `/approvals` | Approvals | Queue/detail/inspector | empty; pending exact scope; approved/rejected receipt; run-attached wait | no |
| Review | `/files` | Files | Queue/detail/inspector | file selected; unsafe refs omitted; empty; review needed | no |
| Review | `/files/review` | File Review | Queue/detail/inspector | safe use; needs correction; exclude; defer; receipt | no |
| Review | `/context/proposals` | Context Proposals | Queue/detail/inspector | include/exclude dirty; injection blocked; proposal saved | no |
| Review | `/action-preview` | Action Preview | Queue/detail/inspector | clean preflight; approval required; denied policy; expired; no side effects | no |
| Runtime | `/runtime` | Runtime | Ledger/inventory | healthy; partial; exact command lane ready; command receipt; arbitrary shell blocked | yes |
| Runtime | `/storage` | Storage | Ledger/inventory | healthy ledger; stale snapshot; capacity caution; rollback point selected | no |
| Runtime | `/runtime/local` | Local Runtime | Setup/readiness | stopped/readiness only; ready; degraded; exact lane unavailable | no |
| Runtime | `/runtime/manual-smoke` | Manual Smoke | Setup/readiness | not run; running; partial; passed; failed sanitized | no |
| Runtime | `/remote-workers` | Remote Workers | Setup/readiness | planned matrix; dry-run metadata; blocked execution | no |
| Runtime | `/mobile-planning` | Mobile Planning | Setup/readiness | planned capabilities; permission denied/unsupported; no sensor authority | no |
| Runtime | `/plugin-governance` | Plugin Governance | Setup/readiness | catalog metadata; activation proposal; runtime import blocked | no |
| Evidence | `/foundation-gate` | Foundation Gate | Ledger/inventory | passed; caution; failed; stale report; verifier details | no |
| Evidence | `/receipts` | Receipts | Queue/detail/inspector | receipt selected; empty; stale; rollback linked; invalid ref blocked | no |
| Evidence | `/events` | Events | Ledger/inventory | normal ledger; event selected; empty; sanitized error | no |
| Evidence | `/events/timeline` | Timeline | Ledger/inventory | typed trace; related refs; empty/mock; blocked event | no |
| System | `/` | Overview | Daily command deck | healthy; partial; mock fallback; no next step | yes |
| System | `/dashboard` | Dashboard | Daily command deck | product loop; runtime; degraded fanout; blocked authority summary | no |
| System | `/capabilities` | Capabilities | Matrix/settings | implemented; partial; blocked; planned; exact lane detail | no |
| System | `/api-routes` | API Routes | Ledger/inventory | all routes; filtered class; route selected; manifest mismatch | no |
| System | `/differentiators` | Differentiators | Ledger/inventory | evidence-backed claims; missing proof; unsupported claim blocked | no |

Route count: 40. Every route in `apps/control-center/src/routes.tsx` is listed.

## Production Order

1. Shared shell and state boards.
2. Today, Action Inbox, Plans, Work Board, Trust, Evidence/Proof, Memory.
3. Setup, Source Inbox/CRM/Briefing, Chat, Settings, Coding.
4. Start/Overview/Dashboard and Models/Files/Action Preview.
5. Runtime, Storage, system/evidence inventories, future-domain surfaces, and
   private trial.
6. Compact variants.
7. Route-specific mobile variants.
8. Cross-set coherence review and approval packet.

No implementation phase begins until the render set is explicitly approved.
