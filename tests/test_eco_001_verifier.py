from __future__ import annotations

import scripts.verify_eco_001_local_data as verifier


def test_eco_001_verifier_passes() -> None:
    assert verifier.verify() == []


def test_eco_001_verifier_rejects_forbidden_runtime_marker(
    monkeypatch, tmp_path
) -> None:
    source = tmp_path / "local_data.py"
    source.write_text("value = os.environ\n", encoding="utf-8")
    monkeypatch.setattr(
        verifier,
        "REQUIRED_FILES",
        (
            str(source.relative_to(tmp_path)),
            str(source.relative_to(tmp_path)),
            str(source.relative_to(tmp_path)),
            str(source.relative_to(tmp_path)),
        ),
    )
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures = verifier.verify()

    assert "forbidden ECO-001 runtime marker: os.environ" in failures
