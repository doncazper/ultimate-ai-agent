# UAA-P1-084 Mutating Route Idempotency Enforcement Audit

Status: Implemented.

UAA-P1-084 adds a runtime boundary check for routes classified as
`mutating_requires_authority`. Before a mutating handler can run, the request
must carry either `X-UAA-Idempotency-Key` or `X-UAA-Idempotency-Ref` with a
safe idempotency value. The policy ref is
`idempotency:p1-084:mutating-routes:v1`.

## Contract

The current mutating route set is the 47 routes classified as
`mutating_requires_authority` in `/api/manifest`.

Requests to those routes without an idempotency header fail with a redacted
`428` response. Requests with an invalid idempotency header fail with a
redacted `400` response. Failure responses do not echo the submitted
idempotency value or request body and still receive the centralized UAA-P1-081
security headers.

The allowed idempotency headers are:

- `X-UAA-Idempotency-Key`
- `X-UAA-Idempotency-Ref`

UAA-P1-082 CORS stays exact-loopback only and now allows those two request
headers so the local Control Center can call mutating routes through the same
browser boundary. CORS remains browser hardening, not auth.

The route inventory fixture records:

- `idempotency_required`
- `idempotency_posture`
- `idempotency_policy_ref`
- `route_idempotency_posture_summary`
- `idempotency_audit_policy_ref`

## Non-Goals

No durable dedupe store, exactly-once execution guarantee, replay execution,
body hashing, request payload storage, rate limit, enterprise auth, OAuth,
password flow, connector write, provider/model call, shell/subprocess
execution, action execution, memory write, Code apply, public beta, public
distribution, production readiness, or production authority is added by this
milestone.

This idempotency gate grants no production authority.

The header gate proves mutating requests carry an idempotency key or scoped
idempotency ref before handler execution. It does not prove duplicate replay
semantics for every route owner; those remain route-owner responsibilities and
later enforcement-test coverage.

## Evidence

- `src/ultimate_ai_agent/api/idempotency.py`
- `src/ultimate_ai_agent/api/app.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `src/ultimate_ai_agent/api/cors.py`
- `tests/test_api_idempotency_audit.py`
- `tests/test_api_manifest.py`
- `tests/test_api_route_inventory_fixture.py`
- `tests/fixtures/api_route_inventory_133.json`
- `docs/schemas/api_mutating_route_idempotency_audit.schema.json`
- `scripts/verify_uaa_p1_084_mutating_route_idempotency.py`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

## Next

UAA-P1-085 Targeted Rate Limits For Expensive And Sensitive Routes and
UAA-P1-086 API Boundary Enforcement Tests are complete as separate scoped
milestones. UAA-P1-084 does not add rate limits or broad API boundary
enforcement-test coverage beyond this scoped idempotency proof.
