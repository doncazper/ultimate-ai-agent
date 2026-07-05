from typing import Any
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import (
    API_MANIFEST_CACHE_EXCLUDED_FIELDS,
    API_MANIFEST_CACHE_INVALIDATION_RULES,
    API_MANIFEST_CACHEABLE_FIELDS,
    active_baseline_label,
    api_manifest_cache_policy,
    build_api_manifest,
    clear_api_manifest_static_cache,
    route_classification_for_path,
    route_group_for_path,
    route_side_effect_class,
)
from ultimate_ai_agent.api.openapi import (
    forbidden_raw_provider_schema_fields,
    forbidden_raw_secret_schema_fields,
)
from scripts.verification.api_routes import (
    EXPECTED_APPROVAL_POSTURE_SUMMARY,
    EXPECTED_AUTH_POSTURE_SUMMARY,
    EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY,
    EXPECTED_RATE_LIMIT_POSTURE_SUMMARY,
)


client = TestClient(app)


def test_api_manifest_endpoint_is_metadata_only_and_versioned() -> None:
    response = client.get("/api/manifest")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["api_version"] == __version__
    assert manifest["package_version"] == __version__
    assert manifest["active_baseline"] == active_baseline_label()
    assert manifest["no_runtime_integrations"] is True
    assert "governed_runtime_loopback_local_model_call_pilot" in manifest[
        "capabilities_declared"
    ]
    assert "runtime_remote_or_unrestricted_model_calls" in manifest[
        "capabilities_blocked"
    ]
    assert "governed_runtime_remote_or_provider_model_calls" in manifest[
        "capabilities_blocked"
    ]
    assert "web_fetching" in manifest["capabilities_blocked"]
    assert "api_contract_metadata" in manifest["capabilities_declared"]
    assert "centralized_fastapi_security_headers" in manifest["capabilities_declared"]
    assert "explicit_loopback_cors_allowlist" in manifest["capabilities_declared"]
    assert "local_protected_route_bearer_gate" in manifest["capabilities_declared"]
    assert (
        "local_protected_route_fail_closed_by_default"
        in manifest["capabilities_declared"]
    )
    assert (
        "local_protected_route_dev_only_bypass_manifest_visible"
        in manifest["capabilities_declared"]
    )
    assert "mutating_route_idempotency_audit" in manifest["capabilities_declared"]
    assert "targeted_local_rate_limits" in manifest["capabilities_declared"]
    assert "security_headers_as_authentication" in manifest["capabilities_blocked"]
    assert "security_headers_as_cors_policy" in manifest["capabilities_blocked"]
    assert "security_headers_as_rate_limits" in manifest["capabilities_blocked"]
    assert "cors_as_authentication" in manifest["capabilities_blocked"]
    assert "cors_credentials" in manifest["capabilities_blocked"]
    assert "cors_wildcard_origins" in manifest["capabilities_blocked"]
    assert (
        "local_protected_route_gate_as_enterprise_auth"
        in manifest["capabilities_blocked"]
    )
    assert (
        "local_protected_route_gate_as_multi_user_auth"
        in manifest["capabilities_blocked"]
    )
    assert "local_protected_route_gate_as_oauth" in manifest["capabilities_blocked"]
    assert (
        "local_protected_route_gate_as_password_flow"
        in manifest["capabilities_blocked"]
    )
    assert (
        "local_protected_route_gate_as_production_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "local_protected_route_dev_only_bypass_as_production_authority"
        in manifest["capabilities_blocked"]
    )
    assert manifest["local_auth_policy"]["fail_closed_by_default"] is True
    assert (
        manifest["local_auth_policy"]["dev_only_bypass_env"]
        == "UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY"
    )
    assert (
        manifest["local_auth_policy"]["dev_only_bypass_production_authority"] is False
    )
    assert (
        "idempotency_audit_as_exactly_once_execution"
        in manifest["capabilities_blocked"]
    )
    assert (
        "idempotency_audit_as_durable_dedupe_store" in manifest["capabilities_blocked"]
    )
    assert "idempotency_audit_as_mutation_authority" in manifest["capabilities_blocked"]
    assert (
        "idempotency_audit_as_production_authority" in manifest["capabilities_blocked"]
    )
    assert "targeted_rate_limits_as_auth" in manifest["capabilities_blocked"]
    assert (
        "targeted_rate_limits_as_distributed_quota" in manifest["capabilities_blocked"]
    )
    assert (
        "targeted_rate_limits_as_production_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "local_loopback_gateway_explicit_bearer_required"
        in manifest["capabilities_declared"]
    )
    assert (
        "local_loopback_gateway_allowlisted_response_shape"
        in manifest["capabilities_declared"]
    )
    assert "file_api_safe_tree_preview_refs" in manifest["capabilities_declared"]
    assert (
        "inspectable_extension_catalog_read_only" in manifest["capabilities_declared"]
    )
    assert (
        "extension_activation_grant_records_exact_scope"
        in manifest["capabilities_declared"]
    )
    assert "redacted_session_logging_local" in manifest["capabilities_declared"]
    assert "observability_safe_summary_api" in manifest["capabilities_declared"]
    assert "control_center_setup_assistant_summary" in manifest["capabilities_declared"]
    assert (
        "control_center_setup_approval_envelopes_dry_run"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_founder_loop_storage_summaries"
        in manifest["capabilities_declared"]
    )
    assert "control_center_today_summary" in manifest["capabilities_declared"]
    assert "control_center_action_inbox_summary" in manifest["capabilities_declared"]
    assert (
        "control_center_morning_briefing_summary" in manifest["capabilities_declared"]
    )
    assert "control_center_storage_status" in manifest["capabilities_declared"]
    assert (
        "control_center_coding_cockpit_session_read_model"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_memory_safe_query_hashed_read_model"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_memory_feedback_receipts" in manifest["capabilities_declared"]
    )
    assert (
        "control_center_memory_observation_candidates"
        in manifest["capabilities_declared"]
    )
    assert "control_center_memory_probe_index" in manifest["capabilities_declared"]
    assert (
        "control_center_memory_contradiction_previews"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_memory_hrr_readiness_blocked_contract"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_memory_hrr_enabled_without_explicit_milestone"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_memory_safe_query_raw_echo" in manifest["capabilities_blocked"]
    )
    for blocked_capability in [
        "control_center_coding_cockpit_file_writes",
        "control_center_coding_cockpit_shell_subprocess_execution",
        "control_center_coding_cockpit_git_mutation",
        "control_center_coding_cockpit_provider_model_calls",
        "control_center_coding_cockpit_browser_automation",
        "control_center_coding_cockpit_connector_writes",
        "control_center_coding_cockpit_background_autonomy",
        "control_center_coding_cockpit_production_authority",
    ]:
        assert blocked_capability in manifest["capabilities_blocked"]
    assert (
        "control_center_provider_credential_readiness_cost_binding_read_only"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_provider_credential_readiness_cli_inspection"
        in manifest["capabilities_declared"]
    )
    assert (
        "control_center_provider_credential_readiness_secret_entry"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_credential_readiness_provider_validation"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_credential_readiness_provider_invocation"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_credential_readiness_as_runtime_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_cost_binding_as_billing_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_cost_binding_without_budget_decision"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_cost_binding_without_receipts"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_provider_unknown_paid_cost_without_explicit_approval"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_contract_shell_metadata_only"
        in manifest["capabilities_declared"]
    )
    assert (
        "provider_credential_vault_contract_cli_inspection"
        in manifest["capabilities_declared"]
    )
    assert (
        "provider_credential_vault_local_secret_ref_backend_v1"
        in manifest["capabilities_declared"]
    )
    assert (
        "provider_credential_vault_backend_cli_inspection"
        in manifest["capabilities_declared"]
    )
    assert (
        "provider_credential_vault_secret_collection"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_raw_secret_storage"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_secret_resolution_api"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_raw_secret_display"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_os_backend_access"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_validation_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_invocation_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_vault_presence_as_authority"
        in manifest["capabilities_blocked"]
    )
    for capability in {
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
        "control_center_turn_router_preview_no_effect",
        "control_center_turn_router_preview_cli_inspection",
    }:
        assert capability in manifest["capabilities_declared"]
    for capability in {
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
    }:
        assert capability in manifest["capabilities_blocked"]
    assert (
        "provider_credential_validation_without_exact_approval"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_validation_model_invocation"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_validation_provider_payload_persistence"
        in manifest["capabilities_blocked"]
    )
    assert (
        "provider_credential_validation_billing_authority"
        in manifest["capabilities_blocked"]
    )
    assert (
        "web_access_provider_adapter_shells_disabled"
        in manifest["capabilities_declared"]
    )
    assert (
        "web_access_provider_diagnostics_metadata_only"
        in manifest["capabilities_declared"]
    )
    assert (
        "web_access_provider_catalog_visibility_metadata_only"
        in manifest["capabilities_declared"]
    )
    assert (
        "mattermost_agent_rooms_disabled_by_default"
        in manifest["capabilities_declared"]
    )
    assert "mattermost_role_catalog" in manifest["capabilities_declared"]
    assert "mattermost_redacted_message_ingress" in manifest["capabilities_declared"]
    assert (
        "mattermost_approval_required_tool_actions" in manifest["capabilities_declared"]
    )
    assert manifest["route_count"] >= 43
    assert any(
        route["path"] == "/api/manifest" and route["method"] == "GET"
        for route in manifest["routes"]
    )
    assert any(
        route["path"] == "/extensions/catalog" and route["method"] == "GET"
        for route in manifest["routes"]
    )
    assert any(
        route["path"] == "/observability/session-events" and route["method"] == "GET"
        for route in manifest["routes"]
    )


