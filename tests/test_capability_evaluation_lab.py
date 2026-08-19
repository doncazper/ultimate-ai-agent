from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
from pydantic import ValidationError

from scripts import run_capability_evaluation_lab as runner
from ultimate_ai_agent.core.evals import (
    CAPABILITY_EVALUATION_LAB_SUBJECT_REFS,
    CapabilityEvaluationLabManifest,
    CapabilityLabFailureAttribution,
    CapabilityLabGateStatus,
    CapabilityLabObservedStatus,
    build_capability_evaluation_run_receipt,
    capability_evaluation_manifest_digest,
)


EVALUATOR_REVISION_REF = f"git-sha:{'a' * 40}"
EVALUATOR_SOURCE_DIGEST_REF = f"sha256:{'b' * 64}"


def _passing_results(
    manifest: CapabilityEvaluationLabManifest,
    *,
    evaluator_revision_ref: str = EVALUATOR_REVISION_REF,
    evaluator_source_digest_ref: str = EVALUATOR_SOURCE_DIGEST_REF,
):
    return tuple(
        runner._case_result(
            case=case,
            evaluator_revision_ref=evaluator_revision_ref,
            evaluator_source_digest_ref=evaluator_source_digest_ref,
            failure_code="none",
        )
        for case in manifest.cases
    )


def test_versioned_manifest_is_deterministic_and_covers_all_subjects() -> None:
    manifest = runner.load_manifest()

    assert manifest.case_refs == tuple(case.case_ref for case in manifest.cases)
    assert {case.subject_ref for case in manifest.cases} == set(
        CAPABILITY_EVALUATION_LAB_SUBJECT_REFS
    )
    assert capability_evaluation_manifest_digest(
        manifest
    ) == capability_evaluation_manifest_digest(manifest)
    assert all(case.bounded_variance is False for case in manifest.cases)
    assert manifest.live_provider_benchmark_enabled is False
    assert manifest.model_judgment_enabled is False
    assert manifest.score_authority_enabled is False
    assert manifest.authority_granted is False


def test_manifest_rejects_raw_payload_fields_and_score_authority() -> None:
    payload = runner.load_manifest().model_dump(mode="json")
    payload["raw_prompt"] = "forbidden"
    with pytest.raises(ValidationError, match="extra"):
        CapabilityEvaluationLabManifest.model_validate(payload)

    payload.pop("raw_prompt")
    payload["score_authority_enabled"] = True
    with pytest.raises(ValidationError, match="literal_error"):
        CapabilityEvaluationLabManifest.model_validate(payload)

    payload = runner.load_manifest().model_dump(mode="json")
    payload["cases"][0]["expected_status"] = "blocked"
    with pytest.raises(ValidationError, match="enum"):
        CapabilityEvaluationLabManifest.model_validate(payload)


def test_pinned_source_digest_drift_fails_registry_validation() -> None:
    manifest = runner.load_manifest()
    cases = list(manifest.cases)
    cases[1] = cases[1].model_copy(
        update={"source_evidence_digest_ref": f"sha256:{'0' * 64}"}
    )
    drifted = manifest.model_copy(update={"cases": tuple(cases)})

    with pytest.raises(ValueError, match="pinned source evidence digest drift"):
        runner._validate_registry(drifted)


def test_run_receipt_binds_revisions_without_granting_score_authority() -> None:
    manifest = runner.load_manifest()
    receipt = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        results=_passing_results(manifest),
    )

    assert receipt.status == CapabilityLabGateStatus.passed
    assert receipt.case_count == 4
    assert receipt.missing_case_refs == ()
    assert receipt.unexpected_case_refs == ()
    assert all(gate.status == CapabilityLabGateStatus.passed for gate in receipt.claim_gates)
    uaa_result = receipt.results[0]
    assert uaa_result.source_revision_ref == EVALUATOR_REVISION_REF
    assert uaa_result.source_evidence_digest_ref == EVALUATOR_SOURCE_DIGEST_REF
    assert receipt.score_authority_granted is False
    assert receipt.live_provider_benchmark_performed is False
    assert receipt.authority_granted is False
    assert set(receipt.model_dump()).isdisjoint(
        {"score", "score_value", "weighted_score"}
    )


def test_missing_case_remains_in_denominator_and_fails_claim_gate() -> None:
    manifest = runner.load_manifest()
    receipt = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        results=_passing_results(manifest)[:-1],
    )

    assert receipt.status == CapabilityLabGateStatus.failed
    assert receipt.case_count == 4
    assert len(receipt.results) == 3
    assert receipt.missing_case_refs == (manifest.case_refs[-1],)
    assert receipt.claim_gates[-1].status == CapabilityLabGateStatus.failed


def test_nonzero_verifier_result_uses_unknown_attribution_and_fails() -> None:
    manifest = runner.load_manifest()
    results = list(_passing_results(manifest))
    results[0] = runner._case_result(
        case=manifest.cases[0],
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        failure_code="assertion_failed",
    )
    first = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        results=tuple(results),
    )
    second = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        results=tuple(results),
    )

    assert first.status == CapabilityLabGateStatus.failed
    assert first.results[0].observed_status == CapabilityLabObservedStatus.unknown
    assert (
        first.results[0].failure_attribution
        == CapabilityLabFailureAttribution.unknown
    )
    assert first.evidence_digest_ref == second.evidence_digest_ref
    assert first.run_ref == second.run_ref


