# UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes

Status: Implemented.

UAA-P1-083 adds a simple local protected-route bearer gate for the current
browser-facing API boundary. Public metadata routes remain open; protected
routes are every route classified outside `public_metadata` in `/api/manifest`:
`local_readonly`, `local_sensitive`, and `mutating_requires_authority`.

## Contract

The local gate policy ref is `auth:p1-083:local-protected-routes:v1`.

The gate fails closed by default for protected routes. It is configured with
local environment refs only:

- `UAA_API_LOCAL_AUTH_ENABLED=1` enables the local protected-route gate.
- `UAA_API_LOCAL_BEARER` supplies the local bearer value.
- `UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY=1` is an explicit local-dev
  harness bypass for protected routes when no bearer is configured.

If `UAA_API_LOCAL_BEARER` is set, the gate accepts only that local bearer even
without `UAA_API_LOCAL_AUTH_ENABLED=1`. If no valid local bearer is configured
and the explicit dev-only bypass is not set, protected routes fail closed with
a redacted `503` response.

Allowed public metadata routes:

- `GET /health`
- `GET /version`
- `GET /api/manifest`
- `GET /openapi.json`

All other route classifications require `Authorization: Bearer <configured
local value>` unless the explicit dev-only bypass is set. Wrong or missing
bearer values return a redacted `401` response. Auth failure responses still
receive the centralized UAA-P1-081 security headers.

Routes with existing endpoint-specific local bearer gates, such as local
`/v1`, task decomposition, and Mattermost bridge routes, may satisfy the P1-083
perimeter with their already-configured local bearer so callers do not need two
different bearer values for one route. Those endpoint gates remain separately
disabled-by-default and scoped to their own safety contracts.

CORS remains browser hardening, not auth. UAA-P1-082 preflight behavior stays
limited to explicit local Control Center origins, no wildcard CORS, and no CORS
credentials.

## Non-Goals

No enterprise auth, multi-user auth, OAuth, roles, password flow, cookie/session
credentials, connector writes, provider/model calls, shell/subprocess
execution, action execution, memory writes, Code apply, public beta, public
distribution, production readiness, or production authority is added by this
milestone.

No production authority is granted by this local gate.
No production authority is granted by the explicit dev-only bypass.

The local bearer gate is a local perimeter control. It is not approval
authority, product authority, model/provider authority, or a production
security certification.

## Evidence

- `src/ultimate_ai_agent/api/local_auth.py`
- `src/ultimate_ai_agent/api/app.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `tests/test_api_local_auth_gate.py`
- `tests/test_api_manifest.py`
- `docs/schemas/api_local_auth_gate.schema.json`
- `scripts/verify_uaa_p1_083_local_auth_gate.py`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

## Next

UAA-P1-084 Mutating Route Idempotency Enforcement Audit is implemented as a
separate boundary gate. The local bearer gate does not add durable idempotency
storage, targeted rate limits, or API boundary enforcement-test coverage beyond
this scoped P1-083 proof.
