# Workspace UI Wiring Matrix

Status: active control-level truth ledger for the isolated `/workspace/*`
implementation.
Matrix date: 2026-07-14.
Repo baseline: v0.104.0 / 0.104.0.

This ledger answers four separate questions: where a surface is coded, which
Python/API contract owns its real state, which controls are wired now, and
which visible controls were intentionally skipped. It is subordinate to the
canonical route inventory in `docs/control_center/UI_WIRING_REPORT.md`; it does
not replace canonical route truth or grant runtime authority.

## Status language

| Status | Exact meaning |
|---|---|
| `Wired` | The coded control reads or mutates through an existing typed backend/core contract. Mutation rows show their receipt and refresh behavior. |
| `Partial` | Some owning backend data or controls are wired, but the complete rendered surface is not. |
| `Skipped` | A compatible backend may exist, but this pass intentionally did not connect the visible control. The reason is stated. |
| `Missing` | No eligible backend/core contract exists for the intended control. |
| `Preview only` | The surface still uses labeled fixtures and cannot mutate backend truth. |
| `Presentation only` | React owns a reversible local display preference, selection, filter, or disclosure state only. |

`Wired` never means production readiness, broad autonomy, or general authority.
Python Core remains the state and authority owner.

## Surface-location and implementation matrix

| Product surface | Review route | Primary code location | Backend owner / canonical route | Workspace UI status | Truth / remaining gap |
|---|---|---|---|---|---|
| Today | `/workspace/today` | `apps/control-center/src/northstar/PrimarySurfaces.tsx` | `GET /control-center/today/summary`; `/today` | Partial | Briefing, action, plan, memory-review, and evidence counts/rows now use backend data. Add-to-Day-Plan and Ask UAA remain unavailable. |
| Communications | `/workspace/communications` | `PrimarySurfaces.tsx` | Source posture only from `GET /control-center/founder-loop/source-readiness` | Fixture only | Messages and summaries are explicitly synthetic render fixtures. Search and selection are local. No account read, draft, CRM, follow-up, calendar, send, or assistant action occurs. |
| Messenger | `/messenger` (also reached from `/workspace/messenger`) | `apps/control-center/src/components/messenger/MessengerShell.tsx` | No Matrix account/sync/send contract | Preview only | The canonical 15-state Messenger shell remains the sole desktop representation; the workspace path is an alias, not a competing client. No auth, sync, encryption runtime, room mutation, send, media, or call authority exists. |
| Work Board | `/workspace/work-board` | `PrimarySurfaces.tsx` | `GET /control-center/work-board`; `/work-board` | Partial | Backend columns/cards and local search are wired read-only. Card/task mutation controls remain unavailable because this surface has no exact prepared approval envelope; task execution and completion remain unavailable. |
| CRM | `/workspace/crm` | `PrimarySurfaces.tsx` | `GET /control-center/crm/summary`; `/crm` | Partial | People, organizations, relationships, follow-ups, opportunities, pipelines, smart lists, timeline counts, proposals, reports, and authority posture use the backend read model. Search/selection are local; calls, messages, follow-up creation, connector writes, calendar writes, and external CRM writes remain disabled. |
| Calendar | `/workspace/calendar` | `PrimarySurfaces.tsx` | Source posture only; no event read model | Fixture only | Event and candidate content is explicitly synthetic. No account read, conflict check, proposal, assistant handoff, or external write occurs. |
| News | `/workspace/news` | `SecondarySurfaces.tsx` | Source posture only; no feed read model | Fixture only | Articles and topics are explicitly synthetic. Search/topic selection are local; no retrieval, source open, save, mute, or assistant action occurs. |
| Studio shell / Create | `/workspace/studio` | `apps/control-center/src/northstar/StudioSurface.tsx` | `GET /control-center/agent-loop/thread`; coding-cockpit read models; connection posture | Partial | Chat now reads the backend Agent Loop thread and Code reads coding session/project/panel posture. Create/Skill/Presentation content remains preview-only; saved ideas, briefs, adaptations, file writes, shell, git mutation, and export are disabled. |
| Skill Workbench | `/workspace/studio` | `StudioSurface.tsx` | No typed sanitized skill-catalog route | Preview only | Discovery metadata is a labeled representation. Import, install, activation, execution, and adaptation remain unavailable. |
| Knowledge | `/workspace/knowledge` | `SecondarySurfaces.tsx` | `GET /control-center/memory/review`; `POST /control-center/memory/manual-candidate`; `/memory` | Partial | Backend review queue, provenance, accept/correct/reject/defer receipts, manual review-candidate intake, and refresh are wired. Manual intake creates no recall record or memory write. Files, context, merge, supersede, delete, export, and context injection remain unavailable. |
| Activity & Trust | `/workspace/activity-trust` | `SecondarySurfaces.tsx` | `GET /control-center/trust-authority/matrix`; `GET /control-center/settings/status`; `/trust`, `/settings` | Partial | Domain/tier matrix, active leases, and policy decisions are backend reads. Revocation requires explicit lease selection, confirmation bound to that unchanged active ref, receipt, and settings refresh. Pause, kill switch, and safe-disable mutation are unavailable. |
| Customize | `/workspace/customize` | `SecondarySurfaces.tsx` | No durable layout preference contract | Presentation only | Visibility and density are local preview state. Cancel, restore, and undo reset that draft; durable save is disabled. This state cannot change capability or authority. |
| Settings | `/workspace/settings` | `SecondarySurfaces.tsx` | `GET /control-center/settings/status`; `/settings` | Partial | Backend authority, feature-flag, kill-switch, provider, lease, and blocked posture are wired read-only. Density is a local presentation preview. All backend settings writes remain disabled because the backend reports `settings_mutation_enabled=false`. |
| Developer Tools | `/workspace/developer-tools` | `SecondarySurfaces.tsx` | Runtime readiness, coding apply/session posture, source readiness, Foundation Gate; canonical inspect routes | Partial | Embedded lane/check/resource rows now derive from backend read models and canonical inspect links remain functional. Refresh, clipboard, terminal execution, and patch application are unavailable from this representation. |
| Terminal | `/workspace/developer-tools/terminal` | `SecondarySurfaces.tsx` | No eligible governed session/command contract is connected | Preview only | All command buttons are disabled and output is labeled reference-only. No shell/subprocess, session-create, cancellation, or receipt claim occurs. |
| Decision Review | `/workspace/decisions` | `SecondarySurfaces.tsx` | `GET /control-center/actions/inbox`; `/actions` | Wired | Backend queue and envelopes render directly. A mutation is eligible only when the matching backend-owned `needs_approval` decision-lane item and item-specific review action exist, with receipt/cost gates intact. Read-only/blocked items never gain controls. |
| Onboarding | `/workspace/onboarding` | `apps/control-center/src/northstar/OnboardingSurface.tsx` | `GET /control-center/setup-assistant/summary`; source readiness; `/setup` | Partial | Backend setup status, blockers, steps, and source-readiness counts are visible. Source selection and Back/Continue are an unsaved local draft; durable save/resume/finish and authentication remain disabled. |
| UAA sidecar | standard `/workspace/*?sidecar=open` | `apps/control-center/src/northstar/NorthStarShell.tsx` | `GET /control-center/agent-loop/thread` | Partial | Sidecar reads backend work request, next decision, proposed action, evidence, and proof refs. Open/close is local. Prompt editing, sending, dismissing, and mutation handoff are disabled; Decision Review navigation is wired. |
| Compact shell | responsive standard workspace routes | `NorthStarShell.tsx`, `northStar.css` | Not applicable | Presentation only | Responsive containment is UI behavior; it has no backend contract. |
| Workspace bootstrap | every `/workspace/*` route | `apps/control-center/src/App.tsx` | Aggregate typed Control Center reads | Partial | The labeled mock representation renders immediately while compatible backend reads are pending, then receives backend data in place. Preview data cannot enable mutations; canonical operator routes retain the fail-closed loading shell. |

