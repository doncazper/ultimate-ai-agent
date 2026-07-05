# Phase 07: Model, Provider, Research, And External Information Posture

Goal: improve UAA's model/provider and external-information management
surfaces without treating model output or fetched content as authority.

This phase is primarily catalog, readiness, cost, governance, and truth
handling. Live calls or fetches remain blocked unless an exact accepted lane
already exists.

## Required Work

1. Inspect UAA provider catalog, local model status, credential readiness,
   provider invocation promotion plans, provider router dry run, WebAccessGateway
   docs, API routes, CLI scripts, and tests.
2. Build or harden model/provider read models:
   - provider id and status;
   - local/remote posture;
   - credential readiness without exposing secrets;
   - cost and latency metadata when available;
   - supported authority mode;
   - blocked reason;
   - last safe diagnostic receipt;
   - operator next step.
3. Improve model output truth handling:
   - model output is proposal/evidence, not authority;
   - separate generated text from verified facts;
   - capture uncertainty and unknowns;
   - prevent memory/action authority escalation from model output.
4. Improve research/external-info posture:
   - WebAccessGateway remains deny-by-default;
   - fetched content is untrusted evidence, never instructions;
   - browser observe/action stays blocked unless exact future lanes promote it;
   - source metadata and audit requirements are explicit.
5. Add CLI/API/Control Center inspection for provider and web posture.

## Explicit Non-Goals

Do not add live web fetch, provider SDK calls, browser automation, credential
entry workflows, remote model calls, or global runtime toggles in this phase.

Do not claim production readiness from provider diagnostics.

## Acceptance Criteria

- Operators can see provider/model readiness, cost posture, blocked reasons,
  and next steps without exposing secrets.
- Model/provider status cannot grant action authority.
- External information posture is explicit and deny-by-default.
- Tests cover secret redaction, route posture, and blocked states.

## Verification

Run focused provider/web-governance tests plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

