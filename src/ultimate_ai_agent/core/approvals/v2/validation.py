import re
from datetime import datetime
from typing import Any

from ultimate_ai_agent.core.approvals.v2.enums import (
    ActionKind,
    ActionSideEffectClass,
    ActorTrustLevel,
    ApprovalGrantStatus,
    ApprovalScopeKind,
    ResourceRefKind,
)
from ultimate_ai_agent.core.time import utc_now


SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")
SECRET_LIKE_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|cookie|password|private\s+key|secret|token|client[_-]?secret)"
)
RAW_LOCAL_PATH_RE = re.compile(r"(^|[\s:=])(/Users/|/home/|/var/|/etc/|[A-Za-z]:\\)")


SAFE_ACTION_KINDS = {ActionKind.no_effect, ActionKind.read_metadata}
SAFE_SIDE_EFFECTS = {ActionSideEffectClass.none, ActionSideEffectClass.read_only_metadata}
BLOCKED_ACTION_KINDS = set(ActionKind) - SAFE_ACTION_KINDS
BLOCKED_ACTOR_TRUST_LEVELS = {
    ActorTrustLevel.model_output_blocked,
    ActorTrustLevel.memory_recall_blocked,
    ActorTrustLevel.context_pack_non_authoritative,
    ActorTrustLevel.unknown_blocked,
}


def validate_safe_action_text(value: str, field_name: str = "text") -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if SECRET_LIKE_RE.search(value) or "-----BEGIN" in value or RAW_LOCAL_PATH_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")


def validate_safe_action_payload(value: Any, field_name: str = "payload") -> None:
    if isinstance(value, str):
        if value:
            validate_safe_action_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            validate_safe_action_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_action_payload(str(key), field_name)
            validate_safe_action_payload(item, field_name)


def validate_action_ref(value: str, field_name: str = "ref", *, allow_wildcard: bool = False) -> None:
    if allow_wildcard and value == "*":
        return
    validate_safe_action_text(value, field_name)
    if value != "none" and not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def assert_approval_ref_not_authority(approval_ref: str | None) -> list[str]:
    if not approval_ref:
        return []
    reasons = ["APPROVAL_REF_NOT_AUTHORITY"]
    if approval_ref.startswith("approval_test_"):
        reasons.append("APPROVAL_TEST_REF_DENIED")
    return reasons


def assert_approval_test_ref_denied(approval_ref: str | None) -> None:
    if approval_ref and approval_ref.startswith("approval_test_"):
        raise ValueError("approval_test refs are test-only and not runtime authority")


def assert_no_wildcard_approval(scope_kind: ApprovalScopeKind, *refs: str) -> list[str]:
    if scope_kind == ApprovalScopeKind.blocked_wildcard or "*" in refs:
        return ["WILDCARD_SCOPE_DENIED"]
    return []


def assert_no_replay(replay_nonce: str | None, used_replay_nonces: list[str]) -> list[str]:
    if replay_nonce and replay_nonce in used_replay_nonces:
        return ["APPROVAL_REPLAY_DETECTED"]
    return []


def assert_no_execution_authorized(value: bool) -> None:
    if value:
        raise ValueError("M28 approval decisions must not authorize execution")


def assert_no_execution_performed(value: bool) -> None:
    if value:
        raise ValueError("M28 approval decisions must not perform execution")


def assert_no_raw_action_content(*flags: bool) -> None:
    if any(flags):
        raise ValueError("raw action content is denied")


def assert_no_model_memory_context_authority(actor_trust_level: ActorTrustLevel, resource_kind: ResourceRefKind) -> list[str]:
    reasons: list[str] = []
    if actor_trust_level in BLOCKED_ACTOR_TRUST_LEVELS:
        reasons.append("ACTOR_TRUST_LEVEL_NOT_AUTHORITY")
    if resource_kind == ResourceRefKind.model_output_ref:
        reasons.append("MODEL_OUTPUT_NOT_AUTHORITY")
    if resource_kind == ResourceRefKind.memory_ref:
        reasons.append("MEMORY_REF_NOT_AUTHORITY")
    if resource_kind == ResourceRefKind.context_pack_ref:
        reasons.append("CONTEXT_PACK_NOT_AUTHORITY")
    if resource_kind == ResourceRefKind.tool_intent_ref:
        reasons.append("TOOL_INTENT_NOT_AUTHORITY")
    return reasons


def grant_status_reason(status: ApprovalGrantStatus) -> list[str]:
    if status == ApprovalGrantStatus.revoked:
        return ["APPROVAL_GRANT_REVOKED"]
    if status == ApprovalGrantStatus.expired:
        return ["APPROVAL_GRANT_EXPIRED"]
    if status != ApprovalGrantStatus.active_for_policy_only:
        return ["APPROVAL_GRANT_NOT_ACTIVE_FOR_POLICY"]
    return []


def expiry_reason(expires_at: datetime | None, current_time: datetime | None = None) -> list[str]:
    if expires_at is not None and expires_at <= (current_time or utc_now()):
        return ["APPROVAL_GRANT_EXPIRED"]
    return []


def action_kind_reason(action_kind: ActionKind, side_effect_class: ActionSideEffectClass) -> list[str]:
    if action_kind in BLOCKED_ACTION_KINDS or side_effect_class not in SAFE_SIDE_EFFECTS:
        return ["ACTION_KIND_DENIED"]
    return []
