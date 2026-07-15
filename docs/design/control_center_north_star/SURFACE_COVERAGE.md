# Control Center North-Star Surface Coverage

Status: current design target with isolated code-native review implementation.
Baseline ID: CC-NS-TARGET-R6-2026-07-13.
Current as of: 2026-07-14.
Repo baseline: v0.104.0 / 0.104.0.

Every active Control Center route in `apps/control-center/src/routes.tsx` has a
mapped visual target below. A single render may cover more than one route when
the surfaces are intentionally part of the same operator workflow.

Normal routes share the static shell defined in `APP_SHELL_BASELINE.md`. Studio
and the Messenger desktop fixture are the two documented immersive exceptions.
The coverage map below assigns route workspaces. `/messenger` is implemented as
synthetic presentation only; every Matrix runtime and authority lane remains
blocked until its later exact milestone is separately accepted.

## Isolated Review Implementation

The current render set now has a code-native review implementation under the
isolated `/workspace/*` route family in `apps/control-center/src/northstar/`.
This lane supplies real React surfaces for Today, Communications, Messenger,
Work Board, CRM, Calendar, News, Studio, Knowledge, Activity & Trust,
Customize, Settings, Developer Tools, Terminal, Decision Review, and
Onboarding. It deliberately does not replace the canonical backend-owned
routes yet, so concurrent core/API implementation can continue without a
route cutover or competing state owner.

The accepted legacy `01`–`19` PNG pack also has a separate code-native review
implementation under `/workspace/reference/*`. These surfaces preserve the
accepted desktop information architecture while using explicit preview
fixtures. Their content controls are disabled with an adjacent global reason;
only the reference-pack navigation remains active. This makes `Built` truthful
without implying that any workflow is backend-wired.

Where an existing compatible read model is authoritative, the review shell
may show that route posture. Otherwise the surface is visibly marked
preview-only and keeps actions disabled, proposal-only, or review-bound. The
Messenger implementation includes the full 15-screen reference-state set but
does not connect a Matrix account or grant network, send, room-mutation,
encryption, media, or call authority. Skill Workbench is a sanitized discovery
representation; external skills remain signals only and cannot be installed,
imported, activated, or executed from this lane.

The control-level source of truth for this route-by-route wiring pass is
`UI_WIRING_MATRIX.md`. It lists every connected control, exact API route,
receipt/refresh behavior, intentional skip, and missing contract.

## Surface Implementation Matrix

Matrix date: 2026-07-14. Status language in this matrix is intentionally strict:

- **Planned** means the module has been discussed and is expected to need a
  product surface.
- **Rendered** means a static PNG/JPG reference image of the intended surface
  exists. SVG-only planning concepts are called out separately.
- **Built** means the surface is coded in the app and has passed desktop
  render/overflow smoke coverage. It does not imply pixel or screenshot parity
  with the reference render.
- **UI implemented** means the built surface is wired to its real backend/core
  contract. Reading only connection or route posture counts as partial, not
  implemented.

Canonical routes remain the compatibility source until an explicit
route-by-route cutover is accepted. `Yes`, `Partial`, `No`, and `N/A` are used
instead of broader readiness language.

### Current Product Surface Set

