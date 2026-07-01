# UAA-P1-021 FastAPI Route Grouping Map

Status: active gated foundation map
Baseline: v0.104.0 / 0.104.0
Current OpenAPI path count: 159
Scope: documentation and route ownership inventory only

This map records the current FastAPI route groups for UAA-P1-058 and future
service-module extraction work. It does not move routes, add routes, remove
routes, rename paths, change operation IDs, add dependencies, add auth
behavior, add runtime authority, or implement product UI expansion.

`src/ultimate_ai_agent/api/manifest.py` remains authoritative for side-effect
classes. OpenAPI remains the public route contract. `/api/manifest` remains the
typed metadata endpoint for route inventory and capabilities.

## Current Agreement

| Contract surface | Result |
|---|---|
| OpenAPI path count | 159 paths. |
| `/api/manifest` route count | 159 routes. |
| Operation ID posture | Stable generated IDs are unique for all current routes. |
| Side-effect classes | All current routes use `none`, `validation_only`, `local_dev_workspace_only`, or `governed_network_read_only`. |
| Route-module ownership tests | UAA-P1-059 checks every current route against this map for owner, target service module, side-effect class, risk class, auth posture, release status, route-count posture, operation ID posture, and evidence behavior. |
| Control Center route-status manifest | Backend route refs checked against `/api/manifest`; 0 missing and 0 path/method/operation/side-effect mismatches. |
| Route inventory doc | Current count matches 159; inventory is summarized by group and remains subordinate to `/api/manifest`. |

## Mismatch Findings

| Area | Finding | Required action |
|---|---|---|
| OpenAPI vs `/api/manifest` | No current route count, path, operation ID, or side-effect mismatch found by required verifiers. | Keep checks release-blocking. |
| Control Center route-status manifest vs `/api/manifest` | No current mismatch for manifest entries that name backend routes. The route-status manifest is a visible-action subset, not an all-route inventory. | Do not use it as the source for non-Control Center service extraction. |
| `docs/api/route_inventory.md` vs `/api/manifest` | Count and high-level groups agree. The doc intentionally summarizes broad groups rather than listing every current route row. | This UAA-P1-021 map is the exhaustive grouping companion. |
| UAA-P1-058 readiness | First extraction is now limited to `GET /health` and `GET /version` under `system_service`; broader extraction remains gated by this map, UAA-P1-020, UAA-P1-052, Foundation Gate, OpenAPI, and API manifest stability. | Do not start broader extraction until all are accepted and green on the target branch. |
| UAA-P1-059 ownership gate | `tests/test_route_module_ownership.py` now fails if a route appears without ownership, module, risk, auth, release, operation ID, side-effect, route-count, or evidence behavior coverage. | Keep this check in the route-modularity lane before broader extraction. |

## Route Group Summary

