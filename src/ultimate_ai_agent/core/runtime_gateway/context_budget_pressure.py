from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_CONTEXT_BUDGET_PRESSURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-context-budget-pressure:v1"
)
RUNTIME_CONTEXT_BUDGET_PRESSURE_ROUTE_REF = "GET /api/runtime/context-budget-pressure"
RUNTIME_CONTEXT_BUDGET_PRESSURE_CLI_REF = "uaa runtime inspect-context-budget-pressure"
RUNTIME_CONTEXT_BUDGET_PRESSURE_SNAPSHOT_REF = (
    "context-budget-pressure-snapshot-ref:runtime:budget-posture"
)
RUNTIME_CONTEXT_BUDGET_PRESSURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-24:context-budget-pressure"
)

RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:context-budget-no-hidden-compression",
    "blocked-authority:context-budget-no-automatic-context-mutation",
    "blocked-authority:context-budget-no-model-summarization-call",
    "blocked-authority:context-budget-no-raw-context-persistence",
    "blocked-authority:context-budget-no-raw-prompt-persistence",
    "blocked-authority:context-budget-no-raw-response-persistence",
    "blocked-authority:context-budget-no-provider-payload-persistence",
    "blocked-authority:context-budget-no-context-injection",
    "blocked-authority:context-budget-no-provider-sdk-call",
    "blocked-authority:context-budget-no-cache-write",
    "blocked-authority:context-budget-no-production-authority",
]


class RuntimeContextBudgetPressureLevel(str, Enum):
    within_budget = "within_budget"
    warning = "warning"
    critical = "critical"
    blocked = "blocked"


class RuntimeContextBudgetProposalKind(str, Enum):
    trim_context_refs = "trim_context_refs"
    request_operator_choice = "request_operator_choice"
    summarize_with_approval = "summarize_with_approval"
    defer_context = "defer_context"