| Surface | Planned | Rendered | Built | UI implemented | Missing / next implementation gap |
|---|---|---|---|---|---|
| Today | Yes | Yes — `target-v1/01-today.png` | Yes — `/workspace/today` | Partial — briefing, action, plan, memory-review, and evidence rows/counts use the Today backend model; missing arrays remain honest empty states | Add exact source-owned CRM/calendar/news/business-pulse projections and separately governed Day Plan/assistant contracts before claiming them |
| Communications | Yes | Yes — `target-v1/02-communications.png` | Yes — `/workspace/communications` | No — content is an explicitly synthetic desktop fixture; only backend source readiness is shown | Define a unified message read contract; account reads, drafts, CRM, follow-up, calendar, sends, and assistant actions remain unavailable |
| Messenger | Yes | Yes — all 15 images in `communications-v1/` | Yes — canonical `/messenger`; `/workspace/messenger` aliases it | No — fixture-only canonical shell | Matrix account/auth, encrypted local store, sync/read contracts, and separately governed send/invite/room/call lanes |
| Work Board | Yes | Yes — `target-v2/03-work-board-v2.png` | Yes — `/workspace/work-board` | Partial — backend columns/cards and local search/select are wired read-only; mutation controls are disabled | Add an exact prepared approval/envelope flow with stable idempotency before card/task writes; execution, Day Plan mutation, and completion remain separate lanes |
| CRM | Yes | Yes — `target-v3/04-crm-v3.png` | Yes — `/workspace/crm` | Partial — relationship, person, organization, follow-up, opportunity, pipeline, smart-list, report, and authority reads use the CRM backend model | Add exact governed local mutations only where canonical contracts and confirmation/receipt UX are eligible; all sends and external writes remain disabled |
| Calendar | Yes | Yes — `target-v1/05-calendar.png` | Yes — `/workspace/calendar` | No — event/candidate content is explicitly synthetic; backend source readiness alone does not make it a calendar read model | Build a read-only event model, then exact proposal/approval lanes; account reads and external writes remain blocked |
| News | Yes | Yes — `target-v2/15-news-v1.png` | Yes — `/workspace/news` | No — article/topic content is explicitly synthetic; backend source posture alone does not make it a feed | Add governed source feed, provenance, freshness, and safe refs through `WebAccessGateway`; retrieval/open/save/mute remain disabled |
| Studio shell and Create | Yes | Yes — `target-v3/06-studio-unified-v7.png` | Yes — Create plus backend-read Chat and Code workspaces are built | Partial — Chat reads Agent Loop truth and Code reads coding-cockpit posture; Create assets remain preview-only | Add durable local asset/version/reference ownership; file writes, shell, git mutation, export, and model execution remain unavailable here |
| Skill Workbench | Yes | Yes — user PNG supplied 2026-07-14 | Yes — default `/workspace/studio` Create view | No | Wire a typed sanitized metadata contract and quarantine/review/adaptation records; install/import/activation/execution remain blocked |
| Knowledge | Yes | Yes — `target-v1/07-knowledge.png` | Yes — `/workspace/knowledge` | Partial — backend review queue, provenance, decisions, manual review-candidate intake, receipts, and refresh are wired | Add lifecycle-specific merge/supersede/expire/forget-request UI and retained Files/Context views without granting context injection |
| Activity & Trust | Yes | Yes — `target-v2/16-trust-v1.png` | Yes — `/workspace/activity-trust` | Partial — matrix, lease, policy-decision reads and exact active-lease revocation are wired | Pause, kill-switch, and safe-disable mutations remain unavailable; add only after exact backend contracts and confirmation/receipt UX exist |
| Customize | Yes | Yes — `target-v1/09-customize.png` | Yes — `/workspace/customize` | No — visibility/density plus cancel/restore/undo are local draft behavior only | Add a durable preference contract before enabling Save; reordering remains unimplemented and is no longer implied |
| Settings | Yes | Yes — `target-v1/10-settings.png` | Yes — `/workspace/settings` | Partial — backend settings/authority/lease/kill-switch/provider posture is wired read-only; density is presentation-only | The backend explicitly disables settings mutation, so writable preferences, review, receipts, and rollback remain missing rather than simulated |
| Developer Tools | Yes | Yes — `target-v1/11-developer-tools.png` | Yes — `/workspace/developer-tools` | Partial — runtime, coding apply/session, source readiness, Foundation Gate, and canonical navigation are wired read-only | Embedded refresh, clipboard, terminal execution, and patch application remain unavailable; canonical routes retain mutation ownership |
| Terminal | Yes | Yes — `target-v2/17-terminal-v1.png` | Yes — `/workspace/developer-tools/terminal` | No | Wire typed allowed-command envelopes, approval, timeout, redacted output, receipts, cancellation, and CLI/core/API parity |
| Decision Review | Yes | Yes — `target-v1/12-decision-review.png` | Yes — `/workspace/decisions` | Yes — backend queue/envelopes and eligible approve/edit/reject/defer receipts are wired with cost gating and read-model reconciliation | Add typed source navigation and local filter/sort only if they preserve backend order and state; blocked/read-only items remain without controls |
| Onboarding | Yes | Yes — `target-v1/13-onboarding.png` | Yes — `/workspace/onboarding` | Partial — backend setup/source readiness is wired and source selection plus Back/Continue is an unsaved local draft | Durable saved choices, authentication, resume, finish receipts, and installer execution remain unavailable |
| UAA sidecar | Yes | Yes — `target-v1/14-uaa-sidecar.png` | Yes — standard workspace routes with `?sidecar=open` | Partial — Agent Loop work request, next decision, proposed action, evidence, and proof refs are wired read-only | Prompt editing/sending/dismiss and governed proposal handoff remain disabled; model output must not become authority |
| Compact desktop shell | Yes | Yes — `target-v2/18-compact-shell-v1.png` | Yes — desktop shell, browser-tested at 1100px | N/A — this is presentation behavior with no backend contract | Keep macOS desktop canonical; mobile implementation is outside this program |

