from typing import Any
import pytest

from tests.m9_helpers import loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter


def decision(endpoint: Any, policy: Any | None = None) -> Any:
    return LocalLoopbackModelRuntimeAdapter().validate_endpoint(endpoint, policy or loopback_policy())


def invalid_policy(**overrides: Any) -> Any:
    return loopback_policy().model_copy(update=overrides)


def test_valid_loopback_hosts_pass_endpoint_policy() -> None:
    assert decision(loopback_endpoint(base_url="http://localhost:11434/api/generate")).allowed is True
    assert decision(loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate")).allowed is True
    assert decision(loopback_endpoint(base_url="http://[::1]:11434/api/generate")).allowed is True


def test_loopback_policy_rejects_disable_loopback_guard() -> None:
    with pytest.raises(ValueError, match="POLICY_CANNOT_DISABLE_LOOPBACK_GUARD"):
        loopback_policy(deny_non_loopback=False)


def test_loopback_policy_rejects_non_loopback_allowed_hosts() -> None:
    for host in ["example.com", "192.168.1.5", "10.0.0.5", "8.8.8.8"]:
        with pytest.raises(ValueError, match="ALLOWED_HOST_NOT_LOOPBACK"):
            loopback_policy(allowed_hosts=[host])


def test_loopback_policy_rejects_mixed_remote_allowlist() -> None:
    with pytest.raises(ValueError, match="ALLOWED_HOST_NOT_LOOPBACK"):
        loopback_policy(allowed_hosts=["127.0.0.1", "example.com"])


def test_remote_hosts_and_https_remote_hosts_are_denied() -> None:
    remote = decision(loopback_endpoint(base_url="http://example.com:11434/api/generate"))
    https_remote = decision(loopback_endpoint(base_url="https://example.com/api/generate", allowed_hosts=["example.com"]))

    assert remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in remote.reason_codes
    assert https_remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in https_remote.reason_codes


def test_caller_cannot_disable_loopback_guard_with_allowed_hosts_override() -> None:
    hostile_policy = invalid_policy(allowed_hosts=["example.com"], deny_non_loopback=False)
    remote_endpoint = loopback_endpoint(
        base_url="http://example.com/api/generate",
        allowed_hosts=["example.com"],
    )

    remote = decision(remote_endpoint, hostile_policy)

    assert remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in remote.reason_codes
    assert "POLICY_CANNOT_DISABLE_LOOPBACK_GUARD" in remote.reason_codes


def test_private_lan_hosts_are_denied_even_when_allowlisted() -> None:
    hostile_policy = invalid_policy(
        allowed_hosts=["127.0.0.1", "localhost", "::1", "192.168.1.5", "10.0.0.5"],
        deny_non_loopback=False,
    )

    for url in ["http://192.168.1.5:11434/api/generate", "http://10.0.0.5:11434/api/generate"]:
        blocked = decision(loopback_endpoint(base_url=url, allowed_hosts=hostile_policy.allowed_hosts), hostile_policy)
        assert blocked.allowed is False
        assert "NON_LOOPBACK_HOST_DENIED" in blocked.reason_codes


def test_public_ip_hosts_are_denied_even_when_allowlisted() -> None:
    hostile_policy = invalid_policy(allowed_hosts=["8.8.8.8"], deny_non_loopback=False)
    blocked = decision(loopback_endpoint(base_url="http://8.8.8.8/api/generate", allowed_hosts=["8.8.8.8"]), hostile_policy)

    assert blocked.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in blocked.reason_codes
    assert "ALLOWED_HOST_NOT_LOOPBACK" in blocked.reason_codes


def test_mixed_allowlist_still_permits_loopback_only() -> None:
    policy = invalid_policy(
        allowed_hosts=["127.0.0.1", "localhost", "::1", "example.com"],
        deny_non_loopback=False,
    )

    local = decision(loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate", allowed_hosts=policy.allowed_hosts), policy)
    remote = decision(loopback_endpoint(base_url="http://example.com/api/generate", allowed_hosts=policy.allowed_hosts), policy)

    assert local.allowed is True
    assert remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in remote.reason_codes


def test_url_credentials_secret_query_and_disabled_endpoint_are_denied() -> None:
    with_credentials = decision(loopback_endpoint(base_url="http://user:pass@127.0.0.1:11434/api/generate"))
    with_secret_query = decision(loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate?api_key=abc"))
    disabled = decision(loopback_endpoint(enabled=False))

    assert with_credentials.allowed is False
    assert "URL_CREDENTIALS_DENIED" in with_credentials.reason_codes
    assert with_secret_query.allowed is False
    assert "SECRET_QUERY_DENIED" in with_secret_query.reason_codes
    assert disabled.allowed is False
    assert "ENDPOINT_DISABLED" in disabled.reason_codes


def test_loopback_boundary_models_forbid_unknown_fields() -> None:
    with pytest.raises(ValueError):
        loopback_endpoint(unknown="field")
    with pytest.raises(ValueError):
        loopback_policy(unknown="field")
