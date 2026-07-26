#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.local_auth import (  # noqa: E402
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_AUTH_ENABLED_ENV,
    LOCAL_API_BEARER_ENV,
    LOCAL_API_BEARER_FILE_ENV,
    MAX_LOCAL_API_BEARER_FILE_BYTES,
    local_api_auth_policy_payload,
)
from ultimate_ai_agent.core.mattermost.api_safety import (  # noqa: E402
    MATTERMOST_BRIDGE_BEARER_ENV,
    MATTERMOST_BRIDGE_ENV,
)
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


CONTRACT_DOC = "docs/api/UAA_P1_083_LOCAL_BEARER_SESSION_GATE.md"
SCHEMA_DOC = "docs/schemas/api_local_auth_gate.schema.json"
LOCAL_TEST_BEARER = "p1-083-verifier-local-bearer"
MATTERMOST_TEST_BEARER = "p1-083-mattermost-local-bearer"
PUBLIC_PATHS = ["/health", "/version", "/api/manifest", "/openapi.json"]
PROTECTED_PATHS = [
    ("GET", "/control-center/routes", None),
    ("GET", "/control-center/today/summary", None),
    ("GET", "/observability/session-events", None),
    ("POST", "/files/tree/preview", {"root_ref": "local_dev_workspace"}),
    ("POST", "/web-evidence/request", {"url": "https://example.com"}),
]
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "auth:p1-083:local-protected-routes:v1",
        "fails closed by default",
        "UAA_API_LOCAL_BEARER",
        "UAA_LOCAL_RUNTIME_SECRET_FILE",
        "4096 bytes",
        "UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY",
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
        "No enterprise auth",
        "No production authority",
        "CORS remains browser hardening, not auth",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-083 adds a simple local bearer gate",
        "not enterprise auth, multi-user auth, OAuth, roles, or a password flow",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-083 implements local protected-route bearer gate posture",
    ],
}
FORBIDDEN_CLAIMS = [
    "enterprise auth is implemented",
    "oauth is implemented",
    "password flow is implemented",
    "production auth is implemented",
    "public beta is ready",
    "public release ready",
    "cors is auth",
]
SUCCESS_MESSAGE = "UAA-P1-083 local auth gate verification passed."


def _read(path: str) -> str:
    return read_text(path)