Current totals: **19 planned**, **19 rendered**, and **19 built**. For UI
implementation, **1 is backend-wired for its owning workflow** (Decision
Review), **10 are partial**, **7 are not wired**, and **1 is not
applicable** because the compact shell is presentation-only. The detailed
partial/skip/missing truth is recorded in `UI_WIRING_MATRIX.md`.

### Accepted Legacy 01–19 Render Pack

This is a separate reference pack, not an addition to the current-product
totals above. Every row has been coded and exercised by desktop render/overflow
smoke coverage at the reference pack's native `1586 × 992` viewport. This does
not claim pixel or screenshot parity. Shared additions—the truthful preview banner,
reference navigation, and disabled unwired controls—are intentional safety
differences from the PNGs.

| Surface | Planned | Rendered | Built | UI implemented | Missing / next implementation gap |
|---|---|---|---|---|---|
| 01 Today Command Center | Yes | Yes — `renders/01_today_command_center.png` | Yes — `/workspace/reference/01-today` | No | Wire briefing, priorities, approvals, memory, evidence, and blocker read models |
| 02 Action Inbox & Approval Envelope | Yes | Yes — `renders/02_action_inbox_approval_envelope.png` | Yes — `/workspace/reference/02-action-inbox` | No | Wire queue reads and exact approve/edit/reject/defer envelopes with receipts |
| 03 Plans & Work Board | Yes | Yes — `renders/03_plans_work_board.png` | Yes — `/workspace/reference/03-plans-work-board` | No | Wire plan and board ownership without duplicating backend state |
| 04 Trust & AuthorityLease | Yes | Yes — `renders/04_trust_authority_lease.png` | Yes — `/workspace/reference/04-trust` | No | Wire lease, domain, policy-decision, revoke, and kill-switch contracts |
| 05 Evidence, Proof & Receipts | Yes | Yes — `renders/05_evidence_proof_receipts.png` | Yes — `/workspace/reference/05-evidence-proof` | No | Wire proof detail, evidence timeline, receipts, rollback, and safe-disable refs |
| 06 Memory Review & Context Manifest | Yes | Yes — `renders/06_memory_review_context_manifest.png` | Yes — `/workspace/reference/06-memory` | No | Wire review, provenance, correction, why-shown, and context proposal contracts |
| 07 Setup & Runtime Readiness | Yes | Yes — `renders/07_setup_runtime_readiness.png` | Yes — `/workspace/reference/07-setup` | No | Wire setup state, local readiness, blockers, manual smoke, and resume state |
| 08 Governed Coding Cockpit | Yes | Yes — `renders/08_coding_cockpit.png` | Yes — `/workspace/reference/08-coding` | No | Wire repo-safe work threads, proposals, exact command lanes, tests, and receipts |
| 09 Source Inbox, CRM & Briefing | Yes | Yes — `renders/09_source_inbox_crm_briefing_prep.png` | Yes — `/workspace/reference/09-sources-crm-briefing` | No | Wire governed read-only sources, CRM-lite, briefing assembly, and provenance |
| 10 Chat & Handoff | Yes | Yes — `renders/10_chat_handoff.png` | Yes — `/workspace/reference/10-chat-handoff` | No | Wire local chat plus typed proposal handoffs to Plans, Actions, Evidence, and Memory |
| 11 Start, Overview & Dashboard | Yes | Yes — `renders/11_start_overview_dashboard.png` | Yes — `/workspace/reference/11-start-overview` | No | Wire readiness, route proof, next-step, and resume state |
| 12 Settings & Authority Profiles | Yes | Yes — `renders/12_settings_authority_profiles.png` | Yes — `/workspace/reference/12-settings-authority` | No | Wire persisted preferences and exact governed profile changes with undo/receipts |
| 13 Model Readiness | Yes | Yes — `renders/13_models_readiness.png` | Yes — `/workspace/reference/13-models` | No | Wire local model/runtime readiness and provider posture without granting calls |
| 14 Files & Context Proposals | Yes | Yes — `renders/14_files_context_proposals.png` | Yes — `/workspace/reference/14-files-context` | No | Wire safe-ref review, redacted previews, include/exclude proposals, and corrections |
| 15 Action Preview & Preflight | Yes | Yes — `renders/15_action_preview_preflight.png` | Yes — `/workspace/reference/15-action-preview` | No | Wire dry-run scope, side effects, idempotency, expiry, approval, and receipt plan |
| 16 Runtime, Storage & Manual Smoke | Yes | Yes — `renders/16_runtime_storage_manual_smoke.png` | Yes — `/workspace/reference/16-runtime-storage` | No | Wire health, exact command lanes, storage ledger, snapshots, and smoke evidence |
| 17 Future Domain Governance | Yes | Yes — `renders/17_future_domain_governance.png` | Yes — `/workspace/reference/17-future-governance` | No | Keep planning-only until exact remote, mobile, and plugin lanes are promoted |
| 18 Private Trial Packet | Yes | Yes — `renders/18_private_trial_packet.png` | Yes — `/workspace/reference/18-private-trial` | No | Wire private acceptance records and safe evidence refs without release claims |
| 19 Operator Loop | Yes | Yes — `renders/19_operator_loop.png` | Yes — `/workspace/reference/19-operator-loop` | No | Wire the observe-plan-act-prove-remember summary to owning read models |

