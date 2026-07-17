from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from threading import RLock

from ultimate_ai_agent.api.contracts import ApiRouteRateLimitPosture


API_TARGETED_RATE_LIMIT_POLICY_REF = "rate-limit:p1-085:targeted-local:v1"
API_TARGETED_RATE_LIMIT_ENABLED_ENV = "UAA_API_TARGETED_RATE_LIMITS_ENABLED"
API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV = "UAA_API_TARGETED_RATE_LIMIT_MAX_REQUESTS"
API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV = (
    "UAA_API_TARGETED_RATE_LIMIT_WINDOW_SECONDS"
)

TARGETED_RATE_LIMIT_GROUP_DEFAULTS: dict[str, dict[str, int]] = {
    "model_chat": {"max_requests": 30, "window_seconds": 60},
    "task_decomposition": {"max_requests": 120, "window_seconds": 60},
    "action_preview_proposal": {"max_requests": 120, "window_seconds": 60},
    "today_to_action_envelope": {"max_requests": 60, "window_seconds": 60},
    "founder_loop_exact_action": {"max_requests": 12, "window_seconds": 60},
    "chat_durable_receipt": {"max_requests": 60, "window_seconds": 60},
    "memory_review_decision": {"max_requests": 60, "window_seconds": 60},
    "memory_context_pack_action_proposal": {"max_requests": 60, "window_seconds": 60},
    "memory_feedback": {"max_requests": 60, "window_seconds": 60},
    "action_decision": {"max_requests": 60, "window_seconds": 60},
    "local_model_validation": {"max_requests": 120, "window_seconds": 60},
    "provider_exact_approved_lane": {"max_requests": 12, "window_seconds": 60},
    "provider_credential_validation": {"max_requests": 12, "window_seconds": 60},
    "provider_router_dry_run": {"max_requests": 60, "window_seconds": 60},
    "web_evidence_product_slice": {"max_requests": 12, "window_seconds": 60},
    "extension_install_disabled_record": {"max_requests": 12, "window_seconds": 60},
    "governed_runtime_pilot": {"max_requests": 30, "window_seconds": 60},
    "communications_matrix_harness": {"max_requests": 12, "window_seconds": 60},
    "communications_matrix_session": {"max_requests": 12, "window_seconds": 60},
    "communications_matrix_crypto": {"max_requests": 12, "window_seconds": 60},
    "communications_matrix_messaging": {"max_requests": 12, "window_seconds": 60},
}

