from typing import Any
import pytest

from ultimate_ai_agent.core.network import (
    AuthlessNetworkExpansionPolicy,
    AuthlessNetworkExpansionRequest,
    AuthlessNetworkExpansionStatus,
    build_authless_network_expansion_decision,
    validate_authless_network_expansion_decision,
    validate_authless_network_expansion_policy,
)


def _policy(**overrides: Any) -> Any:
    data = {
        "allowed_hosts": ("docs.example.test", "status.example.test"),
        "allowed_redirect_hosts": ("status.example.test",),
    }
    data.update(overrides)
    return AuthlessNetworkExpansionPolicy(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "network-authless-expansion-request:m95-safe",
        "actor_ref": "actor:local-reviewer",
        "scoped_session_ref": "autonomy-session:m95-single-session",
        "scope_ref": "scope:m95-docs-status",
        "network_tool_ref": "network-tool:m95-authless-read-only",
        "m72_fetch_tool_ref": "tool:http-fetch-read-only-m72",
        "allowed_host_policy_ref": "network-allowlist-policy:m95-authless",
        "target_host": "docs.example.test",
        "target_path": "/status",
        "exact_scope_approval_ref": "approval:m95-exact-scope",
        "audit_ref": "audit:m95-authless-read-only",
        "revocation_ref": "revocation:m95-authless-read-only",
        "safe_summary": "Allow an authless read-only GET preview for an allowlisted documentation host.",
    }
    data.update(overrides)
    return AuthlessNetworkExpansionRequest(**data)


