from __future__ import annotations

from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


FCC_RELATIONSHIP_MEMORY_SCHEMA_DOCS = [
    "docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md",
    "docs/kanban/founder_command_center_board.md",
    "docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md",
]

FCC_RELATIONSHIP_MEMORY_REASON_CODES = [
    "FCC_P1_010_RELATIONSHIP_MEMORY_SCHEMA",
    "FCC_MEMORY_RECALL_NOT_TRUTH",
    "FCC_MEMORY_SAFE_REFS_ONLY",
    "FCC_MEMORY_REVIEW_ONLY_NO_WRITES",
    "FCC_MEMORY_CONTEXT_INJECTION_BLOCKED",
]


class FCCRelationshipMemoryCandidateKind(str, Enum):
    person = "person"
    organization = "organization"
    project = "project"
    deal = "deal"
    promise = "promise"
    follow_up = "follow-up"
    relationship = "relationship"
    preference = "preference"
    business_context = "business-context"
    semantic_local = "semantic-local"
    episodic = "episodic"


class FCCRelationshipMemoryReviewState(str, Enum):
    review_needed = "review_needed"
    reviewed = "reviewed"
    correction_needed = "correction_needed"
    rejected = "rejected"
    retained = "retained"
    blocked = "blocked"


class FCCRelationshipMemoryCandidate(BaseModel):
    candidate_ref: str
    candidate_kind: FCCRelationshipMemoryCandidateKind
    safe_display_label: str = Field(..., min_length=1, max_length=120)
    redacted_summary: str = Field(..., min_length=1, max_length=500)
    provenance_refs: list[str]
    source_refs: list[str]
    evidence_refs: list[str]
    related_person_refs: list[str] = Field(default_factory=list)
    related_org_refs: list[str] = Field(default_factory=list)
    related_project_refs: list[str] = Field(default_factory=list)
    related_deal_refs: list[str] = Field(default_factory=list)
    related_follow_up_refs: list[str] = Field(default_factory=list)
    review_state: FCCRelationshipMemoryReviewState = (
        FCCRelationshipMemoryReviewState.review_needed
    )
    confidence_posture: str = Field(
        default="safe_summary_unverified_until_review",
        min_length=1,
        max_length=160,
    )
    correction_posture: str = Field(
        default="correction_requires_scoped_memory_write_contract",
        min_length=1,
        max_length=160,
    )
    rejection_posture: str = Field(
        default="rejection_is_review_state_only_until_capture_contract",
        min_length=1,
        max_length=160,
    )
    retention_posture: str = Field(
        default="retention_policy_not_bound",
        min_length=1,
        max_length=160,
    )
    delete_posture: str = Field(
        default="delete_execution_not_scoped",
        min_length=1,
        max_length=160,
    )
    export_posture: str = Field(
        default="export_is_redacted_review_posture_only",
        min_length=1,
        max_length=160,
    )
    stale_state: str = Field(
        default="recheck_source_refs_before_memory_use",
        min_length=1,
        max_length=160,
    )
    authority_boundary: str = Field(
        default=(
            "Memory candidate is recall metadata only, not truth, approval, "
            "write authority, or context-injection authority."
        ),
        min_length=1,
        max_length=260,
    )
    missing_contract_refs: list[str]
    blocked_states: list[str]
    next_safe_action: str = Field(
        default=(
            "Review safe refs and keep memory write, delete, export, and "
            "context-injection actions blocked until scoped contracts exist."
        ),
        min_length=1,
        max_length=260,
    )
    reason_codes: list[str] = Field(
        default_factory=lambda: list(FCC_RELATIONSHIP_MEMORY_REASON_CODES)
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    memory_is_recall_not_truth: bool = True
    approval_authority_enabled: bool = False
    automatic_memory_write_enabled: bool = False
    memory_delete_execution_enabled: bool = False
    memory_export_execution_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_authority_enabled: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    account_auth_enabled: bool = False
    email_calendar_fetch_enabled: bool = False
    background_sync_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    raw_transcript_enabled: bool = False
    raw_prompt_enabled: bool = False
    raw_source_content_enabled: bool = False
    private_connector_content_enabled: bool = False
    private_material_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @model_validator(mode="after")
    def validate_shape(self) -> "FCCRelationshipMemoryCandidate":
        _validate_m61_ref(self.candidate_ref, "candidate_ref")
        for field_name in [
            "provenance_refs",
            "source_refs",
            "evidence_refs",
            "related_person_refs",
            "related_org_refs",
            "related_project_refs",
            "related_deal_refs",
            "related_follow_up_refs",
            "missing_contract_refs",
            "blocked_states",
        ]:
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_reason_codes(self.reason_codes)
        for value in [
            self.safe_display_label,
            self.redacted_summary,
            self.confidence_posture,
            self.correction_posture,
            self.rejection_posture,
            self.retention_posture,
            self.delete_posture,
            self.export_posture,
            self.stale_state,
            self.authority_boundary,
            self.next_safe_action,
        ]:
            _validate_safe_text(value)
        return self


def build_fcc_relationship_memory_candidate(
    candidate_kind: FCCRelationshipMemoryCandidateKind | str = (
        FCCRelationshipMemoryCandidateKind.relationship
    ),
) -> FCCRelationshipMemoryCandidate:
    kind = FCCRelationshipMemoryCandidateKind(candidate_kind)
    kind_suffix = kind.value.replace("-", "_")
    candidate = FCCRelationshipMemoryCandidate(
        candidate_ref=f"fcc-memory-candidate-ref:fcc-p1-010:{kind_suffix}",
        candidate_kind=kind,
        safe_display_label=f"FCC {kind.value} memory candidate",
        redacted_summary=(
            "Relationship and follow-up memory candidate uses safe refs and a "
            "redacted summary only. Memory remains recall, not truth or authority."
        ),
        provenance_refs=[
            f"provenance-ref:fcc-p1-010:{kind_suffix}",
        ],
        source_refs=[
            "source-ref:fcc-p1-010:founder-loop-review",
        ],
        evidence_refs=[
            f"evidence-ref:fcc-p1-010:{kind_suffix}",
        ],
        related_person_refs=[
            "person-ref:fcc-p1-010:reviewed-safe-person",
        ],
        related_org_refs=[
            "org-ref:fcc-p1-010:reviewed-safe-org",
        ],
        related_project_refs=[
            "project-ref:fcc-p1-010:reviewed-safe-project",
        ],
        related_deal_refs=[
            "deal-ref:fcc-p1-010:reviewed-safe-deal",
        ],
        related_follow_up_refs=[
            "follow-up-ref:fcc-p1-010:reviewed-safe-follow-up",
        ],
        missing_contract_refs=[
            "contract-ref:fcc-p1-010:memory-write-policy-missing",
            "contract-ref:fcc-p1-010:memory-review-decision-capture-missing",
            "contract-ref:fcc-p1-010:memory-retention-delete-export-missing",
            "contract-ref:fcc-p1-010:context-injection-missing",
        ],
        blocked_states=[
            "blocked-state-ref:fcc-p1-010:no-automatic-memory-write",
            "blocked-state-ref:fcc-p1-010:no-memory-delete-execution",
            "blocked-state-ref:fcc-p1-010:no-context-injection",
            "blocked-state-ref:fcc-p1-010:no-model-provider-authority",
            "blocked-state-ref:fcc-p1-010:no-connector-runtime-or-write",
        ],
    )
    return validate_fcc_relationship_memory_candidate(candidate)


def validate_fcc_relationship_memory_candidate(
    candidate: FCCRelationshipMemoryCandidate | dict[str, Any],
) -> FCCRelationshipMemoryCandidate:
    payload = _payload(candidate)
    _reject_private_memory_payload(
        payload,
        allowed_keys=set(FCCRelationshipMemoryCandidate.model_fields),
    )
    for field_name, reason in _RELATIONSHIP_MEMORY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = FCCRelationshipMemoryCandidate.model_validate(payload)
    for field_name, reason in _RELATIONSHIP_MEMORY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RELATIONSHIP_MEMORY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _reject_private_memory_payload(validated.metadata)
    for reason_code in FCC_RELATIONSHIP_MEMORY_REASON_CODES:
        if reason_code not in validated.reason_codes:
            raise ValueError("FCC_MEMORY_REASON_CODE_REQUIRED")
    return validated


def _payload(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if isinstance(value, dict):
        return dict(value)
    raise ValueError("FCC_MEMORY_CONTRACT_PAYLOAD_REQUIRED")


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    if not refs:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_reason_codes(reason_codes: list[str]) -> None:
    if not reason_codes:
        raise ValueError("REASON_CODE_REQUIRED")
    for reason_code in reason_codes:
        if not reason_code.startswith("FCC_"):
            raise ValueError("FCC_MEMORY_REASON_CODE_REQUIRED")


def _validate_safe_text(value: str) -> None:
    try:
        _validate_safe_payload({"safe_text": value})
    except ValueError as exc:
        raise ValueError("FCC_MEMORY_PRIVATE_CONTENT_DENIED") from exc


def _reject_private_memory_payload(
    payload: Any,
    *,
    allowed_keys: set[str] | None = None,
) -> None:
    if _contains_forbidden_key(payload, _MEMORY_FORBIDDEN_KEY_RE, allowed_keys):
        raise ValueError("FCC_MEMORY_PRIVATE_FIELD_DENIED")
    if _contains_forbidden_value(payload, _MEMORY_FORBIDDEN_VALUE_RE):
        raise ValueError("FCC_MEMORY_PRIVATE_CONTENT_DENIED")
    try:
        _validate_safe_payload(payload)
    except ValueError as exc:
        raise ValueError("FCC_MEMORY_PRIVATE_CONTENT_DENIED") from exc


def _contains_forbidden_key(
    payload: Any,
    pattern: re.Pattern[str],
    allowed_keys: set[str] | None = None,
) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key)
            if key_text not in (allowed_keys or set()) and pattern.search(key_text):
                return True
            if _contains_forbidden_key(value, pattern):
                return True
    elif isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_key(item, pattern) for item in payload)
    return False


