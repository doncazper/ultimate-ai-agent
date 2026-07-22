from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import scripts.verification.verification_github_prerequisites as prerequisites
import scripts.verification.run_ci_lane as lane_runner
import scripts.verification.verify_ci_evidence_dag as evidence_dag
from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    optional_nonexecution_reason_ref,
    optional_nonexecution_result_ref,
)
from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationReceipt,
    VerificationRiskTier,
    VerificationTerminalStatus,
    TEST_EXECUTION_COMMAND_REFS,
    TYPESCRIPT_EXECUTION_COMMAND_REFS,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_dag_definition_fingerprint,
    verification_plan_contract_fingerprint,
    verification_receipt_fingerprint,
    verification_run_manifest_fingerprint,
    verification_unit_definition_fingerprint,
)
from scripts.verification.verification_execution_identity import (
    build_verification_execution_identity,
)
from scripts.verification.verification_github_prerequisites import (
    PREREQUISITE_CHAIN_UNIT_REFS,
    PREREQUISITE_SOURCE_UNIT_REFS,
    PYTEST_AGGREGATE_SOURCE_UNIT_REFS,
    VerificationGithubPrerequisiteError,
    append_github_output,
    collect_pytest_aggregate,
    collect_foundation_prerequisites,
    encode_foundation_prerequisite_manifest,
    load_foundation_prerequisite_manifest,
    main,
    parse_foundation_prerequisite_evidence,
    parse_foundation_prerequisite_manifest,
)
from scripts.verification.verification_github_transport import (
    build_github_job_output_envelope,
    decode_github_job_output,
    encode_github_job_output,
)
from scripts.verification.typescript_binding import TypeScriptBindingError


def test_prerequisite_builder_is_standalone_workflow_command() -> None:
    completed = subprocess.run(
        (sys.executable, str(Path(prerequisites.__file__)), "--help"),
        cwd=Path(prerequisites.__file__).resolve().parents[2],
        env={**os.environ, "PYTHONPATH": ""},
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0
    assert "foundation-manifest" in completed.stdout


SHA = "a" * 40
DIGEST = "b" * 64
SURFACE = "surface-ref:github"
UNITS_BY_REF = {unit.unit_ref: unit for unit in VERIFICATION_DAG}


@pytest.fixture(autouse=True)
def _canonical_terminal_typescript_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        evidence_dag,
        "_resolve_canonical_typescript_runtime",
        lambda *_args: (DIGEST, "typescript-version-ref:test"),
    )


TIMES = {
    "manifest-attestation": ("2026-07-15T00:00:00Z", "2026-07-15T00:00:01Z"),
    "lint": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "affected-preflight": (
        "2026-07-15T00:00:01Z",
        "2026-07-15T00:00:02Z",
    ),
    "release-lane-docs": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-openapi": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-api-safety": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-security-redaction": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-product-truth": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-local-model-e2e": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "release-lane-durability": ("2026-07-15T00:00:01Z", "2026-07-15T00:00:02Z"),
    "pytest-shards": ("2026-07-15T00:00:02Z", "2026-07-15T00:00:03Z"),
    "static-verification": (
        "2026-07-15T00:00:03Z",
        "2026-07-15T00:00:04Z",
    ),
    "control-center-frontend": (
        "2026-07-15T00:00:03Z",
        "2026-07-15T00:00:04Z",
    ),
    "release-lane-desktop-packaging": (
        "2026-07-15T00:00:04Z",
        "2026-07-15T00:00:05Z",
    ),
    "release-lane-frontend": (
        "2026-07-15T00:00:04Z",
        "2026-07-15T00:00:05Z",
    ),
    "release-lane-visual-regression": (
        "2026-07-15T00:00:04Z",
        "2026-07-15T00:00:05Z",
    ),
    "release-lane-performance": (
        "2026-07-15T00:00:05Z",
        "2026-07-15T00:00:06Z",
    ),
    "foundation-gate-report": (
        "2026-07-15T00:00:06Z",
        "2026-07-15T00:00:07Z",
    ),
}


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _plan(
    *,
    repository_sha: str = SHA,
    base_sha: str | None = None,
    selected_unit_refs: tuple[str, ...] | None = None,
    change_fingerprint: str = DIGEST,
    schema_version: str = "uaa_verification_plan.v3",
    frontend_visual_scope: str = "affected",
) -> VerificationPlan:
    selected = selected_unit_refs or tuple(unit.unit_ref for unit in CI_JOB_GRAPH)
    selected_units = tuple(UNITS_BY_REF[unit_ref] for unit_ref in selected)
    selected_resources = {
        resource_ref
        for unit in selected_units
        for resource_ref in unit.exclusive_resource_refs
    }
    plan = VerificationPlan(
        schema_version=schema_version,
        profile_ref="profile:github-full",
        repository_sha=repository_sha,
        definition_fingerprint=DIGEST,
        dependency_lock_fingerprints=(("uv.lock", DIGEST),),
        affected_path_classification="risk:tier_3",
        selected_lane_refs=_unique(
            tuple(unit.lane_ref for unit in selected_units if unit.lane_ref is not None)
        ),
        selected_command_refs=_unique(
            tuple(
                command_ref
                for unit in selected_units
                for command_ref in unit.command_refs
            )
        ),
        pytest_shard_plan_fingerprint=DIGEST,
        frontend_visual_scope=frontend_visual_scope,
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        plan_fingerprint="0" * 64,
        base_sha=base_sha or repository_sha,
        risk_manifest_version="uaa_verification_risk_manifest.v1",
        risk_manifest_fingerprint=DIGEST,
        risk_tier=VerificationRiskTier.TIER_3,
        changed_path_refs=("scripts/verification/example.py",),
        change_fingerprint=change_fingerprint,
        escalation_reason_refs=("reason-ref:risk:tier-3",),
        selected_unit_refs=selected,
        selected_test_refs=(),
        audit_posture="security_and_final_diff_audits_required",
        full_pytest_required=True,
        typescript_typecheck_required=(
            "resource-ref:typescript-typecheck" in selected_resources
        ),
        release_gate_required=True,
        platform_fingerprint=DIGEST,
        command_manifest_fingerprint=DIGEST,
        verifier_definition_fingerprint=DIGEST,
        test_collection_fingerprint=DIGEST,
        test_collection_posture="inventory_bound",
        typescript_project_fingerprint=DIGEST,
        typescript_project_posture=(
            "project_bound"
            if "resource-ref:typescript-typecheck" in selected_resources
            else "not_applicable"
        ),
        force_full=True,
        shadow_mode=False,
        verification_dag_fingerprint=verification_dag_definition_fingerprint(
            VERIFICATION_DAG
        ),
        selected_unit_definition_fingerprints=tuple(
            (unit.unit_ref, verification_unit_definition_fingerprint(unit))
            for unit in selected_units
        ),
    )
    return replace(plan, plan_fingerprint=verification_plan_contract_fingerprint(plan))


