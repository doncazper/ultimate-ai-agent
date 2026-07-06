from dataclasses import dataclass
from threading import RLock
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.contracts import (
    ApiManifest,
    ApiRouteApprovalPosture,
    ApiRouteAuthPosture,
    ApiRouteClassification,
    ApiRouteIdempotencyPosture,
    ApiRouteInventoryItem,
    ApiRouteRateLimitPosture,
    ApiRouteSideEffectClass,
    ApiWebAccessPosture,
)
from ultimate_ai_agent.api.idempotency import (
    API_IDEMPOTENCY_AUDIT_POLICY_REF,
    route_idempotency_posture,
)
from ultimate_ai_agent.api.rate_limits import (
    API_TARGETED_RATE_LIMIT_POLICY_REF,
    route_rate_limit_posture,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_IDEMPOTENCY_POSTURE_REF,
)


CAPABILITIES_DECLARED = [
    "api_contract_metadata",
    "openapi_schema_export",
    "centralized_fastapi_security_headers",
    "explicit_loopback_cors_allowlist",
    "local_protected_route_bearer_gate",
    "local_protected_route_fail_closed_by_default",
    "local_protected_route_dev_only_bypass_manifest_visible",
    "mutating_route_idempotency_audit",
    "targeted_local_rate_limits",
    "typed_validation_routes",
    "foundation_gate_reporting",
    "local_dev_approval_validation",
    "manual_local_loopback_smoke_validation",
    "remote_worker_foundation_dry_run",
    "runtime_readiness_status",
    "manual_smoke_report_validation",
    "control_center_read_only_dashboard",
    "control_center_setup_assistant_summary",
    "control_center_setup_approval_envelopes_dry_run",
    "control_center_founder_loop_storage_summaries",
    "control_center_crm_local_command_center_read_model",
    "control_center_crm_relationship_timeline_read_model",
    "control_center_crm_follow_up_queue_read_model",
    "control_center_crm_smart_lists_read_model",
    "control_center_crm_pipeline_board_read_model",
    "control_center_crm_exact_local_mutation_receipts",
    "control_center_crm_redacted_local_import_export_preview",
    "control_center_crm_deterministic_proposal_layer",
    "control_center_run_observability_read_model",
    "governed_runtime_gateway_contracts",
    "governed_runtime_profiles_manifest",
    "governed_runtime_invocation_metadata_storage",
    "governed_runtime_safe_disable_state",
    "governed_runtime_api_contract_shells",
    "governed_runtime_loopback_local_model_call_pilot",
    "governed_runtime_allowlisted_readonly_command_pilot",
    "governed_runtime_action_inbox_focused_pytest_command_bridge",
    "governed_runtime_action_inbox_repo_verifier_command_bridge",
    "governed_runtime_action_inbox_frontend_check_command_bridge",
    "governed_runtime_action_inbox_repo_doctor_command_bridge",
    "governed_runtime_staged_orchestration_read_model",
    "governed_runtime_prepared_turn_read_model",
    "governed_product_pilot_authority_profile",
    "authority_decision_preview",
    "governed_product_pilot_portable_evidence_envelope",
    "governed_product_pilot_durable_orchestration_profile",
    "control_center_coding_cockpit_session_read_model",
    "control_center_coding_context_pack_preview_read_model",
    "control_center_coding_patch_apply_readiness_read_model",
    "control_center_coding_patch_proposal_read_model",
    "control_center_coding_test_command_readiness_read_model",
    "control_center_coding_git_review_read_model",
    "control_center_coding_live_preview_read_model",
    "control_center_coding_multi_agent_review_read_model",
    "control_center_today_summary",
    "control_center_agent_loop_thread_read_model",
    "control_center_action_inbox_summary",
    "control_center_today_to_action_envelope_promotion",
    "control_center_action_decision_state_machine",
    "control_center_action_local_task_commit",
    "control_center_chat_durable_receipts",
    "control_center_chat_reviewable_handoffs",
    "control_center_memory_review_decision_receipts",
    "control_center_memory_workbench_read_model",
    "control_center_memory_ranked_retrieval_read_model",
    "control_center_memory_safe_query_hashed_read_model",
    "control_center_memory_search_filters",
    "control_center_memory_impact_graph_read_model",
    "control_center_memory_follow_up_queue_proposals",
    "control_center_memory_recall_health_v2",
    "control_center_memory_retrieval_diagnostics",
    "control_center_memory_citation_integrity",
    "control_center_memory_feedback_quality_queue",
    "control_center_memory_feedback_receipts",
    "control_center_memory_proposal_only_maintenance_runs",
    "control_center_memory_context_manifest",
    "control_center_manual_memory_candidate_intake",
    "control_center_memory_l1_hot_local_index",
    "control_center_memory_l2_factual_graph_temporal_index",
    "control_center_memory_l3_identity_session_preference_modeling",
    "control_center_memory_context_pack_proposals",
    "control_center_memory_context_pack_previews",
    "control_center_memory_context_pack_internal_action_proposal",
    "control_center_memory_feedback_receipts",
    "control_center_memory_observation_candidates",
    "control_center_memory_probe_index",
    "control_center_memory_contradiction_previews",
    "control_center_memory_hrr_readiness_blocked_contract",
    "control_center_evidence_timeline_productization",
    "control_center_morning_briefing_summary",
    "control_center_provider_setup_guide_read_only",
    "control_center_provider_credential_readiness_cost_binding_read_only",
    "control_center_provider_credential_readiness_cli_inspection",
    "provider_credential_vault_contract_shell_metadata_only",
    "provider_credential_vault_contract_cli_inspection",
    "provider_credential_vault_local_secret_ref_backend_v1",
    "provider_credential_vault_backend_cli_inspection",
    "control_center_tiny_exact_approved_provider_lane_disabled_default",
    "control_center_tiny_exact_approved_provider_lane_cost_governed",
    "control_center_tiny_exact_approved_provider_lane_redacted_receipts",
    "control_center_tiny_exact_approved_provider_lane_receipt_completeness",
    "control_center_tiny_exact_approved_second_single_provider_adapter_scope_metadata_only",
    "provider_exact_approved_two_provider_fallback_core_cli_metadata",
    "provider_exact_approved_two_provider_fallback_cli_inspection",
    "provider_exact_approved_two_provider_fallback_per_attempt_receipts",
    "control_center_provider_credential_validation_exact_approved_lane",
    "control_center_provider_credential_validation_redacted_receipts",
    "control_center_provider_credential_validation_cli_inspection",
    "control_center_provider_router_dry_run_proposal_only",
    "control_center_provider_router_dry_run_cli_inspection",
    "control_center_model_provider_control_plane_read_model",
    "control_center_model_provider_control_plane_cli_inspection",
    "control_center_role_based_model_provider_evidence_read_model",
    "control_center_role_based_model_provider_evidence_cli_inspection",
    "control_center_turn_router_preview_no_effect",
    "control_center_turn_router_preview_cli_inspection",
    "control_center_source_readiness_status",
    "control_center_storage_status",
    "openwebui_local_test_gateway_disabled_by_default",
    "local_model_gateway_disabled_by_default",
    "local_loopback_runtime_disabled_by_default",
    "local_loopback_gateway_explicit_bearer_required",
    "local_loopback_gateway_allowlisted_response_shape",
    "task_decomposition_canonical_local_runtime",
    "task_decomposition_local_api_disabled_by_default",
    "task_decomposition_api_redacted_request_refs",
    "task_decomposition_capability_registry",
    "task_decomposition_local_approval_capture",
    "file_api_server_owned_safe_root_refs",
    "file_api_safe_tree_preview_refs",
    "secret_api_reference_only_handles",
    "inspectable_extension_catalog_read_only",
    "extension_activation_grant_records_exact_scope",
    "redacted_session_logging_local",
    "observability_safe_summary_api",
    "governed_web_evidence_status",
    "governed_web_evidence_allowlisted_https_get",
    "governed_web_evidence_chatbot_disclosure",
    "control_center_web_evidence_product_slice",
    "control_center_web_evidence_gateway_preview_receipts",
    "control_center_web_evidence_cli_inspection",
    "web_access_provider_adapter_shells_disabled",
    "web_access_provider_diagnostics_metadata_only",
    "web_access_provider_catalog_visibility_metadata_only",
    "mattermost_agent_rooms_disabled_by_default",
    "mattermost_role_catalog",
    "mattermost_redacted_message_ingress",
    "mattermost_role_bound_speak_only_replies",
    "mattermost_approval_required_tool_actions",
]