ACTION_PREVIEW_PROPOSAL_PATHS = {
    "/control-center/actions/preview",
    "/control-center/turn-router/preview",
    "/files/diff/preview",
    "/".join(("", "files", "review", "approvals", "capture")),
    "/files/write/propose",
}
TASK_DECOMPOSITION_PATHS = {
    "/task-decomposition/approval-requests",
    "/task-decomposition/approvals",
    "/task-decomposition/approvals/grants/capture",
    "/task-decomposition/approvals/revoke",
    "/task-decomposition/audit",
    "/task-decomposition/capabilities/register",
    "/task-decomposition/catalog",
    "/task-decomposition/classify",
    "/task-decomposition/decompose",
    "/task-decomposition/examples/init",
    "/task-decomposition/metrics",
    "/task-decomposition/plans/execute",
    "/task-decomposition/plans/validate",
    "/task-decomposition/registry/export",
    "/task-decomposition/run",
    "/task-decomposition/runs/{run_id}/lifecycle",
    "/task-decomposition/status",
}
LOCAL_MODEL_VALIDATION_PATHS = {
    "/local-runtime/validate",
    "/model-runtime/local/endpoints/validate",
    "/model-runtime/local/execution/validate",
    "/model-runtime/local/simulate-fallback",
    "/model-runtime/local/smoke/validate",
    "/model-runtime/manifests/validate",
    "/model-runtime/requests/validate",
    "/model-runtime/responses/validate",
    "/model-runtime/simulate",
    "/models/profiles/validate",
    "/models/route/preview",
    "/runtime/smoke-reports/validate",
}
ACTION_DECISION_SUFFIXES = ("/approve", "/edit", "/reject", "/defer")
ACTION_LOCAL_TASK_COMMIT_PATHS = {
    "/control-center/actions/{action_id}/local-task/commit",
}
MEMORY_REVIEW_DECISION_SUFFIXES = (
    "/accept",
    "/correct",
    "/reject",
    "/defer",
    "/merge",
    "/supersede",
    "/expire",
    "/forget-request",
)
MEMORY_MANUAL_CANDIDATE_PATHS = {
    "/control-center/memory/review/manual-candidate",
}
MEMORY_FEEDBACK_PATHS = {
    "/control-center/memory/feedback",
}
TODAY_TO_ACTION_ENVELOPE_PATHS = {
    "/control-center/today/action-envelope",
}
FOUNDER_LOOP_EXACT_ACTION_PATHS = {
    "/control-center/today/exact-action/source-review",
    "/control-center/today/exact-action/prepare",
    "/control-center/today/exact-action/approve",
    "/control-center/today/exact-action/execute",
}
MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_PATHS = {
    "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
}
CHAT_DURABLE_RECEIPT_PATHS = {
    "/control-center/chat/turns",
}
PROVIDER_EXACT_APPROVED_LANE_PATHS = {
    "/control-center/providers/exact-approved-lanes/tiny",
}
PROVIDER_CREDENTIAL_VALIDATION_PATHS = {
    "/control-center/providers/credentials/validate",
}
PROVIDER_ROUTER_DRY_RUN_PATHS = {
    "/control-center/providers/router/dry-run",
}
WEB_EVIDENCE_PRODUCT_SLICE_PATHS = {
    "/control-center/web-evidence/attach",
}
EXTENSION_INSTALL_DISABLED_RECORD_PATHS = {
    "/extensions/disabled-install-records",
    "/extensions/disabled-install-records/rollback",
}
GOVERNED_RUNTIME_MUTATING_PATHS = {
    "/api/runtime/authority-missions/approval-decisions",
    "/api/runtime/authority-missions/cancel",
    "/api/runtime/authority-missions/dead-letter-recovery",
    "/api/runtime/authority-leases",
    "/api/runtime/authority-leases/approve-and-issue",
    "/api/runtime/authority-leases/revoke",
    "/api/runtime/command/run",
    "/api/runtime/hermes/chat",
    "/api/runtime/invocations",
    "/api/runtime/local-model/call",
    "/api/runtime/invocations/{id}/approve",
    "/api/runtime/invocations/{id}/execute",
    "/api/runtime/safe-disable",
}
COMMUNICATIONS_MATRIX_HARNESS_PATHS = {
    "/control-center/communications/harness/inspect",
    "/control-center/communications/harness/smoke",
    "/control-center/communications/harness/start",
    "/control-center/communications/harness/fixture-seed",
    "/control-center/communications/harness/stop",
    "/control-center/communications/harness/reset",
}
COMMUNICATIONS_MATRIX_SESSION_PATHS = {
    "/control-center/communications/matrix/discovery-read",
    "/control-center/communications/matrix/auth-methods-read",
    "/control-center/communications/matrix/credential-auth-create",
    "/control-center/communications/matrix/sso-launch",
    "/control-center/communications/matrix/sso-callback-consume",
    "/control-center/communications/matrix/refresh",
    "/control-center/communications/matrix/logout",
    "/control-center/communications/matrix/revoke-all",
    "/control-center/communications/matrix/credential-store-rotate",
    "/control-center/communications/matrix/credential-delete",
}
COMMUNICATIONS_MATRIX_CRYPTO_PATHS = {
    "/control-center/communications/matrix-crypto/proposal",
}
COMMUNICATIONS_MATRIX_MESSAGING_PATHS = {
    "/control-center/communications/matrix-messaging/proposal",
    "/control-center/communications/matrix-messaging/send",
    "/control-center/communications/matrix-messaging/reply",
    "/control-center/communications/matrix-messaging/thread",
    "/control-center/communications/matrix-messaging/reaction",
    "/control-center/communications/matrix-messaging/edit",
    "/control-center/communications/matrix-messaging/redaction",
    "/control-center/communications/matrix-messaging/typing",
    "/control-center/communications/matrix-messaging/read-receipt",
    "/control-center/communications/matrix-messaging/draft-write",
    "/control-center/communications/matrix-messaging/draft-read",
    "/control-center/communications/matrix-messaging/outbox-enqueue",
    "/control-center/communications/matrix-messaging/outbox-read",
    "/control-center/communications/matrix-messaging/outbox-transition",
    "/control-center/communications/matrix-messaging/outbox-discard",
    "/control-center/communications/matrix-messaging/desktop-notify",
}


