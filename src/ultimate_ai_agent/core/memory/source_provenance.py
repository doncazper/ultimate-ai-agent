from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


MEMORY_SOURCE_PROVENANCE_CONTRACT_REF = "contract-ref:memory-source-provenance:v1"
MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE = "untrusted_until_reviewed"

MemorySourceProvenanceKind = Literal[
    "manual_note",
    "external_assistant_review_summary",
    "local_chat_summary",
    "local_coding_summary",
    "task_plan",
    "action_proposal",
    "evidence_timeline_ref",
    "read_only_calendar_metadata_ref",
    "read_only_email_metadata_ref",
    "crm_lite_business_record",
]

MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS: list[MemorySourceProvenanceKind] = [
    "manual_note",
    "external_assistant_review_summary",
    "local_chat_summary",
    "local_coding_summary",
    "task_plan",
    "action_proposal",
    "evidence_timeline_ref",
    "read_only_calendar_metadata_ref",
    "read_only_email_metadata_ref",
    "crm_lite_business_record",
]

MEMORY_SOURCE_PROVENANCE_DENIED_CONTENT_REFS = [
    "denied-content-ref:prompt-body",
    "denied-content-ref:response-body",
    "denied-content-ref:provider-body",
    "denied-content-ref:local-path",
    "denied-content-ref:log-body",
    "denied-content-ref:account-identifier",
    "denied-content-ref:username",
    "denied-content-ref:hostname",
    "denied-content-ref:credential",
    "denied-content-ref:token",
    "denied-content-ref:private-content",
]

