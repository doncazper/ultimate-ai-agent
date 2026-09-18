"""The installer bootstrap carries its exact stdlib-only startup closure."""

from __future__ import annotations

import pytest


@pytest.fixture
def copied_bootstrap(tmp_path, monkeypatch):
    import importlib.util
    import tarfile
    from pathlib import Path

    source_root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "bootstrap_startup_dependency_builder",
        source_root / "scripts" / "macos" / "build_installer_bootstrap.py",
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    python_runtime = tmp_path / "python-runtime"
    (python_runtime / "bin").mkdir(parents=True)
    (python_runtime / "bin" / "python3").write_bytes(b"test interpreter placeholder")
    monkeypatch.setattr(
        builder, "_purelib", lambda python: python.parent.parent / "site-packages"
    )
    monkeypatch.setattr(builder, "_sign_macho_tree", lambda *_args, **_kwargs: None)
    output = tmp_path / "output"
    builder.build_bootstrap(
        source_root=source_root,
        python_runtime=python_runtime,
        output_dir=output,
        architecture="arm64",
        signing_identity=None,
    )
    extracted = tmp_path / "extracted"
    with tarfile.open(output / "uaa-installer-macos-arm64.tar.gz", "r:gz") as archive:
        archive.extractall(extracted, filter="data")
    return source_root, extracted / "bootstrap" / "python" / "site-packages"


@pytest.mark.parametrize(
    ("arguments", "expected_status", "expected_text"),
    [
        (["--help"], 0, "Ultimate AI Agent first-class macOS app and CLI"),
        (["version"], 1, "not-installed"),
        (["status", "--json"], 0, '"installed": false'),
    ],
)
def test_copied_bootstrap_runs_without_checkout_or_dependencies(
    copied_bootstrap, tmp_path, arguments, expected_status, expected_text
):
    import json
    import subprocess
    import sys

    _source_root, purelib = copied_bootstrap
    unrelated_cwd = tmp_path / "unrelated"
    unrelated_cwd.mkdir()
    install_root = tmp_path / "never-created-installation"
    owned_bin = tmp_path / ".local" / "bin"
    owned_bin.mkdir(parents=True)
    owned_gh = owned_bin / "gh"
    owned_gh.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
    owned_gh.chmod(0o700)
    # -I ignores user site/PYTHONPATH/cwd; -S excludes site-packages. Only this
    # extracted bootstrap package is added to the interpreter's stdlib paths.
    runner = """
import os
import runpy
import sys

def deny_side_effects(event, args):
    if event.startswith('socket.') or event in {
        'subprocess.Popen', 'os.system', 'os.mkdir', 'os.remove', 'os.rmdir',
        'os.rename', 'os.chmod', 'os.chown', 'os.link', 'os.symlink', 'os.truncate',
    }:
        raise AssertionError('bootstrap inspection attempted a side effect')
    if event == 'open':
        flags = args[2]
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError('bootstrap inspection attempted a file write')

sys.addaudithook(deny_side_effects)
sys.path.insert(0, sys.argv[1])
from ultimate_ai_agent.distribution.macos import github_releases

assert str(github_releases._find_gh(dict(os.environ))) == os.path.join(
    os.environ['HOME'], '.local', 'bin', 'gh'
)
# Optional host authentication is outside this copied-import dependency check.
# Keep subprocess denial active even though an owned gh executable is available.
github_releases._find_gh = lambda _environ: None
sys.argv = ['uaa', *sys.argv[2:]]
runpy.run_module('ultimate_ai_agent.distribution.macos.runtime', run_name='__main__')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", runner, str(purelib), *arguments],
        cwd=unrelated_cwd,
        env={
            "HOME": str(tmp_path),
            "PATH": str(owned_bin),
            "UAA_INSTALL_ROOT": str(install_root),
        },
        text=True,
        capture_output=True,
        timeout=15.0,
        check=False,
    )

    assert completed.stderr == "", completed.stderr
    assert completed.returncode == expected_status
    assert expected_text in completed.stdout
    if arguments == ["status", "--json"]:
        assert json.loads(completed.stdout)["github_auth_available"] is False
    assert not install_root.exists()
    assert not tuple(purelib.rglob("__pycache__"))


def test_bootstrap_copies_only_exact_core_startup_sources(copied_bootstrap):
    source_root, purelib = copied_bootstrap
    copied_core = purelib / "ultimate_ai_agent" / "core"

    assert sorted(path.name for path in copied_core.iterdir()) == [
        "__init__.py",
        "finance_managed_profile.py",
        "finance_startup.py",
        "private_path_security.py",
    ]
    for name in ("__init__.py", "finance_startup.py", "finance_managed_profile.py", "private_path_security.py"):
        assert (copied_core / name).read_bytes() == (
            source_root / "src" / "ultimate_ai_agent" / "core" / name
        ).read_bytes()
