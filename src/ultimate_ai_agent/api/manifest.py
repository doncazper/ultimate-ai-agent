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
]

CAPABILITIES_BLOCKED = [
    "runtime_model_calls",
    "provider_api_calls",
    "web_fetching",
    "browser_automation",
    "production_persistence",
    "runtime_agent_config_loading",
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
}

LOCAL_DEV_WORKSPACE_PREFIXES = ("/kernel", "/files", "/memory")
VALIDATION_HINTS = ("/validate", "/preview", "/evaluate", "/route", "/freshness/check", "/dry-run")


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
        active_baseline=f"v{__version__}",
        route_count=len(routes),
        route_groups=route_groups,
        routes=routes,
        foundation_gate_status=foundation_gate_status,
        capabilities_declared=CAPABILITIES_DECLARED,
        capabilities_blocked=CAPABILITIES_BLOCKED,
        no_runtime_integrations=True,
    )