CAPABILITIES_BLOCKED = [
    "runtime_remote_or_unrestricted_model_calls",
    "provider_api_calls",
    "web_fetching",
    "browser_automation",
    "control_center_web_evidence_unrestricted_browsing",
    "control_center_web_evidence_browser_actions",
    "control_center_web_evidence_auth_session_state",
    "control_center_web_evidence_download_upload",
    "control_center_web_evidence_post_mutation",
    "control_center_web_evidence_raw_body_persistence",
    "control_center_web_evidence_context_injection",
    "control_center_web_evidence_memory_write",
    "control_center_web_evidence_provider_model_call",
    "control_center_web_evidence_connector_write",
    "production_persistence",
    "runtime_agent_config_loading",
    "runtime_unrestricted_execution_routes",
    "governed_runtime_unrestricted_adapter_execution",
    "governed_runtime_remote_or_provider_model_calls",
    "governed_runtime_unrestricted_command_execution",
    "governed_runtime_command_execution_without_gateway_allowlist",
    "governed_runtime_networked_command_execution",
    "governed_runtime_approval_as_execution_authority",
    "governed_runtime_raw_prompt_response_persistence",
    "governed_runtime_raw_command_output_persistence",
    "governed_runtime_raw_local_path_or_env_persistence",
    "governed_product_pilot_broad_autonomy",
    "governed_product_pilot_unrestricted_shell_subprocess",
    "governed_product_pilot_browser_automation",
    "governed_product_pilot_connector_writes",
    "governed_product_pilot_remote_execution",
    "governed_product_pilot_plugin_runtime_import",
    "governed_product_pilot_production_authority",
    "governed_product_pilot_public_beta_or_release_claim",
    "governed_product_pilot_raw_persistence",
    "security_headers_as_authentication",
    "security_headers_as_cors_policy",
    "security_headers_as_rate_limits",
    "cors_as_authentication",
    "cors_credentials",
    "cors_wildcard_origins",
    "local_protected_route_gate_as_enterprise_auth",
    "local_protected_route_gate_as_multi_user_auth",
    "local_protected_route_gate_as_oauth",
    "local_protected_route_gate_as_password_flow",
    "local_protected_route_gate_as_production_authority",
    "local_protected_route_dev_only_bypass_as_production_authority",
    "idempotency_audit_as_exactly_once_execution",
    "idempotency_audit_as_durable_dedupe_store",
    "idempotency_audit_as_mutation_authority",
    "idempotency_audit_as_production_authority",
    "targeted_rate_limits_as_auth",
    "targeted_rate_limits_as_distributed_quota",
    "targeted_rate_limits_as_production_authority",
    "plugin_enablement_routes",
    "control_center_execution",
    "control_center_run_observability_as_runtime_authority",
    "control_center_run_observability_cancel_resume_execution",
    "control_center_run_observability_live_streaming_runtime",
    "control_center_run_observability_connector_delivery_execution",
    "control_center_run_observability_background_worker_execution",
    "control_center_crm_connector_runtime",
    "control_center_crm_connector_writes",
    "control_center_crm_account_sync",
    "control_center_crm_sends",
    "control_center_crm_calendar_writes",
    "control_center_crm_external_crm_writes",
    "control_center_crm_provider_model_calls",
    "control_center_crm_live_web_fetching",
    "control_center_crm_browser_automation",
    "control_center_crm_hidden_context_injection",
    "control_center_crm_background_autonomy",
    "control_center_crm_production_authority",
    "control_center_crm_public_distribution_claim",
    "control_center_crm_raw_contact_detail_persistence",
    "control_center_crm_raw_message_body_persistence",
    "control_center_coding_cockpit_file_writes",
    "control_center_coding_cockpit_shell_subprocess_execution",
    "control_center_coding_cockpit_git_mutation",
    "control_center_coding_cockpit_provider_model_calls",
    "control_center_coding_cockpit_browser_automation",
    "control_center_coding_cockpit_connector_writes",
    "control_center_coding_cockpit_background_autonomy",
    "control_center_coding_cockpit_production_authority",
    "control_center_today_to_action_envelope_as_execution",
    "control_center_today_to_action_envelope_without_receipt",
    "control_center_action_decisions_as_action_execution",
    "control_center_action_decisions_without_exact_idempotency",
    "control_center_action_decisions_without_receipts",
    "control_center_action_local_task_commit_as_broad_execution",
    "control_center_action_local_task_commit_external_side_effects",
    "control_center_action_local_task_commit_without_exact_approval",
    "control_center_chat_receipts_as_model_authority",
    "control_center_chat_handoffs_as_execution",
    "control_center_chat_handoffs_without_exact_idempotency",
    "control_center_chat_handoffs_without_receipts",
    "control_center_chat_memory_writes",
    "control_center_chat_plan_execution",
    "control_center_chat_action_execution",
    "control_center_memory_review_context_injection",
    "control_center_memory_review_connector_writes",
    "control_center_memory_review_crm_sync",
    "control_center_memory_review_action_execution",
    "control_center_memory_review_truth_authority",
    "control_center_manual_memory_candidate_as_recall_record",
    "control_center_manual_memory_candidate_delete_or_export_execution",
    "control_center_memory_workbench_ui_only_truth",
    "control_center_memory_ranked_retrieval_embeddings",
    "control_center_memory_ranked_retrieval_vector_db",
    "control_center_memory_ranked_retrieval_provider_calls",
    "control_center_memory_ranked_retrieval_context_injection",
    "control_center_memory_ranked_retrieval_memory_writes",
    "control_center_memory_ranked_retrieval_auto_maintenance",
    "control_center_memory_ranked_retrieval_action_execution",
    "control_center_memory_ranked_retrieval_connector_writes",
    "control_center_memory_ranked_retrieval_background_indexing",
    "control_center_memory_ranked_retrieval_truth_authority",
    "control_center_memory_ranked_retrieval_hrr",
    "control_center_memory_ranked_retrieval_algebraic_retrieval",
    "control_center_memory_safe_query_raw_echo",
    "control_center_memory_ranked_retrieval_production_authority",
    "control_center_memory_search_embeddings",
    "control_center_memory_search_vector_db",
    "control_center_memory_search_semantic_search",
    "control_center_memory_search_context_injection",
    "control_center_memory_impact_graph_truth_authority",
    "control_center_memory_impact_graph_context_injection",
    "control_center_memory_impact_graph_action_execution",
    "control_center_memory_impact_graph_connector_writes",
    "control_center_memory_impact_graph_crm_sync",
    "control_center_memory_impact_graph_embeddings",
    "control_center_memory_impact_graph_vector_db",
    "control_center_memory_impact_graph_semantic_search",
    "control_center_memory_follow_up_queue_action_execution",
    "control_center_memory_follow_up_queue_scheduling",
    "control_center_memory_follow_up_queue_connector_writes",
    "control_center_memory_follow_up_queue_crm_sync",
    "control_center_memory_follow_up_queue_memory_writes",
    "control_center_memory_recall_health_as_truth_authority",
    "control_center_memory_recall_health_provider_model_calls",
    "control_center_memory_retrieval_diagnostics_context_injection",
    "control_center_memory_retrieval_diagnostics_semantic_search",
    "control_center_memory_retrieval_diagnostics_provider_model_calls",
    "control_center_memory_retrieval_diagnostics_memory_writes",
    "control_center_memory_citation_integrity_context_injection",
    "control_center_memory_citation_integrity_truth_authority",
    "control_center_memory_citation_integrity_provider_model_calls",
    "control_center_memory_feedback_automatic_writes",
    "control_center_memory_feedback_delete_execution",
    "control_center_memory_feedback_action_execution",
    "control_center_memory_maintenance_auto_merge",
    "control_center_memory_maintenance_auto_supersede",
    "control_center_memory_maintenance_auto_forget",
    "control_center_memory_maintenance_auto_write",
    "control_center_memory_context_manifest_hidden_prompt_injection",
    "control_center_memory_context_manifest_automatic_context_use",
    "control_center_memory_context_manifest_as_execution_authority",
    "control_center_memory_l1_index_context_injection",
    "control_center_memory_l1_index_automatic_recall",
    "control_center_memory_l1_index_automatic_writes",
    "control_center_memory_l1_index_embeddings",
    "control_center_memory_l1_index_vector_db",
    "control_center_memory_l1_index_semantic_search",
    "control_center_memory_l1_index_background_indexing",
    "control_center_memory_l1_index_truth_authority",
    "control_center_memory_l1_index_connector_writes",
    "control_center_memory_l1_index_crm_sync",
    "control_center_memory_l1_index_action_execution",
    "control_center_memory_l2_index_truth_authority",
    "control_center_memory_l2_index_context_injection",
    "control_center_memory_l2_index_automatic_recall",
    "control_center_memory_l2_index_automatic_writes",
    "control_center_memory_l2_index_embeddings",
    "control_center_memory_l2_index_vector_db",
    "control_center_memory_l2_index_semantic_search",
    "control_center_memory_l2_index_llm_entity_extraction",
    "control_center_memory_l2_index_provider_model_calls",
    "control_center_memory_l2_index_background_indexing",
    "control_center_memory_l2_index_context_pack_injection",
    "control_center_memory_l2_index_connector_writes",
    "control_center_memory_l2_index_crm_sync",
    "control_center_memory_l2_index_account_sync",
    "control_center_memory_l2_index_action_execution",
    "control_center_memory_l3_index_truth_authority",
    "control_center_memory_l3_index_approval_authority",
    "control_center_memory_l3_index_action_execution",
    "control_center_memory_l3_index_connector_writes",
    "control_center_memory_l3_index_crm_sync",
    "control_center_memory_l3_index_account_sync",
    "control_center_memory_l3_index_hidden_context_injection",
    "control_center_memory_l3_index_automatic_writes",
    "control_center_memory_l3_index_provider_model_calls",
    "control_center_memory_l3_index_llm_extraction",
    "control_center_memory_l3_index_embeddings",
    "control_center_memory_l3_index_vector_db",
    "control_center_memory_l3_index_semantic_search",
    "control_center_memory_l3_index_background_indexing",
    "control_center_memory_l3_index_context_pack_injection",
    "control_center_memory_l3_index_phase6_execution_hooks",
    "control_center_memory_context_pack_hidden_injection",
    "control_center_memory_context_pack_prompt_stuffing",
    "control_center_memory_context_pack_automatic_injection",
    "control_center_memory_context_pack_preview_runtime_injection",
    "control_center_memory_context_pack_preview_provider_model_calls",
    "control_center_memory_context_pack_preview_connector_writes",
    "control_center_memory_context_pack_preview_action_execution",
    "control_center_memory_context_pack_preview_memory_write",
    "control_center_memory_context_pack_preview_raw_payload_persistence",
    "control_center_memory_context_pack_truth_authority",
    "control_center_memory_context_pack_approval_authority",
    "control_center_memory_context_pack_action_execution",
    "control_center_memory_context_pack_connector_writes",
    "control_center_memory_context_pack_crm_sync",
    "control_center_memory_context_pack_account_sync",
    "control_center_memory_context_pack_provider_model_calls",
    "control_center_memory_context_pack_embeddings",
    "control_center_memory_context_pack_vector_db",
    "control_center_memory_context_pack_semantic_search",
    "control_center_memory_context_pack_background_indexing",
    "control_center_memory_context_pack_phase6_execution_hooks",
    "control_center_memory_context_pack_internal_action_proposal_as_execution",
    "control_center_memory_context_pack_external_side_effects",
    "control_center_memory_feedback_recall_record_create",
    "control_center_memory_feedback_delete_or_export_execution",
    "control_center_memory_feedback_context_injection",
    "control_center_memory_feedback_action_execution",
    "control_center_memory_feedback_connector_writes",
    "control_center_memory_feedback_provider_model_calls",
    "control_center_memory_feedback_cloud_sync",
    "control_center_memory_observation_candidates_truth_authority",
    "control_center_memory_observation_candidates_automatic_opinion",
    "control_center_memory_observation_candidates_context_injection",
    "control_center_memory_probe_context_injection",
    "control_center_memory_probe_action_execution",
    "control_center_memory_contradictions_auto_merge",
    "control_center_memory_contradictions_auto_forget",
    "control_center_memory_contradictions_truth_authority",
    "control_center_memory_hrr_enabled_without_explicit_milestone",
    "control_center_memory_hrr_ranking_influence",
    "control_center_memory_hrr_raw_content_input",
    "control_center_memory_hrr_embeddings_provider",
    "control_center_memory_hrr_vector_db",
    "control_center_memory_hrr_context_injection",
    "control_center_plugin_enablement",
    "control_center_provider_setup_guide_as_credential_enrollment",
    "control_center_provider_setup_guide_as_billing_authority",
    "control_center_provider_setup_guide_runtime_pricing_fetch",
    "control_center_provider_setup_guide_provider_validation",
    "control_center_provider_setup_guide_provider_invocation",
    "control_center_provider_credential_readiness_secret_entry",
    "control_center_provider_credential_readiness_provider_validation",
    "control_center_provider_credential_readiness_provider_invocation",
    "control_center_provider_credential_readiness_as_runtime_authority",
    "control_center_provider_cost_binding_as_billing_authority",
    "control_center_provider_cost_binding_without_budget_decision",
    "control_center_provider_cost_binding_without_receipts",
    "control_center_provider_unknown_paid_cost_without_explicit_approval",
    "control_center_provider_router_dry_run_as_invocation_authority",
    "control_center_provider_router_dry_run_fallback_execution",
    "control_center_provider_router_dry_run_provider_sdk_calls",
    "control_center_provider_router_dry_run_credential_validation",
    "control_center_provider_router_dry_run_model_calls",
    "control_center_provider_router_dry_run_billing_authority",
    "control_center_provider_router_dry_run_background_execution",
    "control_center_model_provider_control_plane_as_runtime_authority",
    "control_center_model_provider_control_plane_provider_sdk_calls",
    "control_center_model_provider_control_plane_network_by_default",
    "control_center_model_provider_control_plane_raw_prompt_response_persistence",
    "control_center_model_provider_control_plane_background_autonomy",
    "control_center_model_provider_control_plane_production_authority",
    "control_center_role_based_model_provider_evidence_as_invocation_authority",
    "control_center_role_based_model_provider_evidence_provider_sdk_calls",
    "control_center_role_based_model_provider_evidence_remote_model_calls",
    "control_center_role_based_model_provider_evidence_fallback_execution",
    "control_center_role_based_model_provider_evidence_provider_output_authority",
    "provider_credential_vault_secret_collection",
    "provider_credential_vault_raw_secret_storage",
    "provider_credential_vault_secret_resolution_api",
    "provider_credential_vault_raw_secret_display",
    "provider_credential_vault_os_backend_access",
    "provider_credential_vault_validation_authority",
    "provider_credential_vault_invocation_authority",
    "provider_credential_vault_presence_as_authority",
    "tiny_provider_lane_without_exact_approval",
    "tiny_provider_lane_unknown_paid_cost",
    "tiny_provider_lane_without_provider_model_credential_refs",
    "tiny_provider_lane_without_cost_budget_receipt_refs",
    "tiny_provider_lane_incomplete_actual_paid_cost_without_review",
    "tiny_provider_lane_broad_provider_router",
    "tiny_provider_lane_unbounded_multi_provider_fallback",
    "tiny_provider_lane_router_dry_run_as_fallback_execution",
    "tiny_provider_lane_fallback_without_per_attempt_exact_approval",
    "tiny_provider_lane_fallback_without_per_attempt_receipts",
    "tiny_provider_lane_fallback_after_incomplete_cost_without_review",
    "tiny_provider_lane_raw_prompt_response_or_provider_exchange_persistence",
    "tiny_provider_lane_autonomous_model_calls",
    "tiny_provider_lane_background_execution",
    "tiny_provider_lane_billing_authority",
    "tiny_provider_lane_provider_sdk_or_network_call_by_default",
    "tiny_provider_lane_network_call_outside_scoped_adapter",
    "provider_credential_validation_without_exact_approval",
    "provider_credential_validation_without_idempotency",
    "provider_credential_validation_without_redacted_receipt",
    "provider_credential_validation_model_invocation",
    "provider_credential_validation_chat_completions",
    "provider_credential_validation_provider_payload_persistence",
    "provider_credential_validation_raw_credential_display",
    "provider_credential_validation_broad_provider_router",
    "provider_credential_validation_multi_provider_fallback",
    "provider_credential_validation_billing_authority",
    "provider_credential_validation_autonomous_background_calls",
    "control_center_frontend_native_build_control",
    "control_center_mobile_sensor_access",
    "control_center_remote_dispatch",
    "control_center_model_provider_invocation",
    "control_center_setup_installer_actions",
    "control_center_setup_model_downloads",
    "control_center_setup_launch_agent_changes",
    "control_center_setup_background_service_changes",
    "control_center_setup_credential_handling",
    "openwebui_runtime_authority",
    "openwebui_provider_calls",
    "openwebui_shell_tool_execution",
    "openwebui_memory_writes",
    "openwebui_context_injection",
    "local_loopback_default_bearer",
    "local_loopback_raw_provider_payload_passthrough",
    "file_api_caller_selected_roots",
    "file_api_raw_tree_paths",
    "file_api_raw_diff_return",
    "file_api_raw_content_write_payload",
    "secret_api_raw_secret_values",
    "task_decomposition_raw_request_echo",
    "task_decomposition_unrestricted_external_execution",
    "task_decomposition_unreviewed_handler_imports",
    "task_decomposition_unscoped_approval_authority",
    "extension_catalog_callable_runtime",
    "extension_catalog_runtime_import",
    "extension_catalog_plugin_execution",
    "extension_catalog_connector_writes",
    "extension_activation_runtime_import",
    "extension_activation_execution",
    "extension_activation_callable_catalog",
    "extension_activation_overbroad_grants",
    "session_logging_raw_capture",
    "session_logging_external_telemetry",
    "session_logging_os_wide_activity_monitoring",
    "session_logging_unbounded_read_all",
    "session_logging_forensic_raw_mode",
    "governed_web_evidence_unrestricted_browsing",
    "governed_web_evidence_browser_automation",
    "governed_web_evidence_raw_body_storage",
    "governed_web_evidence_raw_header_storage",
    "governed_web_evidence_downloads",
    "governed_web_evidence_redirect_following",
    "governed_web_evidence_hidden_network_access",
    "web_access_provider_shells_as_runtime_authority",
    "web_access_provider_sdk_imports",
    "web_access_provider_credentials",
    "search_provider_live_calls",
    "firecrawl_provider_calls",
    "firecrawl_scrape_jobs",
    "browserbase_provider_sessions",
    "mattermost_raw_transcript_storage",
    "mattermost_unapproved_connector_writes",
    "mattermost_credential_or_cookie_handling",
    "mattermost_model_output_authority",
    "mattermost_unbounded_background_autonomy",
    "mattermost_room_operations_without_user_request",
]

