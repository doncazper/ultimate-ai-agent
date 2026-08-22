from __future__ import annotations

from pathlib import Path

import pytest

import scripts.verify_queue_v2_q24_news_signals as verifier


def _temporary_source(monkeypatch, tmp_path: Path, source_text: str) -> None:
    source = tmp_path / "read_model.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("read_model.py",))
    monkeypatch.setattr(verifier, "REQUIRED_MARKERS", {})
    monkeypatch.setattr(verifier, "_operational_failures", lambda: [])


def test_q24_verifier_passes() -> None:
    assert verifier.verify() == []


@pytest.mark.parametrize(
    ("source_text", "runtime_ref"),
    (
        ("import requests\n", "requests"),
        ("import httpx\n", "httpx"),
        ("from urllib import request\n", "urllib.request"),
        ("from subprocess import run\n", "subprocess"),
        ("import playwright\n", "playwright"),
        ("import firecrawl\n", "firecrawl"),
        ("from browserbase import Browserbase\n", "browserbase"),
    ),
)
def test_q24_verifier_rejects_runtime_imports(
    monkeypatch,
    tmp_path: Path,
    source_text: str,
    runtime_ref: str,
) -> None:
    _temporary_source(monkeypatch, tmp_path, source_text)
    assert f"forbidden Q24 runtime import: {runtime_ref}" in verifier.verify()


@pytest.mark.parametrize("fragment", verifier.DENIED_AUTHORITY_FRAGMENTS)
def test_q24_verifier_rejects_authority_promotion(
    monkeypatch, tmp_path: Path, fragment: str
) -> None:
    _temporary_source(monkeypatch, tmp_path, f"payload = {{{fragment}}}\n")
    assert f"denied Q24 authority fragment: {fragment}" in verifier.verify()


def test_q24_verifier_reports_missing_artifact(monkeypatch, tmp_path: Path) -> None:
    _temporary_source(monkeypatch, tmp_path, "read_only = True\n")
    monkeypatch.setattr(
        verifier,
        "REQUIRED_FILES",
        ("read_model.py", "missing.md"),
    )
    assert "missing Q24 artifact: missing.md" in verifier.verify()
