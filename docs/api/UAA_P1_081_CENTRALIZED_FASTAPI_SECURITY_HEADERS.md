# UAA-P1-081 Centralized FastAPI Security Headers

Status: Implemented.

UAA-P1-081 adds centralized response security headers for the browser-facing
FastAPI boundary. It does not add routes and does not change route behavior.

## Contract

All handled FastAPI responses receive the shared policy ref
`security-headers:p1-081:v1` and these centralized headers:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `X-Frame-Options: DENY`
- `Content-Security-Policy` with `default-src 'self'`,
  `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'none'`, and local
  loopback dev connect exceptions.
- `Permissions-Policy` denying unused browser capabilities including camera,
  microphone, geolocation, display capture, payment, USB, and XR tracking.

`Strict-Transport-Security` is emitted only when the incoming request is HTTPS.
HTTP/local loopback responses intentionally do not emit HSTS.

## Non-Goals

No auth, session gate, CORS policy, idempotency enforcement, rate limits,
dependencies, route behavior changes, connector writes, provider/model calls,
shell/subprocess execution, action execution, memory writes, Code apply, public
beta, public distribution, production readiness, or production authority is
added by this milestone.

Security headers are browser hardening only. They are not authentication,
authorization, route authority, approval authority, CORS, rate limiting, or a
production-readiness claim.

## Evidence

- `src/ultimate_ai_agent/api/security_headers.py`
- `src/ultimate_ai_agent/api/app.py`
- `tests/test_api_security_headers.py`
- `tests/test_api_manifest.py`
- `docs/schemas/api_security_headers.schema.json`
- `scripts/verify_uaa_p1_081_fastapi_security_headers.py`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

## Next

UAA-P1-082 Explicit Loopback CORS Allowlist remains planned/queued. CORS is
browser hardening, not authentication, and must be scoped separately.
