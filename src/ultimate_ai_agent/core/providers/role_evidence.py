from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.gateway import (
    DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CONTRACT_REF = (
    "contract-ref:role-based-model-provider-evidence:v1"
)
ROLE_BASED_MODEL_PROVIDER_EVIDENCE_ROUTE_REF = (
    "GET /control-center/providers/runtime-control-plane"
)
ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-role-provider-evidence"
)
ROLE_BASED_MODEL_PROVIDER_EVIDENCE_VERIFIER_REF = (
    "scripts/verify_uaa_goatcitadel_runtime_role_provider_evidence.py"
)
ROLE_BASED_MODEL_PROVIDER_EVIDENCE_DOC_REF = (
    "docs/runtime/UAA_GOATCITADEL_RUNTIME_ROLE_PROVIDER_EVIDENCE.md"
)
ROLE_BASED_MODEL_PROVIDER_EVIDENCE_POLICY_REF = (
    "policy-ref:role-based-model-provider-evidence:advisory-only:v1"
)

_SAFE_REF_PREFIXES = (
    "blocked-state:",
    "candidate-ref:",
    "capability-ref:",
    "cli-ref:",
    "contract-ref:",
    "cost-estimate-ref:",
    "evidence-ref:",
    "fallback-ref:",
    "latency-ref:",
    "model-ref:",
    "model-router-trace-ref:",
    "orchestration-plan-ref:",
    "policy-decision-ref:",
    "policy-ref:",
    "prepared-turn-contract-ref:",
    "provider-catalog:",
    "provider-ref:",
    "redaction-ref:",
    "role-ref:",
    "runtime-ref:",
)


class ModelProviderRole(str, Enum):
    answerer = "answerer"
    planner = "planner"
    reviewer = "reviewer"
    synthesizer = "synthesizer"
    coder = "coder"
    extractor = "extractor"
    safety_reviewer = "safety_reviewer"


class RoleProviderAuthorityStatus(str, Enum):
    local_loopback_metadata_only = "local_loopback_metadata_only"
    remote_provider_blocked = "remote_provider_blocked"
    exact_lane_requires_approval = "exact_lane_requires_approval"
    fallback_only_blocked = "fallback_only_blocked"


class RoleProviderReadinessLabel(str, Enum):
    advisory_selected = "advisory_selected"
    metadata_only = "metadata_only"
    blocked_missing_credential = "blocked_missing_credential"
    blocked_missing_model_ref = "blocked_missing_model_ref"
    cost_blocked = "cost_blocked"
    degraded = "degraded"


class _RoleProviderEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True, hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _reject_unsafe_payload(payload: object, error_code: str) -> None:
    if contains_secret_like(payload) or contains_obvious_secret(payload):
        raise ValueError(error_code)


def _safe_ref_matches(value: str) -> bool:
    if not any(value.startswith(prefix) for prefix in _SAFE_REF_PREFIXES):
        return False
    return all(char.isalnum() or char in {":", "-", "_", "."} for char in value)


def _require_safe_refs(values: Iterable[str], error_code: str) -> None:
    for value in values:
        if not value or not _safe_ref_matches(value):
            raise ValueError(error_code)


def _reason_code(value: str) -> bool:
    return 1 <= len(value) <= 140 and all(
        char.isupper() or char.isdigit() or char == "_" for char in value
    )


