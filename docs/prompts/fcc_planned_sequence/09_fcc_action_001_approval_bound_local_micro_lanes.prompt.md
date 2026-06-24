# FCC-ACTION-001 Approval-Bound Local Micro-Lanes

Role: You are a Principal Software Engineer implementing exact-scoped local
micro-lanes only after maturity gates prove the lane is safe.

Task: Add or harden the first approval-bound local micro-lane, starting with
`local_task_create`, without broadening action execution.

Requirements:
- Each lane must have exact approval, receipt, evidence, idempotency,
  rollback/safe-disable posture, blocked external authority, operational
  maturity manifest rank, CLI/core/API parity, and focused tests.
- Existing `local_task_create` must remain the only rank 5 local execution
  lane unless a new lane is separately accepted and fully gated.
- The UI must show backend-owned eligibility and receipt state; React must not
  mint authority or committed state.

Non-goals:
- No generic execution, connector writes, shell/subprocess work, browser
  automation, provider/model authority, memory writes, context injection,
  external side effects, rollback execution without a separate scoped lane, or
  production authority.

Focused checks:
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py tests/test_founder_loop_storage_actions.py tests/test_control_center_api_routes.py tests/test_fcc_v1_003_founder_loop_vertical_slice.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `make frontend-check`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `git diff --check`
