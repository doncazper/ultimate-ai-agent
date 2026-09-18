"""Managed Finance discovery is frozen once at the backend launch boundary."""

from __future__ import annotations

import pytest


def _explicit(tmp_path):
    from ultimate_ai_agent.core import finance_startup as startup

    return {
        startup.FINANCE_WORKSPACE_REPOSITORY_ENV: str(tmp_path / "book"),
        startup.FINANCE_WORKSPACE_HELPER_ENV: str(tmp_path / "helper"),
        startup.FINANCE_WORKSPACE_HELPER_DIGEST_ENV: "a" * 64,
    }


@pytest.mark.parametrize("mode", ["explicit", "managed", "absent", "invalid"])
@pytest.mark.parametrize("disable", [None, "", "0", "unknown"])
def test_capture_discovers_once_and_replaces_caller_marker(monkeypatch, tmp_path, mode, disable):
    from ultimate_ai_agent.core import finance_startup as startup
    from ultimate_ai_agent.core.finance_managed_profile import FinanceConfigurationResolution

    values = _explicit(tmp_path) if mode in {"explicit", "managed"} else {}
    if disable is not None:
        values[startup.FINANCE_WORKSPACE_DISABLE_ENV] = disable
    calls = []

    def resolve(environ, layout):
        calls.append((dict(environ), layout))
        return FinanceConfigurationResolution(
            mode=mode, effective_environment=tuple(values.items()),
            repository_dir=None, helper_path=None, helper_sha256=None,
            profile_ref=None, state_ref=None, error_code=None,
        )

    monkeypatch.setattr(startup, "resolve_finance_configuration", resolve)
    incoming = {startup.FINANCE_STARTUP_MODE_ENV: "untrusted", "UNRELATED": "ignored"}
    snapshot = startup.capture_finance_startup_environment(incoming)
    assert snapshot == {**values, startup.FINANCE_STARTUP_MODE_ENV: mode}
    assert calls == [(incoming, None)]
    assert startup.finance_startup_environment({**snapshot, "UNRELATED": "ignored"}) == snapshot


@pytest.mark.parametrize("mode,extra,expected", [
    ("absent", {}, "absent"),
    ("absent", {"UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR": "/placeholder"}, "invalid"),
    ("invalid", {}, "invalid"),
    ("unknown", {}, "invalid"),
    ("", {}, "invalid"),
    ("managed", {}, "invalid"),
    ("explicit", {}, "invalid"),
])
def test_frozen_absent_invalid_or_inconsistent_mode_never_rediscovers(
    monkeypatch, mode, extra, expected,
):
    from ultimate_ai_agent.core import finance_startup as startup

    monkeypatch.setattr(startup, "resolve_finance_configuration", lambda *_args: pytest.fail("captured state must not discover"))
    resolution = startup.consume_finance_startup_environment({
        startup.FINANCE_STARTUP_MODE_ENV: mode,
        startup.FINANCE_WORKSPACE_DISABLE_ENV: "", **extra,
    })
    assert resolution.mode == expected
    assert dict(resolution.effective_environment)[startup.FINANCE_WORKSPACE_DISABLE_ENV] == ""
    assert resolution.repository_dir is None
    assert resolution.helper_path is None


@pytest.mark.parametrize("mode", ["explicit", "managed"])
@pytest.mark.parametrize("invalid", [None, "empty", "relative", "nul", "digest"])
def test_captured_configuration_uses_structural_grammar_without_disk_lookup(
    monkeypatch, tmp_path, mode, invalid,
):
    from ultimate_ai_agent.core import finance_managed_profile as profile
    from ultimate_ai_agent.core import finance_startup as startup

    values = _explicit(tmp_path)
    if invalid == "empty":
        values[startup.FINANCE_WORKSPACE_HELPER_ENV] = ""
    elif invalid == "relative":
        values[startup.FINANCE_WORKSPACE_REPOSITORY_ENV] = "relative"
    elif invalid == "nul":
        values[startup.FINANCE_WORKSPACE_HELPER_ENV] += "\x00suffix"
    elif invalid == "digest":
        values[startup.FINANCE_WORKSPACE_HELPER_DIGEST_ENV] = "A" * 64
    monkeypatch.setattr(profile, "default_finance_managed_layout", lambda: pytest.fail("explicit snapshot must not discover home"))
    monkeypatch.setattr(profile, "read_managed_profile", lambda *_args: pytest.fail("explicit snapshot must not read profile"))
    resolution = startup.consume_finance_startup_environment({**values, startup.FINANCE_STARTUP_MODE_ENV: mode})
    assert resolution.mode == (mode if invalid is None else "invalid")
    assert dict(resolution.effective_environment) == values