def _safe_get(value: object, field_name: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(field_name, default)
    return getattr(value, field_name, default)


def _slug(value: str) -> str:
    safe = "".join(char if char.isalnum() else "-" for char in value.lower())
    safe = "-".join(part for part in safe.split("-") if part)
    return safe or "unknown"


class RoleProviderCandidateEvidence(_RoleProviderEvidenceModel):
    candidate_ref: str
    role_ref: str
    provider_ref: str
    provider_label: str = Field(..., min_length=1, max_length=120)
    model_ref: str
    local_remote_posture: Literal["local_loopback", "remote_provider_reference"]
    readiness_label: RoleProviderReadinessLabel
    authority_status: RoleProviderAuthorityStatus
    capability_score: int = Field(..., ge=0, le=100)
    authority_adjusted_score: int = Field(..., ge=0, le=100)
    rank_index: int = Field(..., ge=1)
    cost_visibility: Literal[
        "local_hardware_cost_only",
        "unknown_paid_cost_requires_approval",
        "static_cost_metadata_only",
    ]
    latency_visibility: Literal[
        "local_gateway_metadata_only",
        "unknown_remote_latency",
        "static_latency_metadata_unavailable",
    ]
    policy_decision_ref: str
    fallback_ref: str
    disabled_reason_ref: str
    redacted_evidence_ref: str
    reason_codes: list[str] = Field(default_factory=list)
    selected_for_role: bool = False
    advisory_only: bool = True
    execution_authorized: bool = False
    provider_sdk_call_performed: bool = False
    network_call_performed: bool = False
    model_invocation_performed: bool = False
    provider_payload_persisted: bool = False
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    provider_output_authoritative: bool = False

    @model_validator(mode="after")
    def candidate_must_remain_evidence_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "ROLE_PROVIDER_CANDIDATE_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.candidate_ref,
                self.role_ref,
                self.provider_ref,
                self.model_ref,
                self.policy_decision_ref,
                self.fallback_ref,
                self.disabled_reason_ref,
                self.redacted_evidence_ref,
            ],
            "ROLE_PROVIDER_CANDIDATE_REF_REQUIRED",
        )
        denied_flags = [
            not self.advisory_only,
            self.execution_authorized,
            self.provider_sdk_call_performed,
            self.network_call_performed,
            self.model_invocation_performed,
            self.provider_payload_persisted,
            self.prompt_content_persisted,
            self.response_content_persisted,
            self.provider_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("ROLE_PROVIDER_CANDIDATE_AUTHORITY_DENIED")
        if not self.reason_codes or not all(_reason_code(code) for code in self.reason_codes):
            raise ValueError("ROLE_PROVIDER_CANDIDATE_REASON_CODES_REQUIRED")
        if self.selected_for_role and self.local_remote_posture != "local_loopback":
            raise ValueError("ROLE_PROVIDER_CANDIDATE_REMOTE_SELECTION_DENIED")
        if (
            self.local_remote_posture == "remote_provider_reference"
            and self.authority_status != RoleProviderAuthorityStatus.remote_provider_blocked
        ):
            raise ValueError("ROLE_PROVIDER_CANDIDATE_REMOTE_AUTHORITY_DENIED")
        return self


class RoleBasedProviderSelectionEvidence(_RoleProviderEvidenceModel):
    role: ModelProviderRole
    role_ref: str
    role_label: str = Field(..., min_length=1, max_length=80)
    route_decision_trace_ref: str
    orchestration_stage_ref: str
    policy_decision_ref: str
    fallback_ref: str
    evidence_ref: str
    selected_candidate_ref: str
    highest_capability_candidate_ref: str
    candidate_count: int = Field(..., ge=1)
    candidates: list[RoleProviderCandidateEvidence] = Field(..., min_length=1)
    advisory_only: bool = True
    local_first_policy: bool = True
    remote_provider_candidates_blocked: bool = True
    no_invocation_authorized: bool = True
    provider_sdk_call_performed: bool = False
    network_call_performed: bool = False
    model_invocation_performed: bool = False
    provider_payload_persisted: bool = False
    provider_output_authoritative: bool = False

    @model_validator(mode="after")
    def role_evidence_must_remain_non_authorizing(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "ROLE_PROVIDER_SELECTION_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.role_ref,
                self.route_decision_trace_ref,
                self.orchestration_stage_ref,
                self.policy_decision_ref,
                self.fallback_ref,
                self.evidence_ref,
                self.selected_candidate_ref,
                self.highest_capability_candidate_ref,
            ],
            "ROLE_PROVIDER_SELECTION_REF_REQUIRED",
        )
        if self.candidate_count != len(self.candidates):
            raise ValueError("ROLE_PROVIDER_SELECTION_COUNT_MISMATCH")
        selected = [
            candidate
            for candidate in self.candidates
            if candidate.candidate_ref == self.selected_candidate_ref
        ]
        if len(selected) != 1 or not selected[0].selected_for_role:
            raise ValueError("ROLE_PROVIDER_SELECTION_SELECTED_CANDIDATE_REQUIRED")
        if self.highest_capability_candidate_ref not in {
            candidate.candidate_ref for candidate in self.candidates
        }:
            raise ValueError("ROLE_PROVIDER_SELECTION_HIGHEST_CANDIDATE_REQUIRED")
        denied_flags = [
            not self.advisory_only,
            not self.local_first_policy,
            not self.remote_provider_candidates_blocked,
            not self.no_invocation_authorized,
            self.provider_sdk_call_performed,
            self.network_call_performed,
            self.model_invocation_performed,
            self.provider_payload_persisted,
            self.provider_output_authoritative,
        ]
        if any(denied_flags):
            raise ValueError("ROLE_PROVIDER_SELECTION_AUTHORITY_DENIED")
        return self


