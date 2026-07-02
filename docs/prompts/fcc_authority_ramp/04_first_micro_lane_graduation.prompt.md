# FCC-AUTH-RAMP-001c Follow-On Authority Micro-Lane Graduation Gate

Role: You are a Principal Software Engineer implementing the first follow-on
authority micro-lane after the fixed `read_only_real_world_web_fetch` lane.

Mode: implementation only if a single follow-on candidate is explicitly ranked
`micro_lane_candidate` and all prerequisites are satisfied. Otherwise produce a
blocked/no-go hardening patch instead of adding authority.

Read first:
- `AGENTS.md`
- `docs/prompts/fcc_authority_ramp/01_fcc_auth_ramp_charter.prompt.md`
- `docs/prompts/fcc_authority_ramp/02_read_only_proposal_foundation.prompt.md`
- `docs/prompts/fcc_authority_ramp/03_authority_candidate_ranking.prompt.md`
- current authority candidate scorecard/manifest
- `docs/control_center/OPERATIONALIZATION_LADDER.md`
- `docs/control_center/operational_maturity_manifest.json`
- relevant Python core/API, CLI/script, Evidence Timeline, Action Inbox, UI,
  route metadata, OpenAPI, docs, and tests for the selected follow-on candidate

Hard gate:
Implement exactly one follow-on micro-lane only if the repository already
identifies it as the selected candidate and it has:
- exact scope
- backend/core ownership
- LocalApprovalAuthority validation where mutating
- idempotency and conflict rejection
- durable receipt
- Evidence Timeline event
- rollback/safe-disable posture
- redaction posture
- CLI/API/core parity
- focused tests
- operational maturity manifest/verifier support

If any prerequisite is missing:
1. Do not implement mutation.
2. Add or update the blocker in the scorecard/manifest/docs.
3. Add verifier coverage so the false promotion fails next time.
4. Return a no-go result with the smallest next safe action.

Non-goals:
- No generic execution.
- No multi-lane implementation.
- No connector write unless connector write is the one selected exact lane.
- No shell/subprocess unless the exact local maintenance lane is selected and
  constrained to an allowlisted, non-generic command contract.
- No provider/model authority. Model output may propose; it must not approve or
  execute.
- No context injection unless the exact context-pack injection lane has already
  passed proposal, approval, receipt, rollback, and verifier gates.
- No public beta, public release, production-readiness, or production authority.

Implementation requirements for an approved lane:
1. Add typed backend route(s) only if necessary and keep operation IDs stable
   unless a scoped contract update changes them with tests.
2. Add route metadata/API manifest/OpenAPI alignment.
3. Add storage/state changes as append-first and idempotent.
4. Add CLI/script parity or inspection parity.
5. Add receipt/evidence creation with safe refs only.
6. Add UI controls only after backend eligibility says the exact item is
   eligible.
7. Preserve blocked labels for every disallowed authority class.
8. Update maturity manifest rank only when verifier-backed behavior exists.

Required verification:
- focused storage/API tests
- focused CLI tests
- focused frontend tests if UI changes
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `make frontend-check` if frontend files changed

Definition of done:
- Either one exact follow-on micro-lane is implemented and verifier-backed, or
  the repo is hardened to explain why no follow-on lane can graduate yet.
- No broader authority leaks into routes, UI, docs, tests, fixtures, or evidence.