def _receipt(
    plan: VerificationPlan,
    unit_ref: str,
    *,
    status: VerificationTerminalStatus = VerificationTerminalStatus.PASSED,
    started_at: str | None = None,
    completed_at: str | None = None,
    typescript_runtime_fingerprint: str = DIGEST,
    typescript_version_ref: str = "typescript-version-ref:test",
    reused_command_receipt_bindings: tuple[tuple[str, str], ...] = (),
    nonexecuted_command_refs: tuple[str, ...] = (),
    output_digest: str = DIGEST,
) -> VerificationReceipt:
    unit = UNITS_BY_REF[unit_ref]
    default_started, default_completed = TIMES[unit_ref]
    reused_by_command = dict(reused_command_receipt_bindings)
    executed_command_refs = tuple(
        command_ref
        for command_ref in unit.command_refs
        if command_ref not in reused_by_command
        and command_ref not in set(nonexecuted_command_refs)
    )
    executed_result_refs = tuple(
        f"result-ref:verification:{hashlib.sha256(f'{unit_ref}:{command_ref}'.encode()).hexdigest()}"
        for command_ref in executed_command_refs
    )
    executed_bindings = tuple(
        zip(executed_command_refs, executed_result_refs, strict=True)
    )
    executed_by_command = dict(executed_bindings)
    nonexecuted_bindings = tuple(
        (
            command_ref,
            optional_nonexecution_result_ref(
                plan.repository_sha,
                command_ref,
                reason_ref,
            ),
            reason_ref,
        )
        for command_ref in nonexecuted_command_refs
        for reason_ref in (
            optional_nonexecution_reason_ref(
                command_ref,
                frontend_visual_scope=plan.frontend_visual_scope,
            )
            or "reason-ref:test:declared-nonexecution",
        )
    )
    nonexecuted_by_command = {
        command_ref: result_ref
        for command_ref, result_ref, _reason_ref in nonexecuted_bindings
    }
    result_refs = tuple(
        (
            reused_by_command[command_ref]
            if command_ref in reused_by_command
            else nonexecuted_by_command[command_ref]
            if command_ref in nonexecuted_by_command
            else executed_by_command[command_ref]
        )
        for command_ref in unit.command_refs
    )
    evidenced_command_refs = (*executed_command_refs, *reused_by_command)
    typescript_execution = bool(
        set(evidenced_command_refs).intersection(TYPESCRIPT_EXECUTION_COMMAND_REFS)
    )
    collected = any(
        command_ref.startswith("command:pytest.")
        or command_ref in TEST_EXECUTION_COMMAND_REFS
        for command_ref in evidenced_command_refs
    )
    receipt = VerificationReceipt(
        schema_version="uaa_verification_receipt.v3",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        unit_ref=unit_ref,
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        status=status,
        started_at=started_at or default_started,
        completed_at=completed_at or default_completed,
        duration_ms=1_000,
        result_refs=result_refs,
        output_byte_count=0,
        output_digest=output_digest,
        command_refs=unit.command_refs,
        command_result_bindings=executed_bindings,
        execution_surface_ref=SURFACE,
        proof_equivalence_ref=unit.proof_equivalence_ref,
        test_collection_posture="collected" if collected else "not_applicable",
        observed_test_collection_fingerprint=DIGEST if collected else None,
        observed_test_count=1 if collected else 0,
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        execution_identity_ref=build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref=SURFACE,
            typescript_runtime_fingerprint=(
                typescript_runtime_fingerprint if typescript_execution else None
            ),
            typescript_version_ref=(
                typescript_version_ref if typescript_execution else None
            ),
        ).identity_ref,
        executed_command_result_bindings=executed_bindings,
        nonexecuted_command_result_bindings=nonexecuted_bindings,
        reused_command_receipt_bindings=reused_command_receipt_bindings,
        typescript_binding_posture=(
            "resolved" if typescript_execution else "not_applicable"
        ),
        typescript_project_fingerprint=(
            plan.typescript_project_fingerprint if typescript_execution else None
        ),
        typescript_runtime_fingerprint=(
            typescript_runtime_fingerprint if typescript_execution else None
        ),
        typescript_version_ref=(
            typescript_version_ref if typescript_execution else None
        ),
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    return replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )


def _encoded(plan: VerificationPlan, unit_ref: str, **receipt_kwargs: object) -> str:
    receipt = _receipt(plan, unit_ref, **receipt_kwargs)
    return encode_github_job_output(build_github_job_output_envelope(plan, receipt))


def _envelopes(plan: VerificationPlan) -> tuple[str, ...]:
    return tuple(_encoded(plan, unit_ref) for unit_ref in PREREQUISITE_SOURCE_UNIT_REFS)


def _assert_reason(callable_: object, reason_ref: str) -> None:
    with pytest.raises(VerificationGithubPrerequisiteError) as error:
        callable_()
    assert error.value.reason_ref == reason_ref