WEB_ACCESS_POSTURE = {
    "web_access_gateway_boundary": "implemented",
    "boundary_module": "ultimate_ai_agent.core.web_access",
    "governed_web_access": "boundary_only",
    "unrestricted_web_fetching": "not_available",
    "browser_execution": "not_available",
    "browser_observe_runtime": "not_available",
    "browser_action_dry_run_runtime": "not_available",
    "providers": "not_configured",
    "content_untrusted": True,
    "grants_runtime_browsing_authority": False,
    "allows_clicks_forms_auth_cookies_downloads_uploads": False,
    "allowed_methods": (),
    "mutation_methods": "not_available",
}

ROUTE_GROUPS_BY_PREFIX = {
    "/api/runtime": "governed-runtime",
    "/api": "api-boundary",
    "/health": "system",
    "/version": "system",
    "/contracts": "contracts",
    "/context-packs": "contracts",
    "/events": "ledger",
    "/runs": "ledger",
    "/receipts": "ledger",
    "/world-state": "world-state",
    "/context-budget": "context-budget",
    "/local-runtime": "runtime-boundary",
    "/adapter-manifest": "adapter-boundary",
    "/models": "model-router",
    "/model-runtime": "model-runtime",
    "/runtime": "runtime-readiness",
    "/control-center": "control-center",
    "/remote-workers": "remote-workers",
    "/costs": "cost-governor",
    "/gate": "foundation-gate",
    "/approvals": "approval-authority",
    "/consent": "consent",
    "/tools": "tool-broker",
    "/secrets": "secret-broker",
    "/providers": "provider-registry",
    "/memory": "memory",
    "/files": "files",
    "/truth": "truth",
    "/kernel": "kernel",
    "/task-decomposition": "task-decomposition",
    "/observability": "observability",
    "/v1": "openwebui-local-test",
    "/extensions": "extension-catalog",
    "/web-evidence": "governed-web-evidence",
    "/integrations/mattermost": "mattermost",
}