Reference-pack totals: **19 planned**, **19 rendered**, **19 built**, and **0 UI
implemented**. Backend wiring remains a route-by-route follow-up and must reuse
the Python core/API contracts rather than creating durable React-only state.

### Canonical Compatibility Surfaces

These routes already exist in the current Control Center and remain the source
of route truth. The matrix groups them by product ownership so the migration
queue is visible without pretending each needs a duplicate destination.

| Surface group / routes | Planned | Rendered | Built | UI implemented | Missing relative to the new surface set |
|---|---|---|---|---|---|
| Start and system overview — `/start`, `/`, `/dashboard` | Yes | Yes — legacy composite images | Yes — canonical surfaces | Partial | Decide whether their content folds into Today/Onboarding or receives refreshed renders |
| Source Inbox and Briefing — `/inbox`, `/briefing` | Yes | Yes — legacy source/briefing image | Yes — canonical surfaces | Partial | Define ownership between Communications and Today, then connect shared read models |
| Plans — `/plans` | Yes | Yes — legacy Plans/Work Board image | Yes — canonical surface | Partial | Decide whether Plans remains distinct or becomes a Work Board saved view/inspector |
| Actions — `/actions`, `/approvals`, `/action-preview` | Yes | Yes — legacy action/approval/preflight images | Yes — canonical surfaces | Mixed — Action Inbox paths are implemented; approval/preflight coverage is partial or experimental | Connect `/workspace/decisions` without creating a second action queue |
| Proof and evidence — `/proof`, `/evidence`, `/receipts`, `/events`, `/events/timeline` | Yes | Yes — legacy proof/evidence/event images | Yes — canonical surfaces | Mixed — backend-owned, partial, and experimental | Choose final navigation placement and migrate the new visual treatment |
| Memory and context — `/memory`, `/files`, `/files/review`, `/context/proposals` | Yes | Yes — legacy memory/files/context images | Yes — canonical surfaces | Mixed — Memory is implemented; file/context paths are partial or experimental | Connect Knowledge and decide whether Files/Context stay separate utilities |
| Studio compatibility — `/coding`, `/chat`, `/setup` | Yes | Yes — legacy images plus current Studio/Onboarding renders | Yes — canonical surfaces | Mixed — Chat is implemented; Coding and Setup are partial | Connect immersive Studio/Onboarding and define route cutover |
| Runtime operations — `/runtime`, `/models`, `/storage`, `/runtime/local`, `/runtime/manual-smoke` | Yes | Yes — legacy runtime/storage/model images | Yes — canonical surfaces | Partial | Connect Developer Tools/Terminal to exact read and command contracts |
| System evidence and governance — `/operator-loop`, `/foundation-gate`, `/capabilities`, `/api-routes`, `/differentiators`, `/private-trial` | Yes | Yes — legacy system/governance images | Yes — canonical surfaces | Partial or experimental | Decide retained product placement and refresh renders where needed |
| Future governance — `/remote-workers`, `/mobile-planning`, `/plugin-governance` | Yes | Yes — legacy future-governance image | Yes — planning/dry-run pages | No — no promoted runtime workflows | Exact AuthorityLease domains, adapters, approvals, receipts, rollback/safe-disable, and tests |

