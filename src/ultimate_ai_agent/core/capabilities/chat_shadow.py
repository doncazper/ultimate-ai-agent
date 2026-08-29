from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.familiarity import (
    FamiliarityAssessment,
    FamiliarityState,
)
from ultimate_ai_agent.core.capabilities.retrieval import CapabilityHydrationResult
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW04_CONTRACT_REF = "contract-ref:taw04:chat-shadow-integration:v1"
TAW04_ROUTER_REF = "router-ref:taw04:evidence-only-shadow-v1"
TAW04_CLI_INSPECTION_REF = "inspection-ref:taw04:cli:v1"
TAW04_API_INSPECTION_REF = "inspection-ref:taw04:api:v1"
TAW04_SAFE_DISABLE_REF = "safe-disable-ref:taw04:accepted-legacy-router"
TAW04_CATALOG_INJECTION_FIELD_PATHS = (
    "aliases",
    "availability_metadata",
    "description",
    "effect_metadata",
    "examples",
    "input_schema",
    "operation_metadata",
    "output_schema",
    "preconditions",
    "provenance_review_metadata",
    "risk_approval_metadata",
    "rollback_metadata",
    "terminal_proof_metadata",
)


class AwarenessEvidenceStatus(StrEnum):
    valid = "valid"
    missing = "missing"
    corrupt = "corrupt"
    stale = "stale"
    unreadable = "unreadable"
    over_budget = "over_budget"


class ShadowChatAction(StrEnum):
    preserve_direct_chat = "preserve_direct_chat"
    record_capability_candidate = "record_capability_candidate"
    recommend_clarification = "recommend_clarification"
    block_capability_proposal = "block_capability_proposal"
    record_outcome_uncertain = "record_outcome_uncertain"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("TAW-04 evidence must be canonical JSON") from exc


def _fingerprint(payload: object, *, prefix: str) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


class ChatShadowEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw04-chat-shadow-evidence.v1"] = (
        "uaa-taw04-chat-shadow-evidence.v1"
    )
    awareness_status: AwarenessEvidenceStatus
    legacy_route_ref: str
    safe_disable_ref: Literal["safe-disable-ref:taw04:accepted-legacy-router"] = (
        TAW04_SAFE_DISABLE_REF
    )
    assessment: FamiliarityAssessment | None = None
    hydration: CapabilityHydrationResult | None = None
    material_effect_refs: tuple[str, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def validate_evidence(self) -> "ChatShadowEvidence":
        _validate_ref(self.legacy_route_ref, "legacy_route_ref")
        _validate_ref(self.safe_disable_ref, "safe_disable_ref")
        _validate_refs(self.material_effect_refs, "material_effect_refs")
        if self.awareness_status == AwarenessEvidenceStatus.valid:
            if self.assessment is None:
                raise ValueError("valid awareness requires an exact assessment")
        elif self.assessment is not None or self.hydration is not None:
            raise ValueError("invalid awareness cannot carry trusted derived evidence")
        if self.hydration is not None:
            if self.assessment is None:
                raise ValueError("hydration requires an exact assessment")
            if (
                self.assessment.catalog_fingerprint_ref is None
                or self.hydration.catalog_fingerprint_ref
                != self.assessment.catalog_fingerprint_ref
            ):
                raise ValueError("assessment and hydration catalog binding mismatch")
            candidate_refs = set(self.assessment.candidate_operation_refs)
            envelope_refs = set(self.assessment.candidate_envelope_fingerprint_refs)
            operation_schema_refs = set(
                self.assessment.candidate_operation_schema_fingerprint_refs
            )
            if any(
                item.operation_id not in candidate_refs
                or item.envelope_fingerprint_ref not in envelope_refs
                or item.operation_schema_fingerprint_ref not in operation_schema_refs
                for item in self.hydration.manifests
            ):
                raise ValueError("hydration contains non-candidate bound evidence")
        if (
            self.assessment is None
            or self.assessment.state != FamiliarityState.ambiguous
        ):
            if self.material_effect_refs:
                raise ValueError("material effect refs are valid only for ambiguity")
        return self


class ChatShadowDecision(_FrozenModel):
    schema_version: Literal["uaa-taw04-chat-shadow-decision.v1"] = (
        "uaa-taw04-chat-shadow-decision.v1"
    )
    contract_ref: Literal["contract-ref:taw04:chat-shadow-integration:v1"] = (
        TAW04_CONTRACT_REF
    )
    router_ref: Literal["router-ref:taw04:evidence-only-shadow-v1"] = TAW04_ROUTER_REF
    mode: Literal["evidence_only_shadow"] = "evidence_only_shadow"
    awareness_status: AwarenessEvidenceStatus
    action: ShadowChatAction
    reason_refs: tuple[str, ...] = Field(..., min_length=1)
    legacy_route_ref: str
    operator_visible_route_ref: str
    safe_disable_ref: Literal["safe-disable-ref:taw04:accepted-legacy-router"]
    safe_disable_engaged: bool
    familiarity_state: FamiliarityState | None
    assessment_fingerprint_ref: str | None
    hydration_fingerprint_ref: str | None
    selected_operation_refs: tuple[str, ...]
    material_effect_refs: tuple[str, ...]
    clarification_posture: Literal["not_applicable", "shadow_recommended"]
    clarification_contract_ref: str | None
    ordinary_no_tool_chat_preserved: Literal[True] = True
    direct_chat_path_preserved: Literal[True] = True
    operator_visible_routing_changed: Literal[False] = False
    model_context_changed: Literal[False] = False
    model_visible_manifest_refs: tuple[str, ...] = ()
    extra_model_call_count: Literal[0] = 0
    prompt_assembly_performed: Literal[False] = False
    skill_activation_performed: Literal[False] = False
    proposal_constructed: Literal[False] = False
    approval_requested: Literal[False] = False
    execution_performed: Literal[False] = False
    provider_call_performed: Literal[False] = False
    network_access_performed: Literal[False] = False
    web_fetch_performed: Literal[False] = False
    authority_granted: Literal[False] = False
    decision_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_decision(self) -> "ChatShadowDecision":
        for value, field_name in (
            (self.legacy_route_ref, "legacy_route_ref"),
            (self.operator_visible_route_ref, "operator_visible_route_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
        ):
            _validate_ref(value, field_name)
        if self.operator_visible_route_ref != self.legacy_route_ref:
            raise ValueError("shadow mode cannot alter the operator-visible route")
        _validate_refs(self.reason_refs, "reason_refs")
        _validate_refs(self.selected_operation_refs, "selected_operation_refs")
        _validate_refs(self.material_effect_refs, "material_effect_refs")
        if self.model_visible_manifest_refs:
            raise ValueError("shadow mode cannot expose manifests to a model")
        if self.clarification_posture == "shadow_recommended":
            if (
                self.action != ShadowChatAction.recommend_clarification
                or len(self.material_effect_refs) < 2
                or self.clarification_contract_ref is None
            ):
                raise ValueError("clarification requires materially different effects")
            _validate_ref(self.clarification_contract_ref, "clarification_contract_ref")
        elif self.clarification_contract_ref is not None:
            raise ValueError("non-clarification decisions cannot carry a contract ref")
        if self.safe_disable_engaged and self.selected_operation_refs:
            raise ValueError("safe-disable cannot retain selected operations")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"decision_fingerprint_ref"}),
            prefix="chat-shadow-decision-ref:taw04",
        )
        if self.decision_fingerprint_ref != expected:
            raise ValueError("chat shadow decision fingerprint binding drift")
        return self


class ChatShadowInspection(_FrozenModel):
    schema_version: Literal["uaa-taw04-chat-shadow-inspection.v1"] = (
        "uaa-taw04-chat-shadow-inspection.v1"
    )
    contract_ref: Literal["contract-ref:taw04:chat-shadow-integration:v1"] = (
        TAW04_CONTRACT_REF
    )
    cli_inspection_ref: Literal["inspection-ref:taw04:cli:v1"] = (
        TAW04_CLI_INSPECTION_REF
    )
    api_inspection_ref: Literal["inspection-ref:taw04:api:v1"] = (
        TAW04_API_INSPECTION_REF
    )
    decision_fingerprint_ref: str
    mode: Literal["evidence_only_shadow"]
    awareness_status: AwarenessEvidenceStatus
    action: ShadowChatAction
    reason_refs: tuple[str, ...]
    legacy_route_ref: str
    operator_visible_route_ref: str
    safe_disable_engaged: bool
    familiarity_state: FamiliarityState | None
    selected_operation_refs: tuple[str, ...]
    clarification_posture: Literal["not_applicable", "shadow_recommended"]
    ordinary_no_tool_chat_preserved: Literal[True]
    direct_chat_path_preserved: Literal[True]
    extra_model_call_count: Literal[0]
    execution_performed: Literal[False]
    authority_granted: Literal[False]
    projection_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_projection(self) -> "ChatShadowInspection":
        for value, field_name in (
            (self.decision_fingerprint_ref, "decision_fingerprint_ref"),
            (self.legacy_route_ref, "legacy_route_ref"),
            (self.operator_visible_route_ref, "operator_visible_route_ref"),
        ):
            _validate_ref(value, field_name)
        if self.operator_visible_route_ref != self.legacy_route_ref:
            raise ValueError("inspection cannot alter the operator-visible route")
        _validate_refs(self.reason_refs, "reason_refs")
        _validate_refs(self.selected_operation_refs, "selected_operation_refs")
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"projection_fingerprint_ref"}),
            prefix="chat-shadow-inspection-ref:taw04",
        )
        if self.projection_fingerprint_ref != expected:
            raise ValueError("chat shadow inspection fingerprint binding drift")
        return self