def test_builder_rejects_tampered_case_evidence_digest() -> None:
    manifest = runner.load_manifest()
    results = list(_passing_results(manifest))
    results[0] = results[0].model_copy(
        update={"evidence_digest_ref": f"sha256:{'0' * 64}"}
    )

    with pytest.raises(ValueError, match="evidence digest binding drift"):
        build_capability_evaluation_run_receipt(
            manifest=manifest,
            evaluator_revision_ref=EVALUATOR_REVISION_REF,
            evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
            results=tuple(results),
        )


def test_pinned_case_digest_changes_with_evaluator_revision() -> None:
    manifest = runner.load_manifest()
    first = _passing_results(manifest)
    second = _passing_results(
        manifest,
        evaluator_revision_ref=f"git-sha:{'c' * 40}",
        evaluator_source_digest_ref=f"sha256:{'d' * 64}",
    )

    assert first[1].source_revision_ref == second[1].source_revision_ref
    assert first[1].source_evidence_digest_ref == second[1].source_evidence_digest_ref
    assert first[1].evidence_digest_ref != second[1].evidence_digest_ref


def test_runner_projects_a_content_free_pass_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    monkeypatch.setattr(runner.bounded_runner, "repository_commit", lambda: "c" * 40)
    monkeypatch.setattr(runner, "repository_inputs_match_exact_revision", lambda: True)
    monkeypatch.setattr(
        runner,
        "evaluation_lab_source_digest",
        lambda: f"sha256:{'d' * 64}",
    )
    monkeypatch.setattr(
        runner,
        "evaluation_lab_source_digest_at_commit",
        lambda _: f"sha256:{'d' * 64}",
    )
    monkeypatch.setattr(
        runner.bounded_runner,
        "_run_command",
        lambda *args, **kwargs: runner.bounded_runner.ScenarioCommandResult(
            0, 1, "none"
        ),
    )

    receipt = runner.run_capability_evaluation_lab(manifest)

    assert receipt.status == CapabilityLabGateStatus.passed
    assert receipt.evaluator_revision_ref == f"git-sha:{'c' * 40}"
    assert receipt.content_free is True
    assert receipt.raw_content_persisted is False
    assert {result.failure_attribution for result in receipt.results} == {
        CapabilityLabFailureAttribution.none
    }


def test_runner_refuses_uncommitted_evaluator_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    monkeypatch.setattr(runner.bounded_runner, "repository_commit", lambda: "c" * 40)
    monkeypatch.setattr(runner, "repository_inputs_match_exact_revision", lambda: True)
    monkeypatch.setattr(
        runner,
        "evaluation_lab_source_digest",
        lambda: f"sha256:{'d' * 64}",
    )
    monkeypatch.setattr(
        runner,
        "evaluation_lab_source_digest_at_commit",
        lambda _: f"sha256:{'e' * 64}",
    )

    with pytest.raises(ValueError, match="not committed at the exact revision"):
        runner.run_capability_evaluation_lab(manifest)


def test_runner_refuses_dirty_transitive_verifier_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    monkeypatch.setattr(
        runner,
        "repository_inputs_match_exact_revision",
        lambda: False,
    )

    with pytest.raises(ValueError, match="verifier inputs do not match"):
        runner.run_capability_evaluation_lab(manifest)


def test_python_only_child_environment_does_not_require_node(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = runner.bounded_runner._trusted_executable

    def python_only(name: str) -> str:
        if name in {"npm", "node"}:
            raise OSError("node unavailable")
        return original(name)

    monkeypatch.setattr(runner.bounded_runner, "_trusted_executable", python_only)
    environment = runner.bounded_runner._child_environment(
        tmp_path,
        include_node=False,
    )

    assert environment["UAA_AGENT_EVAL_OFFLINE"] == "1"
    assert "node" not in environment["PATH"].lower()


def test_validate_only_cli_is_revision_safe_and_performs_no_benchmark() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_capability_evaluation_lab.py",
            "--validate-only",
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["case_count"] == 4
    assert payload["validated_only"] is True
    assert payload["live_provider_benchmark_performed"] is False
    assert payload["score_authority_granted"] is False
    assert payload["authority_granted"] is False


def test_validation_failure_does_not_echo_rejected_manifest_content(
    tmp_path: Path,
) -> None:
    secret_marker = "secret-marker-must-not-appear"
    manifest_path = tmp_path / "invalid.json"
    payload = runner.load_manifest().model_dump(mode="json")
    payload["raw_prompt"] = secret_marker
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_capability_evaluation_lab.py",
            "--manifest",
            str(manifest_path),
            "--validate-only",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )

    assert result.returncode == 1
    assert "CAPABILITY_EVALUATION_LAB_VALIDATION_FAILED" in result.stderr
    assert secret_marker not in result.stderr
