# UAA-P1-052 API Service-Module Extraction Plan

Status: active gated foundation plan
Baseline: v0.102.3 / 0.102.3
Current OpenAPI path count: 112
Scope: planning and extraction guardrails only

This plan accepts the service-module boundary for a later UAA-P1-058 route
extraction. It does not move routes, add routes, remove routes, rename paths,
change operation IDs, add dependencies, add auth behavior, add runtime
authority, or expand product UI.

`src/ultimate_ai_agent/api/manifest.py` remains authoritative for side-effect
classes. OpenAPI remains the public route contract. `/api/manifest` remains
the typed metadata endpoint for the route inventory.

## Accepted Inputs

| Artifact | Role |
|---|---|
| `docs/approvals/UAA_P1_020_POLICY_ENGINE_CONSOLIDATION_MAP.md` | Freezes current policy and approval decision owners before extraction. |
| `docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md` | Freezes route group, owner, service module, auth posture, risk, release status, operation ID, and side-effect posture. |
| `src/ultimate_ai_agent/api/app.py` | Current monolithic route registration source. |
| `src/ultimate_ai_agent/api/route_registration.py` | Current canonical operation ID generation helper. |
| `src/ultimate_ai_agent/api/manifest.py` | Current API manifest and side-effect class source of truth. |
| `docs/api/openapi_contract.md` | Current public OpenAPI contract summary. |
| `docs/api/route_inventory.md` | Current route inventory summary. |

## Target Service Modules

| Target module | Route families owned | Dependency boundary | Initial extraction risk | Required tests |
|---|---|---|---|---|
| `ultimate_ai_agent.api.routes.system_service` | `/health`, `/version`, `/api/manifest` | May read package/version constants and manifest builder only; no storage, policy, model, connector, or local runtime mutation. | Low for `/health` and `/version`; low-medium for `/api/manifest` because manifest generation must avoid circular imports. | OpenAPI contract, API manifest, control-center route contracts, Foundation Gate. |
| `ultimate_ai_agent.api.routes.control_center_service` | `/control-center/*` summary and preview routes | May call existing storage/readiness helpers and return bounded safe refs only; no action execution, connector writes, model calls, email/calendar reads, notifications, or UI-only authority. | Medium because visible product language and route-status manifest must stay aligned. | Control Center API routes, focused frontend tests when UI contracts change, OpenAPI/API manifest. |
| `ultimate_ai_agent.api.routes.approval_service` | `/approvals/*`, `/consent/*` | May evaluate approval/consent contracts only; approval refs are identifiers and not authority without exact LocalApprovalAuthority validation. | Medium. | Approval authority tests, API manifest, OpenAPI contract. |
| `ultimate_ai_agent.api.routes.workspace_files_service` | `/files/*` | Must preserve safe refs, redaction, approval-bound proposal/apply/rollback gates, idempotency, and secret-like blocking. | High. | File tree/preview/proposal/apply/rollback/secret-blocking tests plus API contract checks. |
| `ultimate_ai_agent.api.routes.task_decomposition_service` | `/task-decomposition/*` | Must preserve disabled-by-default/local-dev auth, policy gates, approval refs, audit refs, and route side-effect classes. | High. | Task decomposition production API, approval integration, API contract checks. |
| `ultimate_ai_agent.api.routes.model_runtime_service` | `/model-*`, `/runtime-*`, local `/v1/*`, OpenWebUI local test routes | Must preserve disabled/fallback-first behavior, loopback/bearer gates where applicable, no provider authority, no tools/functions/streaming authority, and safe model readiness refs. | High. | M151/M167 local model tests, route contract checks. |
| `ultimate_ai_agent.api.routes.integrations_service` | `/integrations/mattermost/*` | Must preserve disabled-by-default bridge posture, bounded message ingress, safe refs, no credentials, no session material, and no unapproved connector writes. | High. | Mattermost API tests, redaction/static gate checks, API contract checks. |
| `ultimate_ai_agent.api.routes.memory_service` | `/memory/*` | Must preserve reviewed-write/evaluate boundaries, safe memory refs, no automatic memory writes, no context injection, and no raw source display. | High. | Memory API/storage tests, Foundation Gate, API contract checks. |
| `ultimate_ai_agent.api.routes.evidence_service` | `/ledger/*`, evidence receipt families | Must preserve validation-only receipt/evidence behavior and safe refs only. | Medium. | Ledger/evidence tests, API contract checks. |
| `ultimate_ai_agent.api.routes.governed_web_evidence_service` | `/web-evidence/*` | Must preserve allowlisted governed network-read contract and status route; no unrestricted browsing, downloads, redirects, browser automation, or hidden fetches. | Medium-high. | Governed web evidence tests, API manifest, Foundation Gate. |
| `ultimate_ai_agent.api.routes.catalog_service` | `/extensions/catalog` and future static catalog reads | Read-only metadata only; no plugin runtime import, callable catalog, connector writes, or execution. | Medium. | Extension catalog tests, API manifest. |
| `ultimate_ai_agent.api.routes.verification_service` | `/foundation-gate/*` and report/status validation routes | Inspection/report-only; no command execution from route handlers. | Medium. | Foundation Gate script/tests, API contract checks. |
| `ultimate_ai_agent.api.routes.contracts_service` | Adapter, context, contracts, truth, world-state validation-only contracts | Validation-only contracts; no runtime authority or model/provider output authority. | Medium. | Contract/truth/world-state tests plus API manifest. |
| `ultimate_ai_agent.api.routes.remote_worker_service` | `/remote-workers/*` | Planning/preview/status contracts only; no remote execution or public distribution authority. | High. | Remote worker contract tests, API manifest. |
| `ultimate_ai_agent.api.routes.observability_service` | `/observability/*` | Bounded redacted summaries only; no raw JSONL, prompts, provider payloads, local paths, logs, usernames, hostnames, environment dumps, credentials, or external telemetry. | Medium. | Session logging/client error tests, redaction/static checks. |
| `ultimate_ai_agent.api.routes.security_services` | `/secrets/*`, `/tools/*`, provider/cost/runtime-risk contract routes | Validation/dry-run/evaluate contracts only; no secret exposure, tool execution, provider SDK calls, or mutable authority. | Medium-high. | Secret broker, tool broker, provider/cost tests, API manifest. |

