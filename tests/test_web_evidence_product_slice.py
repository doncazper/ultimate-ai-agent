from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api import founder_loop as founder_loop_api
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center import (
    web_evidence_product_slice as web_evidence_slice,
)
from ultimate_ai_agent.core.control_center.proof import (
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV,
    WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WebEvidenceProductSliceAuthorityError,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
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


def _allow_example_org(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, raising=False)
    monkeypatch.setenv(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, "example.org")


def _browser_read_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:web-evidence-browser-read-test",
        mode=TrustMode.read_only,
        domains={AuthorityDomain.browser: [AuthorityCapability.read]},
        constraints={
            "web_evidence_lane_ref": "lane-ref:web-evidence-product-slice",
            "https_get_only": True,
            "browser_actions_allowed": False,
        },
        safe_summary=(
            "Test lease grants Browser read authority for one WebAccessGateway "
            "web evidence preview."
        ),
    )


def _issue_browser_read_lease(state_dir: Path) -> str:
    lease, receipt = AuthorityLeaseStore(state_dir).issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            requested_domains={
                AuthorityDomain.browser: [AuthorityCapability.read]
            },
            decision_reason_ref="reason-ref:test-web-evidence-browser-read",
            safe_summary=(
                "Select Browser read authority for one WebAccessGateway preview."
            ),
        ),
        idempotency_ref="idempotency-ref:test-web-evidence-browser-read",
    )
    assert lease is not None
    assert receipt.status == "issued"
    return lease.lease_ref


def test_web_evidence_product_slice_records_safe_refs_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
        active_authority_leases=[_browser_read_lease()],
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
    assert durable["web_access_gateway_required"] is True
    assert durable["configured_host_allowlist_required"] is True
    assert durable["request_ref_payload_idempotency"] is True
    assert durable["web_access_audit_summary"]["request_ref"] == (
        receipt.web_access_request_ref
    )
    assert durable["web_access_audit_summary"]["safe_url_ref"] == (
        receipt.safe_url_ref
    )
    assert durable["web_access_audit_summary"]["adapter_kind"] == "local_fetch"
    assert durable["web_access_audit_summary"]["network_lane"] == (
        "tool_runtime_read_only_fetch"
    )
    assert durable["web_access_audit_summary"]["authority_mode"] == "read_only"
    assert durable["web_access_audit_summary"]["policy_status"] == "allowed"
    assert durable["web_access_audit_summary"]["raw_url_omitted"] is True
    assert durable["authority_decision_outcome"] == "allow"
    assert durable["authority_lease_ref"] == (
        "authority-lease-ref:web-evidence-browser-read-test"
    )
    assert durable["authority_domain_ref"] == WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF
    assert (
        durable["authority_capability_ref"]
        == WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF
    )
    assert receipt.safe_url_ref.startswith("http-fetch-url:example-org/path-")
    assert "/status" not in receipt.safe_url_ref

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


def test_web_evidence_proof_and_trust_are_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
        active_authority_leases=[_browser_read_lease()],
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


def test_web_evidence_product_slice_requires_configured_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, raising=False)
    monkeypatch.delenv(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, raising=False)

    with pytest.raises(
        ValueError,
        match="WEB_EVIDENCE_PRODUCT_SLICE_CONFIGURED_ALLOWLIST_REQUIRED",
    ):
        build_web_evidence_product_slice_receipt(
            _request(),
            transport=_fake_transport,
            active_authority_leases=[_browser_read_lease()],
        )


def test_web_evidence_product_slice_rejects_caller_self_authorized_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, raising=False)
    monkeypatch.setenv(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, "example.org")
    request = WebEvidenceProductSliceRequest(
        request_ref="web-evidence-request:control-center-other-host",
        url="https://not-example.org/status",
        allowed_host="not-example.org",
    )

    with pytest.raises(
        ValueError,
        match="WEB_EVIDENCE_PRODUCT_SLICE_HOST_NOT_CONFIGURED",
    ):
        build_web_evidence_product_slice_receipt(
            request,
            transport=_fake_transport,
            active_authority_leases=[_browser_read_lease()],
        )


def test_web_evidence_product_slice_requires_browser_read_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    transport_called = False

    def tracking_transport(_request: Any, _policy: Any) -> ReadOnlyHttpFetchTransportResponse:
        nonlocal transport_called
        transport_called = True
        return _fake_transport(_request, _policy)

    with pytest.raises(WebEvidenceProductSliceAuthorityError) as exc_info:
        build_web_evidence_product_slice_receipt(
            _request(),
            transport=tracking_transport,
        )

    assert transport_called is False
    decision = exc_info.value.decision
    assert decision.outcome == "deny"
    assert decision.domain == "browser"
    assert decision.capability == "read"


def test_web_evidence_product_slice_safe_disable_blocks_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WEB_EVIDENCE_PRODUCT_SLICE_DISABLED_ENV, "1")
    monkeypatch.setenv(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, "example.org")
    transport_called = False

    def tracking_transport(_request: Any, _policy: Any) -> ReadOnlyHttpFetchTransportResponse:
        nonlocal transport_called
        transport_called = True
        return _fake_transport(_request, _policy)

    with pytest.raises(ValueError, match="WEB_EVIDENCE_PRODUCT_SLICE_DISABLED"):
        build_web_evidence_product_slice_receipt(
            _request(),
            transport=tracking_transport,
            active_authority_leases=[_browser_read_lease()],
        )

    assert transport_called is False