### Deferred Render Packs

| Pack | Planned | Rendered | Built | UI implemented | Missing / gate |
|---|---|---|---|---|---|
| Social Media Intelligence | Yes | Yes — four JPG reference images in `renders/social-media-v1/` | No | No | Dependency-gated behind accepted Work Board, CRM, and Communications foundations; then requires governed connector reads and separately approved publishing/reply lanes |
| Coherent App Ecosystem (`ECO-000`) | Yes | No under this definition — twelve SVG planning concepts exist, but no PNG/JPG render set | No | No | Requires accepted implementation scope for Calendar, Tasks, Boards, Inbox, Organizer, global search, ChangeSet review/compensation, storage, route migration, and authority contracts |

## Messenger Fixture Route

| Route family | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/messenger` | Messenger | `renders/communications-v1/01-founder-hq.png` through `15-setup-sign-in.png` | Implemented synthetic desktop fixture shell with Home, exactly two Spaces, rooms, DMs, threads, search, settings, security, recovery, UAA intelligence, calling preflight, and the required deterministic state variants. | Fixture presentation only; no Matrix dependency, account, network, sync, encryption session, message read/send, room mutation, media, call, credential, model, memory, or connector authority. Communications remains a separate unified hub. |

## Primary Founder Loop Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/start` | Start Here | `renders/11_start_overview_dashboard.png` | First-run local cockpit with setup state, route proof, next operator step. | No marketing hero, no public beta or production readiness claim. |
| `/today` | Today | `renders/01_today_command_center.png` | Daily command surface with briefing, priorities, approvals, memory, evidence, and blockers in one window. | Today coordinates loop state; it does not create hidden authority. |
| `/news` | News & Signals | `renders/news-signals-v1/01-news-signals-home.png` through `04-news-signals-community-filter.png` | Implemented fixture-only ranked-list preview with selected-item rationale, safe preview refs, and local filter state across desktop widths. | Sample evidence only; no Reddit, X, email, Discord, RSS, blog, video, podcast, connector, browser, polling, or unrestricted fetch authority. |
| `/inbox` | Source Inbox | `renders/09_source_inbox_crm_briefing_prep.png` | Read-only/draft-only source readiness feeding briefing and action proposals. | No connector writes, live import commits, browser automation, or raw private content. |
| `/plans` | Plans | `renders/03_plans_work_board.png` | Plan outline tied to action envelopes, board cards, dependencies, and evidence. | Plans produce proposals and envelopes, not unapproved execution. |
| `/work-board` | Work Board | `renders/03_plans_work_board.png` | Backend-owned board cockpit with bounded columns, approvals, receipts, and rollback posture. | Local board mutation requires exact approval and workspace/write authority. |
| `/actions` | Action Inbox | `renders/02_action_inbox_approval_envelope.png` | Queue, approval envelope, policy decision, and receipt state in one review cockpit. | Approval refs are identifiers; action execution remains governed by exact authority. |
| `/proof` | Proof | `renders/05_evidence_proof_receipts.png` | Proof detail inspector with receipt, rollback, evidence, and route links. | Proof is inspection evidence, not authority. |
| `/trust` | Trust | `renders/04_trust_authority_lease.png` | Authority mode/domain/lease cockpit with ask/deny/degrade decisions and kill switch. | No broad global authority toggle; unknown authority is denied. |
| `/memory` | Memory | `renders/06_memory_review_context_manifest.png` | Review queue, provenance, corrections, why-shown, and context manifest. | Memory is recall, not truth or automatic context injection authority. |
| `/evidence` | Evidence | `renders/05_evidence_proof_receipts.png` | Timeline and ledger for proposed, approved, happened, changed, stale, blocked, undo-ready states. | Evidence refs are redacted safe refs, not raw logs or execution permission. |
| `/settings` | Settings | `renders/12_settings_authority_profiles.png` | Local settings cockpit for authority, runtime, storage, redaction, approvals, and receipts. | Settings visibility must not imply unsupported authority is live. |

