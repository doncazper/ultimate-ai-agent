from datetime import UTC, datetime

from ultimate_ai_agent.core.approvals.v2.contracts import (
    ActionIntent,
    ActionPolicy,
    ActionPolicyDecision,
    ApprovalAuthorityV2Manifest,
    ApprovalBindingStatus,
    ApprovalDecisionStatus,
    ApprovalGrant,
    ApprovalReceiptPlan,
)
from ultimate_ai_agent.core.approvals.v2.enums import ApprovalGrantStatus
from ultimate_ai_agent.core.approvals.v2.validation import (
    action_kind_reason,
    assert_approval_ref_not_authority,
    assert_no_raw_action_content,
    assert_no_model_memory_context_authority,
    assert_no_replay,
    assert_no_wildcard_approval,
    expiry_reason,
    grant_status_reason,
    validate_action_ref as validate_structured_action_ref,
    validate_safe_action_payload,
    validate_safe_action_text,
)


def build_approval_authority_v2_manifest(baseline_version: str = "0.32.1") -> ApprovalAuthorityV2Manifest:
    return ApprovalAuthorityV2Manifest(baseline_version=baseline_version)


def validate_actor_ref(actor_ref) -> bool:
    actor_ref.model_validate(actor_ref.model_dump())
    return True


def validate_action_ref(action_ref) -> bool:
    action_ref.model_validate(action_ref.model_dump())
    return True


def validate_resource_ref(resource_ref) -> bool:
    resource_ref.model_validate(resource_ref.model_dump())
    return True


def validate_approval_scope(scope) -> bool:
    scope.model_validate(scope.model_dump())
    return True


def validate_approval_grant(grant: ApprovalGrant) -> bool:
    ApprovalGrant.model_validate(grant.model_dump())
    return True


def validate_action_intent(intent: ActionIntent) -> bool:
    ActionIntent.model_validate(intent.model_dump())
    return True


def validate_action_policy(policy: ActionPolicy) -> bool:
    ActionPolicy.model_validate(policy.model_dump())
    return True


def validate_approval_decision(decision: ActionPolicyDecision) -> bool:
    ActionPolicyDecision.model_validate(decision.model_dump())
    return True


def validate_action_policy_decision(decision: ActionPolicyDecision) -> bool:
    return validate_approval_decision(decision)


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


def _validation_reason(error: ValueError, *, secret_reason: str, fallback_reason: str) -> list[str]:
    message = str(error).lower()
    if "unsafe content" in message or "secret" in message:
        return [secret_reason, fallback_reason]
    return [fallback_reason]


def _validate_safe_text_reason(value: str | None, field_name: str, *, secret_reason: str, fallback_reason: str) -> list[str]:
    if value is None:
        return []
    try:
        validate_safe_action_text(value, field_name)
    except ValueError as exc:
        return _validation_reason(exc, secret_reason=secret_reason, fallback_reason=fallback_reason)
    return []


def _validate_ref_reason(
    value: str | None,
    field_name: str,
    *,
    secret_reason: str,
    fallback_reason: str,
    allow_wildcard: bool = False,
) -> list[str]:
    if value is None:
        return []
    try:
        validate_structured_action_ref(value, field_name, allow_wildcard=allow_wildcard)
    except ValueError as exc:
        return _validation_reason(exc, secret_reason=secret_reason, fallback_reason=fallback_reason)
    return []


def _validate_payload_reason(value, field_name: str, *, fallback_reason: str) -> list[str]:
    try:
        validate_safe_action_payload(value, field_name)
    except ValueError:
        return ["SECRET_METADATA_DENIED", fallback_reason]
    return []


def _extra_value(model, field_name: str, default=None):
    return getattr(model, field_name, default)


def _expiry_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _most_restrictive_expiry(*values: datetime | None) -> datetime | None:
    candidates = [_expiry_utc(value) for value in values if value is not None]
    return min(candidates) if candidates else None


