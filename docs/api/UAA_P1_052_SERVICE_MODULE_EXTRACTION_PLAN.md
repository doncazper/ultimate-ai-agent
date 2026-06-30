# UAA-P1-052 API Service-Module Extraction Plan

Status: active gated foundation plan
Baseline: v0.104.0 / 0.104.0
Current OpenAPI path count: 151
Scope: planning, extraction guardrails, and first low-risk extraction status

This plan accepts the service-module boundary used by UAA-P1-058 for the first
low-risk route extraction and by later scoped route extractions. It does not add
routes, remove routes, rename paths, change operation IDs, add dependencies,
add auth behavior, add runtime authority, or expand product UI.

`src/ultimate_ai_agent/api/manifest.py` remains authoritative for side-effect
classes. OpenAPI remains the public route contract. `/api/manifest` remains
the typed metadata endpoint for the route inventory.

## Accepted Inputs

| Artifact | Role |
|---|---|
| `docs/approvals/UAA_P1_020_POLICY_ENGINE_CONSOLIDATION_MAP.md` | Freezes current policy and approval decision owners before extraction. |
| `docs/api/UAA_P1_021_FASTAPI_ROUTE_GROUPING_MAP.md` | Freezes route group, owner, service module, auth posture, risk, release status, operation ID, and side-effect posture. |
| `src/ultimate_ai_agent/api/app.py` | Current application factory/registration source. UAA-P1-058 now imports and registers the first system router from here. |
| `src/ultimate_ai_agent/api/route_registration.py` | Current canonical operation ID generation helper. |
| `src/ultimate_ai_agent/api/manifest.py` | Current API manifest and side-effect class source of truth. |
| `docs/api/openapi_contract.md` | Current public OpenAPI contract summary. |
| `docs/api/route_inventory.md` | Current route inventory summary. |

## Target Service Modules

| Target module | Route families owned | Dependency boundary | Initial extraction risk | Required tests |
|---|---|---|---|---|
| `ultimate_ai_agent.api.routes.system_service` | `/health`, `/version`; future candidate `/api/manifest` | May read package/version constants and manifest builder only; no storage, policy, model, connector, or local runtime mutation. | UAA-P1-058 extracted `/health` and `/version`; low-medium remains for `/api/manifest` because manifest generation must avoid circular imports. | OpenAPI contract, API manifest, control-center route contracts, Foundation Gate. |
| `ultimate_ai_agent.api.routes.control_center_service` | `/control-center/*` summary and preview routes | May call existing storage/readiness helpers and return bounded safe refs only; no action execution, connector writes, model calls, email/calendar reads, notifications, or UI-only authority. | Medium because visible product language and route-status manifest must stay aligned. | Control Center API routes, focused frontend tests when UI contracts change, OpenAPI/API manifest. |
| `ultimate_ai_agent.api.routes.runtime_service` | `/runtime/*` readiness, capability, boundary, and smoke-report validation routes | May expose readiness, capability, and validation summaries only; no lifecycle launch/stop, model download, provider SDK call, shell/subprocess execution, or production runtime authority. | Medium because runtime status is product-visible and must not imply lifecycle control. | Runtime readiness tests, OpenAPI contract, API manifest, Foundation Gate. |
| `ultimate_ai_agent.api.routes.approval_service` | `/approvals/*`, `/consent/*` | May evaluate approval/consent contracts only; approval refs are identifiers and not authority without exact LocalApprovalAuthority validation. | Medium. | Approval authority tests, API manifest, OpenAPI contract. |
| `ultimate_ai_agent.api.routes.workspace_files_service` | `/files/*` | Must preserve safe refs, redaction, approval-bound proposal/apply/rollback gates, idempotency, and secret-like blocking. | High. | File tree/preview/proposal/apply/rollback/secret-blocking tests plus API contract checks. |
| `ultimate_ai_agent.api.routes.task_decomposition_service` | `/task-decomposition/*` | Must preserve disabled-by-default/local-dev auth, policy gates, approval refs, audit refs, and route side-effect classes. | High. | Task decomposition production API, approval integration, API contract checks. |
| `ultimate_ai_agent.api.routes.model_runtime_service` | `/model-*`, `/model-runtime/*`, local `/v1/*`, OpenWebUI local test routes | Must preserve disabled/fallback-first behavior, loopback/bearer gates where applicable, no provider authority, no tools/functions/streaming authority, and safe model readiness refs. | High. | M151/M167 local model tests, route contract checks. |
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
| Future `ultimate_ai_agent.api.routes.settings_service` | Future settings/status routes only | May expose safe setup, feature-flag posture, kill-switch posture, disabled boundaries, and redacted local configuration status only after a separate scoped route contract. | Future-scoped; no current route. | Future Settings route/API/frontend tests plus OpenAPI/API manifest. |
| Future `ultimate_ai_agent.api.routes.workflow_service` | Future Founder Command Center aggregate/status routes only | May compose existing safe summaries for Today, Morning Briefing, Action Inbox, Memory Review, Evidence Timeline, and Weekly CEO Review only after a separate scoped route contract. | Future-scoped; no current route. | Future workflow route/API/frontend tests plus OpenAPI/API manifest. |

