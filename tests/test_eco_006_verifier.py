from __future__ import annotations

import pytest

import scripts.verify_eco_006_today as verifier


def _use_temporary_source(monkeypatch, tmp_path, source_text: str) -> None:
    source = tmp_path / "today.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "PROJECTION_SOURCE", "today.py")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("today.py",))
    monkeypatch.setattr(verifier, "ROOT", tmp_path)


def test_eco_006_verifier_passes() -> None:
    assert verifier.verify() == []


@pytest.mark.parametrize(
    ("source_text", "runtime_ref"),
    (
        ("import requests\nrequests.get('https://example.invalid')\n", "requests"),
        ("import httpx as client\nclient.get('https://example.invalid')\n", "httpx"),
        (
            "from urllib import request as fetch\nfetch.urlopen('https://example.invalid')\n",
            "urllib.request",
        ),
        ("import urllib3 as pool\npool.PoolManager()\n", "urllib3"),
        (
            "from http import client as http_client\nhttp_client.HTTPConnection('example.invalid')\n",
            "http.client",
        ),
        ("from subprocess import run as execute\nexecute(('true',))\n", "subprocess"),
        ("from urllib import request as fetch\nhandler = fetch\n", "urllib.request"),
        (
            "import importlib as loader\nloader.import_module('requests')\n",
            "requests",
        ),
        ("__import__('subprocess')\n", "subprocess"),
    ),
)
def test_eco_006_verifier_rejects_forbidden_runtime_imports_and_aliases(
    monkeypatch, tmp_path, source_text: str, runtime_ref: str
) -> None:
    _use_temporary_source(monkeypatch, tmp_path, source_text)

    failures = verifier.verify()

    assert f"forbidden ECO-006 runtime ref: {runtime_ref}" in failures


def test_eco_006_verifier_rejects_denied_authority_fragments(
    monkeypatch, tmp_path
) -> None:
    _use_temporary_source(monkeypatch, tmp_path, "mutation_authorized=True\n")

    failures = verifier.verify()

    assert "denied ECO-006 authority fragment: mutation_authorized=True" in failures


def test_eco_006_verifier_reports_missing_artifacts(monkeypatch, tmp_path) -> None:
    _use_temporary_source(monkeypatch, tmp_path, "projection_only = True\n")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("today.py", "missing.md"))

    failures = verifier.verify()

    assert "missing ECO-006 artifact: missing.md" in failures
