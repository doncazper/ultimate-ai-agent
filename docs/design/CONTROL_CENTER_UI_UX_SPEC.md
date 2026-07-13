# Control Center UI/UX Specification

Status: canonical design contract, documentation only  
Specification ID: `CC-UIUX-2026-07-11`  
Revised: 2026-07-13 for the accepted News & Signals front-page target
North-star input baseline: `CC-NS-2026-07-06`  
Repository baseline: `v0.104.0` / package `0.104.0`  
Primary product: Founder Command Center / Control Center  
Primary operator: one local founder/operator

This specification turns the accepted Control Center north-star renders into
one coherent, implementation-ready UI/UX contract. It governs future renders
and the later real-surface fidelity pass. It does not add routes, controls,
runtime behavior, authority, provider/model calls, connector access, browser
automation, public distribution, or production readiness.

## Source Precedence

When sources disagree, use this order:

1. Python Agent Core, API contracts, policy, approval, redaction, route
   side-effect classification, and current product truth.
2. This specification.
3. `control_center_north_star/APP_SHELL_BASELINE.md`.
4. The route mapping and render requirements in
   `control_center_north_star/SURFACE_COVERAGE.md` and
   `control_center_north_star/RENDER_VARIATION_MATRIX.md`.
5. Individual north-star PNGs.
6. Current implementation styling.

The PNGs establish art direction and composition. They do not override current
authority or invent product capability. Generated labels, example data, route
order, and unsafe/raw values in a PNG are illustrative only.

## Product Experience Contract

The Control Center is the local cockpit for one founder/operator. It should
answer, in this order:

1. What matters now?
2. What needs my decision?
3. What is safe to inspect, draft, or do?
4. Why is this shown?
5. What happened, and what proves it?
6. What remains blocked or needs a separate authority lane?

The target daily product spine is:

`Today -> Communications -> Messenger -> Work Board -> CRM -> Calendar -> News & Signals -> Studio`

Knowledge and Activity & Trust support that loop without displacing daily
work. Action Inbox is the global decision utility surfaced as `Review N
decisions`, not a permanent primary tab. The complete target navigation,
current-to-target mapping, and source-to-calendar proposal loop are locked in
`CONTROL_CENTER_PRODUCT_IA_AND_CALENDAR_CONTRACT.md`.

## Experience Principles

1. **Cockpit, not webpage.** Use one bounded application window with fixed
   navigation, a stable top strip, contained work panes, and optional bottom
   proof/status bands.
2. **Work before diagnostics.** Show the operator's task, queue, board, or
   decision first. Put safe refs, operation IDs, raw route metadata, verifier
   names, and deep governance details in inspectors or explicit details views.
3. **One obvious next action.** Each route has one primary next step. Secondary
   actions stay visually subordinate; blocked remediation is explicit.
4. **Truthful capability.** Implemented, approval-required, read-only,
   proposal-only, blocked, planned, degraded, mock, and missing states remain
   distinct in text and appearance.
5. **Authority is context, not wallpaper.** Show active mode, applicable
   scope, approval posture, and receipt/rollback state near consequential work.
   Do not repeat every blocker across every panel.
6. **Compact, calm, reversible.** Prefer shallow panels, lists, tables,
   split panes, and inspectors over nested cards and long documents.
7. **Real state owns the UI.** React may own selection, filters, disclosure,
   draft input, and unsaved preview layout. Python Core/API owns durable and
   operator-relevant truth.
8. **No visual fiction.** Demo or generated data is labeled. A render may show
   representative safe data, but implementation must use actual backend state.
9. **One integrated assistant.** A persistent, context-aware UAA composer lets
   the operator ask about, find, navigate, explain, or propose work from almost
   every surface without turning the screen into a separate chat product.

## Canonical Application Shell

### Standard desktop geometry

Reference viewport: `1440 x 900` CSS pixels.

