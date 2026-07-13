from __future__ import annotations

import json
import subprocess

from scripts.verification import run_private_affected_preflight as preflight
from scripts.verification.changed_path_selector import (
    FULL_COMMAND_REF as SELECTOR_FULL_COMMAND_REF,
)


def completed(payload: object, *, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=("selector",),
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr="",
    )


def test_affected_preflight_executes_narrow_selection(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_selector(_base_ref: str, *, execute: bool):
        calls.append(execute)
        return completed(
            {"selected_command_refs": ["command-ref:documentation-integrity"]}
        )

    monkeypatch.setattr(preflight, "_selector", fake_selector)
    assert preflight.run("origin/main") == 0
    assert calls == [False, True]


def test_affected_preflight_does_not_duplicate_selected_full_gate(monkeypatch) -> None:
    assert preflight.FULL_COMMAND_REF == SELECTOR_FULL_COMMAND_REF
    calls: list[bool] = []

    def fake_selector(_base_ref: str, *, execute: bool):
        calls.append(execute)
        return completed(
            {"selected_command_refs": [preflight.FULL_COMMAND_REF]}
        )

    monkeypatch.setattr(preflight, "_selector", fake_selector)
    assert preflight.run("origin/main") == 0
    assert calls == [False]


def test_affected_preflight_fails_closed_to_following_full_gate(monkeypatch) -> None:
    monkeypatch.setattr(
        preflight,
        "_selector",
        lambda _base_ref, *, execute: completed({}, returncode=2),
    )
    assert preflight.run("origin/main") == 0