## Founder Command Center Surface Alignment

FCC-P1-012 accepts this document as the route-extraction plan for Founder
Command Center surfaces. It does not create a separate extraction plan, route
inventory, route module, or product roadmap. The surface mapping below is an
alignment layer over UAA-P1-021 and UAA-P1-052 so later FCC work can point to
the accepted service-module boundary without changing the current 151-path API.

| FCC surface | Current route families or status refs | Accepted target service module | Extraction posture |
|---|---|---|---|
| Today / workflow aggregation | `GET /control-center/today/summary`, current safe summary refs | `ultimate_ai_agent.api.routes.control_center_service` first; future aggregate-only work may use `workflow_service` after a scoped route contract exists | No new route in FCC-P1-012; preserve local-dev side-effect class and safe refs. |
| Morning Briefing | `GET /control-center/morning-briefing/summary` | `ultimate_ai_agent.api.routes.control_center_service`; future dedicated aggregation may use `workflow_service` | No email/calendar/notification runtime; preserve source-readiness and missing-contract posture. |
| Action Inbox / approvals | `/control-center/actions/*`, `/control-center/approvals/summary`, `/approvals/*` | `ultimate_ai_agent.api.routes.control_center_service` for UI summaries; `ultimate_ai_agent.api.routes.approval_service` for approval contracts | Approval refs remain identifiers; no action execution or grant shortcut. |
| Plans | `/task-decomposition/*` | `ultimate_ai_agent.api.routes.task_decomposition_service` | Use the accepted extraction name rather than a new `planning_service` module until a later contract changes it. |
| Memory | `/memory/*` plus current Founder Loop memory-review summaries | `ultimate_ai_agent.api.routes.memory_service` and, for current `/control-center/*` summaries, `ultimate_ai_agent.api.routes.control_center_service` | Preserve review-only memory posture, safe refs, and no context injection. |
| Evidence | `/receipts/*`, `/events/*`, `/gate/*`, `/observability/*`, `/control-center/foundation-gate/summary`, current Evidence Timeline refs | `ultimate_ai_agent.api.routes.evidence_service`, `ultimate_ai_agent.api.routes.verification_service`, and `ultimate_ai_agent.api.routes.observability_service` | Preserve validation/report-only posture and redacted summaries. |
| Files | `/files/*` | `ultimate_ai_agent.api.routes.workspace_files_service` | Use the accepted extraction name rather than a new `file_service` module; preserve approval, redaction, idempotency, and rollback gates. |
| Integrations | `/integrations/mattermost/*`, `/web-evidence/*`, and contract-only future connector surfaces | `ultimate_ai_agent.api.routes.integrations_service` and `ultimate_ai_agent.api.routes.governed_web_evidence_service` | No connector runtime/writes, unrestricted browsing, or credential handling. |
| Runtime / models | `/runtime/*`, `/model-runtime/*`, `/models/route/preview`, local `/v1/*`, OpenWebUI local test routes | `ultimate_ai_agent.api.routes.runtime_service` and `ultimate_ai_agent.api.routes.model_runtime_service` | Preserve disabled/fallback-first local runtime posture and no provider/model authority. |
| Settings | No dedicated route; related refs from `/control-center/status`, `/runtime/readiness`, `/runtime/capability-matrix`, and `/api/manifest` | Future `settings_service` only after a separate scoped route contract | FCC-P1-012 adds no settings route, feature-flag writes, or kill-switch execution. |
| System health/version/API manifest | `GET /health`, `GET /version`, `GET /api/manifest` | `ultimate_ai_agent.api.routes.system_service` | UAA-P1-058 extracted `GET /health` and `GET /version`; `GET /api/manifest` stays second because of manifest coupling. |

