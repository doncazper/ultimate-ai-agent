from collections import Counter

from fastapi import FastAPI
from fastapi.routing import APIRoute

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.contracts import ApiContractStatus, ApiRouteSideEffectClass
from ultimate_ai_agent.api.manifest import (
    CONTROL_CENTER_MATRIX_ROOMS_MEDIA_SIDE_EFFECTS,
    iter_api_route_items,
    route_group_for_path,
    route_summary,
    stable_operation_id,
)


FORBIDDEN_ROUTE_FRAGMENTS = [
    "/models/generate",
    "/models/complete",
    "/models/invoke",
    "/providers/call",
    "/providers/invoke",
    "/local-models",
    "/local-models/search",
    "/local-models/acquire",
    "/model-management",
    "/hf/search",
    "/huggingface/search",
    "/hardware/probe",
    "/system/probe",
    "/models/download",
    "/models/pull",
    "/models/load",
    "/models/unload",
    "/models/delete",
    "/model-runtime/local/start",
    "/model-runtime/local/restart",
    "/llama-cpp/server",
    "/llama-cpp/settings/apply",
    "/v1/responses",
    "/v1/completions",
    "/v1/embeddings",
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
    "/model-runtime/local/download",
    "/model-runtime/local/load",
    "/model-runtime/local/unload",
    "/model-runtime/local/serve",
    "/model-runtime/local/smoke/execute",
    "/control-center/local-models/execute",
    "/control-center/local-models/download",
    "/control-center/local-models/apply",
    "/control-center/local-models/start",
    "/control-center/model-management/execute",
    "/control-center/model-management/apply",
    "/remote-workers/dispatch",
    "/remote-workers/execute",
    "/remote-workers/subagents/launch",
]
FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS = {
    "/control-center/local-models/status",
    "/api/runtime/run-events",
}

FORBIDDEN_RAW_SECRET_SCHEMA_FIELDS = {
    "api_key",
    "client_secret",
    "credential_value",
    "password",
    "private_key",
    "raw_secret",
    "secret_value",
    "token",
}

FORBIDDEN_RAW_PROVIDER_SCHEMA_FIELDS = {
    "provider_payload",
    "raw_prompt",
    "raw_provider_payload",
}


def forbidden_raw_secret_schema_fields(schema: dict) -> list[str]:
    findings: list[str] = []

    def visit(node: object, path: str) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for field_name in properties:
                    if field_name in FORBIDDEN_RAW_SECRET_SCHEMA_FIELDS:
                        findings.append(f"{path}.properties.{field_name}")
            for key, value in node.items():
                visit(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, f"{path}[{index}]")

    visit(schema, "$")
    return sorted(set(findings))


def forbidden_raw_provider_schema_fields(schema: dict) -> list[str]:
    findings: list[str] = []

    def visit(node: object, path: str) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for field_name in properties:
                    if field_name in FORBIDDEN_RAW_PROVIDER_SCHEMA_FIELDS:
                        findings.append(f"{path}.properties.{field_name}")
            for key, value in node.items():
                visit(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, f"{path}[{index}]")

    visit(schema, "$")
    return sorted(set(findings))


def configure_openapi_contract(app: FastAPI) -> None:
    _register_safe_api_extensions(app)
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(
            method for method in route.methods if method not in {"HEAD", "OPTIONS"}
        )
        if not methods:
            continue
        method = methods[0]
        route.operation_id = route.operation_id or stable_operation_id(
            method, route.path
        )
        route.tags = list(route.tags or [route_group_for_path(route.path)])
        route.summary = route.summary or route_summary(method, route.path)
    app.openapi_schema = None


