# Control Center North-Star Render Manifest

Status: current target render set, documentation only.
Baseline ID: CC-NS-TARGET-R6-2026-07-13.
Current as of: 2026-07-13.
Repo baseline: v0.104.0 / 0.104.0.

Machine-readable currentness: `CURRENT_RENDER_BASELINE.json`.

The renders were generated as UI mockups for the Control Center target
direction and then copied into this repository as design artifacts. They should
be treated as visual targets and alignment aids, not shipped UI screenshots.

The separate ECO-000 planning-only extension is indexed at
`../ecosystem_north_star/RENDER_MANIFEST.md`; those SVG drafts do not alter the
accepted shell or count as shipped UI evidence.

`APP_SHELL_BASELINE.md` is the normative target shell specification for left-rail
order, route stability, typography, spacing, and state treatment. The PNGs are
not normative when their generated sidebar details conflict with that file.

## Target V1 Defaults

These 14 drafts cover every target top-level workspace, lower utility, and
global workflow surface. The current 40-route implementation remains covered by
the legacy composites and route matrix below; consolidation in a render is not
evidence that consolidation is implemented.

| File | Target surface | Required integration | Must not imply |
|---|---|---|---|
| `renders/target-v1/01-today.png` | Today | briefing, attention, selected detail, Day Plan, news, business pulse, receipts, UAA | duplicated truth or hidden authority |
| `renders/target-v1/02-communications.png` | Communications | email/messages/follow-ups, CRM, Work Board, event proposal | send or connector write |
| `renders/target-v1/03-work-board.png` | Work Board | plans, CRM, Calendar, Communications, evidence | optimistic completion or broad mutation |
| `renders/target-v1/04-crm.png` | CRM | relationships, activity, commitments, schedule proposal | raw contact data or connector sync |
| `renders/target-v1/05-calendar.png` | Calendar | schedule, tasks, CRM, source-backed candidate, conflict checks | candidate as committed or externally synced |
| `renders/target-v1/06-studio.png` | Studio | Chat/Code, diff, context, checks, evidence | arbitrary shell, deploy, or model authority |
| `renders/target-v1/07-knowledge.png` | Knowledge | memory, files, context, provenance, review | memory as truth or automatic injection |
| `renders/target-v1/08-activity-trust.png` | Activity & Trust | receipts, evidence, decisions, authority, proof | audit as execution authority |
| `renders/target-v1/09-customize.png` | Customize | reorder, show/hide, density, preview | capability enable/disable |
| `renders/target-v1/10-settings.png` | Settings | search, preferences, posture, governed settings | unsupported live controls |
| `renders/target-v1/11-developer-tools.png` | Developer Tools | runtime, models, storage, API/gate, plugins, diagnostics | production or unrestricted authority |
| `renders/target-v1/12-decision-review.png` | Decision Review | exact envelope, consequences, receipt, outcomes | approval ref as execution authority |
| `renders/target-v1/13-onboarding.png` | Onboarding | local readiness, read-only source posture, safety defaults | connected providers or production readiness |
| `renders/target-v1/14-uaa-sidecar.png` | UAA Sidecar | safe context, explanation, proposal handoff | DOM scraping or direct mutation |

All target V1 entries begin as `Draft`. Critique, status, and version history
are managed locally by `render-review/renders.json` and the review gallery.

## Today Shell Explorations

The four non-destructive Today iterations below preserve the refinement trail.
The later six-panel `renders/target-v1/01-today.png` composition is the current
review target for the 2026-07 period; `current` here means preferred draft for
critique, not approved or implemented.

| File | Status | Period |
|---|---|---|
| `renders/drafts/CC-R2-SHELL-01-today-desktop-default-v1.png` | Preserved draft | 2026-07 |
| `renders/drafts/CC-R2-SHELL-01-today-desktop-default-v2.png` | Preserved draft | 2026-07 |
| `renders/drafts/CC-R2-SHELL-01-today-desktop-default-v3.png` | Preserved draft | 2026-07 |
| `renders/drafts/CC-R2-SHELL-01-today-desktop-default-v4.png` | Preserved draft | 2026-07 |
| `renders/target-v1/01-today.png` | Current draft | 2026-07 |

