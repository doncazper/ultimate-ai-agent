# UAA Hermes Runtime Slash Command Registry

Phase 36 adds backend-owned slash command registry posture for the Hermes
Runtime Adoption program. It is metadata/read-model posture only. It does not
parse chat turns, execute commands, invoke runtimes, mutate state, call
providers, automate browsers, write connectors, or persist raw prompt/response
content.

## Full-Strength

UAA chat commands are centrally registered, documented, authority-classified,
and CLI/API aligned. A mature command registry would let the operator inspect
available command contracts, side-effect class, approval requirement,
idempotency posture, receipt plan, and proof refs before choosing whether a
command lane should be promoted.

## Repo-Safe

The current implementation is metadata-only:

- Python Agent Core owns `RuntimeSlashCommandRegistryReadModel`.
- API route: `GET /api/runtime/slash-command-registry`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-slash-command-registry`.
- Control Center renders command refs, trigger labels, side-effect classes,
  approval policy refs, idempotency policy refs, receipt plan refs, proof refs,
  promotion path refs, next safe action refs, and blocked authority refs.
- Mock fallback is visibly non-authoritative and keeps command execution,
  runtime invocation, state mutation, shell execution, provider calls, browser
  automation, connector writes, Control Center authority minting, raw prompt
  persistence, and raw response persistence blocked.
- No command parser or slash-command runtime execution is enabled.

## Blocked / Needs Authority

These remain blocked:

- chat slash-command execution
- runtime invocation
- state mutation
- shell execution
- provider/model calls
- browser automation
- connector writes
- Control Center authority minting
- raw prompt persistence
- raw response persistence
- production authority
- public release claims
- broad autonomy

## Exact Promotion Path

Promotion requires all of the following before any command can execute:

- command contract
- side-effect class
- approval policy
- idempotency policy
- receipt plan
- proof linkage
- exact lane scope
- safe-disable posture
- CLI/API/Core parity
- frontend truth labels
- focused tests and verifier coverage

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_slash_command_registry.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_36.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if route classification drifts, CLI parity is missing, or
any command execution, runtime invocation, state mutation, shell execution,
provider call, browser automation, connector write, raw prompt/response
persistence, or Control Center authority flag is enabled.
