from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationReceipt,
    VerificationRiskTier,
    VerificationTerminalStatus,
    VerificationUnit,
    VerificationUnitKind,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_plan_contract_fingerprint,
    verification_receipt_fingerprint,
    verification_run_manifest_fingerprint,
    verification_dag_definition_fingerprint,
    verification_unit_definition_fingerprint,
)
from scripts.verification.verification_run_aggregator import (
    aggregate_verification_run,
)
from scripts.verification.verification_execution_identity import (
    build_verification_execution_identity,
)


SHA = "a" * 40
DIGEST = "b" * 64
SURFACE = "surface-ref:private"


def _units(*, include_audit: bool = False) -> tuple[VerificationUnit, ...]:
    units = [
        VerificationUnit(
            unit_ref="unit:a",
            display_name="A",
            lane_ref="lane:a",
            needs=(),
            command_refs=("command:a",),
            proof_equivalence_ref="proof-equivalence:a",
        ),
        VerificationUnit(
            unit_ref="unit:b",
            display_name="B",
            lane_ref="lane:b",
            needs=("unit:a",),
            command_refs=("command:b",),
            proof_equivalence_ref="proof-equivalence:b",
        ),
        VerificationUnit(
            unit_ref="unit:aggregate",
            display_name="Aggregate",
            lane_ref=None,
            needs=("unit:b",),
            unit_kind=VerificationUnitKind.AGGREGATE,
            proof_equivalence_ref="proof-equivalence:aggregate",
        ),
    ]
    if include_audit:
        units.append(
            VerificationUnit(
                unit_ref="unit:audit",
                display_name="Audit",
                lane_ref=None,
                needs=("unit:aggregate",),
                unit_kind=VerificationUnitKind.AUDIT,
                proof_equivalence_ref="proof-equivalence:audit",
            )
        )
    return tuple(units)


def _plan(units: tuple[VerificationUnit, ...]) -> VerificationPlan:
    plan = VerificationPlan(
        schema_version="uaa_verification_plan.v3",
        profile_ref="profile:test",
        repository_sha=SHA,
        definition_fingerprint=DIGEST,
        dependency_lock_fingerprints=(("uv.lock", DIGEST),),
        affected_path_classification="bounded_core",
        selected_lane_refs=tuple(
            unit.lane_ref for unit in units if unit.lane_ref is not None
        ),
        selected_command_refs=tuple(
            command_ref for unit in units for command_ref in unit.command_refs
        ),
        pytest_shard_plan_fingerprint=DIGEST,
        frontend_visual_scope="not_affected",
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        plan_fingerprint="0" * 64,
        base_sha=SHA,
        risk_manifest_version="uaa_verification_risk_manifest.v1",
        risk_manifest_fingerprint=DIGEST,
        risk_tier=VerificationRiskTier.TIER_2,
        changed_path_refs=("scripts/example.py",),
        change_fingerprint=DIGEST,
        escalation_reason_refs=(),
        selected_unit_refs=tuple(unit.unit_ref for unit in units),
        selected_test_refs=(),
        audit_posture="not_required",
        full_pytest_required=False,
        typescript_typecheck_required=False,
        release_gate_required=False,
        platform_fingerprint=DIGEST,
        command_manifest_fingerprint=DIGEST,
        verifier_definition_fingerprint=DIGEST,
        test_collection_fingerprint=DIGEST,
        test_collection_posture="inventory_bound",
        typescript_project_fingerprint=DIGEST,
        typescript_project_posture="not_applicable",
        force_full=False,
        shadow_mode=False,
        verification_dag_fingerprint=verification_dag_definition_fingerprint(units),
        selected_unit_definition_fingerprints=tuple(
            (unit.unit_ref, verification_unit_definition_fingerprint(unit))
            for unit in units
        ),
    )
    return replace(plan, plan_fingerprint=verification_plan_contract_fingerprint(plan))


