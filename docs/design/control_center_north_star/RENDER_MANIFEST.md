# Control Center North-Star Render Manifest

Status: current design target, documentation only.
Baseline ID: CC-NS-2026-07-06.
Current as of: 2026-07-06.
Repo baseline: v0.104.0 / 0.104.0.

The renders were generated as UI mockups for the Control Center north-star
direction and then copied into this repository as design artifacts. They should
be treated as visual targets and alignment aids, not shipped UI screenshots.

`APP_SHELL_BASELINE.md` is the normative shell specification for left-rail
order, route stability, typography, spacing, and state treatment. The PNGs are
not normative when their generated sidebar details conflict with that file.

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

## Common Prompt Constraints

All renders used the same design constraints:

- contained 1440x900-ish desktop app window;
- no webpage chrome, endless scrolling, landing page, or hero section;
- fixed left navigation and persistent top status/authority strip;
- bounded split panes, inspectors, ledgers, and bottom evidence strips;
- restrained graphite/off-white visual system with blue/teal active states,
  green receipts, amber ask/partial, red denied/blocked, gray planned;
- route-aware UAA feature fit: Python Core ownership, CLI/API parity,
  AuthorityLease posture, exact approvals, receipts, audit, redaction,
  rollback/safe-disable, and Foundation Gate visibility;
- no raw JSON, raw prompts, raw responses, provider payloads, logs, local
  paths, credentials, or production claims.

## Static Shell Requirement

All future render prompts and implementation passes should use the
CC-NS-2026-07-06 static shell:

```text
Start Here, Today, Source Inbox, Plans, Work Board, Action Inbox, Proof,
Trust, Memory, Evidence, Settings.
```

Supporting route groups may be collapsed or exposed through a stable secondary
section, but route-local tabs must stay inside the workspace and must not
replace global navigation.
