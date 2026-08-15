from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import verify_goat_comparison_findings as verifier


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "goat_comparison_20260712.json"
)
PROVENANCE_REPLACEMENT = (
    ARTIFACT.parent / "goat_comparison_20260712.provenance-0001.json"
)


def _data() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _provenance_replacement() -> dict[str, object]:
    return json.loads(PROVENANCE_REPLACEMENT.read_text(encoding="utf-8"))


def test_comparison_findings_verify_exact_scores_and_bounded_result() -> None:
    data = verifier.verify(ARTIFACT)

    assert data["initial_scores"]["uaa"]["weighted_total_reported"] == 88
    assert data["initial_scores"]["goatcitadel"]["weighted_total_reported"] == 86
    assert data["final_scores"]["uaa"]["weighted_total_reported"] == 88
    assert data["final_scores"] == data["initial_scores"]
    assert data["implementation_result"]["scenario_count"] == 23
    assert data["implementation_result"]["passed_unblocked_verifier_count"] == 22
    assert data["implementation_result"]["task_completion_count"] is None
    assert data["implementation_result"]["task_completion_posture"] == "not_measured"
    assert data["implementation_result"]["correctness_rate"] is None
    assert data["implementation_result"]["correctness_rate_posture"] == "not_measured"
    assert (
        data["implementation_result"]["cross_repo_empirical_performance"]
        == "not_measured"
    )
    assert data["implementation_result"]["runtime_revalidation_required"] is True
    assert data["implementation_result"]["external_evidence_posture"] == (
        "opt_in_root_required"
    )


def test_provenance_replacement_preserves_the_historical_artifact() -> None:
    proof = _provenance_replacement()

    assert verifier._sha256_ref(ARTIFACT.read_bytes()) == (
        verifier.HISTORICAL_ARTIFACT_DIGEST
    )
    assert proof["generation"] == 1
    assert (
        proof["historical_binding"]["source_commit"]
        == (_data()["implementation_result"]["uaa_source_commit"])
    )
    assert proof["reachable_replacement"]["source_commit"] == (
        verifier.PROVENANCE_REPAIR_BASE_COMMIT
    )
    assert proof["contract_transition"]["comparison_findings_changed"] is False
    assert proof["contract_transition"]["score_changed"] is False
    assert proof["contract_transition"]["report_projection_changed"] is False
    assert proof["authority_granted"] is False


def test_provenance_replacement_never_accepts_the_historical_sha_as_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ancestry_calls: list[str] = []
    digest_calls: list[str] = []
    original_ancestry = verifier.evaluation_source_commit_is_ancestor
    original_digest = verifier.evaluation_source_digest_at_commit

    def guarded_ancestry(commit: str) -> bool:
        ancestry_calls.append(commit)
        assert commit == verifier.PROVENANCE_REPAIR_BASE_COMMIT
        return original_ancestry(commit)

    def guarded_digest(commit: str) -> str:
        digest_calls.append(commit)
        assert commit == verifier.PROVENANCE_REPAIR_BASE_COMMIT
        return original_digest(commit)

    monkeypatch.setattr(
        verifier, "evaluation_source_commit_is_ancestor", guarded_ancestry
    )
    monkeypatch.setattr(verifier, "evaluation_source_digest_at_commit", guarded_digest)

    verifier.verify_data(_data())

    assert ancestry_calls == [verifier.PROVENANCE_REPAIR_BASE_COMMIT]
    assert digest_calls == [verifier.PROVENANCE_REPAIR_BASE_COMMIT]


@pytest.mark.parametrize(
    ("section", "field", "replacement", "error"),
    (
        (None, "generation", 2, "generation drift"),
        (
            "comparison_artifact",
            "artifact_sha256",
            "sha256:" + ("0" * 64),
            "artifact replacement binding drift",
        ),
        (
            "historical_binding",
            "source_commit",
            "0" * 40,
            "historical evaluator source digest substitution",
        ),
        (
            "reachable_replacement",
            "source_commit",
            "0" * 40,
            "source commit substitution",
        ),
        (
            "contract_transition",
            "current_evaluator_source_digest",
            "sha256:" + ("0" * 64),
            "stale.*current evaluator",
        ),
        (
            "contract_transition",
            "changed_source_refs",
            ["repo-ref:uaa:scripts/run_agent_capability_evaluation.py"],
            "source substitution",
        ),
    ),
)
def test_provenance_replacement_rejects_substitution(
    section: str | None,
    field: str,
    replacement: object,
    error: str,
) -> None:
    proof = copy.deepcopy(_provenance_replacement())
    target = proof if section is None else proof[section]
    target[field] = replacement

    with pytest.raises(verifier.VerificationError, match=error):
        verifier.verify_data(_data(), provenance_replacement=proof)


