#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.local_auth import LOCAL_API_BEARER_ENV  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.api.rate_limits import (  # noqa: E402
    API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
    API_TARGETED_RATE_LIMIT_POLICY_REF,
    API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV,
    api_rate_limit_policy_payload,
    reset_api_rate_limit_state,
)


CONTRACT_DOC = "docs/api/UAA_P1_085_TARGETED_RATE_LIMITS.md"
POLICY_SCHEMA = "docs/schemas/api_targeted_rate_limits.schema.json"
ROUTE_SCHEMA = "docs/schemas/api_route_classification.schema.json"
ROUTE_FIXTURE = "tests/fixtures/api_route_inventory_112.json"
IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:p1-085-verifier"}
EXPECTED_RATE_LIMIT_SUMMARY = {
    "not_targeted_for_route": 78,
    "targeted_local_fixed_window": 34,
}
EXPECTED_GROUPS = {
    "action_preview_proposal",
    "local_model_validation",
    "model_chat",
    "task_decomposition",
}
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "rate-limit:p1-085:targeted-local:v1",
        "local in-memory fixed-window",
        "Retry-After",
        "No auth",
        "No production authority",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-085 adds targeted local fixed-window rate limits",
        "does not add auth, distributed quota, dependencies, billing, or production authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-085 implements targeted local fixed-window rate-limit posture",
        "Future UAA-P1-086",
    ],
}
FORBIDDEN_CLAIMS = [
    "rate limits are auth",
    "distributed quota is implemented",
    "production authority is granted",
    "public beta is ready",
    "public release ready",
]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _load_json(path: str) -> Any:
    return json.loads(_read(path))


def _compact(path: str) -> str:
    return " ".join(_read(path).lower().split())


