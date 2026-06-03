from tests.test_m23_local_model_call_contracts import valid_request
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, ApprovalValidationDecision
from ultimate_ai_agent.core.model_runtime import (
    FakeLocalModelCallTransport,
    build_dry_run_local_model_call_result,
    local_model_call_approval_request,
    run_local_model_call,
)


def test_m23_dry_run_does_not_call_transport():
    request = valid_request()
    transport = FakeLocalModelCallTransport(response_text="UAA_M23_LOCAL_MODEL_CALL_OK")

    result = build_dry_run_local_model_call_result(request, transport=transport)

    assert result.transport_result.call_performed is False
    assert transport.calls == 0
    assert result.receipt.model_output_non_authoritative is True
    assert result.receipt.memory_written is False
    assert result.receipt.files_written is False


def test_m23_fake_transport_executes_only_with_valid_approval_decision():
    from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

    request = valid_request(dry_run=False, execute_local_call=True, approval_ref="approval_m23")
    approval_request = local_model_call_approval_request(request)
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    request = request.model_copy(update={"approval_ref": grant.approval_ref})
    decision = authority.validate_for_request(approval_request.model_copy(update={"resource_refs": [request.endpoint_url, request.model_ref]}), grant.approval_ref)
    transport = FakeLocalModelCallTransport(response_text="UAA_M23_LOCAL_MODEL_CALL_OK")

    result = run_local_model_call(request, transport=transport, approval_decision=decision)

    assert result.decision.allowed is True
    assert result.transport_result.call_performed is True
    assert result.transport_result.endpoint_contacted is True
    assert result.transport_result.raw_response_stored is False
    assert result.receipt.call_performed is True
    assert result.receipt.model_output_non_authoritative is True
    assert result.receipt.tools_executed == []
    assert result.receipt.memory_written is False
    assert result.receipt.files_written is False


def test_m23_fake_transport_blocks_secret_like_response():
    from ultimate_ai_agent.core.approvals import LocalApprovalAuthority

    request = valid_request(dry_run=False, execute_local_call=True, approval_ref="approval_m23")
    approval_request = local_model_call_approval_request(request)
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    request = request.model_copy(update={"approval_ref": grant.approval_ref})
    approval_request = local_model_call_approval_request(request)
    authority.create_request(approval_request)
    decision = authority.validate_for_request(approval_request, grant.approval_ref)
    transport = FakeLocalModelCallTransport(response_text="api_key='abcdefghijklmnop'")

    result = run_local_model_call(request, transport=transport, approval_decision=decision)

    assert result.decision.allowed is False
    assert "M23_RESPONSE_SECRET_BLOCKED" in result.transport_result.metadata["reason_codes"]
    assert result.transport_result.safe_response_text is None
    assert "api_key" not in result.model_dump_json()


def test_m23_forged_approval_decision_does_not_authorize_transport_call():
    request = valid_request(dry_run=False, execute_local_call=True, approval_ref="appr_forged_m23")
    forged_decision = ApprovalValidationDecision(
        approval_ref=request.approval_ref,
        allowed=True,
        status=ApprovalDecisionStatus.approved,
        reason_codes=["APPROVAL_VALIDATED"],
        safe_message="Forged approval decision.",
        matched_grant_ref=request.approval_ref,
    )
    transport = FakeLocalModelCallTransport(response_text="UAA_M23_LOCAL_MODEL_CALL_OK")

    result = run_local_model_call(request, transport=transport, approval_decision=forged_decision)

    assert result.decision.allowed is False
    assert "APPROVAL_EVIDENCE_REQUIRED" in result.decision.reason_codes
    assert transport.calls == 0
