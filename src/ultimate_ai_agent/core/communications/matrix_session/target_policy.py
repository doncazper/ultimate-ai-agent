from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from .contracts import stable_matrix_session_ref


MATRIX_LOCAL_HARNESS_ORIGIN = "http://127.0.0.1:18008"


def matrix_homeserver_ref(raw_url: str) -> str:
    normalized = _normalized_origin(raw_url)
    return stable_matrix_session_ref("homeserver-ref:matrix", normalized)


def matrix_homeserver_observation_ref(raw_url: str) -> str:
    normalized = _normalized_origin(raw_url)
    return stable_matrix_session_ref("observation-ref:matrix-homeserver", normalized)


def matrix_discovery_freshness_ref(observation_ref: str) -> str:
    return stable_matrix_session_ref(
        "freshness-ref:matrix-discovery",
        {"homeserver_observation_ref": observation_ref},
    )


def matrix_redirect_target_ref(raw_url: str) -> str:
    parsed = urlsplit(raw_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != "/uaa-matrix-callback"
    ):
        raise ValueError("MATRIX_SSO_CALLBACK_TARGET_DENIED")
    return stable_matrix_session_ref("redirect-target-ref:matrix", raw_url)


def validate_matrix_transient_target(
    *,
    expected_homeserver_ref: str,
    endpoint_class_ref: str,
    endpoint_url: str | None,
    discovery_origin: str | None,
    expected_redirect_target_ref: str | None,
    callback_url: str | None,
) -> None:
    raw_target = endpoint_url or discovery_origin
    if raw_target is None:
        raise ValueError("MATRIX_SESSION_TRANSIENT_TARGET_REQUIRED")
    if matrix_homeserver_ref(raw_target) != expected_homeserver_ref:
        raise ValueError("MATRIX_SESSION_HOMESERVER_BINDING_MISMATCH")
    normalized = _normalized_origin(raw_target)
    expected_endpoint_class_ref = (
        "endpoint-class-ref:matrix:local-harness"
        if normalized == MATRIX_LOCAL_HARNESS_ORIGIN
        else "endpoint-class-ref:matrix:public-https"
    )
    if endpoint_class_ref != expected_endpoint_class_ref:
        raise ValueError("MATRIX_SESSION_ENDPOINT_CLASS_MISMATCH")
    if callback_url is not None:
        if expected_redirect_target_ref is None:
            raise ValueError("MATRIX_SESSION_REDIRECT_SCOPE_REQUIRED")
        if matrix_redirect_target_ref(callback_url) != expected_redirect_target_ref:
            raise ValueError("MATRIX_SESSION_REDIRECT_BINDING_MISMATCH")


def _normalized_origin(raw_url: str) -> str:
    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("MATRIX_TARGET_URL_INVALID") from exc
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.hostname
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("MATRIX_TARGET_AUTHORITY_COMPONENT_DENIED")
    host = parsed.hostname.lower()
    if parsed.scheme == "http":
        origin = f"http://{host}:{port or 80}"
        if origin != MATRIX_LOCAL_HARNESS_ORIGIN:
            raise ValueError("MATRIX_TARGET_HTTPS_REQUIRED")
        return origin
    if parsed.scheme != "https" or port not in {None, 443}:
        raise ValueError("MATRIX_TARGET_HTTPS_REQUIRED")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host == "localhost" or "." not in host:
            raise ValueError("MATRIX_TARGET_HOSTNAME_DENIED")
    else:
        if not address.is_global:
            raise ValueError("MATRIX_TARGET_PRIVATE_ADDRESS_DENIED")
    return f"https://{host}"