LOCAL_DEV_WORKSPACE_PREFIXES = (
    "/kernel",
    "/files",
    "/memory",
    "/task-decomposition",
    "/observability",
    "/v1",
    "/integrations/mattermost",
)
CONTROL_CENTER_LOCAL_STATE_PREFIXES = (
    "/control-center/chat",
    "/control-center/coding",
    "/control-center/start-here",
    "/control-center/today",
    "/control-center/agent-loop",
    "/control-center/actions",
    "/control-center/proof",
    "/control-center/trust-authority",
    "/control-center/memory",
    "/control-center/evidence",
    "/control-center/morning-briefing",
    "/control-center/sources",
    "/control-center/storage",
    "/control-center/work-board",
    "/control-center/crm",
)
VALIDATION_HINTS = (
    "/validate",
    "/preview",
    "/evaluate",
    "/route",
    "/freshness/check",
    "/dry-run",
)
PUBLIC_METADATA_PATHS = {"/api/manifest", "/health", "/version"}
CONTROL_CENTER_ACTION_DECISION_SUFFIXES = ("/approve", "/edit", "/reject", "/defer")
CONTROL_CENTER_MEMORY_DECISION_SUFFIXES = (
    "/accept",
    "/correct",
    "/reject",
    "/defer",
    "/merge",
    "/supersede",
    "/forget-request",
)
CONTROL_CENTER_TODAY_ACTION_ENVELOPE_PATHS = {
    "/control-center/today/action-envelope",
}
CONTROL_CENTER_ACTION_LOCAL_TASK_COMMIT_PATHS = {
    "/control-center/actions/{action_id}/local-task/commit",
}
CONTROL_CENTER_CRM_LOCAL_MUTATION_PATHS = {
    "/control-center/crm/local-mutations",
}
CONTROL_CENTER_MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_PATHS = {
    "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
}
CONTROL_CENTER_MEMORY_FEEDBACK_PATHS = {
    "/control-center/memory/feedback",
}
CONTROL_CENTER_PROVIDER_TINY_EXACT_APPROVED_LANE_PATHS = {
    "/control-center/providers/exact-approved-lanes/tiny",
}
CONTROL_CENTER_PROVIDER_CREDENTIAL_VALIDATION_PATHS = {
    "/control-center/providers/credentials/validate",
}
CONTROL_CENTER_PROVIDER_ROUTER_DRY_RUN_PATHS = {
    "/control-center/providers/router/dry-run",
}
CONTROL_CENTER_WORK_BOARD_REORDER_PATHS = {
    "/control-center/work-board/reorder",
}
CONTROL_CENTER_WORK_BOARD_CARD_CREATE_PATHS = {
    "/control-center/work-board/cards",
}
CONTROL_CENTER_WEB_EVIDENCE_PRODUCT_SLICE_PATHS = {
    "/control-center/web-evidence/attach",
}
GOVERNED_RUNTIME_READONLY_PATHS = {
    "/api/runtime/authority-decisions/preview",
    "/api/runtime/authority-state",
    "/api/runtime/capabilities",
    "/api/runtime/approval-bridge",
    "/api/runtime/capability-discovery",
    "/api/runtime/checkpoint-rollback",
    "/api/runtime/context-budget-pressure",
    "/api/runtime/context-references",
    "/api/runtime/delegation-adapter",
    "/api/runtime/governed-product-pilot-profile",
    "/api/runtime/hardline-command-blocklist",
    "/api/runtime/interface-mode",
    "/api/runtime/hermes/context-pack",
    "/api/runtime/prompt-stability-tiers",
    "/api/runtime/profiles",
    "/api/runtime/run-events",
    "/api/runtime/session-lineage",
    "/api/runtime/session-search",
    "/api/runtime/streaming-progress",
    "/api/runtime/tool-registry",
    "/api/runtime/usage-cost-analytics",
    "/api/runtime/virtual-provider-moa",
    "/api/runtime/staged-orchestration",
    "/api/runtime/prepared-turn",
    "/api/runtime/parity-loop",
    "/api/runtime/invocations",
    "/api/runtime/invocations/{id}",
    "/api/runtime/invocations/{id}/receipt",
}
GOVERNED_RUNTIME_MUTATING_PATHS = {
    "/api/runtime/authority-leases",
    "/api/runtime/authority-leases/revoke",
    "/api/runtime/command/run",
    "/api/runtime/hermes/chat",
    "/api/runtime/invocations",
    "/api/runtime/local-model/call",
    "/api/runtime/invocations/{id}/approve",
    "/api/runtime/invocations/{id}/execute",
    "/api/runtime/safe-disable",
}
CONTROL_CENTER_VALIDATION_ONLY_PATHS = {
    "/control-center/actions/preview",
    "/control-center/turn-router/preview",
}
LOCAL_READONLY_PATHS = {
    "/control-center/dashboard",
    "/control-center/foundation-gate/summary",
    "/control-center/local-models/status",
    "/control-center/manifest",
    "/control-center/providers/runtime-control-plane",
    "/control-center/providers/setup-guide",
    "/control-center/routes",
    "/control-center/runtime-readiness/summary",
    "/control-center/runs/observability",
    "/control-center/setup-assistant/summary",
    "/control-center/settings/status",
    "/control-center/sources/readiness",
    "/control-center/status",
    "/control-center/crm/follow-ups",
    "/control-center/crm/pipelines",
    "/control-center/crm/relationships",
    "/control-center/crm/smart-lists",
    "/control-center/crm/summary",
    "/control-center/crm/timeline",
    "/extensions/catalog",
    "/remote-workers/mesh/status",
    "/remote-workers/status",
    "/remote-workers/tailnet/status",
    "/runtime/capability-matrix",
    "/runtime/readiness",
    "/web-evidence/status",
}
NON_MUTATING_LOCAL_POSTURE_HINTS = (
    "/classify",
    "/client-errors",
    "/decompose",
    "/dry-run",
    "/evaluate",
    "/freshness/check",
    "/preview",
    "/propose",
    "/query",
    "/read/",
    "/refs/",
    "/route",
    "/simulate",
    "/smoke/",
    "/suggest",
    "/tree/",
    "/validate",
)
MUTATING_LOCAL_POSTURE_HINTS = (
    "/approval-requests",
    "/approvals/grants/capture",
    "/approvals/revoke",
    "/capabilities/register",
    "/events/message",
    "/examples/init",
    "/plans/execute",
    "/roles/bind",
    "/roles/unbind",
    "/tasks/run",
)
ROUTE_CLASSIFICATION_VOCABULARY = tuple(ApiRouteClassification)

