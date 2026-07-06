# UAA Hermes Runtime Context Budget Pressure

Status: Hermes Runtime Adoption Phase 24 repo-safe read model

Phase 24 adds Python Core ownership for context budget pressure posture:

- `RuntimeContextBudgetPressureReadModel`
- `RuntimeContextBudgetSegment`
- `RuntimeContextBudgetProposal`
- `GET /api/runtime/context-budget-pressure`
- `scripts/dev/uaa_runtime.py inspect-context-budget-pressure`
- Control Center Runtime readiness display
- `scripts/verify_hermes_runtime_adoption_phase_24.py`

This is context budget posture only. It exposes safe budget estimates, warning
refs, and review-only trimming or summary proposals. It does not perform hidden
compression, automatic context mutation, model summarization calls, context
injection, provider SDK calls, cache writes, raw context persistence, or
production authority.

## Full-Strength Version

UAA should eventually warn, trim, summarize, or ask the operator before a
runtime turn exceeds its context budget.

The full version requires explicit compression proposals, approval refs,
summary receipts, source coverage, retrieval logs, proof links, and operator
inspection of every included or removed source ref.

## Repo-Safe Current Version

The current implementation exposes a backend-owned read model containing:

- context budget segment refs
- pressure levels and budget estimates
- warning refs
- review-only trimming, summary, and operator-choice proposal refs
- source refs and retrieval log refs
- proof, evidence, verifier, and next-safe-action refs
- explicit blocked authority refs
- redactions for raw context, prompt, response, provider payload, and summary
  material

The Control Center only renders this backend-owned state. It cannot mint
authority and does not claim summarization, cache-write, hidden-compression, or
automatic context mutation capability.

## Blocked / Needs Authority

The following remain blocked:

- hidden compression
- automatic context mutation
- model summarization calls
- raw context persistence
- raw prompt persistence
- raw response persistence
- provider payload persistence
- context injection
- provider SDK calls
- cache writes
- production authority

## Promotion Path

Promotion requires:

1. Compression proposal with exact target refs and expected budget delta.
2. Approval ref bound to the exact proposal.
3. Redacted summary receipt with source coverage and verifier version.
4. Retrieval log proving which source refs were preserved or removed.
5. CLI/API/Core parity and route side-effect classification.
6. Control Center display that distinguishes warnings, proposals, receipts, and
   blocked hidden compression.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_context_budget_pressure.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_24.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run typecheck --prefix apps/control-center
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts
```
