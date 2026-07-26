#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.cors import (  # noqa: E402
    CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS,
    CONTROL_CENTER_LOOPBACK_CORS_HEADERS,
    CONTROL_CENTER_LOOPBACK_CORS_METHODS,
    CONTROL_CENTER_LOOPBACK_CORS_ORIGINS,
    LOOPBACK_CORS_POLICY_REF,
)
from ultimate_ai_agent.api.security_headers import FASTAPI_SECURITY_HEADERS  # noqa: E402
from scripts.verification.api_routes import append_expected_route_count  # noqa: E402
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)


CONTRACT_DOC = "docs/api/UAA_P1_082_EXPLICIT_LOOPBACK_CORS_ALLOWLIST.md"
SCHEMA_DOC = "docs/schemas/api_loopback_cors.schema.json"
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "cors:p1-082:loopback:v1",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
        "http://localhost:4173",
        "Authorization",
        "X-UAA-Idempotency-Key",
        "X-UAA-Idempotency-Ref",
        "X-UAA-Control-Center-Mutation-Binding",
        "X-UAA-Expected-Backend-Revision-Ref",
        "X-UAA-Expected-Backend-Instance-Ref",
        "X-UAA-Expected-Backend-Truth-Ref",
        "wildcard CORS remains denied",
        "CORS is browser hardening, not authentication",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-082",
        "explicit loopback CORS allowlisting",
        "wildcard CORS remains denied",
        "does not add auth, sessions, idempotency enforcement, rate limits, dependencies, route authority, or runtime authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-082",
        "explicit loopback CORS allowlist posture",
    ],
}
FORBIDDEN_CLAIMS = [
    "cors is authentication",
    "cors is authorization",
    "cors grants route authority",
    "wildcard cors allowed",
    "wildcard cors enabled",
    "public beta is ready",
    "public release ready",
    "production ready because of cors",
]
SUCCESS_MESSAGE = "UAA-P1-082 loopback CORS verification passed."


def _read(path: str) -> str:
    return read_text(path)


def _policy_payload() -> dict[str, Any]:
    return {
        "policy_ref": LOOPBACK_CORS_POLICY_REF,
        "allowed_origins": list(CONTROL_CENTER_LOOPBACK_CORS_ORIGINS),
        "blocked_origins": [
            "https://example.com",
            "http://localhost:9999",
            "http://192.168.1.2:5173",
            "null",
        ],
        "allowed_methods": list(CONTROL_CENTER_LOOPBACK_CORS_METHODS),
        "allowed_headers": list(CONTROL_CENTER_LOOPBACK_CORS_HEADERS),
        "exposed_headers": list(CONTROL_CENTER_LOOPBACK_CORS_EXPOSE_HEADERS),
        "allow_credentials": False,
        "wildcard_allowed": False,
        "cors_is_auth": False,
    }


