from fastapi.testclient import TestClient

from tests.m85_helpers import approval_request
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import ApprovalReceipt, LocalApprovalAuthority


client = TestClient(app)


def test_approval_api_validates_request_grant_and_receipt():
    request = approval_request()
    authority = LocalApprovalAuthority()
    authority.create_request(request)
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")
    receipt = ApprovalReceipt.from_grant(grant, reason_codes=["APPROVAL_GRANTED"])

    assert client.post("/approvals/requests/validate", json=request.model_dump(mode="json")).json()["success"] is True
    assert client.post("/approvals/grants/validate", json=grant.model_dump(mode="json")).json()["success"] is True
    assert client.post("/approvals/receipts/validate", json=receipt.model_dump(mode="json")).json()["success"] is True


def test_approval_api_arbitrary_ref_validation_denies():
    payload = {
        "validation_request": approval_request().to_validation_request("human_approved_ref_123").model_dump(mode="json"),
        "grants": [],
    }

    body = client.post("/approvals/validate", json=payload).json()

    assert body["success"] is True
    assert body["data"]["allowed"] is False
    assert "APPROVAL_REF_UNKNOWN" in body["data"]["reason_codes"]


def test_approval_api_validation_error_does_not_echo_secret():
    secret = "sk_test_secret_value_12345"
    payload = approval_request().model_dump(mode="json")
    payload["metadata"] = {"note": f"api_key={secret}"}

    response = client.post("/approvals/requests/validate", json=payload)

    assert secret not in response.text
    assert "api_key" not in response.text
