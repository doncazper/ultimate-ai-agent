from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

import pytest

from scripts.verification.ci_command_manifest import CI_JOB_GRAPH, VERIFICATION_DAG
from scripts.verification.verification_contracts import (
    VerificationGateDecision,
    VerificationGateStatus,
    VerificationGithubGateProof,
    VerificationPlan,
    VerificationReceipt,
    VerificationRiskTier,
    VerificationRunManifest,
    VerificationTerminalStatus,
    VerificationUnit,
    VerificationValueRecord,
    dependency_closed_unit_refs,
    dependency_state_fingerprint,
    evaluate_verification_gate,
    evaluate_verification_gate_v2,
    verification_github_gate_proof_fingerprint,
    verification_plan_contract_fingerprint,
    verification_plan_payload,
    verification_receipt_fingerprint,
    verification_receipt_payload,
    verification_run_manifest_fingerprint,
    verification_run_manifest_payload,
    verification_dag_definition_fingerprint,
    verification_value_record_fingerprint,
    validate_verification_dag,
)
from scripts.verification.verification_risk import (
    ChangeKind,
    ChangeRecord,
    classify_changes,
    risk_definition_payload,
    unit_refs_for_selection,
)


SHA = "a" * 40
DIGEST = "b" * 64


def _change(path: str, kind: ChangeKind = ChangeKind.MODIFIED) -> ChangeRecord:
    return ChangeRecord(kind=kind, path_refs=(path,))


def _unit(unit_ref: str, *, needs: tuple[str, ...] = ()) -> VerificationUnit:
    return VerificationUnit(
        unit_ref=unit_ref,
        display_name=f"Verification {unit_ref}",
        lane_ref=f"lane:{unit_ref}",
        needs=needs,
        command_refs=(f"command:{unit_ref}",),
    )


def _plan() -> VerificationPlan:
    plan = VerificationPlan(
        schema_version="uaa_verification_plan.v2",
        profile_ref="profile:risk-tier-2",
        repository_sha=SHA,
        definition_fingerprint=DIGEST,
        dependency_lock_fingerprints=(("uv.lock", DIGEST),),
        affected_path_classification="tier_2",
        selected_lane_refs=("lane:risk-focused",),
        selected_command_refs=("command:risk-focused",),
        pytest_shard_plan_fingerprint=DIGEST,
        frontend_visual_scope="not_affected",
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        plan_fingerprint="0" * 64,
        base_sha=SHA,
        risk_manifest_version="uaa_verification_risk_manifest.v1",
        risk_manifest_fingerprint=DIGEST,
        risk_tier=VerificationRiskTier.TIER_2,
        changed_path_refs=("src/ultimate_ai_agent/core/evals/capability_metrics.py",),
        change_fingerprint=DIGEST,
        escalation_reason_refs=("reason-ref:risk:bounded-core",),
        selected_unit_refs=("risk-focused-pytest",),
        selected_test_refs=("test-ref:risk-focused",),
        audit_posture="one_final_scoped_diff_audit",
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
        shadow_mode=True,
    )
    return replace(
        plan,
        plan_fingerprint=verification_plan_contract_fingerprint(plan),
    )


def _refingerprint(plan: VerificationPlan) -> VerificationPlan:
    return replace(
        plan,
        plan_fingerprint=verification_plan_contract_fingerprint(plan),
    )


def _receipt() -> VerificationReceipt:
    return VerificationReceipt(
        schema_version="uaa_verification_receipt.v1",
        receipt_ref="receipt:risk-focused",
        plan_fingerprint=_plan().plan_fingerprint,
        unit_ref="risk-focused-pytest",
        repository_sha=SHA,
        dependency_state_fingerprint=DIGEST,
        platform_fingerprint=DIGEST,
        command_manifest_fingerprint=DIGEST,
        verifier_definition_fingerprint=DIGEST,
        test_collection_fingerprint=DIGEST,
        status=VerificationTerminalStatus.PASSED,
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:01Z",
        duration_ms=1_000,
        result_refs=("result-ref:risk-focused:passed",),
        output_byte_count=128,
        output_digest=DIGEST,
    )


