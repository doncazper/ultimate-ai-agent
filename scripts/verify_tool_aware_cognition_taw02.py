from __future__ import annotations

from ultimate_ai_agent.core.capabilities import (
    CapabilityAwarenessBinding,
    CapabilityHealthStatus,
    CapabilityKind,
    CapabilityManifest,
    CapabilityMatchEvidence,
    CapabilityRegistry,
    CoordinationMode,
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


def _verified_catalog():
    manifest = CapabilityManifest(
        id="capability-ref:taw02:verified-read",
        version="1.0.0",
        kind=CapabilityKind.deterministic,
        name="Verified Read",
        description="Inspect bounded reviewed evidence references.",
        tags=["evidence", "reviewed"],
        examples=["Inspect reviewed evidence references."],
        anti_examples=["Do not mutate or widen the requested scope."],
        input_schema={
            "type": "object",
            "properties": {"evidence_ref": {"type": "string"}},
            "required": ["evidence_ref"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"summary_ref": {"type": "string"}},
            "required": ["summary_ref"],
            "additionalProperties": False,
        },
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.low,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=True,
        safety=SafetyPolicy(
            allow_parallel=True,
            max_risk_level=RiskLevel.low,
            max_side_effect_level=SideEffectLevel.read,
        ),
    )
    registry = CapabilityRegistry()
    registry.register(manifest, object())
    operation = operation_schema_from_manifest(
        manifest,
        operation_id="operation-ref:taw02:verified-read",
        operation_version="1.0.0",
        operator_summary="Inspect one reviewed evidence reference.",
        aliases=("inspect reviewed evidence",),
        positive_eval_refs=("eval-ref:taw02:verified-read-positive",),
        negative_eval_refs=("eval-ref:taw02:verified-read-negative",),
        ambiguity_eval_refs=("eval-ref:taw02:verified-read-ambiguity",),
        adversarial_eval_refs=("eval-ref:taw02:verified-read-adversarial",),
        provenance_ref="provenance-ref:taw02:repository-reviewed",
        review_ref="review-ref:taw02:founder-dogfood",
    )
    binding = CapabilityAwarenessBinding(
        operation_id=operation.operation_id,
        health_status=CapabilityHealthStatus.healthy,
        availability_ref="availability-ref:taw02:verified-local",
        policy_decision_status=PolicyDecisionStatus.allowed,
        policy_snapshot_ref="policy-snapshot-ref:taw02:verification",
        authority_lane_status="not_applicable",
        authority_lane_ref="authority-lane-ref:taw02:not-applicable",
        safe_disable_ref="safe-disable-ref:taw02:legacy-router",
        rollback_posture="not_applicable",
        rollback_ref="rollback-ref:taw02:no-side-effect",
        terminal_proof_contract_ref="terminal-proof-contract-ref:taw02:read:v1",
        expected_terminal_status_refs=("terminal-status-ref:taw02:completed",),
    )
    return build_capability_awareness_catalog(
        registry,
        operation_schemas=(operation,),
        bindings=(binding,),
        catalog_epoch_ref="catalog-epoch-ref:taw02:verification",
        availability_epoch_ref="availability-epoch-ref:taw02:verification",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )


def _evidence(catalog) -> FamiliarityAssessmentEvidence:
    envelope = catalog.envelopes[0]
    return FamiliarityAssessmentEvidence(
        possible_tool_intent=True,
        sentinel_evidence_ref="sentinel-evidence-ref:taw02:verification",
        catalog_evidence_status="valid",
        expected_catalog_epoch_ref=catalog.catalog_epoch_ref,
        expected_availability_epoch_ref=catalog.availability_epoch_ref,
        expected_policy_snapshot_ref=catalog.policy_snapshot_ref,
        observed_at_epoch_seconds=150,
        interpretation_refs=("interpretation-ref:taw02:verification",),
        candidate_matches=(
            CapabilityMatchEvidence(
                operation_id=envelope.operation_id,
                envelope_fingerprint_ref=envelope.envelope_fingerprint_ref,
                match_kind="deterministic",
                match_evidence_ref="match-evidence-ref:taw02:verification",
                relevance_basis_points=10_000,
                availability_status="available",
                availability_ref=envelope.availability_ref,
                availability_epoch_ref=envelope.availability_epoch_ref,
            ),
        ),
        selected_operation_id=envelope.operation_id,
        policy_decision_status=envelope.policy_decision_status,
        policy_reason_refs=(),
        safety_decision_status="allowed",
        safety_snapshot_ref="safety-snapshot-ref:taw02:verification",
        safety_reason_refs=(),
        validated_input_field_refs=envelope.required_input_field_refs,
        missing_input_field_refs=(),
        invalid_input_field_refs=(),
        approval_validation_status="not_applicable",
        readiness_status="ready",
        terminal_outcome=TerminalOutcomeEvidence(),
        evaluation_set_fingerprint_ref=("evaluation-set-ref:taw02:sha256:" + "a" * 64),
    )


def verify() -> None:
    catalog = _verified_catalog()
    evidence = _evidence(catalog)
    supported = assess_familiarity(evidence, catalog=catalog)
    if supported.state != FamiliarityState.familiar_supported:
        raise RuntimeError(
            "TAW-02 verification did not classify exact healthy evidence"
        )
    if supported.reason_codes != (FamiliarityReasonCode.exact_capability_supported,):
        raise RuntimeError("TAW-02 verification returned unstable supported reasons")
    if any(
        (
            supported.model_call_performed,
            supported.provider_call_performed,
            supported.proposal_constructed,
            supported.approval_requested,
            supported.execution_performed,
            supported.authority_granted,
        )
    ):
        raise RuntimeError("TAW-02 verification detected authority broadening")

    stale = evidence.model_copy(update={"observed_at_epoch_seconds": 201})
    unavailable = assess_familiarity(stale, catalog=catalog)
    if unavailable.state != FamiliarityState.capability_evidence_unavailable:
        raise RuntimeError("TAW-02 verification did not fail closed on stale evidence")
    if unavailable.reason_codes != (FamiliarityReasonCode.catalog_stale,):
        raise RuntimeError("TAW-02 verification returned the wrong stale reason")

    uncertain = evidence.model_copy(
        update={
            "terminal_outcome": TerminalOutcomeEvidence(
                status="terminal_missing",
                execution_attempt_ref="execution-attempt-ref:taw02:verification",
                durable_start_evidence_ref="durable-start-evidence-ref:taw02:verification",
            )
        }
    )
    if (
        assess_familiarity(uncertain, catalog=catalog).state
        != FamiliarityState.outcome_uncertain
    ):
        raise RuntimeError("TAW-02 verification did not preserve terminal precedence")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-02 familiarity verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
