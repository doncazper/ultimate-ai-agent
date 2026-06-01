from datetime import timedelta

from tests.m7_helpers import actor, classification
from tests.m9_helpers import loopback_endpoint
from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.time import utc_now


def smoke_policy(**overrides):
    from ultimate_ai_agent.core.model_runtime import ManualLoopbackSmokePolicy

    payload = {
        "policy_id": "m10_smoke_policy",
        "enable_manual_smoke": True,
    }
    payload.update(overrides)
    return ManualLoopbackSmokePolicy(**payload)


def smoke_request(**overrides):
    from ultimate_ai_agent.core.model_runtime import DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT, ManualLoopbackSmokeRequest

    payload = {
        "smoke_request_id": "smoke_req_1",
        "run_id": "run_m10",
        "endpoint": loopback_endpoint(endpoint_id="smoke_ep"),
        "model_id": "local-smoke-model",
        "approval_ref": "approval_m10",
        "fixed_prompt": DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
        "expected_marker": "UAA_LOCAL_SMOKE_OK",
        "policy": smoke_policy(),
        "actor_context": actor(),
        "data_classification": classification(),
    }
    payload.update(overrides)
    return ManualLoopbackSmokeRequest(**payload)


def approval_for_smoke(request=None, **approval_overrides):
    from ultimate_ai_agent.core.model_runtime import smoke_approval_request

    smoke = request or smoke_request()
    approval = smoke_approval_request(smoke).model_copy(update=approval_overrides)
    authority = LocalApprovalAuthority()
    authority.create_request(approval)
    grant = authority.grant(approval.approval_request_id, approved_by_actor_id="human_reviewer")
    decision = authority.validate_for_request(approval, grant.approval_ref)
    return authority, approval, grant, decision


def expired_approval_for_smoke(request=None):
    smoke = request or smoke_request()
    authority, approval, _, _ = approval_for_smoke(smoke)
    grant = authority.grant(
        approval.approval_request_id,
        approved_by_actor_id="human_reviewer",
        expires_at=utc_now() - timedelta(seconds=1),
    )
    return authority, approval, grant, authority.validate_for_request(approval, grant.approval_ref)


def wrong_scope_decision(request=None):
    from ultimate_ai_agent.core.model_runtime import smoke_approval_request

    smoke = request or smoke_request()
    wrong = ApprovalRequest(
        approval_request_id="areq_wrong_smoke",
        run_id=smoke.run_id,
        subject_type=ApprovalSubjectType.model_route,
        subject_id="other_subject",
        actor_context=smoke.actor_context,
        requested_action="route_cloud_model",
        purpose="Wrong approval scope.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=smoke.data_classification,
        resource_refs=["other_resource"],
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority = LocalApprovalAuthority()
    authority.create_request(wrong)
    grant = authority.grant(wrong.approval_request_id, approved_by_actor_id="human_reviewer")
    return authority.validate_for_request(smoke_approval_request(smoke), grant.approval_ref)
