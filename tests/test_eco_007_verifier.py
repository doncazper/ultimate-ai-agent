from __future__ import annotations

import pytest

import scripts.verify_eco_007_inbox as verifier


def _use_temporary_source(monkeypatch, tmp_path, source_text: str) -> None:
    source = tmp_path / "inbox.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "INBOX_SOURCE", "inbox.py")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("inbox.py",))
    monkeypatch.setattr(verifier, "ROOT", tmp_path)
    monkeypatch.setattr(verifier, "_operational_failures", lambda: [])


def test_eco_007_verifier_passes() -> None:
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
        ("import playwright.sync_api\n", "playwright"),
        ("from selenium import webdriver\n", "selenium"),
        ("import importlib as loader\nloader.import_module('requests')\n", "requests"),
        ("__import__('subprocess')\n", "subprocess"),
    ),
)
def test_eco_007_verifier_rejects_runtime_imports_and_aliases(
    monkeypatch, tmp_path, source_text: str, runtime_ref: str
) -> None:
    _use_temporary_source(monkeypatch, tmp_path, source_text)
    assert f"forbidden ECO-007 runtime ref: {runtime_ref}" in verifier.verify()


def test_eco_007_verifier_rejects_authority_fragments(monkeypatch, tmp_path) -> None:
    _use_temporary_source(
        monkeypatch, tmp_path, "target_write_performed: Literal[True]\n"
    )
    assert (
        "denied ECO-007 authority fragment: target_write_performed: Literal[True]"
        in verifier.verify()
    )


def test_eco_007_verifier_reports_missing_artifacts(monkeypatch, tmp_path) -> None:
    _use_temporary_source(monkeypatch, tmp_path, "proposal_only = True\n")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("inbox.py", "missing.md"))
    assert "missing ECO-007 artifact: missing.md" in verifier.verify()
