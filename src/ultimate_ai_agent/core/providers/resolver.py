from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.providers.enums import (
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderStatus,
)
from ultimate_ai_agent.core.providers.manifests import ProviderManifest, ProviderSelectionPolicy
from ultimate_ai_agent.core.providers.registry import ProviderRegistry


class ProviderResolutionDecision(BaseModel):
    selected_provider_id: Optional[str] = None
    candidate_provider_ids: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str

    model_config = ConfigDict(extra="forbid")


class ProviderResolver:
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def resolve(
        self,
        domain: ProviderDomain,
        capability: ProviderCapability,
        policy: ProviderSelectionPolicy,
        credential_availability: Optional[Dict[str, bool]] = None,
    ) -> ProviderResolutionDecision:
        providers = self.registry.list_providers(domain=domain, capability=capability)
        candidates: List[ProviderManifest] = []
        reasons: List[str] = []

        for provider in providers:
            if provider.status != ProviderStatus.enabled:
                reasons.append("PROVIDER_NOT_ENABLED")
                continue
            if provider.cost_class == ProviderCostClass.paid and not policy.allow_paid:
                reasons.append("PAID_PROVIDER_DISALLOWED")
                continue
            if provider.cost_class == ProviderCostClass.enterprise and not policy.allow_enterprise:
                reasons.append("ENTERPRISE_PROVIDER_DISALLOWED")
                continue
            if provider.cost_class == ProviderCostClass.self_hosted and not policy.allow_self_hosted:
                reasons.append("SELF_HOSTED_PROVIDER_DISALLOWED")
                continue
            if self._requires_credential(provider):
                if not provider.credential_ref:
                    reasons.append("CREDENTIAL_REF_REQUIRED")
                    continue
                if credential_availability is not None and not credential_availability.get(provider.credential_ref, False):
                    reasons.append("CREDENTIAL_NOT_AVAILABLE")
                    continue
            candidates.append(provider)

        candidates.sort(key=lambda p: (self._cost_rank(p.cost_class), p.default_priority, p.provider_id))
        if not candidates:
            return ProviderResolutionDecision(
                selected_provider_id=None,
                candidate_provider_ids=[],
                reason_codes=sorted(set(reasons)) or ["NO_PROVIDER_AVAILABLE"],
                safe_message="No provider matched the selection policy.",
            )

        selected = candidates[0]
        reason = "SELECTED_PROVIDER"
        if selected.cost_class == ProviderCostClass.free_no_key and selected.auth_requirement == ProviderAuthRequirement.none:
            reason = "SELECTED_FREE_NO_KEY"
        elif selected.cost_class == ProviderCostClass.free_with_key:
            reason = "SELECTED_FREE_WITH_KEY"
        elif selected.cost_class == ProviderCostClass.paid:
            reason = "SELECTED_PAID_PROVIDER"

        return ProviderResolutionDecision(
            selected_provider_id=selected.provider_id,
            candidate_provider_ids=[provider.provider_id for provider in candidates],
            reason_codes=[reason],
            safe_message="Provider selected by deterministic policy.",
        )

    @staticmethod
    def _requires_credential(provider: ProviderManifest) -> bool:
        return provider.auth_requirement in [
            ProviderAuthRequirement.required_key,
            ProviderAuthRequirement.oauth_required,
            ProviderAuthRequirement.service_account_required,
        ] or provider.cost_class == ProviderCostClass.free_with_key

    @staticmethod
    def _cost_rank(cost_class: ProviderCostClass) -> int:
        return {
            ProviderCostClass.free_no_key: 0,
            ProviderCostClass.free_with_key: 1,
            ProviderCostClass.self_hosted: 2,
            ProviderCostClass.paid: 3,
            ProviderCostClass.enterprise: 4,
        }[cost_class]