API_MANIFEST_CACHEABLE_FIELDS = (
    "title",
    "api_version",
    "package_version",
    "active_baseline",
    "route_count",
    "route_groups",
    "routes",
    "route_classification_vocabulary",
    "route_classification_summary",
    "route_auth_posture_summary",
    "route_approval_posture_summary",
    "idempotency_audit_policy_ref",
    "route_idempotency_posture_summary",
    "rate_limit_policy_ref",
    "route_rate_limit_posture_summary",
    "capabilities_declared",
    "capabilities_blocked",
    "web_access_posture",
    "no_runtime_integrations",
)
API_MANIFEST_CACHE_EXCLUDED_FIELDS = (
    "foundation_gate_status",
    "local_auth_policy",
    "policy_decisions",
    "policy_outcomes",
    "approvals",
    "approval_decisions",
    "runtime_authority",
    "user_data",
    "secrets",
    "mutable_state",
)
API_MANIFEST_CACHE_INVALIDATION_RULES = (
    "app_title_change",
    "package_version_change",
    "active_baseline_change",
    "route_path_method_operation_tag_summary_change",
    "route_classification_logic_change",
    "route_auth_posture_logic_change",
    "route_approval_posture_logic_change",
    "route_idempotency_posture_logic_change",
    "route_rate_limit_posture_logic_change",
    "capabilities_declared_change",
    "capabilities_blocked_change",
    "web_access_posture_change",
    "manual_cache_clear",
)


