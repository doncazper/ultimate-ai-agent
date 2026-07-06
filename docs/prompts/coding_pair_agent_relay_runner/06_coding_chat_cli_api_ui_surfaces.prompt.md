# Phase 06: Coding, Chat, CLI, API, And UI Surfaces

Goal: expose the paired-agent relay runner in operator surfaces without making
React state the product truth or raw JSON the primary workflow.

## Required Work

1. Add or harden CLI commands to inspect registry/readiness, create preview pair
   runs, inspect pair runs, start approved foreground runs when authority
   exists, stop runs, and inspect artifacts/receipts.
2. Add or harden API routes with stable operation ids, route side-effect
   classification, idempotency, local auth, and OpenAPI/API manifest tests.
3. Add `/coding` Pair Agents panel showing agent slots, task/scope/turn budget,
   readiness and approval state, live or simulated turn timeline, stop control
   when applicable, disagreement and candidate-action summaries,
   receipts/evidence refs, and blocked authority.
4. Add `/chat` entry point only if it reuses the same backend-owned contract
   and does not duplicate authority.
5. Avoid raw JSON for critical workflows.
6. Update docs and product language.
7. Add frontend tests when UI changes.

## Acceptance Criteria

- CLI/API/UI show the same backend-owned truth.
- UI cannot start a run without backend approval and policy.
- Missing authority is readable and actionable.
- Route manifest/OpenAPI stay aligned.
- Frontend safe validators reject unsafe authoritative payloads.

## Verification

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
```

Run frontend checks only when frontend files changed.