| Region | Contract |
|---|---|
| Window | Full viewport; `overflow: hidden`; no page-document canvas |
| Left rail | 260 px; fixed; dark graphite/navy; internal scroll only when needed |
| Top status strip | 76 px; fixed; 4-6 concise posture groups maximum |
| Workspace | Remaining width/height; 24 px outer padding; 16 px region gaps |
| Primary pane header | 56-64 px; title, short status, local controls |
| Queue/list pane | 280-340 px |
| Inspector | 340-380 px |
| Bottom proof band | 96-128 px only when it closes the workflow |
| Dense row | 40 px target; 36 px minimum |
| Standard control | 32-36 px height |

The normal workflow must fit inside the window. Long queues, chats, ledgers,
tables, and inspectors scroll inside their own pane. Page-level scrolling is a
design failure at the reference desktop viewport unless the surface is an
explicit long-form report.

### Canonical global rail

The target default order is:

1. Today
2. Communications
3. Messenger
4. Work Board
5. CRM
6. Calendar
7. News & Signals
8. Studio
9. Knowledge
10. Activity & Trust
11. Customize
12. Settings
13. Developer Tools, collapsed and hidden by default

Today is the default landing workspace. `Start Here` is onboarding-only after
setup. Plans becomes a Work Board view; Source Inbox becomes a Communications
view; Chat and Coding become Studio modes; Memory and Files become Knowledge;
and receipts, evidence, proof, trust, events, and approvals consolidate under
Activity & Trust. This is a target render and implementation architecture, not
a claim that current routes have already been consolidated. Route-local tabs
never enter the global rail. One item, and only one item, has
`aria-current="page"`.

The operator may enter `Customize sidebar` to pin/unpin surfaces, reorder
pinned surfaces, collapse groups, choose compact or comfortable density, and
restore defaults. This changes presentation only:

- `Hide from sidebar` never disables a route or capability;
- every hidden surface remains reachable through `All surfaces`, the UAA
  composer, command search, and direct navigation;
- capability availability, authority, and sidebar visibility use separate
  language and state;
- approval controls, blockers, global safety posture, and required warnings
  cannot be hidden by layout preferences;
- the customization preview can be cancelled or reset;
- layout preference may remain presentation-owned local state.

### Top status strip

The strip shows only operator-relevant global posture:

- local runtime/connection;
- current authority mode;
- active lease or `No active lease`;
- receipt requirement/proof posture;
- Foundation Gate or global safety posture;
- operator menu.

Each group has an icon, a short label, and a short value. A global degraded or
mock state uses one bounded banner immediately below the strip, not repeated
warnings inside every route panel.

### Standard route toolbar

Normal workspaces use one invariant 64 px toolbar below the posture strip:

- title and one-line subtitle occupy the left slot;
- collection search occupies the same center-right slot on every applicable
  route;
- route-local filters and secondary commands follow search; and
- `Review N decisions` is fixed at the far right when workload exists.

Search does not move above, below, or to the opposite side between routes. At a
compact breakpoint it collapses to an icon/`Command-K` affordance instead of
wrapping. Studio and Messenger are the two immersive shell exceptions. Studio
follows the workbench contract in
`CONTROL_CENTER_RENDER_REVIEW_REVISION_02.md`; Messenger follows
`control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md`.

### Persistent UAA composer and sidecar

Almost every route includes one application-level UAA composer. It is a shared
shell component, not forty unrelated chat boxes.

- Standard placement: a 48-56 px composer integrated into the bottom
  application rail; it may expand upward without moving the route header.
- Invocation: click the composer or use `Command-K`, which unifies route search,
  settings search, navigation, questions, and proposals.
- Default prompt: `Ask UAA about this screen, find something, or propose a next
  step...`.
- Route-aware prompts may be more specific, such as `Ask about this board...`
  or `Search settings or ask UAA...`.
- Current-context indicator shows route, selected item count, and safe context
  refs. Context is removable before submit.
- Context may contain backend-owned safe refs, current route, selected record
  refs, filter state, and explicit bounded summaries. It may not scrape raw DOM
  text, attach raw screen pixels, or silently include raw prompts, responses,
  file contents, paths, logs, contact details, credentials, or provider data.