def _request(client: Any, method: str, path: str, **kwargs: Any):
    if method == "GET":
        return client.get(path, **kwargs)
    if method == "POST":
        return client.post(path, **kwargs)
    raise AssertionError(f"unsupported method: {method}")


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []

    schema = json.loads(_read(SCHEMA_DOC))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(local_api_auth_policy_payload()),
        key=lambda error: error.path,
    )
    for error in errors:
        failures.append(f"api local auth gate schema error: {error.message}")

    client = context.client
    env = {
        LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "",
        LOCAL_API_AUTH_ENABLED_ENV: "1",
        LOCAL_API_BEARER_ENV: LOCAL_TEST_BEARER,
    }
    with patch.dict(os.environ, env, clear=False):
        for path in PUBLIC_PATHS:
            response = client.get(path)
            if response.status_code != 200:
                failures.append(f"public metadata path was gated: {path} -> {response.status_code}")

        for method, path, payload in PROTECTED_PATHS:
            kwargs = {"json": payload} if payload is not None else {}
            missing = _request(client, method, path, **kwargs)
            wrong = _request(
                client,
                method,
                path,
                headers={"Authorization": "Bearer wrong-local-bearer"},
                **kwargs,
            )
            allowed = _request(
                client,
                method,
                path,
                headers={"Authorization": f"Bearer {LOCAL_TEST_BEARER}"},
                **kwargs,
            )
            if missing.status_code != 401:
                failures.append(f"{method} {path} without bearer returned {missing.status_code}")
            if wrong.status_code != 401:
                failures.append(f"{method} {path} with wrong bearer returned {wrong.status_code}")
            if "wrong-local-bearer" in wrong.text:
                failures.append(f"{method} {path} echoed wrong bearer material")
            if allowed.status_code == 401:
                failures.append(f"{method} {path} rejected configured local bearer")
            if missing.headers.get("X-Content-Type-Options") != "nosniff":
                failures.append(f"{method} {path} auth failure missing security headers")

        preflight = client.options(
            "/contracts/validate",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type, authorization",
            },
        )
        if preflight.status_code != 200:
            failures.append(f"CORS preflight was blocked by local auth gate: {preflight.status_code}")
        if "Authorization" not in preflight.headers.get("Access-Control-Allow-Headers", ""):
            failures.append("CORS preflight missing Authorization header for local bearer")
        if preflight.headers.get("Access-Control-Allow-Credentials") is not None:
            failures.append("CORS preflight exposed credentials after P1-083")

    route_specific_env = {
        LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "",
        LOCAL_API_BEARER_ENV: LOCAL_TEST_BEARER,
        MATTERMOST_BRIDGE_ENV: "1",
        MATTERMOST_BRIDGE_BEARER_ENV: MATTERMOST_TEST_BEARER,
    }
    with patch.dict(os.environ, route_specific_env, clear=False):
        response = client.get(
            "/integrations/mattermost/roles/catalog",
            headers={"Authorization": f"Bearer {MATTERMOST_TEST_BEARER}"},
        )
        if response.status_code != 200:
            failures.append("route-specific local bearer was double-gated by P1-083")
        if MATTERMOST_TEST_BEARER in response.text:
            failures.append("route-specific local bearer value was echoed")

    with patch.dict(
        os.environ,
        {
            LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "",
            LOCAL_API_AUTH_ENABLED_ENV: "1",
        },
        clear=False,
    ):
        os.environ.pop(LOCAL_API_BEARER_ENV, None)
        response = client.get("/control-center/routes")
        if response.status_code != 503:
            failures.append("enabled local auth gate did not fail closed without bearer")
        if LOCAL_API_BEARER_ENV in response.text:
            failures.append("local auth failure echoed bearer env name")

    with patch.dict(
        os.environ,
        {
            LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "",
        },
        clear=False,
    ):
        os.environ.pop(LOCAL_API_AUTH_ENABLED_ENV, None)
        os.environ.pop(LOCAL_API_BEARER_ENV, None)
        response = client.get("/control-center/routes")
        if response.status_code != 503:
            failures.append("local auth gate did not fail closed by default without bearer")

    with patch.dict(
        os.environ,
        {
            LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "1",
        },
        clear=False,
    ):
        os.environ.pop(LOCAL_API_AUTH_ENABLED_ENV, None)
        os.environ.pop(LOCAL_API_BEARER_ENV, None)
        response = client.get("/control-center/routes")
        if response.status_code != 200:
            failures.append("explicit dev-only local auth bypass did not keep local harness open")

    manifest = context.manifest
    if "local_protected_route_bearer_gate" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing local_protected_route_bearer_gate")
    if "local_protected_route_fail_closed_by_default" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing local_protected_route_fail_closed_by_default")
    auth_policy = manifest.get("local_auth_policy", {})
    if auth_policy.get("fail_closed_by_default") is not True:
        failures.append("/api/manifest missing fail-closed local auth policy truth")
    if auth_policy.get("dev_only_bypass_env") != LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV:
        failures.append("/api/manifest missing explicit dev-only bypass env")
    if auth_policy.get("bearer_file_env") != LOCAL_API_BEARER_FILE_ENV:
        failures.append("/api/manifest missing local-runtime bearer file env")
    if auth_policy.get("maximum_bearer_file_bytes") != MAX_LOCAL_API_BEARER_FILE_BYTES:
        failures.append("/api/manifest missing bounded bearer file byte limit")
    if auth_policy.get("dev_only_bypass_production_authority") is not False:
        failures.append("/api/manifest overclaims dev-only bypass production authority")
    for blocked in [
        "local_protected_route_gate_as_enterprise_auth",
        "local_protected_route_gate_as_multi_user_auth",
        "local_protected_route_gate_as_oauth",
        "local_protected_route_gate_as_password_flow",
        "local_protected_route_gate_as_production_authority",
        "local_protected_route_dev_only_bypass_as_production_authority",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")
    for route in manifest["routes"]:
        expected = route["route_classification"] != "public_metadata"
        if route["protected_route"] is not expected:
            failures.append(f"{route['method']} {route['path']} protected_route mismatch")

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
