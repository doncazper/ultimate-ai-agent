from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.verification import resolve_ci_visual_scope as resolver


SHA = "a" * 40
BASE_SHA = "b" * 40


@pytest.mark.parametrize(
    ("paths", "expected"),
    (
        (b"src/ultimate_ai_agent/api/app.py\0", "not_affected"),
        (b"apps/control-center/src/App.tsx\0", "affected"),
        (b"docs/control_center/PRODUCT_LANGUAGE_RULES.md\0", "affected"),
    ),
)
def test_visual_scope_is_exact_diff_derived(
    monkeypatch: pytest.MonkeyPatch,
    paths: bytes,
    expected: str,
) -> None:
    monkeypatch.setattr(
        resolver.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=("git",), returncode=0, stdout=paths, stderr=b""
        ),
    )

    assert resolver.resolve_visual_scope(Path("."), BASE_SHA, SHA) == expected


@pytest.mark.parametrize("payload", (b"unsafe\npath\0", b"\xff\0"))
def test_visual_scope_rejects_unsafe_changed_path_evidence(
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
) -> None:
    monkeypatch.setattr(
        resolver.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=("git",), returncode=0, stdout=payload, stderr=b""
        ),
    )

    with pytest.raises(ValueError):
        resolver.resolve_visual_scope(Path("."), BASE_SHA, SHA)


def test_visual_scope_output_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text("unchanged", encoding="ascii")
    target.chmod(0o600)
    output = tmp_path / "github-output"
    output.symlink_to(target)

    with pytest.raises(OSError):
        resolver.append_scope_output(output, "affected")

    assert target.read_text(encoding="ascii") == "unchanged"


def test_visual_scope_output_appends_to_owner_only_regular_file(tmp_path: Path) -> None:
    output = tmp_path / "github-output"
    output.write_text("prior=value\n", encoding="ascii")
    output.chmod(0o600)

    resolver.append_scope_output(output, "not_affected")

    assert output.read_text(encoding="ascii") == (
        "prior=value\nvisual_scope=not_affected\n"
    )
