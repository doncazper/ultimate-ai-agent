# UAA-P1-085 Targeted Rate Limits For Expensive And Sensitive Routes

Status: Implemented.

UAA-P1-085 adds targeted local in-memory fixed-window rate limits for
expensive or sensitive route groups. The policy ref is
`rate-limit:p1-085:targeted-local:v1`.

## Contract

The runtime gate applies to selected route groups:

- `model_chat`
- `task_decomposition`
- `action_preview_proposal`
- `action_decision`
- `today_to_action_envelope`
- `chat_durable_receipt`
- `memory_review_decision`
- `local_model_validation`

When a targeted local fixed-window limit is reached, the API returns a redacted
`429` response with:

- `code=API_TARGETED_RATE_LIMITED`
- `policy_ref=rate-limit:p1-085:targeted-local:v1`
- `rate_limit_group`
- `retry_after_seconds`
- `Retry-After`
- `X-UAA-Rate-Limit-Policy`

The gate does not echo submitted request payloads. Failure responses still
receive the centralized UAA-P1-081 security headers. UAA-P1-082 CORS remains
exact-loopback only and exposes `Retry-After` plus
`X-UAA-Rate-Limit-Policy` so the local Control Center can display bounded
backpressure truth. CORS remains browser hardening, not auth.

The route inventory fixture records:

- `rate_limit_targeted`
- `rate_limit_posture`
- `rate_limit_policy_ref`
- `rate_limit_group`
- `route_rate_limit_posture_summary`
- `rate_limit_policy_ref`

## Non-Goals

No auth, distributed quota store, durable rate-limit store, billing quota,
tenant quota, dependency, enterprise auth, OAuth, password flow, connector
write, provider/model call, shell/subprocess execution, action execution,
memory write, Code apply, public beta, public distribution, production
readiness, or production authority is added by this milestone.

No production authority is enabled by this milestone.

The limiter is a local process backpressure guard. It is not a production abuse
platform, not authentication, not authorization, not billing, and not a
multi-user fairness system.

## Evidence

- `src/ultimate_ai_agent/api/rate_limits.py`
- `src/ultimate_ai_agent/api/app.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `src/ultimate_ai_agent/api/cors.py`
- `tests/test_api_rate_limits.py`
- `tests/test_api_manifest.py`
- `tests/test_api_route_inventory_fixture.py`
- `tests/test_api_cors.py`
- `tests/fixtures/api_route_inventory_129.json`
- `docs/schemas/api_targeted_rate_limits.schema.json`
- `scripts/verify_uaa_p1_085_targeted_rate_limits.py`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

## Next

UAA-P1-086 API Boundary Enforcement Tests is complete. UAA-P1-085
does not add broad API boundary enforcement-test coverage beyond this scoped
targeted rate-limit proof.
