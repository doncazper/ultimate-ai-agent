from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.recall.enums import ContextPackBuildStatus
from ultimate_ai_agent.core.recall.policy import recall_source_identity_reason_codes
from ultimate_ai_agent.core.recall.router import GroundedRecallDecision, RecallSelection
from ultimate_ai_agent.core.recall.validation import validate_safe_recall_payload, validate_safe_recall_text


class ContextPackBuildRequest(BaseModel):
    pack_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    recall_decision: GroundedRecallDecision
    max_context_tokens: int = Field(default=2000, ge=0, le=100000)
    context_injection_enabled: bool = False
    include_raw_content: bool = False
    include_model_output: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_pack_request(self) -> Any:
        if self.context_injection_enabled:
            raise ValueError("context_injection_enabled must be False in M26")
        if self.include_raw_content:
            raise ValueError("include_raw_content must be False in M26")
        if self.include_model_output:
            raise ValueError("include_model_output must be False in M26")
        for item in self.recall_decision.selected:
            if recall_source_identity_reason_codes(item.source_ref, item.source_kind):
                raise ValueError("source_ref/source_kind consistency is required for context packs")
            validate_safe_recall_payload(item.metadata, "recall_decision metadata")
            validate_safe_recall_text(item.safe_summary, "safe_summary")
        validate_safe_recall_payload(self.metadata_refs, "metadata_refs")
        validate_safe_recall_payload(self.metadata)
        return self


class EvidenceLinkedContextPack(BaseModel):
    context_pack_ref: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    status: ContextPackBuildStatus
    items: List[RecallSelection] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    token_budget_summary: str = ""
    warnings: List[str] = Field(default_factory=list)
    safe_message: str
    context_injection_performed: bool = False
    raw_content_included: bool = False
    model_output_included: bool = False
    external_retrieval_performed: bool = False
    memory_write_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_m26_pack(self) -> Any:
        if self.context_injection_performed:
            raise ValueError("M26 context packs must not inject context")
        if self.raw_content_included:
            raise ValueError("M26 context packs must not include raw content")
        if self.model_output_included:
            raise ValueError("M26 context packs must not include model output")
        if self.external_retrieval_performed:
            raise ValueError("M26 context packs must not perform external retrieval")
        if self.memory_write_performed:
            raise ValueError("M26 context packs must not write memory")
        return self


def build_evidence_linked_context_pack(request: ContextPackBuildRequest) -> EvidenceLinkedContextPack:
    items: List[RecallSelection] = []
    used_tokens = 0
    warnings: List[str] = []
    for item in request.recall_decision.selected:
        if used_tokens + item.token_estimate > request.max_context_tokens:
            warnings.append("CONTEXT_BUDGET_LIMIT_REACHED")
            continue
        used_tokens += item.token_estimate
        items.append(item)

    status = ContextPackBuildStatus.built if items else ContextPackBuildStatus.empty
    return EvidenceLinkedContextPack(
        context_pack_ref=request.pack_id,
        request_id=request.request_id,
        status=status,
        items=items,
        evidence_refs=_unique_ref_list(ref for item in items for ref in item.evidence_refs),
        event_refs=_unique_ref_list(ref for item in items for ref in item.event_refs),
        receipt_refs=_unique_ref_list(ref for item in items for ref in item.receipt_refs),
        memory_refs=_unique_ref_list(ref for item in items for ref in item.memory_refs),
        file_refs=_unique_ref_list(ref for item in items for ref in item.file_refs),
        token_budget_summary=f"{used_tokens}/{request.max_context_tokens} estimated tokens used",
        warnings=list(dict.fromkeys(warnings)),
        safe_message="Evidence-linked context pack contains safe summaries only.",
    )


def _unique_ref_list(refs: Any) -> List[str]:
    return list(dict.fromkeys(ref for ref in refs if ref))
