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
from ultimate_ai_agent.api.idempotency import (  # noqa: E402
    API_IDEMPOTENCY_AUDIT_POLICY_REF,
    api_idempotency_audit_policy_payload,
)
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402


CONTRACT_DOC = "docs/api/UAA_P1_084_MUTATING_ROUTE_IDEMPOTENCY_AUDIT.md"
POLICY_SCHEMA = "docs/schemas/api_mutating_route_idempotency_audit.schema.json"
ROUTE_SCHEMA = "docs/schemas/api_route_classification.schema.json"
ROUTE_FIXTURE = "tests/fixtures/api_route_inventory_112.json"
IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:p1-084-verifier"}
MUTATING_ROUTES = {
    ("POST", "/files/review/approvals/capture"),
    ("POST", "/integrations/mattermost/events/message"),
    ("POST", "/integrations/mattermost/roles/bind"),
    ("POST", "/integrations/mattermost/roles/unbind"),
    ("POST", "/kernel/tasks/run"),
    ("POST", "/task-decomposition/approval-requests"),
    ("POST", "/task-decomposition/approvals/grants/capture"),
    ("POST", "/task-decomposition/approvals/revoke"),
    ("POST", "/task-decomposition/capabilities/register"),
    ("POST", "/task-decomposition/examples/init"),
    ("POST", "/task-decomposition/plans/execute"),
    ("POST", "/task-decomposition/run"),
    ("POST", "/v1/chat/completions"),
}
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
        "UAA-P1-085 implements targeted local fixed-window rate-limit posture",
        "Future UAA-P1-086",
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _load_json(path: str) -> Any:
    return json.loads(_read(path))


def _compact(path: str) -> str:
    return " ".join(_read(path).lower().split())


def _post(
    client: TestClient,
    path: str,
    headers: dict[str, str] | None = None,
    json_body: dict[str, str] | None = None,
):
    return client.post(
        path,
        headers=headers or {},
        json=json_body or {"unsafe": "raw request should not echo"},
    )


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
    mutating_count = manifest["route_classification_summary"]["mutating_requires_authority"]

    policy_schema = _load_json(POLICY_SCHEMA)
    policy_payload = api_idempotency_audit_policy_payload(mutating_route_count=mutating_count)
    for error in sorted(
        Draft202012Validator(policy_schema).iter_errors(policy_payload),
        key=lambda error: error.path,
    ):
        failures.append(f"api mutating idempotency policy schema error: {error.message}")

    route_fixture = _load_json(ROUTE_FIXTURE)
    route_schema = _load_json(ROUTE_SCHEMA)
    for error in sorted(
        Draft202012Validator(route_schema).iter_errors(route_fixture),
        key=lambda error: error.path,
    ):
        failures.append(f"route inventory schema error: {error.message}")
    if route_fixture.get("routes") != _fixture_routes_from_manifest(manifest):
        failures.append("route inventory fixture does not match live manifest idempotency posture")

    if manifest.get("idempotency_audit_policy_ref") != API_IDEMPOTENCY_AUDIT_POLICY_REF:
        failures.append("/api/manifest missing P1-084 idempotency audit policy ref")
    if manifest.get("route_idempotency_posture_summary") != {
        "not_required_for_route_classification": 99,
        "required_before_mutation_authority": 13,
    }:
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

    route_index = {(route["method"], route["path"]): route for route in manifest["routes"]}
    required_routes = {
        key for key, route in route_index.items() if route["idempotency_required"] is True
    }
    if required_routes != MUTATING_ROUTES:
        failures.append(f"mutating idempotency route set drifted: {sorted(required_routes)}")
    for key in MUTATING_ROUTES:
        route = route_index[key]
        if route["route_classification"] != "mutating_requires_authority":
            failures.append(f"{key[0]} {key[1]} classification is not mutating")
        if route["idempotency_posture"] != "required_before_mutation_authority":
            failures.append(f"{key[0]} {key[1]} idempotency posture is not required")
        if route["idempotency_policy_ref"] != API_IDEMPOTENCY_AUDIT_POLICY_REF:
            failures.append(f"{key[0]} {key[1]} idempotency policy ref drifted")

    client = TestClient(app)
    for _method, path in sorted(MUTATING_ROUTES):
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
    print("UAA-P1-084 mutating-route idempotency verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
