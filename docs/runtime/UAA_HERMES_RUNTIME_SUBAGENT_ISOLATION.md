# UAA Hermes Runtime Subagent Isolation

Phase 32 adds backend-owned subagent identity and isolation posture for the
Hermes Runtime Adoption program. It is a readiness/read model, not live
subagent dispatch, background fan-out, or autonomous delegation.

## Full-Strength

UAA can delegate work to isolated agent workers with scoped context, tools,
memory, authority, budgets, kill switches, receipts, and proof. A mature lane
would let an operator configure exact roles such as implementer, reviewer, and
verifier, then supervise their outputs as untrusted proposals through UAA-owned
approval and evidence contracts.

## Repo-Safe

The current implementation is metadata/readiness only:

- Python Agent Core owns `RuntimeSubagentIsolationReadModel`.
- API route: `GET /api/runtime/subagent-isolation`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-subagent-isolation`.
- Control Center renders role refs, scope envelopes, context pack grants, tool
  grants, memory grants, budgets, kill switches, receipt plans, proof refs,
  review artifacts, and blocked authority refs.
- Mock fallback is visibly non-authoritative and keeps the same blocked
  dispatch posture.
- Agent output is represented only as safe refs and review artifacts.
- No subagent is spawned, dispatched, run in the background, granted tools,
  granted memory transfer, or allowed to write externally.

## Blocked / Needs Authority

These remain blocked:

- live subagent dispatch
- background fan-out
- cross-agent memory transfer
- tool sharing
- autonomous delegation
- provider calls
- shell execution
- connector writes
- Control Center minting authority
- raw transcript or raw agent-output persistence

## Exact Promotion Path

Promotion requires all of the following before any real subagent lane can run:

- role contract
- scope envelope
- context pack grant
- toolset grant
- memory grant
- approval binding
- budget and turn limits
- kill switch
- receipt and proof refs
- revocation and safe-disable posture
- CLI/API/Core parity
- focused tests and verifier coverage
- route side-effect classification
- Control Center labels that distinguish readiness, review-only, blocked, and
  executable states

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_subagent_isolation.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_32.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, CLI parity is
lost, or any live dispatch, background fan-out, cross-agent memory transfer,
tool sharing, autonomous delegation, provider call, shell execution, connector
write, raw transcript persistence, raw agent-output persistence, or Control
Center authority flag is enabled.
