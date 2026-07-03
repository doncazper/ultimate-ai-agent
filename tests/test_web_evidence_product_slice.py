from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api import founder_loop as founder_loop_api
from ultimate_ai_agent.core.control_center.proof import (
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.tools.runtime.http_fetch import (
    ReadOnlyHttpFetchTransportResponse,
)


ROOT = Path(__file__).resolve().parents[1]


def _fake_transport(_request: Any, _policy: Any) -> ReadOnlyHttpFetchTransportResponse:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"Public launch status. secret=super-sensitive-value",
    )


_fake_transport.transport_ref = "http-fetch-transport:fake-web-evidence"
_fake_transport.real_world_transport_performed = True


def _request() -> WebEvidenceProductSliceRequest:
    return WebEvidenceProductSliceRequest(
        request_ref="web-evidence-request:control-center-test",
        url="https://example.org/status",
        allowed_host="example.org",
        evidence_refs=["evidence-ref:control-center:web-evidence-test"],
        metadata_refs=["metadata-ref:control-center:web-evidence-test"],
    )


def test_web_evidence_product_slice_records_safe_refs_only(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
    )

    durable = repo.record_web_evidence_attachment(receipt)

    durable_text = json.dumps(durable, sort_keys=True).lower()
    assert receipt.redacted_preview == (
        "Public launch status. [REDACTED:SECRET_ASSIGNMENT]"
    )
    assert "super-sensitive-value" not in receipt.redacted_preview
    assert "redacted_preview" not in durable
    assert "public launch status" not in durable_text
    assert "super-sensitive-value" not in durable_text
    assert durable["response_body_storage"] == "omitted"
    assert durable["header_storage"] == "omitted"
    assert durable["safe_refs_only_for_durable_surfaces"] is True

    today = repo.today_summary()
    assert today["web_evidence_product_slice_status"] == (
        "implemented_allowlisted_gateway_preview_receipts"
    )
    assert receipt.receipt_ref in today["web_evidence_receipt_refs"]
    assert receipt.evidence_ref in today["web_evidence_evidence_refs"]
    assert receipt.web_access_audit_ref in today["web_evidence_audit_refs"]

    web_items = [
        item
        for item in today["evidence_timeline"]
        if item["item_kind"] == "web_evidence_attachment_ref"
    ]
    assert web_items
    assert web_items[0]["side_effect_class"] == "governed_network_read_only"
    assert receipt.receipt_ref in web_items[0]["receipt_refs"]
    assert receipt.web_access_audit_ref in web_items[0]["audit_refs"]
    assert web_items[0]["raw_evidence_included"] is False
    evidence = repo.evidence_timeline()
    event_types = {
        event["event_type"] for event in evidence["events"]
    }
    assert "web_evidence_attached" in event_types


def test_web_evidence_proof_and_trust_are_available(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
    )
    repo.record_web_evidence_attachment(receipt)

    proof = build_control_center_proof_index(today_summary=repo.today_summary())
    web_record = next(
        record
        for record in proof["records"]
        if record["proof_ref"] == WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF
    )
    assert web_record["proof_kind"] == "web_evidence"
    assert receipt.receipt_ref in web_record["receipt_refs"]
    assert receipt.web_access_request_ref in web_record["evidence_refs"]
    assert receipt.web_access_audit_ref in web_record["audit_refs"]
    assert web_record["raw_content_included"] is False

    trust = build_trust_authority_matrix_read_model(today_summary=repo.today_summary())
    web_lane = next(
        lane
        for lane in trust["lanes"]
        if lane["lane_ref"] == "trust-lane:web-evidence-product-slice"
    )
    assert web_lane["authority_state"] == "available_now"
    assert WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF in web_lane["route_refs"]
    assert WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF in web_lane["proof_refs"]
    assert web_lane["control_center_grants_authority"] is False


def test_web_evidence_attach_route_returns_backend_receipt(monkeypatch: Any) -> None:
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
    )

    class StubService:
        def attach_web_evidence(
            self,
            request: WebEvidenceProductSliceRequest,
        ) -> dict[str, Any]:
            assert request.request_ref == "web-evidence-request:api-test"
            return {
                **receipt.model_dump(mode="json"),
                "request_ref": request.request_ref,
                "durable_record_ref": receipt.attachment_ref,
            }

    monkeypatch.setattr(
        founder_loop_api,
        "get_founder_loop_service",
        lambda: StubService(),
    )
    client = TestClient(app)

    response = client.post(
        "/control-center/web-evidence/attach",
        json={
            "request_ref": "web-evidence-request:api-test",
            "url": "https://example.org/status",
            "allowed_host": "example.org",
            "evidence_refs": ["evidence-ref:control-center:web-evidence-api-test"],
            "metadata_refs": ["metadata-ref:control-center:web-evidence-api-test"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["operation"] == "control_center_web_evidence_attach"
    assert payload["data"]["receipt_ref"] == receipt.receipt_ref
    assert payload["data"]["raw_response_body_stored"] is False
    assert payload["data"]["auth_session_state_used"] is False
    assert payload["data"]["model_call_performed"] is False
    assert "raw_content_omitted" in payload["redactions_applied"]


def test_web_evidence_cli_inspection_uses_same_storage(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    repo = FounderLoopRepository(state_dir)
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
    )
    repo.record_web_evidence_attachment(receipt)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-web-evidence",
            "--limit",
            "5",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    output_text = result.stdout.lower()
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-web-evidence-inspect"
    )
    assert payload["attachment_count"] == 1
    assert payload["web_evidence_attachments"][0]["receipt_ref"] == (
        receipt.receipt_ref
    )
    assert payload["redacted_preview_omitted"] is True
    assert "super-sensitive-value" not in output_text
    assert str(state_dir).lower() not in output_text
