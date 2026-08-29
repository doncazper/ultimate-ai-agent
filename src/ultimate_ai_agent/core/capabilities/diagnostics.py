from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.chat_shadow import (
    AwarenessEvidenceStatus,
    ChatShadowDecision,
    ChatShadowInspection,
    ShadowChatAction,
    build_chat_shadow_inspection,
)
from ultimate_ai_agent.core.capabilities.familiarity import FamiliarityState
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW06_CONTRACT_REF = "contract-ref:taw06:operator-diagnostics:v1"
TAW06_READ_MODEL_REF = "read-model-ref:taw06:route-familiarity:v1"
TAW06_CLI_REF = "inspection-ref:taw06:cli:v1"
TAW06_API_REF = "inspection-ref:taw06:api:v1"
TAW06_MAX_REASON_REFS = 16
TAW06_MAX_SELECTED_OPERATION_REFS = 16
TAW06_MAX_MATERIAL_EFFECT_REFS = 16
TAW06_MAX_EVIDENCE_REFS = 32
TAW06_MAX_REQUEST_BYTES = 262_144
TAW06_MAX_STRING_CHARACTERS = 512
TAW06_MAX_REQUEST_NESTING_DEPTH = 32
TAW06_MAX_REQUEST_NODES = 4_096


class DiagnosticOperatorStatus(str, Enum):
    ready_for_review = "ready_for_review"
    input_required = "input_required"
    unavailable = "unavailable"
    approval_required = "approval_required"
    blocked = "blocked"
    evidence_unavailable = "evidence_unavailable"
    clarification_required = "clarification_required"
    unsupported = "unsupported"
    outcome_uncertain = "outcome_uncertain"