@dataclass(frozen=True)
class ApiRateLimitFailure:
    status_code: int
    code: str
    safe_message: str
    retry_after_seconds: int
    group: str


@dataclass
class _RateLimitBucket:
    count: int
    reset_at: float


_RATE_LIMIT_BUCKETS: dict[tuple[str, str], _RateLimitBucket] = {}
_RATE_LIMIT_LOCK = RLock()


def _env_int(name: str, default: int, *, minimum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


def targeted_rate_limits_enabled() -> bool:
    return os.getenv(API_TARGETED_RATE_LIMIT_ENABLED_ENV, "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def route_rate_limit_group(method: str, path: str) -> str | None:
    normalized_method = method.upper()
    if normalized_method == "POST" and path == "/v1/chat/completions":
        return "model_chat"
    if normalized_method == "GET" and path == "/v1/models":
        return "model_chat"
    if normalized_method in {"GET", "POST"} and (
        path in TASK_DECOMPOSITION_PATHS
        or (
            path.startswith("/task-decomposition/runs/") and path.endswith("/lifecycle")
        )
    ):
        return "task_decomposition"
    if normalized_method == "POST" and path in ACTION_PREVIEW_PROPOSAL_PATHS:
        return "action_preview_proposal"
    if normalized_method == "POST" and path in TODAY_TO_ACTION_ENVELOPE_PATHS:
        return "today_to_action_envelope"
    if normalized_method == "POST" and path in FOUNDER_LOOP_EXACT_ACTION_PATHS:
        return "founder_loop_exact_action"
    if normalized_method == "POST" and (
        path in CHAT_DURABLE_RECEIPT_PATHS
        or (
            path.startswith("/control-center/chat/turns/") and path.endswith("/handoff")
        )
    ):
        return "chat_durable_receipt"
    if (
        normalized_method == "POST"
        and path.startswith("/control-center/actions/")
        and path.endswith(ACTION_DECISION_SUFFIXES)
    ):
        return "action_decision"
    if normalized_method == "POST" and (
        path in ACTION_LOCAL_TASK_COMMIT_PATHS
        or (
            path.startswith("/control-center/actions/")
            and path.endswith("/local-task/commit")
        )
    ):
        return "action_decision"
    if normalized_method == "POST" and (
        path in MEMORY_MANUAL_CANDIDATE_PATHS
        or (
            path.startswith("/control-center/memory/review/")
            and path.endswith(MEMORY_REVIEW_DECISION_SUFFIXES)
        )
    ):
        return "memory_review_decision"
    if normalized_method == "POST" and (
        path in MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_PATHS
        or (
            path.startswith("/control-center/memory/context-packs/")
            and path.endswith("/action-proposal")
        )
    ):
        return "memory_context_pack_action_proposal"
    if normalized_method == "POST" and path in MEMORY_FEEDBACK_PATHS:
        return "memory_feedback"
    if normalized_method == "POST" and path in LOCAL_MODEL_VALIDATION_PATHS:
        return "local_model_validation"
    if normalized_method == "POST" and path in PROVIDER_EXACT_APPROVED_LANE_PATHS:
        return "provider_exact_approved_lane"
    if normalized_method == "POST" and path in PROVIDER_CREDENTIAL_VALIDATION_PATHS:
        return "provider_credential_validation"
    if normalized_method == "POST" and path in PROVIDER_ROUTER_DRY_RUN_PATHS:
        return "provider_router_dry_run"
    if normalized_method == "POST" and path in WEB_EVIDENCE_PRODUCT_SLICE_PATHS:
        return "web_evidence_product_slice"
    if normalized_method == "POST" and path in EXTENSION_INSTALL_DISABLED_RECORD_PATHS:
        return "extension_install_disabled_record"
    if normalized_method == "POST" and path in COMMUNICATIONS_MATRIX_HARNESS_PATHS:
        return "communications_matrix_harness"
    if normalized_method == "POST" and path in COMMUNICATIONS_MATRIX_SESSION_PATHS:
        return "communications_matrix_session"
    if normalized_method == "POST" and path in COMMUNICATIONS_MATRIX_CRYPTO_PATHS:
        return "communications_matrix_crypto"
    if (
        normalized_method == "POST"
        and path in COMMUNICATIONS_MATRIX_MESSAGING_PATHS
    ):
        return "communications_matrix_messaging"
    if normalized_method == "POST" and (
        path in GOVERNED_RUNTIME_MUTATING_PATHS
        or (
            path.startswith("/api/runtime/invocations/")
            and (path.endswith("/approve") or path.endswith("/execute"))
        )
    ):
        return "governed_runtime_pilot"
    return None


def route_rate_limit_posture(
    method: str,
    path: str,
) -> tuple[bool, ApiRouteRateLimitPosture, str | None, str | None, str]:
    group = route_rate_limit_group(method, path)
    if group is None:
        return (
            False,
            ApiRouteRateLimitPosture.not_targeted_for_route,
            None,
            None,
            "Route is not in the UAA-P1-085 targeted expensive/sensitive route set.",
        )
    return (
        True,
        ApiRouteRateLimitPosture.targeted_local_fixed_window,
        API_TARGETED_RATE_LIMIT_POLICY_REF,
        group,
        "Route is in the UAA-P1-085 targeted local fixed-window rate-limit set.",
    )


def rate_limit_settings_for_group(group: str) -> tuple[int, int]:
    defaults = TARGETED_RATE_LIMIT_GROUP_DEFAULTS[group]
    max_requests = _env_int(
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
        defaults["max_requests"],
        minimum=1,
    )
    window_seconds = _env_int(
        API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV,
        defaults["window_seconds"],
        minimum=1,
    )
    return max_requests, window_seconds


def api_rate_limit_policy_payload(targeted_route_count: int) -> dict[str, object]:
    return {
        "policy_ref": API_TARGETED_RATE_LIMIT_POLICY_REF,
        "targeted_groups": sorted(TARGETED_RATE_LIMIT_GROUP_DEFAULTS),
        "targeted_route_count": targeted_route_count,
        "posture_field": "rate_limit_posture",
        "targeted_field": "rate_limit_targeted",
        "runtime_middleware_added": True,
        "local_in_memory_fixed_window": True,
        "distributed_quota_store_added": False,
        "dependencies_added": False,
        "rate_limits_are_auth": False,
        "production_authority_enabled": False,
    }


def reset_api_rate_limit_state() -> None:
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_BUCKETS.clear()


def rate_limit_failure(
    *,
    method: str,
    path: str,
    client_ref: str | None,
    now: float | None = None,
) -> ApiRateLimitFailure | None:
    if not targeted_rate_limits_enabled():
        return None
    group = route_rate_limit_group(method, path)
    if group is None:
        return None
    max_requests, window_seconds = rate_limit_settings_for_group(group)
    clock = time.monotonic() if now is None else now
    key = (group, client_ref or "local-client")
    with _RATE_LIMIT_LOCK:
        bucket = _RATE_LIMIT_BUCKETS.get(key)
        if bucket is None or clock >= bucket.reset_at:
            _RATE_LIMIT_BUCKETS[key] = _RateLimitBucket(
                count=1, reset_at=clock + window_seconds
            )
            return None
        if bucket.count >= max_requests:
            retry_after = max(1, math.ceil(bucket.reset_at - clock))
            return ApiRateLimitFailure(
                status_code=429,
                code="API_TARGETED_RATE_LIMITED",
                safe_message="The local targeted rate limit was reached for this route group.",
                retry_after_seconds=retry_after,
                group=group,
            )
        bucket.count += 1
    return None
