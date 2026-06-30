# CRM Product Sequence Prompts

Status: stored execution prompts for the CRM product-line sequence.

Purpose: start CRM from the accepted contract-only M0 foundation and move
toward a fixture-only vertical CRM shell, backend-owned read models, read-only
routes, communications metadata, work queues, identity hygiene, and proposal
lanes without granting connector runtime, external CRM writes, account sync,
sends, calendar writes, live web, provider/model calls, public beta, or
production authority.

These prompts are operator-run instructions, not runtime system prompts. They
do not grant authority by themselves and do not replace `AGENTS.md`,
`docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`,
`docs/kanban/current_board.md`, `docs/control_center/PRODUCT_LANGUAGE_RULES.md`,
or `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.

## Prompt Order

Use Prompt 00 when the operator wants one end-to-end run through the full CRM
sequence. The execution agent must gate each prompt by accepted repo authority.
If a later prompt depends on unaccepted authority, it must record a blocked or
planned posture instead of pretending the feature exists.

1. Prompt 01: CRM M1 acceptance and product truth gate.
2. Prompt 02: CRM vertical preset map and fixture data contract.
3. Prompt 03: CRM North Star shell route/status plan.
4. Prompt 04: Real Estate/Realtor workspace screen.
5. Prompt 05: Healthcare workspace screen.
6. Prompt 06: Finance/Insurance workspace screen.
7. Prompt 07: Retail/E-commerce workspace screen.
8. Prompt 08: Professional Services workspace screen.
9. Prompt 09: CRM M2 backend read model and read-only API plan.
10. Prompt 10: CRM communications spine in Inbox plan.
11. Prompt 11: CRM work queues, signals, and relationship graph plan.
12. Prompt 12: CRM proposal lane, exact local-write ladder, and final hardening.

## Global CRM Authority Boundary

All prompts in this file must preserve these boundaries unless a later accepted
milestone grants the exact capability with tests, route manifests, CLI parity,
redacted evidence, and rollback or safe-disable posture:

- No connector runtime.
- No connector writes.
- No external CRM writes or account sync.
- No contact import, silent contact creation, or silent identity merge.
- No email/message sends.
- No calendar writes.
- No inbox/calendar/message raw body ingestion.
- No provider/model calls.
- No live web, browser automation, scraping, or enrichment runtime.
- No hidden context injection.
- No automatic memory truth.
- No production authority, public beta, public release, or public distribution
  claims.

CRM M1 may add deterministic fixture-only shell work only when it is labeled as
fixture-only and backed by route/status/product-language proof. CRM M2 and later
must remain planned or blocked unless their exact milestone is accepted.

## Prompt 00 - Execute CRM Product Sequence End To End

Role: You are a Principal Software Engineer performing CRM product-line
implementation, review, hardening, verification, and finalization.

Task: Read this entire file and execute Prompts 01-12 in order. Keep scope
tight and obey accepted authority. Implement only capabilities that are
currently allowed by repository truth. For future or unaccepted capabilities,
create or update the smallest planning/proof artifact and record the blocked
state clearly.

Required first reads:

- `AGENTS.md`
- `docs/strategy/CRM_COMMUNICATIONS_SPINE_M0.md`
- `src/ultimate_ai_agent/core/crm/contracts.py`
- `tests/test_crm_communications_spine_contracts.py`
- `scripts/verify_crm_communications_spine_m0.py`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/kanban/current_board.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- this file

Execution loop:

1. Inspect `git status --short --branch`.
2. Execute each prompt in order.
3. Before every edit, identify whether the prompt is implementable now or must
   remain planned/blocked.
4. Prefer Python-core contracts and backend-owned read models over React-only
   truth.
5. Add focused tests, verifiers, fixtures, route/status docs, and product
   language updates for any implemented behavior.
6. For frontend work, use existing Control Center design patterns and keep
   fixture/mock/degraded data visibly non-authoritative.
7. Review each diff for authority creep, raw-content leakage, route/API drift,
   UI-only truth, unsupported product claims, and missing verification.
8. Fix and harden until no in-scope faults remain.

Final verification targets:

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_crm_communications_spine_contracts.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_crm_communications_spine_m0.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if API
  routes change
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q` if
  API manifest changes
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
  if Control Center routes change
- `make frontend-check` if frontend files change
- `git diff --check`

Final response must include:

- prompts executed
- which prompts implemented behavior versus recorded planned/blocked posture
- files changed
- tests/verifiers run with pass/fail
- skipped checks and why
- behavior explicitly not added
- remaining risks
- recommended next CRM prompt or milestone
- current git status summary

## Prompt 01 - CRM M1 Acceptance And Product Truth Gate

Role: You are a Principal Software Engineer preparing the first CRM product-line
implementation gate.

Task: Determine whether CRM M1 is accepted and implementable. CRM M1 means a
beautiful deterministic fixture-only CRM shell with route/status/product-
language proof. It does not mean backend CRM endpoints, storage, connector
runtime, external writes, account sync, sends, or production authority.