def test_provenance_replacement_rejects_extra_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = tmp_path / "goat_comparison_20260712.provenance-0001.json"
    canonical.write_text("{}\n", encoding="utf-8")
    (tmp_path / "goat_comparison_20260712.provenance-0002.json").write_text(
        "{}\n", encoding="utf-8"
    )
    monkeypatch.setattr(verifier, "PROVENANCE_REPLACEMENT", canonical)

    with pytest.raises(verifier.VerificationError, match="exactly one bounded"):
        verifier._load_provenance_replacement()


def test_verification_rejects_noncanonical_artifact_substitution(
    tmp_path: Path,
) -> None:
    substituted = tmp_path / ARTIFACT.name
    substituted.write_bytes(ARTIFACT.read_bytes())

    with pytest.raises(verifier.VerificationError, match="path is not canonical"):
        verifier.verify(substituted)


def test_comparison_findings_reject_score_evidence_and_authority_drift() -> None:
    data = _data()
    data["initial_scores"]["uaa"]["weighted_total_raw"] = 99
    with pytest.raises(verifier.VerificationError, match="weighted total"):
        verifier.verify_data(data)

    data = _data()
    data["findings"][0]["evidence_refs"]["uaa"] = ["repo-ref:uaa:missing.py#L1"]
    with pytest.raises(verifier.VerificationError, match="missing UAA"):
        verifier.verify_data(data)

    data = _data()
    data["authority_granted"] = True
    with pytest.raises(verifier.VerificationError, match="cannot grant authority"):
        verifier.verify_data(data)


