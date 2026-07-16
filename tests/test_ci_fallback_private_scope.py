from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import ci_fallback_private_scope as private_scope
from scripts.verification.ci_fallback_contracts import (
    PrivateVerificationResult,
    PrivateVerificationScope,
)
from scripts.verification.verification_contracts import VerificationRiskTier
from scripts.verification.verification_risk import ChangeKind, ChangeRecord


SHA = "a" * 40
BASE_SHA = "b" * 40
BRANCH_BINDING_REF = "branch-binding-ref:private-ci:" + "f" * 64


def exact_scope() -> PrivateVerificationScope:
    return PrivateVerificationScope(
        schema_version="uaa_ci_private_scope.v1",
        repository_sha=SHA,
        base_sha=BASE_SHA,
        source_branch_binding_ref=BRANCH_BINDING_REF,
        authoritative_plan_fingerprint="c" * 64,
        plan_fingerprint="d" * 64,
        dependency_state_fingerprint="e" * 64,
        risk_tier="tier_3",
        selected_unit_refs=("risk-diff-check", "diagnostic-pytest-shard-2"),
        selected_command_refs=(
            "command:git.diff-check",
            "command:pytest.shard-2-reproduce",
        ),
        diagnostic_unit_refs=("diagnostic-pytest-shard-2",),
        deferred_unit_refs=("pytest-shards", "control-center-frontend"),
        reason_refs=("reason-ref:private-ci:github-final-gate-required",),
    )


def test_private_scope_rejects_complete_pytest_typescript_and_bad_diagnostics() -> None:
    exact_scope().validate()
    with pytest.raises(ValueError, match="complete singleton"):
        replace(
            exact_scope(),
            selected_unit_refs=("risk-diff-check", "pytest-shards"),
            diagnostic_unit_refs=(),
            deferred_unit_refs=("control-center-frontend",),
        ).validate()
    with pytest.raises(ValueError, match="complete singleton"):
        replace(
            exact_scope(),
            selected_command_refs=(
                "command:git.diff-check",
                "command:frontend.typecheck",
            ),
        ).validate()
    with pytest.raises(ValueError, match="diagnostics"):
        replace(
            exact_scope(),
            diagnostic_unit_refs=("diagnostic-pytest-shard-7",),
        ).validate()


def test_private_result_can_never_satisfy_github_or_merge_gate() -> None:
    scope = exact_scope()
    result = PrivateVerificationResult(
        repository_sha=scope.repository_sha,
        base_sha=scope.base_sha,
        source_branch_binding_ref=scope.source_branch_binding_ref,
        authoritative_plan_fingerprint=scope.authoritative_plan_fingerprint,
        plan_fingerprint=scope.plan_fingerprint,
        dependency_state_fingerprint=scope.dependency_state_fingerprint,
        selected_unit_refs=scope.selected_unit_refs,
        diagnostic_unit_refs=scope.diagnostic_unit_refs,
        deferred_unit_refs=scope.deferred_unit_refs,
        status="pass",
        receipt_ref="receipt-ref:private-ci:" + "0" * 64,
        command_result_refs=("result-ref:ci:" + "1" * 64,),
        timings_ms=(("unit-ref:risk-diff-check", 1),),
        started_at="2026-01-01T00:00:00Z",
        completed_at="2026-01-01T00:00:01Z",
    )
    payload = {
        key: value for key, value in asdict(result).items() if key != "receipt_ref"
    }
    result = replace(
        result,
        receipt_ref=(
            "receipt-ref:private-ci:"
            + hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        ),
    )
    result.validate()

    with pytest.raises(ValueError, match="authoritative gate"):
        replace(result, merge_gate_satisfied=True).validate()


