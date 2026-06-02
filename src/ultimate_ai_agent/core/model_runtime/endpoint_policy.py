import ipaddress
from typing import Any
from urllib.parse import parse_qsl, urlparse

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_runtime.enums import (
    LocalModelRuntimeKind,
    LocalModelRuntimeStatus,
    LocalModelRuntimeTransportKind,
)
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class _LocalRuntimeEndpointModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class LocalRuntimeEndpointDescriptor(_LocalRuntimeEndpointModel):
    endpoint_ref: str = Field(..., min_length=1)
    runtime_kind: LocalModelRuntimeKind
    status: LocalModelRuntimeStatus = LocalModelRuntimeStatus.planned_disabled
    transport_kind: LocalModelRuntimeTransportKind = LocalModelRuntimeTransportKind.loopback_http_metadata
    safe_summary: str = Field(..., min_length=1)
    allowed_now: bool = False
    endpoint_probe_allowed: bool = False
    endpoint_contacted: bool = False
    credentials_present: bool = False
    secret_query_present: bool = False
    localhost_only_required: bool = True
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


SECRET_QUERY_KEYS = {
    "key",
    "secret",
    "password",
    "credential",
    "authorization",
    "auth",
    "access_" + "token",
    "refresh_" + "token",
    "admin_" + "token",
    "session_" + "token",
    "api_" + "key",
}


def validate_local_runtime_endpoint_descriptor(
    descriptor: LocalRuntimeEndpointDescriptor,
) -> LocalRuntimeEndpointDescriptor:
    assert_secret_clean(descriptor.endpoint_ref, field_name="endpoint_ref")
    assert_secret_clean(descriptor.safe_summary, field_name="safe_summary")
    for value in descriptor.metadata_refs:
        assert_secret_clean(value, field_name="metadata_refs")
    _assert_safe_metadata(descriptor.metadata)
    if descriptor.status != LocalModelRuntimeStatus.planned_disabled:
        raise ValueError("local runtime endpoint descriptor must remain planned-disabled")
    if descriptor.allowed_now:
        raise ValueError("local runtime endpoint is not allowed now in M22")
    if descriptor.endpoint_probe_allowed:
        raise ValueError("local runtime endpoint probe is not allowed in M22")
    if descriptor.endpoint_contacted:
        raise ValueError("local runtime endpoint must not be contacted in M22")
    if descriptor.credentials_present:
        raise ValueError("local runtime endpoint credentials are not allowed")
    if descriptor.secret_query_present:
        raise ValueError("local runtime endpoint secret-like query is not allowed")
    _validate_endpoint_ref(descriptor.endpoint_ref)
    return descriptor


def _validate_endpoint_ref(endpoint_ref: str) -> None:
    parsed = urlparse(endpoint_ref)
    if not parsed.scheme and not parsed.netloc:
        return
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("local runtime endpoint metadata must use relative refs or loopback HTTP refs")
    if parsed.username or parsed.password:
        raise ValueError("local runtime endpoint credentials are not allowed")
    query_keys = {key.lower() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    if any(_is_secret_query_key(key) for key in query_keys):
        raise ValueError("local runtime endpoint secret-like query is not allowed")
    host = parsed.hostname
    if host is None:
        raise ValueError("local runtime endpoint metadata is missing host")
    if not _is_loopback_host(host):
        raise ValueError("local runtime endpoint metadata must be loopback-only; non-loopback hosts are denied")


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_secret_query_key(key: str) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in SECRET_QUERY_KEYS)


def _assert_safe_metadata(metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        if _is_secret_query_key(str(key)):
            raise ValueError("metadata contains secret-like content.")
        assert_secret_clean(str(key), field_name="metadata")
        if isinstance(value, dict):
            _assert_safe_metadata(value)
        elif isinstance(value, list):
            for item in value:
                assert_secret_clean(str(item), field_name="metadata")
        else:
            assert_secret_clean(str(value), field_name="metadata")
