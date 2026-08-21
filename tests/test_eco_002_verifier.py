from __future__ import annotations

import scripts.verify_eco_002_tasks as verifier


def test_eco_002_verifier_passes() -> None:
    assert verifier.verify() == []


def test_eco_002_verifier_rejects_forbidden_runtime_marker(
    monkeypatch, tmp_path
) -> None:
    source = tmp_path / "tasks.py"
    source.write_text("value = requests.get\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("tasks.py",) * 4)
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures = verifier.verify()

    assert "forbidden ECO-002 runtime marker: requests." in failures