@dataclass(frozen=True)
class _ApiManifestStaticCacheEntry:
    fingerprint: tuple[Any, ...]
    title: str
    api_version: str
    package_version: str
    active_baseline: str
    route_count: int
    route_groups: tuple[str, ...]
    routes: tuple[ApiRouteInventoryItem, ...]
    capabilities_declared: tuple[str, ...]
    capabilities_blocked: tuple[str, ...]
    web_access_posture: ApiWebAccessPosture
    no_runtime_integrations: bool


_API_MANIFEST_STATIC_CACHE: dict[int, _ApiManifestStaticCacheEntry] = {}
_API_MANIFEST_STATIC_CACHE_LOCK = RLock()


def active_baseline_label() -> str:
    if __version__.endswith("a0"):
        return f"v{__version__[:-2]}-alpha"
    return f"v{__version__}"


def route_group_for_path(path: str) -> str:
    for prefix, group in ROUTE_GROUPS_BY_PREFIX.items():
        if path == prefix or path.startswith(prefix + "/"):
            return group
    return "api-boundary"


def stable_operation_id(method: str, path: str) -> str:
    stem = (
        path.strip("/")
        .replace("-", "_")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
    )
    return f"{method.lower()}_{stem or 'root'}"


def route_summary(method: str, path: str) -> str:
    action = " ".join(stable_operation_id(method, path).split("_"))
    return action.capitalize()


def route_side_effect_class(path: str) -> ApiRouteSideEffectClass:
    if path == "/api/manifest" or path in {
        "/health",
        "/version",
        "/web-evidence/status",
    }:
        return ApiRouteSideEffectClass.none
    if path in {
        "/api/runtime/authority-decisions/preview",
        "/api/runtime/capabilities",
    }:
        return ApiRouteSideEffectClass.validation_only
    if path.startswith("/api/runtime/"):
        return ApiRouteSideEffectClass.local_dev_workspace_only
    if path.startswith("/web-evidence/"):
        return ApiRouteSideEffectClass.governed_network_read_only
    if path in CONTROL_CENTER_VALIDATION_ONLY_PATHS:
        return ApiRouteSideEffectClass.validation_only
    if path in CONTROL_CENTER_PROVIDER_CREDENTIAL_VALIDATION_PATHS:
        return ApiRouteSideEffectClass.governed_network_read_only
    if path in CONTROL_CENTER_WEB_EVIDENCE_PRODUCT_SLICE_PATHS:
        return ApiRouteSideEffectClass.governed_network_read_only
    if path in CONTROL_CENTER_PROVIDER_ROUTER_DRY_RUN_PATHS:
        return ApiRouteSideEffectClass.validation_only
    if path in CONTROL_CENTER_PROVIDER_TINY_EXACT_APPROVED_LANE_PATHS:
        return ApiRouteSideEffectClass.local_dev_workspace_only
    if path.startswith(CONTROL_CENTER_LOCAL_STATE_PREFIXES):
        return ApiRouteSideEffectClass.local_dev_workspace_only
    if path.startswith(LOCAL_DEV_WORKSPACE_PREFIXES):
        return ApiRouteSideEffectClass.local_dev_workspace_only
    if any(hint in path for hint in VALIDATION_HINTS):
        return ApiRouteSideEffectClass.validation_only
    return ApiRouteSideEffectClass.validation_only