class CatalogInjectionCase(_FrozenModel):
    schema_version: Literal["uaa-taw04-catalog-injection-case.v1"] = (
        "uaa-taw04-catalog-injection-case.v1"
    )
    field_path: str
    case_ref: str
    rendering_path_ref: str
    model_visible_in_shadow: Literal[False] = False
    prompt_assembly_performed: Literal[False] = False
    response_census_status: Literal["blocked_until_no_effect_active_replay"] = (
        "blocked_until_no_effect_active_replay"
    )
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_case(self) -> "CatalogInjectionCase":
        if self.field_path not in TAW04_CATALOG_INJECTION_FIELD_PATHS:
            raise ValueError("catalog injection field is outside the accepted census")
        _validate_ref(self.case_ref, "case_ref")
        _validate_ref(self.rendering_path_ref, "rendering_path_ref")
        return self


def _selected_operations(
    assessment: FamiliarityAssessment,
    hydration: CapabilityHydrationResult | None,
) -> tuple[str, ...]:
    if hydration is None or hydration.status != "ready":
        return ()
    candidates = set(assessment.candidate_operation_refs)
    return tuple(
        sorted(
            item.operation_id
            for item in hydration.manifests
            if item.proposal_eligible and item.operation_id in candidates
        )
    )


def evaluate_chat_shadow(
    evidence: ChatShadowEvidence | dict[str, Any],
) -> ChatShadowDecision:
    evidence_model = ChatShadowEvidence.model_validate(
        evidence.model_dump(mode="python")
        if isinstance(evidence, ChatShadowEvidence)
        else dict(evidence)
    )
    assessment = evidence_model.assessment
    hydration = evidence_model.hydration
    safe_disable = evidence_model.awareness_status != AwarenessEvidenceStatus.valid
    action = ShadowChatAction.preserve_direct_chat
    reason_refs: tuple[str, ...]
    clarification_posture: Literal["not_applicable", "shadow_recommended"] = (
        "not_applicable"
    )
    clarification_contract_ref: str | None = None
    selected_operation_refs: tuple[str, ...] = ()

    if safe_disable:
        reason_refs = (
            f"reason-ref:taw04:awareness-{evidence_model.awareness_status.value}",
        )
    elif assessment is None:  # pragma: no cover - enforced by the model
        raise ValueError("valid awareness requires an assessment")
    elif assessment.state == FamiliarityState.capability_evidence_unavailable:
        safe_disable = True
        action = ShadowChatAction.block_capability_proposal
        reason_refs = ("reason-ref:taw04:capability-evidence-unavailable",)
    elif assessment.state == FamiliarityState.outcome_uncertain:
        action = ShadowChatAction.record_outcome_uncertain
        reason_refs = ("reason-ref:taw04:durable-terminal-proof-required",)
    elif assessment.state == FamiliarityState.ambiguous:
        if len(evidence_model.material_effect_refs) >= 2:
            action = ShadowChatAction.recommend_clarification
            clarification_posture = "shadow_recommended"
            clarification_contract_ref = (
                "turn-contract-ref:taw04:ask-clarifying-question"
            )
            reason_refs = ("reason-ref:taw04:material-effect-ambiguity",)
        else:
            reason_refs = ("reason-ref:taw04:non-material-ambiguity",)
    elif assessment.state in {
        FamiliarityState.familiar_authority_blocked,
        FamiliarityState.familiar_unavailable,
    }:
        action = ShadowChatAction.block_capability_proposal
        reason_refs = (f"reason-ref:taw04:{assessment.state.value}",)
    elif assessment.state == FamiliarityState.novel_unsupported:
        reason_refs = ("reason-ref:taw04:no-supported-capability",)
    else:
        selected_operation_refs = _selected_operations(assessment, hydration)
        action = ShadowChatAction.record_capability_candidate
        reason_refs = (f"reason-ref:taw04:{assessment.state.value}",)

    payload: dict[str, Any] = {
        "awareness_status": evidence_model.awareness_status,
        "action": action,
        "reason_refs": tuple(sorted(reason_refs)),
        "legacy_route_ref": evidence_model.legacy_route_ref,
        "operator_visible_route_ref": evidence_model.legacy_route_ref,
        "safe_disable_ref": evidence_model.safe_disable_ref,
        "safe_disable_engaged": safe_disable,
        "familiarity_state": assessment.state if assessment is not None else None,
        "assessment_fingerprint_ref": (
            assessment.assessment_fingerprint_ref if assessment is not None else None
        ),
        "hydration_fingerprint_ref": (
            hydration.hydration_fingerprint_ref if hydration is not None else None
        ),
        "selected_operation_refs": selected_operation_refs,
        "material_effect_refs": evidence_model.material_effect_refs,
        "clarification_posture": clarification_posture,
        "clarification_contract_ref": clarification_contract_ref,
    }
    payload["decision_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw04-chat-shadow-decision.v1",
            "contract_ref": TAW04_CONTRACT_REF,
            "router_ref": TAW04_ROUTER_REF,
            "mode": "evidence_only_shadow",
            "ordinary_no_tool_chat_preserved": True,
            "direct_chat_path_preserved": True,
            "operator_visible_routing_changed": False,
            "model_context_changed": False,
            "model_visible_manifest_refs": (),
            "extra_model_call_count": 0,
            "prompt_assembly_performed": False,
            "skill_activation_performed": False,
            "proposal_constructed": False,
            "approval_requested": False,
            "execution_performed": False,
            "provider_call_performed": False,
            "network_access_performed": False,
            "web_fetch_performed": False,
            "authority_granted": False,
        },
        prefix="chat-shadow-decision-ref:taw04",
    )
    return ChatShadowDecision.model_validate(payload)