def test_comparison_findings_reject_missing_component_and_unsafe_fields() -> None:
    data = _data()
    data["findings"] = data["findings"][:-1]
    with pytest.raises(verifier.VerificationError, match="16-component"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["rawPrompt"] = "not allowed"
    with pytest.raises(verifier.VerificationError, match="unsafe durable field"):
        verifier.verify_data(data)


@pytest.mark.parametrize("key", ("apiToken", "passwordValue", "secret"))
def test_comparison_findings_reject_sensitive_key_families(key: str) -> None:
    data = copy.deepcopy(_data())
    data[key] = "credential-shaped-value"

    with pytest.raises(verifier.VerificationError, match="unsafe durable field"):
        verifier.verify_data(data)


def test_comparison_findings_reject_report_binding_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = copy.deepcopy(_data())
    data["implementation_result"]["report_projection"]["observations"][0][
        "execution_fingerprint_ref"
    ] = "fingerprint-ref:agent-capability-scenario:sha256:" + ("0" * 64)
    with pytest.raises(verifier.VerificationError, match="binding drift"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["implementation_result"]["report_projection_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(verifier.VerificationError, match="digest drift"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["implementation_result"]["uaa_source_commit"] = "not-a-commit"
    with pytest.raises(verifier.VerificationError, match="source commit"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["implementation_result"]["evaluator_source_digest"] = "sha256:" + ("0" * 64)
    with pytest.raises(verifier.VerificationError, match="source digest"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["implementation_result"]["task_completion_count"] = 23
    data["implementation_result"]["task_completion_posture"] = "measured"
    with pytest.raises(verifier.VerificationError, match="must remain not measured"):
        verifier.verify_data(data)

    data = copy.deepcopy(_data())
    data["implementation_result"]["report_projection"]["observations"][0][
        "task_completed"
    ] = True
    with pytest.raises(verifier.VerificationError, match="cannot synthesize"):
        verifier.verify_data(data)

    monkeypatch.setattr(
        verifier,
        "evaluation_source_digest",
        lambda: "sha256:" + ("1" * 64),
    )
    with pytest.raises(verifier.VerificationError, match="stale.*current evaluator"):
        verifier.verify_data(_data())

    monkeypatch.setattr(
        verifier,
        "evaluation_source_commit_is_ancestor",
        lambda _commit: False,
    )
    with pytest.raises(verifier.VerificationError, match="not reachable"):
        verifier.verify_data(_data())


def test_comparison_findings_runtime_revalidation_uses_actual_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _data()
    expected = data["implementation_result"]["report_projection"]
    sentinel = object()
    monkeypatch.setattr(verifier, "run_agent_capability_evaluation", lambda: sentinel)
    monkeypatch.setattr(
        verifier,
        "evaluation_report_projection",
        lambda report: expected if report is sentinel else {},
    )

    assert verifier.verify_data(data, revalidate_uaa=True) == data

    monkeypatch.setattr(verifier, "evaluation_report_projection", lambda report: {})
    with pytest.raises(verifier.VerificationError, match="current runtime"):
        verifier.verify_data(data, revalidate_uaa=True)


def test_default_verification_does_not_read_external_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = verifier._safe_read

    def guarded(relative: Path, *, root: Path, maximum_bytes: int) -> bytes:
        assert root == verifier.ROOT
        return original(relative, root=root, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(verifier, "_safe_read", guarded)
    verifier.verify(ARTIFACT)


def test_external_evidence_validation_requires_an_explicit_bounded_root(
    tmp_path: Path,
) -> None:
    data = _data()
    required_lines: dict[Path, int] = {}
    for finding in data["findings"]:
        for value in finding["evidence_refs"]["goatcitadel"]:
            match = verifier.EVIDENCE_RE.fullmatch(value)
            assert match is not None
            relative = Path(match.group(2))
            required_lines[relative] = max(
                required_lines.get(relative, 0),
                int(match.group(4) or match.group(3)),
            )
    for relative, line_count in required_lines.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence\n" * line_count, encoding="utf-8")

    assert verifier.verify_data(data, goat_root=tmp_path) == data


def test_comparison_findings_reject_path_escape_and_line_range_drift(
    tmp_path: Path,
) -> None:
    data = _data()
    data["findings"][0]["evidence_refs"]["uaa"] = ["repo-ref:uaa:/etc/hosts#L1"]
    with pytest.raises(verifier.VerificationError, match="path is unsafe"):
        verifier.verify_data(data)

    data = _data()
    data["findings"][0]["evidence_refs"]["goatcitadel"] = [
        "repo-ref:goatcitadel:README.md#L999999"
    ]
    (tmp_path / "README.md").write_text("bounded\n", encoding="utf-8")
    with pytest.raises(verifier.VerificationError, match="line range"):
        verifier.verify_data(data, goat_root=tmp_path)


def test_safe_read_rejects_symlink_and_hardlink(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text("{}", encoding="utf-8")
    linked = tmp_path / "linked.json"
    linked.symlink_to(real)
    with pytest.raises((OSError, verifier.VerificationError)):
        verifier._safe_read(
            linked.relative_to(tmp_path), root=tmp_path, maximum_bytes=100
        )

    hardlink = tmp_path / "hardlink.json"
    hardlink.hardlink_to(real)
    with pytest.raises(verifier.VerificationError, match="single-link"):
        verifier._safe_read(
            real.relative_to(tmp_path), root=tmp_path, maximum_bytes=100
        )


def test_safe_read_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "artifact.json"
    os.mkfifo(fifo)

    with pytest.raises(verifier.VerificationError, match="regular file"):
        verifier._safe_read(
            fifo.relative_to(tmp_path), root=tmp_path, maximum_bytes=100
        )


def test_refresh_requires_an_exact_clean_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=b" M tracked-file\n",
            stderr=b"",
        ),
    )

    with pytest.raises(verifier.VerificationError, match="exact clean committed"):
        verifier.refresh_uaa_evaluation()


def test_refresh_cannot_rewrite_the_historical_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        verifier.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=b"",
            stderr=b"",
        ),
    )

    with pytest.raises(verifier.VerificationError, match="historical.*immutable"):
        verifier.refresh_uaa_evaluation()
