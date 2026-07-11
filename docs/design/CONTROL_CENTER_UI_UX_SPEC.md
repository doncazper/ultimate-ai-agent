# Control Center UI/UX Specification

Status: canonical design contract, documentation only  
Specification ID: `CC-UIUX-2026-07-11`  
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

The daily product spine is:

`Start Here -> Today -> Plans/Work Board -> Action Inbox -> Proof/Evidence -> Memory Review -> Weekly Review`

Source Inbox, CRM, Chat, Coding, Files, Runtime, and Settings feed or govern
that spine. They must not become unrelated diagnostic islands.

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

Always-visible Founder Loop order:

1. Start Here
2. Today
3. Source Inbox
4. Plans
5. Work Board
6. Action Inbox
7. Proof
8. Trust
9. Memory
10. Evidence
11. Settings

Supporting surfaces live in stable collapsed groups or the command palette.
Their membership and order are deterministic. Route-local tabs never enter the
global rail. One item, and only one item, has `aria-current="page"`.

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

- compact summary/next-step rail;
- 2-3 balanced work regions;
- priorities and decisions before low-level readiness;
- bottom receipts/evidence/heartbeat band when useful;
- no repeated dashboard card grid below the first viewport.

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

### D. Matrix and settings cockpit

Used by Trust, Settings, Models, Capabilities, and future-domain governance.

- stable category list or matrix rows;
- status cells use text plus icon/color;
- mutation controls appear only for implemented exact lanes;
- unsupported settings are status rows, not disabled fake toggles;
- consequential changes show scope, confirmation, saving, receipt, and reload
  impact.

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

