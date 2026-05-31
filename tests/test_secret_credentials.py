from datetime import datetime, timedelta

from ultimate_ai_agent.core.secrets import (
    CredentialAuthType,
    CredentialReference,
    CredentialScope,
    CredentialStatus,
    SecretBroker,
    SecretSensitivity,
)


def test_credential_reference_never_serializes_raw_secret_value():
    ref = CredentialReference(
        credential_ref="cred_weather_user",
        provider_id="weather_free_keyed",
        auth_type=CredentialAuthType.api_key,
        scope=CredentialScope.user,
        owner_user_id="user_123",
        status=CredentialStatus.active,
        allowed_purposes=["weather_lookup"],
        metadata={"sensitivity": SecretSensitivity.credential_secret},
    )

    dumped = ref.model_dump()
    assert "secret_value" not in dumped
    assert "raw_secret" not in ref.model_dump_json()


def test_secret_broker_registers_reference_and_denies_expired_credential():
    broker = SecretBroker()
    ref = CredentialReference(
        credential_ref="cred_expired",
        auth_type=CredentialAuthType.api_key,
        scope=CredentialScope.provider,
        status=CredentialStatus.active,
        allowed_purposes=["weather_lookup"],
        expires_at=datetime.utcnow() - timedelta(seconds=1),
    )

    broker.register_credential(ref, secret_value="api_key='abcdefghijklmnop'")
    decision = broker.request_secret(
        credential_ref="cred_expired",
        purpose="weather_lookup",
        consent_ref="consent_123",
    )

    assert decision.allowed is False
    assert "CREDENTIAL_INACTIVE" in decision.reason_codes