def _contains_forbidden_value(payload: Any, pattern: re.Pattern[str]) -> bool:
    if isinstance(payload, str):
        return bool(pattern.search(payload))
    if isinstance(payload, dict):
        return any(_contains_forbidden_value(value, pattern) for value in payload.values())
    if isinstance(payload, list | tuple | set):
        return any(_contains_forbidden_value(item, pattern) for item in payload)
    return False


_RELATIONSHIP_MEMORY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "SAFE_REFS_REQUIRED"),
    ("memory_is_recall_not_truth", "MEMORY_RECALL_NOT_TRUTH_REQUIRED"),
]

_RELATIONSHIP_MEMORY_DENIALS = [
    ("approval_authority_enabled", "APPROVAL_AUTHORITY_DENIED"),
    ("automatic_memory_write_enabled", "AUTOMATIC_MEMORY_WRITE_DENIED"),
    ("memory_delete_execution_enabled", "MEMORY_DELETE_EXECUTION_DENIED"),
    ("memory_export_execution_enabled", "MEMORY_EXPORT_EXECUTION_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_authority_enabled", "MODEL_PROVIDER_AUTHORITY_DENIED"),
    ("connector_runtime_enabled", "CONNECTOR_RUNTIME_DENIED"),
    ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("email_calendar_fetch_enabled", "EMAIL_CALENDAR_FETCH_DENIED"),
    ("background_sync_enabled", "BACKGROUND_SYNC_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
    ("public_beta_claim_enabled", "PUBLIC_BETA_CLAIM_DENIED"),
    ("public_distribution_claim_enabled", "PUBLIC_DISTRIBUTION_CLAIM_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("raw_transcript_enabled", "RAW_TRANSCRIPT_DENIED"),
    ("raw_prompt_enabled", "RAW_PROMPT_DENIED"),
    ("raw_source_content_enabled", "RAW_SOURCE_CONTENT_DENIED"),
    ("private_connector_content_enabled", "PRIVATE_CONNECTOR_CONTENT_DENIED"),
    ("private_material_enabled", "PRIVATE_MATERIAL_DENIED"),
]

_MEMORY_FORBIDDEN_KEY_RE = re.compile(
    r"(raw|transcript|prompt|source[_-]?text|source[_-]?content|"
    r"private[_-]?connector|participant|person[_-]?name|account[_-]?id|"
    r"email[_-]?address|username|hostname|local[_-]?path|path|log|"
    r"environment|env[_-]?dump|credential|password|token|secret|api[_-]?key|"
    r"authorization|bearer|oauth|session|cookie|provider[_-]?payload|"
    r"model[_-]?output)",
    re.IGNORECASE,
)

_MEMORY_FORBIDDEN_VALUE_RE = re.compile(
    r"(@|/users/|/home/|/var/|/etc/|[a-z]:\\|\braw\s+transcript\b|"
    r"\braw[_-]?prompt\b|\bprompt\s*:|\bsource\s+text\b|"
    r"\bsource\s+content\b|\bprivate\s+connector\b|\bparticipant\s*:|"
    r"\bperson\s*:|\busername\s*:|\bhostname\s*:|\blog\s*:|"
    r"\benv(?:ironment)?\s+dump\b|provider[_-]?payload|model[_-]?output|"
    r"api[_-]?key|password|token|secret|bearer|oauth|cookie)",
    re.IGNORECASE,
)
