# UAA-P1-021 FastAPI Route Grouping Map

Current active baseline: **v0.104.0**

Current OpenAPI path count: `286`.

This inventory is generated from the FastAPI application and `/api/manifest`. It is the route ownership and side-effect classification map for the current local-first API boundary.

## Current Route Boundary

- Manifest route operations: `287`
- OpenAPI paths: `286`
- Production runtime authority: blocked
- Public release authority: blocked

## Route Group Summary

| Route group | Count | Owner | Target service module | Auth posture | Side-effect class mix | Risk class | Operation id posture | Release status |
|---|---:|---|---|---|---|---|---|---|
| `adapter-boundary` | 1 | `core-runtime` | `contracts_service` | future auth required | `validation_only`:1 | low | stable/generated from path; unique | partial_backend_not_product_ready |
| `api-boundary` | 1 | `api-boundary` | `api_service` | future auth required | `none`:1 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `approval-authority` | 4 | `approval-authority` | `approval_service` | future auth required | `validation_only`:4 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `consent` | 2 | `consent` | `approval_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `context-budget` | 1 | `context` | `contracts_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `contracts` | 2 | `contracts` | `contracts_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `control-center` | 121 | `control-center` | `control_center_service` | local status or future auth per route | `authenticated_connector_mutation`:4, `destructive_external`:1, `destructive_local_sensitive`:1, `governed_network_read_only`:5, `local_dev_workspace_only`:81, `local_sensitive`:1, `none`:7, `system_browser_exact_launch`:1, `validation_only`:20 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `cost-governor` | 3 | `cost-governor` | `cost_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `extension-catalog` | 3 | `extension-catalog` | `extension_catalog_service` | future auth required | `local_dev_workspace_only`:2, `validation_only`:1 | medium | stable/generated from path; unique | status_available_not_completion |
| `files` | 6 | `workspace-files` | `workspace_files_service` | future auth required and local safe refs | `local_dev_workspace_only`:6 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `foundation-gate` | 2 | `foundation-gate` | `verification_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | status_available_not_completion |
| `governed-runtime` | 63 | `governed-runtime` | `runtime_pilot_service` | future auth required and exact approval before broader execution | `local_dev_workspace_only`:60, `validation_only`:3 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `kernel` | 1 | `kernel` | `kernel_service` | future auth required | `local_dev_workspace_only`:1 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `ledger` | 3 | `ledger` | `evidence_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `mattermost` | 8 | `mattermost` | `integrations_service` | disabled by default and future auth required | `local_dev_workspace_only`:8 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `memory` | 3 | `memory` | `memory_service` | future auth required and local safe refs | `local_dev_workspace_only`:3 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `model-router` | 2 | `model-router` | `model_runtime_service` | future auth required | `validation_only`:2 | medium | stable/generated from path; unique | preview_available_not_execution |
| `model-runtime` | 8 | `model-runtime` | `model_runtime_service` | future auth required | `validation_only`:8 | medium | stable/generated from path; unique | preview_available_not_execution |
| `observability` | 2 | `observability` | `observability_service` | future auth required and local redacted summaries | `local_dev_workspace_only`:2 | medium | stable/generated from path; unique | status_available_not_completion |
| `openwebui-local-test` | 2 | `local-model-runtime` | `model_runtime_service` | loopback bearer required when enabled | `local_dev_workspace_only`:2 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `provider-registry` | 3 | `provider-registry` | `provider_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | preview_available_not_execution |
| `remote-workers` | 8 | `remote-workers` | `remote_worker_service` | future auth required | `validation_only`:8 | high | stable/generated from path; unique | preview_available_not_execution |
| `runtime-boundary` | 1 | `runtime` | `runtime_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | status_available_not_completion |
| `runtime-readiness` | 3 | `runtime-readiness` | `runtime_service` | future auth required | `validation_only`:3 | medium | stable/generated from path; unique | status_available_not_completion |
| `secret-broker` | 2 | `secret-broker` | `secret_service` | future auth required | `validation_only`:2 | high | stable/generated from path; unique | preview_available_not_execution |
| `system` | 2 | `system` | `system_service` | future auth required | `none`:2 | medium | stable/generated from path; unique | status_available_not_completion |
| `task-decomposition` | 18 | `task-decomposition` | `task_decomposition_service` | disabled by default and explicit local auth | `local_dev_workspace_only`:18 | high | stable/generated from path; unique | partial_backend_not_product_ready |
| `tool-broker` | 3 | `tool-broker` | `tool_service` | future auth required | `validation_only`:3 | high | stable/generated from path; unique | preview_available_not_execution |
| `truth` | 6 | `truth` | `truth_service` | future auth required | `validation_only`:6 | medium | stable/generated from path; unique | preview_available_not_execution |
| `web-evidence` | 2 | `web-evidence` | `web_access_service` | future auth required and governed web evidence only | `governed_network_read_only`:1, `none`:1 | medium | stable/generated from path; unique | partial_backend_not_product_ready |
| `world-state` | 1 | `world-state` | `contracts_service` | future auth required | `validation_only`:1 | medium | stable/generated from path; unique | partial_backend_not_product_ready |