- Answers, navigation, and filters may occur directly when they are read-only
  presentation behavior.
- Requests to change state become a clearly labeled proposal, preview, or exact
  action envelope. They do not bypass policy, LocalApprovalAuthority,
  AuthorityLease, idempotency, receipts, safe-disable, rollback, CLI/API parity,
  or route side-effect classification.
- The composer expands into a consistent right-side UAA sidecar containing the
  conversation, included context, proposed next steps, and related evidence.
- The dedicated Chat route remains the full conversation/history workspace.
- The composer rail keeps one compact persistent posture control visible:
  `Local only · External actions blocked · Private`. Selecting it opens a
  `Privacy & authority` popover with `No connector writes`, `No provider
  authority`, `Safe refs only`, `Data stays on this Mac`, and `Proposals require
  approval`. The popover consolidates these facts without repeating the top
  authority strip.

In Settings, the composer is search-first. It returns matching settings,
explains current posture, navigates to the exact row, and can draft a supported
change. Unsupported or non-mutable settings return a truthful blocked or
planned result rather than a fake control.

### Product naming

Use `Control Center` in compact chrome and `Founder Command Center` when the
product context needs to be explicit. Do not alternate among `AI Agent Control
Center`, `Agent Control Center`, `AuthorityLease Control Center`, and other
generated names.

## Responsive Layouts

The product is macOS-first desktop software. Responsive support preserves the
same information architecture rather than shrinking the desktop canvas.

| Viewport | Required composition |
|---|---|
| Wide desktop, `>=1440` | Full rail, top strip, 2-3 workspace panes, optional bottom band |
| Compact desktop, `1280x800` | Full or icon rail; secondary inspector may become drawer; no lost commands |
| Narrow desktop/tablet, `1024x768` | Icon rail or drawer; one primary pane plus inspector drawer |
| Mobile proof, `390x844` | Navigation drawer; one pane at a time; sticky route header and action bar; inspector becomes full-screen sheet |

Mobile is an inspection and bounded-decision surface, not a compressed
three-column desktop. Dangerous, approval, rejection, safe-disable, and
rollback controls may not appear or disappear solely because of a breakpoint.

## Workspace Templates

Every route uses one of these component anatomies. A route may combine two
templates only when the mapped north-star render does so.

### A. Daily command deck

Used by Start Here, Today, Overview, Dashboard, Briefing, and Operator Loop.

- compact Morning Briefing and priority rail;
- one unified `Needs your attention` queue containing approvals, CRM follow-ups,
  Work Board blockers/movement, missing sources, memory conflicts, and stale or
  missing evidence;
- a clearly labeled selected-item inspector showing the selected signal's
  title, why it matters, linked plan/work item, relevant safe evidence,
  authority scope, and next safe step; compact layouts convert it to a drawer;
- a compact business pulse for CRM, Work Board, upcoming commitments, and
  evidence movement;
- a compact News module that separates sourced situational context from work
  requiring attention; current temperature, today's high, and conditions sit
  beside the Today title instead of consuming another card region;
- priorities and cross-surface decisions before low-level readiness;
- bottom receipts/evidence/heartbeat band when useful;
- no repeated dashboard card grid below the first viewport.

Today uses a single-canonical-home rule so cross-surface awareness does not
become repetition:

- Morning Briefing synthesizes what changed and what kind of day this is; it
  does not repeat module counts or queue rows.
- Needs your attention owns concrete approvals, blockers, conflicts, missing
  evidence, and overdue items.
- Today priorities owns planned work in intended execution order.
- News & Signals owns read-only outside context. Today projects at most three
  bounded News & Signals entries as
  summaries with an explicit source type (`Article` or `Email bulletin`),
  source label, freshness, and a safe reference to the underlying source.
  Weather shows only current temperature, today's high, and conditions beside
  the route title.
- Business pulse owns a compact set of non-actionable trend summaries and
  links to the canonical CRM, Work Board, commitment, or Evidence surface.
