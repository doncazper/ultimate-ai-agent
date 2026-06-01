import pytest

from tests.m9_helpers import loopback_endpoint, loopback_policy
from ultimate_ai_agent.core.model_runtime import LocalLoopbackModelRuntimeAdapter


def decision(endpoint, policy=None):
    return LocalLoopbackModelRuntimeAdapter().validate_endpoint(endpoint, policy or loopback_policy())


def test_valid_loopback_hosts_pass_endpoint_policy():
    assert decision(loopback_endpoint(base_url="http://localhost:11434/api/generate")).allowed is True
    assert decision(loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate")).allowed is True
    assert decision(loopback_endpoint(base_url="http://[::1]:11434/api/generate")).allowed is True


def test_remote_hosts_and_https_remote_hosts_are_denied():
    remote = decision(loopback_endpoint(base_url="http://example.com:11434/api/generate"))
    https_remote = decision(loopback_endpoint(base_url="https://example.com/api/generate", allowed_hosts=["example.com"]))

    assert remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in remote.reason_codes
    assert https_remote.allowed is False
    assert "NON_LOOPBACK_HOST_DENIED" in https_remote.reason_codes


def test_url_credentials_secret_query_and_disabled_endpoint_are_denied():
    with_credentials = decision(loopback_endpoint(base_url="http://user:pass@127.0.0.1:11434/api/generate"))
    with_secret_query = decision(loopback_endpoint(base_url="http://127.0.0.1:11434/api/generate?api_key=abc"))
    disabled = decision(loopback_endpoint(enabled=False))

    assert with_credentials.allowed is False
    assert "URL_CREDENTIALS_DENIED" in with_credentials.reason_codes
    assert with_secret_query.allowed is False
    assert "SECRET_QUERY_DENIED" in with_secret_query.reason_codes
    assert disabled.allowed is False
    assert "ENDPOINT_DISABLED" in disabled.reason_codes


def test_loopback_boundary_models_forbid_unknown_fields():
    with pytest.raises(ValueError):
        loopback_endpoint(unknown="field")
    with pytest.raises(ValueError):
        loopback_policy(unknown="field")
