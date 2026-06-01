import pytest
from pydantic import ValidationError

from tests.m85_helpers import approval_request
from ultimate_ai_agent.core.approvals import ApprovalRiskLevel


def test_approval_request_forbids_unknown_fields():
    payload = approval_request().model_dump()
    payload["unexpected"] = "blocked"

    with pytest.raises(ValidationError):
        type(approval_request())(**payload)


def test_approval_request_blocks_secret_like_purpose():
    payload = approval_request().model_dump()
    payload["purpose"] = "api_key='ABCDEFGHIJKLMNOP'"
    with pytest.raises(ValueError, match="secret-like"):
        type(approval_request())(**payload)


def test_approval_request_keeps_scope_and_risk_explicit():
    request = approval_request(risk_level=ApprovalRiskLevel.high, resource_refs=["cloud_reasoner"])

    assert request.subject_id == "route_req_1"
    assert request.requested_action == "route_cloud_model"
    assert request.resource_refs == ["cloud_reasoner"]
    assert request.risk_level == ApprovalRiskLevel.high
