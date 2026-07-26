from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime

from scripts.verification.verification_contracts import (
    MAX_RECEIPTS,
    VerificationPlan,
    VerificationReceipt,
    VerificationRiskTier,
    VerificationRunManifest,
    VerificationTerminalStatus,
    VerificationUnit,
    VerificationUnitKind,
    dependency_closed_unit_refs,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_receipt_fingerprint,
    verification_dag_definition_fingerprint,
    verification_run_manifest_fingerprint,
    verification_unit_definition_fingerprint,
    validate_verification_dag,
)
from scripts.verification.verification_execution_identity import (
    build_verification_execution_identity,
)
from scripts.verification.ci_command_manifest import observed_platform_fingerprint


RUN_SCHEMA_VERSION = "uaa_verification_run.v3"
RECEIPT_SCHEMA_VERSION = "uaa_verification_receipt.v3"


@dataclass(frozen=True)
class VerificationAggregateResult:
    run_manifest: VerificationRunManifest
    derived_receipts: tuple[VerificationReceipt, ...]


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_receipt_for_plan_unit(
    receipt: VerificationReceipt,
    *,
    plan: VerificationPlan,
    unit: VerificationUnit,
    execution_surface_ref: str,
) -> None:
    receipt.validate()
    expected_identity_ref = build_verification_execution_identity(
        plan,
        unit,
        execution_surface_ref=execution_surface_ref,
        typescript_runtime_fingerprint=receipt.typescript_runtime_fingerprint,
        typescript_version_ref=receipt.typescript_version_ref,
    ).identity_ref
    if (
        receipt.schema_version != RECEIPT_SCHEMA_VERSION
        or receipt.plan_fingerprint != plan.plan_fingerprint
        or receipt.repository_sha != plan.repository_sha
        or receipt.dependency_state_fingerprint != dependency_state_fingerprint(plan)
        or receipt.dependency_lock_set_fingerprint
        != dependency_lock_set_fingerprint(plan)
        or receipt.platform_fingerprint != plan.platform_fingerprint
        or receipt.command_manifest_fingerprint
        != plan.command_manifest_fingerprint
        or receipt.verifier_definition_fingerprint
        != plan.verifier_definition_fingerprint
        or receipt.test_collection_fingerprint != plan.test_collection_fingerprint
        or receipt.pytest_shard_plan_fingerprint
        != plan.pytest_shard_plan_fingerprint
        or (
            receipt.status is VerificationTerminalStatus.PASSED
            and receipt.command_refs != unit.command_refs
        )
        or (
            receipt.status is not VerificationTerminalStatus.PASSED
            and bool(unit.command_refs)
            and (
                not receipt.command_refs
                or receipt.command_refs
                != unit.command_refs[: len(receipt.command_refs)]
            )
        )
        or (not unit.command_refs and bool(receipt.command_refs))
        or receipt.proof_equivalence_ref != unit.proof_equivalence_ref
        or receipt.execution_surface_ref != execution_surface_ref
        or receipt.execution_identity_ref != expected_identity_ref
        or (
            receipt.nonexecuted_command_result_bindings
            and unit.evidence_posture != "typed_optional"
        )
    ):
        raise ValueError("verification receipt does not match the exact plan")
    if (
        receipt.typescript_binding_posture == "resolved"
        and receipt.typescript_project_fingerprint
        != plan.typescript_project_fingerprint
    ):
        raise ValueError("verification receipt TypeScript binding is stale")


