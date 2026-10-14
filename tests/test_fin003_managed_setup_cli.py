"""Both command lines use Core setup; preparation files remain untrusted."""

from __future__ import annotations

import pytest


def _repo_cli():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts/dev/uaa_finance.py"
    spec = importlib.util.spec_from_file_location("managed_setup_repo_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installer_bootstrap_missing_finance_core_returns_bounded_error(monkeypatch, capsys):
    import builtins
    import json
    from ultimate_ai_agent.distribution.macos import runtime

    original = builtins.__import__

    def without_finance(name, *args, **kwargs):
        if name == "ultimate_ai_agent.core.finance.managed_setup":
            raise ModuleNotFoundError("untrusted-private-import-detail")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_finance)
    assert runtime.command_finance_setup(runtime.parse_args(["finance-setup", "inspect"])) == 2
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "untrusted-private-import-detail" not in captured.out
    assert json.loads(captured.out) == {
        "schema_version": "uaa-finance-managed-setup-cli-error.v1",
        "ok": False,
        "error_code": "FIN003_MANAGED_REQUEST_FAILED",
        "raw_input_included": False,
    }


@pytest.mark.parametrize("source", ["installed", "developer-artifact"])
def test_both_cli_inspections_share_core_without_source_lookup_or_writes(monkeypatch, tmp_path, capsys, source):
    import json
    from ultimate_ai_agent.core import finance_managed_profile as profile
    from ultimate_ai_agent.distribution.macos import installer, runtime

    layout = profile.FinanceManagedLayout(root=tmp_path / "managed")
    monkeypatch.setattr(profile, "default_finance_managed_layout", lambda: layout)
    for name in profile.FINANCE_CONFIGURATION_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(installer, "verified_installed_finance_helper", lambda *_args: pytest.fail("inspection must not inspect source"))
    monkeypatch.setattr(installer, "verified_developer_finance_helper", lambda *_args: pytest.fail("inspection must not inspect source"))
    monkeypatch.setattr(runtime, "command_update", lambda *_args, **_kwargs: pytest.fail("setup must not update"))
    assert runtime.main(["finance-setup", "inspect"]) == 0
    installed = json.loads(capsys.readouterr().out)
    cli = _repo_cli()
    args = cli.parser().parse_args(["setup-inspect", "--helper-source", source])
    assert args.func(args) == 0
    assert json.loads(capsys.readouterr().out) == installed
    assert installed["status"] == "missing"
    assert not layout.root.exists()


@pytest.mark.parametrize("action", ["prepare", "refresh", "run"])
def test_cli_parsers_share_exact_operation_and_confirmation_shape(action):
    from ultimate_ai_agent.distribution.macos import runtime

    options = (["--operation", "enroll", "--request-ref", "request-ref:finance:setup", "--idempotency-ref", "idempotency-ref:finance:setup"]
        if action == "prepare" else ["--bundle", "preparation.json"])
    installed = runtime.parse_args(["finance-setup", action, *options])
    repo = _repo_cli().parser().parse_args(["setup-" + action, *options])
    for name in ("setup_command", "operation", "request_ref", "idempotency_ref", "bundle", "confirmed"):
        assert getattr(installed, name, None) == getattr(repo, name, None)
    if action == "run":
        assert installed.confirmed is False
    with pytest.raises(SystemExit):
        runtime.parse_args(["finance-setup", action, *options, "--helper-path", "/unselected"])


def test_preparation_reader_accepts_only_bounded_private_regular_bytes(tmp_path):
    from ultimate_ai_agent.distribution.macos.runtime import _read_finance_setup_bundle

    path = tmp_path / "preparation.json"
    path.write_bytes(b'{"untrusted":"syntax validation belongs to Core"}')
    path.chmod(0o600)
    before = tuple(tmp_path.iterdir())
    assert _read_finance_setup_bundle(path) == path.read_bytes()
    assert tuple(tmp_path.iterdir()) == before


@pytest.mark.parametrize("kind", ["missing", "empty", "oversize", "readable", "link", "hardlink", "fifo", "directory"])
def test_preparation_reader_rejects_invalid_files_without_open_side_effects(tmp_path, kind):
    import os
    from ultimate_ai_agent.core.finance.managed_setup_authority import MANAGED_SETUP_PREPARATION_MAX_BYTES, ManagedFinanceSetupError
    from ultimate_ai_agent.distribution.macos.runtime import _read_finance_setup_bundle

    path = tmp_path / "preparation.json"
    if kind == "directory":
        path.mkdir(mode=0o700)
    elif kind == "fifo":
        os.mkfifo(path, 0o600)
    elif kind == "link":
        target = tmp_path / "target"
        target.write_bytes(b"{}")
        target.chmod(0o600)
        path.symlink_to(target)
    elif kind != "missing":
        path.write_bytes(b"" if kind == "empty" else b"x" * (MANAGED_SETUP_PREPARATION_MAX_BYTES + 1) if kind == "oversize" else b"{}")
        path.chmod(0o644 if kind == "readable" else 0o600)
        if kind == "hardlink":
            os.link(path, tmp_path / "second-name")
    with pytest.raises(ManagedFinanceSetupError, match="^FIN003_MANAGED_BUNDLE_FILE_INVALID$"):
        _read_finance_setup_bundle(path)


def test_preparation_leaf_swap_after_nofollow_stat_is_rejected(monkeypatch, tmp_path):
    import os
    from ultimate_ai_agent.core.finance.managed_setup_authority import ManagedFinanceSetupError
    from ultimate_ai_agent.distribution.macos import runtime

    path = tmp_path / "preparation.json"
    target = tmp_path / "other"
    path.write_bytes(b"{}")
    target.write_bytes(b"{}")
    path.chmod(0o600)
    target.chmod(0o600)
    original = os.open
    swapped = False

    def open_swapped(name, flags, *args, **kwargs):
        nonlocal swapped
        if name == path.name and kwargs.get("dir_fd") is not None and not swapped:
            swapped = True
            path.unlink()
            path.symlink_to(target)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(runtime.os, "open", open_swapped)
    monkeypatch.setattr(runtime.os, "supports_dir_fd", {*os.supports_dir_fd, open_swapped})
    with pytest.raises(ManagedFinanceSetupError, match="^FIN003_MANAGED_BUNDLE_FILE_INVALID$"):
        runtime._read_finance_setup_bundle(path)
    assert swapped
    assert target.read_bytes() == b"{}"


def test_cli_failure_does_not_echo_untrusted_bundle_or_exception_text(monkeypatch, tmp_path, capsys):
    import json
    from ultimate_ai_agent.core import finance_managed_profile as profile
    from ultimate_ai_agent.distribution.macos import runtime

    monkeypatch.setattr(profile, "default_finance_managed_layout", lambda: profile.FinanceManagedLayout(root=tmp_path / "managed"))
    path = tmp_path / "preparation.json"
    path.write_bytes(b'{"untrusted":"PRIVATE_MARKER_NOT_FOR_ERROR"}')
    path.chmod(0o600)
    assert runtime.main(["finance-setup", "run", "--bundle", str(path)]) == 2
    output = capsys.readouterr()
    assert output.err == ""
    assert "PRIVATE_MARKER_NOT_FOR_ERROR" not in output.out
    assert str(path) not in output.out
    parsed = json.loads(output.out)
    assert parsed["error_code"].startswith("FIN003_MANAGED_")
    assert parsed["raw_input_included"] is False
    assert not (tmp_path / "managed").exists()
