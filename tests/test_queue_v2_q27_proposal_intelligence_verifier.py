from __future__ import annotations

from pathlib import Path

import pytest

import scripts.verify_queue_v2_q27_proposal_intelligence as verifier


def _temporary_source(monkeypatch, tmp_path: Path, source_text: str) -> None:
    source = tmp_path / "proposals.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("proposals.py",))
    monkeypatch.setattr(verifier, "REQUIRED_MARKERS", {})
    monkeypatch.setattr(verifier, "_operational_failures", lambda: [])


def test_q27_verifier_passes() -> None:
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
    ),
)
def test_q27_verifier_rejects_runtime_imports(
    monkeypatch,
    tmp_path: Path,
    source_text: str,
    runtime_ref: str,
) -> None:
    _temporary_source(monkeypatch, tmp_path, source_text)
    assert f"forbidden Q27 runtime import: {runtime_ref}" in verifier.verify()


@pytest.mark.parametrize("fragment", verifier.DENIED_AUTHORITY_FRAGMENTS)
def test_q27_verifier_rejects_authority_promotion(
    monkeypatch, tmp_path: Path, fragment: str
) -> None:
    _temporary_source(monkeypatch, tmp_path, f"payload = {fragment!r}\n")
    assert f"denied Q27 authority fragment: {fragment}" in verifier.verify()


def test_q27_verifier_reports_missing_artifact(monkeypatch, tmp_path: Path) -> None:
    _temporary_source(monkeypatch, tmp_path, "proposal_only = True\n")
    monkeypatch.setattr(
        verifier,
        "REQUIRED_FILES",
        ("proposals.py", "missing.md"),
    )
    assert "missing Q27 artifact: missing.md" in verifier.verify()


@pytest.mark.parametrize("fragment", verifier.DENIED_CLI_FRAGMENTS)
def test_q27_verifier_rejects_cli_source_reads(
    monkeypatch, tmp_path: Path, fragment: str
) -> None:
    _temporary_source(monkeypatch, tmp_path, "proposal_only = True\n")
    cli = tmp_path / "scripts" / "inspect_eco_010_proposals.py"
    cli.parent.mkdir(parents=True)
    cli.write_text(f"payload = {fragment!r}\n", encoding="utf-8")
    assert f"denied Q27 CLI source-read fragment: {fragment}" in verifier.verify()
