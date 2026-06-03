from datetime import datetime

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
    assert_no_model_memory_context_authority,
    assert_no_replay,
    assert_no_wildcard_approval,
    expiry_reason,
    grant_status_reason,
)


def build_approval_authority_v2_manifest(baseline_version: str = "0.32.0") -> ApprovalAuthorityV2Manifest:
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


def evaluate_approval_grant(
    intent: ActionIntent,
    grant: ApprovalGrant,
    *,
    current_time: datetime | None = None,
    replay_nonce: str | None = None,
) -> list[str]:
    reasons: list[str] = []
    reasons.extend(grant_status_reason(grant.status))
    reasons.extend(expiry_reason(grant.expires_at or grant.scope.expires_at, current_time))
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
    _ = policy or ActionPolicy()
    reasons: list[str] = []
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
