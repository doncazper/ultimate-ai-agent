from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.awareness import (
    CapabilityAwarenessCatalog,
    validate_capability_awareness_catalog,
)
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
TAW04_ACCEPTED_LEGACY_ROUTE_REF = "route-ref:taw04:accepted-legacy-direct-chat"
TAW04_CATALOG_INJECTION_FIELD_PATHS = (
    "aliases",
    "availability_metadata",
    "capability_id",
    "description",
    "effect_metadata",
    "examples",
    "input_schema",
    "operation_id",
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
    legacy_route_ref: Literal["route-ref:taw04:accepted-legacy-direct-chat"] = (
        TAW04_ACCEPTED_LEGACY_ROUTE_REF
    )
    safe_disable_ref: Literal["safe-disable-ref:taw04:accepted-legacy-router"] = (
        TAW04_SAFE_DISABLE_REF
    )
    assessment: FamiliarityAssessment | None = None
    catalog: CapabilityAwarenessCatalog | None = None
    hydration: CapabilityHydrationResult | None = None
    observed_at_epoch_seconds: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_evidence(self) -> "ChatShadowEvidence":
        _validate_ref(self.legacy_route_ref, "legacy_route_ref")
        _validate_ref(self.safe_disable_ref, "safe_disable_ref")
        if self.awareness_status == AwarenessEvidenceStatus.valid:
            if (
                self.assessment is None
                or self.catalog is None
                or self.observed_at_epoch_seconds is None
            ):
                raise ValueError(
                    "valid awareness requires exact assessment, catalog, and observation evidence"
                )
        elif any(
            value is not None
            for value in (
                self.assessment,
                self.catalog,
                self.hydration,
                self.observed_at_epoch_seconds,
            )
        ):
            raise ValueError("invalid awareness cannot carry trusted derived evidence")
        validated_catalog: CapabilityAwarenessCatalog | None = None
        if self.catalog is not None and self.assessment is not None:
            validated_catalog = validate_capability_awareness_catalog(
                self.catalog.model_dump(mode="python"),
                expected_catalog_epoch_ref=self.assessment.catalog_epoch_ref,
                expected_availability_epoch_ref=self.assessment.availability_epoch_ref,
                expected_policy_snapshot_ref=self.assessment.policy_snapshot_ref,
                observed_at_epoch_seconds=self.observed_at_epoch_seconds,
            )
            if (
                self.assessment.catalog_fingerprint_ref is None
                or validated_catalog.catalog_fingerprint_ref
                != self.assessment.catalog_fingerprint_ref
            ):
                raise ValueError("assessment and catalog fingerprint binding mismatch")
            envelope_by_operation = {
                item.operation_id: item for item in validated_catalog.envelopes
            }
            candidate_envelopes = tuple(
                envelope_by_operation.get(operation_id)
                for operation_id in self.assessment.candidate_operation_refs
            )
            if any(item is None for item in candidate_envelopes):
                raise ValueError("assessment contains a non-catalog candidate")
            expected_envelope_refs = tuple(
                sorted(item.envelope_fingerprint_ref for item in candidate_envelopes)
            )
            expected_schema_refs = tuple(
                sorted(
                    item.operation_schema_fingerprint_ref
                    for item in candidate_envelopes
                )
            )
            if (
                expected_envelope_refs
                != self.assessment.candidate_envelope_fingerprint_refs
                or expected_schema_refs
                != self.assessment.candidate_operation_schema_fingerprint_refs
            ):
                raise ValueError("assessment candidate catalog binding mismatch")
        if self.hydration is not None:
            if self.assessment is None or validated_catalog is None:
                raise ValueError(
                    "hydration requires exact assessment and catalog evidence"
                )
            if (
                self.assessment.catalog_fingerprint_ref is None
                or self.hydration.catalog_fingerprint_ref
                != self.assessment.catalog_fingerprint_ref
            ):
                raise ValueError("assessment and hydration catalog binding mismatch")
            candidate_refs = set(self.assessment.candidate_operation_refs)
            envelope_by_operation = {
                item.operation_id: item for item in validated_catalog.envelopes
            }
            if any(
                item.operation_id not in candidate_refs
                or item.envelope_fingerprint_ref
                != envelope_by_operation[item.operation_id].envelope_fingerprint_ref
                or item.operation_schema_fingerprint_ref
                != envelope_by_operation[
                    item.operation_id
                ].operation_schema_fingerprint_ref
                for item in self.hydration.manifests
            ):
                raise ValueError("hydration contains non-candidate bound evidence")
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
    legacy_route_ref: Literal["route-ref:taw04:accepted-legacy-direct-chat"]
    operator_visible_route_ref: Literal["route-ref:taw04:accepted-legacy-direct-chat"]
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
        expected_action = _derive_shadow_action(
            awareness_status=self.awareness_status,
            familiarity_state=self.familiarity_state,
            material_effect_refs=self.material_effect_refs,
        )
        if (
            self.action != expected_action[0]
            or self.reason_refs != expected_action[1]
            or self.safe_disable_engaged != expected_action[2]
            or self.clarification_posture != expected_action[3]
            or self.clarification_contract_ref != expected_action[4]
        ):
            raise ValueError("chat shadow action-state matrix drift")
        if self.awareness_status == AwarenessEvidenceStatus.valid:
            if (
                self.familiarity_state is None
                or self.assessment_fingerprint_ref is None
            ):
                raise ValueError(
                    "valid awareness requires exact assessment output evidence"
                )
        elif any(
            value is not None
            for value in (
                self.familiarity_state,
                self.assessment_fingerprint_ref,
                self.hydration_fingerprint_ref,
            )
        ):
            raise ValueError("invalid awareness cannot publish derived output evidence")
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


def _material_effect_refs(evidence: ChatShadowEvidence) -> tuple[str, ...]:
    if (
        evidence.assessment is None
        or evidence.catalog is None
        or evidence.assessment.state != FamiliarityState.ambiguous
    ):
        return ()
    candidate_refs = set(evidence.assessment.candidate_operation_refs)
    return tuple(
        sorted(
            {
                f"effect-class-ref:taw04:{item.effect_class.value}"
                for item in evidence.catalog.envelopes
                if item.operation_id in candidate_refs
            }
        )
    )


def _derive_shadow_action(
    *,
    awareness_status: AwarenessEvidenceStatus,
    familiarity_state: FamiliarityState | None,
    material_effect_refs: tuple[str, ...],
) -> tuple[
    ShadowChatAction,
    tuple[str, ...],
    bool,
    Literal["not_applicable", "shadow_recommended"],
    str | None,
]:
    if awareness_status != AwarenessEvidenceStatus.valid:
        if familiarity_state is not None or material_effect_refs:
            raise ValueError("invalid awareness cannot derive familiarity routing")
        return (
            ShadowChatAction.preserve_direct_chat,
            (f"reason-ref:taw04:awareness-{awareness_status.value}",),
            True,
            "not_applicable",
            None,
        )
    if familiarity_state is None:
        raise ValueError("valid awareness requires a familiarity state")
    if familiarity_state == FamiliarityState.capability_evidence_unavailable:
        return (
            ShadowChatAction.block_capability_proposal,
            ("reason-ref:taw04:capability-evidence-unavailable",),
            True,
            "not_applicable",
            None,
        )
    if familiarity_state == FamiliarityState.outcome_uncertain:
        return (
            ShadowChatAction.record_outcome_uncertain,
            ("reason-ref:taw04:durable-terminal-proof-required",),
            False,
            "not_applicable",
            None,
        )
    if familiarity_state == FamiliarityState.ambiguous:
        if len(material_effect_refs) >= 2:
            return (
                ShadowChatAction.recommend_clarification,
                ("reason-ref:taw04:material-effect-ambiguity",),
                False,
                "shadow_recommended",
                "turn-contract-ref:taw04:ask-clarifying-question",
            )
        return (
            ShadowChatAction.preserve_direct_chat,
            ("reason-ref:taw04:non-material-ambiguity",),
            False,
            "not_applicable",
            None,
        )
    if familiarity_state in {
        FamiliarityState.familiar_authority_blocked,
        FamiliarityState.familiar_unavailable,
    }:
        return (
            ShadowChatAction.block_capability_proposal,
            (f"reason-ref:taw04:{familiarity_state.value}",),
            False,
            "not_applicable",
            None,
        )
    if familiarity_state == FamiliarityState.novel_unsupported:
        return (
            ShadowChatAction.preserve_direct_chat,
            ("reason-ref:taw04:no-supported-capability",),
            False,
            "not_applicable",
            None,
        )
    return (
        ShadowChatAction.record_capability_candidate,
        (f"reason-ref:taw04:{familiarity_state.value}",),
        False,
        "not_applicable",
        None,
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
    material_effect_refs = _material_effect_refs(evidence_model)
    familiarity_state = assessment.state if assessment is not None else None
    (
        action,
        reason_refs,
        safe_disable,
        clarification_posture,
        clarification_contract_ref,
    ) = _derive_shadow_action(
        awareness_status=evidence_model.awareness_status,
        familiarity_state=familiarity_state,
        material_effect_refs=material_effect_refs,
    )
    selected_operation_refs: tuple[str, ...] = ()
    if (
        assessment is not None
        and not safe_disable
        and action == ShadowChatAction.record_capability_candidate
    ):
        selected_operation_refs = _selected_operations(assessment, hydration)

    payload: dict[str, Any] = {
        "awareness_status": evidence_model.awareness_status,
        "action": action,
        "reason_refs": tuple(sorted(reason_refs)),
        "legacy_route_ref": evidence_model.legacy_route_ref,
        "operator_visible_route_ref": evidence_model.legacy_route_ref,
        "safe_disable_ref": evidence_model.safe_disable_ref,
        "safe_disable_engaged": safe_disable,
        "familiarity_state": familiarity_state,
        "assessment_fingerprint_ref": (
            assessment.assessment_fingerprint_ref if assessment is not None else None
        ),
        "hydration_fingerprint_ref": (
            hydration.hydration_fingerprint_ref if hydration is not None else None
        ),
        "selected_operation_refs": selected_operation_refs,
        "material_effect_refs": material_effect_refs,
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
    "TAW04_ACCEPTED_LEGACY_ROUTE_REF",
    "TAW04_CATALOG_INJECTION_FIELD_PATHS",
    "TAW04_CLI_INSPECTION_REF",
    "TAW04_CONTRACT_REF",
    "TAW04_ROUTER_REF",
    "TAW04_SAFE_DISABLE_REF",
    "build_chat_shadow_inspection",
    "build_catalog_injection_cases",
    "evaluate_chat_shadow",
]
