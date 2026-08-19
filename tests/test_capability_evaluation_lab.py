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
EVALUATOR_ENVIRONMENT_DIGEST_REF = f"sha256:{'e' * 64}"


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
            evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
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


def test_executable_registry_rejects_relabelled_subjects_and_claims() -> None:
    payload = runner.load_manifest().model_dump(mode="json")
    for key in ("subject_ref", "claim_ref"):
        payload["cases"][1][key], payload["cases"][2][key] = (
            payload["cases"][2][key],
            payload["cases"][1][key],
        )
        payload["claims"][1][key], payload["claims"][2][key] = (
            payload["claims"][2][key],
            payload["claims"][1][key],
        )
    relabelled = CapabilityEvaluationLabManifest.model_validate(payload)

    with pytest.raises(ValueError, match="subject or claim binding drift"):
        runner._validate_registry(relabelled)


def test_run_receipt_binds_revisions_without_granting_score_authority() -> None:
    manifest = runner.load_manifest()
    receipt = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
        results=_passing_results(manifest),
    )

    assert receipt.status == CapabilityLabGateStatus.passed
    assert receipt.case_count == 4
    assert receipt.missing_case_refs == ()
    assert receipt.unexpected_case_refs == ()
    assert all(
        gate.status == CapabilityLabGateStatus.passed for gate in receipt.claim_gates
    )
    uaa_result = receipt.results[0]
    assert uaa_result.source_revision_ref == EVALUATOR_REVISION_REF
    assert uaa_result.source_evidence_digest_ref == EVALUATOR_SOURCE_DIGEST_REF
    assert receipt.evaluator_environment_digest_ref == EVALUATOR_ENVIRONMENT_DIGEST_REF
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
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
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
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
        failure_code="assertion_failed",
    )
    first = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
        results=tuple(results),
    )
    second = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
        results=tuple(results),
    )

    assert first.status == CapabilityLabGateStatus.failed
    assert first.results[0].observed_status == CapabilityLabObservedStatus.unknown
    assert (
        first.results[0].failure_attribution == CapabilityLabFailureAttribution.unknown
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
            evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
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


def test_pinned_source_revision_drift_fails_registry_validation() -> None:
    manifest = runner.load_manifest()
    cases = list(manifest.cases)
    cases[1] = cases[1].model_copy(
        update={"source_revision_ref": f"git-sha:{'0' * 40}"}
    )
    drifted = manifest.model_copy(update={"cases": tuple(cases)})

    with pytest.raises(ValueError, match="pinned source revision drift"):
        runner._validate_registry(drifted)


def test_evidence_and_seed_drift_fail_registry_validation() -> None:
    manifest = runner.load_manifest()
    for update in (
        {"evidence_refs": ("repo-ref:unrelated-evidence",)},
        {"deterministic_seed_ref": "seed-ref:capability-lab:unrelated:v1"},
    ):
        cases = list(manifest.cases)
        cases[0] = cases[0].model_copy(update=update)
        drifted = manifest.model_copy(update={"cases": tuple(cases)})
        with pytest.raises(ValueError, match="evidence or seed binding drift"):
            runner._validate_registry(drifted)


def test_dependency_binding_hashes_installed_file_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_file = tmp_path / "demo.py"
    package_file.write_text("VALUE = 1\n", encoding="utf-8")

    class FakeDistribution:
        metadata = {"Name": "demo-dependency"}
        version = "1.0"
        files = (Path("demo.py"),)

        @staticmethod
        def read_text(_name: str) -> None:
            return None

        @staticmethod
        def locate_file(relative: Path) -> Path:
            return tmp_path / relative

    monkeypatch.setattr(runner.sys, "prefix", str(tmp_path))
    monkeypatch.setattr(
        runner.importlib.metadata,
        "distributions",
        lambda: (FakeDistribution(),),
    )
    first = runner._installed_distribution_bindings()
    package_file.write_text("VALUE = 2\n", encoding="utf-8")
    second = runner._installed_distribution_bindings()

    assert first != second


def test_dependency_binding_rejects_record_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_file = tmp_path / "demo.py"
    package_file.write_text("VALUE = 1\n", encoding="utf-8")

    class RecordedHash:
        mode = "sha256"
        value = "invalid-recorded-hash"

    class RecordedPath:
        hash = RecordedHash()

        @staticmethod
        def __fspath__() -> str:
            return "demo.py"

        @staticmethod
        def __str__() -> str:
            return "demo.py"

    class FakeDistribution:
        metadata = {"Name": "demo-dependency"}
        version = "1.0"
        files = (RecordedPath(),)

        @staticmethod
        def read_text(_name: str) -> None:
            return None

        @staticmethod
        def locate_file(relative: RecordedPath) -> Path:
            return tmp_path / Path(relative)

    monkeypatch.setattr(runner.sys, "prefix", str(tmp_path))
    monkeypatch.setattr(
        runner.importlib.metadata,
        "distributions",
        lambda: (FakeDistribution(),),
    )

    with pytest.raises(ValueError, match="installed dependency integrity drift"):
        runner._installed_distribution_bindings()


def test_standard_library_binding_hashes_file_bytes(tmp_path: Path) -> None:
    module = tmp_path / "example.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    first = runner._standard_library_digest(tmp_path)
    module.write_text("VALUE = 2\n", encoding="utf-8")
    second = runner._standard_library_digest(tmp_path)

    assert first != second


def test_environment_digest_changes_case_and_run_evidence() -> None:
    manifest = runner.load_manifest()
    first = _passing_results(manifest)
    other_environment = f"sha256:{'f' * 64}"
    second = tuple(
        runner._case_result(
            case=case,
            evaluator_revision_ref=EVALUATOR_REVISION_REF,
            evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
            evaluator_environment_digest_ref=other_environment,
            failure_code="none",
        )
        for case in manifest.cases
    )
    first_receipt = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        evaluator_environment_digest_ref=EVALUATOR_ENVIRONMENT_DIGEST_REF,
        results=first,
    )
    second_receipt = build_capability_evaluation_run_receipt(
        manifest=manifest,
        evaluator_revision_ref=EVALUATOR_REVISION_REF,
        evaluator_source_digest_ref=EVALUATOR_SOURCE_DIGEST_REF,
        evaluator_environment_digest_ref=other_environment,
        results=second,
    )

    assert first[0].evidence_digest_ref != second[0].evidence_digest_ref
    assert first_receipt.evidence_digest_ref != second_receipt.evidence_digest_ref


