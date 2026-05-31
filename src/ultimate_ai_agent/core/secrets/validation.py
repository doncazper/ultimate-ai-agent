from ultimate_ai_agent.core.secrets.credentials import CredentialReference
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


def validate_credential_reference(reference: CredentialReference) -> bool:
    payload = reference.model_dump()
    if "secret_value" in payload:
        raise ValueError("CredentialReference must not contain raw secret values.")
    if contains_obvious_secret(payload):
        raise ValueError("CredentialReference contains raw secrets.")
    return True
