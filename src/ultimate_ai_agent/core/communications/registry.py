from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType

from ultimate_ai_agent.core.communications.contracts import (
    COMMUNICATIONS_MAX_PROVIDERS,
    CommunicationsProviderDescriptor,
)


class CommunicationsProviderRegistry:
    """Immutable adapter-declaration registry; it never resolves callable authority."""

    def __init__(self, descriptors: Iterable[CommunicationsProviderDescriptor]) -> None:
        by_ref: dict[str, CommunicationsProviderDescriptor] = {}
        for descriptor in descriptors:
            if len(by_ref) >= COMMUNICATIONS_MAX_PROVIDERS:
                raise ValueError("COMMUNICATIONS_PROVIDER_LIMIT_EXCEEDED")
            if descriptor.provider_ref in by_ref:
                raise ValueError("COMMUNICATIONS_PROVIDER_REF_DUPLICATE")
            by_ref[descriptor.provider_ref] = descriptor.model_copy(deep=True)
        self._by_ref = MappingProxyType(by_ref)

    def list_descriptors(self) -> tuple[CommunicationsProviderDescriptor, ...]:
        return tuple(
            self._by_ref[provider_ref].model_copy(deep=True)
            for provider_ref in sorted(self._by_ref)
        )

    def inspect(self, provider_ref: str) -> CommunicationsProviderDescriptor:
        try:
            return self._by_ref[provider_ref].model_copy(deep=True)
        except KeyError as exc:
            raise KeyError("COMMUNICATIONS_PROVIDER_REF_UNKNOWN") from exc
