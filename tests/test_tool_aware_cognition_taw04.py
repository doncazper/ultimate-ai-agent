from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.capabilities import (
    AwarenessEvidenceStatus,
    CapabilityAwarenessBinding,
    CapabilityHealthStatus,
    CapabilityKind,
    CapabilityManifest,
    CapabilityMatchEvidence,
    CapabilityRegistry,
    ChatShadowEvidence,
    CapabilityHydrationResult,
    CoordinationMode,
    FamiliarityAssessmentEvidence,
    FamiliarityState,
    HydrationSourceEvidence,
    HydrationTokenAccounting,
    ManifestTokenCount,
    PolicyDecisionStatus,
    RetrievalConstraints,
    SafetyPolicy,
    ShadowChatAction,
    SideEffectLevel,
    TerminalOutcomeEvidence,
    assess_familiarity,
    build_capability_awareness_catalog,
    build_catalog_injection_cases,
    build_chat_shadow_inspection,
    build_progressive_capability_cache,
    discover_capabilities,
    evaluate_chat_shadow,
    hydrate_capability_manifests,
    operation_schema_from_manifest,
)
from ultimate_ai_agent.core.capabilities import chat_shadow, retrieval
from ultimate_ai_agent.core.capabilities.chat_shadow import (
    TAW04_API_INSPECTION_REF,
    TAW04_ACCEPTED_LEGACY_ROUTE_REF,
    TAW04_CATALOG_INJECTION_FIELD_PATHS,
    TAW04_CLI_INSPECTION_REF,
    TAW04_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


EVAL_SET_REF = "evaluation-set-ref:taw02:sha256:" + "4" * 64
LEGACY_ROUTE_REF = TAW04_ACCEPTED_LEGACY_ROUTE_REF
SAFE_DISABLE_REF = TAW04_SAFE_DISABLE_REF


def _catalog(*, two: bool = False, same_effect: bool = False):
    registry = CapabilityRegistry()
    operations = []
    bindings = []
    definitions = [
        ("read-notes", SideEffectLevel.read),
        (
            "read-notes-copy" if same_effect else "write-notes",
            SideEffectLevel.read if same_effect else SideEffectLevel.write,
        ),
    ][: 2 if two else 1]
    for suffix, effect in definitions:
        mutating = effect == SideEffectLevel.write
        manifest = CapabilityManifest(
            id=f"capability-ref:taw04:{suffix}",
            version="1.0.0",
            kind=CapabilityKind.tool,
            name=f"Reviewed {suffix}",
            description="Operate on bounded reviewed note references.",
            tags=["notes", "reviewed"],
            examples=["Use reviewed note references."],
            anti_examples=["Do not broaden scope."],
            input_schema={
                "type": "object",
                "properties": {"note_ref": {"type": "string"}},
                "required": ["note_ref"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "properties": {"result_ref": {"type": "string"}},
                "required": ["result_ref"],
                "additionalProperties": False,
            },
            input_modes=["structured_ref"],
            output_modes=["artifact"],
            side_effects=effect,
            risk_level=RiskLevel.medium if mutating else RiskLevel.low,
            approval_required=mutating,
            rollback_supported=mutating,
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            concurrency_safe=not mutating,
            single_writer_required=mutating,
            safety=SafetyPolicy(
                allow_parallel=not mutating,
                require_single_writer=mutating,
                approval_required=mutating,
                max_risk_level=RiskLevel.medium if mutating else RiskLevel.low,
                max_side_effect_level=effect,
            ),
        )
        registry.register(manifest, object())
        operation = operation_schema_from_manifest(
            manifest,
            operation_id=f"operation-ref:taw04:{suffix}",
            operation_version="1.0.0",
            operator_summary=f"Use reviewed {suffix} references.",
            aliases=(f"use {suffix}",),
            positive_eval_refs=(f"eval-ref:taw04:{suffix}-positive",),
            negative_eval_refs=(f"eval-ref:taw04:{suffix}-negative",),
            ambiguity_eval_refs=(f"eval-ref:taw04:{suffix}-ambiguity",),
            adversarial_eval_refs=(f"eval-ref:taw04:{suffix}-adversarial",),
            provenance_ref=f"provenance-ref:taw04:{suffix}",
            review_ref=f"review-ref:taw04:{suffix}",
        )
        operations.append(operation)
        bindings.append(
            CapabilityAwarenessBinding(
                operation_id=operation.operation_id,
                health_status=CapabilityHealthStatus.healthy,
                availability_ref=f"availability-ref:taw04:{suffix}",
                policy_decision_status=PolicyDecisionStatus.allowed,
                policy_snapshot_ref="policy-snapshot-ref:taw04:v1",
                authority_lane_status="graduated" if mutating else "not_applicable",
                authority_lane_ref=f"authority-lane-ref:taw04:{suffix}",
                safe_disable_ref=SAFE_DISABLE_REF,
                rollback_posture="supported" if mutating else "not_applicable",
                rollback_ref=f"rollback-ref:taw04:{suffix}",
                terminal_proof_contract_ref=f"terminal-proof-contract-ref:taw04:{suffix}",
                expected_terminal_status_refs=(
                    f"terminal-status-ref:taw04:{suffix}-complete",
                ),
            )
        )
    catalog = build_capability_awareness_catalog(
        registry,
        operation_schemas=operations,
        bindings=bindings,
        catalog_epoch_ref="catalog-epoch-ref:taw04:v1",
        availability_epoch_ref="availability-epoch-ref:taw04:v1",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )
    return catalog, tuple(operations)


def _match(envelope, *, semantic: bool = False) -> CapabilityMatchEvidence:
    suffix = envelope.operation_id.rsplit(":", 1)[-1]
    return CapabilityMatchEvidence(
        operation_id=envelope.operation_id,
        envelope_fingerprint_ref=envelope.envelope_fingerprint_ref,
        match_kind="semantic" if semantic else "deterministic",
        match_evidence_ref=f"match-evidence-ref:taw04:{suffix}",
        relevance_basis_points=8_000 if semantic else 10_000,
        availability_status="available",
        availability_ref=envelope.availability_ref,
        availability_epoch_ref=envelope.availability_epoch_ref,
    )


def _assessment(*, state: str = "supported"):
    catalog, operations = _catalog(
        two=state in {"ambiguous", "ambiguous_same_effect"},
        same_effect=state == "ambiguous_same_effect",
    )
    matches = tuple(
        _match(item, semantic=index == 1)
        for index, item in enumerate(catalog.envelopes)
    )
    selected = matches[0].operation_id if len(matches) == 1 else None
    validated = (
        catalog.envelopes[0].required_input_field_refs if len(matches) == 1 else ()
    )
    evidence_status = "corrupt" if state == "unavailable" else "valid"
    if state == "unavailable":
        matches = ()
        selected = None
        validated = ()
    terminal = (
        TerminalOutcomeEvidence(
            status="terminal_missing",
            execution_attempt_ref="execution-attempt-ref:taw04:one",
            durable_start_evidence_ref="durable-start-evidence-ref:taw04:one",
        )
        if state == "outcome_uncertain"
        else TerminalOutcomeEvidence()
    )
    evidence = FamiliarityAssessmentEvidence(
        possible_tool_intent=True,
        sentinel_evidence_ref="sentinel-evidence-ref:taw04:positive",
        catalog_evidence_status=evidence_status,
        expected_catalog_epoch_ref=catalog.catalog_epoch_ref,
        expected_availability_epoch_ref=catalog.availability_epoch_ref,
        expected_policy_snapshot_ref=catalog.policy_snapshot_ref,
        observed_at_epoch_seconds=150,
        interpretation_refs=("interpretation-ref:taw04:one",),
        candidate_matches=matches,
        selected_operation_id=selected,
        policy_decision_status=PolicyDecisionStatus.allowed,
        safety_decision_status="allowed",
        safety_snapshot_ref="safety-snapshot-ref:taw04:v1",
        validated_input_field_refs=validated,
        approval_validation_status="not_applicable",
        readiness_status="ready" if len(matches) == 1 else "not_applicable",
        terminal_outcome=terminal,
        evaluation_set_fingerprint_ref=EVAL_SET_REF,
    )
    return (
        assess_familiarity(
            evidence,
            catalog=None if state == "unavailable" else catalog,
        ),
        catalog,
        operations,
    )


def _evidence(assessment_bundle):
    assessment, catalog, _operations = assessment_bundle
    return ChatShadowEvidence(
        awareness_status=AwarenessEvidenceStatus.valid,
        assessment=assessment,
        catalog=catalog,
        observed_at_epoch_seconds=150,
    )


def _hydration(catalog, operations):
    environment_ref = "environment-fingerprint-ref:taw04:test"
    cache = build_progressive_capability_cache(
        catalog,
        operation_schemas=operations,
        environment_fingerprint_ref=environment_ref,
        observed_at_epoch_seconds=150,
    )
    shortlist = discover_capabilities(
        cache,
        normalized_request="read write notes",
        constraints=RetrievalConstraints(
            accepted_effect_classes=(SideEffectLevel.read, SideEffectLevel.write)
        ),
        environment_fingerprint_ref=environment_ref,
        observed_at_epoch_seconds=150,
    )
    sources = tuple(
        HydrationSourceEvidence(
            operation_id=item.operation_id,
            source_kind="canonical_registered",
            provenance_ref=item.provenance_ref,
            review_ref=item.review_ref,
            reviewed=True,
        )
        for item in sorted(operations, key=lambda value: value.operation_id)
    )
    accounting = HydrationTokenAccounting(
        backend_ref="backend-ref:taw04:qwen-3-8-27b-local",
        tokenizer_artifact_ref="artifact-ref:taw04:qwen-vocabulary",
        tokenizer_fingerprint_ref="artifact-fingerprint-ref:taw04:qwen-v1",
        prompt_format_ref="prompt-format-ref:taw04:not-assembled",
        estimator_ref="estimator-ref:taw04:conservative-v1",
        model_context_tokens=128_000,
        non_hydration_prompt_tokens=1_000,
        reserved_output_tokens=4_000,
        manifest_counts=tuple(
            ManifestTokenCount(operation_id=item.operation_id, estimated_tokens=100)
            for item in sorted(operations, key=lambda value: value.operation_id)
        ),
    )
    return hydrate_capability_manifests(
        shortlist,
        cache,
        catalog,
        operation_schemas=operations,
        source_evidence=sources,
        token_accounting=accounting,
        environment_fingerprint_ref=environment_ref,
        observed_at_epoch_seconds=150,
    )


@pytest.mark.parametrize(
    "status",
    [
        AwarenessEvidenceStatus.missing,
        AwarenessEvidenceStatus.corrupt,
        AwarenessEvidenceStatus.stale,
        AwarenessEvidenceStatus.unreadable,
        AwarenessEvidenceStatus.over_budget,
    ],
)
def test_awareness_failures_safe_disable_to_ordinary_chat(status) -> None:
    decision = evaluate_chat_shadow(
        ChatShadowEvidence(
            awareness_status=status,
        )
    )
    assert decision.action == ShadowChatAction.preserve_direct_chat
    assert decision.safe_disable_engaged is True
    assert decision.operator_visible_route_ref == LEGACY_ROUTE_REF
    assert decision.ordinary_no_tool_chat_preserved is True
    assert decision.model_visible_manifest_refs == ()
    assert decision.extra_model_call_count == 0
    assert decision.execution_performed is False


def test_supported_capability_is_shadow_evidence_only() -> None:
    decision = evaluate_chat_shadow(_evidence(_assessment()))
    assert decision.action == ShadowChatAction.record_capability_candidate
    assert decision.familiarity_state == FamiliarityState.familiar_supported
    assert decision.operator_visible_routing_changed is False
    assert decision.model_context_changed is False
    assert decision.proposal_constructed is False
    assert decision.approval_requested is False
    assert decision.provider_call_performed is False
    assert decision.web_fetch_performed is False
    assert decision.authority_granted is False


def test_clarification_is_recommended_only_for_materially_different_effects() -> None:
    material = evaluate_chat_shadow(_evidence(_assessment(state="ambiguous")))
    assert material.action == ShadowChatAction.recommend_clarification
    assert material.clarification_posture == "shadow_recommended"
    assert material.operator_visible_routing_changed is False

    non_material = evaluate_chat_shadow(
        _evidence(_assessment(state="ambiguous_same_effect"))
    )
    assert non_material.action == ShadowChatAction.preserve_direct_chat
    assert non_material.clarification_posture == "not_applicable"


def test_missing_capability_evidence_blocks_proposal_but_preserves_chat() -> None:
    decision = evaluate_chat_shadow(
        ChatShadowEvidence(awareness_status=AwarenessEvidenceStatus.corrupt)
    )
    assert decision.action == ShadowChatAction.preserve_direct_chat
    assert decision.safe_disable_engaged is True
    assert decision.ordinary_no_tool_chat_preserved is True
    assert decision.selected_operation_refs == ()


def test_outcome_uncertain_remains_evidence_only() -> None:
    decision = evaluate_chat_shadow(_evidence(_assessment(state="outcome_uncertain")))
    assert decision.action == ShadowChatAction.record_outcome_uncertain
    assert decision.execution_performed is False
    assert decision.operator_visible_route_ref == LEGACY_ROUTE_REF


def test_cli_and_api_share_one_redacted_inspection_projection() -> None:
    decision = evaluate_chat_shadow(_evidence(_assessment()))
    projection = build_chat_shadow_inspection(decision)
    assert projection.cli_inspection_ref == TAW04_CLI_INSPECTION_REF
    assert projection.api_inspection_ref == TAW04_API_INSPECTION_REF
    assert projection.decision_fingerprint_ref == decision.decision_fingerprint_ref
    assert projection.extra_model_call_count == 0
    assert projection.execution_performed is False


def test_copied_decision_cannot_bypass_route_binding() -> None:
    decision = evaluate_chat_shadow(_evidence(_assessment()))
    copied = decision.model_copy(
        update={"operator_visible_route_ref": "route-ref:taw04:substituted"}
    )
    with pytest.raises(ValidationError, match="literal_error"):
        build_chat_shadow_inspection(copied)


def test_safe_disable_target_is_not_caller_selectable() -> None:
    with pytest.raises(ValidationError, match="literal_error"):
        ChatShadowEvidence(
            awareness_status=AwarenessEvidenceStatus.stale,
            safe_disable_ref="safe-disable-ref:taw04:substituted",
        )
    with pytest.raises(ValidationError, match="literal_error"):
        ChatShadowEvidence(
            awareness_status=AwarenessEvidenceStatus.stale,
            legacy_route_ref="route-ref:taw04:substituted",
        )


def test_valid_awareness_revalidates_catalog_freshness() -> None:
    assessment, catalog, _operations = _assessment()
    with pytest.raises(ValidationError, match="stale"):
        ChatShadowEvidence(
            awareness_status=AwarenessEvidenceStatus.valid,
            assessment=assessment,
            catalog=catalog,
            observed_at_epoch_seconds=201,
        )


def test_hydration_requires_per_candidate_envelope_and_schema_tuple() -> None:
    assessment, catalog, operations = _assessment(state="ambiguous")
    hydration = _hydration(catalog, operations)
    assert len(hydration.manifests) == 2
    first, second = hydration.manifests
    swapped = first.model_copy(
        update={
            "envelope_fingerprint_ref": second.envelope_fingerprint_ref,
            "operation_schema_fingerprint_ref": second.operation_schema_fingerprint_ref,
        }
    )
    payload = hydration.model_dump(mode="json")
    payload["manifests"] = [
        swapped.model_dump(mode="json"),
        second.model_dump(mode="json"),
    ]
    payload_without_fingerprint = dict(payload)
    payload_without_fingerprint.pop("hydration_fingerprint_ref")
    payload["hydration_fingerprint_ref"] = retrieval._fingerprint(
        payload_without_fingerprint,
        prefix="capability-hydration-ref:taw03",
    )
    substituted = CapabilityHydrationResult.model_validate(payload)
    with pytest.raises(ValidationError, match="non-candidate bound evidence"):
        ChatShadowEvidence(
            awareness_status=AwarenessEvidenceStatus.valid,
            assessment=assessment,
            catalog=catalog,
            hydration=substituted,
            observed_at_epoch_seconds=150,
        )


def test_decision_rejects_recomputed_action_state_drift() -> None:
    decision = evaluate_chat_shadow(_evidence(_assessment()))
    payload = decision.model_dump(mode="json")
    payload["action"] = ShadowChatAction.block_capability_proposal.value
    payload_without_fingerprint = dict(payload)
    payload_without_fingerprint.pop("decision_fingerprint_ref")
    payload["decision_fingerprint_ref"] = chat_shadow._fingerprint(
        payload_without_fingerprint,
        prefix="chat-shadow-decision-ref:taw04",
    )
    with pytest.raises(ValidationError, match="action-state matrix drift"):
        build_chat_shadow_inspection(payload)


def test_catalog_injection_inventory_is_complete_and_non_model_visible() -> None:
    cases = build_catalog_injection_cases()
    assert tuple(item.field_path for item in cases) == (
        TAW04_CATALOG_INJECTION_FIELD_PATHS
    )
    assert len({item.case_ref for item in cases}) == len(cases)
    assert all(item.model_visible_in_shadow is False for item in cases)
    assert all(item.prompt_assembly_performed is False for item in cases)
    assert all(
        item.response_census_status == "blocked_until_no_effect_active_replay"
        for item in cases
    )
