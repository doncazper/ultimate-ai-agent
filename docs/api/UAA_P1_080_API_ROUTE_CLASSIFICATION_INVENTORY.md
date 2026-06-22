# UAA-P1-080 API Route Classification And Public/Protected Inventory

Status: Implemented.

UAA-P1-080 classifies the current FastAPI route boundary. It adds no routes and
does not change route behavior.

## Contract

Every current route in `/api/manifest` has exactly one route classification:

- `public_metadata`: harmless API metadata or status routes.
- `local_readonly`: local read-only route inventory or status surfaces that are
  still protected in production posture.
- `local_sensitive`: routes that expose or accept sensitive local state,
  previews, validation payloads, evidence, memory, files, model/runtime posture,
  observability, approvals, or connector-adjacent data without mutation
  authority.
- `mutating_requires_authority`: mutation-like or authority-bearing local
  routes that must stay exact-scoped, approval-bound, idempotent, auditable,
  rollback-aware, redacted, and tested before product authority is claimed.

Current route classification summary:

| Classification | Count |
|---|---:|
| `public_metadata` | 3 |
| `local_readonly` | 14 |
| `local_sensitive` | 82 |
| `mutating_requires_authority` | 13 |

The OpenAPI path count remains `112`. Stable paths, methods, operation IDs,
tags, summaries, side-effect classes, `requires_auth_future=True`, and
`blocked_from_production=True` remain preserved.

## Non-Goals

No middleware is added by UAA-P1-080. No auth, session gate, CORS, security
headers, idempotency enforcement, rate limits, dependencies, route behavior
changes, connector writes, provider/model calls, shell/subprocess execution,
action execution, memory writes, Code apply, public beta, public distribution,
production readiness, or production authority is added by this milestone.

## Evidence

- `src/ultimate_ai_agent/api/contracts.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `tests/fixtures/api_route_inventory_112.json`
- `docs/schemas/api_route_classification.schema.json`
- `scripts/verify_uaa_p1_080_api_route_classification.py`
- `tests/test_api_manifest.py`
- `tests/test_api_route_inventory_fixture.py`
- `tests/test_control_center_api_routes.py`
- `docs/control_center/route_status_manifest.json`
- `apps/control-center/src/components/ApiRouteInventoryPanel.tsx`

## Next

UAA-P1-081 Centralized FastAPI Security Headers and UAA-P1-082 Explicit
Loopback CORS Allowlist are complete as separate milestones. UAA-P1-083 remains
planned/queued and cannot be claimed from this classification milestone.
