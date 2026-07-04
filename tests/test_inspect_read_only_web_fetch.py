from __future__ import annotations

import json
from typing import Any

from ultimate_ai_agent.core.tools.runtime import ReadOnlyHttpFetchTransportResponse

from scripts.inspect_read_only_web_fetch import inspect_payload


def _fake_real_world_transport(_request: Any, _policy: Any) -> Any:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"public docs ok\napi_key=super-secret-value\n",
    )


_fake_real_world_transport.transport_ref = (  # type: ignore[attr-defined]
    "http-fetch-transport:web-access-gateway-real-world-v1"
)
_fake_real_world_transport.real_world_transport_performed = True  # type: ignore[attr-defined]


def test_inspect_read_only_web_fetch_outputs_safe_refs_without_raw_url() -> None:
    payload = inspect_payload(
        url="https://docs.example.test/status",
        allowed_host="docs.example.test",
        transport=_fake_real_world_transport,
    )
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["invocation_allowed"] is True
    assert payload["network_call_performed"] is True
    assert payload["authority_posture"]["web_access_gateway_required"] is True
    assert payload["authority_posture"]["raw_url_returned"] is False
    assert payload["authority_posture"]["provider_sdk_call_performed"] is False
    assert payload["authority_posture"]["connector_write_performed"] is False
    assert payload["authority_posture"]["context_injection_performed"] is False
    assert payload["output"]["real_world_transport_performed"] is True
    assert (
        payload["output"]["transport_ref"]
        == "http-fetch-transport:web-access-gateway-real-world-v1"
    )
    assert payload["output"]["safe_url_ref"].startswith(
        "http-fetch-url:docs-example-test/path-"
    )
    assert "/status" not in payload["output"]["safe_url_ref"]
    assert "https://docs.example.test/status" not in rendered
    assert "super-secret-value" not in rendered
    assert "[REDACTED:SECRET_ASSIGNMENT]" in rendered
