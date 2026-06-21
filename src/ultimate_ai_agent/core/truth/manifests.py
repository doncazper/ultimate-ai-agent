from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.truth.enums import TruthSourceKind


class TruthRouterManifest(BaseModel):
    manifest_id: str = Field(default="truth_router_manifest_m25", min_length=1)
    baseline_version: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    truth_router_enabled: bool = True
    external_verification_enabled: bool = False
    web_search_enabled: bool = False
    model_verification_enabled: bool = False
    memory_as_authority_enabled: bool = False
    automatic_claim_verification_enabled: bool = False
    supported_source_kinds: List[TruthSourceKind] = Field(default_factory=list)
    blocked_source_kinds: List[TruthSourceKind] = Field(default_factory=list)
    docs_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_disabled_authority_paths(self) -> Any:
        if self.external_verification_enabled:
            raise ValueError("External verification is not implemented in M25.")
        if self.web_search_enabled:
            raise ValueError("Web search is not implemented in M25.")
        if self.model_verification_enabled:
            raise ValueError("Model verification is not implemented in M25.")
        if self.memory_as_authority_enabled:
            raise ValueError("Memory cannot be truth authority in M25.")
        if self.automatic_claim_verification_enabled:
            raise ValueError("Automatic claim verification is not implemented in M25.")
        return self


def build_truth_router_manifest(baseline_version: str = "0.29.0") -> TruthRouterManifest:
    return TruthRouterManifest(
        baseline_version=baseline_version,
        supported_source_kinds=[
            TruthSourceKind.canonical_document,
            TruthSourceKind.evidence_manifest,
            TruthSourceKind.receipt,
            TruthSourceKind.event_ledger,
            TruthSourceKind.user_reviewed_source,
            TruthSourceKind.source_linked_memory,
            TruthSourceKind.reviewed_memory,
        ],
        blocked_source_kinds=[
            TruthSourceKind.unreviewed_memory,
            TruthSourceKind.model_output,
            TruthSourceKind.runtime_output,
            TruthSourceKind.openwebui_output,
            TruthSourceKind.unknown,
        ],
        docs_refs=[
            "docs/truth/TRUTH_SOURCE_ROUTER.md",
            "docs/truth/EVIDENCE_CLAIM_CHECKER.md",
            "docs/truth/CLAIM_VERIFICATION_POLICY.md",
        ],
        warnings=[
            "M25 validates provided evidence refs only.",
            "Memory is recall, not authority.",
            "Model/runtime/OpenWebUI output cannot verify truth.",
        ],
    )