def test_api_manifest_web_access_posture_is_boundary_only() -> None:
    manifest = client.get("/api/manifest").json()
    posture = manifest["web_access_posture"]

    assert posture == {
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
        "allowed_methods": [],
        "mutation_methods": "not_available",
    }
    assert "web_fetching" in manifest["capabilities_blocked"]
    assert "browser_automation" in manifest["capabilities_blocked"]
    assert (
        "governed_web_evidence_unrestricted_browsing"
        in manifest["capabilities_blocked"]
    )
    assert (
        "governed_web_evidence_browser_automation" in manifest["capabilities_blocked"]
    )
    assert (
        "governed_web_evidence_allowlisted_https_get"
        in manifest["capabilities_declared"]
    )
    assert "web_fetching" not in manifest["capabilities_declared"]
    assert "unrestricted_web_fetching" not in manifest["capabilities_declared"]
    assert "browser_execution" not in manifest["capabilities_declared"]
    assert "browser_automation" not in manifest["capabilities_declared"]
    assert "firecrawl" not in manifest["capabilities_declared"]
    assert "browserbase" not in manifest["capabilities_declared"]


def test_unknown_non_read_routes_fail_into_authority_classification() -> None:
    classification, reason = route_classification_for_path(
        "POST",
        "/unregistered/side-effect",
        route_side_effect_class("/unregistered/side-effect"),
    )

    assert classification == "mutating_requires_authority"
    assert "unknown non-read route" in reason


