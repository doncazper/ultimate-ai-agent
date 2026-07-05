# Phase 08: Cockpit, CLI/API Parity, And Final Hardening

Goal: make the runtime parity loop operator-visible and reviewable across
Control Center, CLI, API contracts, docs, tests, and final scorecard evidence.

## Required Work

1. Inspect every change from Phases 01-07.
2. Ensure the operator can inspect the loop:
   - prepared turn;
   - route-decision binding;
   - durable run;
   - orchestration stages;
   - approval wait;
   - exact action receipt;
   - signed portable evidence;
   - blocked/degraded/retry state.
3. Add or harden Control Center UX without making React state the source of
   product truth.
4. Add or harden CLI commands/scripts for the same critical inspection paths.
5. Update API manifest, OpenAPI docs, route side-effect classification, product
   language, roadmap truth, and docs indexes as needed.
6. Update the runtime parity scorecard with before/after scores, evidence,
   confidence, status, remaining gaps, and "not yet parity" blockers.
7. Run three hardening loops:
   - security/authority hardening;
   - product/UX/readability hardening;
   - verification/contract hardening.
8. If any hardening loop finds a high or medium risk, fix it and rerun the
   relevant checks.

## UX Requirements

- No raw JSON as the primary operator-critical workflow.
- Approvals must be readable before action.
- Blocked states must say what is blocked and why.
- Evidence must be inspectable without exposing sensitive data.
- The UI must distinguish implemented, partial, planned, blocked, mock-only,
  deprecated, contradicted, and unknown states.

## Acceptance Criteria

- UAA can demonstrate the real operation loop end to end within accepted
  authority boundaries.
- CLI/API/Control Center expose the same core truth.
- The final scorecard is evidence-backed and does not overclaim parity.
- Tests and verifiers protect route binding, durable state, orchestration,
  provider evidence, action receipts, evidence signatures, and UX/API contracts.

## Verification

Run focused checks plus the relevant subset of:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
make frontend-visual-check
```

Run frontend checks only when frontend files changed. Report blockers instead
of claiming success.