def test_exact_chain_derives_pytest_but_preserves_full_plan_blocked_truth() -> None:
    plan = _plan()
    result = collect_foundation_prerequisites(plan, tuple(reversed(_envelopes(plan))))

    assert result.manifest.prerequisite_unit_refs == PREREQUISITE_CHAIN_UNIT_REFS
    assert tuple(receipt.unit_ref for receipt in result.derived_receipts) == ("pytest",)
    assert result.run_manifest.status is VerificationTerminalStatus.BLOCKED
    assert result.manifest.run_status == "blocked"
    assert result.manifest.missing_full_plan_unit_refs
    assert "control-center-frontend" in result.manifest.missing_full_plan_unit_refs
    assert result.manifest.reason_refs == (
        "reason-ref:verification:whole-run-incomplete",
    )
    assert result.manifest.run_manifest_ref == result.run_manifest.run_ref
    encoded = encode_foundation_prerequisite_manifest(result.manifest)
    assert parse_foundation_prerequisite_manifest(encoded) == result.manifest
    assert not {
        "authorized",
        "github_gate_satisfied",
        "merge_allowed",
        "merge_gate_satisfied",
    } & set(json.loads(encoded))


def test_canonical_ci_manifest_v3_plan_is_supported() -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")

    result = collect_foundation_prerequisites(plan, _envelopes(plan))

    assert result.manifest.plan_fingerprint == plan.plan_fingerprint


def test_missing_duplicate_and_extra_envelopes_fail_closed() -> None:
    plan = _plan()
    envelopes = _envelopes(plan)
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, envelopes[:-1]),
        "reason-ref:github-prerequisite:envelope-count-invalid",
    )
    _assert_reason(
        lambda: collect_foundation_prerequisites(
            plan,
            (*envelopes[:-1], envelopes[0]),
        ),
        "reason-ref:github-prerequisite:duplicate-evidence",
    )
    _assert_reason(
        lambda: collect_foundation_prerequisites(
            plan,
            (*envelopes[:-1], _encoded(plan, "release-lane-performance")),
        ),
        "reason-ref:github-prerequisite:extra-evidence",
    )


def test_cross_sha_and_cross_plan_evidence_are_rejected() -> None:
    plan = _plan()
    envelopes = list(_envelopes(plan))
    other = _plan(repository_sha="c" * 40)
    envelopes[0] = _encoded(other, "manifest-attestation")
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:envelope-invalid",
    )

    envelopes = list(_envelopes(plan))
    changed_base_plan = _plan(base_sha="c" * 40)
    _assert_reason(
        lambda: collect_foundation_prerequisites(
            changed_base_plan,
            tuple(envelopes),
        ),
        "reason-ref:github-prerequisite:envelope-invalid",
    )

    envelopes = list(_envelopes(plan))
    other = _plan(change_fingerprint="c" * 64)
    envelopes[0] = _encoded(other, "manifest-attestation")
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:envelope-invalid",
    )


def test_malformed_nonpassing_and_dependency_impossible_evidence_are_rejected() -> None:
    plan = _plan()
    envelopes = list(_envelopes(plan))
    envelopes[0] = "not-an-envelope"
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:envelope-invalid",
    )

    envelopes = list(_envelopes(plan))
    envelopes[1] = _encoded(
        plan,
        "lint",
        status=VerificationTerminalStatus.FAILED,
    )
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:nonpassing-evidence",
    )

    envelopes = list(_envelopes(plan))
    envelopes[-1] = _encoded(
        plan,
        "static-verification",
        started_at="2026-07-15T00:00:02Z",
        completed_at="2026-07-15T00:00:03Z",
    )
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:aggregate-invalid",
    )


def test_job_envelopes_cannot_smuggle_a_final_run() -> None:
    plan = _plan()
    result = collect_foundation_prerequisites(plan, _envelopes(plan))
    receipt = _receipt(plan, "manifest-attestation")
    with_run = encode_github_job_output(
        build_github_job_output_envelope(
            plan,
            receipt,
            final_run_manifest=result.run_manifest,
        )
    )
    envelopes = list(_envelopes(plan))
    envelopes[0] = with_run
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, tuple(envelopes)),
        "reason-ref:github-prerequisite:extra-evidence",
    )


def test_plan_without_exact_prerequisite_chain_is_rejected() -> None:
    selected = tuple(
        unit.unit_ref for unit in CI_JOB_GRAPH if unit.unit_ref != "static-verification"
    )
    plan = _plan(selected_unit_refs=selected)
    _assert_reason(
        lambda: collect_foundation_prerequisites(plan, ()),
        "reason-ref:github-prerequisite:plan-chain-missing",
    )


def test_manifest_parser_rejects_gate_claims_unknowns_duplicates_and_drift() -> None:
    plan = _plan()
    result = collect_foundation_prerequisites(plan, _envelopes(plan))
    encoded = encode_foundation_prerequisite_manifest(result.manifest)
    payload = json.loads(encoded)

    payload["merge_allowed"] = True
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(
            json.dumps(payload, separators=(",", ":"), sort_keys=True)
        ),
        "reason-ref:github-prerequisite:gate-claim-forbidden",
    )

    payload = json.loads(encoded)
    payload["unknown_ref"] = "safe-ref:unknown"
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(
            json.dumps(payload, separators=(",", ":"), sort_keys=True)
        ),
        "reason-ref:github-prerequisite:manifest-fields-invalid",
    )

    duplicated = (
        encoded[:-1] + ',"schema_version":"uaa_foundation_prerequisite_manifest.v1"}'
    )
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(duplicated),
        "reason-ref:github-prerequisite:json-duplicate-field",
    )

    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(" " + encoded),
        "reason-ref:github-prerequisite:json-not-canonical",
    )

    payload = json.loads(encoded)
    payload["content_fingerprint"] = "c" * 64
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(
            json.dumps(payload, separators=(",", ":"), sort_keys=True)
        ),
        "reason-ref:github-prerequisite:content-fingerprint-mismatch",
    )

    payload = json.loads(encoded)
    payload["frontend_visual_scope"] = "unknown_fail_closed"
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(
            json.dumps(payload, separators=(",", ":"), sort_keys=True)
        ),
        "reason-ref:github-prerequisite:visual-scope-invalid",
    )


def test_manifest_parser_rejects_malformed_shapes_and_nonfinite_numbers() -> None:
    plan = _plan()
    result = collect_foundation_prerequisites(plan, _envelopes(plan))
    payload = json.loads(encode_foundation_prerequisite_manifest(result.manifest))
    payload["reason_refs"] = "reason-ref:not-a-list"
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest(
            json.dumps(payload, separators=(",", ":"), sort_keys=True)
        ),
        "reason-ref:github-prerequisite:manifest-shape-invalid",
    )
    _assert_reason(
        lambda: parse_foundation_prerequisite_manifest('{"value":NaN}'),
        "reason-ref:github-prerequisite:json-number-nonfinite",
    )