class RoleBasedModelProviderEvidenceReadModel(_RoleProviderEvidenceModel):
    schema_version: Literal["role_based_model_provider_evidence.v1"] = (
        "role_based_model_provider_evidence.v1"
    )
    contract_ref: str = ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CONTRACT_REF
    status: Literal["advisory_evidence_only"] = "advisory_evidence_only"
    route_ref: str = ROLE_BASED_MODEL_PROVIDER_EVIDENCE_ROUTE_REF
    cli_ref: str = ROLE_BASED_MODEL_PROVIDER_EVIDENCE_CLI_REF
    policy_ref: str = ROLE_BASED_MODEL_PROVIDER_EVIDENCE_POLICY_REF
    provider_catalog_ref: str
    prepared_turn_contract_ref: str = "prepared-turn-contract-ref:prepared-turn:v1"
    orchestration_plan_ref: str = "orchestration-plan-ref:runtime-parity:staged-sample"
    router_trace_refs: list[str] = Field(default_factory=list)
    role_count: int = Field(..., ge=1)
    role_evidence: list[RoleBasedProviderSelectionEvidence] = Field(..., min_length=1)
    safe_summary: str = (
        "Role-based model/provider evidence ranks local and remote provider refs "
        "for operator visibility only. Local-first advisory selection is visible, "
        "remote provider candidates remain blocked, and no provider/model call is "
        "authorized or performed."
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:model-provider:provider-sdk-calls",
            "blocked-state:model-provider:remote-model-calls",
            "blocked-state:model-provider:broad-provider-routing",
            "blocked-state:model-provider:provider-output-authority",
            "blocked-state:model-provider:raw-prompt-response-provider-payload",
            "blocked-state:model-provider:background-autonomy",
            "blocked-state:model-provider:production-authority",
        ]
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "redaction-ref:role-provider-evidence:raw-prompt-omitted",
            "redaction-ref:role-provider-evidence:raw-response-omitted",
            "redaction-ref:role-provider-evidence:provider-payload-omitted",
            "redaction-ref:role-provider-evidence:credential-material-omitted",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [ROLE_BASED_MODEL_PROVIDER_EVIDENCE_DOC_REF]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [ROLE_BASED_MODEL_PROVIDER_EVIDENCE_VERIFIER_REF]
    )
    advisory_only: bool = True
    control_center_mints_authority: bool = False
    provider_sdk_call_enabled: bool = False
    remote_model_call_enabled: bool = False
    local_model_call_performed: bool = False
    network_call_performed: bool = False
    model_invocation_performed: bool = False
    provider_payload_persisted: bool = False
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    provider_output_authoritative: bool = False
    broad_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def read_model_must_remain_advisory_only(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "ROLE_PROVIDER_EVIDENCE_SECRET_LIKE_VALUE_REJECTED",
        )
        _require_safe_refs(
            [
                self.contract_ref,
                self.policy_ref,
                self.provider_catalog_ref,
                self.prepared_turn_contract_ref,
                self.orchestration_plan_ref,
                *self.router_trace_refs,
                *self.blocked_authority_refs,
                *self.redactions_applied,
            ],
            "ROLE_PROVIDER_EVIDENCE_REF_REQUIRED",
        )
        if self.role_count != len(self.role_evidence):
            raise ValueError("ROLE_PROVIDER_EVIDENCE_ROLE_COUNT_MISMATCH")
        if {item.role for item in self.role_evidence} != set(ModelProviderRole):
            raise ValueError("ROLE_PROVIDER_EVIDENCE_ROLE_COVERAGE_REQUIRED")
        denied_flags = [
            not self.advisory_only,
            self.control_center_mints_authority,
            self.provider_sdk_call_enabled,
            self.remote_model_call_enabled,
            self.local_model_call_performed,
            self.network_call_performed,
            self.model_invocation_performed,
            self.provider_payload_persisted,
            self.prompt_content_persisted,
            self.response_content_persisted,
            self.provider_output_authoritative,
            self.broad_autonomy_enabled,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("ROLE_PROVIDER_EVIDENCE_AUTHORITY_DENIED")
        return self


_ROLE_LABELS: dict[ModelProviderRole, str] = {
    ModelProviderRole.answerer: "Answerer",
    ModelProviderRole.planner: "Planner",
    ModelProviderRole.reviewer: "Reviewer",
    ModelProviderRole.synthesizer: "Synthesizer",
    ModelProviderRole.coder: "Coder",
    ModelProviderRole.extractor: "Extractor",
    ModelProviderRole.safety_reviewer: "Safety reviewer",
}

_LOCAL_ROLE_SCORES: dict[ModelProviderRole, int] = {
    ModelProviderRole.answerer: 78,
    ModelProviderRole.planner: 74,
    ModelProviderRole.reviewer: 72,
    ModelProviderRole.synthesizer: 75,
    ModelProviderRole.coder: 66,
    ModelProviderRole.extractor: 70,
    ModelProviderRole.safety_reviewer: 68,
}

_REMOTE_ROLE_SCORE_BONUS: dict[str, int] = {
    "openai-compatible": 8,
    "anthropic-compatible": 10,
    "gemini-compatible": 6,
}


def build_role_based_model_provider_evidence(
    *,
    provider_readiness_items: Iterable[object],
    provider_catalog_ref: str,
    router_trace_refs: Iterable[str] = (),
) -> RoleBasedModelProviderEvidenceReadModel:
    readiness_items = list(provider_readiness_items)
    traces = list(router_trace_refs) or [
        "model-router-trace-ref:role-provider-evidence:advisory"
    ]
    role_evidence = [
        _role_evidence(role, readiness_items, traces[0])
        for role in ModelProviderRole
    ]
    return RoleBasedModelProviderEvidenceReadModel(
        provider_catalog_ref=provider_catalog_ref,
        router_trace_refs=traces,
        role_count=len(role_evidence),
        role_evidence=role_evidence,
    )


def _role_evidence(
    role: ModelProviderRole,
    readiness_items: list[object],
    trace_ref: str,
) -> RoleBasedProviderSelectionEvidence:
    role_slug = role.value.replace("_", "-")
    role_ref = f"role-ref:model-provider:{role_slug}"
    local_candidate = _local_candidate(role, role_ref)
    remote_candidates = [
        _remote_candidate(role, role_ref, item, index + 2)
        for index, item in enumerate(readiness_items)
    ]
    candidates = [local_candidate, *remote_candidates]
    highest = max(candidates, key=lambda candidate: candidate.capability_score)
    return RoleBasedProviderSelectionEvidence(
        role=role,
        role_ref=role_ref,
        role_label=_ROLE_LABELS[role],
        route_decision_trace_ref=trace_ref,
        orchestration_stage_ref=f"orchestration-plan-ref:runtime-parity:{role_slug}",
        policy_decision_ref=f"policy-decision-ref:role-provider-evidence:{role_slug}:advisory",
        fallback_ref=f"fallback-ref:role-provider-evidence:{role_slug}:blocked",
        evidence_ref=f"evidence-ref:role-provider-evidence:{role_slug}",
        selected_candidate_ref=local_candidate.candidate_ref,
        highest_capability_candidate_ref=highest.candidate_ref,
        candidate_count=len(candidates),
        candidates=candidates,
    )


def _local_candidate(
    role: ModelProviderRole,
    role_ref: str,
) -> RoleProviderCandidateEvidence:
    role_slug = role.value.replace("_", "-")
    score = _LOCAL_ROLE_SCORES[role]
    return RoleProviderCandidateEvidence(
        candidate_ref=f"candidate-ref:role-provider:{role_slug}:local-llama-cpp",
        role_ref=role_ref,
        provider_ref="provider-ref:local-llama-cpp:loopback",
        provider_label="Local llama.cpp loopback",
        model_ref=f"model-ref:local:{DEFAULT_UAA_LLAMA_CPP_MODEL_ID}",
        local_remote_posture="local_loopback",
        readiness_label=RoleProviderReadinessLabel.advisory_selected,
        authority_status=RoleProviderAuthorityStatus.local_loopback_metadata_only,
        capability_score=score,
        authority_adjusted_score=score,
        rank_index=1,
        cost_visibility="local_hardware_cost_only",
        latency_visibility="local_gateway_metadata_only",
        policy_decision_ref=f"policy-decision-ref:role-provider-evidence:{role_slug}:local-first",
        fallback_ref=f"fallback-ref:role-provider-evidence:{role_slug}:local-manual-review",
        disabled_reason_ref=f"blocked-state:role-provider-evidence:{role_slug}:execution-not-requested",
        redacted_evidence_ref=f"evidence-ref:role-provider-evidence:{role_slug}:local",
        reason_codes=[
            "LOCAL_FIRST_POLICY",
            "ADVISORY_SELECTION_ONLY",
            "NO_MODEL_INVOCATION",
            "NO_PROVIDER_SDK_CALL",
        ],
        selected_for_role=True,
    )


def _remote_candidate(
    role: ModelProviderRole,
    role_ref: str,
    item: object,
    rank_index: int,
) -> RoleProviderCandidateEvidence:
    role_slug = role.value.replace("_", "-")
    provider_ref = str(_safe_get(item, "provider_id", "provider:unknown:reference"))
    provider_label = str(_safe_get(item, "provider_label", "Remote provider reference"))
    provider_slug = _provider_slug(provider_ref)
    cost_binding = _safe_get(item, "cost_governor_binding", {})
    model_ref = str(
        _safe_get(
            cost_binding,
            "model_ref",
            f"model-ref:{provider_slug}:not-selected",
        )
    )
    provider_model_refs_bound = bool(_safe_get(item, "provider_model_refs_bound", False))
    credential_ref_status = str(_safe_get(item, "credential_ref_status", "reference_missing"))
    blocker_codes = list(_safe_get(item, "blocker_codes", []))
    readiness_label = _remote_readiness_label(
        credential_ref_status=credential_ref_status,
        provider_model_refs_bound=provider_model_refs_bound,
        blocker_codes=blocker_codes,
    )
    capability_score = min(96, _LOCAL_ROLE_SCORES[role] + _REMOTE_ROLE_SCORE_BONUS.get(provider_slug, 5))
    reason_codes = [
        "REMOTE_PROVIDER_AUTHORITY_BLOCKED",
        "NO_PROVIDER_SDK_CALL",
        "NO_MODEL_INVOCATION",
        "EXACT_APPROVAL_REQUIRED_FOR_FUTURE_USE",
    ]
    for code in blocker_codes:
        if _reason_code(str(code)) and str(code) not in reason_codes:
            reason_codes.append(str(code))
    return RoleProviderCandidateEvidence(
        candidate_ref=f"candidate-ref:role-provider:{role_slug}:{provider_slug}",
        role_ref=role_ref,
        provider_ref=_normalize_provider_ref(provider_ref, provider_slug),
        provider_label=provider_label,
        model_ref=model_ref,
        local_remote_posture="remote_provider_reference",
        readiness_label=readiness_label,
        authority_status=RoleProviderAuthorityStatus.remote_provider_blocked,
        capability_score=capability_score,
        authority_adjusted_score=0,
        rank_index=rank_index,
        cost_visibility="unknown_paid_cost_requires_approval",
        latency_visibility="unknown_remote_latency",
        policy_decision_ref=f"policy-decision-ref:role-provider-evidence:{role_slug}:{provider_slug}:blocked",
        fallback_ref=f"fallback-ref:role-provider-evidence:{role_slug}:{provider_slug}:not-executed",
        disabled_reason_ref=f"blocked-state:role-provider-evidence:{role_slug}:{provider_slug}:remote-blocked",
        redacted_evidence_ref=f"evidence-ref:role-provider-evidence:{role_slug}:{provider_slug}",
        reason_codes=reason_codes,
    )


def _provider_slug(provider_ref: str) -> str:
    parts = [part for part in provider_ref.split(":") if part]
    if len(parts) >= 2:
        return _slug(parts[1])
    return _slug(provider_ref)


def _normalize_provider_ref(provider_ref: str, provider_slug: str) -> str:
    if provider_ref.startswith("provider-ref:"):
        return provider_ref
    if provider_ref.startswith("provider:"):
        return f"provider-ref:{provider_slug}:reference"
    return f"provider-ref:{provider_slug}:reference"


def _remote_readiness_label(
    *,
    credential_ref_status: str,
    provider_model_refs_bound: bool,
    blocker_codes: list[str],
) -> RoleProviderReadinessLabel:
    if credential_ref_status != "reference_available":
        return RoleProviderReadinessLabel.blocked_missing_credential
    if not provider_model_refs_bound:
        return RoleProviderReadinessLabel.blocked_missing_model_ref
    if "UNKNOWN_PAID_COST_REQUIRES_APPROVAL" in blocker_codes:
        return RoleProviderReadinessLabel.cost_blocked
    return RoleProviderReadinessLabel.metadata_only
