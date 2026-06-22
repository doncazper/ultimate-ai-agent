#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.idempotency import API_IDEMPOTENCY_AUDIT_POLICY_REF  # noqa: E402
from ultimate_ai_agent.api.local_auth import (  # noqa: E402
    LOCAL_API_AUTH_ENABLED_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.rate_limits import (  # noqa: E402
    API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
    API_TARGETED_RATE_LIMIT_POLICY_REF,
    API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV,
    reset_api_rate_limit_state,
)
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.api_routes import (  # noqa: E402
    EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY,
    EXPECTED_MUTATING_ROUTES,
    EXPECTED_RATE_LIMIT_GROUPS,
    EXPECTED_RATE_LIMIT_POSTURE_SUMMARY,
    EXPECTED_ROUTE_COUNT,
    append_route_fixture_mismatches,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
)


CONTRACT_DOC = "docs/api/UAA_P1_086_API_BOUNDARY_ENFORCEMENT_TESTS.md"
ROUTE_STATUS_MANIFEST = "docs/control_center/route_status_manifest.json"
PUBLIC_METADATA_ROUTES = {
    ("GET", "/api/manifest"),
    ("GET", "/health"),
    ("GET", "/version"),
}
SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "Referrer-Policy",
    "X-Frame-Options",
    "Permissions-Policy",
    "Content-Security-Policy",
]
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "OpenAPI, `/api/manifest`, and route inventory enforcement tests",
        "auth:p1-083:local-protected-routes:v1",
        "idempotency:p1-084:mutating-routes:v1",
        "rate-limit:p1-085:targeted-local:v1",
        "No new runtime authority",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-086 adds enforcement tests",
        "This does not add routes, middleware, runtime authority, public beta, or production authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-086 implements route inventory enforcement checks",
    ],
}
FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "public release ready",
    "production authority is granted",
    "enterprise auth is implemented",
    "oauth is implemented",
    "distributed quota is implemented",
    "durable dedupe store is implemented",
    "exactly-once execution is implemented",
]
SUCCESS_MESSAGE = "UAA-P1-086 API boundary enforcement tests verification passed."


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []

    _append_openapi_manifest_alignment_failures(failures, context)
    _append_manifest_route_posture_failures(failures, context)
    _append_route_status_manifest_failures(failures, context)
    _append_runtime_boundary_sample_failures(failures, context)
    _append_docs_failures(failures)
    return failures


def _append_openapi_manifest_alignment_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    schema = context.app.openapi()
    manifest = context.manifest
    openapi_route_keys: set[tuple[str, str]] = set()
    openapi_operation_ids: dict[tuple[str, str], str] = {}

    for path, methods in schema.get("paths", {}).items():
        for method, operation in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            key = (method.upper(), path)
            openapi_route_keys.add(key)
            openapi_operation_ids[key] = operation.get("operationId", "")
            if not operation.get("tags"):
                failures.append(f"OpenAPI operation missing tags: {method.upper()} {path}")

    manifest_route_keys = set(context.routes_by_key)
    if openapi_route_keys != manifest_route_keys:
        missing = sorted(manifest_route_keys - openapi_route_keys)
        extra = sorted(openapi_route_keys - manifest_route_keys)
        failures.append(f"OpenAPI and /api/manifest route keys drifted: missing={missing} extra={extra}")

    operation_ids = list(openapi_operation_ids.values())
    if len(operation_ids) != len(set(operation_ids)):
        failures.append("OpenAPI operation ids are not unique")
    for key, route in context.routes_by_key.items():
        if openapi_operation_ids.get(key) != route["operation_id"]:
            failures.append(f"{key[0]} {key[1]} operationId drifted between OpenAPI and manifest")

    if manifest.get("route_count") != EXPECTED_ROUTE_COUNT:
        failures.append(f"/api/manifest route_count drifted: {manifest.get('route_count')}")
    append_route_fixture_mismatches(failures, manifest, label="route inventory fixture")


