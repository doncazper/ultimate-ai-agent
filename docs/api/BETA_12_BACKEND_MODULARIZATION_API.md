# Beta 12 Backend Modularization And API Contract Hardening

Status: repo-safe beta-12 slice implemented.
Baseline: v0.104.0 / 0.104.0.

## Full-strength version

The full-strength API architecture should move each route family into a clear
service-owned module while preserving UAA's public OpenAPI contract,
`/api/manifest`, side-effect classes, route classifications, approval posture,
redaction, idempotency, rate limits, route-status truth, release-surface truth,
and Foundation Gate coverage.

## Repo-safe beta-12 version

Beta 12 extracts the app-owned Control Center shell/status route block into
`ultimate_ai_agent.api.control_center` using the existing `APIRouter` plus
method-aware `register_router_once` pattern. It preserves the current 169-route
OpenAPI/API manifest boundary, stable operation IDs, public paths, response
envelopes, redactions, route classifications, task-decomposition service
monkeypatch compatibility, and Control Center release-surface posture.

The extracted route block is:

- `GET /control-center/manifest`
- `GET /control-center/dashboard`
- `GET /control-center/status`
- `GET /control-center/routes`
- `GET /control-center/approvals/summary`
- `GET /control-center/approvals/queue`
- `GET /control-center/runs/observability`
- `GET /control-center/runtime-readiness/summary`
- `GET /control-center/settings/status`
- `GET /control-center/local-models/status`
- `GET /control-center/foundation-gate/summary`
- `GET /control-center/setup-assistant/summary`
- `POST /control-center/actions/preview`

Beta 12 also hardens route-truth checks so release-surface backend route refs
must match the live API operation ID, side-effect class, and route
classification. Concrete dynamic URL paths for task-decomposition run
lifecycle and Memory context-pack action proposal rate-limit groups now match
the same groups recorded for their templated route contract.

Verification:
`scripts/verify_beta_12_backend_modularization_api.py`.

## Blocked / Needs Authority

Beta 12 adds no provider/model calls, connector writes, web fetching, browser
automation, shell/subprocess execution, Git mutation, file mutation, background
autonomy, public beta, public release, production readiness, or production
authority. It does not create a canonical app factory, move middleware, change
auth/idempotency/rate-limit semantics, add new API routes, or promote any
Control Center action into runtime execution.

## Exact Promotion Path

Promote the next route group one module at a time through
`docs/api/UAA_P1_052_SERVICE_MODULE_EXTRACTION_PLAN.md`. Each promotion must
prove no route drift with OpenAPI, `/api/manifest`, route-status manifest,
release-surface manifest, module ownership assertions, focused API tests,
documentation integrity, product truth, operational maturity, and Foundation
Gate checks. Higher-risk groups such as files, task decomposition, model
runtime, integrations, web evidence, memory, and kernel routes need separate
approval, rollback/safe-disable, redaction, CLI parity, and evidence coverage
before they move or gain authority.
