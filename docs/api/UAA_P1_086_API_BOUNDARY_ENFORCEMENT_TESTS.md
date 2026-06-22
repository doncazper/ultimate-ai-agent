# UAA-P1-086 API Boundary Enforcement Tests

Status: Implemented.

UAA-P1-086 adds OpenAPI, `/api/manifest`, and route inventory enforcement
tests for the already-scoped API perimeter lane. It does not add routes,
middleware, auth authority, approval authority, durable idempotency storage,
distributed quota, runtime execution, public beta, public distribution,
production readiness, or production authority.

## Scope

The verifier and focused tests enforce that:

- OpenAPI path/method/operation ids match `/api/manifest`.
- The frozen route inventory fixture matches the live manifest projection.
- Public metadata routes stay limited to `GET /health`, `GET /version`, and
  `GET /api/manifest`.
- Non-public routes keep protected-route posture for the
  `auth:p1-083:local-protected-routes:v1` local bearer gate.
- Mutating routes keep exact authority posture, idempotency requirement, and
  `idempotency:p1-084:mutating-routes:v1`.
- Targeted expensive or sensitive routes keep
  `rate-limit:p1-085:targeted-local:v1` and valid rate-limit groups.
- Security headers apply to success and boundary-failure responses.
- Loopback CORS allows local Control Center origins and exposes the scoped
  authorization, idempotency, and rate-limit headers without credentials.
- The Control Center route-status manifest stays aligned with OpenAPI and the
  API manifest for operation id, side-effect class, and route classification.

## Verification

```bash
.venv/bin/python scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_boundary_enforcement.py
```

The combined API verifier lane now runs UAA-P1-080 through UAA-P1-086 in one
cached Python process.

## Safety

No new runtime authority.

These checks make perimeter drift visible. They do not make authority-heavy
Plans, Chat, Code, loop-binding, private beta-readiness, connector writes,
action execution, memory writes, provider/model calls, shell/subprocess
execution, public beta, public distribution, production readiness, or
production authority available.