def test_runner_projects_a_content_free_pass_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    isolated_root = tmp_path / "isolated-repository"
    isolated_root.mkdir()
    observed_execution_roots: list[Path] = []
    monkeypatch.setattr(runner.bounded_runner, "repository_commit", lambda: "c" * 40)
    monkeypatch.setenv(runner.ISOLATED_CONTROLLER_COMMIT_ENV, "c" * 40)
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
        runner,
        "evaluator_environment_digest",
        lambda: EVALUATOR_ENVIRONMENT_DIGEST_REF,
    )
    monkeypatch.setattr(
        runner,
        "_prepare_isolated_checkout",
        lambda _commit, _destination: isolated_root,
    )
    monkeypatch.setattr(
        runner,
        "isolated_checkout_matches_exact_revision",
        lambda _root, _commit: True,
    )
    monkeypatch.setattr(
        runner,
        "_run_python_scenario",
        lambda *args, **kwargs: (
            observed_execution_roots.append(kwargs["execution_root"])
            or runner.bounded_runner.ScenarioCommandResult(0, 1, "none")
        ),
    )

    receipt = runner.run_capability_evaluation_lab(manifest)

    assert receipt.status == CapabilityLabGateStatus.passed
    assert receipt.evaluator_revision_ref == f"git-sha:{'c' * 40}"
    assert receipt.content_free is True
    assert receipt.raw_content_persisted is False
    assert observed_execution_roots == [isolated_root] * 4
    assert {result.failure_attribution for result in receipt.results} == {
        CapabilityLabFailureAttribution.none
    }


def test_runner_refuses_uncommitted_evaluator_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    monkeypatch.setattr(runner.bounded_runner, "repository_commit", lambda: "c" * 40)
    monkeypatch.setenv(runner.ISOLATED_CONTROLLER_COMMIT_ENV, "c" * 40)
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


def test_runner_refuses_an_unbound_controller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = runner.load_manifest()
    monkeypatch.setattr(runner.bounded_runner, "repository_commit", lambda: "c" * 40)
    monkeypatch.setattr(runner, "repository_inputs_match_exact_revision", lambda: True)
    monkeypatch.delenv(runner.ISOLATED_CONTROLLER_COMMIT_ENV, raising=False)

    with pytest.raises(ValueError, match="controller is not bound"):
        runner.run_capability_evaluation_lab(manifest)


def test_main_relaunches_before_loading_the_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(runner.ISOLATED_CONTROLLER_COMMIT_ENV, raising=False)
    monkeypatch.setattr(
        runner,
        "_relaunch_from_isolated_controller",
        lambda argv: 0 if argv == ["--json"] else 1,
    )
    monkeypatch.setattr(
        runner,
        "load_manifest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("outer controller must not load the manifest")
        ),
    )

    assert runner.main(["--json"]) == 0


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
    environment = runner._python_only_child_environment(tmp_path)

    assert environment["UAA_AGENT_EVAL_OFFLINE"] == "1"
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert "node" not in environment["PATH"].lower()


def test_python_launcher_preserves_virtual_environment_identity() -> None:
    launcher = Path(runner._trusted_python_launcher())

    assert launcher == Path(sys.executable)
    assert launcher.resolve().is_file()


def test_case_seed_ref_controls_the_child_hash_seed(tmp_path: Path) -> None:
    first = runner._python_only_child_environment(
        tmp_path / "first",
        deterministic_seed_ref="seed-ref:capability-lab:first:v1",
    )
    second = runner._python_only_child_environment(
        tmp_path / "second",
        deterministic_seed_ref="seed-ref:capability-lab:second:v1",
    )

    assert first["UAA_CAPABILITY_LAB_SEED_REF"].endswith(":first:v1")
    assert first["PYTHONHASHSEED"] != second["PYTHONHASHSEED"]


def test_subprocess_timeout_uses_fixed_redacted_cli_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("git", 10)
        ),
    )

    assert runner.main(["--json"]) == 1
    captured = capsys.readouterr()
    assert "CAPABILITY_EVALUATION_LAB_VALIDATION_FAILED" in captured.err
    assert "Traceback" not in captured.err
    assert str(Path(__file__).resolve().parents[1]) not in captured.err


def test_argument_parser_failure_uses_fixed_redacted_cli_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret_marker = "secret-marker-must-not-appear"

    assert runner.main(["--validate-only", f"--api-token={secret_marker}"]) == 1
    captured = capsys.readouterr()
    assert "CAPABILITY_EVALUATION_LAB_VALIDATION_FAILED" in captured.err
    assert secret_marker not in captured.err
    assert "unrecognized arguments" not in captured.err


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
