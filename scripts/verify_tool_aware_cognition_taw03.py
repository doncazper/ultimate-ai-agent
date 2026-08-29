from __future__ import annotations

from ultimate_ai_agent.core.capabilities import (
    CapabilityAwarenessBinding,
    CapabilityHealthStatus,
    CapabilityKind,
    CapabilityManifest,
    CapabilityRegistry,
    CoordinationMode,
    HydrationSourceEvidence,
    HydrationTokenAccounting,
    ManifestTokenCount,
    PolicyDecisionStatus,
    RetrievalConstraints,
    SafetyPolicy,
    SideEffectLevel,
    build_capability_awareness_catalog,
    build_progressive_capability_cache,
    discover_capabilities,
    hydrate_capability_manifests,
    operation_schema_from_manifest,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


ENVIRONMENT_REF = "environment-fingerprint-ref:taw03:verification-host"


def _evidence():
    registry = CapabilityRegistry()
    operations = []
    bindings = []
    for suffix, effect, approval, lane in (
        ("review", SideEffectLevel.read, False, "not_applicable"),
        ("publish", SideEffectLevel.external, True, "blocked"),
    ):
        manifest = CapabilityManifest(
            id=f"capability-ref:taw03:verify-{suffix}",
            version="1.0.0",
            kind=CapabilityKind.tool,
            name=f"Verify {suffix.title()}",
            description="Operate on bounded reviewed evidence references.",
            tags=["evidence", "reviewed"],
            examples=["Review evidence records."],
            anti_examples=["Do not broaden scope."],
            input_schema={
                "type": "object",
                "properties": {"evidence_ref": {"type": "string"}},
                "required": ["evidence_ref"],
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
            risk_level=RiskLevel.medium if approval else RiskLevel.low,
            approval_required=approval,
            rollback_supported=approval,
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            concurrency_safe=not approval,
            single_writer_required=approval,
            safety=SafetyPolicy(
                allow_parallel=not approval,
                require_single_writer=approval,
                approval_required=approval,
                max_risk_level=RiskLevel.medium if approval else RiskLevel.low,
                max_side_effect_level=effect,
            ),
        )
        registry.register(manifest, object())
        operation = operation_schema_from_manifest(
            manifest,
            operation_id=f"operation-ref:taw03:verify-{suffix}",
            operation_version="1.0.0",
            operator_summary=f"Review {suffix} evidence records.",
            aliases=(f"inspect {suffix} records",),
            positive_eval_refs=(f"eval-ref:taw03:verify-{suffix}-positive",),
            negative_eval_refs=(f"eval-ref:taw03:verify-{suffix}-negative",),
            ambiguity_eval_refs=(f"eval-ref:taw03:verify-{suffix}-ambiguity",),
            adversarial_eval_refs=(f"eval-ref:taw03:verify-{suffix}-adversarial",),
            provenance_ref=f"provenance-ref:taw03:verify-{suffix}",
            review_ref=f"review-ref:taw03:verify-{suffix}",
        )
        operations.append(operation)
        bindings.append(
            CapabilityAwarenessBinding(
                operation_id=operation.operation_id,
                health_status=CapabilityHealthStatus.healthy,
                availability_ref=f"availability-ref:taw03:verify-{suffix}",
                policy_decision_status=(
                    PolicyDecisionStatus.approval_required
                    if approval
                    else PolicyDecisionStatus.allowed
                ),
                policy_snapshot_ref="policy-snapshot-ref:taw03:verification",
                authority_lane_status=lane,
                authority_lane_ref=f"authority-lane-ref:taw03:verify-{suffix}",
                safe_disable_ref="safe-disable-ref:taw03:legacy-router",
                rollback_posture="supported" if approval else "not_applicable",
                rollback_ref=f"rollback-ref:taw03:verify-{suffix}",
                terminal_proof_contract_ref=f"terminal-proof-contract-ref:taw03:verify-{suffix}",
                expected_terminal_status_refs=(
                    f"terminal-status-ref:taw03:verify-{suffix}-complete",
                ),
            )
        )
    catalog = build_capability_awareness_catalog(
        registry,
        operation_schemas=operations,
        bindings=bindings,
        catalog_epoch_ref="catalog-epoch-ref:taw03:verification",
        availability_epoch_ref="availability-epoch-ref:taw03:verification",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )
    return catalog, tuple(operations)


def verify() -> None:
    catalog, operations = _evidence()
    cache = build_progressive_capability_cache(
        catalog,
        operation_schemas=operations,
        environment_fingerprint_ref=ENVIRONMENT_REF,
        observed_at_epoch_seconds=150,
    )
    shortlist = discover_capabilities(
        cache,
        normalized_request="inspect review publish records",
        constraints=RetrievalConstraints(
            accepted_effect_classes=(SideEffectLevel.external, SideEffectLevel.read)
        ),
        environment_fingerprint_ref=ENVIRONMENT_REF,
        observed_at_epoch_seconds=150,
    )
    if shortlist.status != "ready" or len(shortlist.candidates) != 2:
        raise RuntimeError("TAW-03 verifier did not return the bounded shortlist")
    blocked = next(
        item for item in shortlist.candidates if item.operation_id.endswith("publish")
    )
    if (
        blocked.proposal_eligible
        or "authority_blocked" not in blocked.block_reason_codes
    ):
        raise RuntimeError("TAW-03 verifier did not retain and block the exact lane")
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
        backend_ref="backend-ref:taw03:qwen-3-8-27b-local",
        tokenizer_artifact_ref="artifact-ref:taw03:qwen-vocabulary",
        tokenizer_fingerprint_ref="artifact-fingerprint-ref:taw03:qwen-v1",
        prompt_format_ref="prompt-format-ref:taw03:not-assembled",
        estimator_ref="estimator-ref:taw03:conservative-v1",
        model_context_tokens=128_000,
        non_hydration_prompt_tokens=1_000,
        reserved_output_tokens=4_000,
        manifest_counts=tuple(
            ManifestTokenCount(operation_id=item.operation_id, estimated_tokens=100)
            for item in sorted(operations, key=lambda value: value.operation_id)
        ),
    )
    hydration = hydrate_capability_manifests(
        shortlist,
        cache,
        catalog,
        operation_schemas=operations,
        source_evidence=sources,
        token_accounting=accounting,
        environment_fingerprint_ref=ENVIRONMENT_REF,
        observed_at_epoch_seconds=150,
    )
    if hydration.status != "ready" or len(hydration.manifests) != 2:
        raise RuntimeError("TAW-03 verifier did not hydrate bounded manifests")
    if any(
        (
            hydration.model_call_performed,
            hydration.provider_call_performed,
            hydration.prompt_assembly_performed,
            hydration.proposal_constructed,
            hydration.approval_requested,
            hydration.execution_performed,
            hydration.authority_granted,
        )
    ):
        raise RuntimeError("TAW-03 verifier detected authority broadening")


def main() -> int:
    verify()
    print("Tool-aware cognition TAW-03 progressive retrieval verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