def test_registered_routes_do_not_depend_on_implicit_api_boundary_fallback() -> None:
    manifest = client.get("/api/manifest").json()
    implicit_fallback_routes = [
        f"{route['method']} {route['path']}"
        for route in manifest["routes"]
        if route["path"] != "/api/manifest"
        and route_group_for_path(route["path"]) == "api-boundary"
    ]

    assert implicit_fallback_routes == []


def test_api_manifest_route_inventory_has_stable_operation_ids_and_side_effect_classes() -> (
    None
):
    manifest = client.get("/api/manifest").json()
    operation_ids = [route["operation_id"] for route in manifest["routes"]]

    assert len(operation_ids) == len(set(operation_ids))
    assert "get_api_manifest" in operation_ids
    assert all(
        route["side_effect_class"] != "production_runtime"
        for route in manifest["routes"]
    )
    assert all(route["requires_auth_future"] is True for route in manifest["routes"])
    assert all(route["blocked_from_production"] is True for route in manifest["routes"])
    assert manifest["route_classification_vocabulary"] == [
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
    ]
    assert set(manifest["route_classification_summary"]) == set(
        manifest["route_classification_vocabulary"]
    )
    assert (
        sum(manifest["route_classification_summary"].values())
        == manifest["route_count"]
    )
    assert manifest["route_auth_posture_summary"] == EXPECTED_AUTH_POSTURE_SUMMARY
    assert (
        manifest["route_approval_posture_summary"] == EXPECTED_APPROVAL_POSTURE_SUMMARY
    )
    assert (
        manifest["idempotency_audit_policy_ref"]
        == "idempotency:p1-084:mutating-routes:v1"
    )
    assert (
        manifest["route_idempotency_posture_summary"]
        == EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY
    )
    assert manifest["rate_limit_policy_ref"] == "rate-limit:p1-085:targeted-local:v1"
    assert (
        manifest["route_rate_limit_posture_summary"]
        == EXPECTED_RATE_LIMIT_POSTURE_SUMMARY
    )
    assert all(
        route["route_classification"] in manifest["route_classification_vocabulary"]
        for route in manifest["routes"]
    )
    assert all(route["classification_reason"] for route in manifest["routes"])
    assert all(
        route["protected_route"] is (route["route_classification"] != "public_metadata")
        for route in manifest["routes"]
    )
    assert all(
        route["auth_posture"]
        == (
            "public_metadata_no_auth"
            if route["route_classification"] == "public_metadata"
            else "protected_local_bearer_required"
        )
        for route in manifest["routes"]
    )
    assert all(
        route["approval_posture"]
        == (
            "required_before_mutation_authority"
            if route["route_classification"] == "mutating_requires_authority"
            else "not_required_for_route_classification"
        )
        for route in manifest["routes"]
    )
    assert all(
        route["idempotency_required"]
        is (route["route_classification"] == "mutating_requires_authority")
        for route in manifest["routes"]
    )
    assert all(route["rate_limit_reason"] for route in manifest["routes"])
    routes_by_path = {route["path"]: route for route in manifest["routes"]}
    assert routes_by_path["/health"]["route_classification"] == "public_metadata"
    assert routes_by_path["/version"]["route_classification"] == "public_metadata"
    assert routes_by_path["/api/manifest"]["route_classification"] == "public_metadata"
    assert (
        routes_by_path["/control-center/routes"]["route_classification"]
        == "local_readonly"
    )
    assert (
        routes_by_path["/runtime/readiness"]["route_classification"] == "local_readonly"
    )
    assert (
        routes_by_path["/control-center/today/summary"]["route_classification"]
        == "local_sensitive"
    )
    assert (
        routes_by_path["/files/tree/preview"]["route_classification"]
        == "local_sensitive"
    )
    assert (
        routes_by_path["/observability/session-events"]["route_classification"]
        == "local_sensitive"
    )
    assert (
        routes_by_path["/web-evidence/request"]["route_classification"]
        == "local_sensitive"
    )
    assert routes_by_path["/kernel/tasks/run"]["route_classification"] == (
        "mutating_requires_authority"
    )
    assert (
        routes_by_path["/task-decomposition/approvals/grants/capture"][
            "route_classification"
        ]
        == "mutating_requires_authority"
    )
    assert (
        routes_by_path["/task-decomposition/approvals/grants/capture"][
            "idempotency_posture"
        ]
        == "required_before_mutation_authority"
    )
    assert (
        routes_by_path["/task-decomposition/approvals/grants/capture"][
            "idempotency_policy_ref"
        ]
        == "idempotency:p1-084:mutating-routes:v1"
    )
    assert (
        routes_by_path["/task-decomposition/approvals/grants/capture"][
            "rate_limit_posture"
        ]
        == "targeted_local_fixed_window"
    )
    assert (
        routes_by_path["/task-decomposition/approvals/grants/capture"][
            "rate_limit_group"
        ]
        == "task_decomposition"
    )
    lifecycle_route = routes_by_path["/task-decomposition/runs/{run_id}/lifecycle"]
    assert lifecycle_route["side_effect_class"] == "local_dev_workspace_only"
    assert lifecycle_route["route_classification"] == "local_sensitive"
    assert lifecycle_route["approval_posture"] == "not_required_for_route_classification"
    assert lifecycle_route["idempotency_required"] is False
    assert lifecycle_route["rate_limit_group"] == "task_decomposition"
    assert routes_by_path["/files/tree/preview"]["idempotency_posture"] == (
        "not_required_for_route_classification"
    )
    assert routes_by_path["/files/tree/preview"]["rate_limit_posture"] == (
        "not_targeted_for_route"
    )
    assert routes_by_path["/models/route/preview"]["rate_limit_group"] == (
        "local_model_validation"
    )
    assert routes_by_path["/control-center/actions/preview"]["rate_limit_group"] == (
        "action_preview_proposal"
    )
    assert routes_by_path["/control-center/turn-router/preview"][
        "side_effect_class"
    ] == "validation_only"
    assert routes_by_path["/control-center/turn-router/preview"][
        "approval_posture"
    ] == "not_required_for_route_classification"
    assert routes_by_path["/control-center/turn-router/preview"]["rate_limit_group"] == (
        "action_preview_proposal"
    )
    assert routes_by_path["/v1/chat/completions"]["rate_limit_group"] == "model_chat"
    assert (
        routes_by_path["/v1/chat/completions"]["side_effect_class"]
        == "local_dev_workspace_only"
    )
    assert (
        routes_by_path["/files/tree/preview"]["side_effect_class"]
        == "local_dev_workspace_only"
    )
    assert (
        routes_by_path["/files/read/preview"]["side_effect_class"]
        == "local_dev_workspace_only"
    )
    assert routes_by_path["/control-center/setup-assistant/summary"][
        "side_effect_class"
    ] == ("validation_only")
    assert routes_by_path["/control-center/settings/status"][
        "route_classification"
    ] == ("local_readonly")
    assert routes_by_path["/control-center/settings/status"]["side_effect_class"] == (
        "validation_only"
    )
    assert routes_by_path["/control-center/settings/status"]["protected_route"] is True
    assert (
        routes_by_path["/control-center/providers/exact-approved-lanes/tiny"][
            "route_classification"
        ]
        == "mutating_requires_authority"
    )
    assert (
        routes_by_path["/control-center/providers/exact-approved-lanes/tiny"][
            "side_effect_class"
        ]
        == "local_dev_workspace_only"
    )
    assert (
        routes_by_path["/control-center/providers/exact-approved-lanes/tiny"][
            "idempotency_posture"
        ]
        == "required_before_mutation_authority"
    )
    assert (
        routes_by_path["/control-center/providers/exact-approved-lanes/tiny"][
            "rate_limit_group"
        ]
        == "provider_exact_approved_lane"
    )
    assert (
        routes_by_path["/control-center/providers/credentials/validate"][
            "route_classification"
        ]
        == "mutating_requires_authority"
    )
    assert (
        routes_by_path["/control-center/providers/credentials/validate"][
            "side_effect_class"
        ]
        == "governed_network_read_only"
    )
    assert (
        routes_by_path["/control-center/providers/credentials/validate"][
            "rate_limit_group"
        ]
        == "provider_credential_validation"
    )
    assert "/control-center/providers/draft-summarize" not in routes_by_path
    assert "/control-center/providers/draft-preview" not in routes_by_path
    assert (
        routes_by_path["/control-center/web-evidence/attach"][
            "route_classification"
        ]
        == "local_sensitive"
    )
    assert (
        routes_by_path["/control-center/web-evidence/attach"][
            "side_effect_class"
        ]
        == "governed_network_read_only"
    )
    assert (
        routes_by_path["/control-center/web-evidence/attach"][
            "idempotency_posture"
        ]
        == "not_required_for_route_classification"
    )
    assert (
        routes_by_path["/control-center/web-evidence/attach"][
            "idempotency_policy_ref"
        ]
        == "idempotency:web-evidence-product-slice:request-ref-payload"
    )
    assert "request_ref payload-idempotent" in (
        routes_by_path["/control-center/web-evidence/attach"][
            "idempotency_reason"
        ]
    )
    assert (
        routes_by_path["/control-center/web-evidence/attach"]["rate_limit_group"]
        == "web_evidence_product_slice"
    )
    assert routes_by_path["/control-center/local-models/status"][
        "route_classification"
    ] == ("local_readonly")
    assert routes_by_path["/control-center/local-models/status"][
        "side_effect_class"
    ] == ("validation_only")
    assert (
        routes_by_path["/control-center/local-models/status"]["protected_route"] is True
    )
    assert routes_by_path["/control-center/today/summary"]["side_effect_class"] == (
        "local_dev_workspace_only"
    )
    assert routes_by_path["/control-center/actions/inbox"]["side_effect_class"] == (
        "local_dev_workspace_only"
    )
    assert routes_by_path["/control-center/morning-briefing/summary"][
        "side_effect_class"
    ] == ("local_dev_workspace_only")
    assert routes_by_path["/control-center/storage/status"]["side_effect_class"] == (
        "local_dev_workspace_only"
    )
    assert "file_api_caller_selected_roots" in manifest["capabilities_blocked"]
    assert "file_api_raw_tree_paths" in manifest["capabilities_blocked"]
    assert "file_api_raw_content_write_payload" in manifest["capabilities_blocked"]
    assert "secret_api_raw_secret_values" in manifest["capabilities_blocked"]
    assert "local_loopback_default_bearer" in manifest["capabilities_blocked"]
    assert (
        "local_loopback_raw_provider_payload_passthrough"
        in manifest["capabilities_blocked"]
    )
    assert "control_center_setup_installer_actions" in manifest["capabilities_blocked"]
    assert "control_center_setup_model_downloads" in manifest["capabilities_blocked"]
    assert (
        "control_center_setup_launch_agent_changes" in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_setup_background_service_changes"
        in manifest["capabilities_blocked"]
    )
    assert (
        "control_center_setup_credential_handling" in manifest["capabilities_blocked"]
    )
    assert "task_decomposition_raw_request_echo" in manifest["capabilities_blocked"]
    assert "extension_catalog_callable_runtime" in manifest["capabilities_blocked"]
    assert "extension_catalog_runtime_import" in manifest["capabilities_blocked"]
    assert "extension_catalog_plugin_execution" in manifest["capabilities_blocked"]
    assert "extension_catalog_connector_writes" in manifest["capabilities_blocked"]
    assert "extension_activation_runtime_import" in manifest["capabilities_blocked"]
    assert "extension_activation_execution" in manifest["capabilities_blocked"]
    assert "extension_activation_callable_catalog" in manifest["capabilities_blocked"]
    assert "extension_activation_overbroad_grants" in manifest["capabilities_blocked"]
    assert "session_logging_raw_capture" in manifest["capabilities_blocked"]
    assert "session_logging_external_telemetry" in manifest["capabilities_blocked"]
    assert (
        "session_logging_os_wide_activity_monitoring"
        in manifest["capabilities_blocked"]
    )
    assert (
        "web_access_provider_shells_as_runtime_authority"
        in manifest["capabilities_blocked"]
    )
    assert "web_access_provider_sdk_imports" in manifest["capabilities_blocked"]
    assert "web_access_provider_credentials" in manifest["capabilities_blocked"]
    assert "search_provider_live_calls" in manifest["capabilities_blocked"]
    assert "firecrawl_provider_calls" in manifest["capabilities_blocked"]
    assert "firecrawl_scrape_jobs" in manifest["capabilities_blocked"]
    assert "browserbase_provider_sessions" in manifest["capabilities_blocked"]
    assert "mattermost_raw_transcript_storage" in manifest["capabilities_blocked"]
    assert "mattermost_unapproved_connector_writes" in manifest["capabilities_blocked"]
    assert (
        "mattermost_credential_or_cookie_handling" in manifest["capabilities_blocked"]
    )
    assert "mattermost_model_output_authority" in manifest["capabilities_blocked"]
    assert (
        "mattermost_unbounded_background_autonomy" in manifest["capabilities_blocked"]
    )
    assert routes_by_path["/integrations/mattermost/events/message"][
        "side_effect_class"
    ] == ("local_dev_workspace_only")
    assert routes_by_path["/integrations/mattermost/roles/bind"][
        "side_effect_class"
    ] == ("local_dev_workspace_only")
    assert routes_by_path["/observability/session-events"]["side_effect_class"] == (
        "local_dev_workspace_only"
    )
    assert routes_by_path["/observability/client-errors"]["side_effect_class"] == (
        "local_dev_workspace_only"
    )


