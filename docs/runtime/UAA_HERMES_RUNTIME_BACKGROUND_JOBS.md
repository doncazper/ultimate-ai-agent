# UAA Hermes Runtime Background Jobs

Phase 31 adds backend-owned background job posture for the Hermes Runtime
Adoption program. It is a durable proposal/read model, not a scheduler,
background worker, or run-now control lane.

## Full-Strength

UAA can schedule governed local tasks with pause, resume, run-now, proof,
receipts, review, safe-disable posture, failure handling, and operator-visible
state. A mature lane would support exact job types only, with policy-bound
schedule windows, approval refs, idempotency, receipts, cancellation, retry
limits, rollback or safe-disable posture, and proof detail for every run.

## Repo-Safe

The current implementation is read/proposal only:

- Python Agent Core owns `RuntimeBackgroundJobsReadModel`.
- API route: `GET /api/runtime/background-jobs`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-background-jobs`.
- API, CLI, and Control Center bind the read model to AuthorityState capability
  `lane-ref:background-autonomy-scoped`. The current decision is deny because
  delegated background worker and supervisor adapters are unsupported.
- Control Center renders durable job refs, schedule policy, approval scope,
  idempotency, receipt plan, failure handling, proof refs, AuthorityState
  decision refs, unsupported adapter refs, and blocked authority refs.
- Mock fallback is visibly non-authoritative and keeps the same blocked
  execution posture.
- No job is scheduled, paused, resumed, run, retried, delivered, or executed.

## Blocked / Needs Authority

These remain blocked:

- autonomous background execution
- background workers
- schedulers
- autonomous retries
- external delivery
- provider calls
- shell execution
- connector writes
- Control Center minting authority
- raw job payload persistence

## Exact Authority Path

Any future executable background job capability requires all of the following
before a worker, scheduler, retry loop, delivery, or run-now action can run:

- exact job type
- explicit AuthorityLease mode/domain/capability mapping
- delegated mission scope when autonomy is requested
- schedule policy
- approval binding
- idempotency
- safe-disable posture
- receipt and proof refs
- bounded retry and failure handling
- cancellation or pause/resume semantics
- CLI/API/Core parity
- focused tests and verifier coverage
- route side-effect classification
- Control Center labels that distinguish proposal, paused, approval-required,
  blocked, denied, draft-degraded, and executable states
- implemented adapters; unsupported adapters remain denied instead of being
  flipped on by a broad flag

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_background_jobs.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_31.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, AuthorityState
binding is missing, CLI parity is lost, or any pause, resume, run-now, scheduler,
worker, autonomous retry, external delivery, provider call, shell execution,
connector write, raw payload persistence, or Control Center authority flag is
enabled.