def _receipt_v2(plan: VerificationPlan) -> VerificationReceipt:
    receipt = VerificationReceipt(
        schema_version="uaa_verification_receipt.v2",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        unit_ref="risk-focused-pytest",
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        status=VerificationTerminalStatus.PASSED,
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:01Z",
        duration_ms=1_000,
        result_refs=("result-ref:risk-focused:passed",),
        output_byte_count=128,
        output_digest=DIGEST,
        command_refs=("command:risk-focused",),
        command_result_bindings=(
            ("command:risk-focused", "result-ref:risk-focused:passed"),
        ),
        execution_surface_ref="surface-ref:github",
        proof_equivalence_ref="proof-equivalence-ref:risk-focused",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    return replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )


def _run_v2(
    plan: VerificationPlan, receipt: VerificationReceipt
) -> VerificationRunManifest:
    run = VerificationRunManifest(
        schema_version="uaa_verification_run.v2",
        run_ref=f"run:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        repository_sha=plan.repository_sha,
        receipt_refs=(receipt.receipt_ref,),
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:01Z",
        status=VerificationTerminalStatus.PASSED,
        run_fingerprint="0" * 64,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        execution_surface_ref="surface-ref:github",
        unit_receipt_bindings=((receipt.unit_ref, receipt.receipt_ref),),
    )
    fingerprint = verification_run_manifest_fingerprint(run)
    return replace(
        run,
        run_ref=f"run:verification:{fingerprint}",
        run_fingerprint=fingerprint,
    )


def _github_proof(
    plan: VerificationPlan, run: VerificationRunManifest
) -> VerificationGithubGateProof:
    proof = VerificationGithubGateProof(
        schema_version="uaa_verification_github_gate_proof.v1",
        proof_ref=f"proof:github:{'0' * 64}",
        repository_sha=plan.repository_sha,
        plan_fingerprint=plan.plan_fingerprint,
        run_manifest_fingerprint=run.run_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        workflow_ref="workflow:ci",
        github_run_ref="github-run:12345",
        workflow_attempt=1,
        runner_pool_ref="runner-pool:repository-scoped-macos",
        required_check_refs=("check-ref:risk-focused",),
        completed_check_refs=("check-ref:risk-focused",),
        status=VerificationTerminalStatus.PASSED,
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:02Z",
        proof_fingerprint="0" * 64,
    )
    fingerprint = verification_github_gate_proof_fingerprint(proof)
    return replace(
        proof,
        proof_ref=f"proof:github:{fingerprint}",
        proof_fingerprint=fingerprint,
    )


def _canonical_gate_units() -> tuple[VerificationUnit, ...]:
    return (
        VerificationUnit(
            unit_ref="risk-focused-pytest",
            display_name="Risk focused pytest",
            lane_ref="lane:risk-focused",
            needs=(),
            command_refs=("command:risk-focused",),
            proof_equivalence_ref="proof-equivalence-ref:risk-focused",
        ),
    )


def test_tier_zero_inert_documentation() -> None:
    selection = classify_changes((_change("docs/architecture/verification_notes.md"),))

    assert selection.tier is VerificationRiskTier.TIER_0
    assert selection.fail_closed is False
    assert selection.matched_rule_refs == ("risk-rule:inert-documentation",)
    assert selection.reason_refs == ("reason-ref:risk:documentation",)


def test_tier_one_isolated_presentation() -> None:
    selection = classify_changes((_change("apps/control-center/src/styles.css"),))

    assert selection.tier is VerificationRiskTier.TIER_1
    assert selection.fail_closed is False
    assert "surface-ref:frontend" in selection.surface_refs


def test_frontend_behavior_is_not_misclassified_as_presentation_only() -> None:
    selection = classify_changes(
        (_change("apps/control-center/src/components/VerificationCard.tsx"),)
    )

    assert selection.tier is VerificationRiskTier.TIER_2
    assert selection.fail_closed is False
    selected = unit_refs_for_selection(selection, full_unit_refs=("full-suite",))
    assert "risk-frontend-tests" in selected
    assert "risk-focused-pytest" not in selected