## Control-level wired, skipped, and missing matrix

| Surface / control | Operation | API/core contract | State | Receipt / refresh behavior | Reason or remaining gap | Focused evidence |
|---|---|---|---|---|---|---|
| Today — briefing, attention, plans, counts | Read | `GET /control-center/today/summary` | Wired | Read-only on initial app data load | Uses safe summaries and refs only | `NorthStarControlCenter.test.tsx`; frontend typecheck |
| Today — Review decisions | Navigation | `/workspace/decisions` | Wired | Preserves backend app state; opens review surface | Navigation only | North-star route tests |
| Today — Add to Day Plan | Mutation | None eligible | Missing | None | No exact Day Plan mutation/receipt contract | Disabled with an explicit reason |
| Today — Ask UAA | Proposal/handoff | No Today-to-assistant contract connected | Skipped | None | Sidecar/handoff ownership is unresolved | Listed for later sidecar wiring |
| Work Board — columns/cards | Read | `GET /control-center/work-board` | Wired | Initial aggregate read | Python owns board state; no durable React duplicate | `WiredSurfaces.test.tsx` |
| Work Board — search/select | Local UI | In-memory filter/selection | Presentation only | Preserves backend model | Local, reversible, non-durable state | `WiredSurfaces.test.tsx` |
| Work Board — Create card | Mutation | Backend route exists; no prepared envelope supplied here | Missing | None | Exact approval, scope, envelope, lease, and stable idempotency intent are required before this surface may call it | Disabled with an explicit reason |
| Work Board — Create local task record | Mutation | Backend route exists; no prepared envelope supplied here | Missing | None | Exact approval, scope, envelope, lease, and stable idempotency intent are required before this surface may call it | Disabled with an explicit reason |
| Work Board — Persist reorder | Mutation | `POST /control-center/work-board/reorder` | Skipped | None from this surface | Canonical component already owns preview/reorder UX; accepted workspace render did not yet receive equivalent drag/keyboard treatment | Canonical `WorkBoardPanel.tsx` remains available |
| Work Board — Start / Add to Day Plan / complete | Mutation | No eligible exact contracts | Missing | None | Task execution, Day Plan mutation, and completion receipts are separate lanes | Buttons disabled with reasons |
| Decision Review — queue/envelope | Read | `GET /control-center/actions/inbox` | Wired | Refreshed after decision receipts | Requires backend-owned envelope and receipt-visibility grammar | `WiredSurfaces.test.tsx` |
| Decision Review — approve/edit/reject/defer | Mutation | `POST /control-center/actions/{action_id}/{decision}` | Wired | Shows decision receipt, action-executed truth, and reconciliation state | Requires an exact matching backend `needs_approval` decision-lane item, item-specific action, authoritative envelope/receipt posture, and approved cost posture | `WiredSurfaces.test.tsx` |
| Decision Review — filters/sort/open source | Local/read | No mapped implementation in this pass | Skipped | None | Queue remains in backend order; source route mapping is not typed | Controls omitted or disabled |
| Knowledge — review queue/provenance | Read | `GET /control-center/memory/review` | Wired | Refreshed after a decision receipt | Safe refs only; memory is recall, not truth | `WiredSurfaces.test.tsx` |
| Knowledge — accept/correct/reject/defer | Mutation | `POST /control-center/memory/review/{candidate_ref}/{decision}` | Wired | Shows receipt and reloads the review queue | Correct requires bounded correction text/ref | `WiredSurfaces.test.tsx` |
| Knowledge — merge/supersede/expire/forget request | Mutation | Backend routes exist | Skipped | None | Workspace render does not yet expose duplicate/conflict refs and lifecycle-specific confirmation UI | Canonical Memory surface remains owner |
| Knowledge — Add local note | Mutation | `POST /control-center/memory/manual-candidate` | Wired | Shows exact receipt; then reloads Memory Review and preserves receipt truth if refresh fails | Creates a review candidate only; no recall record, memory write, context injection, or connector write | `WiredSurfaces.test.tsx` |
| Trust — domain/tier matrix | Read | `GET /control-center/trust-authority/matrix` | Wired | Initial app data load | Cells come from backend lane/tier mappings; missing mappings show planned | Typecheck and route tests |
| Trust — lease/policy decisions | Read | `GET /control-center/settings/status` | Wired | Refreshed after revocation | Backend AuthorityState owns lease and decisions | `WiredSurfaces.test.tsx` |
| Trust — Revoke selected lease | Mutation | `POST /api/runtime/authority-leases/revoke` through typed client | Wired | First click binds confirmation to the selected ref; second revalidates that unchanged active ref, records a receipt, then refreshes settings | Selection/ref/status changes fail closed without a POST | `WiredSurfaces.test.tsx` |
| Trust — Pause activity | Mutation | No exact pause contract | Missing | None | No backend lane or receipt contract | Disabled |
| Trust — Kill switch | Mutation | Status only; mutation flag false | Missing | None | `kill_switch_mutation_enabled=false` | Disabled with explicit title/reason |
| Trust — Restrict to read-only | Mutation | No exact safe-disable mutation route connected | Missing | None | Safe-disable posture is metadata, not an action grant | Disabled |
| Settings — authority/settings posture | Read | `GET /control-center/settings/status` | Wired | Initial app data load | Mirrors read-only backend truth | North-star tests |
| Settings — density | Local UI | Presentation state only | Presentation only | Immediate preview; not saved | Does not alter backend or authority | North-star tests |
| Settings — preferences/toggles/provider config | Mutation | Backend explicitly disables settings mutation | Missing | None | No writable settings contract; no React simulation | Disabled or shown as status only |
| Developer Tools — Inspect/Review links | Navigation | Canonical `/runtime`, `/actions`, `/models`, `/settings`, `/action-preview` | Wired | Canonical route owns refresh and mutation posture | Avoids duplicating backend state | Typecheck and desktop smoke coverage |
| Developer Tools — Copy safe summary/inspection command | Local capability | No eligible clipboard bridge is connected | Skipped | None | Direct browser clipboard access is forbidden by the frontend safety boundary | Disabled with exact reason |
| Developer Tools — embedded diagnostics | Read | Runtime readiness, coding apply/session, source readiness, Foundation Gate | Wired | Initial app data load | Backend refs/statuses replace representative timing and pass/fail fixtures | `WiredSurfaces.test.tsx`; typecheck |
| Developer Tools — embedded refresh | Read | Could reload global data, but no local refresh callback is exposed | Skipped | None | Global reload would lose context; canonical routes own refresh | Disabled with reason |
| Terminal — command/session buttons | Execution | No eligible contract connected | Missing | None | Arbitrary shell/subprocess remains blocked | Disabled; reference output labeled |
| CRM — v3 table/detail | Read | `GET /control-center/crm/summary` | Wired | Initial app data load | Safe refs/summaries only; all external/write controls remain disabled | `WiredSurfaces.test.tsx`; desktop smoke coverage |
| Onboarding — setup status | Read | `GET /control-center/setup-assistant/summary`; source readiness | Wired | Initial app data load | Local selection draft is not durable; Finish remains disabled | `WiredSurfaces.test.tsx` |
| Communications / Calendar / News source posture | Read | Founder Loop source-readiness contract | Wired | Initial app data load | Message/event/article content still lacks an owning read model | Typecheck and desktop smoke coverage |
| Communications / Calendar / News / Messenger writes | Mutation | Required contracts do not exist or are authority-blocked | Missing | None | Requires separately scoped exact lanes before any write | Disabled with explicit reasons |
| Studio Chat / Code | Read | Agent Loop thread and coding-cockpit read models | Wired | Initial app data load | Mutations stay on canonical governed lanes; no runtime authority added | `WiredSurfaces.test.tsx` |
| Studio Create / Skill Workbench | Read or mutation | No durable asset/skill catalog or adaptation contract | Missing | None | Install/import/activation/execution remain blocked | Preview-only content |
| Customize — save/reset/undo | Mutation | No durable preference route | Skipped | None | Local preview is allowed; persistence contract is not yet required | Presentation state only |
| UAA sidecar — context | Read | `GET /control-center/agent-loop/thread` | Wired | Initial app data load | Safe summaries and refs only | Sidecar component tests/typecheck |
| UAA sidecar — composer/handoff | Proposal | No sidecar mutation contract connected | Skipped | None | Model output/handoff must not become authority | Editing/sending/dismiss controls disabled |
| Workspace bootstrap — pending reads | Read/presentation | Existing aggregate Control Center loader | Wired | Defers aggregate API reads until the code-split workspace module resolves, then displays the explicit preview model until typed backend data resolves; backend data replaces the preview prop without route navigation | Prevents chunk starvation and a long blank shell without loading the workspace bundle on canonical routes or treating fixtures as backend truth/mutation eligibility | `App.test.tsx`; `workspace-surfaces.visual.spec.ts`; desktop smoke coverage |

