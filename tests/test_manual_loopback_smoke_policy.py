import pytest

from tests.m10_helpers import smoke_policy, smoke_request
from tests.m9_helpers import loopback_endpoint
from ultimate_ai_agent.core.model_runtime import DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT


def test_safe_smoke_policy_and_request_validate() -> None:
    policy = smoke_policy()
    request = smoke_request(policy=policy)

    assert policy.enable_manual_smoke is True
    assert request.fixed_prompt == DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT
    assert request.policy.require_fixed_smoke_prompt is True


def test_policy_rejects_remote_allowed_hosts() -> None:
    with pytest.raises(ValueError, match="SMOKE_ALLOWED_HOST_NOT_LOOPBACK"):
        smoke_policy(allowed_hosts=["127.0.0.1", "example.com"])


def test_smoke_request_rejects_secret_and_user_content_prompts() -> None:
    with pytest.raises(ValueError, match="SMOKE_PROMPT_MUST_MATCH_FIXED_PROMPT"):
        smoke_request(fixed_prompt="Summarize this user file content.")

    with pytest.raises(ValueError):
        smoke_request(fixed_prompt="api_key='abcdefghijklmnop'")


def test_smoke_request_rejects_remote_credentials_secret_query_and_unknown_fields() -> None:
    with pytest.raises(ValueError):
        smoke_request(endpoint=loopback_endpoint(base_url="http://example.com/api/generate", allowed_hosts=["example.com"]))

    with pytest.raises(ValueError):
        smoke_request(endpoint=loopback_endpoint(base_url="http://user:pass@127.0.0.1/api/generate"))

    with pytest.raises(ValueError):
        smoke_request(endpoint=loopback_endpoint(base_url="http://127.0.0.1/api/generate?token=abc"))

    with pytest.raises(ValueError):
        smoke_policy(unknown="field")