| Route group | Count | Owner | Target service module | Auth posture | Side-effect class mix | Risk class | Operation ID posture | Release status |
|---|---:|---|---|---|---|---|---|---|
| `adapter-boundary` | 1 | `core-runtime` | `contracts_service` | future auth required | `validation_only`:1 | low | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `api-boundary` | 1 | `system` | `system_service` | none | `none`:1 | low | stable/generated from path; unique | `status_available_not_completion` |
| `approval-authority` | 4 | `approval-authority` | `approval_service` | future auth required | `validation_only`:4 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `consent` | 2 | `consent` | `approval_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `context-budget` | 1 | `context` | `contracts_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `contracts` | 2 | `contracts` | `contracts_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `control-center` | 60 | `control-center` | `control_center_service` | local status or future auth per route | `governed_network_read_only`:1, `local_dev_workspace_only`:46, `validation_only`:13 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `cost-governor` | 3 | `cost-governor` | `cost_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `extension-catalog` | 1 | `extension-catalog` | `extension_catalog_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | `status_available_not_completion` |
| `files` | 6 | `workspace-files` | `workspace_files_service` | future auth required and local safe refs | `local_dev_workspace_only`:6 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `foundation-gate` | 2 | `foundation-gate` | `verification_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | `status_available_not_completion` |
| `kernel` | 1 | `kernel` | `kernel_service` | future auth required | `local_dev_workspace_only`:1 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `ledger` | 3 | `ledger` | `evidence_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `mattermost` | 8 | `mattermost` | `integrations_service` | disabled by default and future auth required | `local_dev_workspace_only`:8 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `memory` | 3 | `memory` | `memory_service` | future auth required and local safe refs | `local_dev_workspace_only`:3 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `model-router` | 2 | `model-router` | `model_runtime_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | `preview_available_not_execution` |
| `model-runtime` | 8 | `model-runtime` | `model_runtime_service` | future auth required | `validation_only`:8 | medium | stable/generated from path; unique | `preview_available_not_execution` |
| `observability` | 2 | `observability` | `observability_service` | future auth required and local redacted summaries | `local_dev_workspace_only`:2 | medium | stable/generated from path; unique | `status_available_not_completion` |
| `openwebui-local-test` | 2 | `local-model-runtime` | `model_runtime_service` | loopback bearer required when enabled | `local_dev_workspace_only`:2 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `provider-registry` | 3 | `provider-registry` | `provider_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | `preview_available_not_execution` |
| `remote-workers` | 8 | `remote-workers` | `remote_worker_service` | future auth required | `validation_only`:8 | high | stable/generated from path; unique | `preview_available_not_execution` |
| `runtime-boundary` | 1 | `runtime` | `runtime_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | `status_available_not_completion` |
| `runtime-readiness` | 3 | `runtime-readiness` | `runtime_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | `status_available_not_completion` |
| `secret-broker` | 2 | `secret-broker` | `secret_service` | future auth required | `validation_only`:2 | high | stable/generated from path; unique | `preview_available_not_execution` |
| `system` | 2 | `system` | `system_service` | none | `none`:2 | low | stable/generated from path; unique | `status_available_not_completion` |
| `task-decomposition` | 16 | `task-decomposition` | `task_decomposition_service` | disabled by default and explicit local auth | `local_dev_workspace_only`:16 | high | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `tool-broker` | 3 | `tool-broker` | `tool_service` | future auth required | `validation_only`:3 | high | stable/generated from path; unique | `preview_available_not_execution` |
| `truth` | 6 | `truth` | `truth_service` | future auth required | `validation_only`:6 | medium | stable/generated from path; unique | `preview_available_not_execution` |
| `web-evidence` | 2 | `governed-web-evidence` | `governed_web_evidence_service` | future auth required for request path | `governed_network_read_only`:1, `none`:1 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |
| `world-state` | 1 | `world-state` | `contracts_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | `partial_backend_not_product_ready` |

## All Current Routes

Columns: method, path, operation ID, side-effect class, validation-only, future-auth posture, blocked-from-production.

### `adapter-boundary`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/adapter-manifest/validate` | `post_adapter_manifest_validate` | `validation_only` | yes | future | yes |

### `api-boundary`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/api/manifest` | `get_api_manifest` | `none` | no | future | yes |

### `approval-authority`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/approvals/grants/validate` | `post_approvals_grants_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/receipts/validate` | `post_approvals_receipts_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/requests/validate` | `post_approvals_requests_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/validate` | `post_approvals_validate` | `validation_only` | yes | future | yes |

### `consent`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/consent/evaluate` | `post_consent_evaluate` | `validation_only` | yes | future | yes |
| POST | `/consent/grants/validate` | `post_consent_grants_validate` | `validation_only` | yes | future | yes |

### `context-budget`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/context-budget/validate` | `post_context_budget_validate` | `validation_only` | yes | future | yes |

### `contracts`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/context-packs/validate` | `post_context_packs_validate` | `validation_only` | yes | future | yes |
| POST | `/contracts/validate` | `post_contracts_validate` | `validation_only` | yes | future | yes |

