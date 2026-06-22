#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.cors import (  # noqa: E402
    CONTROL_CENTER_LOOPBACK_CORS_HEADERS,
    CONTROL_CENTER_LOOPBACK_CORS_METHODS,
    CONTROL_CENTER_LOOPBACK_CORS_ORIGINS,
    LOOPBACK_CORS_POLICY_REF,
)
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.api.security_headers import FASTAPI_SECURITY_HEADERS  # noqa: E402


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
        "wildcard CORS remains denied",
        "CORS is browser hardening, not authentication",
        "UAA-P1-083",
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
        "UAA-P1-083 through UAA-P1-086",
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _compact(path: str) -> str:
    return " ".join(_read(path).lower().split())


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
        "allow_credentials": False,
        "wildcard_allowed": False,
        "cors_is_auth": False,
    }


def _preflight(client: TestClient, origin: str, method: str = "POST"):
    return client.options(
        "/contracts/validate",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )


def main() -> int:
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

    client = TestClient(app)
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

    manifest = build_api_manifest(app).model_dump(mode="json")
    if manifest["route_count"] != 112:
        failures.append(f"route count drifted: {manifest['route_count']}")
    if "explicit_loopback_cors_allowlist" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing explicit_loopback_cors_allowlist")
    for blocked in [
        "cors_as_authentication",
        "cors_credentials",
        "cors_wildcard_origins",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    for doc_path, snippets in REQUIRED_DOC_SNIPPETS.items():
        compact = _compact(doc_path)
        for snippet in snippets:
            if " ".join(snippet.lower().split()) not in compact:
                failures.append(f"{doc_path} missing '{snippet}'")
    for scan_path in [
        CONTRACT_DOC,
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "README.md",
        "VERSION.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ]:
        if not (ROOT / scan_path).exists():
            continue
        compact = _compact(scan_path)
        for forbidden in FORBIDDEN_CLAIMS:
            if forbidden in compact:
                failures.append(f"{scan_path} contains forbidden claim '{forbidden}'")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("UAA-P1-082 loopback CORS verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
