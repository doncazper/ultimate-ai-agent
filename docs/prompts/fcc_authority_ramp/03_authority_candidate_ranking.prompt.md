# FCC-AUTH-RAMP-001b Authority Graduation Candidate Ranking

Role: You are a Principal Software Engineer building an adversarial scorecard
for future Founder Command Center authority candidates.

Mode: implementation of ranking, docs, tests, and verifiers. Do not implement
the authority lanes themselves.

Read first:
- `AGENTS.md`
- `docs/prompts/fcc_authority_ramp/01_fcc_auth_ramp_charter.prompt.md`
- `docs/prompts/fcc_authority_ramp/02_read_only_proposal_foundation.prompt.md`
- `docs/control_center/OPERATIONALIZATION_LADDER.md`
- `docs/control_center/operational_maturity_manifest.json`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- route metadata, API manifest, OpenAPI, Evidence Timeline, Action Inbox, and
  maturity verifier code/tests

Goal:
Rank follow-on authority candidates so the repo can choose one narrow
micro-lane at a time after the fixed `read_only_real_world_web_fetch`
implementation prompt, instead of drifting into broad autonomy.

Follow-on candidate classes:
- connector writes
- memory writes
- shell/subprocess local maintenance
- browser automation
- provider/model authority
- context injection

Scoring dimensions:
- user value in the Founder Loop
- authority risk
- data sensitivity
- blast radius
- reversibility
- exact-scope clarity
- approval posture
- idempotency feasibility
- receipt/evidence feasibility
- rollback/safe-disable feasibility
- CLI/API/core parity
- redaction complexity
- testability
- existing operational maturity rank
- dependency on external services or credentials

Implementation requirements:
1. Add a repo-owned scorecard artifact or manifest section.
2. Keep the scorecard deterministic and safe-ref-only.
3. Mark each candidate as one of:
   - `not_ready`
   - `proposal_only_ready`
   - `contract_ready`
   - `micro_lane_candidate`
   - `blocked_by_policy`
4. Require explicit blockers and smallest next safe action for every candidate.
5. Treat `read_only_real_world_web_fetch` through `WebAccessGateway` as the
   fixed first implementation lane, not a substitute scorecard candidate for
   broader authority. If that lane is blocked, follow-on candidates stay blocked
   too.
6. Add verifier checks that prevent any candidate from being marked
   `micro_lane_candidate` without exact scope, approval plan, idempotency plan,
   receipt/evidence plan, rollback/safe-disable plan, CLI/API/core parity refs,
   and focused tests or test refs.
7. Provider/model output must not become production authority. At most it may
   propose candidates for Python core/policy review.
8. Context injection must remain blocked unless context-pack proposals are
   inspectable, approval-bound, receipt-backed, and explicitly scoped.

Tests to add or update:
- scorecard schema/shape tests
- verifier tests for missing blockers
- verifier tests for false micro-lane promotion
- docs/product-language tests if claims change

Required verification:
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
- focused scorecard/verifier tests
- `.venv/bin/python scripts/verify_documentation_integrity.py`

Definition of done:
- The repo can answer which authority candidate is safest and why.
- No candidate receives authority from the scorecard.
- Future micro-lane work has a hard gate instead of vibes.