def _fixture_routes_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        {
            "path": route["path"],
            "method": route["method"],
            "operation_id": route["operation_id"],
            "tags": route["tags"],
            "summary": route["summary"],
            "side_effect_class": route["side_effect_class"],
            "route_classification": route["route_classification"],
            "idempotency_required": route["idempotency_required"],
            "idempotency_posture": route["idempotency_posture"],
            "idempotency_policy_ref": route["idempotency_policy_ref"],
            "rate_limit_targeted": route["rate_limit_targeted"],
            "rate_limit_posture": route["rate_limit_posture"],
            "rate_limit_policy_ref": route["rate_limit_policy_ref"],
            "rate_limit_group": route["rate_limit_group"],
        }
        for route in manifest["routes"]
    ]
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def main() -> int:
    failures: list[str] = []
    manifest = build_api_manifest(app).model_dump(mode="json")

    policy_schema = _load_json(POLICY_SCHEMA)
    policy_payload = api_rate_limit_policy_payload(targeted_route_count=34)
    for error in sorted(
        Draft202012Validator(policy_schema).iter_errors(policy_payload),
        key=lambda error: error.path,
    ):
        failures.append(f"api targeted rate-limit policy schema error: {error.message}")

    route_fixture = _load_json(ROUTE_FIXTURE)
    route_schema = _load_json(ROUTE_SCHEMA)
    for error in sorted(
        Draft202012Validator(route_schema).iter_errors(route_fixture),
        key=lambda error: error.path,
    ):
        failures.append(f"route inventory schema error: {error.message}")
    if route_fixture.get("schema_version") != "uaa-api-route-inventory.v3":
        failures.append("route inventory fixture schema_version is not v3")
    if route_fixture.get("routes") != _fixture_routes_from_manifest(manifest):
        failures.append("route inventory fixture does not match live manifest rate-limit posture")

    if manifest.get("rate_limit_policy_ref") != API_TARGETED_RATE_LIMIT_POLICY_REF:
        failures.append("/api/manifest missing P1-085 rate-limit policy ref")
    if manifest.get("route_rate_limit_posture_summary") != EXPECTED_RATE_LIMIT_SUMMARY:
        failures.append("/api/manifest route_rate_limit_posture_summary drifted")
    if "targeted_local_rate_limits" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing targeted_local_rate_limits")
    for blocked in [
        "targeted_rate_limits_as_auth",
        "targeted_rate_limits_as_distributed_quota",
        "targeted_rate_limits_as_production_authority",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    route_index = {(route["method"], route["path"]): route for route in manifest["routes"]}
    targeted_routes = {
        key for key, route in route_index.items() if route["rate_limit_targeted"] is True
    }
    if len(targeted_routes) != 34:
        failures.append(f"targeted rate-limit route count drifted: {len(targeted_routes)}")
    targeted_groups = {
        route["rate_limit_group"]
        for route in route_index.values()
        if route["rate_limit_targeted"] is True
    }
    if targeted_groups != EXPECTED_GROUPS:
        failures.append(f"targeted rate-limit groups drifted: {sorted(targeted_groups)}")
    for key in [
        ("POST", "/models/route/preview"),
        ("POST", "/control-center/actions/preview"),
        ("POST", "/task-decomposition/run"),
        ("POST", "/v1/chat/completions"),
    ]:
        route = route_index[key]
        if route["rate_limit_posture"] != "targeted_local_fixed_window":
            failures.append(f"{key[0]} {key[1]} missing targeted rate-limit posture")
        if route["rate_limit_policy_ref"] != API_TARGETED_RATE_LIMIT_POLICY_REF:
            failures.append(f"{key[0]} {key[1]} rate-limit policy ref drifted")

    client = TestClient(app)
    env = {
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV: "1",
        API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV: "60",
    }
    with patch.dict("os.environ", env, clear=False):
        reset_api_rate_limit_state()
        first = client.post("/models/route/preview", json={"unsafe": "raw prompt should not echo"})
        second = client.post("/models/route/preview", json={"unsafe": "raw prompt should not echo"})
        if first.status_code == 429:
            failures.append("first targeted local-model validation request was rate limited")
        if second.status_code != 429:
            failures.append(f"second targeted local-model validation request returned {second.status_code}")
        if second.headers.get("Retry-After") is None:
            failures.append("rate-limit response missing Retry-After")
        if second.headers.get("X-UAA-Rate-Limit-Policy") != API_TARGETED_RATE_LIMIT_POLICY_REF:
            failures.append("rate-limit response missing policy header")
        if second.headers.get("X-Content-Type-Options") != "nosniff":
            failures.append("rate-limit response missing security headers")
        if "raw prompt should not echo" in second.text:
            failures.append("rate-limit response echoed unsafe input")

        reset_api_rate_limit_state()
        origin_headers = {"Origin": "http://localhost:5173"}
        client.post(
            "/models/route/preview",
            headers=origin_headers,
            json={"unsafe": "safe summary"},
        )
        cors_limited = client.post(
            "/models/route/preview",
            headers=origin_headers,
            json={"unsafe": "safe summary"},
        )
        if cors_limited.status_code != 429:
            failures.append("allowed-origin targeted route did not reach 429")
        if cors_limited.headers.get("Access-Control-Allow-Origin") != "http://localhost:5173":
            failures.append("rate-limit 429 missing loopback CORS allow-origin")
        cors_limited_expose = cors_limited.headers.get("Access-Control-Expose-Headers", "")
        for header_name in ["Retry-After", "X-UAA-Rate-Limit-Policy"]:
            if header_name not in cors_limited_expose:
                failures.append(f"rate-limit 429 CORS does not expose {header_name}")

        reset_api_rate_limit_state()
        missing_one = client.post("/task-decomposition/run", json={"raw_request": "safe summary"})
        missing_two = client.post("/task-decomposition/run", json={"raw_request": "safe summary"})
        if missing_one.status_code != 428 or missing_two.status_code != 428:
            failures.append("rate limit masked missing idempotency on mutating route")

        reset_api_rate_limit_state()
        with patch.dict("os.environ", {LOCAL_API_BEARER_ENV: "p1-085-local-bearer"}, clear=False):
            auth_one = client.post("/models/route/preview", json={"unsafe": "safe summary"})
            auth_two = client.post("/models/route/preview", json={"unsafe": "safe summary"})
        if auth_one.status_code != 401 or auth_two.status_code != 401:
            failures.append("rate limit masked local auth failure")

        reset_api_rate_limit_state()
        valid_one = client.post(
            "/task-decomposition/run",
            headers=IDEMPOTENCY_HEADERS,
            json={"raw_request": "safe summary"},
        )
        valid_two = client.post(
            "/task-decomposition/run",
            headers=IDEMPOTENCY_HEADERS,
            json={"raw_request": "safe summary"},
        )
        if valid_one.status_code != 403:
            failures.append("valid idempotency did not reach existing task-decomposition authority check")
        if valid_two.status_code != 429:
            failures.append("targeted task-decomposition route was not rate limited on reentry")

        reset_api_rate_limit_state()
        public_one = client.get("/health")
        public_two = client.get("/health")
        if public_one.status_code != 200 or public_two.status_code != 200:
            failures.append("public metadata route was affected by targeted rate limits")

        reset_api_rate_limit_state()
        wrong_method_one = client.post("/v1/models")
        wrong_method_two = client.post("/v1/models")
        if wrong_method_one.status_code == 429 or wrong_method_two.status_code == 429:
            failures.append("wrong method on targeted path was rate limited")

        reset_api_rate_limit_state()
        typo = client.get("/task-decomposition-typo")
        status = client.get("/task-decomposition/status")
        if typo.status_code == 429 or status.status_code == 429:
            failures.append("unregistered task-decomposition-like path consumed targeted bucket")

    cors_response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    expose_headers = cors_response.headers.get("Access-Control-Expose-Headers", "")
    for header_name in ["Retry-After", "X-UAA-Rate-Limit-Policy"]:
        if header_name not in expose_headers:
            failures.append(f"CORS expose headers missing {header_name}")

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
    print("UAA-P1-085 targeted local rate-limit verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
