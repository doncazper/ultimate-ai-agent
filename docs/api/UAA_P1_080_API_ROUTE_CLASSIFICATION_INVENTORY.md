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
| `local_readonly` | 20 |
| `local_sensitive` | 124 |
| `mutating_requires_authority` | 40 |

The current OpenAPI path count is `186` and `/api/manifest` currently reports
`187` route operations after later scoped FCC-V1-003 through
FCC-V1-006 Founder Loop route work, FCC-MEM-001 Memory Workbench/search/manual
intake and lifecycle routes, the governed memory L1/L2/L3 index routes, Phase
5 context-pack proposals, the Phase 6.1 internal Action proposal hook, the
dedicated read-only Source Readiness route, the Start Here read model route,
the universal proof index/detail routes, and FCC-MEM-022 feedback/probe/
observation/contradiction memory routes, plus the disabled-default tiny
exact-approved provider lane and the exact-approved provider credential
validation lane, plus the proposal-only provider router dry-run lane, plus the
run-attached approval queue inspection routes, plus the read-only run
observability inspection route, plus the read-only governed Memory context-pack
preview inspection route, plus the read-only Trust authority matrix route, plus
the exact Tier 1 allowlisted WebAccessGateway web evidence attachment route,
plus the repo-safe Coding Cockpit session read-model seed route, read-only
context-pack preview route, proposal-only patch proposal route, and blocked
patch apply readiness route, blocked test-command readiness route, blocked Git
review route, blocked live-preview readiness route, and blocked multi-agent
review readiness route, plus the governed runtime pilot Phase 04 contract,
invocation metadata, approval-ref binding, metadata-only local loopback model
receipt, exact read-only command status receipt, blocked receipt, and
safe-disable routes.
Governed runtime pilot Phase 04 adds one exact local loopback model-call route
and one exact allowlisted read-only command status route through
`RuntimeGateway`; it stores safe refs and metadata-only/redacted receipts and
keeps remote provider/model authority and arbitrary shell/subprocess execution
blocked.
UAA-P1-080 itself added no routes; stable
methods, operation IDs, tags, summaries, side-effect classes,
`requires_auth_future=True`, and `blocked_from_production=True` remain preserved
for the current boundary.

FCC-V1-001 later extends the same route inventory projection with
manifest-visible `auth_posture` and `approval_posture` fields. That extension
does not change UAA-P1-080 route behavior.

## Non-Goals

No middleware is added by UAA-P1-080. No auth, session gate, CORS, security
headers, idempotency enforcement, rate limits, dependencies, route behavior
changes, connector writes, provider/model calls, provider SDK calls,
shell/subprocess execution, local agent dispatch, context injection, raw prompt
or response persistence, action execution, memory writes, Code apply, public
beta, public distribution, production readiness, or production authority is
added by this milestone.

## Evidence

- `src/ultimate_ai_agent/api/contracts.py`
- `src/ultimate_ai_agent/api/manifest.py`
- `tests/fixtures/api_route_inventory_133.json`
- `docs/schemas/api_route_classification.schema.json`
- `scripts/verify_uaa_p1_080_api_route_classification.py`
- `tests/test_api_manifest.py`
- `tests/test_api_route_inventory_fixture.py`
- `tests/test_control_center_api_routes.py`
- `docs/control_center/route_status_manifest.json`
- `apps/control-center/src/components/ApiRouteInventoryPanel.tsx`

## Next

UAA-P1-081 Centralized FastAPI Security Headers and UAA-P1-082 Explicit
Loopback CORS Allowlist are complete as separate milestones. UAA-P1-083 Local
Protected-Route Bearer Gate is complete as a separate configured local perimeter
gate and cannot be claimed from this classification milestone. UAA-P1-084
through UAA-P1-086 are now implemented for the API perimeter gate lane.