def _preflight(client: Any, origin: str, method: str = "POST"):
    return client.options(
        "/contracts/validate",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": (
                "content-type, authorization, x-uaa-idempotency-key, "
                "x-uaa-idempotency-ref, "
                "x-uaa-control-center-mutation-binding, "
                "x-uaa-expected-backend-revision-ref, "
                "x-uaa-expected-backend-instance-ref, "
                "x-uaa-expected-backend-truth-ref"
            ),
        },
    )


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA_DOC))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(_policy_payload()),
        key=lambda error: error.path,
    )
    for error in errors:
        failures.append(f"api loopback CORS schema error: {error.message}")

    if "*" in CONTROL_CENTER_LOOPBACK_CORS_ORIGINS:
        failures.append("loopback CORS origins include wildcard")
    if any("0.0.0.0" in origin for origin in CONTROL_CENTER_LOOPBACK_CORS_ORIGINS):
        failures.append("loopback CORS origins include non-loopback bind-all host")
    if CONTROL_CENTER_LOOPBACK_CORS_METHODS != ("GET", "POST"):
        failures.append("loopback CORS methods must stay GET/POST only")

    client = context.client
    for origin in CONTROL_CENTER_LOOPBACK_CORS_ORIGINS:
        response = client.get("/health", headers={"Origin": origin})
        if response.headers.get("Access-Control-Allow-Origin") != origin:
            failures.append(f"allowed origin missing exact allow header: {origin}")
        if response.headers.get("Access-Control-Allow-Credentials") is not None:
            failures.append(f"allowed origin exposes credentials header: {origin}")
        if response.headers.get("Access-Control-Allow-Origin") == "*":
            failures.append(f"allowed origin returned wildcard CORS: {origin}")

    preflight = _preflight(client, "http://localhost:5173")
    if preflight.status_code != 200:
        failures.append(f"allowed preflight failed: {preflight.status_code}")
    if preflight.headers.get("Access-Control-Allow-Origin") != "http://localhost:5173":
        failures.append("allowed preflight missing exact origin")
    if preflight.headers.get("Access-Control-Allow-Methods") != "GET, POST":
        failures.append("allowed preflight method list drifted")
    if "Authorization" not in preflight.headers.get("Access-Control-Allow-Headers", ""):
        failures.append("allowed preflight missing Authorization header")
    if "Content-Type" not in preflight.headers.get("Access-Control-Allow-Headers", ""):
        failures.append("allowed preflight missing Content-Type header")
    if "X-UAA-Idempotency-Key" not in preflight.headers.get("Access-Control-Allow-Headers", ""):
        failures.append("allowed preflight missing X-UAA-Idempotency-Key header")
    if "X-UAA-Idempotency-Ref" not in preflight.headers.get("Access-Control-Allow-Headers", ""):
        failures.append("allowed preflight missing X-UAA-Idempotency-Ref header")
    for header_name in [
        "X-UAA-Control-Center-Mutation-Binding",
        "X-UAA-Expected-Backend-Revision-Ref",
        "X-UAA-Expected-Backend-Instance-Ref",
        "X-UAA-Expected-Backend-Truth-Ref",
    ]:
        if header_name not in preflight.headers.get(
            "Access-Control-Allow-Headers",
            "",
        ):
            failures.append(
                f"allowed preflight missing {header_name} header"
            )
    expose_headers = client.get("/health", headers={"Origin": "http://localhost:5173"}).headers.get(
        "Access-Control-Expose-Headers", ""
    )
    for header_name in [
        "Retry-After",
        "X-UAA-Backend-Instance-Ref",
        "X-UAA-Backend-Revision-Ref",
        "X-UAA-Rate-Limit-Policy",
        "X-UAA-Security-Headers-Policy",
    ]:
        if header_name not in expose_headers:
            failures.append(f"allowed response missing exposed header {header_name}")
    if preflight.headers.get("Access-Control-Allow-Credentials") is not None:
        failures.append("allowed preflight exposes credentials header")
    for name, value in FASTAPI_SECURITY_HEADERS.items():
        if preflight.headers.get(name) != value:
            failures.append(f"allowed preflight missing security header {name}")

    for origin in [
        "https://example.com",
        "http://localhost:9999",
        "http://192.168.1.2:5173",
        "null",
    ]:
        response = client.get("/health", headers={"Origin": origin})
        if "Access-Control-Allow-Origin" in response.headers:
            failures.append(f"blocked origin received CORS allow header: {origin}")
        rejected = _preflight(client, origin)
        if rejected.status_code != 400:
            failures.append(f"blocked preflight was not rejected: {origin}")
        if "Access-Control-Allow-Origin" in rejected.headers:
            failures.append(f"blocked preflight received CORS allow header: {origin}")

    manifest = context.manifest
    append_expected_route_count(failures, manifest)
    if "explicit_loopback_cors_allowlist" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing explicit_loopback_cors_allowlist")
    for blocked in [
        "cors_as_authentication",
        "cors_credentials",
        "cors_wildcard_origins",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(failures, [
        CONTRACT_DOC,
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "README.md",
        "VERSION.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ], FORBIDDEN_CLAIMS)

    return failures


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
