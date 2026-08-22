from __future__ import annotations

from pathlib import Path

from scripts.verify_eco_008_changesets import _prohibited_imports, verify


def test_eco_008_verifier_passes() -> None:
    assert verify() == []


def test_eco_008_verifier_detects_from_import_alias(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "from urllib import request as url_request\n", encoding="utf-8"
    )

    assert _prohibited_imports(candidate) == {"urllib.request"}
