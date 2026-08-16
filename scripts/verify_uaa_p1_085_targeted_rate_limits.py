#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tests.m7_helpers import local_profile, policy, route_request  # noqa: E402
from ultimate_ai_agent.api.local_auth import (  # noqa: E402
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.rate_limits import (  # noqa: E402
    API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
    API_TARGETED_RATE_LIMIT_POLICY_REF,
    API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV,
    api_rate_limit_policy_payload,
    reset_api_rate_limit_state,
)
from scripts.verification.api_routes import (  # noqa: E402
    EXPECTED_RATE_LIMIT_GROUPS,
    EXPECTED_RATE_LIMIT_POSTURE_SUMMARY,
    EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT,
    append_expected_route_count,
    append_route_fixture_mismatches,
    route_fixture,
)
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
)


CONTRACT_DOC = "docs/api/UAA_P1_085_TARGETED_RATE_LIMITS.md"
POLICY_SCHEMA = "docs/schemas/api_targeted_rate_limits.schema.json"
ROUTE_SCHEMA = "docs/schemas/api_route_classification.schema.json"
ROUTE_FIXTURE = "tests/fixtures/api_route_inventory_133.json"
IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:p1-085-verifier"}
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
    ],
}
FORBIDDEN_CLAIMS = [
    "rate limits are auth",
    "distributed quota is implemented",
    "production authority is granted",
    "public beta is ready",
    "public release ready",
]
SUCCESS_MESSAGE = "UAA-P1-085 targeted local rate-limit verification passed."


def _model_route_payload(prompt_summary: str = "safe route summary") -> dict:
    payload = route_request(
        profiles=[local_profile()],
        routing_policy=policy(prefer_local=True),
    ).model_dump(mode="json")
    payload["prompt_summary"] = prompt_summary
    return payload


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []
    manifest = context.manifest
    append_expected_route_count(failures, manifest)

    policy_schema = load_json(POLICY_SCHEMA)
    policy_payload = api_rate_limit_policy_payload(
        targeted_route_count=EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT
    )
    for error in sorted(
        Draft202012Validator(policy_schema).iter_errors(policy_payload),
        key=lambda error: error.path,
    ):
        failures.append(f"api targeted rate-limit policy schema error: {error.message}")

    route_fixture_payload = route_fixture(ROUTE_FIXTURE)
    route_schema = load_json(ROUTE_SCHEMA)
    for error in sorted(
        Draft202012Validator(route_schema).iter_errors(route_fixture_payload),
        key=lambda error: error.path,
    ):
        failures.append(f"route inventory schema error: {error.message}")
    append_route_fixture_mismatches(
        failures,
        manifest,
        label="route inventory fixture",
    )

    if manifest.get("rate_limit_policy_ref") != API_TARGETED_RATE_LIMIT_POLICY_REF:
        failures.append("/api/manifest missing P1-085 rate-limit policy ref")
    if manifest.get("route_rate_limit_posture_summary") != EXPECTED_RATE_LIMIT_POSTURE_SUMMARY:
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

    routes_by_key = context.routes_by_key
    targeted_routes = {
        key for key, route in routes_by_key.items() if route["rate_limit_targeted"] is True
    }
    if len(targeted_routes) != EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT:
        failures.append(f"targeted rate-limit route count drifted: {len(targeted_routes)}")
    targeted_groups = {
        route["rate_limit_group"]
        for route in routes_by_key.values()
        if route["rate_limit_targeted"] is True
    }
    if targeted_groups != EXPECTED_RATE_LIMIT_GROUPS:
        failures.append(f"targeted rate-limit groups drifted: {sorted(targeted_groups)}")
    for key in [
        ("POST", "/models/route/preview"),
        ("POST", "/control-center/actions/preview"),
        ("POST", "/control-center/today/action-envelope"),
        ("POST", "/control-center/chat/turns"),
        ("POST", "/control-center/chat/turns/{turn_ref}/handoff"),
        ("POST", "/control-center/memory/review/{candidate_ref}/accept"),
        ("POST", "/control-center/memory/review/{candidate_ref}/correct"),
        ("POST", "/control-center/memory/review/{candidate_ref}/reject"),
        ("POST", "/control-center/memory/feedback"),
        ("POST", "/control-center/actions/{action_id}/reject"),
        ("POST", "/control-center/actions/{action_id}/cancel"),
        ("POST", "/control-center/actions/{action_id}/local-task/commit"),
        ("POST", "/api/runtime/invocations"),
        ("POST", "/api/runtime/invocations/{id}/approve"),
        ("POST", "/api/runtime/invocations/{id}/execute"),
        ("POST", "/api/runtime/safe-disable"),
        ("POST", "/task-decomposition/run"),
        ("POST", "/v1/chat/completions"),
        ("POST", "/extensions/disabled-install-records"),
        ("POST", "/extensions/disabled-install-records/rollback"),
    ]:
        route = routes_by_key[key]
        if route["rate_limit_posture"] != "targeted_local_fixed_window":
            failures.append(f"{key[0]} {key[1]} missing targeted rate-limit posture")
        if route["rate_limit_policy_ref"] != API_TARGETED_RATE_LIMIT_POLICY_REF:
            failures.append(f"{key[0]} {key[1]} rate-limit policy ref drifted")

    client = context.client
    env = {
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV: "1",
        API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV: "60",
        LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV: "",
        LOCAL_API_BEARER_ENV: "p1-085-local-bearer",
    }
    auth_headers = {"Authorization": "Bearer p1-085-local-bearer"}
    with patch.dict("os.environ", env, clear=False):
        reset_api_rate_limit_state()
        first = client.post(
            "/models/route/preview",
            headers=auth_headers,
            json=_model_route_payload("raw prompt should not echo"),
        )
        second = client.post(
            "/models/route/preview",
            headers=auth_headers,
            json=_model_route_payload("raw prompt should not echo"),
        )
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
        origin_headers = {**auth_headers, "Origin": "http://localhost:5173"}
        client.post(
            "/models/route/preview",
            headers=origin_headers,
            json=_model_route_payload(),
        )
        cors_limited = client.post(
            "/models/route/preview",
            headers=origin_headers,
            json=_model_route_payload(),
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
        missing_one = client.post(
            "/task-decomposition/run",
            json={"raw_request": "safe summary"},
            headers=auth_headers,
        )
        missing_two = client.post(
            "/task-decomposition/run",
            json={"raw_request": "safe summary"},
            headers=auth_headers,
        )
        if missing_one.status_code != 428 or missing_two.status_code != 428:
            failures.append("rate limit masked missing idempotency on mutating route")

        reset_api_rate_limit_state()
        auth_one = client.post("/models/route/preview", json=_model_route_payload())
        auth_two = client.post("/models/route/preview", json=_model_route_payload())
        if auth_one.status_code != 401 or auth_two.status_code != 401:
            failures.append("rate limit masked local auth failure")

        reset_api_rate_limit_state()
        valid_one = client.post(
            "/task-decomposition/run",
            headers={**auth_headers, **IDEMPOTENCY_HEADERS},
            json={"raw_request": "safe summary"},
        )
        valid_two = client.post(
            "/task-decomposition/run",
            headers={**auth_headers, **IDEMPOTENCY_HEADERS},
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