def _register_safe_api_extensions(app: FastAPI) -> None:
    from ultimate_ai_agent.api.mattermost import register_mattermost_routes
    from ultimate_ai_agent.api.web_evidence import register_governed_web_evidence_routes

    register_governed_web_evidence_routes(app)
    register_mattermost_routes(app)


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
    operation_id_counts = Counter(operation_ids)
    duplicate_ids = sorted(
        operation_id for operation_id, count in operation_id_counts.items() if count > 1
    )
    if duplicate_ids:
        errors.append(f"Duplicate operation IDs: {', '.join(duplicate_ids)}")

    legacy_safe_side_effects = {
        ApiRouteSideEffectClass.none.value,
        ApiRouteSideEffectClass.validation_only.value,
        ApiRouteSideEffectClass.local_dev_workspace_only.value,
        ApiRouteSideEffectClass.governed_network_read_only.value,
    }
    matrix_mutation_side_effects = {
        "/control-center/communications/matrix/credential-auth-create": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix/sso-launch": (
            ApiRouteSideEffectClass.system_browser_exact_launch.value
        ),
        "/control-center/communications/matrix/sso-callback-consume": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix/refresh": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix/logout": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix/revoke-all": (
            ApiRouteSideEffectClass.destructive_external.value
        ),
        "/control-center/communications/matrix/credential-store-rotate": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix/credential-delete": (
            ApiRouteSideEffectClass.destructive_local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/send": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/reply": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/thread": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/reaction": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/edit": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/redaction": (
            ApiRouteSideEffectClass.destructive_external.value
        ),
        "/control-center/communications/matrix-messaging/typing": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/read-receipt": (
            ApiRouteSideEffectClass.authenticated_connector_mutation.value
        ),
        "/control-center/communications/matrix-messaging/draft-write": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/draft-read": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/outbox-enqueue": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/outbox-read": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/outbox-transition": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/outbox-discard": (
            ApiRouteSideEffectClass.destructive_local_sensitive.value
        ),
        "/control-center/communications/matrix-messaging/desktop-notify": (
            ApiRouteSideEffectClass.local_sensitive.value
        ),
        **{
            path: side_effect.value
            for path, side_effect in CONTROL_CENTER_MATRIX_ROOMS_MEDIA_SIDE_EFFECTS.items()
        },
    }
    for route in routes:
        exact_matrix_side_effect = matrix_mutation_side_effects.get(route.path)
        if route.side_effect_class not in legacy_safe_side_effects and (
            route.method != "POST"
            or exact_matrix_side_effect != route.side_effect_class
        ):
            errors.append(f"Unsafe side-effect class on {route.method} {route.path}")
        if not route.requires_auth_future:
            warnings.append(
                f"Future auth marker missing on {route.method} {route.path}"
            )
        if not route.blocked_from_production:
            errors.append(
                f"Production block marker missing on {route.method} {route.path}"
            )

    unsafe_routes = [
        route.path
        for route in routes
        if route.path not in FORBIDDEN_ROUTE_FRAGMENT_EXEMPTIONS
        and any(fragment in route.path for fragment in FORBIDDEN_ROUTE_FRAGMENTS)
    ]
    if unsafe_routes:
        errors.append(
            f"Forbidden runtime routes present: {', '.join(sorted(set(unsafe_routes)))}"
        )

    raw_secret_fields = forbidden_raw_secret_schema_fields(schema) if schema else []
    if raw_secret_fields:
        errors.append(
            f"Forbidden raw-secret schema fields present: {', '.join(raw_secret_fields)}"
        )

    raw_provider_fields = forbidden_raw_provider_schema_fields(schema) if schema else []
    if raw_provider_fields:
        errors.append(
            f"Forbidden raw-provider schema fields present: {', '.join(raw_provider_fields)}"
        )

    return ApiContractStatus(
        version_consistent=not schema
        or schema.get("info", {}).get("version") == __version__,
        openapi_generated=bool(schema),
        route_inventory_valid=bool(routes),
        operation_ids_unique=not duplicate_ids,
        unsafe_routes_detected=bool(unsafe_routes),
        warnings=warnings,
        errors=errors,
    )
