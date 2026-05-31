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


def test_secret_redaction_masks_key_token_password_values():
    broker = SecretBroker()
    redacted = broker.redact_value("api_key='abcdefghijklmnop' token='qrstuvwxyz123456'")

    assert "abcdefghijklmnop" not in redacted
    assert "qrstuvwxyz123456" not in redacted
    assert "[REDACTED_SECRET]" in redacted