- Recent receipts appears as a compact full-width `Since your last check`
  activity rail below the six panels with a deep link to the receipt ledger;
  the rail does not count as a seventh panel.
- The inspector title is `Selected item` or the selected object's name.
  `Why it matters` is a subsection inside it, never an unexplained panel title.
- Other regions may show a count or deep link to the canonical home, but must
  not repeat the same full row, description, and status.

#### Today default composition and interaction

The default Today screen contains exactly six panels in an information-rich
three-column command deck: Morning Briefing, Needs your attention, and a
selected-item inspector on the first row; Day Plan, News, and Business pulse on
the second row. A compact full-width receipt/activity rail sits below the grid
and above the composer. Both rows use the same three column tracks so their
vertical boundaries align; use a `30 / 36 / 34` proportion, 14-16 px gutters,
consistent panel header heights, 12-16 px interior padding, and aligned footer
baselines. The relationships between modules must feel intentional rather than
like unrelated dashboard tiles. Selecting any row in the other five panels
updates the named inspector in place, and its safe ref is attached visibly and
removably to the persistent UAA composer. Compact layouts convert the inspector
to a drawer.

- Morning Briefing is read-only synthesis. Its rows open source/provenance
  detail but do not expose completion controls.
- Needs your attention rows open details and offer only type-correct actions:
  `Review`, `Resolve`, `Defer`, `Dismiss`, or `Ask UAA`. A signal is never
  labeled complete merely because the operator dismissed it.
- Day Plan owns `Now`, `Next`, meetings/commitments, and planned priorities.
  Its tasks may offer `Queue`, `Start`, `Defer`, and `Complete` only when the
  backing Python-core/API contract supports that exact transition.
- Today News rows may open the sourced detail, `Ask UAA`, save a safe reference for
  later review, or mute a source. News is not completable work.
- Business pulse rows open their contributing CRM, Work Board, commitment, or
  Evidence detail in the inspector. The separate activity rail opens receipt
  history.
- Compact overflow menus expose secondary actions; the row itself selects and
  opens detail. A chevron is reserved for navigation/disclosure and does not
  submit a change.
- Right-edge controls follow one grammar across all panels: a chevron selects
  and exposes detail, an outward arrow opens the canonical source, one named
  verb button offers the most likely safe action on the selected/hovered row,
  and an ellipsis opens type-correct secondary actions. Status pills remain
  read-only state labels.

The six panels absorb Today context without adding more permanent modules:
meetings and commitments live in Day Plan; urgent memory review and exceptional
weather/calendar conflicts enter Needs your attention; date and ordinary
weather remain in the header; freshness and confidence appear in News and the
inspector; continuity appears in Morning Briefing and Business pulse activity;
morning, midday, end-of-day, calm, overloaded, stale, and offline are content
states of this same layout rather than additional cards.

The header decision command names workload and urgency. When three decision
envelopes are pending, label it `Review 3 decisions`; never use the vague
`Review decisions`. When none are pending, remove the primary blue treatment
and show a quiet `No decisions pending` status or omit the command.

#### Truth-safe queue and completion contract

Display convenience cannot create product truth.

- `Queue` writes or proposes an exact backed plan/task transition; it is not a
  React-only list change. Show proposal, confirmation, receipt, or blocked
  posture according to the implemented lane.
- `Complete` is available only for an object with a defined completion
  transition and required evidence/receipt posture. The control opens a compact
  confirmation naming the object, completion meaning, source of truth, and any
  required proof before recording the change.
- When completion cannot be verified, use `Report complete` or `Mark for
  review`, visibly labeled as unverified, instead of `Complete`. A later source
  conflict reopens review; it never silently preserves a false green state.
- `Dismiss` means remove the signal from attention, not resolve its underlying
  source object. `Defer` records when it should return. `Resolve` requires the
  source's real resolved state or a receipt-backed local decision.
- Completed, user-reported, dismissed, deferred, blocked, and source-conflict
  states have distinct text and icon treatment. Green `Completed` requires the
  backing state plus its receipt or safe evidence reference.