def _receipt(
    plan: VerificationPlan,
    unit: VerificationUnit,
    *,
    status: VerificationTerminalStatus = VerificationTerminalStatus.PASSED,
) -> VerificationReceipt:
    time_bounds = {
        "unit:a": ("2026-07-15T00:00:00Z", "2026-07-15T00:00:01Z"),
        "unit:b": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
        "unit:audit": ("2026-07-15T00:00:03Z", "2026-07-15T00:00:04Z"),
    }
    started_at, completed_at = time_bounds.get(
        unit.unit_ref,
        ("2026-07-15T00:00:00Z", "2026-07-15T00:00:01Z"),
    )
    result_ref = f"result-ref:verification:{hashlib.sha256(unit.unit_ref.encode()).hexdigest()}"
    receipt = VerificationReceipt(
        schema_version="uaa_verification_receipt.v4",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        unit_ref=unit.unit_ref,
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=1_000,
        result_refs=(result_ref,),
        output_byte_count=0,
        output_digest=DIGEST,
        command_refs=unit.command_refs,
        command_result_bindings=((unit.command_refs[0], result_ref),),
        execution_surface_ref=SURFACE,
        proof_equivalence_ref=unit.proof_equivalence_ref,
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        execution_identity_ref=build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref=SURFACE,
        ).identity_ref,
        executed_command_result_bindings=((unit.command_refs[0], result_ref),),
        observed_platform_fingerprint=DIGEST,
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    return replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )


def _refingerprint(receipt: VerificationReceipt) -> VerificationReceipt:
    receipt = replace(
        receipt,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    return replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )


def test_whole_run_is_canonical_content_bound_and_order_independent() -> None:
    units = _units()
    plan = _plan(units)
    a = _receipt(plan, units[0])
    b = _receipt(plan, units[1])

    first = aggregate_verification_run(
        plan, units, (b, a), execution_surface_ref=SURFACE
    )
    second = aggregate_verification_run(
        plan, units, (a, b), execution_surface_ref=SURFACE
    )

    assert first.run_manifest == second.run_manifest
    assert first.run_manifest.status is VerificationTerminalStatus.PASSED
    assert first.run_manifest.required_unit_refs == (
        "unit:a",
        "unit:b",
        "unit:aggregate",
    )
    assert tuple(ref for ref, _ in first.run_manifest.unit_receipt_bindings) == (
        "unit:a",
        "unit:b",
        "unit:aggregate",
    )
    assert first.run_manifest.missing_unit_refs == ()
    assert len(first.derived_receipts) == 1
    first.run_manifest.validate()