## Revision 02 Drafts

Revision 02 preserves every V1 file and adds the accepted review corrections.

| File | Surface/version | Required change | Must not imply |
|---|---|---|---|
| `renders/target-v2/03-work-board-v2.png` | Work Board v2 | status column bars; priority card edges; visible legend | color-only meaning or rainbow cards |
| `renders/target-v2/04-crm-v2.png` | CRM v2 | availability-backed Call chooser; exact review; general placeholder | provider connected or call completed |
| `renders/target-v2/06-studio-v2.png` | Studio v2 | immersive familiar workbench; back path; optional drawer; Terminal | arbitrary shell, deploy, or model authority |
| `renders/target-v2/15-news-v1.png` | News v1 | curated sourced brief; freshness; why selected; saved/source controls | unrestricted fetch or unsourced ranking |
| `renders/target-v2/16-trust-v1.png` | Trust v1 | authority matrix; exact lease; live decisions; revoke/pause/kill/safe-disable | matrix as authority grant |
| `renders/target-v2/17-terminal-v1.png` | Terminal v1 | exact command lanes; redacted output; receipts; pop-out | unrestricted shell or raw environment |
| `renders/target-v2/18-compact-shell-v1.png` | Compact shell v1 | same nav as icons; tooltip/focus labels; fixed utilities | hidden routes or changed capability |

## CRM Revision 03

CRM v3 preserves the v1 general workspace and v2 governed-call concept while
replacing the provisional layout with a compact, general-purpose relationship
operating surface. The reference synthesis and locked design rules are recorded
in `CRM_V3_REFERENCE_SYNTHESIS.md`.

| File | Surface/version | Required change | Must not imply |
|---|---|---|---|
| `renders/target-v3/04-crm-v3.png` | CRM v3 | fixed toolbar; route tabs; six KPIs; smart views; sortable relationship table; persistent inspector; pipeline analytics; availability-backed calling; route-aware UAA composer | specialty vertical; raw contact data; provider connection; sync; dialer launch as completed call; recording by default |

## Studio Unified Revision 05

Unified Studio v7 supersedes the separate Agent Studio / Creative Studio split.
One `UAA Studio` identity now exposes exactly three persistent modes: Chat,
Code, and Create. The refined geometry narrows the Studio rail to 220 px and the
Create presentation strip to 96 px so the center work surface remains dominant.
The normative purpose and ownership contract is
`../STUDIO_TAB_PRODUCT_DIRECTION.md`.

| File | Surface/version | Required change | Must not imply |
|---|---|---|---|
| `renders/target-v3/06-studio-unified-v7.png` | Unified Studio v7 | one Studio identity; persistent Chat/Code/Create mode rail; 220 px rail; flexible center; fixed 350 px inspector; 96 px Create thumbnail strip; mode ownership; proposal composer; blocked export; visible no-runtime-authority posture; full-width status bar | modes as authority; implemented model/runtime/export/publish/deploy/delivery; approval bypass; or implementation evidence |

The following sanitized screens remain preserved comparison artifacts and no
longer define separate current workspaces:

| File | Preserved exploration | Status |
|---|---|---|
| `renders/target-v3/06-agent-studio-v5.png` | coding-only fixed-pane Studio | superseded by unified v7 |
| `renders/target-v3/06-creative-studio-v2.png` | creative-only presentation Studio | superseded by unified v7 |

### Skill Workbench Create surface

The Skill Workbench grid and list views are accepted Create-mode sub-surfaces.
The list is the default view, uses 25-row pagination, and omits both speculative
risk and repeated license columns. Source-provided license detail remains in the
selected-item inspector.
Source rank, stars, downloads, comments, and future ratings remain distinct
discovery signals. Missing ratings render as unavailable, not zero.