### `control-center`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/control-center/actions/inbox` | `get_control_center_actions_inbox` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/preview` | `post_control_center_actions_preview` | `validation_only` | yes | future | yes |
| POST | `/control-center/actions/{action_id}/approve` | `post_control_center_actions_action_id_approve` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/defer` | `post_control_center_actions_action_id_defer` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/edit` | `post_control_center_actions_action_id_edit` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/local-task/commit` | `post_control_center_actions_action_id_local_task_commit` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/actions/{action_id}/receipt` | `get_control_center_actions_action_id_receipt` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/reject` | `post_control_center_actions_action_id_reject` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/approvals/summary` | `get_control_center_approvals_summary` | `validation_only` | yes | future | yes |
| POST | `/control-center/chat/turns` | `post_control_center_chat_turns` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/chat/turns/{turn_ref}/handoff` | `post_control_center_chat_turns_turn_ref_handoff` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/chat/turns/{turn_ref}/receipt` | `get_control_center_chat_turns_turn_ref_receipt` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/dashboard` | `get_control_center_dashboard` | `validation_only` | yes | future | yes |
| GET | `/control-center/evidence/timeline` | `get_control_center_evidence_timeline` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/foundation-gate/summary` | `get_control_center_foundation_gate_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/local-models/status` | `get_control_center_local_models_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/manifest` | `get_control_center_manifest` | `validation_only` | yes | future | yes |
| GET | `/control-center/memory/citation-integrity` | `get_control_center_memory_citation_integrity` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/context-manifest` | `get_control_center_memory_context_manifest` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/context-packs` | `get_control_center_memory_context_packs` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/context-packs/{context_pack_ref}/action-proposal` | `post_control_center_memory_context_packs_context_pack_ref_action_proposal` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/contradictions` | `get_control_center_memory_contradictions` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/feedback` | `post_control_center_memory_feedback` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/follow-ups` | `get_control_center_memory_follow_ups` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/impact-graph` | `get_control_center_memory_impact_graph` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/l1-index` | `get_control_center_memory_l1_index` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/l2-index` | `get_control_center_memory_l2_index` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/l3-index` | `get_control_center_memory_l3_index` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/maintenance-runs` | `get_control_center_memory_maintenance_runs` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/observation-candidates` | `get_control_center_memory_observation_candidates` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/probe` | `get_control_center_memory_probe` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/quality-issues` | `get_control_center_memory_quality_issues` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/recall-health` | `get_control_center_memory_recall_health` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/retrieval-diagnostics` | `get_control_center_memory_retrieval_diagnostics` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/review` | `get_control_center_memory_review` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/manual-candidate` | `post_control_center_memory_review_manual_candidate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/accept` | `post_control_center_memory_review_candidate_ref_accept` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/correct` | `post_control_center_memory_review_candidate_ref_correct` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/defer` | `post_control_center_memory_review_candidate_ref_defer` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/forget-request` | `post_control_center_memory_review_candidate_ref_forget_request` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/merge` | `post_control_center_memory_review_candidate_ref_merge` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/review/{candidate_ref}/receipt` | `get_control_center_memory_review_candidate_ref_receipt` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/reject` | `post_control_center_memory_review_candidate_ref_reject` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/supersede` | `post_control_center_memory_review_candidate_ref_supersede` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/search` | `get_control_center_memory_search` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/workbench` | `get_control_center_memory_workbench` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/morning-briefing/summary` | `get_control_center_morning_briefing_summary` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/providers/credentials/validate` | `post_control_center_providers_credentials_validate` | `governed_network_read_only` | no | future | yes |
| POST | `/control-center/providers/exact-approved-lanes/tiny` | `post_control_center_providers_exact_approved_lanes_tiny` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/providers/router/dry-run` | `post_control_center_providers_router_dry_run` | `validation_only` | yes | future | yes |
| GET | `/control-center/providers/setup-guide` | `get_control_center_providers_setup_guide` | `validation_only` | yes | future | yes |
| GET | `/control-center/routes` | `get_control_center_routes` | `validation_only` | yes | future | yes |
| GET | `/control-center/runtime-readiness/summary` | `get_control_center_runtime_readiness_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/settings/status` | `get_control_center_settings_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/setup-assistant/summary` | `get_control_center_setup_assistant_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/sources/readiness` | `get_control_center_sources_readiness` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/status` | `get_control_center_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/storage/status` | `get_control_center_storage_status` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/action-envelope` | `post_control_center_today_action_envelope` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/today/summary` | `get_control_center_today_summary` | `local_dev_workspace_only` | no | future | yes |

### `cost-governor`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/costs/budgets/validate` | `post_costs_budgets_validate` | `validation_only` | yes | future | yes |
| POST | `/costs/estimate/preview` | `post_costs_estimate_preview` | `validation_only` | yes | future | yes |
| POST | `/costs/evaluate` | `post_costs_evaluate` | `validation_only` | yes | future | yes |

