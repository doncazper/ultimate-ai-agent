import pytest

from tests.test_m23_local_model_call_contracts import valid_request
from ultimate_ai_agent.core.model_runtime import validate_local_model_endpoint, validate_local_model_call_request


@pytest.mark.parametrize(
    "endpoint_url",
    [
        "http://127.0.0.1:11434/api/generate",
        "http://localhost:11434/api/generate",
        "http://[::1]:11434/api/generate",
    ],
)
def test_m23_endpoint_accepts_loopback_only(endpoint_url):
    validated = validate_local_model_endpoint(endpoint_url)

    assert validated == endpoint_url


@pytest.mark.parametrize(
    ("endpoint_url", "message"),
    [
        ("https://example.com/api/generate", "loopback"),
        ("http://192.168.1.20:11434/api/generate", "loopback"),
        ("http://10.0.0.2:11434/api/generate", "loopback"),
        ("http://8.8.8.8:11434/api/generate", "loopback"),
        ("http://local-runtime.lan:11434/api/generate", "loopback"),
        ("http://user:pass@localhost:11434/api/generate", "credentials"),
        ("http://localhost:11434/api/generate?api_key=abc", "secret-like query"),
    ],
)
def test_m23_endpoint_rejects_external_lan_public_domain_credentials_and_secret_query(endpoint_url, message):
    with pytest.raises(ValueError, match=message):
        validate_local_model_endpoint(endpoint_url)


def test_m23_request_endpoint_validation_is_enforced():
    with pytest.raises(ValueError, match="loopback"):
        validate_local_model_call_request(valid_request(endpoint_url="http://example.com/api/generate"))