## Registration Pattern

1. Keep the existing module-level `app = FastAPI(...)` registration shape and
   preserve current middleware, validation-error sanitization, OpenAPI setup,
   exception handling, capability declarations, and manifest cache behavior.
2. Move one low-risk group into an `APIRouter` at a time.
3. Register the router from `app.py` through a small explicit helper, keeping
   route order stable where tests or docs depend on generated OpenAPI shape.
4. Continue using `use_route_names_as_operation_ids(app)` after all routers are
   registered so operation IDs remain generated from current route names.
5. Do not duplicate side-effect metadata in router modules. Update
   `src/ultimate_ai_agent/api/manifest.py` only when an accepted route-contract
   change requires it.
6. Do not move policy/approval decisions into React, route wrappers, or module
   globals. Service modules may call existing core helpers; they must not become
   parallel authorities.

## Extraction Order

| Order | Candidate | Reason | Gate before merge |
|---:|---|---|---|
| 1 | `system_service` for `GET /health` and `GET /version` | Smallest read-only pair, side-effect class `none`, no storage dependency, no local state mutation, no auth change, and lowest chance of product-language drift. | OpenAPI count 112, operation IDs unchanged, API manifest side-effect classes unchanged, Foundation Gate green. |
| 2 | Add `GET /api/manifest` to `system_service` only after circular-import review | Read-only metadata route, but it depends on the manifest builder and static capability declarations. | Same gates plus explicit manifest-cache behavior check. |
| 3 | `control_center_service` read-only summary routes | Product-facing but already inspection/preview oriented. This should wait until the first system extraction proves the registration pattern. | Control Center route-status manifest agreement and focused frontend/API route tests. |
| 4 | `contracts_service` validation-only routes | Mostly low mutation risk but broader contract surface. | Contract tests and API manifest checks. |
| 5 | Higher-risk local-dev, integration, memory, model, file, task, and web-evidence groups | These carry local-dev side effects, redaction, approval, disabled runtime, or governed network-read boundaries. | Dedicated scoped milestones per group. |

First UAA-P1-058 candidate: extract `GET /health` and `GET /version` into
`ultimate_ai_agent.api.routes.system_service`.

`GET /api/manifest` is intentionally second within the same target module
because it is read-only but more coupled to manifest generation and static
capability metadata.

## No-Route-Drift Rules

Every extraction must prove that these stay unchanged unless a separately
accepted route-contract milestone updates docs and tests in the same change:

- path
- HTTP method
- request schema
- response schema
- tags
- operation ID
- side-effect class
- validation-only posture
- auth posture
- capability declarations
- release status
- blocked capability lists
- OpenAPI path count
- `/api/manifest` route count and route metadata
- Control Center route-status manifest truth for visible actions

## Test And Verification Matrix

| Change type | Required checks |
|---|---|
| First system extraction | `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`; `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py`; `.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`; `git diff --check`. |
| Control Center route extraction | First-system checks plus focused Control Center API/frontend tests and route-status manifest checks. |
| Approval/policy route extraction | First-system checks plus `tests/test_approval_authority.py`, `tests/test_approval_authority_v2_contracts.py`, and `tests/test_approval_integration_kernel.py`. |
| File/task/memory/model/integration extraction | First-system checks plus the focused suite for the moved group and Foundation Gate static safety checks. |
| Documentation-only updates | Documentation integrity plus any map-specific route/manifest verifier used as evidence. |

## Acceptance Notes

- UAA-P1-052 accepts the extraction plan only; it does not implement
  UAA-P1-058.
- UAA-P1-058 remains blocked until UAA-P1-020, UAA-P1-021, this plan,
  Foundation Gate, OpenAPI, and `/api/manifest` are green.
- The first extraction must be a route-organization change only. Any route
  behavior, authority, lifecycle, storage, UI, connector, model, or network
  change must be rejected from that milestone.