def _revalidate_actor_for_evaluation(intent: ActionIntent) -> list[str]:
    reasons: list[str] = []
    reasons.extend(
        _validate_ref_reason(
            getattr(intent.actor, "actor_ref", None),
            "actor_ref",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    if getattr(intent.actor, "safe_label", ""):
        reasons.extend(
            _validate_safe_text_reason(
                getattr(intent.actor, "safe_label", ""),
                "safe_label",
                secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
                fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
            )
        )
    return reasons


def _revalidate_action_for_evaluation(intent: ActionIntent) -> list[str]:
    reasons: list[str] = []
    reasons.extend(
        _validate_ref_reason(
            getattr(intent.action, "action_ref", None),
            "action_ref",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    reasons.extend(
        _validate_safe_text_reason(
            getattr(intent.action, "safe_summary", ""),
            "safe_summary",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    return reasons


def _revalidate_resource_for_evaluation(intent: ActionIntent) -> list[str]:
    reasons: list[str] = []
    reasons.extend(
        _validate_ref_reason(
            getattr(intent.resource, "resource_ref", None),
            "resource_ref",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    if getattr(intent.resource, "safe_label", ""):
        reasons.extend(
            _validate_safe_text_reason(
                getattr(intent.resource, "safe_label", ""),
                "safe_label",
                secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
                fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
            )
        )
    return reasons


def _revalidate_action_intent_for_evaluation(intent: ActionIntent) -> list[str]:
    reasons: list[str] = []
    raw_flags = (
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_raw_model_output", "RAW_MODEL_OUTPUT_DENIED"),
        ("contains_raw_file_content", "RAW_FILE_CONTENT_DENIED"),
        ("contains_raw_transcript", "RAW_TRANSCRIPT_DENIED"),
    )
    for field_name, reason in raw_flags:
        if bool(_extra_value(intent, field_name, False)):
            reasons.extend([reason, "ACTION_INTENT_RAW_CONTENT_DENIED"])
    try:
        assert_no_raw_action_content(*(bool(_extra_value(intent, field_name, False)) for field_name, _ in raw_flags))
    except ValueError:
        if "ACTION_INTENT_RAW_CONTENT_DENIED" not in reasons:
            reasons.append("ACTION_INTENT_RAW_CONTENT_DENIED")
    if bool(_extra_value(intent, "contains_secret_like_content", False)):
        reasons.append("ACTION_INTENT_SECRET_CONTENT_DENIED")

    reasons.extend(
        _validate_ref_reason(
            getattr(intent, "intent_id", None),
            "intent_id",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    reasons.extend(
        _validate_safe_text_reason(
            getattr(intent, "safe_summary", None),
            "safe_summary",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    reasons.extend(
        _validate_safe_text_reason(
            getattr(intent, "approval_ref", None),
            "approval_ref",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    reasons.extend(
        _validate_ref_reason(
            getattr(intent, "consent_ref", None),
            "consent_ref",
            secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
        )
    )
    for ref in list(getattr(intent, "input_refs", [])):
        reasons.extend(
            _validate_ref_reason(
                ref,
                "input_ref",
                secret_reason="ACTION_INTENT_SECRET_CONTENT_DENIED",
                fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
            )
        )
    for ref in list(_extra_value(intent, "metadata_refs", [])):
        reasons.extend(
            _validate_ref_reason(
                ref,
                "metadata_ref",
                secret_reason="SECRET_METADATA_DENIED",
                fallback_reason="ACTION_INTENT_REVALIDATION_FAILED",
            )
        )
    reasons.extend(_validate_payload_reason(getattr(intent, "metadata", {}), "metadata", fallback_reason="ACTION_INTENT_REVALIDATION_FAILED"))
    reasons.extend(_revalidate_actor_for_evaluation(intent))
    reasons.extend(_revalidate_action_for_evaluation(intent))
    reasons.extend(_revalidate_resource_for_evaluation(intent))
    return _dedupe_reasons(reasons)


def _revalidate_policy_for_evaluation(policy: ActionPolicy) -> list[str]:
    reasons: list[str] = []
    reasons.extend(
        _validate_ref_reason(
            getattr(policy, "policy_ref", None),
            "policy_ref",
            secret_reason="ACTION_POLICY_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_POLICY_REVALIDATION_FAILED",
        )
    )
    reasons.extend(
        _validate_safe_text_reason(
            getattr(policy, "safe_summary", None),
            "safe_summary",
            secret_reason="ACTION_POLICY_SECRET_CONTENT_DENIED",
            fallback_reason="ACTION_POLICY_REVALIDATION_FAILED",
        )
    )
    return _dedupe_reasons(reasons)


def _revalidate_approval_scope_for_evaluation(grant: ApprovalGrant) -> list[str]:
    reasons: list[str] = []
    scope = grant.scope
    allow_wildcard = getattr(scope, "scope_kind", None) == "blocked_wildcard"
    for value, field_name in [
        (getattr(scope, "scope_ref", None), "scope_ref"),
        (getattr(scope, "actor_ref", None), "actor_ref"),
        (getattr(scope, "action_ref", None), "action_ref"),
        (getattr(scope, "resource_ref", None), "resource_ref"),
        (getattr(scope, "replay_nonce", None), "replay_nonce"),
    ]:
        reasons.extend(
            _validate_ref_reason(
                value,
                field_name,
                secret_reason="SECRET_METADATA_DENIED",
                fallback_reason="APPROVAL_GRANT_REVALIDATION_FAILED",
                allow_wildcard=allow_wildcard,
            )
        )
    return reasons


def _revalidate_approval_grant_for_evaluation(grant: ApprovalGrant) -> list[str]:
    reasons: list[str] = []
    allow_wildcard = getattr(grant.scope, "scope_kind", None) == "blocked_wildcard"
    for value, field_name in [
        (getattr(grant, "grant_ref", None), "grant_ref"),
        (getattr(grant, "actor_ref", None), "actor_ref"),
        (getattr(grant, "action_ref", None), "action_ref"),
        (getattr(grant, "resource_ref", None), "resource_ref"),
        (getattr(grant, "replay_nonce", None), "replay_nonce"),
    ]:
        if isinstance(value, str) and value.startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
        reasons.extend(
            _validate_ref_reason(
                value,
                field_name,
                secret_reason="SECRET_METADATA_DENIED",
                fallback_reason="APPROVAL_GRANT_REVALIDATION_FAILED",
                allow_wildcard=allow_wildcard,
            )
        )
    for nonce in list(getattr(grant, "used_replay_nonces", [])):
        reasons.extend(
            _validate_ref_reason(
                nonce,
                "used_replay_nonce",
                secret_reason="SECRET_METADATA_DENIED",
                fallback_reason="APPROVAL_GRANT_REVALIDATION_FAILED",
            )
        )
    for ref in list(_extra_value(grant, "metadata_refs", [])):
        reasons.extend(
            _validate_ref_reason(
                ref,
                "metadata_ref",
                secret_reason="SECRET_METADATA_DENIED",
                fallback_reason="APPROVAL_GRANT_REVALIDATION_FAILED",
            )
        )
    reasons.extend(_validate_payload_reason(getattr(grant, "metadata", {}), "metadata", fallback_reason="APPROVAL_GRANT_REVALIDATION_FAILED"))
    reasons.extend(_revalidate_approval_scope_for_evaluation(grant))
    return _dedupe_reasons(reasons)


def evaluate_approval_grant(
    intent: ActionIntent,
    grant: ApprovalGrant,
    *,
    current_time: datetime | None = None,
    replay_nonce: str | None = None,
) -> list[str]:
    reasons: list[str] = _revalidate_approval_grant_for_evaluation(grant)
    reasons.extend(grant_status_reason(grant.status))
    # The effective expiry is the most restrictive (earliest) of the grant-level
    # and scope-level deadlines. Using `or` would ignore an already-expired scope
    # deadline whenever the grant-level expiry is set, letting an expired scope be
    # bypassed by a later grant expiry.
    effective_expiry = _most_restrictive_expiry(grant.expires_at, grant.scope.expires_at)
    reasons.extend(expiry_reason(effective_expiry, _expiry_utc(current_time)))
    reasons.extend(assert_no_wildcard_approval(grant.scope.scope_kind, grant.actor_ref, grant.action_ref, grant.resource_ref))
    reasons.extend(assert_no_replay(replay_nonce or grant.replay_nonce or grant.scope.replay_nonce, grant.used_replay_nonces))
    if grant.actor_ref != intent.actor.actor_ref or grant.scope.actor_ref != intent.actor.actor_ref:
        reasons.append("APPROVAL_ACTOR_MISMATCH")
    if grant.action_ref != intent.action.action_ref or grant.scope.action_ref != intent.action.action_ref:
        reasons.append("APPROVAL_ACTION_MISMATCH")
    if grant.resource_ref != intent.resource.resource_ref or grant.scope.resource_ref != intent.resource.resource_ref:
        reasons.append("APPROVAL_RESOURCE_MISMATCH")
    if grant.status == ApprovalGrantStatus.revoked and "APPROVAL_GRANT_REVOKED" not in reasons:
        reasons.append("APPROVAL_GRANT_REVOKED")
    return list(dict.fromkeys(reasons))


def evaluate_action_policy(
    intent: ActionIntent,
    *,
    grant: ApprovalGrant | None = None,
    policy: ActionPolicy | None = None,
    current_time: datetime | None = None,
    replay_nonce: str | None = None,
) -> ActionPolicyDecision:
    active_policy = policy or ActionPolicy()
    reasons: list[str] = []
    reasons.extend(_revalidate_action_intent_for_evaluation(intent))
    reasons.extend(_revalidate_policy_for_evaluation(active_policy))
    reasons.extend(assert_approval_ref_not_authority(intent.approval_ref))
    if intent.consent_ref:
        reasons.append("CONSENT_REF_NOT_AUTHORITY")
    reasons.extend(action_kind_reason(intent.action.action_kind, intent.action.side_effect_class))
    reasons.extend(assert_no_model_memory_context_authority(intent.actor.trust_level, intent.resource.resource_kind))

    if grant is not None:
        reasons.extend(evaluate_approval_grant(intent, grant, current_time=current_time, replay_nonce=replay_nonce))
    elif intent.approval_ref or intent.consent_ref:
        reasons.append("VALID_APPROVAL_GRANT_REQUIRED")

    reasons = list(dict.fromkeys(reasons))
    if reasons:
        status = ApprovalDecisionStatus.denied
        if "APPROVAL_REPLAY_DETECTED" in reasons:
            status = ApprovalDecisionStatus.replay_detected
        elif "APPROVAL_GRANT_EXPIRED" in reasons:
            status = ApprovalDecisionStatus.expired
        elif "APPROVAL_GRANT_REVOKED" in reasons:
            status = ApprovalDecisionStatus.revoked
        return ActionPolicyDecision(
            decision_id=f"approval-decision:{intent.intent_id}",
            intent_id=intent.intent_id,
            status=status,
            binding_status=ApprovalBindingStatus.mismatch,
            allowed_for_policy=False,
            execution_authorized=False,
            execution_performed=False,
            reason_codes=reasons,
            safe_message="Action policy denied the request. No execution was authorized or performed.",
        )

    return ActionPolicyDecision(
        decision_id=f"approval-decision:{intent.intent_id}",
        intent_id=intent.intent_id,
        status=ApprovalDecisionStatus.allowed_for_policy,
        binding_status=ApprovalBindingStatus.bound,
        allowed_for_policy=True,
        execution_authorized=False,
        execution_performed=False,
        reason_codes=["ACTION_POLICY_ALLOWED_FOR_POLICY_ONLY"],
        safe_message="Action is allowed for policy decision only. No execution was authorized or performed.",
        receipt_plan=ApprovalReceiptPlan(
            receipt_plan_ref=f"approval-receipt-plan:{intent.intent_id}",
            decision_id=f"approval-decision:{intent.intent_id}",
            intent_id=intent.intent_id,
            grant_ref=grant.grant_ref if grant else None,
            execution_authorized=False,
            execution_performed=False,
            safe_summary="Non-authoritative receipt plan for M28 policy-only approval decision.",
        ),
    )