def test_errors_never_reflect_untrusted_envelope_or_manifest_content() -> None:
    unsafe = "raw-private-value-that-must-not-be-reflected"
    with pytest.raises(VerificationGithubPrerequisiteError) as envelope_error:
        collect_foundation_prerequisites(_plan(), (unsafe,) * 5)
    assert unsafe not in str(envelope_error.value)

    with pytest.raises(VerificationGithubPrerequisiteError) as manifest_error:
        parse_foundation_prerequisite_manifest(unsafe)
    assert unsafe not in str(manifest_error.value)


def _cli_envelope_args(
    plan: VerificationPlan,
    unit_refs: tuple[str, ...] = PREREQUISITE_SOURCE_UNIT_REFS,
) -> list[str]:
    return [
        argument
        for unit_ref in unit_refs
        for argument in ("--envelope", _encoded(plan, unit_ref))
    ]


def test_cli_aggregate_writes_one_owner_safe_github_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    monkeypatch.setattr(
        prerequisites,
        "_reconstruct_plan",
        lambda _repo, _sha, _base_sha, _visual_scope: plan,
    )
    github_output = tmp_path / "github-output"
    github_output.write_bytes(b"")
    github_output.chmod(0o600)

    exit_code = main(
        [
            "aggregate",
            "--repo",
            ".",
            "--sha",
            SHA,
            "--base-sha",
            plan.base_sha,
            *_cli_envelope_args(plan, PYTEST_AGGREGATE_SOURCE_UNIT_REFS),
            "--github-output-file",
            str(github_output),
        ]
    )

    assert exit_code == 0
    key, value = github_output.read_text(encoding="ascii").strip().split("=", 1)
    assert key == "verification_envelope"
    envelope = decode_github_job_output(value)
    assert envelope.receipt.unit_ref == "pytest"
    assert envelope.final_run_manifest is not None
    assert envelope.final_run_manifest.status is VerificationTerminalStatus.BLOCKED
    assert oct(github_output.stat().st_mode & 0o777) == "0o600"