def test_unmarked_consumer_discovers_but_marked_workspace_does_not(monkeypatch, tmp_path):
    from ultimate_ai_agent.core import finance_startup as startup
    from ultimate_ai_agent.core.finance.workspace import FinanceWorkspace
    from ultimate_ai_agent.core.finance_managed_profile import FinanceManagedLayout

    layout = FinanceManagedLayout(root=tmp_path / "absent-managed")
    actual = startup.consume_finance_startup_environment({}, layout)
    assert actual.mode == "absent"
    for name in startup.FINANCE_STARTUP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(startup.FINANCE_STARTUP_MODE_ENV, "absent")
    monkeypatch.setattr(startup, "resolve_finance_configuration", lambda *_args: pytest.fail("running absent backend must stay absent"))
    assert FinanceWorkspace.from_env().configuration_error == "configuration_missing"
    monkeypatch.setenv(startup.FINANCE_STARTUP_MODE_ENV, "invalid")
    assert FinanceWorkspace.from_env().configuration_error == "configuration_invalid"
    assert not layout.root.exists()


def test_packaged_snapshot_transport_does_not_recapture(monkeypatch, tmp_path):
    from ultimate_ai_agent.core import finance_startup as startup
    from ultimate_ai_agent.distribution.macos import runtime

    snapshot = {**_explicit(tmp_path), startup.FINANCE_STARTUP_MODE_ENV: "managed"}
    monkeypatch.setattr(runtime, "capture_finance_startup_environment", lambda *_args: pytest.fail("already captured"))
    environment = runtime._runtime_environment(
        local_bearer="owned-test-bearer", source_commit="a" * 40,
        finance_environment=snapshot,
    )
    assert startup.finance_startup_environment(environment) == snapshot


@pytest.mark.parametrize("foreign", [None, "ultimate_ai_agent", "ultimate_ai_agent.core", "ultimate_ai_agent.core.finance_managed_profile"])
def test_plain_launcher_checks_preloaded_origins_and_restores_search_path(tmp_path, foreign):
    import json
    from pathlib import Path
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    code = r'''
import importlib.util, json, sys, types
from pathlib import Path
root, foreign = Path(sys.argv[1]), json.loads(sys.argv[2])
def deny_native_lookup(event, args):
    if event == 'ctypes.dlopen':
        raise AssertionError('plain startup import attempted native library lookup')
sys.addaudithook(deny_native_lookup)
spec = importlib.util.spec_from_file_location('owned_launcher', root/'scripts/dev/uaa_launcher.py')
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)
if foreign:
    module = types.ModuleType(foreign)
    module.__file__ = str(Path.cwd()/'foreign.py')
    module.__spec__ = importlib.util.spec_from_file_location(foreign, module.__file__)
    sys.modules[foreign] = module
before_path = list(sys.path)
before_modules = set(sys.modules)
if foreign:
    try:
        launcher._load_finance_startup_module()
    except RuntimeError:
        pass
    else:
        raise AssertionError('foreign module was accepted')
    assert not any(name.startswith('ultimate_ai_agent') for name in set(sys.modules)-before_modules)
else:
    contract = launcher._load_finance_startup_module()
    assert Path(contract.__file__).resolve() == root/'src/ultimate_ai_agent/core/finance_startup.py'
    assert 'pydantic' not in sys.modules
    assert 'ultimate_ai_agent.core.finance' not in sys.modules
assert sys.path == before_path
'''
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", code, str(root), json.dumps(foreign)],
        cwd=tmp_path, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