## Files changed by this wiring pass

| File | Responsibility |
|---|---|
| `apps/control-center/src/App.tsx` | Shows the explicit workspace preview during aggregate reads and upgrades it to backend data while canonical routes remain fail-closed. |
| `apps/control-center/src/hooks/useControlCenterData.ts` | Supports deferring aggregate reads until a route-specific module is ready, preventing UI code from competing with backend requests. |
| `apps/control-center/src/northstar/NorthStarControlCenter.tsx` | Passes backend data into every eligible workspace representation. |
| `apps/control-center/src/northstar/NorthStarShell.tsx` | Wires global posture and the read-only Agent Loop sidecar while keeping prompt/handoff mutations disabled. |
| `apps/control-center/src/northstar/PrimarySurfaces.tsx` | Wires Today, Work Board, CRM, source readiness, and receipt-safe local mutations. |
| `apps/control-center/src/northstar/SecondarySurfaces.tsx` | Wires Memory Review/manual intake, Action Inbox, Trust/Authority, Settings, source posture, and backend Developer Tools diagnostics. |
| `apps/control-center/src/northstar/StudioSurface.tsx` | Wires read-only Agent Loop and Coding cockpit models; hardens unwired Create/Skill/Presentation controls. |
| `apps/control-center/src/northstar/OnboardingSurface.tsx` | Wires setup/source-readiness reads and local unsaved review navigation. |
| `apps/control-center/src/northstar/primitives.tsx` | Defaults handler-less tabs and searches to disabled, preventing dead enabled controls. |
| `apps/control-center/src/northstar/northStar.css` | Adds contained create forms, bounded safe-ref cards, status rows, responsive layout, and a consistent visibly disabled treatment for unavailable controls. |
| `apps/control-center/src/northstar/WiredSurfaces.test.tsx` | Proves receipt, refresh, eligibility, and confirmation behavior. |

No backend route, OpenAPI operation, authority flag, provider call, connector,
browser action, shell execution, or production behavior was added in this pass.
