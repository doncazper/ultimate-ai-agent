# Control Center App Shell Baseline

Status: current target shell baseline, documentation only.
Baseline ID: CC-NS-TARGET-R2-2026-07-11.
Current as of: 2026-07-11.
Repo baseline: v0.104.0 / 0.104.0.

This file is the source of truth for the static Control Center shell used by
the north-star renders. If a generated render shows a different left rail,
different tab order, different typography, or a route-specific sidebar, this
baseline wins.

This file does not change frontend behavior, route contracts, runtime
authority, approval behavior, or product readiness. It defines the visual
target for implementation and future render generation.

## Static App Shell

The Control Center uses one persistent shell across the app:

- fixed left navigation rail;
- persistent top status and authority strip;
- bounded route workspace;
- optional bottom evidence/receipt band;
- route-local panes, tabs, queues, and inspectors inside the workspace only.

The left rail must not be replaced by route-specific navigation. Route-specific
navigation belongs in the route workspace as tabs, split-pane lists, segmented
controls, or inspectors.

## Canonical Left Rail

The target product rail below is governed by
`../CONTROL_CENTER_PRODUCT_IA_AND_CALENDAR_CONTRACT.md`. The current route
registry in `apps/control-center/src/routes.tsx` remains implementation truth
until consolidation is separately implemented. The operator may customize
which middle workspaces are pinned and their pinned order without changing
route availability, capability state, authority, or the resettable default.

### Primary workspaces

1. Today
2. Communications
3. Work Board
4. CRM
5. Calendar
6. News
7. Studio

Today is fixed first and is the default landing workspace. Communications,
Work Board, CRM, Calendar, News, and Studio may be reordered or hidden as presentation
preferences without disabling their routes or capabilities.

### Supporting workspaces and utilities

The stable supporting section is:

1. Knowledge
2. Activity & Trust

The stable lower utilities are:

1. Customize
2. Settings
3. Developer Tools, collapsed and hidden by default

Current Memory and Files concepts consolidate under Knowledge. Receipts,
Evidence, Proof, Trust, Events, and Approvals consolidate under Activity &
Trust. Runtime, Models, Storage, API Routes, Foundation Gate, Plugins, setup
diagnostics, and other technical routes consolidate under Developer Tools.
`Start Here` becomes onboarding-only after setup. Plans becomes a Work Board
view; Source Inbox becomes a Communications view; Chat and Coding become
Studio modes.

Action Inbox is a global decision utility reached through `Review N decisions`,
attention items, command search, and Activity & Trust. It is not a permanent
primary rail item. With no pending decisions the CTA is demoted or omitted.

## Rail Behavior

- Active route: one active item only.
- Active supporting route: highlight it in the supporting section and keep the
  primary list unchanged.
- Route-local tabs must not be added to the global rail.
- Disabled, planned, blocked, partial, experimental, and mock-only states may
  appear as compact state labels, but state labels must not change item order.
- The rail may collapse to icons at compact desktop widths only when the same
  item order and route reachability are preserved. Icon-only mode provides
  tooltips, accessible names, focus-visible labels, badges, and active state.
- The rail may expose overflow through a stable "More" or command-palette
  affordance only when the hidden list remains deterministic.
- `Customize sidebar` may pin, unpin, reorder, collapse, change density, cancel,
  or restore defaults. Use visibility/pinning language, never capability
  enable/disable language.
- Hidden surfaces remain reachable from `All surfaces`, the UAA composer,
  command search, and direct navigation.
- Global safety posture, blockers, and approval controls are not customizable
  navigation items and cannot be hidden through rail preferences.

## Persistent UAA Composer

The standard shell includes the shared UAA composer defined by
`../CONTROL_CENTER_UI_UX_SPEC.md`. It occupies the bottom application rail,
uses safe route/selection context only, and expands into a consistent sidecar.
It does not replace the dedicated Chat workspace or grant mutation authority.

## Standard Desktop Layout

Target viewport: 1440 x 900. The saved render assets are 1586 x 992 and should
be treated as high-resolution 16:10-ish approximations of that target.