## Supporting Founder Loop Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/briefing` | Briefing | `renders/09_source_inbox_crm_briefing_prep.png` | Morning Briefing builder from source refs, memory reasons, missing evidence, and proposed actions. | Briefing assembly must not imply connector reads/writes beyond implemented contracts. |
| `/crm` | CRM | `renders/09_source_inbox_crm_briefing_prep.png` | CRM-lite local command center with follow-ups, relationship notes, and safe proposal refs. | No external CRM writes, account sync, sends, calendar writes, provider calls, or browser runtime. |
| `/private-trial` | Trial Packet | `renders/18_private_trial_packet.png` | Private operator acceptance ledger with pass/fail/skipped/blocked/partial/mock-only states. | Private review only; no public beta, distribution, or production readiness claim. |

## Review Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/operator-loop` | Operator Loop | `renders/19_operator_loop.png` | Readable loop map for observe, plan, act, prove, remember, plus gaps and next lane. | Loop readability is not broad autonomy. |
| `/setup` | Setup | `renders/07_setup_runtime_readiness.png` | Mac-first Setup Assistant with runtime health, local model readiness, manual smoke, and blockers. | No raw paths, raw logs, installer authority, or production claims. |
| `/coding` | Coding | `renders/08_coding_cockpit.png` | Governed repo-local coding cockpit with safe diff summary, exact lanes, tests, receipts, rollback. | Arbitrary shell/subprocess and production authority remain denied unless separately granted. |
| `/chat` | Chat | `renders/10_chat_handoff.png` | First-party local chat tied to Plans, Actions, Evidence, and Memory handoffs. | Model/runtime output is not authority; handoffs are proposals or receipts. |
| `/models` | Models | `renders/13_models_readiness.png` | Local model readiness, runtime profiles, provider/cost posture, and credential readiness. | Local readiness is not provider/model execution authority. |
| `/approvals` | Approvals | `renders/02_action_inbox_approval_envelope.png` | Approval summary tied to exact envelopes, policy decisions, and receipts. | Approval UI cannot mint authority without matching validated scope. |
| `/files` | Files | `renders/14_files_context_proposals.png` | Safe-ref local file review inbox and redacted metadata preview. | No raw local paths, raw file content, or broad filesystem authority. |
| `/files/review` | File Review | `renders/14_files_context_proposals.png` | Review-only file detail with redacted preview, unsafe omission, correction path. | Review-only means no hidden write/import/context injection. |
| `/context/proposals` | Context Proposals | `renders/14_files_context_proposals.png` | Context pack include/exclude proposals with source refs and blocked injection state. | Context injection remains blocked until separately scoped and tested. |
| `/action-preview` | Action Preview | `renders/15_action_preview_preflight.png` | Dry-run/preflight surface for side effects, exact scope, idempotency, expiry, and receipt plan. | Preview does not execute. |