## All Current Routes

The three AuthorityLease mission failure-management POST routes are durable
operator-intent mutations, not execution endpoints. Approval decisions grant
no execution authority; cancellation only adds a pre-start fence; dead-letter
recovery records intent without replay. A later worker start must freshly
validate the exact request-scoped authority boundary.

| Method | Path | Operation ID | Side-effect class | Validation only | Auth posture | Blocked from production |
|---|---|---|---|---|---|---|
| POST | `/adapter-manifest/validate` | `post_adapter_manifest_validate` | `validation_only` | yes | future | yes |
| GET | `/api/manifest` | `get_api_manifest` | `none` | no | future | yes |
| GET | `/api/runtime/approval-bridge` | `get_api_runtime_approval_bridge` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-decisions/preview` | `post_api_runtime_authority_decisions_preview` | `validation_only` | yes | future | yes |
| GET | `/api/runtime/authority-domain-readiness` | `get_api_runtime_authority_domain_readiness` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-leases` | `post_api_runtime_authority_leases` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-leases/approve-and-issue` | `post_api_runtime_authority_leases_approve_and_issue` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-leases/revoke` | `post_api_runtime_authority_leases_revoke` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-missions/plan` | `post_api_runtime_authority_missions_plan` | `validation_only` | yes | future | yes |
| GET | `/api/runtime/authority-missions/completions` | `get_api_runtime_authority_missions_completions` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/authority-missions/worker-state` | `get_api_runtime_authority_missions_worker_state` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-missions/cancel` | `post_api_runtime_authority_mission_cancel` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-missions/approval-decisions` | `post_api_runtime_authority_mission_approval_decision` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/authority-missions/dead-letter-recovery` | `post_api_runtime_authority_mission_dead_letter_recovery` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/authority-state` | `get_api_runtime_authority_state` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/background-jobs` | `get_api_runtime_background_jobs` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/capabilities` | `get_api_runtime_capabilities` | `validation_only` | yes | future | yes |
| GET | `/api/runtime/capability-discovery` | `get_api_runtime_capability_discovery` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/checkpoint-rollback` | `get_api_runtime_checkpoint_rollback` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/command/run` | `post_api_runtime_command_run` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/context-budget-pressure` | `get_api_runtime_context_budget_pressure` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/context-references` | `get_api_runtime_context_references` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/delegation-adapter` | `get_api_runtime_delegation_adapter` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/doctor-diagnostics` | `get_api_runtime_doctor_diagnostics` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/governed-product-pilot-profile` | `get_api_runtime_governed_product_pilot_profile` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/hardline-command-blocklist` | `get_api_runtime_hardline_command_blocklist` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/hermes/chat` | `post_api_runtime_hermes_chat` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/hermes/context-pack` | `get_api_runtime_hermes_context_pack` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/interface-mode` | `get_api_runtime_interface_mode` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/interrupt-redirect` | `get_api_runtime_interrupt_redirect` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/invocations` | `get_api_runtime_invocations` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/invocations` | `post_api_runtime_invocations` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/invocations/{id}` | `get_api_runtime_invocations_id` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/invocations/{id}/approve` | `post_api_runtime_invocations_id_approve` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/invocations/{id}/execute` | `post_api_runtime_invocations_id_execute` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/invocations/{id}/receipt` | `get_api_runtime_invocations_id_receipt` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/local-model/call` | `post_api_runtime_local_model_call` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/logging-profile` | `get_api_runtime_logging_profile` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/lsp-diagnostics` | `get_api_runtime_lsp_diagnostics` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/managed-scope-policy` | `get_api_runtime_managed_scope_policy` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/mcp-catalog-filtering` | `get_api_runtime_mcp_catalog_filtering` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/messaging-gateway-posture` | `get_api_runtime_messaging_gateway_posture` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/parity-loop` | `get_api_runtime_parity_loop` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/plugin-metadata-posture` | `get_api_runtime_plugin_metadata_posture` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/prepared-turn` | `get_api_runtime_prepared_turn` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/preview-rail` | `get_api_runtime_preview_rail` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/profiles` | `get_api_runtime_profiles` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/prompt-stability-tiers` | `get_api_runtime_prompt_stability_tiers` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/remote-execution-posture` | `get_api_runtime_remote_execution_posture` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/result-classification` | `get_api_runtime_result_classification` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/run-events` | `get_api_runtime_run_events` | `local_dev_workspace_only` | no | future | yes |
| POST | `/api/runtime/safe-disable` | `post_api_runtime_safe_disable` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/session-continuity` | `get_api_runtime_session_continuity` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/session-lineage` | `get_api_runtime_session_lineage` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/session-search` | `get_api_runtime_session_search` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/skill-marketplace-posture` | `get_api_runtime_skill_marketplace_posture` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/slash-command-registry` | `get_api_runtime_slash_command_registry` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/staged-orchestration` | `get_api_runtime_staged_orchestration` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/streaming-progress` | `get_api_runtime_streaming_progress` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/subagent-isolation` | `get_api_runtime_subagent_isolation` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/tool-registry` | `get_api_runtime_tool_registry` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/usage-cost-analytics` | `get_api_runtime_usage_cost_analytics` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/virtual-provider-moa` | `get_api_runtime_virtual_provider_moa` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/voice-media-posture` | `get_api_runtime_voice_media_posture` | `local_dev_workspace_only` | no | future | yes |
| GET | `/api/runtime/worktree-per-agent` | `get_api_runtime_worktree_per_agent` | `local_dev_workspace_only` | no | future | yes |
| POST | `/approvals/grants/validate` | `post_approvals_grants_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/receipts/validate` | `post_approvals_receipts_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/requests/validate` | `post_approvals_requests_validate` | `validation_only` | yes | future | yes |
| POST | `/approvals/validate` | `post_approvals_validate` | `validation_only` | yes | future | yes |
| POST | `/consent/evaluate` | `post_consent_evaluate` | `validation_only` | yes | future | yes |
| POST | `/consent/grants/validate` | `post_consent_grants_validate` | `validation_only` | yes | future | yes |
| POST | `/context-budget/validate` | `post_context_budget_validate` | `validation_only` | yes | future | yes |
| POST | `/context-packs/validate` | `post_context_packs_validate` | `validation_only` | yes | future | yes |
| POST | `/contracts/validate` | `post_contracts_validate` | `validation_only` | yes | future | yes |
| GET | `/control-center/actions/inbox` | `get_control_center_actions_inbox` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/preview` | `post_control_center_actions_preview` | `validation_only` | yes | future | yes |
| POST | `/control-center/actions/{action_id}/approve` | `post_control_center_actions_action_id_approve` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/defer` | `post_control_center_actions_action_id_defer` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/edit` | `post_control_center_actions_action_id_edit` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/local-task/commit` | `post_control_center_actions_action_id_local_task_commit` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/actions/{action_id}/receipt` | `get_control_center_actions_action_id_receipt` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/actions/{action_id}/reject` | `post_control_center_actions_action_id_reject` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/agent-loop/thread` | `get_control_center_agent_loop_thread` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/approvals/queue` | `get_control_center_approvals_queue` | `validation_only` | yes | future | yes |
| GET | `/control-center/approvals/summary` | `get_control_center_approvals_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/capabilities/surface` | `get_control_center_capabilities_surface` | `validation_only` | yes | future | yes |
| GET | `/control-center/capabilities/availability` | `get_control_center_capabilities_availability` | `validation_only` | yes | future | yes |
| POST | `/control-center/chat/turns` | `post_control_center_chat_turns` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/chat/turns/{turn_ref}/handoff` | `post_control_center_chat_turns_turn_ref_handoff` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/chat/turns/{turn_ref}/receipt` | `get_control_center_chat_turns_turn_ref_receipt` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/context` | `get_control_center_coding_context` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/git-review` | `get_control_center_coding_git_review` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/live-preview` | `get_control_center_coding_live_preview` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/multi-agent-review` | `get_control_center_coding_multi_agent_review` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/patch-apply-readiness` | `get_control_center_coding_patch_apply_readiness` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/patch-proposal` | `get_control_center_coding_patch_proposal` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/session` | `get_control_center_coding_session` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/coding/test-command-readiness` | `get_control_center_coding_test_command_readiness` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/communications/failed-sends` | `get_control_center_communications_failed_sends` | `none` | yes | future | yes |
| POST | `/control-center/communications/harness/fixture-seed` | `post_control_center_communications_harness_fixture_seed` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/communications/harness/inspect` | `post_control_center_communications_harness_inspect` | `validation_only` | yes | future | yes |
| POST | `/control-center/communications/harness/reset` | `post_control_center_communications_harness_reset` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/communications/harness/smoke` | `post_control_center_communications_harness_smoke` | `governed_network_read_only` | no | future | yes |
| POST | `/control-center/communications/harness/start` | `post_control_center_communications_harness_start` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/communications/harness/stop` | `post_control_center_communications_harness_stop` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/communications/matrix/auth-methods-read` | `post_control_center_communications_matrix_auth_methods_read` | `governed_network_read_only` | no | future | yes |
| POST | `/control-center/communications/matrix/credential-auth-create` | `post_control_center_communications_matrix_credential_auth_create` | `authenticated_connector_mutation` | no | future | yes |
| POST | `/control-center/communications/matrix/credential-delete` | `post_control_center_communications_matrix_credential_delete` | `destructive_local_sensitive` | no | future | yes |
| POST | `/control-center/communications/matrix/credential-store-rotate` | `post_control_center_communications_matrix_credential_store_rotate` | `local_sensitive` | no | future | yes |
| POST | `/control-center/communications/matrix/discovery-read` | `post_control_center_communications_matrix_discovery_read` | `governed_network_read_only` | no | future | yes |
| POST | `/control-center/communications/matrix/logout` | `post_control_center_communications_matrix_logout` | `authenticated_connector_mutation` | no | future | yes |
| POST | `/control-center/communications/matrix/refresh` | `post_control_center_communications_matrix_refresh` | `authenticated_connector_mutation` | no | future | yes |
| POST | `/control-center/communications/matrix/revoke-all` | `post_control_center_communications_matrix_revoke_all` | `destructive_external` | no | future | yes |
| POST | `/control-center/communications/matrix/sso-callback-consume` | `post_control_center_communications_matrix_sso_callback_consume` | `authenticated_connector_mutation` | no | future | yes |
| POST | `/control-center/communications/matrix/sso-launch` | `post_control_center_communications_matrix_sso_launch` | `system_browser_exact_launch` | no | future | yes |
| GET | `/control-center/communications/matrix-sync/posture` | `get_control_center_communications_matrix_sync_posture` | `none` | yes | future | yes |
| GET | `/control-center/communications/providers` | `get_control_center_communications_providers` | `none` | yes | future | yes |
| GET | `/control-center/communications/receipts/{receipt_ref}` | `get_control_center_communications_receipt` | `none` | yes | future | yes |
| GET | `/control-center/communications/rooms` | `get_control_center_communications_rooms` | `none` | yes | future | yes |
| GET | `/control-center/communications/security-posture` | `get_control_center_communications_security_posture` | `none` | yes | future | yes |
| GET | `/control-center/communications/session-posture` | `get_control_center_communications_session_posture` | `none` | yes | future | yes |
| GET | `/control-center/crm/follow-ups` | `get_control_center_crm_follow_ups` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/crm/local-mutations` | `post_control_center_crm_local_mutations` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/crm/pipelines` | `get_control_center_crm_pipelines` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/crm/relationships` | `get_control_center_crm_relationships` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/crm/smart-lists` | `get_control_center_crm_smart_lists` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/crm/summary` | `get_control_center_crm_summary` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/crm/timeline` | `get_control_center_crm_timeline` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/dashboard` | `get_control_center_dashboard` | `validation_only` | yes | future | yes |
| GET | `/control-center/evidence/timeline` | `get_control_center_evidence_timeline` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/foundation-gate/summary` | `get_control_center_foundation_gate_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/local-models/status` | `get_control_center_local_models_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/manifest` | `get_control_center_manifest` | `validation_only` | yes | future | yes |
| GET | `/control-center/memory/citation-integrity` | `get_control_center_memory_citation_integrity` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/context-manifest` | `get_control_center_memory_context_manifest` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/context-packs` | `get_control_center_memory_context_packs` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/context-packs/{context_pack_ref}/action-proposal` | `post_control_center_memory_context_packs_context_pack_ref_action_proposal` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/context-packs/{context_pack_ref}/preview` | `get_control_center_memory_context_packs_context_pack_ref_preview` | `local_dev_workspace_only` | no | future | yes |
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
| POST | `/control-center/memory/review/{candidate_ref}/expire` | `post_control_center_memory_review_candidate_ref_expire` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/forget-request` | `post_control_center_memory_review_candidate_ref_forget_request` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/merge` | `post_control_center_memory_review_candidate_ref_merge` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/review/{candidate_ref}/receipt` | `get_control_center_memory_review_candidate_ref_receipt` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/reject` | `post_control_center_memory_review_candidate_ref_reject` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/memory/review/{candidate_ref}/supersede` | `post_control_center_memory_review_candidate_ref_supersede` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/search` | `get_control_center_memory_search` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/memory/workbench` | `get_control_center_memory_workbench` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/morning-briefing/summary` | `get_control_center_morning_briefing_summary` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/proof/index` | `get_control_center_proof_index` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/proof/{proof_ref}` | `get_control_center_proof_proof_ref` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/providers/credentials/validate` | `post_control_center_providers_credentials_validate` | `governed_network_read_only` | no | future | yes |
| POST | `/control-center/providers/exact-approved-lanes/tiny` | `post_control_center_providers_exact_approved_lanes_tiny` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/providers/router/dry-run` | `post_control_center_providers_router_dry_run` | `validation_only` | yes | future | yes |
| GET | `/control-center/providers/runtime-control-plane` | `get_control_center_providers_runtime_control_plane` | `validation_only` | yes | future | yes |
| GET | `/control-center/providers/setup-guide` | `get_control_center_providers_setup_guide` | `validation_only` | yes | future | yes |
| GET | `/control-center/routes` | `get_control_center_routes` | `validation_only` | yes | future | yes |
| GET | `/control-center/runs/observability` | `get_control_center_runs_observability` | `validation_only` | yes | future | yes |
| GET | `/control-center/runtime-readiness/summary` | `get_control_center_runtime_readiness_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/settings/status` | `get_control_center_settings_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/setup-assistant/summary` | `get_control_center_setup_assistant_summary` | `validation_only` | yes | future | yes |
| GET | `/control-center/sources/readiness` | `get_control_center_sources_readiness` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/start-here/summary` | `get_control_center_start_here_summary` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/status` | `get_control_center_status` | `validation_only` | yes | future | yes |
| GET | `/control-center/storage/status` | `get_control_center_storage_status` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/action-envelope` | `post_control_center_today_action_envelope` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/exact-action/approve` | `post_control_center_today_exact_action_approve` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/exact-action/execute` | `post_control_center_today_exact_action_execute` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/exact-action/source-review` | `post_control_center_today_exact_action_source_review` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/today/exact-action/prepare` | `post_control_center_today_exact_action_prepare` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/today/exact-action/{today_item_ref}/status` | `get_control_center_today_exact_action_today_item_ref_status` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/today/summary` | `get_control_center_today_summary` | `local_dev_workspace_only` | no | future | yes |
| GET | `/control-center/trust-authority/matrix` | `get_control_center_trust_authority_matrix` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/turn-router/preview` | `post_control_center_turn_router_preview` | `validation_only` | yes | future | yes |
| POST | `/control-center/web-evidence/attach` | `post_control_center_web_evidence_attach` | `governed_network_read_only` | no | future | yes |
| GET | `/control-center/work-board` | `get_control_center_work_board` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/work-board/cards` | `post_control_center_work_board_cards` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/work-board/reorder` | `post_control_center_work_board_reorder` | `local_dev_workspace_only` | no | future | yes |
| POST | `/control-center/work-board/tasks` | `post_control_center_work_board_tasks` | `local_dev_workspace_only` | no | future | yes |
| POST | `/costs/budgets/validate` | `post_costs_budgets_validate` | `validation_only` | yes | future | yes |
| POST | `/costs/estimate/preview` | `post_costs_estimate_preview` | `validation_only` | yes | future | yes |
| POST | `/costs/evaluate` | `post_costs_evaluate` | `validation_only` | yes | future | yes |
| POST | `/events/validate` | `post_events_validate` | `validation_only` | yes | future | yes |
| GET | `/extensions/catalog` | `get_extensions_catalog` | `validation_only` | yes | future | yes |
| POST | `/extensions/disabled-install-records` | `post_extensions_disabled_install_records` | `local_dev_workspace_only` | no | future | yes |
| POST | `/extensions/disabled-install-records/rollback` | `post_extensions_disabled_install_records_rollback` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/diff/preview` | `post_files_diff_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/read/preview` | `post_files_read_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/refs/validate` | `post_files_refs_validate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/review/approvals/capture` | `post_files_review_approvals_capture` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/tree/preview` | `post_files_tree_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/files/write/propose` | `post_files_write_propose` | `local_dev_workspace_only` | no | future | yes |
| POST | `/gate/reports/validate` | `post_gate_reports_validate` | `validation_only` | yes | future | yes |
| POST | `/gate/shadow-replay/validate` | `post_gate_shadow_replay_validate` | `validation_only` | yes | future | yes |
| GET | `/health` | `get_health` | `none` | no | future | yes |
| GET | `/integrations/mattermost/audit` | `get_integrations_mattermost_audit` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/events/message` | `post_integrations_mattermost_events_message` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/receipts` | `get_integrations_mattermost_receipts` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/bind` | `post_integrations_mattermost_roles_bind` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/roles/catalog` | `get_integrations_mattermost_roles_catalog` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/suggest` | `post_integrations_mattermost_roles_suggest` | `local_dev_workspace_only` | no | future | yes |
| POST | `/integrations/mattermost/roles/unbind` | `post_integrations_mattermost_roles_unbind` | `local_dev_workspace_only` | no | future | yes |
| GET | `/integrations/mattermost/status` | `get_integrations_mattermost_status` | `local_dev_workspace_only` | no | future | yes |
| POST | `/kernel/tasks/run` | `post_kernel_tasks_run` | `local_dev_workspace_only` | no | future | yes |
| POST | `/local-runtime/validate` | `post_local_runtime_validate` | `validation_only` | yes | future | yes |
| POST | `/memory/query/preview` | `post_memory_query_preview` | `local_dev_workspace_only` | no | future | yes |
| POST | `/memory/records/validate` | `post_memory_records_validate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/memory/write/evaluate` | `post_memory_write_evaluate` | `local_dev_workspace_only` | no | future | yes |
| POST | `/model-runtime/local/endpoints/validate` | `post_model_runtime_local_endpoints_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/execution/validate` | `post_model_runtime_local_execution_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/simulate-fallback` | `post_model_runtime_local_simulate_fallback` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/local/smoke/validate` | `post_model_runtime_local_smoke_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/manifests/validate` | `post_model_runtime_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/requests/validate` | `post_model_runtime_requests_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/responses/validate` | `post_model_runtime_responses_validate` | `validation_only` | yes | future | yes |
| POST | `/model-runtime/simulate` | `post_model_runtime_simulate` | `validation_only` | yes | future | yes |
| POST | `/models/profiles/validate` | `post_models_profiles_validate` | `validation_only` | yes | future | yes |
| POST | `/models/route/preview` | `post_models_route_preview` | `validation_only` | yes | future | yes |
| POST | `/observability/client-errors` | `post_observability_client_errors` | `local_dev_workspace_only` | no | future | yes |
| GET | `/observability/session-events` | `get_observability_session_events` | `local_dev_workspace_only` | no | future | yes |
| POST | `/providers/manifests/validate` | `post_providers_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/providers/resolve` | `post_providers_resolve` | `validation_only` | yes | future | yes |
| POST | `/providers/results/validate` | `post_providers_results_validate` | `validation_only` | yes | future | yes |
| POST | `/receipts/preview` | `post_receipts_preview` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/dry-run` | `post_remote_workers_dry_run` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/jobs/validate` | `post_remote_workers_jobs_validate` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/mesh/status` | `get_remote_workers_mesh_status` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/nodes/validate` | `post_remote_workers_nodes_validate` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/policy/validate` | `post_remote_workers_policy_validate` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/status` | `get_remote_workers_status` | `validation_only` | yes | future | yes |
| GET | `/remote-workers/tailnet/status` | `get_remote_workers_tailnet_status` | `validation_only` | yes | future | yes |
| POST | `/remote-workers/transports/validate` | `post_remote_workers_transports_validate` | `validation_only` | yes | future | yes |
| POST | `/runs/state/transition/validate` | `post_runs_state_transition_validate` | `validation_only` | yes | future | yes |
| GET | `/runtime/capability-matrix` | `get_runtime_capability_matrix` | `validation_only` | yes | future | yes |
| GET | `/runtime/readiness` | `get_runtime_readiness` | `validation_only` | yes | future | yes |
| POST | `/runtime/smoke-reports/validate` | `post_runtime_smoke_reports_validate` | `validation_only` | yes | future | yes |
| POST | `/secrets/access/evaluate` | `post_secrets_access_evaluate` | `validation_only` | yes | future | yes |
| POST | `/secrets/credentials/validate` | `post_secrets_credentials_validate` | `validation_only` | yes | future | yes |
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
| GET | `/task-decomposition/runs/{run_id}/approvals` | `get_task_decomposition_runs_run_id_approvals` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/runs/{run_id}/lifecycle` | `get_task_decomposition_runs_run_id_lifecycle` | `local_dev_workspace_only` | no | future | yes |
| GET | `/task-decomposition/status` | `get_task_decomposition_status` | `local_dev_workspace_only` | no | future | yes |
| POST | `/tools/manifests/validate` | `post_tools_manifests_validate` | `validation_only` | yes | future | yes |
| POST | `/tools/requests/dry-run` | `post_tools_requests_dry_run` | `validation_only` | yes | future | yes |
| POST | `/tools/requests/evaluate` | `post_tools_requests_evaluate` | `validation_only` | yes | future | yes |
| POST | `/truth/conflicts/validate` | `post_truth_conflicts_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/evidence/validate` | `post_truth_evidence_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/freshness/check` | `post_truth_freshness_check` | `validation_only` | yes | future | yes |
| POST | `/truth/grounding-policy/validate` | `post_truth_grounding_policy_validate` | `validation_only` | yes | future | yes |
| POST | `/truth/route` | `post_truth_route` | `validation_only` | yes | future | yes |
| POST | `/truth/sources/validate` | `post_truth_sources_validate` | `validation_only` | yes | future | yes |
| POST | `/v1/chat/completions` | `post_v1_chat_completions` | `local_dev_workspace_only` | no | future | yes |
| GET | `/v1/models` | `get_v1_models` | `local_dev_workspace_only` | no | future | yes |
| GET | `/version` | `get_version` | `none` | no | future | yes |
| POST | `/web-evidence/request` | `post_web_evidence_request` | `governed_network_read_only` | no | future | yes |
| GET | `/web-evidence/status` | `get_web_evidence_status` | `none` | no | future | yes |
| POST | `/world-state/validate` | `post_world_state_validate` | `validation_only` | yes | future | yes |