| Token | Target |
|---|---|
| App shell | full-window grid, no page-like document canvas |
| Left rail width | 260 px standard, 72 px collapsed only by explicit breakpoint |
| Top strip height | 72-84 px |
| Workspace padding | 24-32 px |
| Panel gap | 16 px |
| Panel radius | 8 px maximum |
| Nav item radius | 6 px maximum |
| Button/control radius | 6 px maximum |
| Bottom evidence band | 96-144 px when present |
| Dense table row | 36-44 px |
| Inspector width | 320-380 px |
| Queue/list pane width | 260-340 px |

The window may contain internal pane scrolling where needed, but the primary
route composition should not read as an endless page. Fixed pane headers and
bounded ledgers are preferred over full-page vertical scroll.

## Typography

Typography should stay close to the current Control Center CSS and use a
system-native professional rhythm.

Font stack:

```text
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

Monospace stack for refs, command names, hashes, and safe identifiers:

```text
ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace
```

| Use | Size | Line height | Weight |
|---|---:|---:|---:|
| Surface title | 24 px | 30-32 px | 650 |
| Top-strip status | 13 px | 18 px | 500 |
| Section heading | 18 px | 24 px | 650 |
| Panel title | 15-16 px | 20-22 px | 650 |
| Body text | 14 px | 20 px | 400 |
| Dense table text | 13 px | 18 px | 400-500 |
| Secondary text | 12-13 px | 16-18 px | 400 |
| Eyebrow/state label | 11-12 px | 14-16 px | 650 |
| Primary nav label | 14 px | 18 px | 600 |
| Nav status sublabel | 11-12 px | 14-16 px | 400 |
| Button label | 13 px | 16 px | 600 |
| Safe ref/code label | 12 px | 16 px | 500 |

Rules:

- Do not scale font size with viewport width.
- Letter spacing is 0 except for short all-caps section labels, where it may
  be subtle and must remain readable.
- Text must not overlap icons, chips, adjacent columns, or following content.
- Prefer truncation with tooltips for safe refs and long route metadata.
- Avoid hero-scale type inside panels, sidebars, queues, tables, and cockpit
  surfaces.

## Color And State Grounding

Use the existing Control Center palette as the grounding layer:

| Role | Color |
|---|---|
| App background | `#f5f7fa` |
| Panel background | `#ffffff` |
| Sidebar background | `#12212f` |
| Sidebar active | `#28445c` |
| Primary text | `#102a43` or `#1f2933` |
| Secondary text | `#52606d` |
| Border | `#d9e2ec` |
| Info/accent | `#0b69a3` |
| Ready/receipt | `#2f855a` |
| Ask/partial/warning | `#f0b429` |
| Denied/error | `#d64545` |
| Planned/unsupported | `#9fb3c8` |

State must use text plus color. Color alone is not enough for authority,
approval, readiness, or failure states.

## Date And Currency Rules

Every render set must have:

- a baseline ID;
- a current-as-of date;
- a repo baseline;
- a route coverage map;
- an app shell baseline;
- a render manifest.

This render set is current until a later dated baseline supersedes it. New or
regenerated renders should either preserve `CC-NS-2026-07-06` or create a new
dated baseline and update this package.

## Future Render Prompt Requirements

Future standard-shell render prompts must explicitly include:

```text
Use the CC-NS-TARGET-R2-2026-07-11 app shell.
The standard left rail is identical across normal routes.
Primary nav order: Today, Communications, Work Board, CRM, Calendar, News,
Studio, Knowledge, Activity & Trust, Customize, Settings, Developer Tools.
Do not add route-local tabs to the global left rail.
Place route-local tabs and queues inside the workspace.
Keep search in the fixed standard toolbar slot and Review N decisions at right.
Use Inter/system typography and the CC-NS-TARGET-R2-2026-07-11 size scale.
```

Studio is the explicit immersive exception: it replaces the ordinary rail with
the UAA Studio workbench rail and provides a visible Back to Control Center
command.

Generated images are allowed to be visually approximate, but implementation
must follow this baseline where generated pixels conflict with the spec.
