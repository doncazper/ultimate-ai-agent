# Control Center North-Star Surface Coverage

Status: current design target, documentation only.
Baseline ID: CC-NS-TARGET-R6-2026-07-13.
Current as of: 2026-07-13.
Repo baseline: v0.104.0 / 0.104.0.

Every active Control Center route in `apps/control-center/src/routes.tsx` has a
mapped visual target below. A single render may cover more than one route when
the surfaces are intentionally part of the same operator workflow.

Normal routes share the static shell defined in `APP_SHELL_BASELINE.md`. Studio
and the planned Messenger workspace are the two documented immersive
exceptions. The coverage map below assigns route workspaces; it does not claim
that planned Messenger routes are implemented.

## Planned Messenger Routes

| Route family | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/messenger` | Messenger | `renders/communications-v1/01-founder-hq.png` through `15-setup-sign-in.png` | Clean-room Element-familiar Matrix client with Home, exactly two Spaces, rooms, DMs, threads, search, settings, security, recovery, UAA intelligence, and calling preflight. | Planned design only; no Matrix account, network, sync, encryption, send, room mutation, media, or call authority. Communications remains a separate unified hub. |

## Primary Founder Loop Routes

| Route | Label | Render target | Design intent | Boundary to preserve |
|---|---|---|---|---|
| `/start` | Start Here | `renders/11_start_overview_dashboard.png` | First-run local cockpit with setup state, route proof, next operator step. | No marketing hero, no public beta or production readiness claim. |
| `/today` | Today | `renders/01_today_command_center.png` | Daily command surface with briefing, priorities, approvals, memory, evidence, and blockers in one window. | Today coordinates loop state; it does not create hidden authority. |
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