def test_api_manifest_static_cache_policy_excludes_authority_and_private_state() -> (
    None
):
    policy = api_manifest_cache_policy()

    assert "routes" in API_MANIFEST_CACHEABLE_FIELDS
    assert "route_groups" in API_MANIFEST_CACHEABLE_FIELDS
    assert "capabilities_declared" in API_MANIFEST_CACHEABLE_FIELDS
    assert "web_access_posture" in API_MANIFEST_CACHEABLE_FIELDS
    assert "foundation_gate_status" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "local_auth_policy" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "policy_decisions" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "approvals" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "runtime_authority" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "user_data" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "secrets" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "mutable_state" in API_MANIFEST_CACHE_EXCLUDED_FIELDS
    assert "route_path_method_operation_tag_summary_change" in (
        API_MANIFEST_CACHE_INVALIDATION_RULES
    )
    assert "route_classification_logic_change" in API_MANIFEST_CACHE_INVALIDATION_RULES
    assert "route_auth_posture_logic_change" in API_MANIFEST_CACHE_INVALIDATION_RULES
    assert (
        "route_approval_posture_logic_change" in API_MANIFEST_CACHE_INVALIDATION_RULES
    )
    assert policy["authority_decisions_cached"] is False
    assert policy["policy_decisions_cached"] is False
    assert policy["approval_decisions_cached"] is False
    assert policy["secret_material_cached"] is False
    assert policy["durable_cache"] is False