def test_tier_two_bounded_non_authority_core() -> None:
    selection = classify_changes(
        (_change("src/ultimate_ai_agent/core/evals/capability_metrics.py"),)
    )

    assert selection.tier is VerificationRiskTier.TIER_2
    assert selection.fail_closed is False
    assert selection.reason_refs == ("reason-ref:risk:bounded-core",)


@pytest.mark.parametrize(
    "path",
    [
        "src/ultimate_ai_agent/core/authority/contracts.py",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "src/ultimate_ai_agent/core/memory/store.py",
        "src/ultimate_ai_agent/api/founder_exact_action.py",
        "src/ultimate_ai_agent/core/autonomy/contracts.py",
        "src/ultimate_ai_agent/core/browser/gateway.py",
        "src/ultimate_ai_agent/core/plugin_execution_sandbox/__init__.py",
        "src/ultimate_ai_agent/core/secrets/contracts.py",
        "tests/test_authority_leases.py",
        "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
        "docs/capability_registry.md",
        "docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md",
    ],
)
def test_tier_three_authority_ci_dependency_and_release(path: str) -> None:
    selection = classify_changes((_change(path),))

    assert selection.tier is VerificationRiskTier.TIER_3


def test_mixed_changes_select_the_maximum_risk_tier() -> None:
    selection = classify_changes(
        (
            _change("docs/architecture/verification_notes.md"),
            _change("src/ultimate_ai_agent/core/evals/capability_metrics.py"),
        )
    )

    assert selection.tier is VerificationRiskTier.TIER_2
    assert selection.changed_path_refs == (
        "docs/architecture/verification_notes.md",
        "src/ultimate_ai_agent/core/evals/capability_metrics.py",
    )


def test_unknown_path_and_unknown_change_kind_fail_closed() -> None:
    unknown_path = classify_changes((_change("unclassified/runtime.surface"),))
    unknown_kind = classify_changes(
        (_change("docs/architecture/verification_notes.md", ChangeKind.UNKNOWN),)
    )

    assert unknown_path.tier is VerificationRiskTier.TIER_3
    assert unknown_path.fail_closed is True
    assert "reason-ref:risk:unclassified-path" in unknown_path.reason_refs
    assert unknown_kind.tier is VerificationRiskTier.TIER_3
    assert unknown_kind.fail_closed is True
    assert "reason-ref:risk:unknown" in unknown_kind.reason_refs


@pytest.mark.parametrize(
    "path",
    (
        "",
        "./README.md",
        "../README.md",
        "/tmp/README.md",
        "bad\\path.py",
        "bad\npath.py",
        "bad\u202epath.py",
        "bad//path.py",
    ),
)
def test_malformed_paths_are_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="VERIFICATION_CHANGED_PATH_INVALID"):
        classify_changes((_change(path),))


def test_malformed_rename_record_is_rejected() -> None:
    with pytest.raises(ValueError, match="VERIFICATION_CHANGE_RECORD_INVALID"):
        classify_changes(
            (ChangeRecord(ChangeKind.RENAMED, ("docs/architecture/old.md",)),)
        )


@pytest.mark.parametrize(
    ("record", "reason_ref"),
    [
        (
            ChangeRecord(ChangeKind.DELETED, ("docs/architecture/removed.md",)),
            "reason-ref:risk:deleted",
        ),
        (
            ChangeRecord(
                ChangeKind.RENAMED,
                ("docs/architecture/old.md", "docs/architecture/new.md"),
            ),
            "reason-ref:risk:renamed",
        ),
        (
            ChangeRecord(ChangeKind.TYPE_CHANGED, ("docs/architecture/changed.md",)),
            "reason-ref:risk:type-change",
        ),
    ],
    ids=("deleted", "renamed", "type-changed"),
)
def test_delete_rename_and_type_change_fail_closed(
    record: ChangeRecord, reason_ref: str
) -> None:
    selection = classify_changes((record,))

    assert selection.tier is VerificationRiskTier.TIER_3
    assert selection.fail_closed is True
    assert reason_ref in selection.reason_refs


