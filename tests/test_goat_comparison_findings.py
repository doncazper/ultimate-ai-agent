from __future__ import annotations

import copy
import json
import os
from pathlib import Path

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


def _data() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_comparison_findings_verify_exact_scores_and_bounded_result() -> None:
    data = verifier.verify(ARTIFACT)

    assert data["initial_scores"]["uaa"]["weighted_total_reported"] == 88
    assert data["initial_scores"]["goatcitadel"]["weighted_total_reported"] == 86
    assert data["final_scores"]["uaa"]["weighted_total_reported"] == 88
    assert data["final_scores"] == data["initial_scores"]
    assert data["implementation_result"]["scenario_count"] == 23
    assert data["implementation_result"]["passed_unblocked_verifier_count"] == 22
    assert data["implementation_result"]["task_completion_count"] == 23
    assert data["implementation_result"]["correctness_rate"] == 1
    assert (
        data["implementation_result"]["cross_repo_empirical_performance"]
        == "not_measured"
    )
    assert data["implementation_result"]["runtime_revalidation_required"] is True
    assert data["implementation_result"]["external_evidence_posture"] == (
        "opt_in_root_required"
    )


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


def test_comparison_findings_reject_report_binding_drift() -> None:
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
    data["implementation_result"]["evaluator_source_digest"] = "sha256:" + (
        "0" * 64
    )
    with pytest.raises(verifier.VerificationError, match="source digest"):
        verifier.verify_data(data)


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
