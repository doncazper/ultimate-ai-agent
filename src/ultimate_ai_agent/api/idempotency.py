from __future__ import annotations

import re
from dataclasses import dataclass

from ultimate_ai_agent.api.contracts import (
    ApiRouteClassification,
    ApiRouteIdempotencyEnforcement,
    ApiRouteIdempotencyPosture,
)


API_IDEMPOTENCY_AUDIT_POLICY_REF = "idempotency:p1-084:mutating-routes:v1"
IDEMPOTENCY_KEY_HEADER = "x-uaa-idempotency-key"
IDEMPOTENCY_REF_HEADER = "x-uaa-idempotency-ref"
IDEMPOTENCY_HEADER_NAMES = (IDEMPOTENCY_KEY_HEADER, IDEMPOTENCY_REF_HEADER)
WEB_EVIDENCE_DURABLE_IDEMPOTENCY_OWNER_REF = (
    "idempotency-owner:control-center-web-evidence-receipt-store:v1"
)
GOAL_JOURNAL_DURABLE_IDEMPOTENCY_OWNER_REF = "idempotency-owner:goal-journal:v1"
GOAL_APPROVAL_LEDGER_DURABLE_IDEMPOTENCY_OWNER_REF = (
    "idempotency-owner:goal-mutation-approval-ledger:v1"
)
GOAL_JOURNAL_DURABLE_REPLAY_PATHS = frozenset(
    {
        "/api/runtime/goals",
        "/api/runtime/goals/{goal_ref}/edit",
        "/api/runtime/goals/{goal_ref}/transition",
    }
)
GOAL_APPROVAL_LEDGER_DURABLE_REPLAY_PATHS = frozenset(
    {
        "/api/runtime/goals/approval-requests/create",
        "/api/runtime/goals/{goal_ref}/approval-requests/edit",
        "/api/runtime/goals/{goal_ref}/approval-requests/transition",
        (
            "/api/runtime/goals/approval-requests/"
            "{approval_request_ref}/decision"
        ),
        "/api/runtime/goals/approval-requests/revoke",
    }
)
IDEMPOTENCY_REQUIRED_INPUT_KINDS: tuple[str, ...] = (
    "idempotency_key",
    "idempotency_key_ref",
    "idempotency_ref",
    "scoped_idempotency_ref",
)
MIN_IDEMPOTENCY_VALUE_LENGTH = 8
MAX_IDEMPOTENCY_VALUE_LENGTH = 200
_IDEMPOTENCY_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,199}$")


@dataclass(frozen=True)
class ApiIdempotencyFailure:
    status_code: int
    code: str
    safe_message: str


def route_idempotency_posture(
    route_classification: ApiRouteClassification,
) -> tuple[bool, ApiRouteIdempotencyPosture, str | None, str]:
    if route_classification == ApiRouteClassification.mutating_requires_authority:
        return (
            True,
            ApiRouteIdempotencyPosture.required_before_mutation_authority,
            API_IDEMPOTENCY_AUDIT_POLICY_REF,
            "Mutating route class requires an idempotency key or scoped idempotency ref before mutation authority is claimed.",
        )
    return (
        False,
        ApiRouteIdempotencyPosture.not_required_for_route_classification,
        None,
        "Route classification does not currently grant mutation authority; no idempotency input is required by this audit.",
    )


def route_classification_requires_idempotency(
    route_classification: ApiRouteClassification,
) -> bool:
    return route_classification == ApiRouteClassification.mutating_requires_authority


def route_idempotency_enforcement(
    *,
    method: str,
    path: str,
    route_classification: ApiRouteClassification,
) -> tuple[ApiRouteIdempotencyEnforcement, str | None]:
    if method == "POST" and path == "/control-center/web-evidence/attach":
        return (
            ApiRouteIdempotencyEnforcement.route_owned_durable_replay,
            WEB_EVIDENCE_DURABLE_IDEMPOTENCY_OWNER_REF,
        )
    if method == "POST" and path in GOAL_JOURNAL_DURABLE_REPLAY_PATHS:
        return (
            ApiRouteIdempotencyEnforcement.route_owned_durable_replay,
            GOAL_JOURNAL_DURABLE_IDEMPOTENCY_OWNER_REF,
        )
    if method == "POST" and path in GOAL_APPROVAL_LEDGER_DURABLE_REPLAY_PATHS:
        return (
            ApiRouteIdempotencyEnforcement.route_owned_durable_replay,
            GOAL_APPROVAL_LEDGER_DURABLE_IDEMPOTENCY_OWNER_REF,
        )
    if route_classification_requires_idempotency(route_classification):
        return ApiRouteIdempotencyEnforcement.header_shape_gate_only, None
    return ApiRouteIdempotencyEnforcement.not_required, None


def idempotency_value_valid(value: str | None) -> bool:
    if value is None:
        return False
    candidate = value.strip()
    if len(candidate) < MIN_IDEMPOTENCY_VALUE_LENGTH:
        return False
    if len(candidate) > MAX_IDEMPOTENCY_VALUE_LENGTH:
        return False
    return _IDEMPOTENCY_VALUE_PATTERN.fullmatch(candidate) is not None


def idempotency_header_failure(
    headers: object,
    *,
    route_classification: ApiRouteClassification,
) -> ApiIdempotencyFailure | None:
    if not route_classification_requires_idempotency(route_classification):
        return None
    values = [
        str(headers.get(header_name, "")).strip()  # type: ignore[attr-defined]
        for header_name in IDEMPOTENCY_HEADER_NAMES
    ]
    if not any(values):
        return ApiIdempotencyFailure(
            status_code=428,
            code="API_IDEMPOTENCY_REQUIRED",
            safe_message=(
                "Mutating routes require an idempotency key or scoped "
                "idempotency ref before handler execution."
            ),
        )
    if any(idempotency_value_valid(value) for value in values):
        return None
    return ApiIdempotencyFailure(
        status_code=400,
        code="API_IDEMPOTENCY_INVALID",
        safe_message="The idempotency key or scoped idempotency ref is invalid.",
    )


def api_idempotency_audit_policy_payload(
    mutating_route_count: int,
) -> dict[str, object]:
    return {
        "policy_ref": API_IDEMPOTENCY_AUDIT_POLICY_REF,
        "applies_to_route_classification": ApiRouteClassification.mutating_requires_authority.value,
        "required_input_kinds": list(IDEMPOTENCY_REQUIRED_INPUT_KINDS),
        "accepted_header_names": list(IDEMPOTENCY_HEADER_NAMES),
        "mutating_route_count": mutating_route_count,
        "manifest_field": "idempotency_required",
        "posture_field": "idempotency_posture",
        "runtime_middleware_added": True,
        "durable_dedupe_store_added": False,
        "global_middleware_enforcement": "header_shape_gate_only",
        "route_owned_durable_replay_required_for_authority": True,
        "request_header_required_by_middleware": True,
        "mutation_authority_granted": False,
        "production_authority_enabled": False,
    }