_DENIAL_FLAGS = [
    "source_truth_authority",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_payload_storage_allowed",
    "private_content_storage_allowed",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

_FORBIDDEN_KEY_RE = re.compile(
    r"(raw|transcript|prompt|response|source[_-]?text|source[_-]?content|"
    r"private[_-]?connector|participant|person[_-]?name|account[_-]?id|"
    r"email[_-]?address|username|hostname|local[_-]?path|path|log|"
    r"environment|env[_-]?dump|credential|password|token|secret|api[_-]?key|"
    r"authorization|bearer|oauth|session|cookie|provider[_-]?payload|"
    r"model[_-]?output)",
    re.IGNORECASE,
)

_FORBIDDEN_VALUE_RE = re.compile(
    r"(@|/users/|/home/|/var/|/etc/|[a-z]:\\|\braw\s+transcript\b|"
    r"\braw[_-]?prompt\b|\braw[_-]?response\b|\bprompt\s*:|"
    r"\bresponse\s*:|\bsource\s+text\b|\bsource\s+content\b|"
    r"\bprivate\s+connector\b|\bparticipant\s*:|\bperson\s*:|"
    r"\busername\s*:|\bhostname\s*:|\blog\s*:|\benv(?:ironment)?\s+dump\b|"
    r"provider[_-]?payload|model[_-]?output|api[_-]?key|password|token|"
    r"secret|bearer|oauth|cookie|account[_-]?id|account identifier)",
    re.IGNORECASE,
)


def _kind_ref(source_kind: str) -> str:
    return f"memory-source-kind:{source_kind.replace('_', '-')}"


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    if _FORBIDDEN_VALUE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe memory source provenance text")


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _validate_no_forbidden_payload(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        if value:
            _safe_text(value, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_no_forbidden_payload(item, field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if _FORBIDDEN_KEY_RE.search(key_text):
                raise ValueError(f"{field_name} contains unsafe memory source key")
            _validate_no_forbidden_payload(item, field_name)


class MemorySourceProvenanceRef(BaseModel):
    contract_ref: str = Field(default=MEMORY_SOURCE_PROVENANCE_CONTRACT_REF)
    source_ref: str = Field(..., min_length=1)
    source_kind: MemorySourceProvenanceKind
    provenance_ref: str = Field(..., min_length=1)
    safe_label: str | None = Field(default=None, max_length=120)
    redacted_summary_ref: str | None = Field(default=None, max_length=120)
    evidence_refs: list[str] = Field(default_factory=list)
    source_readiness_refs: list[str] = Field(default_factory=list)
    review_required: bool = True
    trust_posture: str = Field(default=MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE)
    redaction_status: str = Field(default="redacted_summary_only")
    stale_state: str = Field(default="recheck_source_refs_before_memory_use")
    authority_boundary: str = Field(
        default=(
            "Memory source provenance is review-only; source refs do not grant "
            "truth, write, context injection, connector, account, or release authority."
        ),
        min_length=1,
        max_length=240,
    )
    blocked_states: list[str] = Field(
        default_factory=lambda: [
            "no_memory_write",
            "no_context_injection",
            "no_connector_runtime",
            "no_account_auth",
            "no_model_provider_authority",
            "no_public_beta_or_production_authority",
        ]
    )
    reason_codes: list[str] = Field(
        default_factory=lambda: [
            "MEMORY_SOURCE_REVIEW_REQUIRED",
            "MEMORY_SOURCE_SAFE_REFS_ONLY",
            "MEMORY_SOURCE_UNTRUSTED_UNTIL_REVIEWED",
        ]
    )
    source_truth_authority: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    provider_or_model_authority_allowed: bool = False
    source_payload_storage_allowed: bool = False
    private_content_storage_allowed: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_source_provenance(self) -> "MemorySourceProvenanceRef":
        if self.contract_ref != MEMORY_SOURCE_PROVENANCE_CONTRACT_REF:
            raise ValueError("memory source provenance contract ref drifted")
        if not self.safe_label and not self.redacted_summary_ref:
            raise ValueError("safe_label or redacted_summary_ref is required")
        if self.redacted_summary_ref:
            _safe_ref(self.redacted_summary_ref, "redacted_summary_ref")
        if self.safe_label:
            _safe_text(self.safe_label, "safe_label")
        _safe_ref(self.source_ref, "source_ref")
        _safe_ref(self.provenance_ref, "provenance_ref")
        _safe_refs(self.evidence_refs, "evidence_refs")
        _safe_refs(self.source_readiness_refs, "source_readiness_refs")
        for blocked_state in self.blocked_states:
            _safe_text(blocked_state, "blocked_state")
        for reason_code in self.reason_codes:
            _safe_text(reason_code, "reason_code")
        if self.review_required is not True:
            raise ValueError("memory source provenance requires review")
        if self.trust_posture != MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE:
            raise ValueError("memory source provenance is untrusted until reviewed")
        for flag in _DENIAL_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by memory source provenance")
        _validate_no_forbidden_payload(
            {
                "source_kind": self.source_kind,
                "safe_label": self.safe_label,
                "redacted_summary_ref": self.redacted_summary_ref,
                "authority_boundary": self.authority_boundary,
                "stale_state": self.stale_state,
                "reason_codes": self.reason_codes,
            },
            "memory_source_provenance",
        )
        return self


def build_memory_source_provenance_ref(
    *,
    source_ref: str,
    source_kind: MemorySourceProvenanceKind,
    provenance_ref: str,
    safe_label: str | None = None,
    redacted_summary_ref: str | None = None,
    evidence_refs: list[str] | None = None,
    source_readiness_refs: list[str] | None = None,
) -> MemorySourceProvenanceRef:
    return MemorySourceProvenanceRef(
        source_ref=source_ref,
        source_kind=source_kind,
        provenance_ref=provenance_ref,
        safe_label=safe_label,
        redacted_summary_ref=redacted_summary_ref,
        evidence_refs=evidence_refs or [],
        source_readiness_refs=source_readiness_refs or [],
    )


def validate_memory_source_provenance_ref(
    source: MemorySourceProvenanceRef,
) -> bool:
    MemorySourceProvenanceRef(**source.model_dump())
    return True


def memory_source_provenance_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_kind": source_kind,
            "source_kind_ref": _kind_ref(source_kind),
            "safe_ref_prefix": _source_prefix(source_kind),
            "safe_summary_required": True,
            "review_required": True,
            "trusted_without_review": False,
            "source_payload_storage_allowed": False,
            "automatic_memory_write_allowed": False,
            "context_injection_allowed": False,
            "connector_runtime_allowed": False,
            "provider_or_model_authority_allowed": False,
            "account_auth_allowed": False,
        }
        for source_kind in MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS
    ]


def memory_source_provenance_review_posture() -> dict[str, Any]:
    return {
        "review_required_before_recall": True,
        "source_summary_trusted_without_review": False,
        "external_assistant_summary_trusted_without_review": False,
        "local_model_summary_trusted_without_review": False,
        "automatic_memory_write_enabled": False,
        "hidden_context_injection_enabled": False,
        "connector_runtime_enabled": False,
        "account_auth_enabled": False,
        "provider_or_model_authority_allowed": False,
        "source_payload_storage_allowed": False,
        "private_content_storage_allowed": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_authority_enabled": False,
    }


__all__ = [
    "MEMORY_SOURCE_PROVENANCE_CONTRACT_REF",
    "MEMORY_SOURCE_PROVENANCE_DENIED_CONTENT_REFS",
    "MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS",
    "MEMORY_SOURCE_PROVENANCE_TRUST_POSTURE",
    "MemorySourceProvenanceKind",
    "MemorySourceProvenanceRef",
    "build_memory_source_provenance_ref",
    "memory_source_provenance_policy_rows",
    "memory_source_provenance_review_posture",
    "validate_memory_source_provenance_ref",
]
