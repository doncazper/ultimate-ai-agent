from fastapi import FastAPI
from fastapi.routing import APIRoute

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.contracts import ApiContractStatus, ApiRouteSideEffectClass
from ultimate_ai_agent.api.manifest import iter_api_route_items, route_group_for_path, route_summary, stable_operation_id


FORBIDDEN_ROUTE_FRAGMENTS = [
    "/models/generate",
    "/models/complete",
    "/models/invoke",
    "/providers/call",
    "/providers/invoke",
    "/web/fetch",
    "/browser",
    "/scanners",
    "/tools/execute",
    "/agent/config/load",
    "/runtime/config/load",
    "/runtime/execute",
    "/runtime/run",
    "/runtime/connect",
    "/runtime/dispatch",
    "/runtime/smoke-reports/execute",
    "/runtime/plugins/enable",
    "/control-center/actions/execute",
    "/control-center/plugins/enable",
    "/control-center/runtime/execute",
    "/control-center/remote-workers/dispatch",
    "/control-center/mobile/sensors",
    "/control-center/frontend",
    "/model-runtime/local/execute",
    "/model-runtime/local/smoke/execute",
    "/remote-workers/dispatch",
    "/remote-workers/execute",
    "/remote-workers/subagents/launch",
]


def configure_openapi_contract(app: FastAPI) -> None:
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(method for method in route.methods if method not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        method = methods[0]
        route.operation_id = route.operation_id or stable_operation_id(method, route.path)
        route.tags = list(route.tags or [route_group_for_path(route.path)])
        route.summary = route.summary or route_summary(method, route.path)
    app.openapi_schema = None


def verify_openapi_contract(app: FastAPI) -> ApiContractStatus:
    errors: list[str] = []
    warnings: list[str] = []
    schema = {}
    try:
        schema = app.openapi()
    except Exception as exc:
        errors.append(f"OpenAPI generation failed: {exc}")

    if schema and schema.get("info", {}).get("version") != __version__:
        errors.append("OpenAPI info.version does not match package version")

    routes = iter_api_route_items(app)
    operation_ids = [route.operation_id for route in routes]
    duplicate_ids = sorted({operation_id for operation_id in operation_ids if operation_ids.count(operation_id) > 1})
    if duplicate_ids:
        errors.append(f"Duplicate operation IDs: {', '.join(duplicate_ids)}")

    for route in routes:
        if route.side_effect_class not in {
            ApiRouteSideEffectClass.none.value,
            ApiRouteSideEffectClass.validation_only.value,
            ApiRouteSideEffectClass.local_dev_workspace_only.value,
        }:
            errors.append(f"Unsafe side-effect class on {route.method} {route.path}")
        if not route.requires_auth_future:
            warnings.append(f"Future auth marker missing on {route.method} {route.path}")
        if not route.blocked_from_production:
            errors.append(f"Production block marker missing on {route.method} {route.path}")

    unsafe_routes = [
        route.path
        for route in routes
        if any(fragment in route.path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
    ]
    if unsafe_routes:
        errors.append(f"Forbidden runtime routes present: {', '.join(sorted(set(unsafe_routes)))}")

    return ApiContractStatus(
        version_consistent=not schema or schema.get("info", {}).get("version") == __version__,
        openapi_generated=bool(schema),
        route_inventory_valid=bool(routes),
        operation_ids_unique=not duplicate_ids,
        unsafe_routes_detected=bool(unsafe_routes),
        warnings=warnings,
        errors=errors,
    )
