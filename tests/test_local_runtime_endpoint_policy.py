import pytest

from ultimate_ai_agent.core.model_runtime import (
    LocalModelRuntimeKind,
    LocalRuntimeEndpointDescriptor,
    validate_local_runtime_endpoint_descriptor,
)


@pytest.mark.parametrize(
    "endpoint_ref",
    [
        "loopback_ollama_default",
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://[::1]:11434",
    ],
)
def test_endpoint_descriptor_accepts_loopback_or_relative_metadata_only(endpoint_ref):
    descriptor = LocalRuntimeEndpointDescriptor(
        endpoint_ref=endpoint_ref,
        runtime_kind=LocalModelRuntimeKind.ollama_planned,
        safe_summary="loopback metadata only endpoint descriptor",
    )

    validated = validate_local_runtime_endpoint_descriptor(descriptor)

    assert validated.allowed_now is False
    assert validated.endpoint_probe_allowed is False
    assert validated.endpoint_contacted is False


@pytest.mark.parametrize(
    ("endpoint_ref", "message"),
    [
        ("https://example.com/v1", "non-loopback"),
        ("http://192.168.1.5:11434", "non-loopback"),
        ("http://8.8.8.8:11434", "non-loopback"),
        ("http://user:pass@localhost:11434", "credentials"),
        ("http://localhost:11434?api_key=secret", "secret-like query"),
    ],
)
def test_endpoint_descriptor_rejects_external_credentials_or_secret_query(endpoint_ref, message):
    descriptor = LocalRuntimeEndpointDescriptor(
        endpoint_ref=endpoint_ref,
        runtime_kind=LocalModelRuntimeKind.generic_loopback_http_planned,
        safe_summary="metadata only endpoint descriptor",
    )

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_endpoint_descriptor(descriptor)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("allowed_now", "allowed"),
        ("endpoint_probe_allowed", "probe"),
        ("endpoint_contacted", "contacted"),
        ("credentials_present", "credentials"),
        ("secret_query_present", "secret-like query"),
    ],
)
def test_endpoint_descriptor_rejects_activation_or_contact_flags(field, message):
    descriptor = LocalRuntimeEndpointDescriptor(
        endpoint_ref="loopback_future_runtime",
        runtime_kind=LocalModelRuntimeKind.mlx_planned,
        safe_summary="metadata only endpoint descriptor",
        **{field: True},
    )

    with pytest.raises(ValueError, match=message):
        validate_local_runtime_endpoint_descriptor(descriptor)
