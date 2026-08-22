from __future__ import annotations

from pathlib import Path

import pytest

import scripts.verify_eco_009_read_only_connectors as verifier


def _temporary_source(monkeypatch, tmp_path: Path, source_text: str) -> None:
    source = tmp_path / "read_only_platform.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("read_only_platform.py",))
    monkeypatch.setattr(verifier, "REQUIRED_MARKERS", {})
    monkeypatch.setattr(verifier, "_operational_failures", lambda: [])


def test_eco_009_verifier_passes() -> None:
    assert verifier.verify() == []


@pytest.mark.parametrize(
    ("source_text", "runtime_ref"),
    (
        ("import requests\n", "requests"),
        ("import httpx as client\n", "httpx"),
        ("from urllib import request as fetch\n", "urllib.request"),
        ("from http import client as transport\n", "http.client"),
        ("from subprocess import run\n", "subprocess"),
        ("import firecrawl\n", "firecrawl"),
        ("from browserbase import Browserbase\n", "browserbase"),
    ),
)
def test_eco_009_verifier_rejects_runtime_imports(
    monkeypatch,
    tmp_path: Path,
    source_text: str,
    runtime_ref: str,
) -> None:
    _temporary_source(monkeypatch, tmp_path, source_text)
    assert f"forbidden ECO-009 runtime import: {runtime_ref}" in verifier.verify()


@pytest.mark.parametrize(
    "fragment",
    (
        "account_auth_enabled: Literal[True]",
        "background_sync_enabled: Literal[True]",
        "connector_write_enabled: Literal[True]",
        "network_access_enabled: Literal[True]",
        "production_authority_enabled: Literal[True]",
        "raw_content_enabled: Literal[True]",
        "network_access_performed: Literal[True]",
        "model_call_enabled: Literal[True]",
        "model_call_performed: Literal[True]",
    ),
)
def test_eco_009_verifier_rejects_authority_promotion(
    monkeypatch,
    tmp_path: Path,
    fragment: str,
) -> None:
    _temporary_source(monkeypatch, tmp_path, fragment)
    assert f"denied ECO-009 authority fragment: {fragment}" in verifier.verify()


def test_eco_009_verifier_reports_missing_artifact(monkeypatch, tmp_path: Path) -> None:
    _temporary_source(monkeypatch, tmp_path, "snapshot_only = True\n")
    monkeypatch.setattr(
        verifier,
        "REQUIRED_FILES",
        ("read_only_platform.py", "missing.md"),
    )
    assert "missing ECO-009 artifact: missing.md" in verifier.verify()