Deliverables:

- Add or update the smallest CRM M1 scope artifact under `docs/strategy/`,
  `docs/control_center/`, or `docs/prompts/` if no accepted artifact exists.
- State the exact allowed implementation boundary for M1.
- Add a no-go posture for anything beyond fixture-only shell work.
- Keep `docs/kanban/current_board.md`, product truth, and product language
  aligned if changed.

Acceptance checks:

- The repo has one clear M1 entry point.
- Future M2+ capabilities are named but not claimed.
- Existing CRM M0 verifier and contract tests still pass.

## Prompt 02 - CRM Vertical Preset Map And Fixture Data Contract

Role: You are a Principal Software Engineer defining deterministic CRM fixture
contracts.

Task: Convert the existing `CrmWorkspaceKind` preset packs into a screen-ready
fixture map for:

- Real Estate/Realtor
- Healthcare
- Finance/Insurance
- Retail/E-commerce
- Professional Services

Requirements:

- Use safe refs and redacted summaries only.
- Include nav refs, object-kind refs, work-queue refs, pipeline refs, inspector
  section refs, blocked-authority refs, and state labels.
- Keep fixture generation code-owned and deterministic.
- Do not add import/export, schema migration, account sync, connector runtime,
  or customization runtime.

Acceptance checks:

- Fixture data is validated by focused tests or a verifier.
- Each vertical has distinct terminology and workflow emphasis.
- UI labels distinguish `fixture_only`, `read_only`, `proposal_only`, and
  `blocked` where relevant.

## Prompt 03 - CRM North Star Shell Route And Status Plan

Role: You are a Principal Software Engineer shaping the CRM shell without
claiming live CRM authority.

Task: Add or plan the `/crm` Control Center shell route only if M1 authority is
accepted. Otherwise, create the route/status plan and blocked-state proof
without adding the route.

Requirements if implemented:

- Route/status manifests must label the route fixture-only or equivalent.
- No backend CRM endpoints are added in M1.
- Mock/fixture data must be explicitly non-authoritative.
- The shell must show vertical switcher, pipeline, people/orgs, work queue,
  communications metadata placeholders, evidence, memory provenance, and
  blocked authority posture.

Acceptance checks:

- Product language never implies live CRM sync.
- React does not mint authority, evidence, eligibility, or source truth.
- Frontend tests cover fixture-only posture.

## Prompt 04 - Real Estate/Realtor Workspace Screen

Role: You are a Principal Software Engineer implementing or specifying the Real
Estate/Realtor CRM vertical.

Task: Build the Real Estate workspace from deterministic fixtures if CRM M1
shell work is accepted. Otherwise, write the exact fixture/screen spec.

Screen intent:

- Leads, buyers, sellers, listings, showings, offers, closings, follow-ups,
  relationship context, and next safe actions.

Required sections:

- Pipeline board.
- Relationship inspector.
- Property/listing context.
- Follow-up work queue.
- Communications metadata timeline.
- Evidence and memory provenance.
- Blocked-authority panel.

Non-goals:

- No MLS fetch, enrichment, contact import, outbound send, calendar write,
  external CRM sync, or account auth.

## Prompt 05 - Healthcare Workspace Screen

Role: You are a Principal Software Engineer implementing or specifying the
Healthcare CRM vertical.

Task: Build the Healthcare workspace from deterministic fixtures if CRM M1 shell
work is accepted. Otherwise, write the exact fixture/screen spec.

Screen intent:

- Referral relationships, patient-intake style pipeline objects, care-team
  coordination metadata, follow-up obligations, and evidence-backed next safe
  actions.

Required sections:

- Intake/referral pipeline.
- Organization and provider relationship view.
- Follow-up and handoff queue.
- Communications metadata timeline.
- Consent/sensitive-data posture.
- Evidence and memory provenance.
- Blocked-authority panel.

Non-goals:

- No PHI ingestion, EHR integration, medical advice, appointment writes,
  contact sync, account auth, sends, or connector runtime.

## Prompt 06 - Finance/Insurance Workspace Screen

Role: You are a Principal Software Engineer implementing or specifying the
Finance/Insurance CRM vertical.

Task: Build the Finance/Insurance workspace from deterministic fixtures if CRM
M1 shell work is accepted. Otherwise, write the exact fixture/screen spec.

Screen intent:

- Prospects, households or organizations by safe ref, policy/opportunity
  pipeline, renewal follow-ups, risk review posture, and proposal-only next
  actions.

Required sections:

- Opportunity/renewal pipeline.
- Relationship and household/org inspector using safe refs.
- Follow-up and review queue.
- Communications metadata timeline.
- Evidence and memory provenance.
- Compliance/blocked-authority panel.

Non-goals:

- No financial advice, underwriting automation, account sync, external CRM
  write, contact import, sends, calendar writes, or provider/model authority.

## Prompt 07 - Retail/E-commerce Workspace Screen