class DiagnosticApprovalPosture(str, Enum):
    not_required = "not_required"
    not_required_or_already_validated = "not_required_or_already_validated"
    exact_approval_required = "exact_approval_required"
    authority_blocked = "authority_blocked"
    not_applicable = "not_applicable"
    deferred_until_input_complete = "deferred_until_input_complete"
    deferred_until_available = "deferred_until_available"
    deferred_until_outcome_resolved = "deferred_until_outcome_resolved"
    unknown_until_clarified = "unknown_until_clarified"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            _json_ready(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("TAW-06 diagnostics must be canonical JSON") from exc


def _json_ready(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value


def _fingerprint(payload: object, *, prefix: str) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_ref(value: str, field_name: str) -> None:
    if len(value) > TAW06_MAX_STRING_CHARACTERS:
        raise ValueError(
            f"{field_name} exceeds the TAW-06 string bound of "
            f"{TAW06_MAX_STRING_CHARACTERS}"
        )
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str, *, max_items: int) -> None:
    if len(values) > max_items:
        raise ValueError(f"{field_name} exceeds the TAW-06 bound of {max_items}")
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


def _validate_request_shape_bounds(value: object) -> None:
    pending: list[tuple[object, int]] = [(value, 0)]
    visited_nodes = 0

    while pending:
        item, depth = pending.pop()
        visited_nodes += 1
        if visited_nodes > TAW06_MAX_REQUEST_NODES:
            raise ValueError(
                "TAW-06 diagnostic request exceeds the request node bound of "
                f"{TAW06_MAX_REQUEST_NODES}"
            )
        if depth > TAW06_MAX_REQUEST_NESTING_DEPTH:
            raise ValueError(
                "TAW-06 diagnostic request exceeds the nesting depth bound of "
                f"{TAW06_MAX_REQUEST_NESTING_DEPTH}"
            )
        if isinstance(item, BaseModel):
            pending.append((item.model_dump(mode="python"), depth))
            continue
        if isinstance(item, str):
            if len(item) > TAW06_MAX_STRING_CHARACTERS:
                raise ValueError("TAW-06 diagnostic request contains an oversized string")
            continue
        if isinstance(item, Mapping):
            for key, child in item.items():
                pending.append((key, depth + 1))
                pending.append((child, depth + 1))
            continue
        if isinstance(item, (list, tuple)):
            pending.extend((child, depth + 1) for child in item)


class ToolAwareDiagnosticRequest(_FrozenModel):
    schema_version: Literal["uaa-taw06-diagnostic-request.v1"] = (
        "uaa-taw06-diagnostic-request.v1"
    )
    decision: ChatShadowDecision

    @model_validator(mode="before")
    @classmethod
    def validate_request_materialization_bound(cls, value: Any) -> Any:
        if isinstance(value, cls):
            payload: object = value.model_dump(mode="python")
        else:
            payload = value
        _validate_request_shape_bounds(payload)
        canonical = _canonical_json(payload)
        if len(canonical.encode("utf-8")) > TAW06_MAX_REQUEST_BYTES:
            raise ValueError(
                f"TAW-06 diagnostic request exceeds {TAW06_MAX_REQUEST_BYTES} bytes"
            )
        if isinstance(payload, Mapping):
            decision = payload.get("decision")
            if isinstance(decision, BaseModel):
                decision = decision.model_dump(mode="python")
            if isinstance(decision, Mapping):
                for field_name, max_items in (
                    ("reason_refs", TAW06_MAX_REASON_REFS),
                    (
                        "selected_operation_refs",
                        TAW06_MAX_SELECTED_OPERATION_REFS,
                    ),
                    ("material_effect_refs", TAW06_MAX_MATERIAL_EFFECT_REFS),
                ):
                    field_value = decision.get(field_name)
                    if (
                        isinstance(field_value, (list, tuple))
                        and len(field_value) > max_items
                    ):
                        raise ValueError(
                            f"{field_name} exceeds the TAW-06 bound of {max_items}"
                        )
        return value

    @model_validator(mode="after")
    def validate_decision_bounds(self) -> "ToolAwareDiagnosticRequest":
        _validate_refs(
            self.decision.reason_refs,
            "reason_refs",
            max_items=TAW06_MAX_REASON_REFS,
        )
        _validate_refs(
            self.decision.selected_operation_refs,
            "selected_operation_refs",
            max_items=TAW06_MAX_SELECTED_OPERATION_REFS,
        )
        _validate_refs(
            self.decision.material_effect_refs,
            "material_effect_refs",
            max_items=TAW06_MAX_MATERIAL_EFFECT_REFS,
        )
        return self


def _route_fields(
    inspection: ChatShadowInspection,
) -> tuple[str, str]:
    if inspection.safe_disable_engaged:
        if inspection.awareness_status == AwarenessEvidenceStatus.valid:
            return (
                "Direct chat preserved; capability evidence blocked",
                "Awareness is valid, but capability evidence is unavailable. Ordinary direct chat remains available while capability proposal and execution stay blocked.",
            )
        return (
            "Direct chat preserved; awareness evidence invalid",
            "Awareness evidence is not trusted. Ordinary direct chat remains available while capability proposal and execution stay blocked.",
        )
    routes = {
        ShadowChatAction.preserve_direct_chat: (
            "Direct chat preserved",
            "The accepted direct-chat route remains active; shadow evidence does not change model context or activate a capability.",
        ),
        ShadowChatAction.record_capability_candidate: (
            "Capability candidate observed",
            "The accepted direct-chat route remains active while a reviewed capability candidate is recorded as non-authoritative evidence.",
        ),
        ShadowChatAction.recommend_clarification: (
            "Clarification recommended",
            "The accepted direct-chat route remains active; materially different effects should be clarified before any separate proposal.",
        ),
        ShadowChatAction.block_capability_proposal: (
            "Capability proposal blocked",
            "The accepted direct-chat route remains active, but current evidence blocks capability proposal and execution.",
        ),
        ShadowChatAction.record_outcome_uncertain: (
            "Outcome evidence uncertain",
            "The accepted direct-chat route remains active while missing or inconsistent terminal proof keeps the capability outcome uncertain.",
        ),
    }
    return routes[inspection.action]


def _familiarity_fields(
    inspection: ChatShadowInspection,
) -> tuple[
    DiagnosticOperatorStatus,
    str,
    str,
    DiagnosticApprovalPosture,
    str,
    tuple[str, ...],
    tuple[str, ...],
]:
    familiarity_state = inspection.familiarity_state
    if familiarity_state is None:
        return (
            DiagnosticOperatorStatus.evidence_unavailable,
            "Familiarity unavailable",
            "No familiarity conclusion is available because the awareness evidence failed closed.",
            DiagnosticApprovalPosture.not_applicable,
            "Approval is not evaluated while capability evidence is unavailable.",
            (
                "The diagnostic explains the evidence failure without exposing routine machinery in ordinary chat.",
                "Capability proposal and execution remain blocked.",
            ),
            ("Repair or refresh the reviewed capability evidence before proposal.",),
        )
    fields = {
        FamiliarityState.familiar_supported: (
            DiagnosticOperatorStatus.ready_for_review,
            "Familiar and supported",
            "One reviewed capability matches, required inputs are complete, and current evidence reports it ready for separate review.",
            DiagnosticApprovalPosture.not_required_or_already_validated,
            "TAW-04 does not retain whether approval was not applicable or exact request-scoped approval was already validated; this diagnostic grants no approval.",
            (
                "Readiness evidence is informational and does not create a proposal or execution authority.",
            ),
            (
                "Review the selected capability evidence before any separately authorized proposal.",
            ),
        ),
        FamiliarityState.familiar_input_required: (
            DiagnosticOperatorStatus.input_required,
            "Familiar; input required",
            "A reviewed capability matches, but required typed input is missing or invalid.",
            DiagnosticApprovalPosture.deferred_until_input_complete,
            "Approval posture is deferred until the required typed input is complete; exact approval may still be required afterward.",
            ("No input is inferred, collected, or persisted by this diagnostic.",),
            (
                "Provide the missing reviewed typed input through a separately governed path.",
            ),
        ),
        FamiliarityState.familiar_unavailable: (
            DiagnosticOperatorStatus.unavailable,
            "Familiar but unavailable",
            "A reviewed capability matches, but current availability evidence is disabled, unhealthy, stale, or absent.",
            DiagnosticApprovalPosture.deferred_until_available,
            "Approval posture is deferred until availability is restored; exact approval may still be required afterward.",
            (
                "Capability proposal and execution remain blocked while availability is not healthy.",
            ),
            ("Restore and revalidate capability availability before proposal.",),
        ),
        FamiliarityState.familiar_requires_approval: (
            DiagnosticOperatorStatus.approval_required,
            "Familiar; exact approval required",
            "A reviewed capability matches and current policy requires exact request-scoped approval before any effectful proposal can advance.",
            DiagnosticApprovalPosture.exact_approval_required,
            "Exact approval is required and has not been granted by this diagnostic.",
            (
                "An approval reference alone cannot mint authority or authorize execution.",
            ),
            (
                "Use the governing approval lane with exact scope and current policy evidence.",
            ),
        ),
        FamiliarityState.familiar_authority_blocked: (
            DiagnosticOperatorStatus.blocked,
            "Capability authority blocked",
            "Current policy, safety, or exact authority-lane evidence blocks proposal and execution; this state does not prove that exactly one reviewed capability matched.",
            DiagnosticApprovalPosture.authority_blocked,
            "Current authority is blocked; this diagnostic cannot override policy or safety.",
            (
                "No broad approval or settings toggle can bypass the blocked authority lane.",
            ),
            (
                "Resolve the exact policy, safety, or authority-lane evidence before proposal.",
            ),
        ),
        FamiliarityState.capability_evidence_unavailable: (
            DiagnosticOperatorStatus.evidence_unavailable,
            "Capability evidence unavailable",
            "The capability catalog is missing, corrupt, stale, over budget, or substituted, so familiarity fails closed.",
            DiagnosticApprovalPosture.not_applicable,
            "Approval is not evaluated without trustworthy capability evidence.",
            (
                "Ordinary direct chat remains available while capability proposal and execution stay blocked.",
            ),
            ("Repair or refresh the exact reviewed capability evidence.",),
        ),
        FamiliarityState.ambiguous: (
            DiagnosticOperatorStatus.clarification_required,
            "Capability intent ambiguous",
            "Multiple interpretations or capability matches remain, so a focused clarification is required before proposal.",
            DiagnosticApprovalPosture.unknown_until_clarified,
            "Approval posture remains unknown until the material effect is clarified.",
            (
                "The diagnostic does not choose an interpretation or broaden the requested effect.",
            ),
            ("Ask one focused clarification that distinguishes the material effects.",),
        ),
        FamiliarityState.novel_unsupported: (
            DiagnosticOperatorStatus.unsupported,
            "No supported capability",
            "No reviewed capability matches the possible tool intent.",
            DiagnosticApprovalPosture.not_applicable,
            "Approval is not applicable because no supported capability was identified.",
            ("The diagnostic does not invent, import, or activate a capability.",),
            (
                "Continue ordinary chat or separately add and review an exact capability contract.",
            ),
        ),
        FamiliarityState.outcome_uncertain: (
            DiagnosticOperatorStatus.outcome_uncertain,
            "Capability outcome uncertain",
            "Durable execution-start evidence exists, but exact terminal proof is missing or inconsistent.",
            DiagnosticApprovalPosture.deferred_until_outcome_resolved,
            "Approval posture remains deferred while the exact terminal outcome is uncertain; approval may have been required or already validated, and this diagnostic grants none.",
            (
                "The attempt remains an uncertain non-success until exact terminal evidence is available.",
            ),
            ("Reconcile the exact durable start and terminal receipt evidence.",),
        ),
    }
    if (
        familiarity_state == FamiliarityState.ambiguous
        and inspection.action == ShadowChatAction.preserve_direct_chat
        and inspection.clarification_posture == "not_applicable"
    ):
        return (
            DiagnosticOperatorStatus.ready_for_review,
            "Non-material capability ambiguity",
            "Multiple reviewed capability matches remain, but they do not differ materially; direct chat remains available and no clarification is required.",
            DiagnosticApprovalPosture.not_applicable,
            "Neither clarification nor approval is required by this evidence-only diagnostic.",
            (
                "The diagnostic does not choose a capability or create proposal authority.",
            ),
            (
                "Continue ordinary direct chat or separately review the matching capability evidence.",
            ),
        )
    return fields[familiarity_state]


def _derived_fields(inspection: ChatShadowInspection) -> dict[str, Any]:
    if len(inspection.reason_refs) > TAW06_MAX_REASON_REFS:
        raise ValueError("reason_refs exceed the TAW-06 diagnostic bound")
    if len(inspection.selected_operation_refs) > TAW06_MAX_SELECTED_OPERATION_REFS:
        raise ValueError("selected_operation_refs exceed the TAW-06 diagnostic bound")
    route_label, route_summary = _route_fields(inspection)
    (
        operator_status,
        familiarity_label,
        familiarity_summary,
        approval_posture,
        approval_summary,
        limitation_summaries,
        required_next_steps,
    ) = _familiarity_fields(inspection)
    evidence_refs = tuple(
        sorted(
            {
                inspection.decision_fingerprint_ref,
                inspection.projection_fingerprint_ref,
                *inspection.reason_refs,
                *inspection.selected_operation_refs,
            }
        )
    )
    if len(evidence_refs) > TAW06_MAX_EVIDENCE_REFS:
        raise ValueError("evidence_refs exceed the TAW-06 diagnostic bound")
    return {
        "awareness_status": inspection.awareness_status,
        "shadow_action": inspection.action,
        "familiarity_state": inspection.familiarity_state,
        "operator_status": operator_status,
        "route_label": route_label,
        "route_summary": route_summary,
        "familiarity_label": familiarity_label,
        "familiarity_summary": familiarity_summary,
        "approval_posture": approval_posture,
        "approval_summary": approval_summary,
        "limitation_summaries": limitation_summaries,
        "required_next_steps": required_next_steps,
        "reason_refs": inspection.reason_refs,
        "selected_operation_refs": inspection.selected_operation_refs,
        "evidence_refs": evidence_refs,
        "safe_disable_engaged": inspection.safe_disable_engaged,
    }


class ToolAwareOperatorDiagnostic(_FrozenModel):
    schema_version: Literal["uaa-taw06-operator-diagnostic.v1"] = (
        "uaa-taw06-operator-diagnostic.v1"
    )
    contract_ref: Literal["contract-ref:taw06:operator-diagnostics:v1"] = (
        TAW06_CONTRACT_REF
    )
    read_model_ref: Literal["read-model-ref:taw06:route-familiarity:v1"] = (
        TAW06_READ_MODEL_REF
    )
    cli_inspection_ref: Literal["inspection-ref:taw06:cli:v1"] = TAW06_CLI_REF
    api_inspection_ref: Literal["inspection-ref:taw06:api:v1"] = TAW06_API_REF
    source_inspection: ChatShadowInspection
    awareness_status: AwarenessEvidenceStatus
    shadow_action: ShadowChatAction
    familiarity_state: FamiliarityState | None
    operator_status: DiagnosticOperatorStatus
    route_label: str = Field(..., min_length=1, max_length=96)
    route_summary: str = Field(..., min_length=1, max_length=320)
    familiarity_label: str = Field(..., min_length=1, max_length=96)
    familiarity_summary: str = Field(..., min_length=1, max_length=320)
    approval_posture: DiagnosticApprovalPosture
    approval_summary: str = Field(..., min_length=1, max_length=320)
    limitation_summaries: tuple[str, ...] = Field(..., min_length=1, max_length=4)
    required_next_steps: tuple[str, ...] = Field(..., min_length=1, max_length=3)
    reason_refs: tuple[str, ...] = Field(..., max_length=TAW06_MAX_REASON_REFS)
    selected_operation_refs: tuple[str, ...] = Field(
        ..., max_length=TAW06_MAX_SELECTED_OPERATION_REFS
    )
    evidence_refs: tuple[str, ...] = Field(..., max_length=TAW06_MAX_EVIDENCE_REFS)
    safe_disable_engaged: bool
    routine_machinery_hidden_from_ordinary_chat: Literal[True] = True
    relevant_limitations_disclosed: Literal[True] = True
    operator_visible_route_changed: Literal[False] = False
    model_context_changed: Literal[False] = False
    raw_operator_content_included: Literal[False] = False
    raw_model_content_included: Literal[False] = False
    raw_provider_payload_included: Literal[False] = False
    raw_local_paths_included: Literal[False] = False
    model_call_count: Literal[0] = 0
    second_ordinary_chat_model_call_count: Literal[0] = 0
    provider_call_performed: Literal[False] = False
    proposal_constructed: Literal[False] = False
    approval_granted: Literal[False] = False
    execution_performed: Literal[False] = False
    connector_call_performed: Literal[False] = False
    external_write_performed: Literal[False] = False
    authority_granted: Literal[False] = False
    production_authority_granted: Literal[False] = False
    control_center_surface_added: Literal[False] = False
    redactions_applied: tuple[
        Literal["redaction-ref:taw06:safe-refs-only"],
        Literal["redaction-ref:taw06:raw-content-omitted"],
        Literal["redaction-ref:taw06:provider-payload-omitted"],
        Literal["redaction-ref:taw06:local-paths-omitted"],
    ]
    diagnostic_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_diagnostic(self) -> "ToolAwareOperatorDiagnostic":
        expected_fields = _derived_fields(self.source_inspection)
        for field_name, expected in expected_fields.items():
            if getattr(self, field_name) != expected:
                raise ValueError(f"TAW-06 diagnostic {field_name} binding drift")
        _validate_refs(
            self.reason_refs,
            "reason_refs",
            max_items=TAW06_MAX_REASON_REFS,
        )
        _validate_refs(
            self.selected_operation_refs,
            "selected_operation_refs",
            max_items=TAW06_MAX_SELECTED_OPERATION_REFS,
        )
        _validate_refs(
            self.evidence_refs,
            "evidence_refs",
            max_items=TAW06_MAX_EVIDENCE_REFS,
        )
        expected_fingerprint = _fingerprint(
            self.model_dump(mode="json", exclude={"diagnostic_fingerprint_ref"}),
            prefix="operator-diagnostic-ref:taw06",
        )
        if self.diagnostic_fingerprint_ref != expected_fingerprint:
            raise ValueError("TAW-06 diagnostic fingerprint binding drift")
        return self


def build_tool_aware_operator_diagnostic(
    request: ToolAwareDiagnosticRequest | ChatShadowDecision | dict[str, Any],
) -> ToolAwareOperatorDiagnostic:
    if isinstance(request, ChatShadowDecision):
        request_model = ToolAwareDiagnosticRequest(decision=request)
    elif isinstance(request, ToolAwareDiagnosticRequest):
        request_model = ToolAwareDiagnosticRequest.model_validate(
            request.model_dump(mode="python")
        )
    else:
        request_model = ToolAwareDiagnosticRequest.model_validate(dict(request))
    inspection = build_chat_shadow_inspection(request_model.decision)
    payload: dict[str, Any] = {
        "source_inspection": inspection,
        **_derived_fields(inspection),
        "redactions_applied": (
            "redaction-ref:taw06:safe-refs-only",
            "redaction-ref:taw06:raw-content-omitted",
            "redaction-ref:taw06:provider-payload-omitted",
            "redaction-ref:taw06:local-paths-omitted",
        ),
    }
    payload["diagnostic_fingerprint_ref"] = _fingerprint(
        {
            **payload,
            "schema_version": "uaa-taw06-operator-diagnostic.v1",
            "contract_ref": TAW06_CONTRACT_REF,
            "read_model_ref": TAW06_READ_MODEL_REF,
            "cli_inspection_ref": TAW06_CLI_REF,
            "api_inspection_ref": TAW06_API_REF,
            "routine_machinery_hidden_from_ordinary_chat": True,
            "relevant_limitations_disclosed": True,
            "operator_visible_route_changed": False,
            "model_context_changed": False,
            "raw_operator_content_included": False,
            "raw_model_content_included": False,
            "raw_provider_payload_included": False,
            "raw_local_paths_included": False,
            "model_call_count": 0,
            "second_ordinary_chat_model_call_count": 0,
            "provider_call_performed": False,
            "proposal_constructed": False,
            "approval_granted": False,
            "execution_performed": False,
            "connector_call_performed": False,
            "external_write_performed": False,
            "authority_granted": False,
            "production_authority_granted": False,
            "control_center_surface_added": False,
        },
        prefix="operator-diagnostic-ref:taw06",
    )
    return ToolAwareOperatorDiagnostic.model_validate(payload)


__all__ = [
    "DiagnosticApprovalPosture",
    "DiagnosticOperatorStatus",
    "TAW06_API_REF",
    "TAW06_CLI_REF",
    "TAW06_CONTRACT_REF",
    "TAW06_READ_MODEL_REF",
    "ToolAwareDiagnosticRequest",
    "ToolAwareOperatorDiagnostic",
    "build_tool_aware_operator_diagnostic",
]