The product-facing architecture may use broader names such as
`planning_service`, `file_service`, `settings_service`, and `workflow_service`
when describing future product ownership. UAA-P1-052 extraction prompts must
use the accepted module names in this plan unless a later route-contract
milestone updates UAA-P1-021, this plan, OpenAPI, `/api/manifest`, and tests in
the same change.

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
| 1 | `system_service` for `GET /health` and `GET /version` | Smallest read-only pair, side-effect class `none`, no storage dependency, no local state mutation, no auth change, and lowest chance of product-language drift. | Implemented by UAA-P1-058 with then-current OpenAPI count 112, operation IDs unchanged, API manifest side-effect classes unchanged, and Foundation Gate green. |
| 2 | Add `GET /api/manifest` to `system_service` only after circular-import review | Read-only metadata route, but it depends on the manifest builder and static capability declarations. | Same gates plus explicit manifest-cache behavior check. |
| 3 | `control_center_service` read-only summary routes | Product-facing but already inspection/preview oriented. This should wait until the first system extraction proves the registration pattern. | Control Center route-status manifest agreement and focused frontend/API route tests. |
| 4 | `contracts_service` validation-only routes | Mostly low mutation risk but broader contract surface. | Contract tests and API manifest checks. |
| 5 | Higher-risk local-dev, integration, memory, model, file, task, and web-evidence groups | These carry local-dev side effects, redaction, approval, disabled runtime, or governed network-read boundaries. | Dedicated scoped milestones per group. |

UAA-P1-058 first extraction: `GET /health` and `GET /version` are extracted
into `ultimate_ai_agent.api.routes.system_service`.

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
- local-dev and governed-read posture where applicable
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
| First system extraction | `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`; `PYTHONPATH=src .venv/bin/python -m pytest tests/test_route_module_ownership.py tests/test_api_manifest.py tests/test_control_center_api_routes.py`; `.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`; `git diff --check`. |
| Control Center route extraction | First-system checks plus focused Control Center API/frontend tests and route-status manifest checks. |
| Approval/policy route extraction | First-system checks plus `tests/test_approval_authority.py`, `tests/test_approval_authority_v2_contracts.py`, and `tests/test_approval_integration_kernel.py`. |
| File/task/memory/model/integration extraction | First-system checks plus the focused suite for the moved group and Foundation Gate static safety checks. |
| Documentation-only updates | Documentation integrity plus any map-specific route/manifest verifier used as evidence. |

## Acceptance Notes

- UAA-P1-052 accepts the extraction plan and UAA-P1-058 records only the first
  low-risk route-module extraction.
- FCC-P1-012 accepts the Founder Command Center surface alignment only; it does
  not create a competing plan, route module, backend route, Control Center UI,
  product authority, or UAA-P1-058 extraction.
- Broader extraction remains blocked until UAA-P1-020, UAA-P1-021, this plan,
  Foundation Gate, OpenAPI, and `/api/manifest` stay green on the target branch.
- Every extraction must be a route-organization change only unless a separately
  accepted route-contract milestone says otherwise. Any route behavior,
  authority, lifecycle, storage, UI, connector, model, or network change must
  be rejected from route-organization milestones.