### `extension-catalog`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/extensions/catalog` | `get_extensions_catalog` | `validation_only` | yes | future | yes |

### `files`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/files/diff/preview` | `post_files_diff_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/read/preview` | `post_files_read_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/refs/validate` | `post_files_refs_validate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/review/approvals/capture` | `post_files_review_approvals_capture` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/tree/preview` | `post_files_tree_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/write/propose` | `post_files_write_propose` | `local_dev_workspace_only` | no | future | yes |

### `foundation-gate`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/gate/reports/validate` | `post_gate_reports_validate` | `validation_only` | yes | future | yes |
| POST | `/gate/shadow-replay/validate` | `post_gate_shadow_replay_validate` | `validation_only` | yes | future | yes |

### `kernel`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/kernel/tasks/run` | `post_kernel_tasks_run` | `local_dev_workspace_only` | no | future | yes |

### `ledger`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/events/validate` | `post_events_validate` | `validation_only` | yes | future | yes |
| POST | `/receipts/preview` | `post_receipts_preview` | `validation_only` | yes | future | yes |
| POST | `/runs/state/transition/validate` | `post_runs_state_transition_validate` | `validation_only` | yes | future | yes |

### `mattermost`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/integrations/mattermost/audit` | `get_integrations_mattermost_audit` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/events/message` | `post_integrations_mattermost_events_message` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/receipts` | `get_integrations_mattermost_receipts` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/bind` | `post_integrations_mattermost_roles_bind` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/roles/catalog` | `get_integrations_mattermost_roles_catalog` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/suggest` | `post_integrations_mattermost_roles_suggest` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/unbind` | `post_integrations_mattermost_roles_unbind` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/status` | `get_integrations_mattermost_status` | `local_dev_workspace_only` | no | future | yes |

### `memory`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/memory/query/preview` | `post_memory_query_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/memory/records/validate` | `post_memory_records_validate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/memory/write/evaluate` | `post_memory_write_evaluate` | `local_dev_workspace_only` | no | future | yes |

### `model-router`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/models/profiles/validate` | `post_models_profiles_validate` | `validation_only` | yes | future | yes |
| POST | `/models/route/preview` | `post_models_route_preview` | `validation_only` | yes | future | yes |

### `model-runtime`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/model-runtime/local/endpoints/validate` | `post_model_runtime_local_endpoints_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/execution/validate` | `post_model_runtime_local_execution_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/simulate-fallback` | `post_model_runtime_local_simulate_fallback` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/smoke/validate` | `post_model_runtime_local_smoke_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/manifests/validate` | `post_model_runtime_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/requests/validate` | `post_model_runtime_requests_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/responses/validate` | `post_model_runtime_responses_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/simulate` | `post_model_runtime_simulate` | `validation_only` | yes | future | yes |

### `observability`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/observability/client-errors` | `post_observability_client_errors` | `local_dev_workspace_only` | no | future | yes |
| GET | `/observability/session-events` | `get_observability_session_events` | `local_dev_workspace_only` | no | future | yes |

### `openwebui-local-test`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/v1/chat/completions` | `post_v1_chat_completions` | `local_dev_workspace_only` | no | future | yes |
| GET | `/v1/models` | `get_v1_models` | `local_dev_workspace_only` | no | future | yes |