def test_overlapping_rules_select_the_maximum_tier() -> None:
    selection = classify_changes((_change("docs/verification/policy.md"),))

    assert selection.tier is VerificationRiskTier.TIER_3
    assert selection.fail_closed is True
    assert "risk-rule:verification-ci" in selection.matched_rule_refs
    assert "risk-rule:inert-documentation" in selection.matched_rule_refs
    assert "reason-ref:risk:overlapping-rules-max-tier" in selection.reason_refs


def test_overlapping_change_records_fail_closed() -> None:
    selection = classify_changes(
        (
            _change("docs/architecture/verification_notes.md"),
            _change("docs/architecture/verification_notes.md"),
        )
    )

    assert selection.tier is VerificationRiskTier.TIER_3
    assert selection.fail_closed is True
    assert "reason-ref:risk:overlapping-change-records" in selection.reason_refs


def test_tier_three_selection_is_dependency_closed() -> None:
    selection = classify_changes(
        (_change("src/ultimate_ai_agent/core/authority/contracts.py"),)
    )
    selected = unit_refs_for_selection(
        selection,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
    )
    closed = dependency_closed_unit_refs(VERIFICATION_DAG, selected)

    assert "risk-security-audit" in closed
    assert "risk-final-diff-audit" in closed
    assert "risk-diff-check" in closed


def test_force_full_escalates_even_an_empty_or_documentation_change() -> None:
    empty = classify_changes((), force_full=True)
    documentation = classify_changes(
        (_change("docs/architecture/verification_notes.md"),), force_full=True
    )

    for selection in (empty, documentation):
        assert selection.tier is VerificationRiskTier.TIER_3
        assert selection.fail_closed is True
        assert "reason-ref:risk:force-full" in selection.reason_refs


def test_verification_dag_accepts_a_valid_dependency_graph() -> None:
    units = (
        _unit("unit:a"),
        _unit("unit:b", needs=("unit:a",)),
        _unit("unit:c", needs=("unit:a", "unit:b")),
    )

    assert validate_verification_dag(units) is None
    assert dependency_closed_unit_refs(units, ("unit:c",)) == (
        "unit:a",
        "unit:b",
        "unit:c",
    )


