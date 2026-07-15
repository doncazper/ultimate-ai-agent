from __future__ import annotations

import hashlib
import json
from typing import Any


PUBLIC_METADATA_ROUTES = frozenset(
    {
        ("GET", "/api/manifest"),
        ("GET", "/health"),
        ("GET", "/version"),
    }
)
MUTATING_ROUTES = frozenset(
    {
        ("POST", "/api/runtime/authority-leases"),
        ("POST", "/api/runtime/authority-leases/approve-and-issue"),
        ("POST", "/api/runtime/authority-leases/revoke"),
        ("POST", "/api/runtime/authority-missions/approval-decisions"),
        ("POST", "/api/runtime/authority-missions/cancel"),
        ("POST", "/api/runtime/authority-missions/dead-letter-recovery"),
        ("POST", "/api/runtime/command/run"),
        ("POST", "/api/runtime/hermes/chat"),
        ("POST", "/api/runtime/invocations"),
        ("POST", "/api/runtime/invocations/{id}/approve"),
        ("POST", "/api/runtime/invocations/{id}/execute"),
        ("POST", "/api/runtime/local-model/call"),
        ("POST", "/api/runtime/safe-disable"),
        ("POST", "/control-center/actions/{action_id}/approve"),
        ("POST", "/control-center/actions/{action_id}/defer"),
        ("POST", "/control-center/actions/{action_id}/edit"),
        ("POST", "/control-center/actions/{action_id}/local-task/commit"),
        ("POST", "/control-center/actions/{action_id}/reject"),
        ("POST", "/control-center/chat/turns"),
        ("POST", "/control-center/chat/turns/{turn_ref}/handoff"),
        ("POST", "/control-center/crm/local-mutations"),
        ("POST", "/control-center/communications/harness/fixture-seed"),
        ("POST", "/control-center/communications/harness/reset"),
        ("POST", "/control-center/communications/harness/start"),
        ("POST", "/control-center/communications/harness/stop"),
        ("POST", "/control-center/communications/matrix/credential-auth-create"),
        ("POST", "/control-center/communications/matrix/credential-delete"),
        (
            "POST",
            "/control-center/communications/matrix/credential-store-rotate",
        ),
        ("POST", "/control-center/communications/matrix/logout"),
        ("POST", "/control-center/communications/matrix/refresh"),
        ("POST", "/control-center/communications/matrix/revoke-all"),
        ("POST", "/control-center/communications/matrix/sso-callback-consume"),
        ("POST", "/control-center/communications/matrix/sso-launch"),
        (
            "POST",
            "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        ),
        ("POST", "/control-center/memory/feedback"),
        ("POST", "/control-center/memory/review/manual-candidate"),
        ("POST", "/control-center/memory/review/{candidate_ref}/accept"),
        ("POST", "/control-center/memory/review/{candidate_ref}/correct"),
        ("POST", "/control-center/memory/review/{candidate_ref}/defer"),
        ("POST", "/control-center/memory/review/{candidate_ref}/expire"),
        ("POST", "/control-center/memory/review/{candidate_ref}/forget-request"),
        ("POST", "/control-center/memory/review/{candidate_ref}/merge"),
        ("POST", "/control-center/memory/review/{candidate_ref}/reject"),
        ("POST", "/control-center/memory/review/{candidate_ref}/supersede"),
        ("POST", "/control-center/providers/credentials/validate"),
        ("POST", "/control-center/providers/exact-approved-lanes/tiny"),
        ("POST", "/control-center/providers/router/dry-run"),
        ("POST", "/control-center/today/action-envelope"),
        ("POST", "/control-center/today/exact-action/approve"),
        ("POST", "/control-center/today/exact-action/execute"),
        ("POST", "/control-center/today/exact-action/prepare"),
        ("POST", "/control-center/today/exact-action/source-review"),
        ("POST", "/control-center/work-board/cards"),
        ("POST", "/control-center/work-board/reorder"),
        ("POST", "/control-center/work-board/tasks"),
        ("POST", "/extensions/disabled-install-records"),
        ("POST", "/extensions/disabled-install-records/rollback"),
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
)
TARGETED_RATE_LIMIT_GROUPS = frozenset(
    {
        "action_decision",
        "action_preview_proposal",
        "chat_durable_receipt",
        "communications_matrix_harness",
        "communications_matrix_session",
        "extension_install_disabled_record",
        "founder_loop_exact_action",
        "governed_runtime_pilot",
        "local_model_validation",
        "memory_context_pack_action_proposal",
        "memory_feedback",
        "memory_review_decision",
        "model_chat",
        "provider_credential_validation",
        "provider_exact_approved_lane",
        "provider_router_dry_run",
        "task_decomposition",
        "today_to_action_envelope",
        "web_evidence_product_slice",
    }
)
TARGETED_RATE_LIMIT_ROUTE_COUNT = 94
TARGETED_RATE_LIMIT_ROUTE_FINGERPRINT = (
    "11669334edb8e59f468c2d6a0e0e75ccd11bdb63cb20c095dbd09537dc1ecf09"
)


def validate_route_policy_floor(routes: list[dict[str, Any]]) -> None:
    index = {(route["method"], route["path"]): route for route in routes}
    public_routes = frozenset(
        key
        for key, route in index.items()
        if route["route_classification"] == "public_metadata"
    )
    mutating_routes = frozenset(
        key
        for key, route in index.items()
        if route["route_classification"] == "mutating_requires_authority"
    )
    if public_routes != PUBLIC_METADATA_ROUTES:
        raise ValueError("API_CONTRACT_PUBLIC_ROUTE_POLICY_DRIFT")
    if mutating_routes != MUTATING_ROUTES:
        raise ValueError("API_CONTRACT_MUTATING_ROUTE_POLICY_DRIFT")
    for key, route in index.items():
        expected_auth = (
            "public_metadata_no_auth"
            if key in PUBLIC_METADATA_ROUTES
            else "protected_local_bearer_required"
        )
        if route["auth_posture"] != expected_auth:
            raise ValueError("API_CONTRACT_AUTH_POLICY_DRIFT")
    for key in MUTATING_ROUTES:
        route = index[key]
        if (
            route["approval_posture"] != "required_before_mutation_authority"
            or route["idempotency_required"] is not True
            or route["idempotency_posture"] != "required_before_mutation_authority"
        ):
            raise ValueError("API_CONTRACT_MUTATION_GUARD_POLICY_DRIFT")
    for key, route in index.items():
        if key in MUTATING_ROUTES:
            continue
        if (
            route["approval_posture"] != "not_required_for_route_classification"
            or route["idempotency_required"] is not False
            or route["idempotency_posture"] != "not_required_for_route_classification"
        ):
            raise ValueError("API_CONTRACT_NONMUTATING_GUARD_POLICY_DRIFT")
    targeted = [route for route in routes if route["rate_limit_targeted"] is True]
    targeted_groups = frozenset(route["rate_limit_group"] for route in targeted)
    if len(targeted) != TARGETED_RATE_LIMIT_ROUTE_COUNT:
        raise ValueError("API_CONTRACT_RATE_LIMIT_COUNT_POLICY_DRIFT")
    if targeted_groups != TARGETED_RATE_LIMIT_GROUPS:
        raise ValueError("API_CONTRACT_RATE_LIMIT_GROUP_POLICY_DRIFT")
    targeted_route_payload = sorted(
        [route["method"], route["path"]] for route in targeted
    )
    targeted_route_fingerprint = hashlib.sha256(
        json.dumps(
            targeted_route_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    if targeted_route_fingerprint != TARGETED_RATE_LIMIT_ROUTE_FINGERPRINT:
        raise ValueError("API_CONTRACT_RATE_LIMIT_ROUTE_POLICY_DRIFT")
