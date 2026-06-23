# FCC-AUTH-RAMP-001a Read-Only And Proposal Foundation

Role: You are a Principal Software Engineer implementing the read-only and
proposal-only foundation for the Founder Command Center authority ramp.

Mode: implementation, but no new runtime authority.

Read first:
- `AGENTS.md`
- `docs/prompts/fcc_authority_ramp/01_fcc_auth_ramp_charter.prompt.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- existing Control Center Today, Morning Briefing, Action Inbox, Memory, and
  Evidence components/tests
- existing Python core/API contracts for source readiness, memory-to-loop,
  context packs, Action Inbox, and Evidence Timeline

Goal:
Make the soon-needed proposal foundation visible and useful:
- read-only connector metadata
- memory-to-loop proposal UX
- context-pack proposal display

Authority boundary:
This task must not add connector reads beyond accepted read-only metadata
contracts, connector writes, account auth, source polling, send/archive/delete,
shell/subprocess execution, provider/model calls, memory writes, context
injection, generic execution, or production authority.

Implementation requirements:
1. Surface read-only connector metadata only where backend/core contracts
   already exist or add contract-only/read-only status structures with route
   metadata and tests.
2. Make Memory-to-loop proposals scannable from the appropriate Founder Loop
   surfaces without treating memory recall as truth or authority.
3. Make context-pack proposals inspectable before any context injection exists.
4. Feed safe proposal refs into Action Inbox, Morning Briefing, Today, Memory,
   and Evidence only through backend/core-owned data.
5. Display explicit blockers for missing connector runtime, missing exact scope,
   missing approval, missing receipt/evidence contract, and missing
   rollback/safe-disable posture.
6. Do not use raw JSON as the primary operator UI.
7. Preserve safe refs and bounded summaries only.

Tests to add or update:
- backend/API tests for any read-only/proposal status payloads
- frontend tests proving proposal-only display and blocked-state copy
- tests proving no connector write, memory write, context injection, model call,
  shell/subprocess, or generic execute control appears
- documentation/product-language checks when docs change

Required verification:
- focused backend/API tests for changed routes or storage helpers
- focused frontend tests for changed Control Center surfaces
- `make frontend-check` if frontend files changed
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if API contracts change
- `.venv/bin/python scripts/verify_operational_maturity.py`

Definition of done:
- The foundation is useful and inspectable.
- Every item remains read-only or proposal-only.
- No new runtime authority is added.
- Tests/verifiers fail if future UI copy implies unsupported authority.
