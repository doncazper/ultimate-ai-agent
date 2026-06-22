#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.idempotency import (  # noqa: E402
    API_IDEMPOTENCY_AUDIT_POLICY_REF,
    api_idempotency_audit_policy_payload,
)
from scripts.verification.api_routes import (  # noqa: E402
    EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY,
    EXPECTED_MUTATING_ROUTES,
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


CONTRACT_DOC = "docs/api/UAA_P1_084_MUTATING_ROUTE_IDEMPOTENCY_AUDIT.md"
POLICY_SCHEMA = "docs/schemas/api_mutating_route_idempotency_audit.schema.json"
ROUTE_SCHEMA = "docs/schemas/api_route_classification.schema.json"
ROUTE_FIXTURE = "tests/fixtures/api_route_inventory_126.json"
IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:p1-084-verifier"}
REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "idempotency:p1-084:mutating-routes:v1",
        "X-UAA-Idempotency-Key",
        "X-UAA-Idempotency-Ref",
        "mutating_requires_authority",
        "No durable dedupe store",
        "No production authority",
    ],
    "docs/api/openapi_contract.md": [
        "UAA-P1-084 adds a runtime boundary check",
        "does not add durable idempotency storage, replay execution, mutation authority, or production authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-084 implements mutating-route idempotency enforcement audit posture",
    ],
}
FORBIDDEN_CLAIMS = [
    "exactly-once execution is implemented",
    "durable dedupe store is implemented",
    "idempotent execution is guaranteed",
    "production authority is granted",
    "public beta is ready",
    "public release ready",
]
SUCCESS_MESSAGE = "UAA-P1-084 mutating-route idempotency verification passed."


def _post(
    client,
    path: str,
    headers: dict[str, str] | None = None,
    json_body: dict[str, str] | None = None,
):
    return client.post(
        path,
        headers=headers or {},
        json=json_body or {"unsafe": "raw request should not echo"},
    )


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []
    manifest = context.manifest
    mutating_count = manifest["route_classification_summary"]["mutating_requires_authority"]
    append_expected_route_count(failures, manifest)

    policy_schema = load_json(POLICY_SCHEMA)
    policy_payload = api_idempotency_audit_policy_payload(mutating_route_count=mutating_count)
    for error in sorted(
        Draft202012Validator(policy_schema).iter_errors(policy_payload),
        key=lambda error: error.path,
    ):
        failures.append(f"api mutating idempotency policy schema error: {error.message}")

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

    if manifest.get("idempotency_audit_policy_ref") != API_IDEMPOTENCY_AUDIT_POLICY_REF:
        failures.append("/api/manifest missing P1-084 idempotency audit policy ref")
    if manifest.get("route_idempotency_posture_summary") != EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY:
        failures.append("/api/manifest route_idempotency_posture_summary drifted")
    if "mutating_route_idempotency_audit" not in manifest["capabilities_declared"]:
        failures.append("/api/manifest missing mutating_route_idempotency_audit")
    for blocked in [
        "idempotency_audit_as_exactly_once_execution",
        "idempotency_audit_as_durable_dedupe_store",
        "idempotency_audit_as_mutation_authority",
        "idempotency_audit_as_production_authority",
    ]:
        if blocked not in manifest["capabilities_blocked"]:
            failures.append(f"/api/manifest missing blocked capability {blocked}")

    routes_by_key = context.routes_by_key
    required_routes = {
        key for key, route in routes_by_key.items() if route["idempotency_required"] is True
    }
    if required_routes != EXPECTED_MUTATING_ROUTES:
        failures.append(f"mutating idempotency route set drifted: {sorted(required_routes)}")
    for key in EXPECTED_MUTATING_ROUTES:
        route = routes_by_key[key]
        if route["route_classification"] != "mutating_requires_authority":
            failures.append(f"{key[0]} {key[1]} classification is not mutating")
        if route["idempotency_posture"] != "required_before_mutation_authority":
            failures.append(f"{key[0]} {key[1]} idempotency posture is not required")
        if route["idempotency_policy_ref"] != API_IDEMPOTENCY_AUDIT_POLICY_REF:
            failures.append(f"{key[0]} {key[1]} idempotency policy ref drifted")

    client = context.client
    for _method, path in sorted(EXPECTED_MUTATING_ROUTES):
        missing = _post(client, path)
        invalid = _post(client, path, headers={"X-UAA-Idempotency-Key": "short"})
        if missing.status_code != 428:
            failures.append(f"{path} without idempotency returned {missing.status_code}")
        if invalid.status_code != 400:
            failures.append(f"{path} with invalid idempotency returned {invalid.status_code}")
        if "raw request should not echo" in missing.text or "short" in invalid.text:
            failures.append(f"{path} idempotency failure echoed unsafe input")
        if missing.headers.get("X-Content-Type-Options") != "nosniff":
            failures.append(f"{path} idempotency failure missing security headers")

    allowed_to_handler = _post(
        client,
        "/task-decomposition/run",
        headers=IDEMPOTENCY_HEADERS,
        json_body={"raw_request": "safe summary"},
    )
    if allowed_to_handler.status_code != 403:
        failures.append("valid idempotency did not reach existing task-decomposition authority check")

    non_mutating = client.post("/files/tree/preview", json={"unsafe": "shape"})
    if non_mutating.status_code == 428:
        failures.append("local_sensitive non-mutating route required idempotency")

    preflight = client.options(
        "/contracts/validate",
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
        failures.append(f"CORS preflight for idempotency headers failed: {preflight.status_code}")
    allow_headers = preflight.headers.get("Access-Control-Allow-Headers", "")
    for header_name in ["X-UAA-Idempotency-Key", "X-UAA-Idempotency-Ref"]:
        if header_name not in allow_headers:
            failures.append(f"CORS preflight missing {header_name}")

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
