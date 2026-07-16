from __future__ import annotations

from pathlib import Path

from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    build_plan,
)
from scripts.verification.changed_path_selector import select_paths
from scripts.verification.ci_fallback_contracts import PrivateVerificationScope
from scripts.verification.plan_affected_verification import (
    changed_records,
    unsafe_path_refs,
)
from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationRiskTier,
    dependency_state_fingerprint,
)
from scripts.verification.verification_risk import (
    classify_changes,
    unit_refs_for_selection,
)


_ALWAYS_FOCUSED_UNIT_REFS = {
    "risk-diff-check",
    "risk-product-truth",
    "risk-redaction",
}
_FORBIDDEN_PRIVATE_UNIT_REFS = {
    "pytest-shards",
    "pytest",
    "control-center-frontend",
}
_FORBIDDEN_PRIVATE_COMMAND_REFS = {
    "command:pytest.sharded-suite",
    "command:frontend.typecheck",
    "command:frontend.check",
}


class PrivateScopeFullGateRequiredError(ValueError):
    """Safe fail-closed signal when affected selection requires the full gate."""

    reason_ref = "reason-ref:private-ci:full-gate-required"

    def __init__(self, selector_reason_refs: tuple[str, ...]) -> None:
        self.reason_refs = tuple(
            dict.fromkeys((self.reason_ref, *selector_reason_refs))
        )
        super().__init__("PRIVATE_CI_FULL_GATE_REQUIRES_EXPLICIT_DIAGNOSTIC")


def _validate_diagnostic_unit_refs(
    diagnostic_unit_refs: tuple[str, ...],
) -> tuple[str, ...]:
    if (
        not isinstance(diagnostic_unit_refs, tuple)
        or len(diagnostic_unit_refs) != len(set(diagnostic_unit_refs))
        or len(diagnostic_unit_refs) > 8
    ):
        raise ValueError("private CI diagnostic units must be a bounded unique tuple")
    allowed = {f"diagnostic-pytest-shard-{index}" for index in range(8)}
    if any(unit_ref not in allowed for unit_ref in diagnostic_unit_refs):
        raise ValueError("private CI diagnostic unit is not canonical")
    return tuple(sorted(diagnostic_unit_refs, key=lambda value: int(value.rsplit("-", 1)[1])))


def _focused_unit_refs(
    *,
    risk_tier: VerificationRiskTier,
    surface_refs: tuple[str, ...],
    selected_test_refs: tuple[str, ...],
) -> tuple[str, ...]:
    surfaces = set(surface_refs)
    refs = set(_ALWAYS_FOCUSED_UNIT_REFS)
    if risk_tier.rank >= VerificationRiskTier.TIER_1.rank:
        refs.add("risk-ruff")
    if "surface-ref:documentation" in surfaces:
        refs.add("risk-documentation")
    if "surface-ref:frontend" in surfaces:
        # Complete TypeScript is deliberately reserved for the final exact-SHA
        # GitHub run.  Vite build currently depends on that singleton in the
        # canonical DAG, so private diagnosis runs the isolated tests and safety
        # verifier but defers the build and typecheck together.
        refs.update({"risk-frontend-tests", "risk-frontend-safety"})
    if "surface-ref:api" in surfaces:
        refs.update({"risk-openapi", "risk-api-safety"})
    if selected_test_refs:
        refs.add("risk-focused-pytest")
    return tuple(unit.unit_ref for unit in VERIFICATION_DAG if unit.unit_ref in refs)


def build_private_verification_scope(
    repo: Path,
    *,
    repository_sha: str,
    base_sha: str,
    source_branch_binding_ref: str,
    diagnostic_unit_refs: tuple[str, ...] = (),
    verify_repository_state: bool = True,
) -> tuple[PrivateVerificationScope, VerificationPlan]:
    """Build one exact affected/diagnostic-only scope from the canonical DAG."""

    diagnostics = _validate_diagnostic_unit_refs(diagnostic_unit_refs)
    records = changed_records(repo, base_sha=base_sha, head_sha=repository_sha)
    unsafe_refs = unsafe_path_refs(
        repo,
        head_sha=repository_sha,
        records=records,
    )
    selection = classify_changes(records, unsafe_path_refs=unsafe_refs)
    affected_selection = select_paths(
        list(selection.changed_path_refs),
        tier="affected",
        repo=repo,
    )
    if affected_selection.status == "full_gate_required" and not diagnostics:
        raise PrivateScopeFullGateRequiredError(
            affected_selection.fallback_reason_refs
        )
    authoritative_unit_refs = unit_refs_for_selection(
        selection,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
    )
    authoritative_plan = build_plan(
        repo,
        repository_sha,
        change_records=records,
        selected_unit_refs=authoritative_unit_refs,
        base_sha=base_sha,
        unsafe_path_refs=unsafe_refs,
        verify_repository_state=verify_repository_state,
    )
    selected_unit_refs = (
        *_focused_unit_refs(
            risk_tier=selection.tier,
            surface_refs=selection.surface_refs,
            selected_test_refs=affected_selection.selected_test_refs,
        ),
        *diagnostics,
    )
    private_plan = build_plan(
        repo,
        repository_sha,
        change_records=records,
        selected_unit_refs=selected_unit_refs,
        base_sha=base_sha,
        unsafe_path_refs=unsafe_refs,
        selected_test_refs=affected_selection.selected_test_refs,
        verify_repository_state=verify_repository_state,
    )
    units_by_ref = {unit.unit_ref: unit for unit in VERIFICATION_DAG}
    for unit_ref in private_plan.selected_unit_refs:
        unit = units_by_ref[unit_ref]
        if (
            unit_ref in _FORBIDDEN_PRIVATE_UNIT_REFS
            or unit.unit_kind.value in {"aggregate", "audit"}
            or "private" not in unit.execution_surfaces
            or "resource-ref:complete-pytest" in unit.exclusive_resource_refs
            or "resource-ref:typescript-typecheck" in unit.exclusive_resource_refs
            or set(unit.command_refs).intersection(_FORBIDDEN_PRIVATE_COMMAND_REFS)
        ):
            raise ValueError("private CI scope contains a forbidden verification unit")
    deferred = tuple(
        unit_ref
        for unit_ref in authoritative_plan.selected_unit_refs
        if unit_ref not in private_plan.selected_unit_refs
    )
    reason_refs = tuple(
        dict.fromkeys(
            (
                *selection.reason_refs,
                *affected_selection.fallback_reason_refs,
                "reason-ref:private-ci:complete-pytest-github-only",
                "reason-ref:private-ci:typescript-typecheck-github-only",
                "reason-ref:private-ci:github-final-gate-required",
            )
        )
    )
    scope = PrivateVerificationScope(
        schema_version="uaa_ci_private_scope.v1",
        repository_sha=repository_sha,
        base_sha=base_sha,
        source_branch_binding_ref=source_branch_binding_ref,
        authoritative_plan_fingerprint=authoritative_plan.plan_fingerprint,
        plan_fingerprint=private_plan.plan_fingerprint,
        dependency_state_fingerprint=dependency_state_fingerprint(private_plan),
        risk_tier=selection.tier.value,
        selected_unit_refs=private_plan.selected_unit_refs,
        selected_command_refs=private_plan.selected_command_refs,
        diagnostic_unit_refs=diagnostics,
        deferred_unit_refs=deferred,
        reason_refs=reason_refs,
    )
    scope.validate()
    return scope, private_plan