def _derive_aggregate_receipt(
    plan: VerificationPlan,
    unit: VerificationUnit,
    dependencies: tuple[VerificationReceipt, ...],
    *,
    execution_surface_ref: str,
    typed_optional_unit_refs: frozenset[str] = frozenset(),
) -> VerificationReceipt:
    if unit.unit_kind is not VerificationUnitKind.AGGREGATE or not dependencies:
        raise ValueError("aggregate receipt requires exact dependency evidence")
    dependency_statuses = {receipt.status for receipt in dependencies}
    if VerificationTerminalStatus.FAILED in dependency_statuses:
        status = VerificationTerminalStatus.FAILED
    elif all(
        receipt.status is VerificationTerminalStatus.PASSED
        or (
            receipt.unit_ref in typed_optional_unit_refs
            and receipt.status
            in {
                VerificationTerminalStatus.BLOCKED,
                VerificationTerminalStatus.SKIPPED,
            }
        )
        for receipt in dependencies
    ):
        status = VerificationTerminalStatus.PASSED
    else:
        status = VerificationTerminalStatus.BLOCKED
    started = min(dependencies, key=lambda receipt: _timestamp(receipt.started_at))
    completed = max(dependencies, key=lambda receipt: _timestamp(receipt.completed_at))
    duration_ms = max(
        0,
        int(
            (_timestamp(completed.completed_at) - _timestamp(started.started_at))
            .total_seconds()
            * 1000
        ),
    )
    result_refs = tuple(receipt.receipt_ref for receipt in dependencies)
    output_digest = hashlib.sha256(
        json.dumps(result_refs, separators=(",", ":")).encode()
    ).hexdigest()
    receipt = VerificationReceipt(
        schema_version=RECEIPT_SCHEMA_VERSION,
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
        started_at=started.started_at,
        completed_at=completed.completed_at,
        duration_ms=duration_ms,
        result_refs=result_refs,
        output_byte_count=0,
        output_digest=output_digest,
        command_refs=(),
        command_result_bindings=(),
        execution_surface_ref=execution_surface_ref,
        proof_equivalence_ref=unit.proof_equivalence_ref,
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        execution_identity_ref=build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref=execution_surface_ref,
        ).identity_ref,
        observed_platform_fingerprint=observed_platform_fingerprint(),
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    receipt = replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    receipt.validate()
    return receipt


def _validate_reused_commands(
    receipts_by_unit: dict[str, VerificationReceipt],
    canonical_by_ref: dict[str, VerificationUnit],
) -> None:
    receipt_by_ref = {
        receipt.receipt_ref: receipt for receipt in receipts_by_unit.values()
    }
    for unit_ref, receipt in receipts_by_unit.items():
        dependency_closure = set(
            dependency_closed_unit_refs(
                tuple(canonical_by_ref.values()),
                canonical_by_ref[unit_ref].needs,
            )
        )
        for command_ref, source_receipt_ref in receipt.reused_command_receipt_bindings:
            source = receipt_by_ref.get(source_receipt_ref)
            if (
                source is None
                or source.unit_ref not in dependency_closure
                or source.status is not VerificationTerminalStatus.PASSED
                or command_ref
                not in dict(source.executed_command_result_bindings)
            ):
                raise ValueError("reused verification command lacks exact source proof")


