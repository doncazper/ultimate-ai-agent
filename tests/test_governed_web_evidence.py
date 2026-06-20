from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

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
from ultimate_ai_agent.core.truth import (
    FutureAllowlistedHttpsGetLanePlan,
    GovernedWebEvidenceIntakePolicy,
    GovernedWebEvidenceIntakeRecord,
    WEB_EVIDENCE_MAX_QUOTE_CHARS,
    WEB_EVIDENCE_MAX_REDACTED_PREVIEW_CHARS,
    build_fixture_governed_web_evidence_intake_bundle,
    build_fixture_governed_web_evidence_intake_record,
    validate_future_allowlisted_https_get_lane_plan,
    validate_governed_web_evidence_intake_bundle,
    validate_governed_web_evidence_intake_policy,
    validate_governed_web_evidence_intake_record,
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
    assert result.preview.text_preview
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


def _intake_record_payload():
    return build_fixture_governed_web_evidence_intake_record().model_dump(
        mode="python",
        round_trip=True,
    )


def test_governed_web_evidence_accepts_operator_supplied_metadata_only():
    record = build_fixture_governed_web_evidence_intake_record()
    bundle = build_fixture_governed_web_evidence_intake_bundle()
    policy = GovernedWebEvidenceIntakePolicy()

    assert validate_governed_web_evidence_intake_record(record) == record
    assert validate_governed_web_evidence_intake_bundle(bundle) == bundle
    assert validate_governed_web_evidence_intake_policy(policy) == policy
    assert policy.disabled_by_default is True
    assert policy.operator_supplied_metadata_only is True
    assert policy.live_fetch_allowed is False
    assert policy.openwebui_web_search_allowed is False


def test_governed_web_evidence_rejects_raw_body_fields_and_metadata():
    payload = _intake_record_payload()

    with pytest.raises(ValidationError, match="extra"):
        GovernedWebEvidenceIntakeRecord(**payload, raw_body="<html>full body</html>")

    payload = _intake_record_payload()
    payload["metadata"] = {"raw_body": "<html>full body</html>"}

    with pytest.raises(ValidationError, match="WEB_EVIDENCE_RAW_OR_AUTH_METADATA_DENIED"):
        GovernedWebEvidenceIntakeRecord(**payload)


def test_governed_web_evidence_rejects_overlong_quote_and_preview():
    payload = _intake_record_payload()
    payload["bounded_quote"] = "q" * (WEB_EVIDENCE_MAX_QUOTE_CHARS + 1)

    with pytest.raises(ValidationError, match="bounded_quote"):
        GovernedWebEvidenceIntakeRecord(**payload)

    payload = _intake_record_payload()
    payload["bounded_redacted_preview"] = "p" * (WEB_EVIDENCE_MAX_REDACTED_PREVIEW_CHARS + 1)

    with pytest.raises(ValidationError, match="bounded_redacted_preview"):
        GovernedWebEvidenceIntakeRecord(**payload)


def test_governed_web_evidence_requires_freshness_authority_and_receipts():
    payload = _intake_record_payload()
    payload.pop("freshness")

    with pytest.raises(ValidationError, match="freshness"):
        GovernedWebEvidenceIntakeRecord(**payload)

    payload = _intake_record_payload()
    payload["source_metadata"].pop("source_authority")

    with pytest.raises(ValidationError, match="source_authority"):
        GovernedWebEvidenceIntakeRecord(**payload)

    payload = _intake_record_payload()
    payload["receipt_refs"].pop("evidence_receipt_ref")

    with pytest.raises(ValidationError, match="evidence_receipt_ref"):
        GovernedWebEvidenceIntakeRecord(**payload)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("live_fetch_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("network_fetch_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("browser_automation_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("openwebui_web_search_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("model_provider_call_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("download_performed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("raw_body_stored", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("auth_used", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("cookies_used", "WEB_EVIDENCE_NO_LIVE_FETCH"),
        ("redirects_followed", "WEB_EVIDENCE_NO_LIVE_FETCH"),
    ],
)
def test_governed_web_evidence_rejects_live_fetch_or_browsing_flags(field_name, reason):
    payload = _intake_record_payload()
    payload[field_name] = True

    with pytest.raises(ValidationError, match=reason):
        GovernedWebEvidenceIntakeRecord(**payload)


def test_governed_web_evidence_future_https_lane_is_disabled_and_bounded():
    plan = FutureAllowlistedHttpsGetLanePlan(
        rollback_plan_ref="rollback:web-evidence-future-lane",
        non_goal_ref="non-goal:web-evidence-future-lane",
    )

    assert validate_future_allowlisted_https_get_lane_plan(plan) == plan
    assert plan.future_lane_only is True
    assert plan.disabled_by_default is True
    assert plan.https_get_only is True
    assert plan.allowlisted_targets_only is True
    assert plan.auth_allowed is False
    assert plan.cookies_allowed is False
    assert plan.redirects_allowed is False
    assert plan.downloads_allowed is False
    assert plan.raw_body_storage_allowed is False
    assert "outside UAA governance" in plan.openwebui_web_search_boundary

    with pytest.raises(ValidationError, match="WEB_EVIDENCE_FUTURE_LANE_DENIED:auth_allowed"):
        FutureAllowlistedHttpsGetLanePlan(
            rollback_plan_ref="rollback:web-evidence-future-lane",
            non_goal_ref="non-goal:web-evidence-future-lane",
            auth_allowed=True,
        )


def test_governed_web_evidence_source_contains_no_live_transport_code():
    source = Path("src/ultimate_ai_agent/core/truth/web_evidence.py").read_text(
        encoding="utf-8"
    )

    forbidden = [
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "selenium",
        "playwright",
        "openai.",
        "anthropic.",
    ]

    assert not [fragment for fragment in forbidden if fragment in source]
