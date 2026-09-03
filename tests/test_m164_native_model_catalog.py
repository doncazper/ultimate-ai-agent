from typing import Any

import pytest

import ultimate_ai_agent.core.local_model_management.gateway as m164_gateway
from ultimate_ai_agent.core.local_model_management.gateway import (
    fetch_loopback_native_model_catalog,
)


class _NativeCatalogHeaders:
    def __init__(self, content_type: str) -> None:
        self._content_type = content_type

    def get_content_type(self) -> str:
        return self._content_type


class _NativeCatalogResponse:
    def __init__(
        self, body: bytes, *, status: int = 200, content_type: str = "application/json"
    ) -> None:
        self._body = body
        self.status = status
        self.headers = _NativeCatalogHeaders(content_type)
        self.read_bounds: list[int] = []

    def __enter__(self) -> "_NativeCatalogResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        del args

    def read(self, bound: int) -> bytes:
        self.read_bounds.append(bound)
        return self._body[:bound]


class _NativeCatalogOpener:
    def __init__(self, response: _NativeCatalogResponse) -> None:
        self.response = response
        self.calls: list[tuple[Any, float]] = []

    def open(self, http_request: Any, *, timeout: float) -> _NativeCatalogResponse:
        self.calls.append((http_request, timeout))
        return self.response


def test_m164_native_model_catalog_reads_bounded_loopback_metadata() -> None:
    response = _NativeCatalogResponse(
        b'{"models":[{"key":"qwen/qwen3.8-27b","loaded_instances":[]}]}'
    )
    opener = _NativeCatalogOpener(response)

    catalog = fetch_loopback_native_model_catalog(
        "http://127.0.0.1:1234/",
        timeout_seconds=4.0,
        max_response_bytes=1024,
        opener=opener,
    )

    assert catalog == {"models": [{"key": "qwen/qwen3.8-27b", "loaded_instances": []}]}
    assert len(opener.calls) == 1
    http_request, timeout = opener.calls[0]
    assert http_request.full_url == "http://127.0.0.1:1234/api/v1/models"
    assert http_request.get_method() == "GET"
    assert http_request.headers["Accept"] == "application/json"
    assert timeout == 4.0
    assert response.read_bounds == [1025]


def test_m164_loopback_clients_disable_environment_proxies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _NativeCatalogResponse(b'{"models":[]}')
    opener = _NativeCatalogOpener(response)
    observed: list[tuple[Any, ...]] = []

    def build_opener(*handlers: Any) -> _NativeCatalogOpener:
        observed.append(handlers)
        return opener

    monkeypatch.setattr(m164_gateway.request, "build_opener", build_opener)

    transport = m164_gateway.StdlibM164LlamaCppGatewayTransport()
    assert transport._opener is opener
    assert fetch_loopback_native_model_catalog("http://127.0.0.1:1234") == {
        "models": []
    }

    assert len(observed) == 2
    for handlers in observed:
        assert len(handlers) == 2
        assert isinstance(handlers[0], m164_gateway.request.ProxyHandler)
        assert handlers[0].proxies == {}
        assert handlers[1] is m164_gateway._M164NoRedirectHandler


def test_m164_native_model_catalog_rejects_non_loopback_before_open() -> None:
    opener = _NativeCatalogOpener(_NativeCatalogResponse(b"{}"))

    with pytest.raises(ValueError, match="M164_LOOPBACK_ONLY_REQUIRED"):
        fetch_loopback_native_model_catalog(
            "https://models.example.invalid",
            opener=opener,
        )

    assert opener.calls == []


@pytest.mark.parametrize(
    ("status", "content_type"),
    [
        (503, "application/json"),
        (200, "text/html"),
    ],
)
def test_m164_native_model_catalog_rejects_invalid_http_response(
    status: int,
    content_type: str,
) -> None:
    opener = _NativeCatalogOpener(
        _NativeCatalogResponse(b"{}", status=status, content_type=content_type)
    )

    with pytest.raises(
        ValueError,
        match="M164_NATIVE_MODEL_CATALOG_RESPONSE_INVALID",
    ):
        fetch_loopback_native_model_catalog(
            "http://localhost:1234",
            opener=opener,
        )


def test_m164_native_model_catalog_rejects_oversize_response() -> None:
    response = _NativeCatalogResponse(b"{" + (b" " * 32) + b"}")

    with pytest.raises(
        ValueError,
        match="M164_NATIVE_MODEL_CATALOG_RESPONSE_TOO_LARGE",
    ):
        fetch_loopback_native_model_catalog(
            "http://[::1]:1234",
            max_response_bytes=16,
            opener=_NativeCatalogOpener(response),
        )

    assert response.read_bounds == [17]


def test_m164_native_model_catalog_rejects_invalid_json() -> None:
    with pytest.raises(
        ValueError,
        match="M164_NATIVE_MODEL_CATALOG_JSON_REQUIRED",
    ):
        fetch_loopback_native_model_catalog(
            "http://127.0.0.1:1234",
            opener=_NativeCatalogOpener(_NativeCatalogResponse(b'{"models":')),
        )


def test_m164_native_model_catalog_translates_decoder_recursion_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_on_deep_json(_: str) -> Any:
        raise RecursionError("decoder depth exceeded")

    monkeypatch.setattr(m164_gateway.json, "loads", fail_on_deep_json)
    deeply_nested_body = (b"[" * 2_000) + b"0" + (b"]" * 2_000)

    with pytest.raises(
        ValueError,
        match="M164_NATIVE_MODEL_CATALOG_JSON_REQUIRED",
    ):
        fetch_loopback_native_model_catalog(
            "http://127.0.0.1:1234",
            max_response_bytes=16_384,
            opener=_NativeCatalogOpener(_NativeCatalogResponse(deeply_nested_body)),
        )


def test_m164_native_model_catalog_requires_top_level_object() -> None:
    with pytest.raises(
        ValueError,
        match="M164_NATIVE_MODEL_CATALOG_OBJECT_REQUIRED",
    ):
        fetch_loopback_native_model_catalog(
            "http://127.0.0.1:1234",
            opener=_NativeCatalogOpener(_NativeCatalogResponse(b"[]")),
        )