def aggregate_verification_run(
    plan: VerificationPlan,
    canonical_units: tuple[VerificationUnit, ...],
    receipts: tuple[VerificationReceipt, ...],
    *,
    execution_surface_ref: str,
) -> VerificationAggregateResult:
    """Build one content-bound whole-plan run without granting merge authority."""

    plan.validate()
    validate_verification_dag(canonical_units)
    if (
        plan.schema_version
        not in {
            "uaa_ci_command_manifest.v4",
            "uaa_ci_command_manifest.v3",
            "uaa_verification_plan.v3",
        }
        or plan.verification_dag_fingerprint
        != verification_dag_definition_fingerprint(canonical_units)
    ):
        raise ValueError("verification plan does not bind the canonical DAG")
    if (
        dependency_closed_unit_refs(canonical_units, plan.selected_unit_refs)
        != plan.selected_unit_refs
    ):
        raise ValueError("verification plan membership is not canonically ordered")
    if len(receipts) > MAX_RECEIPTS:
        raise ValueError("verification aggregate exceeds its receipt bound")
    canonical_by_ref = {unit.unit_ref: unit for unit in canonical_units}
    selected = set(plan.selected_unit_refs)
    if selected - set(canonical_by_ref):
        raise ValueError("verification plan contains a noncanonical unit")
    if plan.selected_unit_definition_fingerprints != tuple(
        (
            unit_ref,
            verification_unit_definition_fingerprint(canonical_by_ref[unit_ref]),
        )
        for unit_ref in plan.selected_unit_refs
    ):
        raise ValueError("verification plan does not bind exact selected units")
    expected_lane_refs = tuple(
        dict.fromkeys(
            canonical_by_ref[unit_ref].lane_ref
            for unit_ref in plan.selected_unit_refs
            if canonical_by_ref[unit_ref].lane_ref is not None
        )
    )
    expected_command_refs = tuple(
        dict.fromkeys(
            command_ref
            for unit_ref in plan.selected_unit_refs
            for command_ref in canonical_by_ref[unit_ref].command_refs
        )
    )
    if (
        plan.selected_lane_refs != expected_lane_refs
        or plan.selected_command_refs != expected_command_refs
    ):
        raise ValueError("verification plan lane or command membership is not exact")
    selected_resources = {
        resource_ref
        for unit_ref in plan.selected_unit_refs
        for resource_ref in canonical_by_ref[unit_ref].exclusive_resource_refs
    }
    if (
        plan.typescript_typecheck_required
        != ("resource-ref:typescript-typecheck" in selected_resources)
        or plan.full_pytest_required
        != (
            plan.risk_tier is VerificationRiskTier.TIER_3
            or "resource-ref:complete-pytest" in selected_resources
        )
        or plan.release_gate_required != (
            plan.risk_tier is VerificationRiskTier.TIER_3
        )
    ):
        raise ValueError("verification plan gate posture is not exact")

    receipts_by_unit: dict[str, VerificationReceipt] = {}
    receipt_refs: set[str] = set()
    for receipt in receipts:
        unit = canonical_by_ref.get(receipt.unit_ref)
        if unit is None or receipt.unit_ref not in selected:
            raise ValueError("verification aggregate contains extra evidence")
        if unit.unit_kind is VerificationUnitKind.AGGREGATE:
            raise ValueError("aggregate verification receipts must be derived")
        if receipt.unit_ref in receipts_by_unit or receipt.receipt_ref in receipt_refs:
            raise ValueError("verification aggregate contains duplicate evidence")
        validate_receipt_for_plan_unit(
            receipt,
            plan=plan,
            unit=unit,
            execution_surface_ref=execution_surface_ref,
        )
        receipts_by_unit[receipt.unit_ref] = receipt
        receipt_refs.add(receipt.receipt_ref)

    derived: list[VerificationReceipt] = []
    for unit_ref in plan.selected_unit_refs:
        unit = canonical_by_ref[unit_ref]
        if unit.unit_kind is not VerificationUnitKind.AGGREGATE:
            continue
        dependency_closure = dependency_closed_unit_refs(
            canonical_units,
            unit.needs,
        )
        if not dependency_closure or any(
            dependency_ref not in receipts_by_unit
            for dependency_ref in dependency_closure
        ):
            continue
        aggregate = _derive_aggregate_receipt(
            plan,
            unit,
            tuple(receipts_by_unit[dependency_ref] for dependency_ref in dependency_closure),
            execution_surface_ref=execution_surface_ref,
            typed_optional_unit_refs=frozenset(
                candidate.unit_ref
                for candidate in canonical_units
                if candidate.evidence_posture == "typed_optional"
            ),
        )
        receipts_by_unit[unit_ref] = aggregate
        derived.append(aggregate)

    def satisfies_dependency(unit_ref: str, receipt: VerificationReceipt) -> bool:
        unit = canonical_by_ref[unit_ref]
        return receipt.status is VerificationTerminalStatus.PASSED or (
            unit.evidence_posture == "typed_optional"
            and receipt.status
            in {
                VerificationTerminalStatus.BLOCKED,
                VerificationTerminalStatus.SKIPPED,
            }
        )

    for unit_ref, receipt in receipts_by_unit.items():
        unit = canonical_by_ref[unit_ref]
        if unit.unit_kind is VerificationUnitKind.AGGREGATE:
            continue
        for dependency_ref in unit.needs:
            dependency = receipts_by_unit.get(dependency_ref)
            if (
                dependency is None
                or not satisfies_dependency(dependency_ref, dependency)
            ):
                raise ValueError(
                    "verification receipt contradicts dependency completion"
                )
            if _timestamp(dependency.completed_at) > _timestamp(receipt.started_at):
                raise ValueError(
                    "verification receipt precedes dependency completion"
                )

    _validate_reused_commands(receipts_by_unit, canonical_by_ref)

    ordered_receipts = tuple(
        receipts_by_unit[unit_ref]
        for unit_ref in plan.selected_unit_refs
        if unit_ref in receipts_by_unit
    )
    bound_units = tuple(receipt.unit_ref for receipt in ordered_receipts)
    missing_units = tuple(
        unit_ref for unit_ref in plan.selected_unit_refs if unit_ref not in receipts_by_unit
    )
    failed_units = tuple(
        receipt.unit_ref
        for receipt in ordered_receipts
        if receipt.status is VerificationTerminalStatus.FAILED
    )
    nonpassing = tuple(
        receipt.unit_ref
        for receipt in ordered_receipts
        if not satisfies_dependency(receipt.unit_ref, receipt)
    )
    if failed_units:
        status = VerificationTerminalStatus.FAILED
        reason_refs = ("reason-ref:verification:unit-failed",)
    elif missing_units or nonpassing:
        status = VerificationTerminalStatus.BLOCKED
        reason_refs = ("reason-ref:verification:whole-run-incomplete",)
    else:
        status = VerificationTerminalStatus.PASSED
        reason_refs = ()

    if ordered_receipts:
        started_at = min(
            ordered_receipts,
            key=lambda receipt: _timestamp(receipt.started_at),
        ).started_at
        completed_at = max(
            ordered_receipts,
            key=lambda receipt: _timestamp(receipt.completed_at),
        ).completed_at
    else:
        raise ValueError("verification aggregate requires at least one unit receipt")
    observed_collection_bindings = tuple(
        (receipt.unit_ref, receipt.observed_test_collection_fingerprint)
        for receipt in ordered_receipts
        if receipt.observed_test_collection_fingerprint is not None
    )
    run = VerificationRunManifest(
        schema_version=RUN_SCHEMA_VERSION,
        run_ref=f"run:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        repository_sha=plan.repository_sha,
        receipt_refs=tuple(receipt.receipt_ref for receipt in ordered_receipts),
        started_at=started_at,
        completed_at=completed_at,
        status=status,
        run_fingerprint="0" * 64,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        execution_surface_ref=execution_surface_ref,
        unit_receipt_bindings=tuple(
            (receipt.unit_ref, receipt.receipt_ref) for receipt in ordered_receipts
        ),
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        typescript_project_fingerprint=plan.typescript_project_fingerprint,
        required_unit_refs=plan.selected_unit_refs,
        missing_unit_refs=missing_units,
        failed_unit_refs=failed_units,
        reason_refs=reason_refs,
        observed_test_collection_bindings=observed_collection_bindings,
    )
    fingerprint = verification_run_manifest_fingerprint(run)
    run = replace(
        run,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )
    run.validate()
    if tuple(unit_ref for unit_ref, _receipt_ref in run.unit_receipt_bindings) != bound_units:
        raise ValueError("verification aggregate run order changed")
    return VerificationAggregateResult(run_manifest=run, derived_receipts=tuple(derived))
