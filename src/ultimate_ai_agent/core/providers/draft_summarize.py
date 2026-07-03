from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.providers.invocation import (
    TinyProviderInvocationAdapter,
    TinyProviderInvocationReceiptStore,
    TinyProviderInvocationRequest,
    TinyProviderInvocationStatus,
    evaluate_tiny_provider_invocation,
)


PROVIDER_DRAFT_SUMMARIZE_LANE_REF = (
    "provider-draft-summarize-lane:exact-approved:v1"
)
PROVIDER_DRAFT_SUMMARIZE_CLI_REF = (
    "python scripts/inspect_provider_draft_summarize_lane.py"
)
PROVIDER_DRAFT_SUMMARIZE_PROOF_REF = "proof-ref:provider-draft-summarize:exact"
PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF = (
    "safe-disable-ref:provider-draft-summarize:disable-exact-lane"
)
PROVIDER_DRAFT_SUMMARIZE_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:provider-draft-summarize:no-autonomous-provider-call",
    "blocked-state:provider-draft-summarize:no-model-output-truth",
    "blocked-state:provider-draft-summarize:no-action-execution",
    "blocked-state:provider-draft-summarize:no-memory-write",
    "blocked-state:provider-draft-summarize:no-context-injection",
    "blocked-state:provider-draft-summarize:no-connector-write",
    "blocked-state:provider-draft-summarize:no-background-execution",
    "blocked-state:provider-draft-summarize:no-production-authority",
)


class ProviderDraftSummarizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_ref: str = Field(..., min_length=1)
    source_context_ref: str = Field(..., min_length=1)
    safe_prompt_envelope_ref: str = Field(..., min_length=1)
    operator_intent_ref: str = Field(..., min_length=1)
    purpose: Literal["summarize", "classify", "draft"] = "summarize"
    tiny_provider_request: TinyProviderInvocationRequest

    @model_validator(mode="after")
    def request_must_be_safe_refs_only(self) -> "ProviderDraftSummarizeRequest":
        for field_name in (
            "draft_ref",
            "source_context_ref",
            "safe_prompt_envelope_ref",
            "operator_intent_ref",
        ):
            validate_execution_ref(getattr(self, field_name), field_name)
        return self


class ProviderDraftSummarizeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "provider-draft-summarize-result.v1"
    lane_ref: str = PROVIDER_DRAFT_SUMMARIZE_LANE_REF
    cli_ref: str = PROVIDER_DRAFT_SUMMARIZE_CLI_REF
    proof_ref: str = PROVIDER_DRAFT_SUMMARIZE_PROOF_REF
    status: Literal[
        "draft_ready",
        "provider_receipt_recorded_preview_unavailable",
        "blocked",
    ]
    draft_ref: str
    source_context_ref: str
    safe_prompt_envelope_ref: str
    operator_intent_ref: str
    purpose: Literal["summarize", "classify", "draft"]
    provider_decision_ref: str
    provider_invocation_status: str
    provider_invocation_allowed: bool
    provider_invocation_receipt_ref: str | None = None
    provider_ref: str
    model_ref: str
    credential_ref: str
    approval_ref: str
    approval_scope_ref: str
    cost_estimate_ref: str
    budget_decision_ref: str
    max_approved_usd_ref: str
    idempotency_ref: str
    redacted_input_summary_ref: str
    redacted_output_summary_ref: str
    draft_preview_ref: str
    redacted_draft_preview: str | None = Field(default=None, max_length=2048)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(
        default_factory=lambda: [PROVIDER_DRAFT_SUMMARIZE_SAFE_DISABLE_REF]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(PROVIDER_DRAFT_SUMMARIZE_BLOCKED_AUTHORITY_REFS)
    )
    authority_posture: str = (
        "Exact-approved provider/model call may create only a local draft/proposal "
        "preview for operator review; model output is not truth or action authority."
    )
    next_safe_action: str = (
        "Review the draft preview manually; approve a separate exact lane before any "
        "send, write, memory update, context injection, or action execution."
    )
    output_is_draft_only: bool = True
    model_output_authoritative: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_exchange_persisted: bool = False
    provider_sdk_call_enabled: bool = False
    autonomous_provider_call_enabled: bool = False
    background_execution_enabled: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    connector_write_performed: bool = False
    action_execution_performed: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def result_must_stay_draft_only(self) -> "ProviderDraftSummarizeResult":
        for ref in [
            self.lane_ref,
            self.proof_ref,
            self.draft_ref,
            self.source_context_ref,
            self.safe_prompt_envelope_ref,
            self.operator_intent_ref,
            self.provider_decision_ref,
            self.provider_ref,
            self.model_ref,
            self.credential_ref,
            self.approval_ref,
            self.approval_scope_ref,
            self.cost_estimate_ref,
            self.budget_decision_ref,
            self.max_approved_usd_ref,
            self.idempotency_ref,
            self.redacted_input_summary_ref,
            self.redacted_output_summary_ref,
            self.draft_preview_ref,
        ]:
            validate_execution_ref(ref, "provider_draft_ref")
        validate_safe_execution_text(self.cli_ref, "cli_ref")
        if self.provider_invocation_receipt_ref is not None:
            validate_execution_ref(
                self.provider_invocation_receipt_ref,
                "provider_invocation_receipt_ref",
            )
        for field_name in (
            "receipt_refs",
            "evidence_refs",
            "audit_refs",
            "safe_disable_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.authority_posture, "authority_posture")
        validate_safe_execution_text(self.next_safe_action, "next_safe_action")
        if self.redacted_draft_preview is not None:
            validate_safe_execution_text(
                self.redacted_draft_preview,
                "redacted_draft_preview",
            )
        denied_flags = [
            self.model_output_authoritative,
            self.raw_prompt_persisted,
            self.raw_response_persisted,
            self.raw_provider_exchange_persisted,
            self.provider_sdk_call_enabled,
            self.autonomous_provider_call_enabled,
            self.background_execution_enabled,
            self.memory_write_performed,
            self.context_injection_performed,
            self.connector_write_performed,
            self.action_execution_performed,
            self.production_authority_granted,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_DRAFT_SUMMARIZE_AUTHORITY_DENIED")
        if not self.output_is_draft_only:
            raise ValueError("PROVIDER_DRAFT_SUMMARIZE_OUTPUT_MUST_BE_DRAFT")
        if self.status == "draft_ready":
            if not self.provider_invocation_allowed:
                raise ValueError("PROVIDER_DRAFT_SUMMARIZE_READY_REQUIRES_PROVIDER")
            if not self.provider_invocation_receipt_ref:
                raise ValueError("PROVIDER_DRAFT_SUMMARIZE_READY_REQUIRES_RECEIPT")
            if self.redacted_draft_preview is None:
                raise ValueError("PROVIDER_DRAFT_SUMMARIZE_READY_REQUIRES_PREVIEW")
        return self

    def durable_record(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude={"redacted_draft_preview"})
        payload["draft_preview_storage"] = "omitted_returned_to_requester_only"
        return payload


def evaluate_provider_draft_summarize(
    request: ProviderDraftSummarizeRequest,
    *,
    adapter: TinyProviderInvocationAdapter | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    receipt_store: TinyProviderInvocationReceiptStore | None = None,
) -> ProviderDraftSummarizeResult:
    decision = evaluate_tiny_provider_invocation(
        request.tiny_provider_request,
        adapter=adapter,
        approval_authority=approval_authority,
        receipt_store=receipt_store,
    )
    receipt = decision.receipt
    preview = decision.redacted_output_preview
    status: Literal[
        "draft_ready",
        "provider_receipt_recorded_preview_unavailable",
        "blocked",
    ]
    if decision.allowed and preview:
        status = "draft_ready"
    elif decision.allowed:
        status = "provider_receipt_recorded_preview_unavailable"
    else:
        status = "blocked"

    receipt_ref = receipt.receipt_ref if receipt else None
    return ProviderDraftSummarizeResult(
        status=status,
        draft_ref=request.draft_ref,
        source_context_ref=request.source_context_ref,
        safe_prompt_envelope_ref=request.safe_prompt_envelope_ref,
        operator_intent_ref=request.operator_intent_ref,
        purpose=request.purpose,
        provider_decision_ref=decision.decision_ref,
        provider_invocation_status=decision.status.value
        if isinstance(decision.status, TinyProviderInvocationStatus)
        else str(decision.status),
        provider_invocation_allowed=decision.allowed,
        provider_invocation_receipt_ref=receipt_ref,
        provider_ref=request.tiny_provider_request.provider_ref,
        model_ref=request.tiny_provider_request.model_ref,
        credential_ref=request.tiny_provider_request.credential_ref,
        approval_ref=request.tiny_provider_request.approval_ref,
        approval_scope_ref=request.tiny_provider_request.approval_scope_ref,
        cost_estimate_ref=request.tiny_provider_request.cost_estimate_ref,
        budget_decision_ref=request.tiny_provider_request.budget_decision_ref,
        max_approved_usd_ref=request.tiny_provider_request.max_approved_usd_ref,
        idempotency_ref=request.tiny_provider_request.idempotency_ref,
        redacted_input_summary_ref=(
            request.tiny_provider_request.redacted_input_summary_ref
        ),
        redacted_output_summary_ref=(
            request.tiny_provider_request.redacted_output_summary_ref
        ),
        draft_preview_ref=(
            f"provider-draft-preview-ref:{_short_digest(preview)}"
            if preview
            else "provider-draft-preview-ref:omitted"
        ),
        redacted_draft_preview=preview,
        receipt_refs=[receipt_ref] if receipt_ref else [],
        evidence_refs=[
            request.source_context_ref,
            request.safe_prompt_envelope_ref,
            request.tiny_provider_request.cost_estimate_ref,
            request.tiny_provider_request.budget_decision_ref,
        ],
        audit_refs=[
            request.tiny_provider_request.approval_ref,
            request.tiny_provider_request.idempotency_ref,
        ],
    )


def _short_digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()[:16]
