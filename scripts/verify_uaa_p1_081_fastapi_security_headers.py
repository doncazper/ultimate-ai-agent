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

from ultimate_ai_agent.api.security_headers import (  # noqa: E402
    FASTAPI_SECURITY_HEADERS,
    HTTPS_ONLY_SECURITY_HEADERS,
    SECURITY_HEADERS_POLICY_REF,
)
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


CONTRACT_DOC = "docs/api/UAA_P1_081_CENTRALIZED_FASTAPI_SECURITY_HEADERS.md"
SCHEMA_DOC = "docs/schemas/api_security_headers.schema.json"
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "security-headers:p1-081:v1",
        "X-Content-Type-Options: nosniff",
        "Referrer-Policy: no-referrer",
        "X-Frame-Options: DENY",
        "Strict-Transport-Security",
        "HTTPS",
        "No auth",
        "No auth, session gate, CORS policy, idempotency enforcement, rate limits",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-081",
        "centralized FastAPI response security headers",
        "implemented API boundary hardening invariant",
        "HSTS only for actual HTTPS requests",
        "does not add auth, sessions, CORS, idempotency enforcement, rate limits, dependencies, or runtime authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-081",
        "security-header posture",
        "X-Content-Type-Options",
    ],
}
FORBIDDEN_CLAIMS = [
    "auth implemented by UAA-P1-081",
    "cors implemented by UAA-P1-081",
    "rate limits implemented by UAA-P1-081",
    "public beta is ready",
    "public release ready",
    "production ready because of security headers",
]
SUCCESS_MESSAGE = "UAA-P1-081 FastAPI security-header verification passed."


def _read(path: str) -> str:
    return read_text(path)


def _policy_payload() -> dict[str, Any]:
    return {
        "policy_ref": SECURITY_HEADERS_POLICY_REF,
        "required_headers": dict(FASTAPI_SECURITY_HEADERS),
        "hsts_https_only": True,
        "no_auth_added": True,
        "no_cors_added": True,
        "no_rate_limits_added": True,
    }


def _assert_headers(response, failures: list[str], label: str) -> None:
    for name, expected in FASTAPI_SECURITY_HEADERS.items():
        actual = response.headers.get(name)
        if actual != expected:
            failures.append(f"{label} missing {name}: {actual!r}")
    if response.headers.get("X-UAA-Security-Headers-Policy") != SECURITY_HEADERS_POLICY_REF:
        failures.append(f"{label} missing security header policy ref")
    if "access-control-allow-origin" in {key.lower() for key in response.headers}:
        failures.append(f"{label} unexpectedly emits CORS headers")


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []
    schema = json.loads(_read(SCHEMA_DOC))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(_policy_payload()),
        key=lambda error: error.path,
    )
    for error in errors:
        failures.append(f"api security header schema error: {error.message}")

    http_client = context.client
    https_client = context.https_client
    success = http_client.get("/health")
    validation_error = http_client.post(
        "/contracts/validate",
        json={"api_key": "ABCDEFGHIJKLMNOP"},
    )
    https = https_client.get("/version")

    _assert_headers(success, failures, "GET /health")
    _assert_headers(validation_error, failures, "POST /contracts/validate 422")
    _assert_headers(https, failures, "HTTPS GET /version")
    if "Strict-Transport-Security" in success.headers:
        failures.append("HTTP response unexpectedly emits HSTS")
    if https.headers.get("Strict-Transport-Security") != HTTPS_ONLY_SECURITY_HEADERS[
        "Strict-Transport-Security"
    ]:
        failures.append("HTTPS response missing Strict-Transport-Security")
    if validation_error.status_code != 422 or "ABCDEFGHIJKLMNOP" in validation_error.text:
        failures.append("validation-error response safety drifted")

    manifest = context.manifest
    append_expected_route_count(failures, manifest)
    for capability in [
        "centralized_fastapi_security_headers",
    ]:
        if capability not in manifest["capabilities_declared"]:
            failures.append(f"/api/manifest missing declared capability {capability}")
    for blocked in [
        "security_headers_as_authentication",
        "security_headers_as_cors_policy",
        "security_headers_as_rate_limits",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    app_text = _read("src/ultimate_ai_agent/api/app.py")
    if "security_headers_api_middleware" not in app_text:
        failures.append("FastAPI app missing centralized security-header middleware")

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
