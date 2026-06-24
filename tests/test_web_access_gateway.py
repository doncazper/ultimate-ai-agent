from __future__ import annotations

from typing import Any, Mapping

from ultimate_ai_agent.core.web_access import (
    WebAccessAdapterKind,
    WebAccessGateway,
    WebAccessNetworkLane,
    WebAccessPolicy,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)


class DummyReadOnlyAdapter:
    adapter_kind = WebAccessAdapterKind.LOCAL_FETCH

    def __init__(self) -> None:
        self.calls: list[WebAccessRequest] = []

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        self.calls.append(request)
        return {
            "url": request.url,
            "preview": "bounded redacted preview from dummy adapter",
            "sources": [{"url": request.url}],
        }


def _gateway(adapter: DummyReadOnlyAdapter | None = None) -> WebAccessGateway:
    adapter = adapter or DummyReadOnlyAdapter()
    return WebAccessGateway(
        policy=WebAccessPolicy(allow_read_only_fetch=True),
        adapters={WebAccessRequestKind.READ_ONLY_FETCH: adapter},
    )


def test_read_only_https_get_allowed_and_audited() -> None:
    adapter = DummyReadOnlyAdapter()
    gateway = _gateway(adapter)

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url="https://example.com/page",
            allowed_domains=("example.com",),
        )
    )

    assert result.status == WebAccessPolicyStatus.ALLOWED
    assert adapter.calls
    assert result.audit.request_id == result.request_id
    assert result.audit.adapter_kind == WebAccessAdapterKind.LOCAL_FETCH
    assert result.audit.policy_status == WebAccessPolicyStatus.ALLOWED
    assert result.audit.content_untrusted is True
    assert result.content_untrusted is True
    assert result.source_metadata
    assert result.source_metadata[0].content_untrusted is True


def test_post_is_denied_before_adapter_call() -> None:
    adapter = DummyReadOnlyAdapter()
    gateway = _gateway(adapter)

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url="https://example.com/submit",
            method="POST",
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert not adapter.calls
    assert "method_not_allowed:POST" in result.decision.reasons
    assert result.audit.policy_status == WebAccessPolicyStatus.DENIED


def test_private_or_local_network_is_denied() -> None:
    adapter = DummyReadOnlyAdapter()
    gateway = _gateway(adapter)

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url="https://127.0.0.1/admin",
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert not adapter.calls
    assert "private_or_local_network_denied" in result.decision.reasons


def test_browser_click_is_denied_and_not_routed() -> None:
    adapter = DummyReadOnlyAdapter()
    gateway = _gateway(adapter)

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.BROWSER_CLICK,
            url="https://example.com",
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert not adapter.calls
    assert "request_kind_not_enabled:browser_click" in result.decision.reasons


def test_non_gateway_network_lane_is_explicitly_denied() -> None:
    gateway = _gateway()

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url="https://huggingface.co/models",
            network_lane=WebAccessNetworkLane.MODEL_ACQUISITION,
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert result.decision.reasons == ("network_lane_not_gateway_phase_1:model_acquisition",)


def test_auth_cookies_body_download_upload_metadata_is_denied() -> None:
    gateway = _gateway()

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url="https://example.com/private",
            metadata={"cookies": True},
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert "auth_cookies_body_download_upload_denied" in result.decision.reasons
