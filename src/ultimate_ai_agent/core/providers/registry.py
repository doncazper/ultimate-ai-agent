from typing import Dict, List, Optional

from ultimate_ai_agent.core.providers.enums import ProviderCapability, ProviderDomain, ProviderStatus
from ultimate_ai_agent.core.providers.manifests import ProviderManifest
from ultimate_ai_agent.core.providers.validation import validate_provider_manifest


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ProviderManifest] = {}

    def register_provider(self, manifest: ProviderManifest) -> None:
        validate_provider_manifest(manifest)
        self._providers[manifest.provider_id] = manifest

    def get_provider(self, provider_id: str) -> Optional[ProviderManifest]:
        return self._providers.get(provider_id)

    def list_providers(
        self,
        domain: Optional[ProviderDomain] = None,
        capability: Optional[ProviderCapability] = None,
        status: Optional[ProviderStatus] = None,
    ) -> List[ProviderManifest]:
        providers = list(self._providers.values())
        if domain is not None:
            providers = [p for p in providers if p.domain == domain]
        if capability is not None:
            providers = [p for p in providers if capability in p.capabilities]
        if status is not None:
            providers = [p for p in providers if p.status == status]
        return providers

    def validate_provider(self, manifest: ProviderManifest) -> bool:
        return validate_provider_manifest(manifest)