def test_api_manifest_static_cache_keeps_dynamic_status_live() -> None:
    clear_api_manifest_static_cache(app)

    passed = build_api_manifest(app, foundation_gate_status="passed")
    failed = build_api_manifest(app, foundation_gate_status="failed")

    assert passed.foundation_gate_status == "passed"
    assert failed.foundation_gate_status == "failed"
    assert passed.route_count == failed.route_count
    assert passed.routes is not failed.routes
    assert passed.routes[0] is not failed.routes[0]


def test_api_manifest_static_cache_is_copy_isolated() -> None:
    local_app = FastAPI(title="Cache Isolation")

    @local_app.get("/health")
    def local_health() -> Any:
        return {"status": "ok"}

    clear_api_manifest_static_cache(local_app)
    manifest = build_api_manifest(local_app)
    manifest.routes.clear()
    manifest.web_access_posture.allowed_methods.append("GET")

    rebuilt = build_api_manifest(local_app)

    assert rebuilt.route_count == 1
    assert len(rebuilt.routes) == 1
    assert rebuilt.routes[0].path == "/health"
    assert rebuilt.web_access_posture.allowed_methods == []


def test_api_manifest_static_cache_invalidates_when_route_risk_changes() -> None:
    local_app = FastAPI(title="Cache Invalidation")

    @local_app.get("/api/status")
    def local_status() -> Any:
        return {"status": "ok"}

    clear_api_manifest_static_cache(local_app)
    first = build_api_manifest(local_app)

    @local_app.post("/files/cache-test")
    def local_file_preview() -> Any:
        return {"status": "ok"}

    second = build_api_manifest(local_app)
    routes_by_path = {route.path: route for route in second.routes}

    assert second.route_count == first.route_count + 1
    assert routes_by_path["/files/cache-test"].side_effect_class == (
        "local_dev_workspace_only"
    )
    assert routes_by_path["/files/cache-test"].route_classification == (
        "mutating_requires_authority"
    )
    assert routes_by_path["/files/cache-test"].validation_only is False