def test_scope_builder_selects_only_focused_and_explicit_diagnostic_units(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = SimpleNamespace(
        tier=VerificationRiskTier.TIER_3,
        surface_refs=("surface-ref:verification",),
        changed_path_refs=("tests/test_ci_fallback_controller.py",),
        reason_refs=("reason-ref:risk:verification-topology",),
    )
    monkeypatch.setattr(private_scope, "changed_records", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(private_scope, "unsafe_path_refs", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(private_scope, "classify_changes", lambda *_args, **_kwargs: selection)
    monkeypatch.setattr(
        private_scope,
        "unit_refs_for_selection",
        lambda *_args, **_kwargs: (
            "pytest-shards",
            "control-center-frontend",
            "foundation-gate-report",
        ),
    )
    plans: list[SimpleNamespace] = []

    def fake_build_plan(_repo: Path, _sha: str, **kwargs: object) -> SimpleNamespace:
        selected = tuple(kwargs["selected_unit_refs"])
        plan = SimpleNamespace(
            plan_fingerprint=("c" if not plans else "d") * 64,
            selected_unit_refs=selected,
            selected_command_refs=tuple(
                command_ref
                for unit_ref in selected
                for command_ref in {
                    "risk-diff-check": ("command:git.diff-check",),
                    "risk-product-truth": (
                        "command:product-truth.regression-verifier",
                    ),
                    "risk-redaction": ("command:security.artifact-redaction",),
                    "risk-ruff": ("command:ci.ruff",),
                    "risk-focused-pytest": ("command:pytest.focused",),
                    "diagnostic-pytest-shard-2": (
                        "command:pytest.shard-2-reproduce",
                    ),
                    "pytest-shards": ("command:pytest.sharded-suite",),
                    "control-center-frontend": ("command:frontend.check",),
                    "foundation-gate-report": (
                        "command:foundation-gate.ci-parallel",
                    ),
                }.get(unit_ref, ())
            ),
        )
        plans.append(plan)
        return plan

    monkeypatch.setattr(private_scope, "build_plan", fake_build_plan)
    monkeypatch.setattr(
        private_scope,
        "dependency_state_fingerprint",
        lambda _plan: "e" * 64,
    )

    scope, _plan = private_scope.build_private_verification_scope(
        tmp_path,
        repository_sha=SHA,
        base_sha=BASE_SHA,
        source_branch_binding_ref=BRANCH_BINDING_REF,
        diagnostic_unit_refs=("diagnostic-pytest-shard-2",),
    )

    assert "pytest-shards" not in scope.selected_unit_refs
    assert "control-center-frontend" not in scope.selected_unit_refs
    assert "command:frontend.typecheck" not in scope.selected_command_refs
    assert scope.diagnostic_unit_refs == ("diagnostic-pytest-shard-2",)
    assert set(scope.deferred_unit_refs) == {
        "pytest-shards",
        "control-center-frontend",
        "foundation-gate-report",
    }


def test_scope_builder_uses_canonical_source_owned_test_from_exact_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_ref = "src/ultimate_ai_agent/core/example.py"
    test_ref = "tests/test_example.py"
    (tmp_path / source_ref).parent.mkdir(parents=True)
    (tmp_path / source_ref).write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / test_ref).parent.mkdir(parents=True)
    (tmp_path / test_ref).write_text("def test_value(): pass\n", encoding="utf-8")
    selection = SimpleNamespace(
        tier=VerificationRiskTier.TIER_2,
        surface_refs=("surface-ref:python", "surface-ref:core"),
        changed_path_refs=(source_ref,),
        reason_refs=("reason-ref:risk:bounded-core",),
    )
    monkeypatch.setattr(private_scope, "changed_records", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(private_scope, "unsafe_path_refs", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(private_scope, "classify_changes", lambda *_args, **_kwargs: selection)
    monkeypatch.setattr(
        private_scope,
        "unit_refs_for_selection",
        lambda *_args, **_kwargs: ("pytest-shards",),
    )
    calls: list[dict[str, object]] = []
    units_by_ref = {unit.unit_ref: unit for unit in private_scope.VERIFICATION_DAG}

    def fake_build_plan(_repo: Path, _sha: str, **kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        selected = tuple(kwargs["selected_unit_refs"])
        return SimpleNamespace(
            plan_fingerprint=("c" if len(calls) == 1 else "d") * 64,
            selected_unit_refs=selected,
            selected_command_refs=tuple(
                dict.fromkeys(
                    command_ref
                    for unit_ref in selected
                    for command_ref in units_by_ref[unit_ref].command_refs
                )
            ),
        )

    monkeypatch.setattr(private_scope, "build_plan", fake_build_plan)
    monkeypatch.setattr(
        private_scope,
        "dependency_state_fingerprint",
        lambda _plan: "e" * 64,
    )

    scope, _plan = private_scope.build_private_verification_scope(
        tmp_path,
        repository_sha=SHA,
        base_sha=BASE_SHA,
        source_branch_binding_ref=BRANCH_BINDING_REF,
    )

    assert calls[1]["selected_test_refs"] == (test_ref,)
    assert "risk-focused-pytest" in scope.selected_unit_refs
    assert "command:pytest.focused" in scope.selected_command_refs


@pytest.mark.parametrize(
    ("path_ref", "selector_reason_ref"),
    [
        ("unclassified/new_surface.xyz", "reason-ref:verification:unknown-path"),
        (
            "scripts/verification/new_topology.py",
            "reason-ref:verification:critical-topology-change",
        ),
    ],
)
def test_scope_builder_fails_closed_when_affected_selection_requires_full_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_ref: str,
    selector_reason_ref: str,
) -> None:
    records = (ChangeRecord(ChangeKind.MODIFIED, (path_ref,)),)
    monkeypatch.setattr(
        private_scope,
        "changed_records",
        lambda *_args, **_kwargs: records,
    )
    monkeypatch.setattr(private_scope, "unsafe_path_refs", lambda *_args, **_kwargs: ())

    with pytest.raises(
        private_scope.PrivateScopeFullGateRequiredError,
        match="PRIVATE_CI_FULL_GATE_REQUIRES_EXPLICIT_DIAGNOSTIC",
    ) as raised:
        private_scope.build_private_verification_scope(
            tmp_path,
            repository_sha=SHA,
            base_sha=BASE_SHA,
            source_branch_binding_ref=BRANCH_BINDING_REF,
        )

    assert raised.value.reason_refs == (
        "reason-ref:private-ci:full-gate-required",
        selector_reason_ref,
    )