| File | Surface/version | Required change | Must not imply |
|---|---|---|---|
| `renders/target-v3/07-skill-workbench-grid-v1.png` | Skill Workbench grid v1, Hermes filter | compact discovery cards; honest missing source scores; metadata-only and review posture; selected inspector | live marketplace fetch, trusted popularity, imported code, install, or execution |
| `renders/target-v3/08-skill-workbench-list-v1.png` | canonical Studio dense-workbench reference | dense rows; complete primary values; natural category/rank wrapping; whole-column compact reduction; list/grid toggle; 25-row pagination; source-specific missing values; no license column; inspector detail | clipped primary signals, pill-shaped metadata, invented average ratings, guessed risk, source signal as UAA trust, or adaptation authority |

## Messenger Matrix Client V1

The 15-image `communications-v1` set defines the clean-room,
Element-familiar UAA Messenger workspace. It includes the two-Space model, daily
conversation surfaces, room management, account security, UAA intelligence,
failure recovery, dark appearance, and later calling preflight. See
`UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md` for the complete surface and truth
contract. MSG-MX-001 accepts all fifteen as desktop target renders, with the
normal/narrow desktop and command-truth constraints in
`UAA_MESSENGER_MATRIX_RENDER_ACCEPTANCE.md`. These images do not claim any
current Matrix runtime.

## Social Media Intelligence V1

The four-image `social-media-v1` set records the accepted planning-only creator
intelligence direction and its projections into existing application owners.
It is dependency-gated behind accepted completion of Work Board/Kanban,
first-class CRM, and Communications/Messenger.

| File | Surface/version | Required relationship | Must not imply |
|---|---|---|---|
| `renders/social-media-v1/01-social-command-view.jpg` | Social command view v1 | interpret performance, audience, campaigns, cadence, and conversation signals | implemented route, live accounts, connector reads, publishing, or replies |
| `renders/social-media-v1/02-calendar-social-publishing-view.jpg` | Calendar Social publishing v1 | Calendar retains schedule ownership | external scheduling or a second calendar |
| `renders/social-media-v1/03-work-board-social-content-view.jpg` | Work Board Social Content v1 | Work Board retains production ownership | a second Kanban engine or copied task truth |
| `renders/social-media-v1/04-communications-social-media-view.jpg` | Communications Social Media v1 | Communications retains conversation ownership | live threads, sends, replies, or moderation |

See `renders/social-media-v1/README.md` for locked labels, ownership, and the
future implementation gate. These renders are concept artifacts, not current
Control Center screenshots or implementation evidence.

## Legacy Composite Coverage