def test_validation_error_response_does_not_echo_secret_like_payload() -> None:
    secret_value = "ABCDEFGHIJKLMNOP"
    payload = {
        "event_id": "evt_api_secret",
        "event_type": "run",
        "event_name": "run.created",
        "run_id": "run_api_secret",
        "trace_id": "trace_api",
        "span_id": "span_api",
        "correlation_id": "corr_api",
        "actor_context": {
            "actor_type": "orchestrator",
            "actor_id": "test_orchestrator",
            "authority_source": "explicit_user_request",
        },
        "temporal_context": {
            "current_time_utc": "2026-05-30T12:00:00",
            "freshness_class": "daily",
            "staleness_policy": "allow_with_label",
        },
        "data_classification": {
            "classification": "project_private",
            "source": "api_contract_test",
        },
        "event_source": "test_source",
        "subject": "Agent Execution",
        "action": "start",
        "outcome": "blocked",
        "status": "failed",
        "severity": "warning",
        "metadata": {"note": f"api_key='{secret_value}'"},
    }

    response = client.post("/events/validate", json=payload)

    assert response.status_code == 200
    body_text = response.text
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "SECRET_EXPOSURE_BLOCKED"
    assert secret_value not in body_text


def test_openapi_schema_has_no_raw_secret_request_fields() -> None:
    findings = forbidden_raw_secret_schema_fields(app.openapi())

    assert findings == []


def test_openapi_schema_has_no_raw_provider_payload_fields() -> None:
    schema = app.openapi()
    findings = forbidden_raw_provider_schema_fields(schema)
    chat_schema = schema["components"]["schemas"]["V1ChatCompletionAPIRequest"]

    assert findings == []
    assert "model" in chat_schema["properties"]
    assert "messages" in chat_schema["properties"]
