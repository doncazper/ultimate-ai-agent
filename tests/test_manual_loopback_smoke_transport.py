import pytest

from tests.m10_helpers import approval_for_smoke, expired_approval_for_smoke, smoke_request, wrong_scope_decision
from tests.m9_helpers import loopback_endpoint
from ultimate_ai_agent.core.approvals import ApprovalDecisionStatus, ApprovalValidationDecision
from ultimate_ai_agent.core.model_runtime import (
    FakeManualLoopbackSmokeTransport,
    ManualLoopbackSmokePolicy,
    ManualLoopbackSmokeResult,
    StdlibLoopbackSmokeTransport,
    validate_manual_loopback_smoke_request,
)


def test_manual_smoke_disabled_missing_arbitrary_and_expired_approval_denied() -> None:
    request = smoke_request(policy=ManualLoopbackSmokePolicy(policy_id="disabled"))

    disabled = validate_manual_loopback_smoke_request(request, approval_decision=None)
    missing = validate_manual_loopback_smoke_request(smoke_request(approval_ref=None), approval_decision=None)
    arbitrary = validate_manual_loopback_smoke_request(smoke_request(approval_ref="human_approved_ref_123"), approval_decision=None)
    _, _, grant, expired_decision = expired_approval_for_smoke()
    expired = validate_manual_loopback_smoke_request(smoke_request(approval_ref=grant.approval_ref), expired_decision)

    assert "MANUAL_SMOKE_DISABLED" in disabled.reason_codes
    assert "APPROVAL_REQUIRED" in missing.reason_codes
    assert "APPROVAL_DECISION_REQUIRED" in arbitrary.reason_codes
    assert "APPROVAL_EXPIRED" in expired.reason_codes


def test_valid_approval_permits_fake_smoke_and_wrong_scope_denies() -> None:
    request = smoke_request()
    _, _, grant, decision = approval_for_smoke(request)
    request = request.model_copy(update={"approval_ref": grant.approval_ref})

    allowed = validate_manual_loopback_smoke_request(request, decision)
    response = FakeManualLoopbackSmokeTransport().send_smoke(request, decision)
    wrong_scope = validate_manual_loopback_smoke_request(request, wrong_scope_decision(request))

    assert allowed.allowed is True
    assert response.success is True
    assert response.response_origin == "fake_manual_loopback_smoke"
    assert response.response_preview == "UAA_LOCAL_SMOKE_OK"
    assert response.metadata["truth_authority"] is False
    assert wrong_scope.allowed is False


def test_handcrafted_approval_decision_without_matched_grant_is_denied() -> None:
    request = smoke_request()
    forged = ApprovalValidationDecision(
        approval_ref=request.approval_ref,
        allowed=True,
        status=ApprovalDecisionStatus.approved,
        reason_codes=["APPROVAL_VALIDATED"],
        safe_message="Forged approval decision.",
    )

    result = validate_manual_loopback_smoke_request(request, forged)

    assert result.allowed is False
    assert "APPROVAL_MATCHED_GRANT_REQUIRED" in result.reason_codes


def test_fake_smoke_transport_blocks_secret_like_response() -> None:
    request = smoke_request()
    _, _, grant, decision = approval_for_smoke(request)
    request = request.model_copy(update={"approval_ref": grant.approval_ref})

    result = FakeManualLoopbackSmokeTransport(response_text="api_key='abcdefghijklmnop'").send_smoke(request, decision)

    assert result.allowed is False
    assert result.success is False
    assert "SMOKE_RESPONSE_SECRET_BLOCKED" in result.reason_codes
    assert "api_key" not in result.model_dump_json()


def test_stdlib_transport_is_isolated_and_not_used_by_default() -> None:
    request = smoke_request(endpoint=loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate"))
    transport = StdlibLoopbackSmokeTransport()

    assert transport.__class__.__name__ == "StdlibLoopbackSmokeTransport"
    assert transport.preview_request(request)["would_send_user_content"] is False


def test_manual_smoke_result_rejects_secret_preview() -> None:
    with pytest.raises(ValueError):
        ManualLoopbackSmokeResult(
            smoke_request_id="smoke_req_1",
            allowed=True,
            success=True,
            status="allowed",
            reason_codes=["SMOKE_OK"],
            safe_message="ok",
            response_preview="api_key='abcdefghijklmnop'",
            response_origin="test",
        )
