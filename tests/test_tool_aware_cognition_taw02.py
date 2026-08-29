from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from scripts import verify_tool_aware_cognition_taw02 as verifier
from ultimate_ai_agent.core.capabilities import (
    CapabilityAwarenessBinding,
    CapabilityHealthStatus,
    CapabilityKind,
    CapabilityManifest,
    CapabilityMatchEvidence,
    CapabilityRegistry,
    CoordinationMode,
    FamiliarityAssessment,
    FamiliarityAssessmentEvidence,
    FamiliarityReasonCode,
    FamiliarityState,
    PolicyDecisionStatus,
    SafetyPolicy,
    SideEffectLevel,
    TerminalOutcomeEvidence,
    assess_familiarity,
    build_capability_awareness_catalog,
    operation_schema_from_manifest,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


EVAL_SET_REF = "evaluation-set-ref:taw02:sha256:" + "a" * 64


def _catalog(*, mutating: bool = False, second: bool = False, unhealthy: bool = False):
    manifests = []
    count = 2 if second else 1
    for index in range(count):
        suffix = "notes-write" if mutating else f"notes-read-{index + 1}"
        side_effect = SideEffectLevel.write if mutating else SideEffectLevel.read
        manifest = CapabilityManifest(
            id=f"capability-ref:test:{suffix}",
            version="1.0.0",
            kind=CapabilityKind.tool,
            name="Reviewed Notes",
            description="Operate on reviewed note metadata for one bounded project.",
            tags=["notes", "reviewed"],
            examples=["Use reviewed project notes."],
            anti_examples=["Do not use unrelated records."],
            input_schema={
                "type": "object",
                "properties": {
                    "project_ref": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["project_ref"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "properties": {"result_refs": {"type": "array"}},
                "required": ["result_refs"],
                "additionalProperties": False,
            },
            input_modes=["structured_ref"],
            output_modes=["artifact"],
            side_effects=side_effect,
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
                max_side_effect_level=side_effect,
            ),
        )
        manifests.append(manifest)
    registry = CapabilityRegistry()
    operations = []
    bindings = []
    for manifest in manifests:
        registry.register(manifest, object())
        operation_id = manifest.id.replace("capability-ref", "operation-ref")
        operations.append(
            operation_schema_from_manifest(
                manifest,
                operation_id=operation_id,
                operation_version="1.0.0",
                operator_summary="Use reviewed note references for one project.",
                aliases=("find reviewed notes", "use reviewed notes"),
                positive_eval_refs=("eval-ref:taw02:positive",),
                negative_eval_refs=("eval-ref:taw02:negative",),
                ambiguity_eval_refs=("eval-ref:taw02:ambiguity",),
                adversarial_eval_refs=("eval-ref:taw02:adversarial",),
                provenance_ref="provenance-ref:taw02:repository-reviewed",
                review_ref="review-ref:taw02:founder-dogfood",
            )
        )
        bindings.append(
            CapabilityAwarenessBinding(
                operation_id=operation_id,
                health_status=(
                    CapabilityHealthStatus.unhealthy
                    if unhealthy
                    else CapabilityHealthStatus.healthy
                ),
                availability_ref=f"availability-ref:test:{manifest.id.rsplit(':', 1)[-1]}",
                policy_decision_status=(
                    PolicyDecisionStatus.approval_required
                    if mutating
                    else PolicyDecisionStatus.allowed
                ),
                policy_snapshot_ref="policy-snapshot-ref:test:v1",
                authority_lane_status="graduated" if mutating else "not_applicable",
                authority_lane_ref=(
                    "authority-lane-ref:test:notes-write"
                    if mutating
                    else "authority-lane-ref:test:not-applicable"
                ),
                safe_disable_ref="safe-disable-ref:taw02:legacy-router",
                rollback_posture="supported" if mutating else "not_applicable",
                rollback_ref="rollback-ref:taw02:notes",
                terminal_proof_contract_ref="terminal-proof-contract-ref:test:receipt:v1",
                expected_terminal_status_refs=("terminal-status-ref:test:completed",),
            )
        )
    return build_capability_awareness_catalog(
        registry,
        operation_schemas=tuple(operations),
        bindings=tuple(bindings),
        catalog_epoch_ref="catalog-epoch-ref:test:one",
        availability_epoch_ref="availability-epoch-ref:test:one",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )


def _match(envelope, *, availability_status: str = "available", semantic: bool = False):
    return CapabilityMatchEvidence(
        operation_id=envelope.operation_id,
        envelope_fingerprint_ref=envelope.envelope_fingerprint_ref,
        match_kind="semantic" if semantic else "deterministic",
        match_evidence_ref=f"match-evidence-ref:taw02:{envelope.operation_id.rsplit(':', 1)[-1]}",
        relevance_basis_points=8750 if semantic else 10_000,
        availability_status=availability_status,
        availability_ref=envelope.availability_ref,
        availability_epoch_ref=envelope.availability_epoch_ref,
    )


def _evidence(catalog, **overrides):
    matches = overrides.pop("candidate_matches", (_match(catalog.envelopes[0]),))
    selected = overrides.pop(
        "selected_operation_id", matches[0].operation_id if len(matches) == 1 else None
    )
    required = (
        catalog.envelopes[0].required_input_field_refs if len(matches) == 1 else ()
    )
    payload = {
        "possible_tool_intent": True,
        "sentinel_evidence_ref": "sentinel-evidence-ref:taw02:positive",
        "catalog_evidence_status": "valid",
        "expected_catalog_epoch_ref": catalog.catalog_epoch_ref,
        "expected_availability_epoch_ref": catalog.availability_epoch_ref,
        "expected_policy_snapshot_ref": catalog.policy_snapshot_ref,
        "observed_at_epoch_seconds": 150,
        "interpretation_refs": ("interpretation-ref:taw02:one",),
        "candidate_matches": matches,
        "selected_operation_id": selected,
        "policy_decision_status": catalog.envelopes[0].policy_decision_status,
        "policy_reason_refs": (),
        "safety_decision_status": "allowed",
        "safety_snapshot_ref": "safety-snapshot-ref:taw02:v1",
        "safety_reason_refs": (),
        "validated_input_field_refs": required,
        "missing_input_field_refs": (),
        "invalid_input_field_refs": (),
        "approval_validation_status": (
            "required"
            if catalog.envelopes[0].approval_class == "exact_approval_required"
            else "not_applicable"
        ),
        "readiness_status": "ready",
        "terminal_outcome": TerminalOutcomeEvidence(),
        "evaluation_set_fingerprint_ref": EVAL_SET_REF,
    }
    payload.update(overrides)
    return FamiliarityAssessmentEvidence(**payload)


@pytest.mark.parametrize(
    ("mutating", "overrides", "state", "reason"),
    [
        (
            False,
            {},
            FamiliarityState.familiar_supported,
            FamiliarityReasonCode.exact_capability_supported,
        ),
        (
            False,
            {
                "validated_input_field_refs": (),
                "missing_input_field_refs": (
                    "input-field-ref:test/notes-read-1/project_ref",
                ),
                "readiness_status": "not_ready",
            },
            FamiliarityState.familiar_input_required,
            FamiliarityReasonCode.required_input_missing,
        ),
        (
            False,
            {
                "validated_input_field_refs": (),
                "invalid_input_field_refs": (
                    "input-field-ref:test/notes-read-1/project_ref",
                ),
                "readiness_status": "not_ready",
            },
            FamiliarityState.familiar_input_required,
            FamiliarityReasonCode.typed_input_invalid,
        ),
        (
            True,
            {},
            FamiliarityState.familiar_requires_approval,
            FamiliarityReasonCode.exact_approval_required,
        ),
        (
            True,
            {
                "approval_validation_status": "validated",
                "approval_scope_ref": "approval-scope-ref:taw02:notes-write",
                "approval_operation_ref": "operation-ref:test:notes-write",
                "approval_authority_lane_ref": "authority-lane-ref:test:notes-write",
                "approval_policy_snapshot_ref": "policy-snapshot-ref:test:v1",
                "approval_binding_evidence_ref": "approval-binding-evidence-ref:taw02:notes-write",
            },
            FamiliarityState.familiar_supported,
            FamiliarityReasonCode.exact_capability_supported,
        ),
    ],
)
def test_exact_capability_states(mutating, overrides, state, reason) -> None:
    catalog = _catalog(mutating=mutating)
    result = assess_familiarity(_evidence(catalog, **overrides), catalog=catalog)
    assert result.state == state
    assert result.reason_codes == (reason,)
    assert result.model_call_performed is False
    assert result.provider_call_performed is False
    assert result.proposal_constructed is False
    assert result.approval_requested is False
    assert result.execution_performed is False
    assert result.authority_granted is False


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("missing", FamiliarityReasonCode.catalog_missing),
        ("corrupt", FamiliarityReasonCode.catalog_corrupt),
        ("stale", FamiliarityReasonCode.catalog_stale),
        ("over_budget", FamiliarityReasonCode.catalog_over_budget),
    ],
)
def test_catalog_failures_are_capability_evidence_unavailable(status, reason) -> None:
    catalog = _catalog()
    evidence = _evidence(
        catalog,
        catalog_evidence_status=status,
        candidate_matches=(),
        selected_operation_id=None,
        validated_input_field_refs=(),
        approval_validation_status="not_applicable",
        readiness_status="not_applicable",
    )
    result = assess_familiarity(evidence, catalog=None)
    assert result.state == FamiliarityState.capability_evidence_unavailable
    assert result.reason_codes == (reason,)
    assert result.catalog_fingerprint_ref is None