def test_web_evidence_attach_route_returns_backend_receipt(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _allow_example_org(monkeypatch)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
        active_authority_leases=[_browser_read_lease()],
    )

    class StubService:
        def attach_web_evidence(
            self,
            request: WebEvidenceProductSliceRequest,
            active_authority_leases: list[AuthorityLease] | None = None,
        ) -> dict[str, Any]:
            assert request.request_ref == "web-evidence-request:api-test"
            assert active_authority_leases == []
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


def test_web_evidence_attach_route_uses_gateway_storage_replay_and_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    lease_ref = _issue_browser_read_lease(authority_dir)
    monkeypatch.setattr(
        web_evidence_slice,
        "build_read_only_real_world_http_fetch_transport",
        lambda: _fake_transport,
    )
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    service = FounderLoopControlCenterService(repo)
    monkeypatch.setattr(
        founder_loop_api,
        "get_founder_loop_service",
        lambda: service,
    )
    client = TestClient(app)
    payload = {
        "request_ref": "web-evidence-request:api-storage-test",
        "url": "https://example.org/status",
        "allowed_host": "example.org",
        "evidence_refs": ["evidence-ref:control-center:web-evidence-storage-test"],
        "metadata_refs": ["metadata-ref:control-center:web-evidence-storage-test"],
    }

    first = client.post("/control-center/web-evidence/attach", json=payload)
    second = client.post("/control-center/web-evidence/attach", json=payload)
    conflict = client.post(
        "/control-center/web-evidence/attach",
        json={**payload, "url": "https://example.org/changed"},
    )

    assert first.status_code == 200
    assert first.json()["data"]["replayed"] is False
    assert first.json()["data"]["authority_lease_ref"] == lease_ref
    assert first.json()["data"]["web_access_audit_summary"]["raw_url_omitted"] is True
    assert second.status_code == 200
    assert second.json()["data"]["replayed"] is True
    assert conflict.status_code == 409
    assert "https://example.org/changed" not in conflict.text
    assert "raw_content_omitted" not in json.dumps(
        repo.list_web_evidence_attachments()
    ).lower()


def test_web_evidence_attach_route_blocks_unsafe_url_without_echoing_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    client = TestClient(app)
    raw_secret = "super-sensitive-value"
    response = client.post(
        "/control-center/web-evidence/attach",
        json={
            "request_ref": "web-evidence-request:unsafe-url-test",
            "url": f"https://example.org/status?token={raw_secret}",
            "allowed_host": "example.org",
        },
    )

    assert response.status_code == 400
    assert raw_secret not in response.text
    assert "https://example.org/status" not in response.text


def test_web_evidence_attach_route_requires_browser_read_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(tmp_path / "authority"))
    monkeypatch.setattr(
        web_evidence_slice,
        "build_read_only_real_world_http_fetch_transport",
        lambda: _fake_transport,
    )
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    service = FounderLoopControlCenterService(repo)
    monkeypatch.setattr(
        founder_loop_api,
        "get_founder_loop_service",
        lambda: service,
    )
    client = TestClient(app)

    response = client.post(
        "/control-center/web-evidence/attach",
        json={
            "request_ref": "web-evidence-request:api-authority-test",
            "url": "https://example.org/status",
            "allowed_host": "example.org",
            "evidence_refs": ["evidence-ref:control-center:web-evidence-auth-test"],
            "metadata_refs": ["metadata-ref:control-center:web-evidence-auth-test"],
        },
    )

    assert response.status_code == 403
    payload = response.json()["detail"]
    assert payload["code"] == "CONTROL_CENTER_WEB_EVIDENCE_AUTHORITY_DENIED"
    assert WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF in (
        payload["required_refs"]["required_domain_ref"]
    )
    assert repo.list_web_evidence_attachments() == []


def test_web_evidence_cli_attach_failure_omits_raw_url_secret_and_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(WEB_EVIDENCE_PRODUCT_SLICE_ALLOWED_HOSTS_ENV, raising=False)
    raw_secret = "super-sensitive-value"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(tmp_path / "state"),
            "attach-web-evidence",
            "--request-ref",
            "web-evidence-request:cli-failure-test",
            "--url",
            f"https://example.org/status?token={raw_secret}",
            "--allowed-host",
            "example.org",
            "--attach-to-ref",
            "founder-loop:daily-loop",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert raw_secret not in result.stdout
    assert "https://example.org/status" not in result.stdout
    assert str(tmp_path).lower() not in result.stdout.lower()


def test_web_evidence_cli_inspection_uses_same_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _allow_example_org(monkeypatch)
    state_dir = tmp_path / "state"
    repo = FounderLoopRepository(state_dir)
    receipt = build_web_evidence_product_slice_receipt(
        _request(),
        transport=_fake_transport,
        active_authority_leases=[_browser_read_lease()],
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


def test_web_evidence_authority_docs_track_control_center_route() -> None:
    conveyor = (
        ROOT / "docs/control_center/AUTHORITY_RAMP_CONVEYOR.md"
    ).read_text(encoding="utf-8")
    scorecard = json.loads(
        (ROOT / "docs/control_center/authority_candidate_scorecard.json").read_text(
            encoding="utf-8"
        )
    )

    assert WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF in conveyor
    assert "no backend route or Control Center control" not in conveyor
    first_lane = scorecard["first_implementation_lane"]
    foundation = next(
        item
        for item in scorecard["proposal_foundation"]
        if item["foundation_id"] == "read_only_real_world_web_fetch"
    )
    assert "no backend route or Control Center control" not in first_lane[
        "safe_summary"
    ]
    assert WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF in first_lane["route_refs"]
    assert WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF in foundation["route_refs"]