@pytest.mark.parametrize(
    ("units", "message"),
    [
        ((_unit("unit:a"), _unit("unit:a")), "refs must be unique"),
        ((_unit("unit:a", needs=("unit:missing",)),), "unknown dependencies"),
        ((_unit("unit:a", needs=("unit:a",)),), "self dependency"),
        (
            (
                _unit("unit:a", needs=("unit:b",)),
                _unit("unit:b", needs=("unit:a",)),
            ),
            "contain a cycle",
        ),
    ],
    ids=("duplicate", "missing", "self", "cycle"),
)
def test_verification_dag_rejects_invalid_graphs(
    units: tuple[VerificationUnit, ...], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_verification_dag(units)


def test_canonical_verification_dag_fingerprint_requires_topological_order() -> None:
    units = (
        _unit("unit:b", needs=("unit:a",)),
        _unit("unit:a"),
    )

    assert validate_verification_dag(units) is None
    with pytest.raises(ValueError, match="topologically ordered"):
        verification_dag_definition_fingerprint(units)


def test_typed_contracts_validate_with_content_free_refs_and_hashes() -> None:
    plan = _plan()
    receipt = _receipt()
    run = VerificationRunManifest(
        schema_version="uaa_verification_run.v1",
        run_ref="run:risk-focused",
        plan_fingerprint=plan.plan_fingerprint,
        repository_sha=SHA,
        receipt_refs=(receipt.receipt_ref,),
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:01Z",
        status=VerificationTerminalStatus.PASSED,
        run_fingerprint=DIGEST,
    )
    gate = VerificationGateDecision(
        schema_version="uaa_verification_gate_decision.v1",
        decision_ref="decision:risk-focused",
        repository_sha=SHA,
        plan_fingerprint=plan.plan_fingerprint,
        status=VerificationGateStatus.BLOCKED,
        required_unit_refs=(receipt.unit_ref,),
        validated_receipt_refs=(receipt.receipt_ref,),
        missing_unit_refs=(),
        reason_refs=("reason-ref:verification:shadow-plan-non-authoritative",),
        github_run_ref="github-run:pending",
        github_gate_satisfied=False,
        merge_gate_satisfied=False,
    )
    value = VerificationValueRecord(
        schema_version="uaa_verification_value.v2",
        value_ref="value:verification:" + "0" * 64,
        unit_ref=receipt.unit_ref,
        verifier_ref="verifier:risk-focused",
        synthetic_mutation_ref="mutation:risk-focused",
        defect_ref="defect:risk-focused",
        outcome="killed",
        receipt_ref="receipt:verification-value:" + "0" * 64,
        overlap_ref="overlap:none",
        disposition="retain",
        duration_ms=250,
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        probe_definition_fingerprint=DIGEST,
        detection_ref="detection:verification:killed",
        value_fingerprint="0" * 64,
    )
    value_fingerprint = verification_value_record_fingerprint(value)
    value = replace(
        value,
        value_ref=f"value:verification:{value_fingerprint}",
        receipt_ref=f"receipt:verification-value:{value_fingerprint}",
        value_fingerprint=value_fingerprint,
    )

    for contract in (_unit("unit:a"), plan, receipt, run, gate, value):
        assert contract.validate() is None
    assert len(dependency_state_fingerprint(plan)) == 64

    payloads = tuple(asdict(contract) for contract in (plan, receipt, run, gate, value))
    assert all("raw_output" not in payload for payload in payloads)


def test_dependency_state_binds_the_exact_pytest_shard_plan() -> None:
    plan = _plan()

    changed = replace(plan, pytest_shard_plan_fingerprint="c" * 64)

    assert dependency_state_fingerprint(changed) != dependency_state_fingerprint(plan)


def test_receipt_and_run_timestamp_spans_are_bounded() -> None:
    receipt = replace(
        _receipt(),
        completed_at="2026-07-17T00:00:00Z",
        duration_ms=1,
    )
    with pytest.raises(ValueError, match="duration evidence"):
        receipt.validate()

    plan = _refingerprint(replace(_plan(), shadow_mode=False))
    run = replace(
        _run_v2(plan, _receipt_v2(plan)),
        completed_at="2026-07-17T00:00:00Z",
    )
    with pytest.raises(ValueError, match="bounded duration"):
        run.validate()


def test_plan_validation_recomputes_fingerprint_and_enforces_tier_three_proof() -> None:
    unknown_schema = _refingerprint(
        replace(_plan(), schema_version="uaa_verification_plan.future")
    )
    with pytest.raises(ValueError, match="unsupported verification plan schema"):
        unknown_schema.validate()

    with pytest.raises(ValueError, match="fingerprint does not match"):
        replace(_plan(), selected_unit_refs=("unit:tampered",)).validate()

    incomplete_tier_three = _refingerprint(
        replace(
            _plan(),
            risk_tier=VerificationRiskTier.TIER_3,
            force_full=True,
            release_gate_required=True,
            full_pytest_required=False,
        )
    )
    with pytest.raises(ValueError, match="full release proof"):
        incomplete_tier_three.validate()


def test_typed_contracts_reject_unsafe_refs_and_redaction_postures() -> None:
    with pytest.raises(ValueError, match="redaction posture"):
        replace(_plan(), redaction_status="raw_payload_allowed").validate()
    with pytest.raises(ValueError, match="redaction posture"):
        replace(_receipt(), redaction_status="raw_logs_allowed").validate()
    with pytest.raises(ValueError, match="bounded safe ref"):
        replace(_unit("unit:a"), unit_ref="unsafe/path").validate()
    with pytest.raises(ValueError, match="safe repository-relative path"):
        replace(_plan(), changed_path_refs=("bad\npath.py",)).validate()
    with pytest.raises(ValueError, match="bounded safe ref"):
        VerificationRunManifest(
            schema_version="uaa_verification_run.v1",
            run_ref="/private/raw/path",
            plan_fingerprint=DIGEST,
            repository_sha=SHA,
            receipt_refs=("receipt:safe",),
            started_at="2026-07-15T00:00:00Z",
            completed_at="2026-07-15T00:00:01Z",
            status=VerificationTerminalStatus.PASSED,
            run_fingerprint=DIGEST,
        ).validate()


def test_merge_gate_cannot_pass_without_exact_github_proof() -> None:
    decision = VerificationGateDecision(
        schema_version="uaa_verification_gate_decision.v1",
        decision_ref="decision:no-github-proof",
        repository_sha=SHA,
        plan_fingerprint=DIGEST,
        status=VerificationGateStatus.PASSED,
        required_unit_refs=("unit:a",),
        validated_receipt_refs=("receipt:a",),
        missing_unit_refs=(),
        reason_refs=("reason-ref:verification:private-only",),
        github_run_ref="github-run:pending",
        github_gate_satisfied=False,
        merge_gate_satisfied=True,
    )

    with pytest.raises(ValueError, match="typed GitHub proof"):
        decision.validate()

    with pytest.raises(ValueError, match="unsupported verification gate schema"):
        replace(
            decision,
            schema_version="uaa_verification_gate_decision.v3",
            github_gate_satisfied=True,
        ).validate()


def test_gate_contract_cannot_pass_without_one_receipt_per_required_unit() -> None:
    decision = VerificationGateDecision(
        schema_version="uaa_verification_gate_decision.v1",
        decision_ref="decision:no-receipts",
        repository_sha=SHA,
        plan_fingerprint=DIGEST,
        status=VerificationGateStatus.PASSED,
        required_unit_refs=("unit:a",),
        validated_receipt_refs=(),
        missing_unit_refs=(),
        reason_refs=("reason-ref:verification:unsafe-pass",),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
        merge_gate_satisfied=True,
    )

    with pytest.raises(ValueError, match="exact receipt coverage"):
        decision.validate()


def test_gate_evaluator_requires_exact_bindings_collection_and_github_proof() -> None:
    plan = _plan()
    receipt = replace(
        _receipt(),
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
    )

    pending = evaluate_verification_gate(
        plan,
        (receipt,),
        github_run_ref="github-run:pending",
        github_gate_satisfied=False,
    )
    assert pending.status is VerificationGateStatus.BLOCKED
    assert pending.merge_gate_satisfied is False

    proof_unavailable = evaluate_verification_gate(
        plan,
        (receipt,),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )
    assert proof_unavailable.status is VerificationGateStatus.BLOCKED
    assert proof_unavailable.github_gate_satisfied is False
    assert proof_unavailable.merge_gate_satisfied is False
    assert "reason-ref:verification:shadow-plan-non-authoritative" in (
        proof_unavailable.reason_refs
    )

    non_shadow_plan = _refingerprint(replace(plan, shadow_mode=False))
    non_shadow_receipt = replace(
        receipt,
        plan_fingerprint=non_shadow_plan.plan_fingerprint,
        dependency_state_fingerprint=dependency_state_fingerprint(non_shadow_plan),
    )
    typed_proof_required = evaluate_verification_gate(
        non_shadow_plan,
        (non_shadow_receipt,),
        github_run_ref="github-run:unbound-boolean",
        github_gate_satisfied=True,
    )
    assert typed_proof_required.status is VerificationGateStatus.BLOCKED
    assert typed_proof_required.github_gate_satisfied is False
    assert typed_proof_required.merge_gate_satisfied is False
    assert "reason-ref:verification:typed-github-proof-unavailable" in (
        typed_proof_required.reason_refs
    )

    changed_receipt = replace(receipt, repository_sha="c" * 40)
    denied = evaluate_verification_gate(
        plan,
        (changed_receipt,),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )
    assert denied.status is VerificationGateStatus.DENIED
    assert denied.missing_unit_refs == ("risk-focused-pytest",)


def test_v2_gate_keeps_structural_github_proof_nonauthoritative() -> None:
    plan = _refingerprint(replace(_plan(), shadow_mode=False))
    receipt = _receipt_v2(plan)
    run = _run_v2(plan, receipt)
    proof = _github_proof(plan, run)

    decision = evaluate_verification_gate_v2(
        plan,
        (receipt,),
        canonical_units=_canonical_gate_units(),
        run_manifest=run,
        github_proof=proof,
    )

    assert decision.status is VerificationGateStatus.BLOCKED
    assert decision.github_gate_satisfied is False
    assert decision.merge_gate_satisfied is False
    assert decision.github_proof_ref == proof.proof_ref
    assert decision.run_manifest_ref == run.run_ref
    assert decision.reason_refs == (
        "reason-ref:verification:trusted-github-attestation-unavailable",
    )
    with pytest.raises(ValueError, match="decision ref is not content bound"):
        replace(
            decision,
            reason_refs=("reason-ref:verification:tampered",),
        ).validate()


def test_legacy_v2_fingerprints_and_wire_shapes_remain_byte_stable() -> None:
    plan = _refingerprint(replace(_plan(), shadow_mode=False))
    receipt = _receipt_v2(plan)
    run = _run_v2(plan, receipt)

    assert plan.plan_fingerprint == (
        "f2dcc848661cb9026d48c2e253e124f7975d84a2963ad50d439b6a1be44792db"
    )
    assert receipt.receipt_fingerprint == (
        "f8e23c5ad48ddfa1c684d7311a29a794ddfd1d9938b38f812219079de0b4b330"
    )
    assert run.run_fingerprint == (
        "96520d233a2242d7da86edafabe845d8c87b6a4f674e2876dd3a40e443c85768"
    )
    payloads_and_expected_bytes = (
        (
            verification_plan_payload(plan),
            2_072,
            "6245f6ec0693307751cf514536b6c00985688c104c30b6672ca949d2c5069df8",
        ),
        (
            verification_receipt_payload(receipt),
            1_766,
            "6db66a34fc41ff1a9924004abc9afe3353aa7684c543c097a8427a9968b9f296",
        ),
        (
            verification_run_manifest_payload(run),
            1_017,
            "268a065400820735737518c28921b0625067b1675ff6b65ebecd90c4f6413eda",
        ),
    )
    for payload, expected_size, expected_digest in payloads_and_expected_bytes:
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        assert len(encoded) == expected_size
        assert hashlib.sha256(encoded).hexdigest() == expected_digest


def test_v2_gate_rejects_changed_sha_and_unbound_receipt_payloads() -> None:
    plan = _refingerprint(replace(_plan(), shadow_mode=False))
    receipt = _receipt_v2(plan)
    run = _run_v2(plan, receipt)
    proof = _github_proof(plan, run)

    tampered_receipt = replace(receipt, output_byte_count=129)
    denied = evaluate_verification_gate_v2(
        plan,
        (tampered_receipt,),
        canonical_units=_canonical_gate_units(),
        run_manifest=run,
        github_proof=proof,
    )
    assert denied.status is VerificationGateStatus.DENIED
    assert denied.merge_gate_satisfied is False

    wrong_command = replace(
        receipt,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        command_refs=("command:other",),
        command_result_bindings=(
            ("command:other", "result-ref:risk-focused:passed"),
        ),
        receipt_fingerprint="0" * 64,
    )
    wrong_fingerprint = verification_receipt_fingerprint(wrong_command)
    wrong_command = replace(
        wrong_command,
        receipt_ref=f"receipt:verification:{wrong_fingerprint}",
        receipt_fingerprint=wrong_fingerprint,
    )
    wrong_run = _run_v2(plan, wrong_command)
    wrong_proof = _github_proof(plan, wrong_run)
    command_denied = evaluate_verification_gate_v2(
        plan,
        (wrong_command,),
        canonical_units=_canonical_gate_units(),
        run_manifest=wrong_run,
        github_proof=wrong_proof,
    )
    assert command_denied.status is VerificationGateStatus.DENIED

    changed_proof = replace(proof, repository_sha="c" * 40)
    changed_sha = evaluate_verification_gate_v2(
        plan,
        (receipt,),
        canonical_units=_canonical_gate_units(),
        run_manifest=run,
        github_proof=changed_proof,
    )
    assert changed_sha.status is VerificationGateStatus.DENIED
    assert changed_sha.merge_gate_satisfied is False


def test_v2_test_receipt_cannot_pass_with_inventory_only_collection() -> None:
    receipt = replace(
        _receipt_v2(_refingerprint(replace(_plan(), shadow_mode=False))),
        command_refs=("command:pytest.focused",),
        command_result_bindings=(
            ("command:pytest.focused", "result-ref:risk-focused:passed"),
        ),
    )

    with pytest.raises(ValueError, match="observed collection proof"):
        receipt.validate()
    with pytest.raises(ValueError, match="command results are not exactly bound"):
        replace(
            _receipt_v2(_refingerprint(replace(_plan(), shadow_mode=False))),
            command_result_bindings=(),
        ).validate()

    plan = _plan()
    receipt = replace(
        _receipt(),
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
    )
    inventory_only = _refingerprint(
        replace(
            plan,
            selected_command_refs=("command:pytest.focused",),
        )
    )
    collection_denied = evaluate_verification_gate(
        inventory_only,
        (
            replace(
                receipt,
                plan_fingerprint=inventory_only.plan_fingerprint,
                dependency_state_fingerprint=dependency_state_fingerprint(
                    inventory_only
                ),
            ),
        ),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )
    assert collection_denied.status is VerificationGateStatus.DENIED
    assert "reason-ref:verification:test-collection-unverified" in (
        collection_denied.reason_refs
    )

    frontend_inventory_only = _refingerprint(
        replace(
            plan,
            selected_command_refs=("command:frontend.unit-tests",),
        )
    )
    frontend_denied = evaluate_verification_gate(
        frontend_inventory_only,
        (
            replace(
                receipt,
                plan_fingerprint=frontend_inventory_only.plan_fingerprint,
                dependency_state_fingerprint=dependency_state_fingerprint(
                    frontend_inventory_only
                ),
            ),
        ),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )
    assert frontend_denied.status is VerificationGateStatus.DENIED
    assert "reason-ref:verification:test-collection-unverified" in (
        frontend_denied.reason_refs
    )


def test_gate_evaluator_denies_malformed_receipt_refs_without_propagating_them() -> None:
    plan = _plan()
    malformed = replace(_receipt(), unit_ref="unsafe/path")

    decision = evaluate_verification_gate(
        plan,
        (malformed,),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )

    assert decision.status is VerificationGateStatus.DENIED
    assert decision.missing_unit_refs == plan.selected_unit_refs
    assert "unsafe/path" not in decision.missing_unit_refs
    assert "reason-ref:verification:invalid-receipt-binding" in decision.reason_refs


def test_gate_evaluator_denies_non_string_receipt_refs_without_crashing() -> None:
    plan = _plan()
    malformed = replace(_receipt(), unit_ref=None)  # type: ignore[arg-type]

    decision = evaluate_verification_gate(
        plan,
        (malformed,),
        github_run_ref="github-run:12345",
        github_gate_satisfied=True,
    )

    assert decision.status is VerificationGateStatus.DENIED
    assert decision.missing_unit_refs == plan.selected_unit_refs


def test_passed_receipt_requires_content_free_result_evidence() -> None:
    with pytest.raises(ValueError, match="requires result evidence"):
        replace(_receipt(), result_refs=()).validate()


def test_risk_architecture_does_not_require_size_or_complexity_refactors() -> None:
    payload = risk_definition_payload()

    assert payload["line_count_or_complexity_refactor_required"] is False
    assert "maximum_file_lines" not in payload
    assert "complexity_threshold" not in payload
