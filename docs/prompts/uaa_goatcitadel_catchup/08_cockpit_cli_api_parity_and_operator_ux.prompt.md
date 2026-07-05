# Phase 08: Cockpit, CLI/API Parity, And Operator UX

Goal: make UAA feel more like a capable AI cockpit: the operator should
understand what the agent knows, plans, can do, cannot do, has done, and needs
approval for.

This phase is product and parity work. It must not move product truth into UI
state.

## Required Work

1. Inspect Control Center route surfaces, API client, panels, visual manifests,
   CLI scripts, route inventory, OpenAPI contract, API manifest, smoke tests,
   and product-language docs.
2. Improve IA around the Founder Command Center loop:
   - Today;
   - Inbox;
   - Plans;
   - Actions;
   - Memory;
   - Evidence;
   - Settings;
   - optional unified work thread.
3. Add or harden readable cockpit affordances:
   - status chips;
   - blocked/no-go reasons;
   - approval summaries;
   - action receipts;
   - plan revisions;
   - memory review cards;
   - evidence drilldowns;
   - safe degraded/backend-unavailable states.
4. Ensure every operator-relevant UI action maps to Python core/API and CLI or
   repo-local script inspection.
5. Add frontend tests and visual checks where UI changed.
6. Update product-language verifiers to prevent raw JSON primary UX and
   unsupported maturity claims.

## UX Requirements

- Use operator-readable language.
- Avoid raw JSON for critical workflows.
- Separate facts, assumptions, unknowns, and recommendations.
- Label statuses as implemented, partial, planned, mock-only, blocked,
  deprecated, contradicted, or unknown.
- Make approvals readable: scope, risk, side-effect class, expiry, receipt
  requirements, rollback/safe-disable posture.
- Do not expose secrets, paths, raw prompts, raw responses, or raw logs.

## Acceptance Criteria

- A user can make real operator decisions from the cockpit.
- CLI/API surfaces expose the same core truth as the UI.
- UI-only state is limited to presentation concerns.
- Frontend tests prove the critical workflows render and degrade safely.

## Verification

Run focused UI/API/CLI tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/verify_product_truth.py
make frontend-check
make frontend-visual-check
```

Run visual checks when UI layout or release-surface screenshots changed.
