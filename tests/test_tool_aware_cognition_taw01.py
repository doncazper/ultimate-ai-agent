from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from scripts import verify_tool_aware_cognition_taw01 as verifier
from ultimate_ai_agent.core.capabilities import (
    CapabilityAuthorityLevel,
    CapabilityAwarenessBinding,
    CapabilityAwarenessCatalog,
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


def _manifest(
    capability_id: str = "capability-ref:test:notes-read",
    *,
    side_effects: SideEffectLevel = SideEffectLevel.read,
    risk_level: RiskLevel = RiskLevel.low,
    approval_required: bool | str | None = None,
    rollback_supported: bool = False,
) -> CapabilityManifest:
    mutating = side_effects in {
        SideEffectLevel.write,
        SideEffectLevel.external,
        SideEffectLevel.destructive,
    }
    return CapabilityManifest(
        id=capability_id,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="Reviewed Notes",
        description="Read reviewed note metadata for a bounded operator request.",
        tags=["notes", "reviewed"],
        examples=["Find reviewed notes for the current project."],
        anti_examples=["Do not use for unreviewed or unrelated records."],
        input_schema={
            "type": "object",
            "properties": {
                "project_ref": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
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
        side_effects=side_effects,
        risk_level=risk_level,
        approval_required=approval_required,
        rollback_supported=rollback_supported,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=not mutating,
        single_writer_required=mutating,
        safety=SafetyPolicy(
            allow_parallel=not mutating,
            require_single_writer=mutating,
            approval_required=bool(approval_required),
            max_risk_level=risk_level,
            max_side_effect_level=side_effects,
        ),
    )


def _registry(manifest: CapabilityManifest | None = None) -> CapabilityRegistry:
    selected = manifest or _manifest()
    registry = CapabilityRegistry()
    registry.register(selected, object())
    return registry


def _operation(
    manifest: CapabilityManifest | None = None, *, suffix: str = "notes-read"
):
    selected = manifest or _manifest()
    return operation_schema_from_manifest(
        selected,
        operation_id=f"operation-ref:test:{suffix}",
        operation_version="1.0.0",
        operator_summary="Read reviewed note references for one project.",
        aliases=("find reviewed notes", "read project notes"),
        precondition_refs=("precondition-ref:test:project-known",),
        incompatibility_refs=("incompatibility-ref:test:unreviewed-content",),
        positive_eval_refs=("eval-ref:taw01:positive-notes-read",),
        negative_eval_refs=("eval-ref:taw01:negative-notes-write",),
        ambiguity_eval_refs=("eval-ref:taw01:ambiguous-notes-scope",),
        adversarial_eval_refs=("eval-ref:taw01:adversarial-notes-catalog",),
        provenance_ref="provenance-ref:taw01:repository-reviewed",
        review_ref="review-ref:taw01:founder-dogfood",
    )


def _binding(
    operation_id: str = "operation-ref:test:notes-read",
    *,
    policy_snapshot_ref: str = "policy-snapshot-ref:test:v1",
    rollback_posture: str = "not_applicable",
    authority_lane_status: str = "not_applicable",
) -> CapabilityAwarenessBinding:
    return CapabilityAwarenessBinding(
        operation_id=operation_id,
        health_status=CapabilityHealthStatus.healthy,
        availability_ref="availability-ref:test:local-healthy",
        policy_decision_status=PolicyDecisionStatus.allowed,
        policy_snapshot_ref=policy_snapshot_ref,
        authority_lane_status=authority_lane_status,
        authority_lane_ref="authority-lane-ref:test:not-applicable",
        safe_disable_ref="safe-disable-ref:taw01:legacy-router",
        rollback_posture=rollback_posture,
        rollback_ref="rollback-ref:taw01:no-side-effect",
        terminal_proof_contract_ref="terminal-proof-contract-ref:test:read-receipt:v1",
        expected_terminal_status_refs=("terminal-status-ref:test:completed",),
    )


def _catalog(
    *,
    registry: CapabilityRegistry | None = None,
    operations=None,
    bindings=None,
) -> CapabilityAwarenessCatalog:
    return build_capability_awareness_catalog(
        registry or _registry(),
        operation_schemas=operations or (_operation(),),
        bindings=bindings or (_binding(),),
        catalog_epoch_ref="catalog-epoch-ref:test:one",
        availability_epoch_ref="availability-epoch-ref:test:one",
        generated_at_epoch_seconds=100,
        expires_at_epoch_seconds=200,
    )


def test_catalog_is_deterministic_content_free_and_non_authorizing() -> None:
    first = _catalog()
    second = _catalog()
    envelope = first.envelopes[0]

    assert first == second
    assert first.catalog_fingerprint_ref.startswith(
        "awareness-catalog-ref:taw01:sha256:"
    )
    assert envelope.envelope_fingerprint_ref.startswith(
        "awareness-envelope-ref:taw01:sha256:"
    )
    assert envelope.required_input_field_refs == (
        "input-field-ref:test/notes-read/project_ref",
    )
    assert envelope.optional_input_field_refs == (
        "input-field-ref:test/notes-read/limit",
    )
    assert envelope.authority_class == CapabilityAuthorityLevel.metadata_only
    assert envelope.approval_class == "not_required"
    assert envelope.model_call_performed is False
    assert envelope.provider_call_performed is False
    assert envelope.execution_enabled is False
    assert envelope.authority_granted is False
    assert "input_schema" not in envelope.model_dump(mode="json")
    assert "output_schema" not in envelope.model_dump(mode="json")


def test_catalog_validation_rejects_stale_or_substituted_epochs() -> None:
    catalog = _catalog()
    assert (
        validate_capability_awareness_catalog(
            catalog,
            expected_catalog_epoch_ref="catalog-epoch-ref:test:one",
            expected_availability_epoch_ref="availability-epoch-ref:test:one",
            expected_policy_snapshot_ref="policy-snapshot-ref:test:v1",
            observed_at_epoch_seconds=200,
        )
        == catalog
    )
    with pytest.raises(ValueError, match="catalog is stale"):
        validate_capability_awareness_catalog(
            catalog,
            expected_catalog_epoch_ref="catalog-epoch-ref:test:one",
            expected_availability_epoch_ref="availability-epoch-ref:test:one",
            expected_policy_snapshot_ref="policy-snapshot-ref:test:v1",
            observed_at_epoch_seconds=201,
        )
    with pytest.raises(ValueError, match="epoch is stale or substituted"):
        validate_capability_awareness_catalog(
            catalog,
            expected_catalog_epoch_ref="catalog-epoch-ref:test:two",
            expected_availability_epoch_ref="availability-epoch-ref:test:one",
            expected_policy_snapshot_ref="policy-snapshot-ref:test:v1",
            observed_at_epoch_seconds=150,
        )


def test_tampered_or_extra_envelope_fields_fail_closed() -> None:
    payload = _catalog().model_dump(mode="json")
    payload["envelopes"][0]["availability_ref"] = "availability-ref:test:substituted"
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        CapabilityAwarenessCatalog.model_validate(payload)

    extra = _catalog().model_dump(mode="json")
    extra["envelopes"][0]["raw_prompt"] = "not allowed"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CapabilityAwarenessCatalog.model_validate(extra)

    unsafe = _catalog().model_dump(mode="json")
    unsafe["envelopes"][0]["operator_summary"] = "/Users/operator/private record"
    with pytest.raises(ValidationError, match="unsafe content"):
        CapabilityAwarenessCatalog.model_validate(unsafe)

    wrong_prefix = _catalog().model_dump(mode="json")
    digest = wrong_prefix["envelopes"][0]["output_schema_fingerprint_ref"].rsplit(
        ":", 1
    )[-1]
    wrong_prefix["envelopes"][0]["output_schema_fingerprint_ref"] = (
        f"unrelated-ref:taw01:sha256:{digest}"
    )
    with pytest.raises(ValidationError, match="output_schema_fingerprint_ref"):
        CapabilityAwarenessCatalog.model_validate(wrong_prefix)


def test_duplicate_or_incomplete_operation_bindings_fail_closed() -> None:
    operation = _operation()
    binding = _binding()
    with pytest.raises(ValueError, match="duplicate operation IDs"):
        _catalog(operations=(operation, operation), bindings=(binding,))
    with pytest.raises(ValueError, match="duplicate operation IDs"):
        _catalog(operations=(operation,), bindings=(binding, binding))
    with pytest.raises(ValueError, match="exactly one awareness binding"):
        _catalog(
            operations=(operation,),
            bindings=(_binding("operation-ref:test:different"),),
        )


def test_registry_schema_version_and_policy_inconsistency_fail_closed() -> None:
    manifest = _manifest()
    operation_payload = _operation(manifest).model_dump(mode="python")
    operation_payload["capability_version"] = "2.0.0"
    with pytest.raises(ValueError, match="version does not match"):
        _catalog(
            registry=_registry(manifest),
            operations=(type(_operation()).model_validate(operation_payload),),
        )

    second_manifest = _manifest("capability-ref:test:notes-second")
    second_operation = _operation(second_manifest, suffix="notes-second")
    registry = _registry(manifest)
    registry.register(second_manifest, object())
    with pytest.raises(ValueError, match="one exact policy snapshot"):
        _catalog(
            registry=registry,
            operations=(_operation(manifest), second_operation),
            bindings=(
                _binding(),
                _binding(
                    "operation-ref:test:notes-second",
                    policy_snapshot_ref="policy-snapshot-ref:test:v2",
                ),
            ),
        )


def test_mutating_contract_binds_approval_and_missing_rollback_without_grant() -> None:
    manifest = _manifest(
        "capability-ref:test:notes-write",
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
        approval_required=True,
    )
    operation = _operation(manifest, suffix="notes-write")
    binding = _binding(
        "operation-ref:test:notes-write",
        rollback_posture="required_but_unavailable",
        authority_lane_status="blocked",
    )
    catalog = _catalog(
        registry=_registry(manifest), operations=(operation,), bindings=(binding,)
    )
    envelope = catalog.envelopes[0]

    assert envelope.authority_class == CapabilityAuthorityLevel.mutating
    assert envelope.approval_class == "exact_approval_required"
    assert envelope.authority_lane_status == "blocked"
    assert envelope.rollback_posture == "required_but_unavailable"
    assert envelope.execution_enabled is False
    assert envelope.authority_granted is False


def test_sensitive_read_can_bind_exact_approval_lane_without_granting_authority() -> (
    None
):
    manifest = _manifest(
        "capability-ref:test:notes-sensitive-read",
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.medium,
        approval_required=True,
    )
    operation = _operation(manifest, suffix="notes-sensitive-read")
    binding = _binding(
        "operation-ref:test:notes-sensitive-read",
        authority_lane_status="graduated",
    )
    catalog = _catalog(
        registry=_registry(manifest), operations=(operation,), bindings=(binding,)
    )

    assert catalog.envelopes[0].approval_class == "exact_approval_required"
    assert catalog.envelopes[0].authority_lane_status == "graduated"
    assert catalog.envelopes[0].execution_enabled is False
    assert catalog.envelopes[0].authority_granted is False


def test_malformed_schema_unsafe_summary_and_inconsistent_rollback_are_rejected() -> (
    None
):
    operation_payload = _operation().model_dump(mode="python")
    operation_payload["input_schema"] = {
        "type": "object",
        "properties": {"known": {"type": "string"}},
        "required": ["missing"],
    }
    with pytest.raises(ValidationError, match="duplicate or undefined"):
        type(_operation()).model_validate(operation_payload)

    invalid_json_schema = _operation().model_dump(mode="python")
    invalid_json_schema["input_schema"]["properties"]["project_ref"] = {
        "type": "not-a-json-schema-type"
    }
    with pytest.raises(ValidationError, match="not a valid JSON Schema"):
        type(_operation()).model_validate(invalid_json_schema)

    unsafe_payload = _operation().model_dump(mode="python")
    unsafe_payload["operator_summary"] = "/Users/operator/private record"
    with pytest.raises(ValidationError, match="unsafe content"):
        type(_operation()).model_validate(unsafe_payload)

    with pytest.raises(ValueError, match="rollback posture contradicts"):
        _catalog(bindings=(_binding(rollback_posture="supported"),))


def test_catalog_fingerprint_covers_ordered_envelope_set() -> None:
    first_manifest = _manifest()
    second_manifest = _manifest("capability-ref:test:notes-second")
    registry = _registry(first_manifest)
    registry.register(second_manifest, object())
    catalog = _catalog(
        registry=registry,
        operations=(
            _operation(second_manifest, suffix="notes-second"),
            _operation(first_manifest),
        ),
        bindings=(
            _binding("operation-ref:test:notes-second"),
            _binding(),
        ),
    )
    assert [item.operation_id for item in catalog.envelopes] == [
        "operation-ref:test:notes-read",
        "operation-ref:test:notes-second",
    ]

    payload = copy.deepcopy(catalog.model_dump(mode="json"))
    payload["envelopes"].reverse()
    with pytest.raises(ValidationError, match="unique and sorted"):
        CapabilityAwarenessCatalog.model_validate(payload)


def test_repo_verifier_passes() -> None:
    verifier.verify()
