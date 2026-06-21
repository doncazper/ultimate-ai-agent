from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope
from ultimate_ai_agent.core.secrets import (
    CredentialAuthType,
    CredentialReference,
    CredentialScope,
    CredentialStatus,
    SecretBroker,
)


def test_secret_broker_detects_obvious_secret_leakage() -> None:
    broker = SecretBroker()

    assert broker.validate_no_secret_leak({"payload": "api_key='abcdefghijklmnop'"}) is False
    assert broker.validate_no_secret_leak({"credential_ref": "cred_123"}) is True


def test_result_envelope_data_can_carry_secret_handle_without_raw_secret() -> None:
    broker = SecretBroker()
    broker.register_credential(
        CredentialReference(
            credential_ref="cred_result",
            auth_type=CredentialAuthType.api_key,
            scope=CredentialScope.user,
            status=CredentialStatus.active,
            allowed_purposes=["testing"],
        ),
        secret_value="api_key='abcdefghijklmnop'",
    )
    decision = broker.request_secret(
        credential_ref="cred_result",
        purpose="testing",
        consent_ref="consent_123",
    )
    envelope = ResultEnvelope(
        success=True,
        operation="evaluate_secret_access",
        service="SecretBroker",
        trace_id="trace_secret",
        data=decision.model_dump(),
    )

    serialized = envelope.model_dump_json()
    assert "abcdefghijklmnop" not in serialized
    assert "secret_handle" in serialized