def build_chat_shadow_inspection(
    decision: ChatShadowDecision | dict[str, Any],
) -> ChatShadowInspection:
    decision_model = ChatShadowDecision.model_validate(
        decision.model_dump(mode="python")
        if isinstance(decision, ChatShadowDecision)
        else dict(decision)
    )
    payload: dict[str, Any] = {
        "decision_fingerprint_ref": decision_model.decision_fingerprint_ref,
        "mode": decision_model.mode,
        "awareness_status": decision_model.awareness_status,
        "action": decision_model.action,
        "reason_refs": decision_model.reason_refs,
        "legacy_route_ref": decision_model.legacy_route_ref,
        "operator_visible_route_ref": decision_model.operator_visible_route_ref,
        "safe_disable_engaged": decision_model.safe_disable_engaged,
        "familiarity_state": decision_model.familiarity_state,
        "selected_operation_refs": decision_model.selected_operation_refs,
        "clarification_posture": decision_model.clarification_posture,
        "ordinary_no_tool_chat_preserved": True,
        "direct_chat_path_preserved": True,
        "extra_model_call_count": 0,
        "execution_performed": False,
        "authority_granted": False,
    }
    payload["projection_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw04-chat-shadow-inspection.v1",
            "contract_ref": TAW04_CONTRACT_REF,
            "cli_inspection_ref": TAW04_CLI_INSPECTION_REF,
            "api_inspection_ref": TAW04_API_INSPECTION_REF,
        },
        prefix="chat-shadow-inspection-ref:taw04",
    )
    return ChatShadowInspection.model_validate(payload)


def build_catalog_injection_cases() -> tuple[CatalogInjectionCase, ...]:
    return tuple(
        CatalogInjectionCase(
            field_path=field_path,
            case_ref=f"adversarial-case-ref:taw04:catalog-{field_path.replace('_', '-')}",
            rendering_path_ref=f"rendering-path-ref:taw04:{field_path.replace('_', '-')}",
        )
        for field_path in TAW04_CATALOG_INJECTION_FIELD_PATHS
    )


__all__ = [
    "AwarenessEvidenceStatus",
    "CatalogInjectionCase",
    "ChatShadowDecision",
    "ChatShadowEvidence",
    "ChatShadowInspection",
    "ShadowChatAction",
    "TAW04_API_INSPECTION_REF",
    "TAW04_CATALOG_INJECTION_FIELD_PATHS",
    "TAW04_CLI_INSPECTION_REF",
    "TAW04_CONTRACT_REF",
    "TAW04_ROUTER_REF",
    "TAW04_SAFE_DISABLE_REF",
    "build_chat_shadow_inspection",
    "build_catalog_injection_cases",
    "evaluate_chat_shadow",
]