def test_stale_catalog_and_substituted_candidate_fail_closed() -> None:
    catalog = _catalog()
    stale = _evidence(catalog, observed_at_epoch_seconds=201)
    assert assess_familiarity(stale, catalog=catalog).reason_codes == (
        FamiliarityReasonCode.catalog_stale,
    )

    substituted = _evidence(catalog).model_copy(
        update={
            "candidate_matches": (
                _match(catalog.envelopes[0]).model_copy(
                    update={
                        "envelope_fingerprint_ref": "awareness-envelope-ref:taw01:sha256:"
                        + "b" * 64
                    }
                ),
            )
        }
    )
    result = assess_familiarity(substituted, catalog=catalog)
    assert result.state == FamiliarityState.capability_evidence_unavailable
    assert result.reason_codes == (
        FamiliarityReasonCode.capability_evidence_substituted,
    )


def test_policy_and_terminal_precedence_are_fail_closed() -> None:
    catalog = _catalog()
    denied = _evidence(
        catalog,
        policy_decision_status=PolicyDecisionStatus.denied,
        policy_reason_refs=("policy-reason-ref:taw02:request-denied",),
        interpretation_refs=(
            "interpretation-ref:taw02:one",
            "interpretation-ref:taw02:two",
        ),
    )
    assert (
        assess_familiarity(denied, catalog=catalog).state
        == FamiliarityState.familiar_authority_blocked
    )

    uncertain = denied.model_copy(
        update={
            "terminal_outcome": TerminalOutcomeEvidence(
                status="terminal_missing",
                execution_attempt_ref="execution-attempt-ref:taw02:one",
                durable_start_evidence_ref="durable-start-evidence-ref:taw02:one",
            )
        }
    )
    result = assess_familiarity(uncertain, catalog=catalog)
    assert result.state == FamiliarityState.outcome_uncertain
    assert result.reason_codes == (
        FamiliarityReasonCode.outcome_terminal_proof_missing,
    )