def route_classification_for_path(
    method: str,
    path: str,
    side_effect_class: ApiRouteSideEffectClass,
) -> tuple[ApiRouteClassification, str]:
    normalized_method = method.upper()
    unknown_route_group = (
        route_group_for_path(path) == "api-boundary" and path != "/api/manifest"
    )
    explicit_non_mutating_posture = (
        side_effect_class == ApiRouteSideEffectClass.governed_network_read_only
        or any(hint in path for hint in NON_MUTATING_LOCAL_POSTURE_HINTS)
        or path in LOCAL_READONLY_PATHS
        or path in CONTROL_CENTER_VALIDATION_ONLY_PATHS
    )
    if normalized_method == "GET" and path in PUBLIC_METADATA_PATHS:
        return (
            ApiRouteClassification.public_metadata,
            "harmless API metadata or status route with no local user state",
        )
    if normalized_method == "GET" and path == "/api/runtime/capabilities":
        return (
            ApiRouteClassification.local_readonly,
            "Governed runtime capability route exposes protected local RuntimeGateway profile and blocked-authority posture only.",
        )
    if normalized_method == "POST" and path == "/api/runtime/authority-decisions/preview":
        return (
            ApiRouteClassification.local_sensitive,
            "Authority decision preview evaluates active lease scope and returns redacted allow/ask/deny/degrade refs without mutation or execution.",
        )
    if normalized_method == "GET" and path in GOVERNED_RUNTIME_READONLY_PATHS:
        return (
            ApiRouteClassification.local_sensitive,
            "Governed runtime inspection route exposes local safe refs, policy decisions, receipts, authority profile, and blocked execution posture only.",
        )
    if normalized_method == "POST" and path == "/api/runtime/invocations":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Governed runtime invocation metadata route is mutation-like authority posture only; it stores safe refs and policy decisions, and idempotency, approval posture, redaction, and execution-blocked receipts are required before later runtime promotion.",
        )
    if normalized_method == "POST" and path == "/api/runtime/command/run":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Governed runtime command authority route permits only exact RuntimeGateway-derived argv for a Phase 04 read-only status intent; arbitrary command text, shell execution, networked commands, raw output persistence, and unvalidated approval refs remain blocked.",
        )
    if normalized_method == "POST" and path == "/api/runtime/hermes/chat":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Hermes interface-mode chat route permits only exact Hermes CLI chat argv with query hashing, redacted output receipts, idempotency, and visible mode posture; yolo, oneshot, arbitrary args, toolset passthrough, shell strings, raw persistence, direct memory writes, and production authority remain blocked.",
        )
    if normalized_method == "POST" and path == "/api/runtime/invocations/{id}/approve":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Governed runtime approval-binding route records exact Action Inbox runtime envelopes only when backend-derived approval, envelope, scope, payload, policy, adapter, rollback, and safe-disable refs match; arbitrary approval refs and broad runtime authority remain blocked.",
        )
    if normalized_method == "POST" and path == "/api/runtime/invocations/{id}/execute":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Governed runtime execute route can run only the exact Action Inbox approved focused pytest, repo-verifier, frontend-check, and repo-doctor RuntimeGateway command lanes with top-level approval/envelope/payload/policy refs, idempotency, redacted receipts, and safe-disable posture; arbitrary shell, generic Makefile commands outside exact lanes, browser, connector, provider, plugin, remote, and production authority remain blocked.",
        )
    if normalized_method == "POST" and path == "/api/runtime/safe-disable":
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Governed runtime safe-disable route is mutation-like authority posture only; it records local safe-disable posture, and idempotency, audit, and profile downgrade posture are required.",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_TODAY_ACTION_ENVELOPE_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Today-to-Action envelope authority route; exact idempotency, receipt, audit, and evidence posture required",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_ACTION_LOCAL_TASK_COMMIT_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Action Inbox local task commit authority route; exact approval, idempotency, receipt, evidence, and safe-disable posture required",
        )
    if normalized_method == "POST" and path in CONTROL_CENTER_CRM_LOCAL_MUTATION_PATHS:
        return (
            ApiRouteClassification.mutating_requires_authority,
            "CRM local mutation authority route; contacts/write AuthorityLease, exact local-only approval, idempotency, receipt, rollback-readiness, evidence refs, and blocked external connector/send/write posture required",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Memory context-pack internal Action proposal authority route; exact approval, idempotency, receipt, rollback, and evidence posture required while execution stays blocked",
        )
    if normalized_method == "POST" and path in CONTROL_CENTER_WORK_BOARD_REORDER_PATHS:
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Work Board reorder authority route; exact local approval, idempotency, safe card refs, receipt, rollback, and safe-disable posture required while issue tracker, connector, shell, browser, background, and production authority remain blocked",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_WORK_BOARD_CARD_CREATE_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Work Board local card-create authority route; exact local approval, idempotency, safe card refs, receipt, rollback-readiness, and safe-disable posture required while archive, assignment, issue tracker, connector, shell, browser, background, and production authority remain blocked",
        )
    if normalized_method == "POST" and path in CONTROL_CENTER_MEMORY_FEEDBACK_PATHS:
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Memory feedback receipt route; exact local authority, approval, idempotency, audit, and evidence posture required while deletes, exports, context injection, connector writes, and execution stay blocked",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_PROVIDER_TINY_EXACT_APPROVED_LANE_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Tiny exact-approved provider lane; exact approval, CostGovernor decision, idempotency, redacted receipt refs, actual usage/cost refs, receipt completeness, two named disabled-by-default single-provider live adapter scopes, and safe-disable posture required while incomplete actual paid cost blocks further use until review and broad provider authority and fallback execution stay blocked",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_PROVIDER_CREDENTIAL_VALIDATION_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Exact-approved provider credential validation lane; exact approval, policy, idempotency, redacted validation receipt, revocation, and safe-disable posture required while model invocation, provider SDKs, fallback, and billing authority stay blocked",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_WEB_EVIDENCE_PRODUCT_SLICE_PATHS
    ):
        return (
            ApiRouteClassification.local_sensitive,
            "Tier 1 WebAccessGateway preview route; allowlisted HTTPS GET only, bounded redacted preview returned, safe receipt refs stored locally, and browser/session/download/upload/mutation/context/memory/provider/connector authority remains blocked",
        )
    if (
        normalized_method == "POST"
        and path in CONTROL_CENTER_PROVIDER_ROUTER_DRY_RUN_PATHS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Provider router dry-run proposal lane; safe task/model refs, local provider readiness, CostGovernor posture, exact approval scope recommendations, idempotency, and redacted refs required while invocation, fallback execution, provider SDK calls, credential validation, model calls, billing authority, and background execution stay blocked",
        )
    if (
        normalized_method == "POST"
        and path.startswith("/control-center/actions/")
        and path.endswith(CONTROL_CENTER_ACTION_DECISION_SUFFIXES)
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Action Inbox decision route; exact authority, idempotency, audit, and receipt posture required",
        )
    if (
        normalized_method == "POST"
        and path.startswith("/control-center/memory/review/")
        and path.endswith(CONTROL_CENTER_MEMORY_DECISION_SUFFIXES)
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "Memory Review decision route; exact authority, idempotent backend receipt, and context-injection block posture required",
        )
    if path.endswith("/run") or any(
        hint in path for hint in MUTATING_LOCAL_POSTURE_HINTS
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "mutation-like local route; exact authority, idempotency, audit, and rollback posture required",
        )
    if (
        normalized_method not in {"GET", "HEAD", "OPTIONS"}
        and unknown_route_group
        and not explicit_non_mutating_posture
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "unknown non-read route without an explicit preview/validation posture; authority required by default",
        )
    if (
        side_effect_class == ApiRouteSideEffectClass.local_dev_workspace_only
        and normalized_method not in {"GET", "HEAD", "OPTIONS"}
        and not any(hint in path for hint in NON_MUTATING_LOCAL_POSTURE_HINTS)
    ):
        return (
            ApiRouteClassification.mutating_requires_authority,
            "local non-read route without a preview/validation posture; authority required before product use",
        )
    if normalized_method == "GET" and path in LOCAL_READONLY_PATHS:
        return (
            ApiRouteClassification.local_readonly,
            "local read-only route inventory or status surface; protected in production posture",
        )
    return (
        ApiRouteClassification.local_sensitive,
        "sensitive local state, request payload, evidence, memory, file, runtime, approval, or connector-adjacent route",
    )


def route_auth_posture(
    route_classification: ApiRouteClassification,
) -> ApiRouteAuthPosture:
    if route_classification == ApiRouteClassification.public_metadata:
        return ApiRouteAuthPosture.public_metadata_no_auth
    return ApiRouteAuthPosture.protected_local_bearer_required


def route_approval_posture(
    route_classification: ApiRouteClassification,
) -> ApiRouteApprovalPosture:
    if route_classification == ApiRouteClassification.mutating_requires_authority:
        return ApiRouteApprovalPosture.required_before_mutation_authority
    return ApiRouteApprovalPosture.not_required_for_route_classification


def iter_api_routes(routes: list[Any]) -> list[APIRoute]:
    api_routes: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            api_routes.append(route)
            continue
        original_router = getattr(route, "original_router", None)
        nested_routes = getattr(original_router, "routes", None)
        if nested_routes is not None:
            api_routes.extend(iter_api_routes(list(nested_routes)))
    return api_routes