Role: You are a Principal Software Engineer implementing or specifying the
Retail/E-commerce CRM vertical.

Task: Build the Retail/E-commerce workspace from deterministic fixtures if CRM
M1 shell work is accepted. Otherwise, write the exact fixture/screen spec.

Screen intent:

- Customer cohorts by safe ref, order/support metadata placeholders, campaign
  ideas as proposals, retention follow-ups, and evidence-backed blocked states.

Required sections:

- Customer/opportunity pipeline.
- Cohort and relationship inspector.
- Retention/follow-up work queue.
- Communications metadata timeline.
- Evidence and memory provenance.
- Blocked-authority panel.

Non-goals:

- No commerce-platform sync, order import, email marketing send, customer data
  ingestion, account auth, external CRM write, or live tracking.

## Prompt 08 - Professional Services Workspace Screen

Role: You are a Principal Software Engineer implementing or specifying the
Professional Services CRM vertical.

Task: Build the Professional Services workspace from deterministic fixtures if
CRM M1 shell work is accepted. Otherwise, write the exact fixture/screen spec.

Screen intent:

- Leads, clients, projects, proposals, commitments, account health,
  relationship memory, and follow-up obligations.

Required sections:

- Lead/proposal/project pipeline.
- Client and stakeholder relationship inspector.
- Promise/follow-up work queue.
- Communications metadata timeline.
- Evidence and memory provenance.
- Blocked-authority panel.

Non-goals:

- No invoice/payment integration, external CRM write, email send, calendar
  write, account auth, connector runtime, or hidden context injection.

## Prompt 09 - CRM M2 Backend Read Model And Read-only API Plan

Role: You are a Principal Software Engineer preparing the backend-owned CRM
read-model milestone.

Task: If CRM M2 is accepted, implement backend-owned read models and read-only
routes. If not accepted, create the exact M2 implementation plan and no-go
posture.

Target concepts:

- `CrmPerson`
- `CrmOrganization`
- `CrmWorkspace`
- `CrmWorkspaceContext`
- `CrmRelationship`
- `CrmPipelineObject`
- `CrmCommunicationItem`
- `CrmWorkQueue`
- `CrmEvidenceRef`
- `CrmMemoryProvenance`

Requirements if implemented:

- Python core owns read model truth.
- OpenAPI, API manifest, route status, and tests are updated.
- CLI inspection exists without React.
- No mutating CRM routes are added.

## Prompt 10 - CRM Communications Spine In Inbox Plan

Role: You are a Principal Software Engineer preparing metadata-only CRM
communications.

Task: Plan or implement, depending on accepted authority, communications
metadata posture in the existing Inbox surface.

Allowed concepts:

- Safe communication refs.
- Metadata-only email/text/call/calendar/message/note/reminder items.
- Related person/org/workspace/pipeline refs.
- Next safe action refs.
- Evidence refs and source posture refs.

Blocked:

- Raw body ingestion.
- Account auth.
- Background polling.
- Sends.
- Calendar writes.
- Connector reads or writes unless later exact authority grants them.

## Prompt 11 - CRM Work Queues, Signals, And Relationship Graph Plan

Role: You are a Principal Software Engineer preparing CRM review intelligence
without execution authority.

Task: Plan or implement fixture/read-only work queues, engagement signals, and
relationship graph posture depending on accepted authority.

Requirements:

- Work queues are review-only.
- Signals use safe summaries and evidence refs only.
- Relationship graph items show why-shown refs and provenance.
- Identity match candidates remain review candidates, not merges.
- No automatic task creation or silent CRM updates.

Acceptance checks:

- Follow-up, stale, conflict, missing-evidence, and blocked states are visible.
- Action Inbox handoff is proposal-only unless a later exact lane is accepted.

## Prompt 12 - CRM Proposal Lane, Exact Local-write Ladder, And Hardening

Role: You are a Principal Software Engineer closing the CRM sequence with
proposal and authority-ladder clarity.

Task: Define or implement, depending on accepted authority, the CRM proposal
lane and later exact local-write ladder.

Proposal lane concepts:

- Follow-up task proposal.
- Pipeline stage-change proposal.
- Workspace link proposal.
- Identity merge proposal.
- Communication attach proposal.
- Email/message/calendar draft proposal.

Exact local-write ladder candidates:

- Create local CRM-lite lead.
- Update local opportunity stage.
- Mark local follow-up complete.
- Attach reviewed memory ref to local relationship.

Hard requirements:

- Approval refs are identifiers only until exact LocalApprovalAuthority scope
  validates them.
- Every mutation candidate needs idempotency, receipt, evidence refs,
  rollback/safe-disable posture, and tests.
- External CRM writes, sends, calendar writes, connector writes, account sync,
  and production authority remain blocked until separately accepted.

Final hardening:

- Update smallest relevant docs and indexes.
- Run focused tests and verifiers.
- Review product language for overclaims.
- Record skipped or blocked checks clearly.