def test_commandless_aggregate_binds_source_platform_observations() -> None:
    units = _units()
    plan = _plan(units)
    first_source = _refingerprint(
        replace(
            _receipt(plan, units[0]),
            observed_platform_fingerprint="a" * 64,
        )
    )
    second_source = _refingerprint(
        replace(
            _receipt(plan, units[1]),
            observed_platform_fingerprint="b" * 64,
        )
    )

    result = aggregate_verification_run(
        plan,
        units,
        (second_source, first_source),
        execution_surface_ref=SURFACE,
    )

    expected = hashlib.sha256(
        json.dumps(
            (
                ("unit:a", "a" * 64),
                ("unit:b", "b" * 64),
            ),
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    assert result.derived_receipts[0].observed_platform_fingerprint == expected


def test_declared_typed_optional_block_does_not_weaken_required_units() -> None:
    base_units = _units()
    units = (
        replace(base_units[0], evidence_posture="typed_optional"),
        *base_units[1:],
    )
    plan = _plan(units)
    optional = _receipt(
        plan,
        units[0],
        status=VerificationTerminalStatus.BLOCKED,
    )
    required = _receipt(plan, units[1])

    result = aggregate_verification_run(
        plan,
        units,
        (optional, required),
        execution_surface_ref=SURFACE,
    )

    assert result.run_manifest.status is VerificationTerminalStatus.PASSED
    assert result.run_manifest.missing_unit_refs == ()


def test_missing_audit_is_blocked_and_never_synthesized() -> None:
    units = _units(include_audit=True)
    plan = _plan(units)
    result = aggregate_verification_run(
        plan,
        units,
        (_receipt(plan, units[0]), _receipt(plan, units[1])),
        execution_surface_ref=SURFACE,
    )

    assert result.run_manifest.status is VerificationTerminalStatus.BLOCKED
    assert result.run_manifest.missing_unit_refs == ("unit:audit",)
    assert tuple(receipt.unit_ref for receipt in result.derived_receipts) == (
        "unit:aggregate",
    )


def test_failed_dependency_propagates_to_aggregate_and_run() -> None:
    units = _units()
    plan = _plan(units)
    result = aggregate_verification_run(
        plan,
        units,
        (
            _receipt(plan, units[0]),
            _receipt(plan, units[1], status=VerificationTerminalStatus.FAILED),
        ),
        execution_surface_ref=SURFACE,
    )

    assert result.run_manifest.status is VerificationTerminalStatus.FAILED
    assert result.run_manifest.failed_unit_refs == ("unit:b", "unit:aggregate")


def test_dependent_receipt_without_passed_dependency_is_rejected() -> None:
    units = _units()
    plan = _plan(units)

    with pytest.raises(ValueError, match="contradicts dependency"):
        aggregate_verification_run(
            plan,
            units,
            (_receipt(plan, units[1]),),
            execution_surface_ref=SURFACE,
        )

    with pytest.raises(ValueError, match="contradicts dependency"):
        aggregate_verification_run(
            plan,
            units,
            (
                _receipt(
                    plan,
                    units[0],
                    status=VerificationTerminalStatus.FAILED,
                ),
                _receipt(plan, units[1]),
            ),
            execution_surface_ref=SURFACE,
        )


def test_dependent_receipt_cannot_start_before_dependency_completes() -> None:
    units = _units()
    plan = _plan(units)
    b = _refingerprint(
        replace(
            _receipt(plan, units[1]),
            started_at="2026-07-15T00:00:00Z",
        )
    )

    with pytest.raises(ValueError, match="precedes dependency"):
        aggregate_verification_run(
            plan,
            units,
            (_receipt(plan, units[0]), b),
            execution_surface_ref=SURFACE,
        )


@pytest.mark.parametrize(
    "change",
    (
        {"needs": ()},
        {"timeout_minutes": 44},
        {"execution_surfaces": ("private",)},
        {"unit_kind": VerificationUnitKind.AUDIT, "command_refs": ()},
    ),
)
def test_changed_canonical_unit_definition_is_rejected(
    change: dict[str, object],
) -> None:
    units = _units()
    plan = _plan(units)
    changed_b = replace(units[1], **change)
    changed_units = (units[0], changed_b, units[2])

    with pytest.raises(ValueError, match="canonical DAG|exact selected units"):
        aggregate_verification_run(
            plan,
            changed_units,
            (_receipt(plan, units[0]), _receipt(plan, units[1])),
            execution_surface_ref=SURFACE,
        )


@pytest.mark.parametrize(
    "change",
    (
        {"selected_command_refs": ("command:a", "command:b", "command:extra")},
        {"selected_lane_refs": ("lane:a", "lane:b", "lane:extra")},
        {
            "typescript_typecheck_required": True,
            "typescript_project_posture": "project_bound",
        },
        {"full_pytest_required": True},
    ),
)
def test_extra_plan_membership_or_gate_posture_is_rejected(
    change: dict[str, object],
) -> None:
    units = _units()
    plan = _plan(units)
    changed_plan = replace(plan, **change, plan_fingerprint="0" * 64)
    changed_plan = replace(
        changed_plan,
        plan_fingerprint=verification_plan_contract_fingerprint(changed_plan),
    )

    with pytest.raises(ValueError, match="membership|gate posture"):
        aggregate_verification_run(
            changed_plan,
            units,
            (
                _receipt(changed_plan, units[0]),
                _receipt(changed_plan, units[1]),
            ),
            execution_surface_ref=SURFACE,
        )


@pytest.mark.parametrize(
    "change",
    (
        {
            "result_refs": ("lowercase-secret",),
            "command_result_bindings": (("command:a", "lowercase-secret"),),
            "executed_command_result_bindings": (
                ("command:a", "lowercase-secret"),
            ),
        },
        {"execution_identity_ref": "lowercase-secret"},
        {"equivalent_receipt_ref": "lowercase-secret"},
    ),
)
def test_v4_receipt_rejects_plain_dynamic_refs(change: dict[str, object]) -> None:
    units = _units()
    plan = _plan(units)
    receipt = _refingerprint(replace(_receipt(plan, units[0]), **change))

    with pytest.raises(ValueError, match="content-bound|SHA-256"):
        receipt.validate()


def test_executed_command_binding_cannot_use_a_receipt_ref() -> None:
    units = _units()
    plan = _plan(units)
    receipt_ref = f"receipt:verification:{'d' * 64}"
    receipt = _refingerprint(
        replace(
            _receipt(plan, units[0]),
            result_refs=(receipt_ref,),
            command_result_bindings=(("command:a", receipt_ref),),
            executed_command_result_bindings=(("command:a", receipt_ref),),
        )
    )

    with pytest.raises(ValueError, match="executed result"):
        receipt.validate()


def test_non_typescript_v4_receipt_rejects_extraneous_runtime_binding() -> None:
    units = _units()
    plan = _plan(units)
    receipt = _refingerprint(
        replace(
            _receipt(plan, units[0]),
            typescript_binding_posture="resolved",
            typescript_project_fingerprint="1" * 64,
            typescript_runtime_fingerprint="2" * 64,
            typescript_version_ref="typescript-version:7.0.2",
        )
    )

    with pytest.raises(ValueError, match="non-TypeScript"):
        receipt.validate()


def test_typescript_typecheck_receipt_requires_runtime_even_on_failure() -> None:
    units = _units()
    plan = _plan(units)
    result_ref = f"result-ref:verification:{'3' * 64}"
    receipt = _refingerprint(
        replace(
            _receipt(
                plan,
                units[0],
                status=VerificationTerminalStatus.FAILED,
            ),
            command_refs=("command:frontend.typecheck",),
            result_refs=(result_ref,),
            command_result_bindings=(("command:frontend.typecheck", result_ref),),
            executed_command_result_bindings=(
                ("command:frontend.typecheck", result_ref),
            ),
        )
    )

    with pytest.raises(ValueError, match="pre-start runtime binding"):
        receipt.validate()


def test_v3_run_rejects_plain_receipt_refs() -> None:
    units = _units()
    plan = _plan(units)
    result = aggregate_verification_run(
        plan,
        units,
        (_receipt(plan, units[0]), _receipt(plan, units[1])),
        execution_surface_ref=SURFACE,
    )
    run = replace(
        result.run_manifest,
        receipt_refs=("lowercase-secret",) + result.run_manifest.receipt_refs[1:],
        unit_receipt_bindings=(
            (result.run_manifest.unit_receipt_bindings[0][0], "lowercase-secret"),
            *result.run_manifest.unit_receipt_bindings[1:],
        ),
        run_ref=f"run:verification:{'0' * 64}",
        run_fingerprint="0" * 64,
    )
    fingerprint = verification_run_manifest_fingerprint(run)
    run = replace(
        run,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )

    with pytest.raises(ValueError, match="content-bound"):
        run.validate()


def test_blocked_v3_run_cannot_claim_failed_units() -> None:
    units = _units()
    plan = _plan(units)
    result = aggregate_verification_run(
        plan,
        units,
        (_receipt(plan, units[0]),),
        execution_surface_ref=SURFACE,
    )
    run = replace(
        result.run_manifest,
        failed_unit_refs=("unit:a",),
        run_ref=f"run:verification:{'0' * 64}",
        run_fingerprint="0" * 64,
    )
    fingerprint = verification_run_manifest_fingerprint(run)
    run = replace(
        run,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )

    with pytest.raises(ValueError, match="cannot claim failures"):
        run.validate()


@pytest.mark.parametrize(
    "change",
    (
        {"repository_sha": "c" * 40},
        {"dependency_lock_set_fingerprint": "c" * 64},
        {"platform_fingerprint": "c" * 64},
        {"command_manifest_fingerprint": "c" * 64},
        {"verifier_definition_fingerprint": "c" * 64},
        {"test_collection_fingerprint": "c" * 64},
        {"pytest_shard_plan_fingerprint": "c" * 64},
        {"execution_surface_ref": "surface-ref:github"},
    ),
)
def test_cross_identity_receipts_are_rejected(change: dict[str, str]) -> None:
    units = _units()
    plan = _plan(units)
    changed = _refingerprint(replace(_receipt(plan, units[0]), **change))

    with pytest.raises(ValueError, match="exact plan"):
        aggregate_verification_run(
            plan,
            units,
            (changed, _receipt(plan, units[1])),
            execution_surface_ref=SURFACE,
        )


def test_duplicate_and_extra_evidence_are_rejected() -> None:
    units = _units()
    plan = _plan(units)
    a = _receipt(plan, units[0])
    b = _receipt(plan, units[1])

    with pytest.raises(ValueError, match="duplicate evidence"):
        aggregate_verification_run(
            plan, units, (a, a, b), execution_surface_ref=SURFACE
        )

    extra_unit = VerificationUnit(
        unit_ref="unit:extra",
        display_name="Extra",
        lane_ref="lane:extra",
        needs=(),
        command_refs=("command:extra",),
        proof_equivalence_ref="proof-equivalence:extra",
    )
    extra_plan = _plan((*units, extra_unit))
    extra = _receipt(extra_plan, extra_unit)
    with pytest.raises(ValueError, match="extra evidence"):
        aggregate_verification_run(
            plan, units, (a, b, extra), execution_surface_ref=SURFACE
        )
