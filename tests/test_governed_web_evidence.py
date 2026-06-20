from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.network.governed_web_evidence import (
    GOVERNED_WEB_EVIDENCE_ALLOWED_HOSTS_ENV,
    GOVERNED_WEB_EVIDENCE_ENABLED_ENV,
    GovernedWebEvidencePolicy,
    GovernedWebEvidenceRequest,
    GovernedWebEvidenceTransportResponse,
    build_governed_web_evidence_status,
    fetch_governed_web_evidence,
)


class FakeGovernedWebTransport:
    def __init__(self, response: GovernedWebEvidenceTransportResponse):
        self.response = response
        self.called = False

    def get(self, url: str, *, max_bytes: int, timeout_s: float) -> GovernedWebEvidenceTransportResponse:
        self.called = True
        assert url == "https://example.com/evidence"
        assert max_bytes <= 65536
        assert timeout_s <= 10
        return self.response


def _request(url: str = "https://example.com/evidence") -> GovernedWebEvidenceRequest:
    return GovernedWebEvidenceRequest(
        request_ref="web-evidence-request:test",
        run_id="web-evidence-run:test",
        actor_ref="actor:test-operator",
        purpose="Check a single allowlisted public evidence page.",
        url=url,
    )


def test_governed_web_evidence_status_discloses_disabled_capability() -> None:
    status = build_governed_web_evidence_status(GovernedWebEvidencePolicy())

    assert status.available is False
    assert status.enabled is False
    assert "GOVERNED_WEB_EVIDENCE_DISABLED" in status.reason_codes
    assert status.chatbot_capability_disclosure["available"] is False
    assert "unrestricted_browsing" in status.chatbot_capability_disclosure["blocked_capabilities"]


def test_governed_web_evidence_requires_enabled_allowlisted_host() -> None:
    result = fetch_governed_web_evidence(
        _request(),
        policy=GovernedWebEvidencePolicy(enabled=False, allowed_hosts=("example.com",)),
        transport=FakeGovernedWebTransport(
            GovernedWebEvidenceTransportResponse(
                status_code=200,
                final_url="https://example.com/evidence",
                content_type="text/plain",
                body=b"should not be called",
            )
        ),
    )

    assert result.allowed is False
    assert result.reason_codes == ["GOVERNED_WEB_EVIDENCE_DISABLED"]
    assert result.receipt.network_call_performed is False


def test_governed_web_evidence_blocks_non_allowlisted_hosts_without_network_call() -> None:
    transport = FakeGovernedWebTransport(
        GovernedWebEvidenceTransportResponse(
            status_code=200,
            final_url="https://example.com/evidence",
            content_type="text/plain",
            body=b"should not be called",
        )
    )
    result = fetch_governed_web_evidence(
        _request("https://not-example.test/evidence"),
        policy=GovernedWebEvidencePolicy(enabled=True, allowed_hosts=("example.com",)),
        transport=transport,
    )

    assert result.allowed is False
    assert result.reason_codes == ["GOVERNED_WEB_EVIDENCE_HOST_NOT_ALLOWLISTED"]
    assert result.receipt.network_call_performed is False
    assert transport.called is False


def test_governed_web_evidence_returns_bounded_redacted_preview_and_receipt_refs() -> None:
    secret_like = "api_key='ABCDEFGHIJKLMNOP'"
    transport = FakeGovernedWebTransport(
        GovernedWebEvidenceTransportResponse(
            status_code=200,
            final_url="https://example.com/evidence",
            content_type="text/html; charset=utf-8",
            body=f"<html><body>Evidence sentence. {secret_like}</body></html>".encode("utf-8"),
        )
    )

    result = fetch_governed_web_evidence(
        _request(),
        policy=GovernedWebEvidencePolicy(enabled=True, allowed_hosts=("example.com",)),
        transport=transport,
    )

    assert result.allowed is True
    assert result.preview is not None
    assert result.receipt.network_call_performed is True
    assert result.receipt.raw_body_stored is False
    assert result.receipt.raw_headers_stored is False
    assert result.receipt.redirect_followed is False
    assert result.receipt.browser_automation_used is False
    assert result.preview.untrusted_web_evidence is True
    assert "Evidence sentence" in result.preview.text_preview
    assert "ABCDEFGHIJKLMNOP" not in result.preview.text_preview
    assert "secret_value" in result.preview.redactions_applied
    assert result.receipt.receipt_ref.startswith("web-evidence-receipt:")
    assert result.preview.preview_ref.startswith("web-evidence-preview:")


def test_governed_web_evidence_blocks_redirect_response() -> None:
    result = fetch_governed_web_evidence(
        _request(),
        policy=GovernedWebEvidencePolicy(enabled=True, allowed_hosts=("example.com",)),
        transport=FakeGovernedWebTransport(
            GovernedWebEvidenceTransportResponse(
                status_code=302,
                final_url="https://example.com/other",
                content_type="text/plain",
                body=b"redirect",
            )
        ),
    )

    assert result.allowed is False
    assert result.reason_codes == ["GOVERNED_WEB_EVIDENCE_REDIRECT_DENIED"]
    assert result.receipt.network_call_performed is True
    assert result.receipt.redirect_followed is False


def test_governed_web_evidence_api_status_is_operator_visible(monkeypatch) -> None:
    monkeypatch.setenv(GOVERNED_WEB_EVIDENCE_ENABLED_ENV, "1")
    monkeypatch.setenv(GOVERNED_WEB_EVIDENCE_ALLOWED_HOSTS_ENV, "example.com")
    client = TestClient(app)

    response = client.get("/web-evidence/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["available"] is True
    assert body["data"]["allowed_hosts"] == ["example.com"]
    assert body["data"]["chatbot_capability_disclosure"]["available"] is True


def test_governed_web_evidence_api_request_is_blocked_without_runtime_transport(monkeypatch) -> None:
    monkeypatch.setenv(GOVERNED_WEB_EVIDENCE_ENABLED_ENV, "1")
    monkeypatch.setenv(GOVERNED_WEB_EVIDENCE_ALLOWED_HOSTS_ENV, "example.com")
    client = TestClient(app)

    response = client.post(
        "/web-evidence/request",
        json={
            "request_ref": "web-evidence-request:api",
            "run_id": "web-evidence-run:api",
            "actor_ref": "actor:test-operator",
            "purpose": "Check a single allowlisted public evidence page.",
            "url": "https://example.com/evidence",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "GOVERNED_WEB_EVIDENCE_TRANSPORT_UNAVAILABLE"
    assert "https://example.com/evidence" not in response.text
    assert body["data"]["receipt"]["raw_body_stored"] is False


def test_governed_web_evidence_routes_are_in_manifest_with_safe_metadata() -> None:
    client = TestClient(app)
    manifest = client.get("/api/manifest").json()
    routes = {route["path"]: route for route in manifest["routes"]}

    assert "/web-evidence/status" in routes
    assert "/web-evidence/request" in routes
    assert routes["/web-evidence/status"]["side_effect_class"] == "none"
    assert routes["/web-evidence/request"]["side_effect_class"] == "governed_network_read_only"
    assert "governed_web_evidence_status" in manifest["capabilities_declared"]
    assert "governed_web_evidence_raw_body_storage" in manifest["capabilities_blocked"]