def test_cli_foundation_manifest_and_loader_bind_the_exact_local_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(
        schema_version="uaa_ci_command_manifest.v3",
        base_sha="d" * 40,
    )
    observed_reconstruction: list[tuple[str, str]] = []

    def reconstruct(
        _repo: Path,
        _sha: str,
        base_sha: str,
        visual_scope: str,
    ) -> VerificationPlan:
        observed_reconstruction.append((base_sha, visual_scope))
        return plan

    monkeypatch.setattr(
        prerequisites,
        "_reconstruct_plan",
        reconstruct,
    )
    monkeypatch.setenv("UAA_VERIFICATION_BASE_SHA", plan.base_sha)
    monkeypatch.setenv("UAA_VERIFICATION_VISUAL_SCOPE", "not_affected")
    output = tmp_path / "foundation.json"

    exit_code = main(
        [
            "foundation-manifest",
            "--repo",
            ".",
            "--sha",
            SHA,
            "--base-sha",
            plan.base_sha,
            "--visual-scope",
            plan.frontend_visual_scope,
            *_cli_envelope_args(plan),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert oct(output.stat().st_mode & 0o777) == "0o600"
    loaded = load_foundation_prerequisite_manifest(output, Path("."), SHA)
    evidence = parse_foundation_prerequisite_evidence(
        output.read_text(encoding="ascii")
    )
    assert loaded == evidence.manifest
    assert loaded.frontend_visual_scope == plan.frontend_visual_scope
    assert observed_reconstruction[:2] == [
        (plan.base_sha, plan.frontend_visual_scope),
        (plan.base_sha, plan.frontend_visual_scope),
    ]

    with pytest.raises(VerificationGithubPrerequisiteError) as mismatch:
        load_foundation_prerequisite_manifest(output, Path("."), "c" * 40)
    assert mismatch.value.reason_ref == (
        "reason-ref:github-prerequisite:manifest-plan-mismatch"
    )

    standalone = tmp_path / "standalone.json"
    standalone.write_text(
        encode_foundation_prerequisite_manifest(loaded),
        encoding="ascii",
    )
    standalone.chmod(0o600)
    with pytest.raises(VerificationGithubPrerequisiteError) as incomplete:
        load_foundation_prerequisite_manifest(standalone, Path("."), SHA)
    assert incomplete.value.reason_ref == (
        "reason-ref:github-prerequisite:manifest-file-invalid"
    )


def test_loader_recomputes_receipts_instead_of_trusting_content_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    monkeypatch.setattr(
        prerequisites,
        "_reconstruct_plan",
        lambda _repo, _sha, _base_sha, _visual_scope: plan,
    )
    output = tmp_path / "foundation.json"
    assert (
        main(
            [
                "foundation-manifest",
                "--repo",
                ".",
                "--sha",
                SHA,
                "--base-sha",
                plan.base_sha,
                "--visual-scope",
                plan.frontend_visual_scope,
                *_cli_envelope_args(plan),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text(encoding="ascii"))
    alternate_receipt = _receipt(plan, "manifest-attestation")
    alternate_receipt = replace(
        alternate_receipt,
        output_digest="c" * 64,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(alternate_receipt)
    alternate_receipt = replace(
        alternate_receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    alternate_envelope = build_github_job_output_envelope(plan, alternate_receipt)
    payload["source_envelopes"][0] = encode_github_job_output(alternate_envelope)
    payload["manifest"]["source_envelope_refs"][0] = alternate_envelope.content_ref
    payload["manifest"]["prerequisite_receipt_refs"][0] = alternate_receipt.receipt_ref
    manifest_unsigned = {
        key: value
        for key, value in payload["manifest"].items()
        if key not in {"content_fingerprint", "content_ref"}
    }
    manifest_fingerprint = hashlib.sha256(
        json.dumps(manifest_unsigned, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    payload["manifest"]["content_fingerprint"] = manifest_fingerprint
    payload["manifest"]["content_ref"] = (
        f"foundation-prerequisite:{manifest_fingerprint}"
    )
    evidence_unsigned = {
        key: value
        for key, value in payload.items()
        if key not in {"content_fingerprint", "content_ref"}
    }
    evidence_fingerprint = hashlib.sha256(
        json.dumps(evidence_unsigned, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    payload["content_fingerprint"] = evidence_fingerprint
    payload["content_ref"] = f"foundation-prerequisite-evidence:{evidence_fingerprint}"
    output.write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True),
        encoding="ascii",
    )
    output.chmod(0o600)

    with pytest.raises(VerificationGithubPrerequisiteError) as error:
        load_foundation_prerequisite_manifest(output, Path("."), SHA)
    assert error.value.reason_ref == (
        "reason-ref:github-prerequisite:manifest-recomputation-mismatch"
    )


def test_cli_owner_safe_outputs_reject_symlinks_and_unsafe_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    monkeypatch.setattr(
        prerequisites,
        "_reconstruct_plan",
        lambda _repo, _sha, _base_sha, _visual_scope: plan,
    )
    target = tmp_path / "target"
    target.write_text("unchanged", encoding="ascii")
    target.chmod(0o600)
    symlink = tmp_path / "github-output"
    symlink.symlink_to(target)

    exit_code = main(
        [
            "aggregate",
            "--repo",
            ".",
            "--sha",
            SHA,
            "--base-sha",
            plan.base_sha,
            *_cli_envelope_args(plan, PYTEST_AGGREGATE_SOURCE_UNIT_REFS),
            "--github-output-file",
            str(symlink),
        ]
    )

    assert exit_code == 2
    assert target.read_text(encoding="ascii") == "unchanged"
    assert str(symlink) not in capsys.readouterr().err

    unsafe = tmp_path / "unsafe.json"
    unsafe.write_text("{}", encoding="ascii")
    unsafe.chmod(0o666)
    with pytest.raises(VerificationGithubPrerequisiteError) as error:
        load_foundation_prerequisite_manifest(unsafe, Path("."), SHA)
    assert error.value.reason_ref == "reason-ref:github-prerequisite:output-file-unsafe"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO required")
def test_manifest_loader_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "foundation.fifo"
    os.mkfifo(fifo, 0o600)

    with pytest.raises(VerificationGithubPrerequisiteError) as error:
        load_foundation_prerequisite_manifest(fifo, Path("."), SHA)

    assert error.value.reason_ref == "reason-ref:github-prerequisite:output-file-unsafe"


def test_github_output_append_is_bounded_and_preserves_existing_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    monkeypatch.setattr(
        prerequisites,
        "_reconstruct_plan",
        lambda _repo, _sha, _base_sha, _visual_scope: plan,
    )
    github_output = tmp_path / "github-output"
    github_output.write_text("prior=value\n", encoding="ascii")
    github_output.chmod(0o600)

    assert (
        main(
            [
                "aggregate",
                "--repo",
                ".",
                "--sha",
                SHA,
                "--base-sha",
                plan.base_sha,
                *_cli_envelope_args(plan, PYTEST_AGGREGATE_SOURCE_UNIT_REFS),
                "--github-output-file",
                str(github_output),
            ]
        )
        == 0
    )
    assert github_output.read_text(encoding="ascii").startswith("prior=value\n")
    assert os.path.getsize(github_output) < prerequisites.MAX_GITHUB_OUTPUT_BYTES


def _final_gate_bindings(
    plan: VerificationPlan,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    upstream = tuple(
        unit for unit in CI_JOB_GRAPH if unit.unit_ref != "foundation-gate-report"
    )
    aggregate = collect_pytest_aggregate(
        plan,
        tuple(_encoded(plan, unit_ref) for unit_ref in PYTEST_AGGREGATE_SOURCE_UNIT_REFS),
    )
    aggregate_envelope = encode_github_job_output(
        build_github_job_output_envelope(
            plan,
            aggregate.receipt,
            final_run_manifest=aggregate.run_manifest,
        )
    )
    frontend_source_ref = _receipt(plan, "control-center-frontend").receipt_ref
    envelopes = tuple(
        f"{unit.unit_ref}="
        + (
            aggregate_envelope
            if unit.unit_ref == "pytest"
            else _encoded(
                plan,
                unit.unit_ref,
                **(
                    {
                        "reused_command_receipt_bindings": (
                            ("command:frontend.check", frontend_source_ref),
                        )
                    }
                    if unit.unit_ref == "release-lane-frontend"
                    else {"status": VerificationTerminalStatus.BLOCKED}
                    if unit.evidence_posture == "typed_optional"
                    else {}
                ),
            )
        )
        for unit in upstream
        if unit.evidence_posture != "typed_optional"
    )
    results = tuple(f"{unit.unit_ref}=success" for unit in upstream)
    return results, envelopes


def _final_optional_bindings(plan: VerificationPlan) -> tuple[str, str]:
    desktop = _encoded(
        plan,
        "release-lane-desktop-packaging",
        status=VerificationTerminalStatus.BLOCKED,
        nonexecuted_command_refs=("command:desktop-packaging.proof",),
    )
    visual = _encoded(
        plan,
        "release-lane-visual-regression",
        **(
            {}
            if plan.frontend_visual_scope == "affected"
            else {
                "status": VerificationTerminalStatus.BLOCKED,
                "nonexecuted_command_refs": (
                    "command:frontend.visual-regression",
                ),
            }
        ),
    )
    return (
        f"release-lane-desktop-packaging={desktop}",
        f"release-lane-visual-regression={visual}",
    )


def _replace_binding(
    bindings: tuple[str, ...],
    unit_ref: str,
    encoded: str,
) -> tuple[str, ...]:
    return tuple(
        f"{unit_ref}={encoded}" if binding.startswith(f"{unit_ref}=") else binding
        for binding in bindings
    )


def test_final_ci_evidence_dag_accepts_only_the_complete_exact_ordered_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    payload = evidence_dag.validate_final_gate(
        Path("."),
        plan.repository_sha,
        plan.base_sha,
        plan.frontend_visual_scope,
        results,
        envelopes,
        _final_optional_bindings(plan),
    )

    assert payload["repository_sha"] == plan.repository_sha
    assert payload["plan_fingerprint"] == plan.plan_fingerprint
    assert len(payload["receipt_bindings"]) == len(CI_JOB_GRAPH) - 1
    assert len(payload["content_fingerprint"]) == 64


def test_final_ci_evidence_dag_validates_present_typed_optional_envelopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    optional = (
        "release-lane-desktop-packaging="
        + _encoded(plan, "release-lane-desktop-packaging"),
        "release-lane-visual-regression="
        + _encoded(plan, "release-lane-visual-regression"),
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    payload = evidence_dag.validate_final_gate(
        Path("."),
        plan.repository_sha,
        plan.base_sha,
        plan.frontend_visual_scope,
        results,
        envelopes,
        optional,
    )

    assert len(payload["receipt_bindings"]) == len(CI_JOB_GRAPH) - 1


@pytest.mark.parametrize("result_status", ("failure", "cancelled", "skipped"))
def test_final_ci_evidence_dag_rejects_every_non_success_terminal_result(
    monkeypatch: pytest.MonkeyPatch,
    result_status: str,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)
    tampered = (*results[:-1], f"release-lane-performance={result_status}")

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            tampered,
            envelopes,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:upstream-not-successful"


@pytest.mark.parametrize(
    ("mutation", "reason_ref"),
    (
        ("missing", "reason-ref:ci-evidence:envelope-membership-invalid"),
        ("reordered", "reason-ref:ci-evidence:envelope-membership-invalid"),
        ("duplicate", "reason-ref:ci-evidence:envelope-duplicate"),
        ("cross_unit", "reason-ref:ci-evidence:cross-unit-substitution"),
    ),
)
def test_final_ci_evidence_dag_rejects_arity_order_and_substitution(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    reason_ref: str,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)
    if mutation == "missing":
        tampered = envelopes[:-1]
    elif mutation == "reordered":
        tampered = (envelopes[1], envelopes[0], *envelopes[2:])
    elif mutation == "duplicate":
        tampered = (*envelopes, envelopes[0])
    else:
        first_ref, first_value = envelopes[0].split("=", 1)
        second_ref, second_value = envelopes[1].split("=", 1)
        tampered = (
            f"{first_ref}={second_value}",
            f"{second_ref}={first_value}",
            *envelopes[2:],
        )

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            tampered,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == reason_ref


def test_final_ci_evidence_dag_rejects_cross_plan_recomputed_envelopes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    other_plan = _plan(
        repository_sha="c" * 40,
        schema_version="uaa_ci_command_manifest.v3",
    )
    results, envelopes = _final_gate_bindings(plan)
    other_envelope = _encoded(other_plan, "manifest-attestation")
    tampered = (f"manifest-attestation={other_envelope}", *envelopes[1:])
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            tampered,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:envelope-invalid"


def test_final_ci_evidence_dag_redacts_plan_reconstruction_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)

    def fail_plan(*_args: object, **_kwargs: object) -> VerificationPlan:
        raise subprocess.CalledProcessError(1, ("git", "status"))

    monkeypatch.setattr(evidence_dag, "build_plan", fail_plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:canonical-plan-invalid"


def test_final_ci_evidence_dag_redacts_typescript_plan_binding_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)

    def fail_plan(*_args: object, **_kwargs: object) -> VerificationPlan:
        raise TypeScriptBindingError("typescript-declaration:private-path-invalid")

    monkeypatch.setattr(evidence_dag, "build_plan", fail_plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:canonical-plan-invalid"


def test_final_ci_evidence_dag_rejects_recomputed_noncanonical_unit_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    receipt = replace(
        _receipt(plan, "manifest-attestation"),
        proof_equivalence_ref="proof-equivalence-ref:substituted",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    receipt = replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    recomputed = encode_github_job_output(
        build_github_job_output_envelope(plan, receipt)
    )
    tampered = (f"manifest-attestation={recomputed}", *envelopes[1:])
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            tampered,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:receipt-unit-invalid"


def test_final_ci_evidence_dag_rejects_recomputed_typescript_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    substituted = _encoded(
        plan,
        "control-center-frontend",
        typescript_runtime_fingerprint="c" * 64,
        typescript_version_ref="typescript-version-ref:substituted",
    )
    tampered = tuple(
        (
            f"control-center-frontend={substituted}"
            if binding.startswith("control-center-frontend=")
            else binding
        )
        for binding in envelopes
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            tampered,
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:typescript-runtime-invalid"
    )


def test_final_ci_evidence_dag_rejects_same_plan_receipt_substitution_outside_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    substituted = _encoded(plan, "lint", output_digest="c" * 64)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            _replace_binding(envelopes, "lint", substituted),
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:aggregate-proof-invalid"


def test_final_ci_evidence_dag_rejects_dependency_chronology_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    substituted = _encoded(
        plan,
        "static-verification",
        started_at="2026-07-15T00:00:02Z",
        completed_at="2026-07-15T00:00:03Z",
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            _replace_binding(envelopes, "static-verification", substituted),
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:dependency-proof-invalid"


def test_final_ci_evidence_dag_rejects_shortened_aggregate_dependency_span(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    pytest_binding = next(
        binding for binding in envelopes if binding.startswith("pytest=")
    )
    aggregate_envelope = decode_github_job_output(pytest_binding.split("=", 1)[1])
    shortened_receipt = replace(
        aggregate_envelope.receipt,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
        started_at="2026-07-15T00:00:02Z",
        completed_at="2026-07-15T00:00:03Z",
        duration_ms=1_000,
    )
    shortened_fingerprint = verification_receipt_fingerprint(shortened_receipt)
    shortened_receipt = replace(
        shortened_receipt,
        receipt_ref=f"receipt:verification:{shortened_fingerprint}",
        receipt_fingerprint=shortened_fingerprint,
    )
    assert aggregate_envelope.final_run_manifest is not None
    shortened_bindings = tuple(
        (
            (unit_ref, shortened_receipt.receipt_ref)
            if unit_ref == "pytest"
            else (unit_ref, receipt_ref)
        )
        for unit_ref, receipt_ref in (
            aggregate_envelope.final_run_manifest.unit_receipt_bindings
        )
    )
    shortened_run = replace(
        aggregate_envelope.final_run_manifest,
        run_ref=f"run:verification:{'0' * 64}",
        run_fingerprint="0" * 64,
        receipt_refs=tuple(receipt_ref for _unit_ref, receipt_ref in shortened_bindings),
        unit_receipt_bindings=shortened_bindings,
        started_at="2026-07-15T00:00:02Z",
        completed_at="2026-07-15T00:00:03Z",
    )
    shortened_run_fingerprint = verification_run_manifest_fingerprint(shortened_run)
    shortened_run = replace(
        shortened_run,
        run_ref=f"run:verification:{shortened_run_fingerprint}",
        run_fingerprint=shortened_run_fingerprint,
    )
    substituted = encode_github_job_output(
        build_github_job_output_envelope(
            plan,
            shortened_receipt,
            final_run_manifest=shortened_run,
        )
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            _replace_binding(envelopes, "pytest", substituted),
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:aggregate-proof-invalid"


def test_final_ci_evidence_dag_seals_every_post_pytest_receipt_in_terminal_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    optional = _final_optional_bindings(plan)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    payload = evidence_dag.validate_final_gate(
        Path("."),
        plan.repository_sha,
        plan.base_sha,
        plan.frontend_visual_scope,
        results,
        envelopes,
        optional,
    )

    terminal_bindings = dict(payload["terminal_run_manifest"]["unit_receipt_bindings"])
    decoded_by_unit = {
        unit_ref: decode_github_job_output(encoded).receipt
        for unit_ref, encoded in (
            binding.split("=", 1) for binding in (*envelopes, *optional)
        )
    }
    for unit_ref in (
        "static-verification",
        "control-center-frontend",
        "release-lane-desktop-packaging",
        "release-lane-frontend",
        "release-lane-visual-regression",
        "release-lane-performance",
    ):
        assert terminal_bindings[unit_ref] == decoded_by_unit[unit_ref].receipt_ref


def test_foundation_receipt_completes_the_exact_terminal_run() -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    _results, envelopes = _final_gate_bindings(plan)
    optional = _final_optional_bindings(plan)
    decoded_by_unit = {
        unit_ref: decode_github_job_output(encoded).receipt
        for unit_ref, encoded in (
            binding.split("=", 1) for binding in (*envelopes, *optional)
        )
    }
    foundation_unit = next(
        unit for unit in CI_JOB_GRAPH if unit.unit_ref == "foundation-gate-report"
    )
    dependency_receipts = {
        unit_ref: decoded_by_unit[unit_ref] for unit_ref in foundation_unit.needs
    }
    foundation_receipt = _receipt(plan, "foundation-gate-report")

    run = lane_runner._build_terminal_foundation_run(
        plan,
        dependency_receipts,
        foundation_receipt,
        execution_surface_ref=SURFACE,
    )

    assert run.status is VerificationTerminalStatus.PASSED
    assert run.missing_unit_refs == ()
    assert run.failed_unit_refs == ()
    assert dict(run.unit_receipt_bindings)["foundation-gate-report"] == (
        foundation_receipt.receipt_ref
    )
    encoded = encode_github_job_output(
        build_github_job_output_envelope(
            plan,
            foundation_receipt,
            final_run_manifest=run,
        )
    )
    decoded = decode_github_job_output(encoded)
    assert decoded.receipt == foundation_receipt
    assert decoded.final_run_manifest == run


def test_final_ci_evidence_dag_rejects_required_command_as_optional_nonexecution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(
        schema_version="uaa_ci_command_manifest.v3",
        frontend_visual_scope="not_affected",
    )
    results, envelopes = _final_gate_bindings(plan)
    invalid_visual = _encoded(
        plan,
        "release-lane-visual-regression",
        status=VerificationTerminalStatus.BLOCKED,
        nonexecuted_command_refs=(
            "command:frontend.visual-regression",
            "command:frontend.visual-regression-contract",
        ),
    )
    optional = (
        _final_optional_bindings(plan)[0],
        f"release-lane-visual-regression={invalid_visual}",
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            optional,
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:optional-command-proof-invalid"
    )


@pytest.mark.parametrize(
    ("unit_ref", "optional_command_ref"),
    (
        (
            "release-lane-desktop-packaging",
            "command:desktop-packaging.proof",
        ),
        (
            "release-lane-visual-regression",
            "command:frontend.visual-regression",
        ),
    ),
)
def test_final_ci_evidence_dag_rejects_missing_typed_optional_contract_proof(
    monkeypatch: pytest.MonkeyPatch,
    unit_ref: str,
    optional_command_ref: str,
) -> None:
    plan = _plan(
        schema_version="uaa_ci_command_manifest.v3",
        frontend_visual_scope="not_affected",
    )
    results, envelopes = _final_gate_bindings(plan)
    receipt = _receipt(
        plan,
        unit_ref,
        status=VerificationTerminalStatus.BLOCKED,
        nonexecuted_command_refs=(optional_command_ref,),
    )
    forged = replace(
        receipt,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
        result_refs=receipt.result_refs[:1],
        command_refs=(optional_command_ref,),
        command_result_bindings=(),
        executed_command_result_bindings=(),
    )
    forged_fingerprint = verification_receipt_fingerprint(forged)
    forged = replace(
        forged,
        receipt_ref=f"receipt:verification:{forged_fingerprint}",
        receipt_fingerprint=forged_fingerprint,
    )
    substituted = encode_github_job_output(
        build_github_job_output_envelope(plan, forged)
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            _replace_binding(
                _final_optional_bindings(plan),
                unit_ref,
                substituted,
            ),
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:optional-command-proof-invalid"
    )


@pytest.mark.parametrize(
    ("unit_ref", "command_ref"),
    (
        (
            "release-lane-desktop-packaging",
            "command:desktop-packaging.proof",
        ),
        (
            "release-lane-visual-regression",
            "command:frontend.visual-regression",
        ),
    ),
)
def test_final_ci_evidence_dag_rejects_recomputed_optional_nonexecution_forgery(
    monkeypatch: pytest.MonkeyPatch,
    unit_ref: str,
    command_ref: str,
) -> None:
    plan = _plan(
        schema_version="uaa_ci_command_manifest.v3",
        frontend_visual_scope="not_affected",
    )
    results, envelopes = _final_gate_bindings(plan)
    receipt = _receipt(
        plan,
        unit_ref,
        status=VerificationTerminalStatus.BLOCKED,
        nonexecuted_command_refs=(command_ref,),
    )
    forged_reason = "reason-ref:forged:optional-nonexecution"
    forged_result = optional_nonexecution_result_ref(
        plan.repository_sha,
        command_ref,
        forged_reason,
    )
    forged = replace(
        receipt,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
        result_refs=tuple(
            forged_result if ref == command_ref else result_ref
            for ref, result_ref in zip(
                UNITS_BY_REF[unit_ref].command_refs,
                receipt.result_refs,
                strict=True,
            )
        ),
        nonexecuted_command_result_bindings=(
            (command_ref, forged_result, forged_reason),
        ),
    )
    forged_fingerprint = verification_receipt_fingerprint(forged)
    forged = replace(
        forged,
        receipt_ref=f"receipt:verification:{forged_fingerprint}",
        receipt_fingerprint=forged_fingerprint,
    )
    substituted = encode_github_job_output(
        build_github_job_output_envelope(plan, forged)
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            _replace_binding(
                _final_optional_bindings(plan),
                unit_ref,
                substituted,
            ),
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:optional-command-proof-invalid"
    )


def test_final_ci_evidence_dag_rejects_fresh_frontend_execution_in_reuse_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    fresh = _encoded(plan, "release-lane-frontend")
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            _replace_binding(envelopes, "release-lane-frontend", fresh),
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:reused-proof-invalid"


def test_final_ci_evidence_dag_rejects_cross_receipt_frontend_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    wrong_source = _receipt(plan, "lint").receipt_ref
    substituted = _encoded(
        plan,
        "release-lane-frontend",
        reused_command_receipt_bindings=(("command:frontend.check", wrong_source),),
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            _replace_binding(envelopes, "release-lane-frontend", substituted),
            _final_optional_bindings(plan),
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:reused-proof-invalid"


def test_final_ci_evidence_dag_rejects_missing_affected_visual_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(schema_version="uaa_ci_command_manifest.v3")
    results, envelopes = _final_gate_bindings(plan)
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:optional-envelope-missing"
    )


def test_final_ci_evidence_dag_rejects_visual_envelope_when_not_affected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(
        schema_version="uaa_ci_command_manifest.v3",
        frontend_visual_scope="not_affected",
    )
    results, envelopes = _final_gate_bindings(plan)
    optional = (
        _final_optional_bindings(plan)[0],
        "release-lane-visual-regression="
        + _encoded(plan, "release-lane-visual-regression"),
    )
    monkeypatch.setattr(evidence_dag, "build_plan", lambda *_args, **_kwargs: plan)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag.validate_final_gate(
            Path("."),
            plan.repository_sha,
            plan.base_sha,
            plan.frontend_visual_scope,
            results,
            envelopes,
            optional,
        )

    assert error.value.reason_ref == (
        "reason-ref:ci-evidence:visual-envelope-posture-invalid"
    )


def test_final_ci_evidence_dag_output_is_exclusive_and_owner_only(
    tmp_path: Path,
) -> None:
    output = tmp_path / "evidence.json"
    payload = {"schema_version": "test"}

    evidence_dag._write_output(output, payload)

    assert output.stat().st_mode & 0o077 == 0
    original = output.read_bytes()
    with pytest.raises(evidence_dag.CiEvidenceDagError):
        evidence_dag._write_output(output, payload)
    assert output.read_bytes() == original


def test_final_ci_evidence_dag_output_rejects_symlink_without_mutating_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.write_text("unchanged", encoding="ascii")
    output = tmp_path / "evidence.json"
    output.symlink_to(target)

    with pytest.raises(evidence_dag.CiEvidenceDagError):
        evidence_dag._write_output(output, {"schema_version": "test"})

    assert target.read_text(encoding="ascii") == "unchanged"


def test_final_ci_evidence_dag_output_rejects_symlinked_parent(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    symlinked_parent = tmp_path / "linked"
    symlinked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag._write_output(
            symlinked_parent / "evidence.json",
            {"schema_version": "test"},
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:output-invalid"
    assert not (real_parent / "evidence.json").exists()


def test_final_ci_evidence_dag_output_rejects_writable_nonsticky_parent(
    tmp_path: Path,
) -> None:
    writable_parent = tmp_path / "writable-parent"
    writable_parent.mkdir()
    writable_parent.chmod(0o777)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag._write_output(
            writable_parent / "evidence.json",
            {"schema_version": "test"},
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:output-invalid"
    assert not (writable_parent / "evidence.json").exists()


def test_final_ci_evidence_dag_output_redacts_low_level_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsafe_detail = f"private output path {tmp_path}"

    def fail_write(*_args: object, **_kwargs: object) -> int:
        raise OSError(unsafe_detail)

    monkeypatch.setattr(evidence_dag.os, "write", fail_write)

    with pytest.raises(evidence_dag.CiEvidenceDagError) as error:
        evidence_dag._write_output(
            tmp_path / "evidence.json",
            {"schema_version": "test"},
        )

    assert error.value.reason_ref == "reason-ref:ci-evidence:output-invalid"
    assert unsafe_detail not in str(error.value)


def test_public_github_output_helper_rejects_raw_values_and_fifos(
    tmp_path: Path,
) -> None:
    output = tmp_path / "github-output"
    output.write_bytes(b"")
    output.chmod(0o600)
    with pytest.raises(VerificationGithubPrerequisiteError) as raw_error:
        append_github_output(output, "verification_envelope", "raw-log-value")
    assert raw_error.value.reason_ref == (
        "reason-ref:github-prerequisite:github-output-value-invalid"
    )
    assert output.read_bytes() == b""

    fifo = tmp_path / "github-output-fifo"
    os.mkfifo(fifo, 0o600)
    with pytest.raises(VerificationGithubPrerequisiteError) as fifo_error:
        append_github_output(
            fifo,
            "verification_envelope",
            _encoded(_plan(), "manifest-attestation"),
        )
    assert fifo_error.value.reason_ref == (
        "reason-ref:github-prerequisite:output-path-unsafe"
    )
