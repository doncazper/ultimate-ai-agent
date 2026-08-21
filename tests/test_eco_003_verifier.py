from __future__ import annotations

import scripts.verify_eco_003_boards as verifier


def test_eco_003_verifier_passes() -> None:
    assert verifier.verify() == []


def test_eco_003_verifier_rejects_forbidden_runtime_marker(
    monkeypatch, tmp_path
) -> None:
    source = tmp_path / "boards.py"
    source.write_text("value = requests.get\n", encoding="utf-8")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("boards.py",) * 4)
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures = verifier.verify()

    assert "forbidden ECO-003 runtime marker: requests." in failures