### `provider-registry`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/providers/manifests/validate` | `post_providers_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/providers/resolve` | `post_providers_resolve` | `validation_only` | yes | future | yes |
| POST | `/providers/results/validate` | `post_providers_results_validate` | `validation_only` | yes | future | yes |

### `remote-workers`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/remote-workers/dry-run` | `post_remote_workers_dry_run` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/jobs/validate` | `post_remote_workers_jobs_validate` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/mesh/status` | `get_remote_workers_mesh_status` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/nodes/validate` | `post_remote_workers_nodes_validate` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/policy/validate` | `post_remote_workers_policy_validate` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/status` | `get_remote_workers_status` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/tailnet/status` | `get_remote_workers_tailnet_status` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/transports/validate` | `post_remote_workers_transports_validate` | `validation_only` | yes | future | yes |

### `runtime-boundary`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/local-runtime/validate` | `post_local_runtime_validate` | `validation_only` | yes | future | yes |

### `runtime-readiness`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/runtime/capability-matrix` | `get_runtime_capability_matrix` | `validation_only` | yes | future | yes |
| GET | `/runtime/readiness` | `get_runtime_readiness` | `validation_only` | yes | future | yes |
| POST | `/runtime/smoke-reports/validate` | `post_runtime_smoke_reports_validate` | `validation_only` | yes | future | yes |

### `secret-broker`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/secrets/access/evaluate` | `post_secrets_access_evaluate` | `validation_only` | yes | future | yes |
| POST | `/secrets/credentials/validate` | `post_secrets_credentials_validate` | `validation_only` | yes | future | yes |

### `system`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| GET | `/health` | `get_health` | `none` | no | future | yes |
| GET | `/version` | `get_version` | `none` | no | future | yes |

### `task-decomposition`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/task-decomposition/approval-requests` | `post_task_decomposition_approval_requests` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/approvals` | `get_task_decomposition_approvals` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/approvals/grants/capture` | `post_task_decomposition_approvals_grants_capture` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/approvals/revoke` | `post_task_decomposition_approvals_revoke` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/audit` | `get_task_decomposition_audit` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/capabilities/register` | `post_task_decomposition_capabilities_register` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/catalog` | `get_task_decomposition_catalog` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/classify` | `post_task_decomposition_classify` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/decompose` | `post_task_decomposition_decompose` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/examples/init` | `post_task_decomposition_examples_init` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/metrics` | `get_task_decomposition_metrics` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/plans/execute` | `post_task_decomposition_plans_execute` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/plans/validate` | `post_task_decomposition_plans_validate` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/registry/export` | `get_task_decomposition_registry_export` | `local_dev_workspace_only` | no | future | yes |
| POST | `/task-decomposition/run` | `post_task_decomposition_run` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/status` | `get_task_decomposition_status` | `local_dev_workspace_only` | no | future | yes |

### `tool-broker`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/tools/manifests/validate` | `post_tools_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/tools/requests/dry-run` | `post_tools_requests_dry_run` | `validation_only` | yes | future | yes |
| POST | `/tools/requests/evaluate` | `post_tools_requests_evaluate` | `validation_only` | yes | future | yes |

### `truth`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/truth/conflicts/validate` | `post_truth_conflicts_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/evidence/validate` | `post_truth_evidence_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/freshness/check` | `post_truth_freshness_check` | `validation_only` | yes | future | yes |
| POST | `/truth/grounding-policy/validate` | `post_truth_grounding_policy_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/route` | `post_truth_route` | `validation_only` | yes | future | yes |
| POST | `/truth/sources/validate` | `post_truth_sources_validate` | `validation_only` | yes | future | yes |

### `web-evidence`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/web-evidence/request` | `post_web_evidence_request` | `governed_network_read_only` | no | future | yes |
| GET | `/web-evidence/status` | `get_web_evidence_status` | `none` | no | future | yes |

### `world-state`

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/world-state/validate` | `post_world_state_validate` | `validation_only` | yes | future | yes |
