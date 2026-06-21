from typing import Any
from fastapi.testclient import TestClient

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.app import app


client = TestClient(app)


def _payload(**overrides: Any) -> Any:
    data = {
        "approval_ref": "file-review-approval-capture:api",
        "actor_ref": "user:api",
        "review_packet_ref": "file-review-packet:api",
        "preview_result_ref": "redacted-file-preview-output:api",
        "redaction_summary_ref": "file-review-redaction-summary:api",
        "file_ref": "file-ref:api",
        "safe_path_ref": "filesystem-preview-path:safe-root_api/docs/review.md",
        "decision": "approve_review_only",
        "idempotency_key": "file-review-approval-idempotency:api",
        "safe_reason": "User reviewed the redacted packet.",
    }
    data.update(overrides)
    return data


def test_file_review_approval_capture_route_persists_review_only_record() -> None:
    response = client.post("/files/review/approvals/capture", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "approved_for_review_only"
    assert body["data"]["captured"] is True
    assert body["data"]["persisted"] is True
    assert body["data"]["raw_file_access_authorized"] is False
    assert body["data"]["context_proposal_authorized"] is False
    assert body["data"]["context_injection_authorized"] is False
    assert body["data"]["memory_write_authorized"] is False
    assert body["data"]["export_authorized"] is False
    assert body["data"]["execution_authorized"] is False
    assert body["data"]["execution_performed"] is False


def test_file_review_approval_capture_route_rejects_raw_content_extra() -> None:
    response = client.post(
        "/files/review/approvals/capture",
        json=_payload(raw_content="raw secret text"),
    )

    assert response.status_code == 422
    assert "raw secret text" not in response.text


def test_openapi_current_boundary_includes_review_capture_and_m151_smoke_routes() -> None:
    schema = app.openapi()

    assert schema["info"]["version"] == __version__
    assert len(schema["paths"]) == 112
    assert "/files/review/approvals/capture" in schema["paths"]
    assert "/files/tree/preview" in schema["paths"]
    assert "/observability/session-events" in schema["paths"]
    assert "/observability/client-errors" in schema["paths"]
    assert "/v1/models" in schema["paths"]
    assert "/v1/chat/completions" in schema["paths"]
    assert "/task-decomposition/run" in schema["paths"]
    assert schema["paths"]["/files/review/approvals/capture"]["post"]["operationId"] == "post_files_review_approvals_capture"
    for forbidden in [
        "/files/read",
        "/files/read/raw",
        "/files/read/content",
        "/files/read/full",
        "/files/review/approve",
        "/files/review/submit",
        "/context/propose",
        "/context/inject",
        "/memory/write",
        "/tools/execute",
        "/tool-runtime/execute",
    ]:
        assert forbidden not in schema["paths"]
