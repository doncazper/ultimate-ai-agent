# Unblock Provider / Model Invocation Live Call

Goal:
Perform or explicitly no-go one exact approved, capped test provider/model
invocation through the existing tiny provider lane without granting broad
provider authority.

Branch:
`codex/unblock-provider-model-live-call`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- do not broaden provider/model authority beyond this one invocation
- no autonomous provider/model calls
- no provider router fallback execution
- no model-output-as-truth
- no memory write or context injection from model output
- no raw prompt, raw response, provider exchange, credential, or token
  persistence
- no connector writes, browser automation, shell execution, background worker,
  public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/provider_model_invocation_live_call_2026_07_03.md`
   - `docs/control_center/PROVIDER_BILLING_AUTHORITY_BOUNDARY.md`
   - `docs/control_center/EXACT_APPROVED_PROVIDER_FALLBACK.md`
   - `src/ultimate_ai_agent/core/providers/invocation.py`
   - `scripts/inspect_tiny_provider_invocation_lane.py`
   - `scripts/verify_tiny_provider_invocation_lane.py`
2. Verify whether a safe test credential ref, exact approval scope,
   CostGovernor max-approved USD decision, idempotency ref, and redacted receipt
   store are available for one named tiny live adapter.
3. If any prerequisite is missing, do not call a provider. Update the blocker
   report with the missing prerequisite and keep the lane blocked.
4. If every prerequisite is present, run exactly one foreground invocation
   through the existing tiny provider lane.
5. Persist only redacted receipt refs, actual usage refs, actual cost refs,
   approval refs, audit refs, and safe provider/model refs.
6. Add or update tests proving:
   - exact approval is required;
   - CostGovernor blocks unknown or over-budget cost;
   - incomplete actual cost blocks further use until review;
   - raw prompt, response, provider exchange, and credentials are not persisted;
   - broad provider/model authority remains blocked.

Tests/verifiers:
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_tiny_provider_invocation_lane.py tests/test_tiny_live_provider_adapter.py tests/test_tiny_live_provider_adapter_receipts.py tests/test_provider_usage_cost_receipt_hardening.py -q`
- `.venv/bin/python scripts/verify_tiny_provider_invocation_lane.py`
- `.venv/bin/python scripts/verify_provider_billing_authority_boundary.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and the scope remains exactly one test invocation
