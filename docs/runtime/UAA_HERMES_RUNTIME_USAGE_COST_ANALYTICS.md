# UAA Hermes Runtime Usage Cost Analytics

Status: Hermes Runtime Adoption Phase 22 repo-safe read model

Phase 22 adds Python Core ownership for redacted runtime usage and cost
analytics posture:

- `RuntimeUsageCostAnalyticsReadModel`
- `RuntimeUsageCostRecord`
- `GET /api/runtime/usage-cost-analytics`
- `scripts/dev/uaa_runtime.py inspect-usage-cost-analytics`
- Control Center Runtime readiness display
- `scripts/verify_hermes_runtime_adoption_phase_22.py`

This is accounting posture only. It does not perform live provider calls,
provider SDK calls, billing actions, live price fetches, operator export,
runtime dispatch, shell/subprocess execution, connector writes, browser
automation, or production authority.

## Full-Strength Version

UAA should eventually show live cost, usage, latency, model, runtime, and
task-value attribution across native, delegated, local, and future runtime
lanes. The operator should be able to understand what a task cost, which runtime
produced the evidence, which receipt supports the number, and whether the value
was worth it.

The full version requires provider result envelopes, exact cost attribution,
usage accounting from trusted receipts, redacted receipt storage, export
controls, safe-disable posture, and verifier-backed proof.

## Repo-Safe Current Version

The current implementation exposes a backend-owned read model containing:

- safe accounting record refs
- runtime, provider, model, task-value, receipt, and estimate refs
- bounded usage estimates
- latency and cost minor-unit estimates
- proof, evidence, verifier, and next-safe-action refs
- explicit blocked authority refs
- redactions for prompt, response, provider payload, billing payload, and
  export payload content

The Control Center only renders this backend-owned state. It does not mint
authority and does not claim billing, provider execution, or export readiness.

## Blocked / Needs Authority

The following remain blocked:

- billing actions
- provider calls
- provider SDK calls
- live price fetches
- operator export of accounting ledgers
- raw prompt persistence
- raw response persistence
- raw provider payload persistence
- model-output authority
- production authority

## Promotion Path

Promotion requires:

1. Provider result envelope contract with safe refs and bounded redacted fields.
2. Cost attribution policy tied to runtime receipt refs and task-value refs.
3. Usage accounting from receipt metadata instead of raw prompt or response
   bodies.
4. Redacted receipt envelope with verifier version, policy decision,
   authority profile, and proof refs.
5. Operator export lane with explicit approval, redaction, idempotency,
   receipt, and safe-disable posture.
6. CLI/API/Core parity and route side-effect classification.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_usage_cost_analytics.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_22.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run typecheck --prefix apps/control-center
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts
```