def test_authless_network_expansion_allows_only_exact_scope_read_only_boundary() -> None:
    decision = build_authless_network_expansion_decision(_request(), _policy())

    assert decision.status == AuthlessNetworkExpansionStatus.authless_read_only_allowed
    assert decision.authless_read_only_allowed is True
    assert decision.capability_exists is True
    assert decision.disabled_by_default is True
    assert decision.exact_scope_bound is True
    assert decision.exact_approval_bound is True
    assert decision.allowlisted_domain_bound is True
    assert decision.redirect_policy_bound is True
    assert decision.bounded_output_bound is True
    assert decision.redaction_bound is True
    assert decision.audit_bound is True
    assert decision.revocation_bound is True
    assert decision.transport_injection_required is True
    assert decision.network_call_performed is False
    assert decision.unrestricted_network_allowed is False
    assert decision.authenticated_network_allowed is False
    assert decision.credential_headers_allowed is False
    assert decision.cookies_allowed is False
    assert decision.request_body_allowed is False
    assert decision.mutation_method_allowed is False
    assert decision.private_network_allowed is False
    assert decision.account_action_allowed is False
    assert decision.download_or_export_allowed is False
    assert decision.browser_form_allowed is False
    assert decision.provider_model_call_allowed is False
    assert decision.shell_execution_allowed is False
    assert decision.plugin_execution_allowed is False
    assert decision.memory_write_allowed is False
    assert decision.context_injection_allowed is False
    assert decision.backend_route_added is False
    assert decision.control_center_control_added is False
    assert decision.dependency_added is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.receipt_plan.store_redacted_preview_only is True
    assert decision.receipt_plan.raw_response_stored is False
    assert "M95_AUTHLESS_READ_ONLY_NETWORK_EXPANSION_ALLOWED" in decision.reason_codes
    assert "M96_REMAINS_FUTURE" in decision.reason_codes


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"target_host": "evil.example.test"}, "HOST_NOT_ALLOWLISTED_DENIED"),
        ({"target_host": "127.0.0.1"}, "PRIVATE_NETWORK_DENIED"),
        ({"target_host": "localhost"}, "PRIVATE_NETWORK_DENIED"),
        ({"target_path": "/secret-token"}, "SECRET_LIKE_PATH_DENIED"),
        ({"target_path": "/../admin"}, "PATH_TRAVERSAL_DENIED"),
        ({"target_path": "/status?token=value"}, "QUERY_STRING_DENIED"),
        ({"method": "POST"}, "NON_GET_METHOD_DENIED"),
        ({"query_string_present": True}, "QUERY_STRING_DENIED"),
        ({"raw_response_requested": True}, "RAW_RESPONSE_DENIED"),
        ({"raw_headers_requested": True}, "RAW_HEADERS_DENIED"),
        ({"unrestricted_network_requested": True}, "UNRESTRICTED_NETWORK_DENIED"),
        ({"authenticated_network_requested": True}, "AUTHENTICATED_NETWORK_DENIED"),
        ({"credentials_or_cookies_requested": True}, "CREDENTIAL_OR_COOKIE_DENIED"),
        ({"credential_headers_requested": True}, "CREDENTIAL_HEADERS_DENIED"),
        ({"mutation_method_requested": True}, "MUTATION_METHOD_DENIED"),
        ({"private_network_requested": True}, "PRIVATE_NETWORK_DENIED"),
        ({"account_action_requested": True}, "ACCOUNT_ACTION_DENIED"),
        ({"download_or_export_requested": True}, "DOWNLOAD_OR_EXPORT_DENIED"),
        ({"browser_form_requested": True}, "BROWSER_FORM_DENIED"),
        ({"provider_model_call_requested": True}, "PROVIDER_MODEL_CALL_DENIED"),
        ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
        ({"plugin_execution_requested": True}, "PLUGIN_EXECUTION_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"backend_route_requested": True}, "BACKEND_ROUTE_DENIED"),
        ({"control_center_control_requested": True}, "CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_requested": True}, "DEPENDENCY_CHANGE_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_authless_network_expansion_denies_unsafe_request_shapes(
    override: dict[str, object], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        build_authless_network_expansion_decision(_request(**override), _policy())


def test_authless_network_expansion_redirect_policy_is_allowlist_bound() -> None:
    allowed = build_authless_network_expansion_decision(
        _request(redirect_target_host="status.example.test", redirect_count=1),
        _policy(),
    )
    assert "REDIRECT_POLICY_BOUND" in allowed.reason_codes

    with pytest.raises(ValueError, match="REDIRECT_HOST_NOT_ALLOWLISTED"):
        build_authless_network_expansion_decision(
            _request(redirect_target_host="other.example.test", redirect_count=1),
            _policy(),
        )

    with pytest.raises(ValueError, match="REDIRECT_LIMIT_DENIED"):
        build_authless_network_expansion_decision(_request(redirect_count=2), _policy())


def test_authless_network_expansion_policy_rejects_wildcards_private_and_auth_enablement() -> None:
    with pytest.raises(ValueError, match="HOST_INVALID"):
        validate_authless_network_expansion_policy(AuthlessNetworkExpansionPolicy(allowed_hosts=("*",)))

    with pytest.raises(ValueError, match="PRIVATE_NETWORK_DENIED"):
        validate_authless_network_expansion_policy(
            AuthlessNetworkExpansionPolicy(allowed_hosts=("192.168.1.10",))
        )

    with pytest.raises(ValueError, match="AUTHENTICATED_NETWORK_DENIED"):
        validate_authless_network_expansion_policy(
            AuthlessNetworkExpansionPolicy(
                allowed_hosts=("docs.example.test",),
                authenticated_network_allowed=True,
            )
        )


def test_authless_network_expansion_requires_explicit_allowlist_policy() -> None:
    with pytest.raises(ValueError, match="ALLOWLIST_POLICY_REQUIRED"):
        build_authless_network_expansion_decision(_request())


def test_authless_network_expansion_approval_refs_and_authority_refs_are_not_authority() -> None:
    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        build_authless_network_expansion_decision(_request(approval_ref="approval:m95-extra"), _policy())

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        AuthlessNetworkExpansionRequest(
            **{
                **_request().model_dump(),
                "approval_test_ref": "approval_test_m95",
            }
        )

    with pytest.raises(ValueError, match="AUTHORITY_REF_NOT_NETWORK_AUTHORITY"):
        build_authless_network_expansion_decision(
            _request(authority_refs=["context-pack:m95"]),
            _policy(),
        )


def test_authless_network_expansion_revalidates_model_copy_mutated_fields() -> None:
    decision = build_authless_network_expansion_decision(_request(), _policy())

    with pytest.raises(ValueError, match="NETWORK_CALL_PERFORMED_DENIED_IN_DECISION"):
        validate_authless_network_expansion_decision(
            decision.model_copy(update={"network_call_performed": True})
        )

    with pytest.raises(ValueError, match="PRODUCTION_AUTHORITY_DENIED"):
        validate_authless_network_expansion_decision(
            decision.model_copy(update={"production_authority_granted": True})
        )

    with pytest.raises(ValueError, match="RAW_RESPONSE_DENIED"):
        validate_authless_network_expansion_decision(
            decision.model_copy(
                update={"receipt_plan": decision.receipt_plan.model_copy(update={"raw_response_stored": True})}
            )
        )


def test_authless_network_expansion_denies_secret_like_metadata_and_headers() -> None:
    with pytest.raises(ValueError, match="SECRET_LIKE_NETWORK_METADATA_DENIED"):
        build_authless_network_expansion_decision(
            _request(metadata={"api_key": "super-secret"}),
            _policy(),
        )

    with pytest.raises(ValueError, match="CREDENTIAL_HEADERS_DENIED"):
        build_authless_network_expansion_decision(
            _request(request_headers={"Authorization": "Bearer abc"}),
            _policy(),
        )
