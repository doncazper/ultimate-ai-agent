from __future__ import annotations

from ultimate_ai_agent.core.capabilities import (
    CapabilityAwarenessBinding,
    CapabilityHealthStatus,
    CapabilityKind,
    CapabilityManifest,
    CapabilityRegistry,
    CoordinationMode,
    PolicyDecisionStatus,
    SafetyPolicy,
    SideEffectLevel,
    build_capability_awareness_catalog,
    operation_schema_from_manifest,
    validate_capability_awareness_catalog,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


def _verified_catalog():
    manifest = CapabilityManifest(
        id="capability-ref:taw01:verified-read",
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
        operation_id="operation-ref:taw01:verified-read",
        operation_version="1.0.0",
        operator_summary="Inspect one reviewed evidence reference.",
        aliases=("inspect reviewed evidence",),
        positive_eval_refs=("eval-ref:taw01:verified-read-positive",),
        negative_eval_refs=("eval-ref:taw01:verified-read-negative",),
        ambiguity_eval_refs=("eval-ref:taw01:verified-read-ambiguity",),
        adversarial_eval_refs=("eval-ref:taw01:verified-read-adversarial",),
        provenance_ref="provenance-ref:taw01:repository-reviewed",
        review_ref="review-ref:taw01:founder-dogfood",
    )
    binding = CapabilityAwarenessBinding(
        operation_id=operation.operation_id,
        health_status=CapabilityHealthStatus.healthy,
        availability_ref="availability-ref:taw01:verified-local",
        policy_decision_status=PolicyDecisionStatus.allowed,
        policy_snapshot_ref="policy-snapshot-ref:taw01:verification",
        authority_lane_status="not_applicable",
        authority_lane_ref="authority-lane-ref:taw01:not-applicable",
        safe_disable_ref="safe-disable-ref:taw01:legacy-router",
        rollback_posture="not_applicable",
        rollback_ref="rollback-ref:taw01:no-side-effect",
        terminal_proof_contract_ref="terminal-proof-contract-ref:taw01:read:v1",
        expected_terminal_status_refs=("terminal-status-ref:taw01:completed",),
    )
    return build_capability_awareness_catalog(
        registry,
        operation_schemas=(operation,),
        bindings=(binding,),
        catalog_epoch_ref="catalog-epoch-ref:taw01:verification",
        availability_epoch_ref="availability-epoch-ref:taw01:verification",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )


def verify() -> None:
    catalog = _verified_catalog()
    validated = validate_capability_awareness_catalog(
        catalog,
        expected_catalog_epoch_ref=catalog.catalog_epoch_ref,
        expected_availability_epoch_ref=catalog.availability_epoch_ref,
        expected_policy_snapshot_ref=catalog.policy_snapshot_ref,
        observed_at_epoch_seconds=150,
    )
    envelope = validated.envelopes[0]
    if any(
        (
            validated.model_call_performed,
            validated.provider_call_performed,
            validated.execution_enabled,
            validated.authority_granted,
            envelope.model_call_performed,
            envelope.provider_call_performed,
            envelope.execution_enabled,
            envelope.authority_granted,
        )
    ):
        raise RuntimeError("TAW-01 verification detected authority broadening")
    try:
        validate_capability_awareness_catalog(
            catalog,
            expected_catalog_epoch_ref=catalog.catalog_epoch_ref,
            expected_availability_epoch_ref=catalog.availability_epoch_ref,
            expected_policy_snapshot_ref=catalog.policy_snapshot_ref,
            observed_at_epoch_seconds=201,
        )
    except ValueError as exc:
        if "stale" not in str(exc):
            raise RuntimeError(
                "TAW-01 stale rejection returned the wrong reason"
            ) from exc
    else:
        raise RuntimeError("TAW-01 verification accepted a stale catalog")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-01 capability evidence verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
