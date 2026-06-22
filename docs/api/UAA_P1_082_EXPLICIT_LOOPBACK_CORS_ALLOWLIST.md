# UAA-P1-082 Explicit Loopback CORS Allowlist

Status: Implemented.

UAA-P1-082 adds a fixed server-side CORS allowlist for the local Control Center
browser boundary. It does not add routes, does not change route behavior, and
does not create authentication or route authority.

## Contract

The loopback CORS policy ref is `cors:p1-082:loopback:v1`.

Allowed origins are explicit and limited to local Control Center dev/preview
origins:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://[::1]:5173`
- `http://localhost:4173`
- `http://127.0.0.1:4173`
- `http://[::1]:4173`

Allowed browser methods are `GET` and `POST`. Allowed request headers are
`Content-Type` and `X-Requested-With`. CORS credentials are disabled. Wildcard
CORS remains denied.

Allowed origins receive an exact `Access-Control-Allow-Origin` match. Disallowed
external, LAN, wrong-port, wildcard, and `null` origins do not receive CORS
allow headers, and disallowed preflight requests are rejected.

Security headers from UAA-P1-081 still apply to handled CORS preflight
responses.

## Non-Goals

No auth, session gate, idempotency enforcement, rate limits, route behavior
changes, connector writes, provider/model calls, shell/subprocess execution,
action execution, memory writes, Code apply, public beta, public distribution,
production readiness, or production authority is added by this milestone.

CORS is browser hardening, not authentication, authorization, route authority,
approval authority, rate limiting, or a production-readiness claim.

## Evidence

- `src/ultimate_ai_agent/api/cors.py`
- `src/ultimate_ai_agent/api/app.py`
- `tests/test_api_cors.py`
- `tests/test_api_manifest.py`
- `docs/schemas/api_loopback_cors.schema.json`
- `scripts/verify_uaa_p1_082_loopback_cors.py`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

## Next

UAA-P1-083 Local Bearer Or Session Gate For Sensitive Routes remains
planned/queued. CORS must not be treated as the auth boundary for those routes.