def test_ambiguity_retains_semantic_relevance_separately() -> None:
    catalog = _catalog(second=True)
    matches = tuple(
        _match(item, semantic=index == 1)
        for index, item in enumerate(catalog.envelopes)
    )
    evidence = _evidence(
        catalog,
        candidate_matches=matches,
        selected_operation_id=None,
        validated_input_field_refs=(),
        approval_validation_status="not_applicable",
        readiness_status="not_applicable",
    )
    result = assess_familiarity(evidence, catalog=catalog)
    assert result.state == FamiliarityState.ambiguous
    assert result.dimensions.deterministic_match_count == 1
    assert result.dimensions.semantic_match_count == 1
    assert result.dimensions.capability_match_count == 2


@pytest.mark.parametrize(
    ("availability", "reason"),
    [
        ("disabled", FamiliarityReasonCode.capability_disabled),
        ("unhealthy", FamiliarityReasonCode.capability_unhealthy),
        ("stale", FamiliarityReasonCode.capability_stale),
        ("absent", FamiliarityReasonCode.capability_absent),
    ],
)
def test_known_unavailable_capability_is_not_reported_unsupported(
    availability, reason
) -> None:
    catalog = _catalog(unhealthy=True)
    match = _match(catalog.envelopes[0], availability_status=availability)
    evidence = _evidence(
        catalog, candidate_matches=(match,), readiness_status="not_ready"
    )
    result = assess_familiarity(evidence, catalog=catalog)
    assert result.state == FamiliarityState.familiar_unavailable
    assert result.reason_codes == (reason,)


def test_valid_catalog_without_match_is_novel_unsupported() -> None:
    catalog = _catalog()
    evidence = _evidence(
        catalog,
        candidate_matches=(),
        selected_operation_id=None,
        validated_input_field_refs=(),
        approval_validation_status="not_applicable",
        readiness_status="not_applicable",
    )
    result = assess_familiarity(evidence, catalog=catalog)
    assert result.state == FamiliarityState.novel_unsupported
    assert result.reason_codes == (FamiliarityReasonCode.no_capability_match,)


def test_malformed_and_inconsistent_evidence_is_rejected() -> None:
    catalog = _catalog()
    duplicate = _evidence(catalog).model_dump(mode="json")
    duplicate["candidate_matches"].append(
        copy.deepcopy(duplicate["candidate_matches"][0])
    )
    with pytest.raises(ValidationError, match="candidate matches must be unique"):
        FamiliarityAssessmentEvidence.model_validate(duplicate)

    inconsistent = _evidence(catalog, readiness_status="not_ready")
    with pytest.raises(ValueError, match="not decision-ready"):
        assess_familiarity(inconsistent, catalog=catalog)

    mutating_catalog = _catalog(mutating=True)
    substituted_approval = _evidence(
        mutating_catalog,
        approval_validation_status="validated",
        approval_scope_ref="approval-scope-ref:taw02:notes-write",
        approval_operation_ref="operation-ref:test:notes-write",
        approval_authority_lane_ref="authority-lane-ref:test:substituted",
        approval_policy_snapshot_ref="policy-snapshot-ref:test:v1",
        approval_binding_evidence_ref="approval-binding-evidence-ref:taw02:notes-write",
    )
    with pytest.raises(ValueError, match="scope-substituted"):
        assess_familiarity(substituted_approval, catalog=mutating_catalog)


def test_assessment_fingerprint_rejects_tampering() -> None:
    catalog = _catalog()
    result = assess_familiarity(_evidence(catalog), catalog=catalog)
    payload = result.model_dump(mode="json")
    payload["state"] = FamiliarityState.novel_unsupported
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        FamiliarityAssessment.model_validate(payload)


def test_taw02_verifier_passes() -> None:
    verifier.verify()