- Every mutation remains exact-scoped, idempotent, auditable, redacted, and
  reload-verifiable. Mock or unavailable backing state never exposes a control
  that can claim completion.

#### Today News and Weather contract

The module is a target product contract, not a grant of live network or
connector authority. Weather is a compact title-line status. The News module
contains at most three ranked summaries so it does not displace operator work.

- Article discovery and retrieval must use an exact, governed, read-only
  `WebAccessGateway` lane when that lane is implemented. Fetched content is
  untrusted evidence and cannot issue instructions or directly trigger work.
- Email bulletins must use a separately accepted read-only email-source lane.
  The Today module shows a bounded redacted summary and safe source reference,
  never a raw message body, account identifier, or write control.
- Every news row must expose source type, human-readable source label,
  freshness, and a source/detail affordance. Unsourced summaries are blocked
  from the assembled state.
- The module distinguishes `loading`, `ready`, `mixed sources`, `stale`,
  `partially blocked`, `blocked`, `empty`, and `error` states. A blocked source
  remains visibly blocked rather than being presented as current.
- Weather uses a configured read-only source and does not infer or persist a
  private location from IP or hidden account data. Its visible payload is
  limited to current temperature, today's high, and conditions; stale or
  unavailable data carries an explicit status.
- News is situational context, not another attention queue or business pulse.
  If an item becomes actionable, UAA may propose a linked plan or action through
  the existing governed proposal flow; the module itself does not mutate state.

#### News & Signals front-page contract

The canonical `/news` workspace is a personalized news front page rather than
an analytics dashboard, attention queue, or endless generic feed. Its default
desktop hierarchy is:

1. familiar category navigation;
2. `Top stories for you` with visible source and freshness;
3. a bounded, paginated `Morning Brief queue` with a stable path to the full
   Morning Briefing;
4. source-specific scanner and subscription previews;
5. source readiness and coverage posture.

The default categories include Top, AI, Technology, Business, Politics, World,
Sports, Science, and Culture. Later user-configured categories may extend this
set. Category grouping and source grouping are separate dimensions: categories
answer what a story is about, while Source Feeds answers what an exact watched
source found.

Source-specific previews may name Reddit findings, watched public X accounts,
email newsletter bulletins, Discord channels, RSS feeds, official blogs,
YouTube channels, podcasts, and later exact adapters. These names define visual
slots and product taxonomy only. The UI must show blocked, missing, stale,
partial, fixture-only, or unsupported posture per adapter and may not imply an
account, authenticated session, scraper, connector, browser, or background
poller exists.

Every top-story or source-feed row preserves a human-readable source label,
category when applicable, freshness, content type, and safe detail path. The
reason an item is personalized remains inspectable. Source-specific `View all`
paths must not erase source identity by flattening every item into one opaque
cluster.

Morning Briefing receives only a bounded selected projection. Pagination
browses the candidate pool; it does not add every item to the brief. `Open full
Morning Briefing` remains visible independently from pagination. News & Signals
does not own tasks, approvals, messages, or owned-channel social performance.
Social retains owned-channel performance and audience interpretation.

The accepted desktop reference is
`control_center_north_star/renders/news-signals-v1/01-news-signals-home.png`,
with the truth contract in the adjacent `README.md`. The current `/news`
implementation may remain partial or sample-only until separately implemented,
tested, and promoted.

### B. Queue, detail, inspector

Used by Action Inbox, Approvals, Memory, Files, File Review, Context Proposals,
Action Preview, Proof, Receipts, and Events.

- queue/list on the left;
- selected work in the center;
- authority, provenance, proof, rollback, or related context on the right;
- selected row has a strong but quiet blue outline/background;
- no selection shows a purposeful empty inspector, not a blank panel.

### C. Board and planning canvas

Used by Plans, Work Board, and CRM pipeline views.

- plan/list context at left or in route-local tabs;
- bounded horizontal board/canvas in the center;
- selected-item inspector at right;
- board columns scroll internally;
- drag/move preview, dirty state, confirmation, persistence result, and reset
  remain visually distinct.
