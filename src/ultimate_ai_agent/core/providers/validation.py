from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.providers.enums import ProviderAuthRequirement
from ultimate_ai_agent.core.providers.manifests import ProviderManifest
from ultimate_ai_agent.core.providers.results import ProviderResultEnvelope


def validate_provider_manifest(manifest: ProviderManifest) -> bool:
    if manifest.auth_requirement in [
        ProviderAuthRequirement.required_key,
        ProviderAuthRequirement.oauth_required,
        ProviderAuthRequirement.service_account_required,
    ] and not manifest.credential_ref:
        raise ValueError("Provider manifest requires credential_ref for credentialed auth.")
    if scan_payload_for_secrets(manifest.model_dump()):
        raise ValueError("Provider manifest contains raw secrets.")
    return True


def validate_provider_result_envelope(envelope: ProviderResultEnvelope) -> bool:
    return not scan_payload_for_secrets(envelope.model_dump())
