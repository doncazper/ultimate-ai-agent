from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .repo import load_json


ROUTE_FIXTURE_PATH = "tests/fixtures/api_route_inventory_133.json"
ROUTE_FIXTURE_SCHEMA_VERSION = "uaa-api-route-inventory.v4"
EXPECTED_ROUTE_COUNT = 211
EXPECTED_OPENAPI_PATH_COUNT = 210
EXPECTED_AUTH_POSTURE_SUMMARY = {
    "public_metadata_no_auth": 3,
    "protected_local_bearer_required": 208,
}
EXPECTED_APPROVAL_POSTURE_SUMMARY = {
    "not_required_for_route_classification": 169,
    "required_before_mutation_authority": 42,
}
EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY = {
    "not_required_for_route_classification": 169,
    "required_before_mutation_authority": 42,
}
EXPECTED_RATE_LIMIT_POSTURE_SUMMARY = {
    "not_targeted_for_route": 147,
    "targeted_local_fixed_window": 64,
}
EXPECTED_MUTATING_ROUTE_COUNT = EXPECTED_APPROVAL_POSTURE_SUMMARY[
    "required_before_mutation_authority"
]
EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT = EXPECTED_RATE_LIMIT_POSTURE_SUMMARY[
    "targeted_local_fixed_window"
]
EXPECTED_CONTROL_CENTER_ROUTE_COUNT = 88
EXPECTED_MUTATING_ROUTES = {
    ("POST", "/control-center/actions/{action_id}/approve"),
    ("POST", "/control-center/actions/{action_id}/defer"),
    ("POST", "/control-center/actions/{action_id}/edit"),
    ("POST", "/control-center/actions/{action_id}/local-task/commit"),
    ("POST", "/control-center/actions/{action_id}/reject"),
    ("POST", "/control-center/chat/turns"),
    ("POST", "/control-center/chat/turns/{turn_ref}/handoff"),
    ("POST", "/control-center/crm/local-mutations"),
    ("POST", "/control-center/memory/context-packs/{context_pack_ref}/action-proposal"),
    ("POST", "/control-center/memory/feedback"),
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"),
    ("POST", "/control-center/memory/review/{candidate_ref}/correct"),
    ("POST", "/control-center/memory/review/{candidate_ref}/defer"),
    ("POST", "/control-center/memory/review/{candidate_ref}/forget-request"),
    ("POST", "/control-center/memory/review/{candidate_ref}/merge"),
    ("POST", "/control-center/memory/review/{candidate_ref}/reject"),
    ("POST", "/control-center/memory/review/{candidate_ref}/supersede"),
    ("POST", "/control-center/memory/review/manual-candidate"),
    ("POST", "/control-center/providers/credentials/validate"),
    ("POST", "/control-center/providers/exact-approved-lanes/tiny"),
    ("POST", "/control-center/providers/router/dry-run"),
    ("POST", "/control-center/today/action-envelope"),
    ("POST", "/control-center/work-board/reorder"),
    ("POST", "/files/review/approvals/capture"),
    ("POST", "/integrations/mattermost/events/message"),
    ("POST", "/integrations/mattermost/roles/bind"),
    ("POST", "/integrations/mattermost/roles/unbind"),
    ("POST", "/api/runtime/command/run"),
    ("POST", "/api/runtime/invocations"),
    ("POST", "/api/runtime/local-model/call"),
    ("POST", "/api/runtime/invocations/{id}/approve"),
    ("POST", "/api/runtime/invocations/{id}/execute"),
    ("POST", "/api/runtime/safe-disable"),
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
EXPECTED_RATE_LIMIT_GROUPS = {
    "action_decision",
    "action_preview_proposal",
    "chat_durable_receipt",
    "local_model_validation",
    "memory_context_pack_action_proposal",
    "memory_feedback",
    "memory_review_decision",
    "model_chat",
    "provider_credential_validation",
    "provider_exact_approved_lane",
    "provider_router_dry_run",
    "governed_runtime_pilot",
    "task_decomposition",
    "today_to_action_envelope",
    "web_evidence_product_slice",
}
ROUTE_PROJECTION_FIELDS = (
    "path",
    "method",
    "operation_id",
    "tags",
    "summary",
    "side_effect_class",
    "route_classification",
    "auth_posture",
    "approval_posture",
    "idempotency_required",
    "idempotency_posture",
    "idempotency_policy_ref",
    "rate_limit_targeted",
    "rate_limit_posture",
    "rate_limit_policy_ref",
    "rate_limit_group",
)


def route_key(route: dict[str, Any]) -> tuple[str, str]:
    return (route["method"], route["path"])


def route_index(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {route_key(route): route for route in manifest["routes"]}


def projected_routes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        {field: route[field] for field in ROUTE_PROJECTION_FIELDS}
        for route in manifest["routes"]
    ]
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def route_fixture(path: str | Path = ROUTE_FIXTURE_PATH) -> dict[str, Any]:
    return load_json(path)


def classification_counter(manifest: dict[str, Any]) -> Counter[str]:
    return Counter(route.get("route_classification") for route in manifest["routes"])


def side_effect_counter(manifest: dict[str, Any]) -> Counter[str]:
    return Counter(route.get("side_effect_class") for route in manifest["routes"])


def append_expected_route_count(failures: list[str], manifest: dict[str, Any]) -> None:
    if manifest["route_count"] != EXPECTED_ROUTE_COUNT:
        failures.append(f"/api/manifest route_count changed: {manifest['route_count']}")


def append_route_fixture_mismatches(
    failures: list[str],
    manifest: dict[str, Any],
    *,
    label: str = "route inventory fixture",
) -> None:
    fixture = route_fixture()
    if fixture.get("schema_version") != ROUTE_FIXTURE_SCHEMA_VERSION:
        failures.append(f"{label} schema_version is stale")
    if fixture.get("routes") != projected_routes(manifest):
        failures.append(f"{label} does not match live manifest")
    for key in [
        "route_classification_vocabulary",
        "route_classification_summary",
        "route_auth_posture_summary",
        "route_approval_posture_summary",
        "route_idempotency_posture_summary",
        "idempotency_audit_policy_ref",
        "route_rate_limit_posture_summary",
        "rate_limit_policy_ref",
    ]:
        if fixture.get(key) != manifest.get(key):
            failures.append(f"{label} {key} is stale")


def expected_summary_total(summary: dict[str, int]) -> int:
    return sum(summary.values())
