# FCC-ACTION-INBOX-LOOP-001e Recommended Next Step: Local Task Gate Review

Role: You are a Principal Software Engineer performing an adversarial,
production-grade graduation-gate review.

Mode: review-first. Do not implement fixes unless the operator explicitly asks
after the review.

Task: Re-run the exact-scope `local_task_create` graduation gate after the
Action Inbox truth-binding, receipt refresh/reconciliation, lane drilldown, and
Morning Briefing source-readiness work.

Treat `AGENTS.md` as binding.

Explicitly not in scope:
- generic execution
- connector writes
- shell/subprocess execution
- browser automation
- provider/model authority
- memory writes
- context injection
- plugin runtime import
- remote execution
- production/public release claims
- maturity rank promotion unless the manifest/verifier already supports it
- new route authority

Read first:
- `AGENTS.md`
- `docs/control_center/OPERATIONALIZATION_LADDER.md`
- `docs/control_center/operational_maturity_manifest.json`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/kanban/founder_command_center_board.md`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `src/ultimate_ai_agent/core/control_center/local_tasks.py`
- Action Inbox API routes, route metadata, OpenAPI, API manifest, CLI parity,
  frontend types, and `/actions` components/tests

Gate question:
Can an operator safely understand live `/actions` eligibility, approval,
pending receipt state, committed state, replay posture, and conflict posture
from backend-owned data only, with no React-minted authority or UI-only success
truth?

Review these required properties:

1. Backend-owned truth
- `approval_envelope` and `receipt_visibility` come from Python core/API data.
- React does not mint action kind, exact scope, risk class, side-effect class,
  approval requirement, eligibility, grants, receipt refs, replay posture, or
  conflict posture.
- Mock/degraded data cannot claim backend ownership or commit eligibility.
- Missing, pending, unavailable, unknown, and not-applicable states are explicit.

2. Commit and reconciliation
- Commit control appears only for backend-eligible approved `local_task_create`.
- POST receipt is displayed as local POST result only.
- The `/actions` card moves to `receipt_recorded` only after
  `GET /control-center/actions/inbox` returns backend-owned receipt visibility
  with matching `local_task_commit_receipt_ref`.
- Refresh failure or stale read model keeps the UI in explicit pending backend
  refresh state.
- Duplicate same idempotency returns prior receipt; conflicting idempotency is
  rejected and visible as conflict posture.

3. Receipts and evidence
- Decision receipt ref, local task ref, local task commit receipt ref, Evidence
  Timeline event ref, replay posture, and conflict posture are visible when the
  backend provides them.
- Pre-commit deterministic task refs are labeled as target/pending, not
  committed state.
- Evidence Timeline contains the `local_task_created` event.

4. Authority and redaction
- Approval refs are identifiers until `LocalApprovalAuthority` validates exact
  scope.
- Storage rejects missing, forged, expired, wrong-scope, wrong-kind, stale,
  empty, or conflicting authority.
- UI, docs, tests, receipts, evidence, and fixtures use safe refs/redacted
  summaries only.
- No raw prompts, responses, provider payloads, raw logs, raw local paths,
  usernames, hostnames, env dumps, credentials, or secret-like values appear.

5. Contract alignment
- Route metadata, OpenAPI, API manifest, CLI parity, storage behavior,
  frontend types, docs, and tests agree.
- `local_task_create` remains the only narrow local execution lane.
- Broader operational maturity is not claimed without verifier support.

Run focused checks:
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `make frontend-check`

Output format:
Start with findings only, ordered by severity. For each finding include
severity, file/line reference, what is wrong, why it matters, concrete fix
direction, and test/verifier that should catch it.

Then include:
- Gate decision: PASS, PASS WITH CONDITIONS, or FAIL
- Evidence supporting the decision
- Tests/verifiers run with pass/fail
- Checks skipped or blocked
- Remaining risks
- Recommended next implementation prompt, only if the gate passes or has a
  small well-scoped condition

