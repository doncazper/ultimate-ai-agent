from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import verification_environment_preflight as preflight


@pytest.fixture(autouse=True)
def _complete_npm_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        preflight.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0),
    )


def _runtime_file(root: Path, relative: Path) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")


def test_pytest_preflight_accepts_complete_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    _runtime_file(repo, preflight.MATRIX_RUNTIME_MARKER)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/node")

    assert preflight.validate_lane_environment(
        repo,
        temp_root,
        lane_ref="ci-pytest-shards",
    ) == (
        "preflight-ref:temp-capacity-and-write-ready",
        "preflight-ref:python-runtime-3.12-ready",
        "preflight-ref:pytest-runtime-ready",
        "preflight-ref:matrix-runtime-ready",
    )


def test_pytest_preflight_rejects_noncanonical_python_before_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    monkeypatch.setattr(preflight.sys, "version_info", (3, 13))

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="python-runtime-version-mismatch",
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref="ci-pytest-shards",
        )


def test_pytest_preflight_rejects_missing_matrix_runtime_before_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/node")

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="matrix-runtime-unavailable",
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref="ci-pytest-shards",
        )


def test_frontend_preflight_rejects_symlink_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    target = repo / "tsc-target"
    target.write_text("runtime\n", encoding="utf-8")
    marker = repo / preflight.FRONTEND_RUNTIME_MARKER
    marker.parent.mkdir(parents=True)
    marker.symlink_to(target)
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/node")

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="frontend-runtime-unavailable",
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref="ci-control-center-frontend",
        )


def test_frontend_preflight_accepts_regular_typescript_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    for marker in preflight.FRONTEND_RUNTIME_MARKERS:
        _runtime_file(repo, marker)
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/node")

    assert preflight.validate_lane_environment(
        repo,
        temp_root,
        lane_ref="ci-control-center-frontend",
    ) == (
        "preflight-ref:temp-capacity-and-write-ready",
        "preflight-ref:frontend-runtime-ready",
    )


@pytest.mark.parametrize(
    ("lane_ref", "runtime_root", "runtime_markers", "reason"),
    (
        (
            "ci-pytest-shards",
            preflight.MATRIX_RUNTIME_ROOT,
            (preflight.MATRIX_RUNTIME_MARKER,),
            "matrix-runtime-unavailable",
        ),
        (
            "ci-control-center-frontend",
            preflight.FRONTEND_RUNTIME_ROOT,
            preflight.FRONTEND_RUNTIME_MARKERS,
            "frontend-runtime-unavailable",
        ),
    ),
)
def test_preflight_rejects_incomplete_frozen_dependency_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane_ref: str,
    runtime_root: Path,
    runtime_markers: tuple[Path, ...],
    reason: str,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    for marker in runtime_markers:
        _runtime_file(repo, marker)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(preflight.shutil, "which", lambda name: f"/usr/bin/{name}")
    observed: dict[str, object] = {}

    def reject_tree(command: object, **kwargs: object) -> SimpleNamespace:
        observed["command"] = command
        observed["cwd"] = kwargs.get("cwd")
        observed["stdout"] = kwargs.get("stdout")
        observed["stderr"] = kwargs.get("stderr")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(preflight.subprocess, "run", reject_tree)

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match=reason,
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref=lane_ref,
        )

    assert observed["cwd"] == repo / runtime_root
    assert tuple(observed["command"])[1:] == (
        "ls",
        "--all",
        "--offline",
        "--ignore-scripts",
        "--json",
    )
    assert observed["stdout"] is preflight.subprocess.DEVNULL
    assert observed["stderr"] is preflight.subprocess.DEVNULL


@pytest.mark.parametrize("missing_marker", preflight.FRONTEND_RUNTIME_MARKERS)
def test_frontend_preflight_rejects_each_missing_frozen_tool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_marker: Path,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    for marker in preflight.FRONTEND_RUNTIME_MARKERS:
        if marker != missing_marker:
            _runtime_file(repo, marker)
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: "/usr/bin/tool")

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="frontend-runtime-unavailable",
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref="ci-control-center-frontend",
        )


@pytest.mark.parametrize(
    ("lane_ref", "runtime_marker"),
    (
        ("ci-pytest-shards", preflight.MATRIX_RUNTIME_MARKER),
        ("ci-control-center-frontend", preflight.FRONTEND_RUNTIME_MARKER),
    ),
)
def test_exclusive_preflight_rejects_missing_npm_before_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    lane_ref: str,
    runtime_marker: Path,
) -> None:
    repo = tmp_path / "repo"
    temp_root = tmp_path / "temp"
    repo.mkdir()
    temp_root.mkdir()
    _runtime_file(repo, runtime_marker)
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(
        preflight.shutil,
        "which",
        lambda name: "/usr/bin/node" if name == "node" else None,
    )

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="npm-runtime-unavailable",
    ):
        preflight.validate_lane_environment(
            repo,
            temp_root,
            lane_ref=lane_ref,
        )


def test_preflight_rejects_insufficient_temp_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    usage = SimpleNamespace(total=1, used=1, free=0)
    monkeypatch.setattr(preflight.shutil, "disk_usage", lambda _path: usage)

    with pytest.raises(
        preflight.VerificationEnvironmentPreflightError,
        match="temp-capacity-insufficient",
    ):
        preflight.validate_lane_environment(
            tmp_path,
            tmp_path,
            lane_ref="ci-lint",
        )