class RuntimeContextBudgetSegment(BaseModel):
    segment_ref: str
    display_label: str
    source_ref: str
    source_route_ref: str
    budget_bucket_ref: str
    pressure_level: RuntimeContextBudgetPressureLevel
    safe_summary: str
    token_estimate: int = Field(..., ge=0)
    token_budget_limit: int = Field(..., ge=1)
    token_budget_remaining: int
    warning_refs: list[str] = Field(default_factory=list)
    proposal_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    hidden_compression_enabled: bool = False
    automatic_context_mutation_enabled: bool = False
    model_summarization_call_performed: bool = False
    summary_receipt_created: bool = False
    raw_context_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    context_injection_performed: bool = False
    provider_sdk_call_performed: bool = False
    cache_write_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_segment(self) -> "RuntimeContextBudgetSegment":
        for value, field_name in [
            (self.segment_ref, "segment_ref"),
            (self.source_ref, "source_ref"),
            (self.budget_bucket_ref, "budget_bucket_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "warning_refs",
            "proposal_refs",
            "evidence_refs",
            "proof_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (self.source_route_ref, "source_route_ref"),
            (str(self.pressure_level), "pressure_level"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.token_budget_remaining != self.token_budget_limit - self.token_estimate:
            raise ValueError("RUNTIME_CONTEXT_BUDGET_SEGMENT_REMAINING_MISMATCH")
        if self.pressure_level != RuntimeContextBudgetPressureLevel.within_budget.value:
            if not self.warning_refs:
                raise ValueError("RUNTIME_CONTEXT_BUDGET_WARNING_REF_REQUIRED")
            if not self.proposal_refs:
                raise ValueError("RUNTIME_CONTEXT_BUDGET_PROPOSAL_REF_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_CONTEXT_BUDGET_SEGMENT_BLOCKERS_REQUIRED")
        denied_flags = {
            "hidden_compression_enabled": self.hidden_compression_enabled,
            "automatic_context_mutation_enabled": (
                self.automatic_context_mutation_enabled
            ),
            "model_summarization_call_performed": (
                self.model_summarization_call_performed
            ),
            "summary_receipt_created": self.summary_receipt_created,
            "raw_context_persisted": self.raw_context_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "context_injection_performed": self.context_injection_performed,
            "provider_sdk_call_performed": self.provider_sdk_call_performed,
            "cache_write_performed": self.cache_write_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CONTEXT_BUDGET_SEGMENT_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeContextBudgetProposal(BaseModel):
    proposal_ref: str
    proposal_kind: RuntimeContextBudgetProposalKind
    target_segment_ref: str
    display_label: str
    safe_summary: str
    expected_token_delta: int
    approval_required: bool = True
    source_coverage_required: bool = True
    retrieval_log_required: bool = True
    summary_receipt_required: bool = True
    source_refs: list[str] = Field(default_factory=list)
    retrieval_log_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    auto_applied: bool = False
    hidden_compression_performed: bool = False
    automatic_context_mutation_performed: bool = False
    model_summarization_call_performed: bool = False
    summary_receipt_created: bool = False
    raw_context_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    context_injection_performed: bool = False
    provider_sdk_call_performed: bool = False
    cache_write_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "RuntimeContextBudgetProposal":
        for value, field_name in [
            (self.proposal_ref, "proposal_ref"),
            (self.target_segment_ref, "target_segment_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "source_refs",
            "retrieval_log_refs",
            "proof_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (str(self.proposal_kind), "proposal_kind"),
            (self.display_label, "display_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for required, name in [
            (self.approval_required, "approval_required"),
            (self.source_coverage_required, "source_coverage_required"),
            (self.retrieval_log_required, "retrieval_log_required"),
            (self.summary_receipt_required, "summary_receipt_required"),
        ]:
            if required is not True:
                raise ValueError(f"RUNTIME_CONTEXT_BUDGET_{name.upper()}_DENIED")
        if not self.source_refs:
            raise ValueError("RUNTIME_CONTEXT_BUDGET_PROPOSAL_SOURCE_REFS_REQUIRED")
        if not self.retrieval_log_refs:
            raise ValueError(
                "RUNTIME_CONTEXT_BUDGET_PROPOSAL_RETRIEVAL_LOG_REQUIRED"
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_CONTEXT_BUDGET_PROPOSAL_BLOCKERS_REQUIRED")
        denied_flags = {
            "auto_applied": self.auto_applied,
            "hidden_compression_performed": self.hidden_compression_performed,
            "automatic_context_mutation_performed": (
                self.automatic_context_mutation_performed
            ),
            "model_summarization_call_performed": (
                self.model_summarization_call_performed
            ),
            "summary_receipt_created": self.summary_receipt_created,
            "raw_context_persisted": self.raw_context_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "context_injection_performed": self.context_injection_performed,
            "provider_sdk_call_performed": self.provider_sdk_call_performed,
            "cache_write_performed": self.cache_write_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CONTEXT_BUDGET_PROPOSAL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeContextBudgetPressureReadModel(BaseModel):
    schema_version: str = "runtime_context_budget_pressure.v1"
    contract_ref: str = RUNTIME_CONTEXT_BUDGET_PRESSURE_CONTRACT_REF
    status: str = "read_only_context_budget_pressure_posture"
    snapshot_ref: str = RUNTIME_CONTEXT_BUDGET_PRESSURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-context-budget:pending"
    route_ref: str = RUNTIME_CONTEXT_BUDGET_PRESSURE_ROUTE_REF
    cli_ref: str = RUNTIME_CONTEXT_BUDGET_PRESSURE_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Context budget pressure exposes safe budget estimates, warning refs, and "
        "operator-review trimming proposals without hidden compression or mutation."
    )
    pressure_level: RuntimeContextBudgetPressureLevel
    token_budget_limit: int = Field(..., ge=1)
    estimated_token_count: int = Field(..., ge=0)
    token_budget_remaining: int
    pressure_ratio: float
    segments: list[RuntimeContextBudgetSegment]
    proposals: list[RuntimeContextBudgetProposal]
    segment_count: int = 0
    proposal_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    trimming_proposal_count: int = 0
    summarization_proposal_count: int = 0
    ask_operator_proposal_count: int = 0
    blocked_hidden_compression_label: str = "blocked"
    compression_proposal_required: bool = True
    operator_approval_required: bool = True
    source_coverage_required: bool = True
    retrieval_log_required: bool = True
    summary_receipt_required: bool = True
    hidden_compression_enabled: bool = False
    automatic_context_mutation_enabled: bool = False
    model_summarization_enabled: bool = False
    raw_context_persistence_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    provider_payload_persistence_enabled: bool = False
    context_injection_enabled: bool = False
    provider_sdk_enabled: bool = False
    cache_write_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_context_omitted",
                "raw_prompts_omitted",
                "raw_responses_omitted",
                "provider_payloads_omitted",
                "summaries_omitted_until_approved",
            ]
        )
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeContextBudgetPressureReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
            (str(self.pressure_level), "pressure_level"),
            (self.blocked_hidden_compression_label, "blocked_hidden_compression_label"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.token_budget_remaining != (
            self.token_budget_limit - self.estimated_token_count
        ):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_REMAINING_MISMATCH")
        if self.segment_count != len(self.segments):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_SEGMENT_COUNT_MISMATCH")
        if self.proposal_count != len(self.proposals):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_PROPOSAL_COUNT_MISMATCH")
        if self.warning_count != len(
            [
                segment
                for segment in self.segments
                if segment.pressure_level
                == RuntimeContextBudgetPressureLevel.warning.value
            ]
        ):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_WARNING_COUNT_MISMATCH")
        if self.critical_count != len(
            [
                segment
                for segment in self.segments
                if segment.pressure_level
                == RuntimeContextBudgetPressureLevel.critical.value
            ]
        ):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_CRITICAL_COUNT_MISMATCH")
        kind_counts = {
            RuntimeContextBudgetProposalKind.trim_context_refs.value: (
                self.trimming_proposal_count
            ),
            RuntimeContextBudgetProposalKind.summarize_with_approval.value: (
                self.summarization_proposal_count
            ),
            RuntimeContextBudgetProposalKind.request_operator_choice.value: (
                self.ask_operator_proposal_count
            ),
        }
        for proposal_kind, expected_count in kind_counts.items():
            actual = len(
                [
                    proposal
                    for proposal in self.proposals
                    if proposal.proposal_kind == proposal_kind
                ]
            )
            if expected_count != actual:
                raise ValueError("RUNTIME_CONTEXT_BUDGET_PROPOSAL_KIND_MISMATCH")
        for required, name in [
            (self.compression_proposal_required, "compression_proposal_required"),
            (self.operator_approval_required, "operator_approval_required"),
            (self.source_coverage_required, "source_coverage_required"),
            (self.retrieval_log_required, "retrieval_log_required"),
            (self.summary_receipt_required, "summary_receipt_required"),
        ]:
            if required is not True:
                raise ValueError(f"RUNTIME_CONTEXT_BUDGET_{name.upper()}_DENIED")
        denied_flags = {
            "hidden_compression_enabled": self.hidden_compression_enabled,
            "automatic_context_mutation_enabled": (
                self.automatic_context_mutation_enabled
            ),
            "model_summarization_enabled": self.model_summarization_enabled,
            "raw_context_persistence_enabled": self.raw_context_persistence_enabled,
            "raw_prompt_persistence_enabled": self.raw_prompt_persistence_enabled,
            "raw_response_persistence_enabled": self.raw_response_persistence_enabled,
            "provider_payload_persistence_enabled": (
                self.provider_payload_persistence_enabled
            ),
            "context_injection_enabled": self.context_injection_enabled,
            "provider_sdk_enabled": self.provider_sdk_enabled,
            "cache_write_enabled": self.cache_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CONTEXT_BUDGET_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if RUNTIME_CONTEXT_BUDGET_PRESSURE_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_CONTEXT_BUDGET_PROOF_REQUIRED")
        if set(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_CONTEXT_BUDGET_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-context-budget:{digest}"


def _segment(
    *,
    slug: str,
    display_label: str,
    source_ref: str,
    source_route_ref: str,
    token_estimate: int,
    token_budget_limit: int,
    pressure_level: RuntimeContextBudgetPressureLevel,
    safe_summary: str,
    proposal_refs: list[str],
) -> RuntimeContextBudgetSegment:
    warnings = (
        [f"warning-ref:context-budget:{slug}:{pressure_level.value}"]
        if pressure_level != RuntimeContextBudgetPressureLevel.within_budget
        else []
    )
    return RuntimeContextBudgetSegment(
        segment_ref=f"context-budget-segment-ref:{slug}",
        display_label=display_label,
        source_ref=source_ref,
        source_route_ref=source_route_ref,
        budget_bucket_ref=f"context-budget-bucket-ref:{slug}",
        pressure_level=pressure_level,
        safe_summary=safe_summary,
        token_estimate=token_estimate,
        token_budget_limit=token_budget_limit,
        token_budget_remaining=token_budget_limit - token_estimate,
        warning_refs=warnings,
        proposal_refs=proposal_refs,
        evidence_refs=[f"evidence-ref:context-budget:{slug}"],
        proof_refs=[RUNTIME_CONTEXT_BUDGET_PRESSURE_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS),
    )


def _proposal(
    *,
    slug: str,
    proposal_kind: RuntimeContextBudgetProposalKind,
    target_segment_ref: str,
    display_label: str,
    safe_summary: str,
    expected_token_delta: int,
    source_refs: list[str],
) -> RuntimeContextBudgetProposal:
    return RuntimeContextBudgetProposal(
        proposal_ref=f"context-budget-proposal-ref:{slug}",
        proposal_kind=proposal_kind,
        target_segment_ref=target_segment_ref,
        display_label=display_label,
        safe_summary=safe_summary,
        expected_token_delta=expected_token_delta,
        source_refs=source_refs,
        retrieval_log_refs=[f"retrieval-log-ref:context-budget:{slug}"],
        proof_refs=[RUNTIME_CONTEXT_BUDGET_PRESSURE_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS),
    )


def _default_proposals() -> list[RuntimeContextBudgetProposal]:
    return [
        _proposal(
            slug="trim-low-signal-context-refs",
            proposal_kind=RuntimeContextBudgetProposalKind.trim_context_refs,
            target_segment_ref="context-budget-segment-ref:retrieval-context",
            display_label="Trim low-signal context refs",
            safe_summary=(
                "Proposal suggests removing lower-priority retrieval refs after "
                "operator review; it is not auto-applied."
            ),
            expected_token_delta=-1800,
            source_refs=[
                "context-preview-ref:runtime:governed-safe-refs",
                "why-included-ref:context-pack:low-priority",
            ],
        ),
        _proposal(
            slug="ask-operator-context-priority",
            proposal_kind=RuntimeContextBudgetProposalKind.request_operator_choice,
            target_segment_ref="context-budget-segment-ref:operator-turn",
            display_label="Ask operator for context priority",
            safe_summary=(
                "Proposal asks the operator which context refs matter before any "
                "compression or trimming lane exists."
            ),
            expected_token_delta=0,
            source_refs=[
                "turn-ref:prepared-turn:ephemeral",
                "budget-state-ref:runtime-context:warning",
            ],
        ),
        _proposal(
            slug="summarize-with-approval",
            proposal_kind=RuntimeContextBudgetProposalKind.summarize_with_approval,
            target_segment_ref="context-budget-segment-ref:durable-context",
            display_label="Summarize only with approval",
            safe_summary=(
                "Future proposal requires approval, source coverage, retrieval log, "
                "and summary receipt before any model summarization call."
            ),
            expected_token_delta=-2400,
            source_refs=[
                "context-pack-ref:prepared-turn:review-required",
                "proof-ref:runtime-context-references:phase-16",
            ],
        ),
    ]


def _default_segments() -> list[RuntimeContextBudgetSegment]:
    return [
        _segment(
            slug="stable-policy",
            display_label="Stable policy refs",
            source_ref="policy-ref:uaa:non-negotiable-invariants",
            source_route_ref="GET /api/runtime/prompt-stability-tiers",
            token_estimate=1500,
            token_budget_limit=4000,
            pressure_level=RuntimeContextBudgetPressureLevel.within_budget,
            safe_summary="Stable policy refs are within budget and cache-posture only.",
            proposal_refs=[],
        ),
        _segment(
            slug="durable-context",
            display_label="Durable context refs",
            source_ref="context-pack-ref:prepared-turn:review-required",
            source_route_ref="GET /api/runtime/context-references",
            token_estimate=5200,
            token_budget_limit=6000,
            pressure_level=RuntimeContextBudgetPressureLevel.warning,
            safe_summary=(
                "Durable context refs are near budget and require review before "
                "summarization or trimming."
            ),
            proposal_refs=["context-budget-proposal-ref:summarize-with-approval"],
        ),
        _segment(
            slug="retrieval-context",
            display_label="Retrieval context refs",
            source_ref="search-ref:runtime-session-search:sample",
            source_route_ref="GET /api/runtime/session-search",
            token_estimate=6100,
            token_budget_limit=6000,
            pressure_level=RuntimeContextBudgetPressureLevel.critical,
            safe_summary=(
                "Retrieval context refs exceed their segment budget and produce a "
                "trim proposal only."
            ),
            proposal_refs=["context-budget-proposal-ref:trim-low-signal-context-refs"],
        ),
        _segment(
            slug="operator-turn",
            display_label="Operator turn ref",
            source_ref="turn-ref:prepared-turn:ephemeral",
            source_route_ref="GET /api/turn-router/prepared-turn",
            token_estimate=2100,
            token_budget_limit=4000,
            pressure_level=RuntimeContextBudgetPressureLevel.warning,
            safe_summary=(
                "Operator turn text remains omitted; budget posture may ask for "
                "operator priority instead of compressing it."
            ),
            proposal_refs=["context-budget-proposal-ref:ask-operator-context-priority"],
        ),
    ]


def build_runtime_context_budget_pressure_read_model() -> (
    RuntimeContextBudgetPressureReadModel
):
    segments = _default_segments()
    proposals = _default_proposals()
    token_budget_limit = 16000
    estimated_token_count = sum(segment.token_estimate for segment in segments)
    model = RuntimeContextBudgetPressureReadModel(
        pressure_level=RuntimeContextBudgetPressureLevel.warning,
        token_budget_limit=token_budget_limit,
        estimated_token_count=estimated_token_count,
        token_budget_remaining=token_budget_limit - estimated_token_count,
        pressure_ratio=round(estimated_token_count / token_budget_limit, 4),
        segments=segments,
        proposals=proposals,
        segment_count=len(segments),
        proposal_count=len(proposals),
        warning_count=len(
            [
                segment
                for segment in segments
                if segment.pressure_level
                == RuntimeContextBudgetPressureLevel.warning.value
            ]
        ),
        critical_count=len(
            [
                segment
                for segment in segments
                if segment.pressure_level
                == RuntimeContextBudgetPressureLevel.critical.value
            ]
        ),
        trimming_proposal_count=len(
            [
                proposal
                for proposal in proposals
                if proposal.proposal_kind
                == RuntimeContextBudgetProposalKind.trim_context_refs.value
            ]
        ),
        summarization_proposal_count=len(
            [
                proposal
                for proposal in proposals
                if proposal.proposal_kind
                == RuntimeContextBudgetProposalKind.summarize_with_approval.value
            ]
        ),
        ask_operator_proposal_count=len(
            [
                proposal
                for proposal in proposals
                if proposal.proposal_kind
                == RuntimeContextBudgetProposalKind.request_operator_choice.value
            ]
        ),
        blocked_authority_refs=list(
            RUNTIME_CONTEXT_BUDGET_PRESSURE_BLOCKED_AUTHORITY_REFS
        ),
        proof_refs=[RUNTIME_CONTEXT_BUDGET_PRESSURE_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-24"],
        next_safe_action_refs=[
            "next-safe-action-ref:context-budget:review-trim-proposal",
            "next-safe-action-ref:context-budget:add-approved-summary-receipt-lane",
            "next-safe-action-ref:context-budget:keep-hidden-compression-blocked",
        ],
    )
    model.snapshot_hash_ref = _hash_payload(
        {
            "segments": [
                {
                    "segment_ref": segment.segment_ref,
                    "pressure_level": segment.pressure_level,
                    "token_estimate": segment.token_estimate,
                    "token_budget_limit": segment.token_budget_limit,
                    "proposal_refs": segment.proposal_refs,
                }
                for segment in segments
            ],
            "proposals": [
                {
                    "proposal_ref": proposal.proposal_ref,
                    "proposal_kind": proposal.proposal_kind,
                    "target_segment_ref": proposal.target_segment_ref,
                    "expected_token_delta": proposal.expected_token_delta,
                }
                for proposal in proposals
            ],
        }
    )
    return RuntimeContextBudgetPressureReadModel(**model.model_dump(mode="json"))
