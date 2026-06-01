from typing import Any

from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


BLOCKED_METADATA_KEYS = {
    "base_url",
    "host",
    "hostname",
    "ip",
    "private_ip",
    "node_key",
    "auth_key",
    "credential",
    "credential_ref",
    "api_key",
    "token",
    "secret",
    "password",
}


def assert_remote_secret_clean(value: Any, field_name: str) -> None:
    assert_secret_clean(value, field_name)
    _assert_no_blocked_metadata(value, field_name)


def _assert_no_blocked_metadata(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in BLOCKED_METADATA_KEYS:
                raise ValueError(f"{field_name} contains blocked remote metadata.")
            _assert_no_blocked_metadata(item, field_name)
    elif isinstance(value, list):
        for item in value:
            _assert_no_blocked_metadata(item, field_name)