def _append_manifest_route_posture_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    manifest = context.manifest
    if manifest.get("route_idempotency_posture_summary") != EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY:
        failures.append("/api/manifest idempotency posture summary drifted")
    if manifest.get("route_rate_limit_posture_summary") != EXPECTED_RATE_LIMIT_POSTURE_SUMMARY:
        failures.append("/api/manifest rate-limit posture summary drifted")
    if manifest.get("idempotency_audit_policy_ref") != API_IDEMPOTENCY_AUDIT_POLICY_REF:
        failures.append("/api/manifest idempotency policy ref drifted")
    if manifest.get("rate_limit_policy_ref") != API_TARGETED_RATE_LIMIT_POLICY_REF:
        failures.append("/api/manifest rate-limit policy ref drifted")

    capabilities_declared = set(manifest.get("capabilities_declared", []))
    capabilities_blocked = set(manifest.get("capabilities_blocked", []))
    for capability in [
        "local_protected_route_bearer_gate",
        "mutating_route_idempotency_audit",
        "targeted_local_rate_limits",
    ]:
        if capability not in capabilities_declared:
            failures.append(f"/api/manifest missing declared capability {capability}")
    for blocked in [
        "local_protected_route_gate_as_enterprise_auth",
        "local_protected_route_gate_as_oauth",
        "local_protected_route_gate_as_password_flow",
        "idempotency_audit_as_exactly_once_execution",
        "idempotency_audit_as_durable_dedupe_store",
        "idempotency_audit_as_mutation_authority",
        "targeted_rate_limits_as_auth",
        "targeted_rate_limits_as_distributed_quota",
        "targeted_rate_limits_as_production_authority",
        "task_decomposition_unscoped_approval_authority",
    ]:
        if blocked not in capabilities_blocked:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    public_routes = {
        key for key, route in context.routes_by_key.items()
        if route["route_classification"] == "public_metadata"
    }
    if public_routes != PUBLIC_METADATA_ROUTES:
        failures.append(f"public metadata route set drifted: {sorted(public_routes)}")

    targeted_groups = set()
    mutating_routes = set()
    for key, route in context.routes_by_key.items():
        if not route.get("classification_reason"):
            failures.append(f"{key[0]} {key[1]} missing classification reason")
        if not route.get("idempotency_reason"):
            failures.append(f"{key[0]} {key[1]} missing idempotency reason")
        if not route.get("rate_limit_reason"):
            failures.append(f"{key[0]} {key[1]} missing rate-limit reason")
        expected_protected = route["route_classification"] != "public_metadata"
        if route["protected_route"] is not expected_protected:
            failures.append(f"{key[0]} {key[1]} protected-route posture drifted")
        if route["requires_auth_future"] is not True:
            failures.append(f"{key[0]} {key[1]} requires_auth_future drifted")
        if route["blocked_from_production"] is not True:
            failures.append(f"{key[0]} {key[1]} production block marker drifted")

        if route["route_classification"] == "mutating_requires_authority":
            mutating_routes.add(key)
            if route["protected_route"] is not True:
                failures.append(f"{key[0]} {key[1]} mutating route is not protected")
            if route["idempotency_required"] is not True:
                failures.append(f"{key[0]} {key[1]} mutating route does not require idempotency")
            if route["idempotency_posture"] != "required_before_mutation_authority":
                failures.append(f"{key[0]} {key[1]} mutating idempotency posture drifted")
            if route["idempotency_policy_ref"] != API_IDEMPOTENCY_AUDIT_POLICY_REF:
                failures.append(f"{key[0]} {key[1]} mutating idempotency policy ref drifted")
            if "authority" not in route["classification_reason"]:
                failures.append(f"{key[0]} {key[1]} mutating route lacks authority posture reason")
        elif route["idempotency_required"] is not False or route["idempotency_policy_ref"] is not None:
            failures.append(f"{key[0]} {key[1]} non-mutating idempotency posture drifted")

        if route["rate_limit_targeted"] is True:
            targeted_groups.add(route["rate_limit_group"])
            if route["rate_limit_posture"] != "targeted_local_fixed_window":
                failures.append(f"{key[0]} {key[1]} targeted rate-limit posture drifted")
            if route["rate_limit_policy_ref"] != API_TARGETED_RATE_LIMIT_POLICY_REF:
                failures.append(f"{key[0]} {key[1]} targeted rate-limit policy ref drifted")
        elif route["rate_limit_policy_ref"] is not None or route["rate_limit_group"] is not None:
            failures.append(f"{key[0]} {key[1]} non-targeted rate-limit posture drifted")

    if mutating_routes != EXPECTED_MUTATING_ROUTES:
        failures.append(f"mutating route set drifted: {sorted(mutating_routes)}")
    if targeted_groups != EXPECTED_RATE_LIMIT_GROUPS:
        failures.append(f"targeted rate-limit groups drifted: {sorted(targeted_groups)}")


