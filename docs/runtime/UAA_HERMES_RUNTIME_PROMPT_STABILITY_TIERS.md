# UAA Hermes Runtime Prompt Stability Tiers

Status: Hermes Runtime Adoption Phase 23 repo-safe read model

Phase 23 adds Python Core ownership for prompt/input stability posture:

- `RuntimePromptStabilityTiersReadModel`
- `RuntimePromptStabilityTier`
- `GET /api/runtime/prompt-stability-tiers`
- `scripts/dev/uaa_runtime.py inspect-prompt-stability-tiers`
- Control Center Runtime readiness display
- `scripts/verify_hermes_runtime_adoption_phase_23.py`

This is prompt/input contract posture only. It does not store raw prompts,
materialize prompt bodies, inject hidden context, call models, call provider
SDKs, write prompt caches, treat model output as authority, or grant production
authority.

## Full-Strength Version

UAA should eventually separate stable identity/policy, durable context refs,
retrieval refs, volatile runtime state, and operator-turn data so runtime
delegation can be cached, audited, replayed, and proved without hiding prompt
composition from the operator.

The full version requires a safe prompt manifest, content hashes, cache policy,
redacted receipt envelopes, proof links, and clear operator inspection of what
each tier can and cannot contain.

## Repo-Safe Current Version

The current implementation exposes a backend-owned read model containing:

- prompt stability tier refs
- manifest refs and redacted tier hash refs
- cache policy refs
- safe source refs only
- proof, evidence, verifier, and next-safe-action refs
- explicit blocked authority refs
- redactions for prompt, response, provider payload, prompt material, and
  operator-turn text content

The Control Center only renders this backend-owned state. It cannot mint
authority and does not claim live model, cache-write, hidden-injection, or
prompt-materialization capability.

## Blocked / Needs Authority

The following remain blocked:

- hidden prompt injection
- raw prompt persistence
- raw response persistence
- provider payload persistence
- model-output authority
- model calls
- provider SDK calls
- context injection
- prompt cache writes
- production authority

## Promotion Path

Promotion requires:

1. Safe prompt manifest with stable tier refs and bounded redacted fields.
2. Hashes over safe refs and redacted manifests, not raw prompt bodies.
3. Cache policy that distinguishes stable, semi-stable, volatile, and
   operator-scoped no-cache tiers.
4. Redacted receipt envelope with policy decision, verifier version, and proof
   refs.
5. CLI/API/Core parity and route side-effect classification.
6. Control Center display that distinguishes cached/ref posture from actual
   prompt material.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_prompt_stability_tiers.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_23.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run typecheck --prefix apps/control-center
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts
```
