import json
import subprocess
from pathlib import Path

import pytest

from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    scan_public_gate_payload_for_secrets,
)


def test_gate_evaluator_report_contains_no_raw_secret_like_values(foundation_gate_report):
    payload = foundation_gate_report.model_dump(mode="json")

    assert scan_public_gate_payload_for_secrets(payload) == []
    assert foundation_gate_report.overall_status in {FoundationGateStatus.passed, FoundationGateStatus.warning}


def test_sample_gate_report_is_secret_clean():
    with open("reports/foundation_gate/sample_foundation_gate_report.json", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert scan_public_gate_payload_for_secrets(payload) == []


def test_verify_all_detects_actual_private_key_header_in_tracked_file(monkeypatch, tmp_path):
    import scripts.verify_all as verify_all

    unsafe = tmp_path / "src/unsafe.py"
    unsafe.parent.mkdir(parents=True)
    unsafe.write_text('PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----"\n', encoding="utf-8")
    monkeypatch.setattr(verify_all, "ROOT", tmp_path)
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "src/unsafe.py\n")

    with pytest.raises(SystemExit) as exc:
        verify_all.verify_no_obvious_secrets()

    assert exc.value.code == 1


def test_verify_all_detects_tracked_generated_artifact(monkeypatch):
    import scripts.verify_all as verify_all

    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "src/ultimate_ai_agent.egg-info/PKG-INFO\n")

    with pytest.raises(SystemExit) as exc:
        verify_all.verify_no_generated_artifacts()

    assert exc.value.code == 1


def test_verify_all_does_not_flag_foundation_gate_evaluator_false_positive(monkeypatch):
    import scripts.verify_all as verify_all

    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *args, **kwargs: "src/ultimate_ai_agent/core/gate/evaluators.py\n",
    )

    verify_all.verify_no_obvious_secrets()


def test_core_runtime_avoids_deprecated_datetime_utcnow():
    source_files = (Path("src") / "ultimate_ai_agent").rglob("*.py")
    offenders = [
        str(path)
        for path in source_files
        if "datetime.utcnow" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
