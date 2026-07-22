from __future__ import annotations

import os
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


def test_visual_scope_output_rejects_symlinked_parent(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    output = real_parent / "github-output"
    output.write_text("unchanged", encoding="ascii")
    output.chmod(0o600)
    symlinked_parent = tmp_path / "linked-parent"
    symlinked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(OSError):
        resolver.append_scope_output(symlinked_parent / output.name, "affected")

    assert output.read_text(encoding="ascii") == "unchanged"


def test_visual_scope_output_rejects_writable_nonsticky_parent(
    tmp_path: Path,
) -> None:
    writable_parent = tmp_path / "writable-parent"
    writable_parent.mkdir()
    writable_parent.chmod(0o777)
    output = writable_parent / "github-output"
    output.write_text("unchanged", encoding="ascii")
    output.chmod(0o644)

    with pytest.raises(ValueError):
        resolver.append_scope_output(output, "affected")

    assert output.read_text(encoding="ascii") == "unchanged"


def test_visual_scope_output_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    output = tmp_path / "github-output"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    os.mkfifo(output, mode=0o600)

    with pytest.raises(OSError):
        resolver.append_scope_output(output, "affected")


@pytest.mark.parametrize("mode", (0o600, 0o644))
def test_visual_scope_output_appends_to_owner_controlled_regular_file(
    tmp_path: Path,
    mode: int,
) -> None:
    output = tmp_path / "github-output"
    output.write_text("prior=value\n", encoding="ascii")
    output.chmod(mode)

    resolver.append_scope_output(output, "not_affected")

    assert output.read_text(encoding="ascii") == (
        "prior=value\nvisual_scope=not_affected\n"
    )


@pytest.mark.parametrize("mode", (0o620, 0o602, 0o666))
def test_visual_scope_output_rejects_group_or_other_writable_file(
    tmp_path: Path,
    mode: int,
) -> None:
    output = tmp_path / "github-output"
    output.write_text("unchanged\n", encoding="ascii")
    output.chmod(mode)

    with pytest.raises(ValueError):
        resolver.append_scope_output(output, "affected")

    assert output.read_text(encoding="ascii") == "unchanged\n"
