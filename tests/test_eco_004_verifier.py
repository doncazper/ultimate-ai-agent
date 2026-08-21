from __future__ import annotations

import pytest

import scripts.verify_eco_004_calendar as verifier


def test_eco_004_verifier_passes() -> None:
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
        ("import schedule as scheduler\nscheduler.run_pending()\n", "schedule"),
    ),
)
def test_eco_004_verifier_rejects_forbidden_runtime_imports_and_aliases(
    monkeypatch, tmp_path, source_text: str, runtime_ref: str
) -> None:
    source = tmp_path / "calendar.py"
    source.write_text(source_text, encoding="utf-8")
    monkeypatch.setattr(verifier, "REQUIRED_FILES", ("calendar.py",) * 4)
    monkeypatch.setattr(verifier, "ROOT", tmp_path)

    failures = verifier.verify()

    assert f"forbidden ECO-004 runtime ref: {runtime_ref}" in failures