| File | Covered surfaces | Must show | Must not imply |
|---|---|---|---|
| `renders/01_today_command_center.png` | Today, daily loop, Morning Briefing pulse | Briefing, priorities, approvals, memory, evidence, source blockers | Hidden authority, endless feed, connector writes |
| `renders/02_action_inbox_approval_envelope.png` | Action Inbox, Approvals | Queue, exact envelope, policy decision, receipt posture | Approval ref as execution authority |
| `renders/03_plans_work_board.png` | Plans, Work Board | Plan outline, kanban, action envelope, rollback/evidence links | Unapproved mutation or broad board authority |
| `renders/04_trust_authority_lease.png` | Trust, AuthorityLease | Mode/domain/lease matrix, ask/deny/degrade, kill switch | Broad global autonomy toggle |
| `renders/05_evidence_proof_receipts.png` | Evidence, Proof, Receipts | Timeline, proof detail, receipt ledger, rollback/safe-disable | Raw logs or execution permission |
| `renders/06_memory_review_context_manifest.png` | Memory | Review decisions, provenance, why shown, context manifest | Memory as truth or automatic context injection |
| `renders/07_setup_runtime_readiness.png` | Setup, runtime readiness | Setup checklist, backend/API health, local model readiness, blockers | Public beta, installer authority, production readiness |
| `renders/08_coding_cockpit.png` | Coding | Safe diff summary, exact command lanes, tests, receipts, rollback | Arbitrary shell, production deploy authority |
| `renders/09_source_inbox_crm_briefing_prep.png` | Source Inbox, CRM, Briefing | Read-only sources, CRM follow-ups, briefing builder, missing evidence | Connector writes, sends, imports, browser runtime |
| `renders/10_chat_handoff.png` | Chat | Local chat, runtime/tool truth, plan/action/memory/evidence handoff | Model output as authority |
| `renders/11_start_overview_dashboard.png` | Start Here, Overview, Dashboard | Setup state, route proof, next step, blocked/planned states | Marketing page or public readiness |
| `renders/12_settings_authority_profiles.png` | Settings | Authority, runtime, storage, redaction, receipts, revoke/kill posture | Unsupported authority as live |
| `renders/13_models_readiness.png` | Models | Local readiness, runtime profiles, provider/cost posture | Provider/model execution authority |
| `renders/14_files_context_proposals.png` | Files, File Review, Context Proposals | Safe refs, redacted previews, include/exclude proposals | Raw paths/content, broad filesystem authority |
| `renders/15_action_preview_preflight.png` | Action Preview | Dry run, side effects, idempotency, expiry, approval requirement | Preview as execution |
| `renders/16_runtime_storage_manual_smoke.png` | Runtime, Storage, Local Runtime, Manual Smoke | Health, command lanes, rate limits, ledgers, smoke checklist | Unrestricted subprocess/shell authority |
| `renders/17_future_domain_governance.png` | Remote Workers, Plugin Governance, Mobile Planning | Planned/dry-run/blocked matrix, exact-lane requirements | Remote execution, plugin import, mobile control |
| `renders/18_private_trial_packet.png` | Trial Packet | Acceptance ledger, review questions, private evidence refs | Public beta or production readiness |
| `renders/19_operator_loop.png` | Operator Loop | Observe-plan-act-prove-remember loop, route proof, blockers | Broad autonomy or fake workflow completion |
| `renders/20_api_foundation_events.png` | API Routes, Foundation Gate, Events, Differentiators | Route classes, OpenAPI/manifest checks, event ledger, proof claims | Contracts as runtime authority |

## Draft Candidates

Draft candidates are preserved for design review but are not part of the
accepted `CC-NS-2026-07-06` baseline. Every visible status, count, timestamp,
receipt, and control in these files is illustrative mock data rather than
backend or runtime evidence.

| File | Candidate scope | Review posture | Must not imply |
|---|---|---|---|
| `renders/drafts/CC-R2-SHELL-01-today-desktop-default-v1.png` | Alternate Today desktop shell | Draft-only; route wiring, data states, and product language remain unaccepted | Live system health, completed work, callable controls, current receipts, or runtime authority |

## Common Prompt Constraints

All renders used the same design constraints:

- contained 1440x900-ish desktop app window;
- no webpage chrome, endless scrolling, landing page, or hero section;
- fixed left navigation and persistent top status/authority strip on standard
  routes; Studio uses the documented immersive workbench exception;
- bounded split panes, inspectors, ledgers, and bottom evidence strips;
- restrained graphite/off-white visual system with blue/teal active states,
  green receipts, amber ask/partial, red denied/blocked, gray planned;
- route-aware UAA feature fit: Python Core ownership, CLI/API parity,
  AuthorityLease posture, exact approvals, receipts, audit, redaction,
  rollback/safe-disable, and Foundation Gate visibility;
- no raw JSON, raw prompts, raw responses, provider payloads, logs, local
  paths, credentials, or production claims.

## Target Shell Requirement

All future target render prompts and implementation passes should use the
CC-NS-TARGET-R3-2026-07-11 shell:

```text
Today, Communications, Messenger, Work Board, CRM, Calendar, News, Studio,
Knowledge, Activity & Trust, Customize, Settings, Developer Tools.
```

Action Inbox is reached through `Review N decisions` rather than a permanent
primary tab. Developer Tools is collapsed and hidden by default. Route-local
tabs stay inside the workspace and never replace global navigation.