def _append_route_status_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    route_status = load_json(ROUTE_STATUS_MANIFEST)
    for section_name, route_key in (
        ("surfaces", "current_backend_routes"),
        ("visible_actions", "backend_routes"),
    ):
        for item in route_status.get(section_name, []):
            for route in item.get(route_key, []):
                key = (route.get("method"), route.get("path"))
                manifest_route = context.routes_by_key.get(key)
                if manifest_route is None:
                    failures.append(f"route status manifest references missing route: {key}")
                    continue
                for field in ["operation_id", "side_effect_class", "route_classification"]:
                    if route.get(field) != manifest_route[field]:
                        failures.append(
                            f"route status manifest {key[0]} {key[1]} {field} mismatch"
                        )


def _append_runtime_boundary_sample_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    _append_security_header_failures(
        failures,
        "GET /health",
        context.https_client.get("/health"),
        expect_hsts=True,
    )

    env = {
        LOCAL_API_AUTH_ENABLED_ENV: "1",
        LOCAL_API_BEARER_ENV: "p1-086-local-bearer",
    }
    with patch.dict(os.environ, env, clear=False):
        missing_auth = context.client.get("/control-center/today/summary")
        allowed_auth = context.client.get(
            "/control-center/today/summary",
            headers={"Authorization": "Bearer p1-086-local-bearer"},
        )
    if missing_auth.status_code != 401:
        failures.append(f"protected route without bearer returned {missing_auth.status_code}")
    if allowed_auth.status_code == 401:
        failures.append("protected route rejected configured bearer")
    if "p1-086-local-bearer" in missing_auth.text:
        failures.append("local auth failure echoed bearer material")
    _append_security_header_failures(failures, "local auth failure", missing_auth)

    missing_idempotency = context.client.post(
        "/task-decomposition/run",
        json={"raw_request": "safe summary"},
    )
    if missing_idempotency.status_code != 428:
        failures.append(f"mutating route without idempotency returned {missing_idempotency.status_code}")
    _append_security_header_failures(failures, "idempotency failure", missing_idempotency)

    env = {
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV: "1",
        API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV: "60",
    }
    with patch.dict(os.environ, env, clear=False):
        reset_api_rate_limit_state()
        context.client.post("/models/route/preview", json={"unsafe": "safe summary"})
        rate_limited = context.client.post(
            "/models/route/preview",
            headers={"Origin": "http://localhost:5173"},
            json={"unsafe": "safe summary"},
        )
    if rate_limited.status_code != 429:
        failures.append(f"targeted route second request returned {rate_limited.status_code}")
    if rate_limited.headers.get("X-UAA-Rate-Limit-Policy") != API_TARGETED_RATE_LIMIT_POLICY_REF:
        failures.append("rate-limit response missing targeted policy header")
    _append_security_header_failures(failures, "rate-limit failure", rate_limited)
    if rate_limited.headers.get("Access-Control-Allow-Origin") != "http://localhost:5173":
        failures.append("rate-limit failure missing allowed loopback CORS origin")

    preflight = context.client.options(
        "/task-decomposition/run",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": (
                "content-type, authorization, x-uaa-idempotency-key, "
                "x-uaa-idempotency-ref"
            ),
        },
    )
    if preflight.status_code != 200:
        failures.append(f"boundary CORS preflight returned {preflight.status_code}")
    allow_headers = preflight.headers.get("Access-Control-Allow-Headers", "")
    for header_name in ["Authorization", "X-UAA-Idempotency-Key", "X-UAA-Idempotency-Ref"]:
        if header_name not in allow_headers:
            failures.append(f"boundary CORS preflight missing {header_name}")
    if preflight.headers.get("Access-Control-Allow-Credentials") is not None:
        failures.append("boundary CORS preflight exposed credentials")


def _append_security_header_failures(
    failures: list[str],
    label: str,
    response: Any,
    *,
    expect_hsts: bool = False,
) -> None:
    for header_name in SECURITY_HEADERS:
        if not response.headers.get(header_name):
            failures.append(f"{label} missing {header_name}")
    if expect_hsts and not response.headers.get("Strict-Transport-Security"):
        failures.append(f"{label} missing HTTPS-only HSTS")


def _append_docs_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [
            CONTRACT_DOC,
            "docs/api/openapi_contract.md",
            "docs/api/route_inventory.md",
            "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            "docs/kanban/current_board.md",
            "docs/kanban/founder_command_center_board.md",
            "README.md",
            "VERSION.md",
        ],
        FORBIDDEN_CLAIMS,
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
