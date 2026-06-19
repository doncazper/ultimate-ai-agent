from fastapi import FastAPI
from fastapi.routing import APIRoute

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.contracts import ApiManifest, ApiRouteInventoryItem, ApiRouteSideEffectClass


CAPABILITIES_DECLARED = [
    "api_contract_metadata",
    "openapi_schema_export",
    "typed_validation_routes",
    "foundation_gate_reporting",
    "local_dev_approval_validation",
    "manual_local_loopback_smoke_validation",
    "remote_worker_foundation_dry_run",
    "runtime_readiness_status",
    "manual_smoke_report_validation",
    "control_center_read_only_dashboard",
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
    "secret_api_reference_only_handles",
]

CAPABILITIES_BLOCKED = [
    "runtime_model_calls",
    "provider_api_calls",
    "web_fetching",
    "browser_automation",
    "production_persistence",
    "runtime_agent_config_loading",
    "runtime_execution_routes",
    "plugin_enablement_routes",
    "control_center_execution",
    "control_center_plugin_enablement",
    "control_center_frontend_native_build_control",
    "control_center_mobile_sensor_access",
    "control_center_remote_dispatch",
    "control_center_model_provider_invocation",
    "openwebui_runtime_authority",
    "openwebui_provider_calls",
    "openwebui_shell_tool_execution",
    "openwebui_memory_writes",
    "openwebui_context_injection",
    "local_loopback_default_bearer",
    "local_loopback_raw_provider_payload_passthrough",
    "file_api_caller_selected_roots",
    "file_api_raw_diff_return",
    "file_api_raw_content_write_payload",
    "secret_api_raw_secret_values",
    "task_decomposition_raw_request_echo",
    "task_decomposition_unrestricted_external_execution",
    "task_decomposition_unreviewed_handler_imports",
    "task_decomposition_unscoped_approval_authority",
]

ROUTE_GROUPS_BY_PREFIX = {
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
    "/v1": "openwebui-local-test",
}

LOCAL_DEV_WORKSPACE_PREFIXES = ("/kernel", "/files", "/memory", "/task-decomposition", "/v1")
VALIDATION_HINTS = ("/validate", "/preview", "/evaluate", "/route", "/freshness/check", "/dry-run")


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
    stem = path.strip("/").replace("-", "_").replace("/", "_").replace("{", "").replace("}", "")
    return f"{method.lower()}_{stem or 'root'}"


def route_summary(method: str, path: str) -> str:
    action = " ".join(stable_operation_id(method, path).split("_"))
    return action.capitalize()


def route_side_effect_class(path: str) -> ApiRouteSideEffectClass:
    if path == "/api/manifest" or path in {"/health", "/version"}:
        return ApiRouteSideEffectClass.none
    if path.startswith(LOCAL_DEV_WORKSPACE_PREFIXES):
        return ApiRouteSideEffectClass.local_dev_workspace_only
    if any(hint in path for hint in VALIDATION_HINTS):
        return ApiRouteSideEffectClass.validation_only
    return ApiRouteSideEffectClass.validation_only


def iter_api_route_items(app: FastAPI) -> list[ApiRouteInventoryItem]:
    items: list[ApiRouteInventoryItem] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(method for method in route.methods if method not in {"HEAD", "OPTIONS"})
        for method in methods:
            operation_id = route.operation_id or stable_operation_id(method, route.path)
            tags = list(route.tags or [route_group_for_path(route.path)])
            side_effect_class = route_side_effect_class(route.path)
            items.append(
                ApiRouteInventoryItem(
                    path=route.path,
                    method=method,
                    operation_id=operation_id,
                    tags=tags,
                    summary=route.summary or route_summary(method, route.path),
                    validation_only=side_effect_class == ApiRouteSideEffectClass.validation_only,
                    side_effect_class=side_effect_class,
                )
            )
    return sorted(items, key=lambda item: (item.path, item.method))


def build_api_manifest(app: FastAPI, foundation_gate_status: str | None = None) -> ApiManifest:
    routes = iter_api_route_items(app)
    route_groups = sorted({tag for route in routes for tag in route.tags})
    return ApiManifest(
        title=app.title,
        api_version=__version__,
        package_version=__version__,
        active_baseline=active_baseline_label(),
        route_count=len(routes),
        route_groups=route_groups,
        routes=routes,
        foundation_gate_status=foundation_gate_status,
        capabilities_declared=CAPABILITIES_DECLARED,
        capabilities_blocked=CAPABILITIES_BLOCKED,
        no_runtime_integrations=True,
    )