## Runtime Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/runtime` | Runtime | `renders/16_runtime_storage_manual_smoke.png` | Runtime operations cockpit with profiles, command lanes, health, rate limits, and receipts. | Governed exact lanes only; no unrestricted shell/subprocess authority. |
| `/storage` | Storage | `renders/16_runtime_storage_manual_smoke.png` | Storage ledger, snapshots, receipt destinations, and rollback points. | No raw local paths, environment dumps, or secret-like values. |
| `/runtime/local` | Local Runtime | `renders/16_runtime_storage_manual_smoke.png` | Local runtime profile/status with sealed, local-runtime, operator-approved posture. | Runtime profile visibility is not unrestricted execution. |
| `/runtime/manual-smoke` | Manual Smoke | `renders/16_runtime_storage_manual_smoke.png` | Manual validation checklist with blockers and redacted evidence refs. | Manual pass/fail state is evidence, not production readiness. |
| `/remote-workers` | Remote Workers | `renders/17_future_domain_governance.png` | Experimental governance matrix for remote/worker authority candidates. | Remote execution remains planned/dry-run/blocked unless separately promoted. |
| `/mobile-planning` | Mobile Planning | `renders/17_future_domain_governance.png` | Future mobile sensor/control planning with requirements and blockers. | No mobile control, sensor runtime, or app authority implied. |
| `/plugin-governance` | Plugin Governance | `renders/17_future_domain_governance.png` | Plugin/skill governance matrix with activation grants, import posture, and no-go blockers. | No plugin runtime import or connector authority implied. |

## Evidence And System Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/foundation-gate` | Foundation Gate | `renders/20_api_foundation_events.png` | Gate result cockpit tied to manifest, OpenAPI, route state, and evidence refs. | Gate visibility is verification evidence, not authority. |
| `/receipts` | Receipts | `renders/05_evidence_proof_receipts.png` | Receipt ledger with safe refs, approval refs, rollback/safe-disable posture. | Receipts record what happened; they do not authorize future work. |
| `/events` | Events | `renders/20_api_foundation_events.png` | Event ledger tied to route and product proof states. | Events must be redacted and safe-ref-only. |
| `/events/timeline` | Timeline | `renders/20_api_foundation_events.png` | Timeline view for typed product and runtime events. | Timeline may be mock/experimental where route state says so. |
| `/` | Overview | `renders/11_start_overview_dashboard.png` | System overview of route readiness, product loop state, and next step. | Overview is informational and non-authoritative. |
| `/dashboard` | Dashboard | `renders/11_start_overview_dashboard.png` | Compact system/product dashboard with readiness, blocked/planned states, and receipts. | Dashboard status does not imply production readiness. |
| `/capabilities` | Capabilities | `renders/17_future_domain_governance.png` | Backend-owned capability matrix showing implemented, partial, blocked, planned, exact-lane, and safe-disable posture. | Capability visibility does not grant runtime authority or imply unsupported adapters are available. |
| `/api-routes` | API Routes | `renders/20_api_foundation_events.png` | Route inventory, side-effect class, OpenAPI/manifest posture, stable operation IDs. | Contracts do not grant runtime capability. |
| `/differentiators` | Differentiators | `renders/20_api_foundation_events.png` | Evidence-backed product differentiators grounded in local-first governance and receipts. | No marketing-only or unsupported product claims. |

## Shared Visual Requirements

- Fit the complete route workflow inside one desktop application window.
- Prefer split panes, inspectors, compact ledgers, tabs, and segmented controls.
- Treat route status as first-class: implemented, partial, blocked, planned,
  experimental, mock-only, degraded, skipped, and receipt-recorded states must
  remain visually distinct.
- Use icons for common controls, with text reserved for clear commands and
  short status labels.
- Keep cards shallow; do not nest cards inside cards.
- Use redaction and safe refs instead of raw prompts, responses, provider
  payloads, logs, local paths, credentials, usernames, hostnames, or serials.
- Make the operator's next action obvious without hiding approval, policy,
  rollback, or safe-disable posture.
- Preserve the canonical left rail from `APP_SHELL_BASELINE.md` across normal
  route workspaces. Studio and Messenger use their documented immersive rails
  with a visible Back to Control Center command.
- Use `RENDER_VARIATION_MATRIX.md` for the required default, compact,
  route-specific state, mobile, overlay, and shared-state render deliverables.
