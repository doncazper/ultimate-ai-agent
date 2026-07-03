# Unblock Action Execution Additional Exact Kind

Goal:
Promote or explicitly no-go one additional exact Action kind after
`local_task_create`, without granting broad action execution.

Branch:
`codex/unblock-action-execution-additional-exact-kind`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not broaden Action Execution beyond one named action kind
- no broad approve-all or standing authority
- no connector writes/sends
- no shell/subprocess execution
- no provider/model calls
- no browser automation
- no memory writes or runtime context injection
- no external side effects unless that exact authority has already graduated
- no scheduler/background/autonomous execution
- no UI-only eligibility or UI-only operator truth
- no raw prompt, response, payload, file path, credential, account, contact, or
  secret-like persistence
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/action_execution_additional_exact_kind_2026_07_03.md`
   - `docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md`
   - `docs/control_center/operational_maturity_manifest.json`
   - `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
2. Select exactly one new local, low-risk Action kind that does not depend on
   blocked connector, shell, provider/model, browser, memory-write,
   context-injection, scheduler, or production authority.
3. If no such Action kind is available, update the blocker report and keep the
   lane blocked.
4. If a safe kind is selected, implement only that kind:
   - backend-owned Action envelope fields
   - exact LocalApprovalAuthority scope
   - idempotency/replay/conflict behavior
   - durable receipt refs
   - Evidence Timeline event refs
   - rollback or safe-disable posture
   - Proof/read-model refs where applicable
   - CLI parity over the same backend contract
   - frontend binding that cannot invent committed/executable state
5. Add or update tests proving:
   - unsupported action kinds are denied;
   - approval scope mismatch blocks;
   - duplicate idempotency replays safely;
   - evidence/proof/receipt refs are present;
   - no UI-only action truth appears;
   - connector/shell/provider/browser/memory/context/background authorities
     remain blocked.

Tests/verifiers:
- focused Action Inbox/state-machine pytest
- focused frontend tests if UI changed
- `.venv/bin/python scripts/verify_fcc_action_001_approval_bound_local_micro_lanes.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` if routes change
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and the new Action kind remains exact-scoped