- Work Board column accents identify status and a narrow card edge plus label
  identifies priority. An explicit Group/Color selector chooses Status,
  Priority, or Project grammar; color is never the only signal.

### D. Matrix and settings cockpit

Used by Trust, Settings, Models, Capabilities, and future-domain governance.

- stable category list or matrix rows;
- status cells use text plus icon/color;
- mutation controls appear only for implemented exact lanes;
- unsupported settings are status rows, not disabled fake toggles;
- consequential changes show scope, confirmation, saving, receipt, and reload
  impact.
- Activity & Trust provides a dedicated Trust cockpit with mode/domain matrix,
  exact lease, live policy decisions, receipts/audit refs, revoke/pause/kill,
  and safe-disable posture.

### E. Ledger and system inventory

Used by Evidence, Foundation Gate, API Routes, Timeline, Differentiators,
Storage, Runtime, and Manual Smoke.

- table/list is primary;
- summary counts stay compact;
- filters do not consume a full row when fewer than four choices exist;
- detail/trace is an inspector or selected lower pane;
- raw JSON is never the primary representation.

### F. Conversation and handoff

Used by Chat and related handoff views.

- contained thread list;
- contained message history;
- composer anchored at the bottom;
- Automatic versus Specific Model uses real selector semantics;
- actual route/model used appears after a response;
- plan, action, memory, and evidence handoffs are explicit proposal tabs in an
  inspector, never hidden side effects.
- route-local UAA sidecars use this same conversation and handoff anatomy so a
  question started on Today can inspect a Work Board or CRM safe ref and remain
  coherent when opened in the full Chat route.

### G. Setup and readiness

Used by Setup, Local Runtime, Remote Workers, Mobile Planning, Plugin
Governance, and Private Trial.

- ordered steps or candidate list;
- current step in the main pane;
- readiness/blockers in the inspector;
- manual commands, proof, and redacted evidence in a bottom band;
- planned steps look planned, never like clickable disabled commands.

## Visual Tokens

### Color

Use true white panels on a cool light-gray canvas. Do not warm the palette to
cream or beige.

| Token | Value | Use |
|---|---|---|
| `canvas` | `#f5f7fa` | workspace background |
| `surface` | `#ffffff` | panels, menus, drawers |
| `surface-subtle` | `#f8fafc` | selected subregions, table headers |
| `rail` | `#12212f` | navigation rail |
| `rail-active` | `#28445c` | active nav row |
| `text` | `#1f2933` | primary text |
| `text-strong` | `#102a43` | titles and selected values |
| `text-muted` | `#52606d` | secondary copy |
| `border` | `#d9e2ec` | standard separators |
| `border-strong` | `#bcccdc` | active structure |
| `accent` | `#2563eb` | selection, primary informational action |
| `info` | `#0b69a3` | read-only/info posture |
| `receipt` | `#2f855a` | happened/verified/recorded |
| `ask` | `#d97706` | approval/partial/caution |
| `danger` | `#d64545` | denied/blocked/destructive |
| `planned` | `#829ab1` | planned/unsupported/inactive |
| `focus` | `#2563eb` | 2 px focus ring plus 2 px offset |

Status backgrounds use 6-10% tints of the semantic foreground. Do not fill
large panels with saturated status color.

### Typography

Font stack:

`Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

Monospace is reserved for copied refs, hashes, commands, and operation IDs.

| Role | Size / line height | Weight |
|---|---|---|
| Surface title | `24 / 32` | 650 |
| Section title | `18 / 24` | 650 |
| Panel title | `15 / 21` | 650 |
| Body | `14 / 20` | 400 |
| Dense row | `13 / 18` | 450 |
| Secondary | `12 / 17` | 400 |
| Control label | `13 / 16` | 600 |
| State label | `11 / 14` | 650 |
| Safe ref | `12 / 16` | 500 monospace |

No viewport-scaled typography, negative tracking, hero-scale application
titles, or browser-default control type.

### Spacing, radius, elevation

- spacing scale: `4, 8, 12, 16, 24, 32` px;
- panel padding: 16 px compact, 20 px standard;
- workspace padding: 24 px standard, 16 px compact desktop;
- panel radius: 8 px maximum;
- control/nav radius: 6 px maximum;
- chips: 4-6 px radius; use capsule pills only for short state labels;
- shadows: none for ordinary panels; subtle single shadow for menus, drawers,
  command palette, dialogs, and floating inspectors;
- borders and whitespace establish hierarchy before shadows.

### Icons

Use the repo's `NorthStarIcon` family or a reviewed extension of it. Icons are
16 px in controls, 18 px in navigation, and 20-24 px only for major state
markers. Use a consistent 1.75-2 px stroke, rounded joins, and `currentColor`.
Do not use emoji, text glyph arrows, or mixed filled/outline families.

## Status And Authority Grammar

Every state includes visible text. Color and icons reinforce meaning.

| State | Visual treatment | Required operator meaning |
|---|---|---|
| Read-only | quiet blue/gray | inspection only; no mutation |
| Proposal-only | amber | draft or proposal; no receipt yet |
| Approval required | amber, stronger border near action | exact decision needed before the lane may proceed |
| Receipt-backed | green | a bounded event or decision was recorded |
| Success/ready | green | the scoped check or read model succeeded |
| Partial/degraded | amber | usable subset; name what is missing |
| Blocked/denied | red | unavailable under current policy; explain next safe lane |
| Planned/unsupported | gray | future or absent; not an interactive control |
| Mock fallback | amber banner | demo/non-authoritative; cannot prove state |
| Error | red alert | sanitized failure plus retry or inspection path |
| Stale | amber/red based on consequence | freshness problem; canonical source outranks it |

`Connected`, `online`, `healthy`, and `ready` never imply authority or
production readiness. Approval refs are identifiers until exact backend scope
is validated. Receipts describe past work and do not authorize future work.

## Control Semantics

- Buttons run explicit commands and use verbs.
- Links, tabs, rail items, and breadcrumbs navigate.
- Selects/radios/segmented controls choose values or modes.
- Toggles represent implemented binary settings only.
- Search plus compact chips filters collections.
- Static posture uses text/status rows, never disabled toggles or button-shaped
  values.
- A chevron means disclosure or navigation consistently; it never means
  submit.
- Save/apply controls are disabled until dirty, confirm consequential changes,
  show progress, expose a safe success/failure result, and reload persisted
  state.
- Every unavailable control has an adjacent reason and a separate remediation
  path when one exists.
- `Customize sidebar` changes navigation presentation. It never uses `Enable`,
  `Disable`, or authority terminology.
- Compact rail mode preserves order, badges, active state, accessible names,
  tooltips, focus-visible labels, and bottom Settings/Developer Tools anchors.
- The UAA composer distinguishes `Search`, `Go to`, `Ask`, `Filter`, `Draft`,
  and `Propose` intent before any operator-relevant mutation path is offered.

## Required Interaction States

Every applicable component and route render covers:

- default;
- hover and focus-visible;
- selected;
- empty/no selection;
- loading;
- partial/degraded;
- blocked/disabled with reason;
- validation error;
- network/runtime error;
- dirty/unsaved;
- confirmation;
- busy/submitting;
- cancelled;
- saved/receipt recorded;
- reloaded persisted state;
- mock fallback where the route supports it.

These are equivalence classes, not a mandate to render every combinatorial
permutation. Every route gets a canonical default desktop and compact-desktop
render. Shared state boards define generic states; route-specific renders are
required when the state changes layout, authority, copy, or available actions.

## Content And Copy Rules

- Lead with the user concept and human-readable label.
- Put stable internal refs behind `Details`, copy buttons, tooltips, inspectors,
  or a diagnostics disclosure.
- Keep route status explanations to one sentence plus one next safe action.
- Do not show raw paths, prompts, responses, provider payloads, logs,
  credentials, environment dumps, private account/contact data, or secrets.
- Truncate long safe refs visually while preserving copy/accessibility access.
- Use `Review`, `Preview`, `Validate`, `Inspect`, `Save`, `Reject`, `Defer`,
  `Restore`, and other exact verbs.
- Do not label a preview-only control `Run`, `Execute`, `Send`, `Connect`,
  `Install`, `Sync`, `Commit`, `Publish`, or `Approve` unless the exact current
  backend lane supports that action and the screen clearly shows its scope.

## Accessibility

- WCAG 2.2 AA contrast for text and controls;
- semantic landmarks and heading order;
- one visible `h1` or route title per workspace;
- complete keyboard operation for navigation, queues, boards, dialogs, and
  forms;
- 2 px visible focus ring, never color-only selection;
- live regions for loading/saving/success and alerts for actionable failure;
- dialogs trap focus and restore it to the invoking control;
- drag/drop has keyboard move parity;
- tables retain headers and accessible row names;
- reduced-motion is respected;
- 44 px minimum target on touch/mobile, while desktop controls may remain
  32-36 px with adequate spacing.

## Motion

Motion is restrained and functional:

- 120-160 ms for hover/selection;
- 180-220 ms for drawer/dialog transitions;
- no background animation, parallax, bounce, or decorative loading loops;
- progress indicators do not imply work has started before backend acceptance;
- `prefers-reduced-motion` removes nonessential transitions.

## Render Production Contract

The complete artifact queue is defined in
`control_center_north_star/RENDER_VARIATION_MATRIX.md`.

Render rules:

1. Use the same shell, tokens, typography, icon language, and pane geometry in
   every render.
2. Use synthetic, sanitized, safe-ref-only example data.
3. Preserve current implemented/partial/blocked truth; do not promote planned
   authority for visual drama.
4. Render code-native text and controls as if they will be implemented in
   React; do not rely on raster text as product implementation.
5. Produce default desktop first, then compact desktop, route-specific state
   variants, mobile proof, and shared overlay/state boards.
6. Every artifact records render ID, route, viewport, scenario, source data
   posture, current-as-of date, and approval state.
7. Approved renders become the visual contract. Later implementation cannot
   creatively reinterpret them.

## Pixel-Fidelity Implementation Contract

After render approval:

- capture implementation at the render's exact viewport;
- lock browser engine, zoom, device scale factor, fonts, animation state, time,
  and sanitized fixture/backend scenario;
- compare concept and implementation with image overlays and pixel diffs;
- match shell geometry, panes, typography, palette, spacing, borders, radii,
  icons, selection, scroll containment, and control states;
- allow copy and value differences only where real backend context requires
  them; surrounding geometry and component behavior remain faithful;
- document every intentional deviation with the exact product or accessibility
  constraint;
- do not mask entire dynamic regions merely to obtain a passing diff.

Acceptance target:

- no unexplained structural or visual mismatch;
- no clipped or overlapping content;
- no unintended page scrolling at desktop targets;
- no relevant console errors;
- no fake/dead controls;
- all commands and selectors match their semantics;
- same screenshot pair reviewed with `view_image` before sign-off.

## Three-Pass Polish Gate

After every real surface matches its approved render, run the
`polish-ui-ux-gui` workflow three separate times.

1. **Pass 1 — Structure and semantics:** shell, hierarchy, control meaning,
   fake/dead controls, state ownership, scroll containment.
2. **Pass 2 — Visual fidelity and responsive quality:** concept comparison,
   typography, icons, spacing, density, mobile/compact behavior, overflow.
3. **Pass 3 — Interaction and release polish:** keyboard/focus, dirty/loading/
   error/success/reload paths, network patch scope, console health, final image
   comparison.

Each pass starts only after all findings from the previous pass are fixed and
reverified. A pass with unresolved findings does not count. The three reports
must be separate artifacts with their own screenshots, mismatch ledger, tests,
and completion result.

## Change Control

Changing this spec, an approved render, or a pixel-matched surface requires:

- the affected route and state variants;
- the reason for the change;
- product/authority impact review;
- updated render or accepted no-render rationale;
- updated visual baseline and focused tests;
- no silent drift between spec, render, and implementation.
