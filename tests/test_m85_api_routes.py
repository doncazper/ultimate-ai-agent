from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.m85_helpers import approval_request
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import ApprovalReceipt, ApprovalStatus, LocalApprovalAuthority
from ultimate_ai_agent.core.time import utc_now


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


def test_approval_api_uses_public_authority_helper():
    app_source = Path("src/ultimate_ai_agent/api/app.py").read_text(encoding="utf-8")

    assert "authority.load_grant_for_validation(" in app_source
    assert "authority._grants" not in app_source


def test_approval_api_validation_denies_wrong_subject_action_resource_expired_and_revoked():
    request = approval_request()
    authority = LocalApprovalAuthority()
    authority.create_request(request)
    grant = authority.grant(request.approval_request_id, approved_by_actor_id="human_reviewer")

    for update, reason in [
        ({"subject_id": "other_subject"}, "APPROVAL_SUBJECT_MISMATCH"),
        ({"requested_action": "other_action"}, "APPROVAL_ACTION_NOT_GRANTED"),
        ({"resource_refs": ["other_resource"]}, "APPROVAL_RESOURCE_NOT_GRANTED"),
    ]:
        payload = {
            "validation_request": request.to_validation_request(grant.approval_ref).model_copy(update=update).model_dump(mode="json"),
            "grants": [grant.model_dump(mode="json")],
        }
        body = client.post("/approvals/validate", json=payload).json()
        assert body["success"] is True
        assert body["data"]["allowed"] is False
        assert reason in body["data"]["reason_codes"]

    expired = grant.model_copy(update={"expires_at": utc_now() - timedelta(minutes=1)})
    expired_payload = {
        "validation_request": request.to_validation_request(expired.approval_ref).model_dump(mode="json"),
        "grants": [expired.model_dump(mode="json")],
    }
    expired_body = client.post("/approvals/validate", json=expired_payload).json()
    assert expired_body["data"]["allowed"] is False
    assert "APPROVAL_EXPIRED" in expired_body["data"]["reason_codes"]

    revoked = grant.model_copy(update={"status": ApprovalStatus.revoked, "revoked_at": utc_now()})
    revoked_payload = {
        "validation_request": request.to_validation_request(revoked.approval_ref).model_dump(mode="json"),
        "grants": [revoked.model_dump(mode="json")],
    }
    revoked_body = client.post("/approvals/validate", json=revoked_payload).json()
    assert revoked_body["data"]["allowed"] is False
    assert "APPROVAL_REVOKED" in revoked_body["data"]["reason_codes"]


def test_approval_api_validation_error_does_not_echo_secret():
    secret = "sk_test_secret_value_12345"
    payload = approval_request().model_dump(mode="json")
    payload["metadata"] = {"note": f"api_key={secret}"}

    response = client.post("/approvals/requests/validate", json=payload)

    assert secret not in response.text
    assert "api_key" not in response.text
