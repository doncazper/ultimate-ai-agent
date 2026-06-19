from ultimate_ai_agent.core.secrets import (
    CredentialAuthType,
    CredentialReference,
    CredentialScope,
    CredentialStatus,
    SecretAccessRequest,
    SecretBroker,
)


def active_reference() -> CredentialReference:
    return CredentialReference(
        credential_ref="cred_test",
        provider_id="provider_test",
        tool_id="tool_test",
        auth_type=CredentialAuthType.api_key,
        scope=CredentialScope.user,
        owner_user_id="user_123",
        status=CredentialStatus.active,
        allowed_purposes=["provider_lookup"],
    )


def test_secret_access_requires_consent_and_matching_purpose():
    broker = SecretBroker()
    broker.register_credential(active_reference(), secret_value="super-secret-token")

    missing_consent = broker.request_secret(
        SecretAccessRequest(
            credential_ref="cred_test",
            requester_actor_id="actor",
            purpose="provider_lookup",
            provider_id="provider_test",
        )
    )
    wrong_purpose = broker.request_secret(
        SecretAccessRequest(
            credential_ref="cred_test",
            requester_actor_id="actor",
            purpose="other_purpose",
            provider_id="provider_test",
            consent_ref="consent_123",
        )
    )

    assert missing_consent.allowed is False
    assert "CONSENT_REQUIRED" in missing_consent.reason_codes
    assert wrong_purpose.allowed is False
    assert "PURPOSE_NOT_ALLOWED" in wrong_purpose.reason_codes


def test_secret_access_returns_handle_not_raw_secret_and_redacts_views():
    broker = SecretBroker()
    broker.register_credential(active_reference(), secret_value="super-secret-token")

    decision = broker.request_secret(
        credential_ref="cred_test",
        purpose="provider_lookup",
        provider_id="provider_test",
        consent_ref="consent_123",
    )
    redacted = broker.redacted_view("cred_test")

    assert decision.allowed is True
    assert decision.secret_handle is not None
    assert "super-secret-token" not in decision.model_dump_json()
    assert redacted.redacted_value == "[REDACTED_SECRET]"
    assert broker.validate_no_secret_leak(decision.model_dump()) is True
    assert broker.validate_no_secret_leak(redacted.model_dump()) is True


def test_secret_access_rejects_secret_like_credential_ref_without_echoing_secret():
    broker = SecretBroker()
    secret_like_ref = "token='abcdefghijklmnop'"

    decision = broker.request_secret(
        SecretAccessRequest(
            credential_ref=secret_like_ref,
            requester_actor_id="actor",
            purpose="provider_lookup",
            provider_id="provider_test",
            consent_ref="consent_123",
        )
    )

    assert decision.allowed is False
    assert "SECRET_ACCESS_REF_UNSAFE" in decision.reason_codes
    assert "abcdefghijklmnop" not in decision.model_dump_json()
    assert decision.credential_ref == "[redacted]"


def test_secret_redaction_masks_key_token_password_values():
    broker = SecretBroker()
    redacted = broker.redact_value("api_key='abcdefghijklmnop' token='qrstuvwxyz123456'")

    assert "abcdefghijklmnop" not in redacted
    assert "qrstuvwxyz123456" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_secret_denial_output_is_secret_clean():
    broker = SecretBroker()
    broker.register_credential(active_reference(), secret_value="super-secret-token")

    decision = broker.request_secret(
        credential_ref="cred_test",
        purpose="provider_lookup",
        provider_id="other_provider",
        consent_ref="consent_123",
    )

    serialized = decision.model_dump_json()
    assert decision.allowed is False
    assert "PROVIDER_SCOPE_MISMATCH" in decision.reason_codes
    assert "super-secret-token" not in serialized
    assert broker.validate_no_secret_leak(decision.model_dump()) is True


def test_validate_no_secret_leak_rejects_nested_secret_like_output():
    broker = SecretBroker()

    payload = {
        "safe_summary": "redaction regression check",
        "metadata": {"unsafe_value": "token='abcdefghijklmnop'"},
    }

    assert broker.validate_no_secret_leak(payload) is False
