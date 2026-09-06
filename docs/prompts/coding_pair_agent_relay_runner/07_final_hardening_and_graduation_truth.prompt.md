# Phase 07: Final Hardening And Graduation Truth

Goal: harden the paired-agent relay runner and report exactly what graduated,
what remains blocked, and what is needed next.

## Required Work

1. Run authority/security, product/UX, and verification/contract hardening
   loops.
2. Confirm no arbitrary command entry, provider SDK calls, hidden background
   dispatch, unbounded turns/time/output, raw durable transcript, patch apply
   without separate approval, Git mutation, browser/connector authority, or
   production authority claim.
3. Update product truth packet, operator shell gap map, route status manifest,
   docs index, and authority blocker or graduation doc.
4. If foreground execution was promoted, document exact scope, approvals,
   receipts, rollback/safe-disable, idempotency, CLI/API parity, tests, and
   remaining blocks.
5. If foreground execution remains blocked, document the preview/readiness lane
   and generate the exact future unblock prompt.
6. Run final verification and report blockers honestly.

## Acceptance Criteria

- The final docs do not overclaim.
- Every execution-capable behavior has exact tests and receipts.
- Every blocked behavior has an explicit blocked state.
- The operator can understand whether Pair Agents is preview-only or genuinely
  execution-capable.

## Verification

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_coding_cockpit_read_model.py -q
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

Report blocked checks instead of claiming success.

