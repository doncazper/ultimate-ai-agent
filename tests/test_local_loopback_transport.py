import pytest

from tests.m9_helpers import loopback_endpoint
from ultimate_ai_agent.core.model_runtime import DisabledNetworkTransport, FakeModelRuntimeTransport


def test_fake_transport_is_deterministic_and_marks_simulated_false():
    endpoint = loopback_endpoint()
    payload = {"runtime_request_id": "mrt_req_1", "output_format": "text"}
    first = FakeModelRuntimeTransport().send(payload, endpoint, timeout_seconds=2)
    second = FakeModelRuntimeTransport().send(payload, endpoint, timeout_seconds=2)

    assert first == second
    assert first.status_code == 200
    assert first.simulated is False
    assert "Authorization" not in first.headers_summary
    assert "Cookie" not in first.headers_summary


def test_disabled_network_transport_never_sends():
    response = DisabledNetworkTransport().send({"runtime_request_id": "mrt_req_1"}, loopback_endpoint(), timeout_seconds=2)

    assert response.status_code == 403
    assert response.simulated is True
    assert "NETWORK_TRANSPORT_DISABLED" in response.body["reason_codes"]


def test_transport_response_rejects_secret_body_and_headers():
    from ultimate_ai_agent.core.model_runtime import TransportResponse

    with pytest.raises(ValueError):
        TransportResponse(status_code=200, body={"note": "api_key='abcdefghijklmnop'"}, elapsed_ms=1)
    with pytest.raises(ValueError):
        TransportResponse(status_code=200, body={"ok": True}, elapsed_ms=1, headers_summary={"Authorization": "redacted"})