def iter_api_route_items(app: FastAPI) -> list[ApiRouteInventoryItem]:
    items: list[ApiRouteInventoryItem] = []
    for route in iter_api_routes(app.routes):
        methods = sorted(
            method for method in route.methods if method not in {"HEAD", "OPTIONS"}
        )
        for method in methods:
            operation_id = route.operation_id or stable_operation_id(method, route.path)
            tags = list(route.tags or [route_group_for_path(route.path)])
            side_effect_class = route_side_effect_class(route.path)
            route_classification, classification_reason = route_classification_for_path(
                method,
                route.path,
                side_effect_class,
            )
            auth_posture = route_auth_posture(route_classification)
            approval_posture = route_approval_posture(route_classification)
            (
                idempotency_required,
                idempotency_posture,
                idempotency_policy_ref,
                idempotency_reason,
            ) = route_idempotency_posture(route_classification)
            if (
                method == "POST"
                and route.path in CONTROL_CENTER_WEB_EVIDENCE_PRODUCT_SLICE_PATHS
            ):
                idempotency_policy_ref = (
                    WEB_EVIDENCE_PRODUCT_SLICE_IDEMPOTENCY_POSTURE_REF
                )
                idempotency_reason = (
                    "Tier 1 Web Evidence stores a local receipt and is "
                    "request_ref payload-idempotent: the same request_ref "
                    "replays the stored receipt, while a changed fingerprint "
                    "returns a safe conflict. The route does not grant "
                    "mutation authority."
                )
            (
                rate_limit_targeted,
                rate_limit_posture,
                rate_limit_policy_ref,
                rate_limit_group,
                rate_limit_reason,
            ) = route_rate_limit_posture(method, route.path)
            items.append(
                ApiRouteInventoryItem(
                    path=route.path,
                    method=method,
                    operation_id=operation_id,
                    tags=tags,
                    summary=route.summary or route_summary(method, route.path),
                    validation_only=side_effect_class
                    == ApiRouteSideEffectClass.validation_only,
                    side_effect_class=side_effect_class,
                    route_classification=route_classification,
                    protected_route=route_classification
                    != ApiRouteClassification.public_metadata,
                    auth_posture=auth_posture,
                    approval_posture=approval_posture,
                    classification_reason=classification_reason,
                    idempotency_required=idempotency_required,
                    idempotency_posture=idempotency_posture,
                    idempotency_policy_ref=idempotency_policy_ref,
                    idempotency_reason=idempotency_reason,
                    rate_limit_targeted=rate_limit_targeted,
                    rate_limit_posture=rate_limit_posture,
                    rate_limit_policy_ref=rate_limit_policy_ref,
                    rate_limit_group=rate_limit_group,
                    rate_limit_reason=rate_limit_reason,
                )
            )
    return sorted(items, key=lambda item: (item.path, item.method))


def clear_api_manifest_static_cache(app: FastAPI | None = None) -> None:
    with _API_MANIFEST_STATIC_CACHE_LOCK:
        if app is None:
            _API_MANIFEST_STATIC_CACHE.clear()
        else:
            _API_MANIFEST_STATIC_CACHE.pop(id(app), None)


def api_manifest_cache_policy() -> dict[str, object]:
    return {
        "scope": "process_local_static_api_manifest_data_only",
        "cacheable_fields": list(API_MANIFEST_CACHEABLE_FIELDS),
        "excluded_fields": list(API_MANIFEST_CACHE_EXCLUDED_FIELDS),
        "invalidation_rules": list(API_MANIFEST_CACHE_INVALIDATION_RULES),
        "authority_decisions_cached": False,
        "policy_decisions_cached": False,
        "approval_decisions_cached": False,
        "mutable_user_data_cached": False,
        "secret_material_cached": False,
        "durable_cache": False,
    }


def _api_manifest_static_fingerprint(app: FastAPI) -> tuple[Any, ...]:
    route_fingerprints: list[tuple[object, ...]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = tuple(
            sorted(
                method for method in route.methods if method not in {"HEAD", "OPTIONS"}
            )
        )
        route_fingerprints.append(
            (
                route.path,
                methods,
                route.operation_id,
                tuple(route.tags or ()),
                route.summary,
            )
        )
    return (
        app.title,
        __version__,
        active_baseline_label(),
        tuple(CAPABILITIES_DECLARED),
        tuple(CAPABILITIES_BLOCKED),
        tuple(sorted(WEB_ACCESS_POSTURE.items())),
        tuple(sorted(route_fingerprints)),
    )


def _build_api_manifest_static_cache_entry(
    app: FastAPI,
    fingerprint: tuple[Any, ...],
) -> _ApiManifestStaticCacheEntry:
    routes = tuple(iter_api_route_items(app))
    route_groups = tuple(sorted({tag for route in routes for tag in route.tags}))
    return _ApiManifestStaticCacheEntry(
        fingerprint=fingerprint,
        title=app.title,
        api_version=__version__,
        package_version=__version__,
        active_baseline=active_baseline_label(),
        route_count=len(routes),
        route_groups=route_groups,
        routes=routes,
        capabilities_declared=tuple(CAPABILITIES_DECLARED),
        capabilities_blocked=tuple(CAPABILITIES_BLOCKED),
        web_access_posture=ApiWebAccessPosture(**WEB_ACCESS_POSTURE),
        no_runtime_integrations=True,
    )


def _get_api_manifest_static_cache_entry(app: FastAPI) -> _ApiManifestStaticCacheEntry:
    fingerprint = _api_manifest_static_fingerprint(app)
    cache_key = id(app)
    with _API_MANIFEST_STATIC_CACHE_LOCK:
        cached = _API_MANIFEST_STATIC_CACHE.get(cache_key)
        if cached is not None and cached.fingerprint == fingerprint:
            return cached
        refreshed = _build_api_manifest_static_cache_entry(app, fingerprint)
        _API_MANIFEST_STATIC_CACHE[cache_key] = refreshed
        return refreshed


def build_api_manifest(
    app: FastAPI, foundation_gate_status: str | None = None
) -> ApiManifest:
    from ultimate_ai_agent.api.local_auth import local_api_auth_policy_payload

    static = _get_api_manifest_static_cache_entry(app)
    classification_summary = {
        classification.value: 0 for classification in ROUTE_CLASSIFICATION_VOCABULARY
    }
    auth_posture_summary = {posture.value: 0 for posture in ApiRouteAuthPosture}
    approval_posture_summary = {posture.value: 0 for posture in ApiRouteApprovalPosture}
    idempotency_summary = {posture.value: 0 for posture in ApiRouteIdempotencyPosture}
    rate_limit_summary = {posture.value: 0 for posture in ApiRouteRateLimitPosture}
    for route in static.routes:
        classification_summary[str(route.route_classification)] += 1
        auth_posture_summary[str(route.auth_posture)] += 1
        approval_posture_summary[str(route.approval_posture)] += 1
        idempotency_summary[str(route.idempotency_posture)] += 1
        rate_limit_summary[str(route.rate_limit_posture)] += 1
    return ApiManifest(
        title=static.title,
        api_version=static.api_version,
        package_version=static.package_version,
        active_baseline=static.active_baseline,
        route_count=static.route_count,
        route_groups=list(static.route_groups),
        routes=[route.model_copy(deep=True) for route in static.routes],
        route_classification_vocabulary=[
            classification.value for classification in ROUTE_CLASSIFICATION_VOCABULARY
        ],
        route_classification_summary=classification_summary,
        route_auth_posture_summary=auth_posture_summary,
        route_approval_posture_summary=approval_posture_summary,
        idempotency_audit_policy_ref=API_IDEMPOTENCY_AUDIT_POLICY_REF,
        route_idempotency_posture_summary=idempotency_summary,
        rate_limit_policy_ref=API_TARGETED_RATE_LIMIT_POLICY_REF,
        route_rate_limit_posture_summary=rate_limit_summary,
        local_auth_policy=local_api_auth_policy_payload(),
        foundation_gate_status=foundation_gate_status,
        capabilities_declared=list(static.capabilities_declared),
        capabilities_blocked=list(static.capabilities_blocked),
        web_access_posture=static.web_access_posture.model_copy(deep=True),
        no_runtime_integrations=static.no_runtime_integrations,
    )
