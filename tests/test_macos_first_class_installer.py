from __future__ import annotations

import io
import json
import os
import plistlib
import stat
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.macos.build_release_bundle import (
    _launcher_source,
    build_release_bundle,
)
from scripts.macos.release_policy import classify_tag
from scripts.macos.verify_installer_e2e import (
    InstallerE2EError,
    validate_receipts,
    validate_status_payload,
)
from ultimate_ai_agent.distribution.macos.static_policy import (
    MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES,
    macos_distribution_adapter_policy_failures,
    macos_distribution_policy_failures,
    macos_distribution_static_fragment_allowed,
)
from ultimate_ai_agent.distribution.macos.contracts import (
    APP_BUNDLE_IDENTIFIER,
    APP_BUNDLE_NAME,
    BUNDLE_MANIFEST_SCHEMA,
    MINIMUM_MACOS,
    PRODUCT_LINE,
    RELEASE_DESCRIPTOR_SCHEMA,
    ReleaseCandidate,
    ReleaseDescriptor,
    select_release,
    sha256_file,
)
from ultimate_ai_agent.distribution.macos.github_releases import GitHubReleaseClient
from ultimate_ai_agent.distribution.macos.installer import (
    APP_MANAGED_MARKER,
    CLI_MARKER,
    InstallError,
    InstallLayout,
    current_manifest,
    current_version_id,
    install_archive,
    rollback,
    safe_extract_archive,
    _select_applications_dir,
)
from ultimate_ai_agent.distribution.macos.runtime import (
    RuntimePaths,
    _runtime_environment,
    check_for_update,
    command_launch,
)


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_launcher_binds_the_exact_build_revision() -> None:
    commit = "a" * 40

    launcher = _launcher_source(commit)

    assert f'setenv("UAA_BUILD_COMMIT", "{commit}", 1)' in launcher
    with pytest.raises(ValueError, match="exact lowercase SHA"):
        _launcher_source("not-a-commit")


def test_packaged_runtime_child_uses_the_manifest_source_revision(
    monkeypatch,
) -> None:
    manifest_commit = "a" * 40
    monkeypatch.setenv("UAA_BUILD_COMMIT", "b" * 40)

    environment = _runtime_environment(
        local_bearer="local-session-bearer",
        source_commit=manifest_commit,
    )

    assert environment["UAA_BUILD_COMMIT"] == manifest_commit
    assert environment["UAA_API_LOCAL_BEARER"] == "local-session-bearer"
    with pytest.raises(RuntimeError, match="source revision"):
        _runtime_environment(
            local_bearer="local-session-bearer",
            source_commit="not-a-commit",
        )


def test_launch_replaces_live_runtime_from_superseded_install(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_METADATA_KEY,
        finance_startup_configuration_ref,
    )

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    paths.runtime_state.write_text("{}", encoding="utf-8")
    old_state = {
        "pid": 111,
        "port": 8765,
        "nonce": "old-runtime-nonce",
        "version_ref": "macos-version:old-version",
        FINANCE_STARTUP_METADATA_KEY: finance_startup_configuration_ref(os.environ),
    }
    terminated: list[dict[str, object]] = []
    written_states: list[dict[str, object]] = []
    process = SimpleNamespace(pid=222, poll=lambda: None)

    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._ensure_local_bearer",
        lambda _paths: "local-session-bearer",
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime.current_manifest",
        lambda _layout: {
            "source_commit": "a" * 40,
            "tag": "v0.104.0",
        },
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime.current_version_id",
        lambda _layout: "new-version",
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._load_runtime_state",
        lambda _paths: old_state,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._runtime_identity_matches",
        lambda _state: True,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._terminate_owned_process",
        lambda state: terminated.append(dict(state)) or True,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._next_available_port",
        lambda _host, _port: 8766,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._runtime_environment",
        lambda **_kwargs: {"PATH": "/usr/bin"},
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime.subprocess.Popen",
        lambda *_args, **_kwargs: process,
    )
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.runtime._write_json",
        lambda _path, state, **_kwargs: written_states.append(dict(state)),
    )

    result = command_launch(paths, skip_update=True, no_browser=True)

    assert result == 0
    assert terminated == [old_state]
    assert written_states[-1]["status"] == "ready"
    assert written_states[-1]["version_ref"] == "macos-version:new-version"


@pytest.mark.parametrize("disable_value", ["", "unknown", "false", "1"])
def test_packaged_runtime_preserves_only_exact_finance_configuration(
    monkeypatch, tmp_path: Path, disable_value: str
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_WORKSPACE_DISABLE_ENV,
        FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
        FINANCE_WORKSPACE_HELPER_ENV,
        FINANCE_WORKSPACE_REPOSITORY_ENV,
        finance_startup_environment,
    )

    expected = {
        FINANCE_WORKSPACE_REPOSITORY_ENV: str(tmp_path / "sample-book"),
        FINANCE_WORKSPACE_HELPER_ENV: str(tmp_path / "sample-helper"),
        FINANCE_WORKSPACE_HELPER_DIGEST_ENV: "invalid-digest-remains-invalid",
        FINANCE_WORKSPACE_DISABLE_ENV: disable_value,
    }
    for name, value in expected.items():
        monkeypatch.setenv(name, value)
    for name in ["UAA_FINANCE_CRYPTO_BACKEND", "UAA_FINANCE_EXTRA", "UNRELATED_TOKEN"]:
        monkeypatch.setenv(name, "must-not-pass")
    environment = _runtime_environment(local_bearer="local-session-bearer", source_commit="a" * 40)
    assert finance_startup_environment(environment) == expected
    assert not any(name in environment for name in [
        "UAA_FINANCE_CRYPTO_BACKEND", "UAA_FINANCE_EXTRA", "UNRELATED_TOKEN"
    ])
    assert not (tmp_path / "sample-book").exists()


@pytest.mark.parametrize("recorded", ["matching", "missing", "malformed", "changed"])
def test_packaged_finance_reuse_preserves_binding_and_stop(
    monkeypatch, tmp_path: Path, capsys, recorded: str
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_ENV_NAMES,
        FINANCE_STARTUP_METADATA_KEY,
        FINANCE_WORKSPACE_DISABLE_ENV,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    for name in FINANCE_STARTUP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(FINANCE_WORKSPACE_DISABLE_ENV, "")
    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    state = {
        "schema_version": macos_runtime.RUNTIME_STATE_SCHEMA,
        "pid": 111,
        "port": 8765,
        "nonce": "runtime-nonce",
        "version_ref": "macos-version:same-version",
    }
    if recorded != "missing":
        state[FINANCE_STARTUP_METADATA_KEY] = (
            "malformed" if recorded == "malformed" else
            finance_startup_configuration_ref({} if recorded == "changed" else os.environ)
        )
    paths.runtime_state.write_text(json.dumps(state), encoding="utf-8")
    original_state = paths.runtime_state.read_bytes()
    opened = []
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda _state: True)
    monkeypatch.setattr(macos_runtime.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("reuse must not spawn"))
    monkeypatch.setattr(macos_runtime, "_terminate_owned_process", lambda _state: pytest.fail("reuse must not stop"))
    if recorded == "matching":
        monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
        monkeypatch.setattr(macos_runtime, "command_update", lambda *_args, **_kwargs: 0)
        monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40})
        monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "same-version")
    else:
        monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: pytest.fail("refusal must not provision bearer"))
        monkeypatch.setattr(macos_runtime, "command_update", lambda *_args, **_kwargs: pytest.fail("refusal must not update"))

    result = command_launch(paths, skip_update=False, no_browser=False)
    output = capsys.readouterr().out
    assert paths.runtime_state.read_bytes() == original_state
    if recorded == "matching":
        assert result == 0
        assert len(opened) == 1
        assert "is ready" in output
    else:
        assert result == 1
        assert opened == []
        assert "Run uaa stop, then uaa launch" in output
        assert "is ready" not in output
    stopped = []
    monkeypatch.setattr(macos_runtime, "_terminate_owned_process", lambda owned: stopped.append(owned) or True)
    assert macos_runtime.command_stop(paths, quiet=True) == 0
    assert stopped == [state]
    assert not paths.runtime_state.exists()


def test_packaged_finance_startup_state_binds_actual_child_environment(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_ENV_NAMES,
        FINANCE_STARTUP_METADATA_KEY,
        FINANCE_WORKSPACE_DISABLE_ENV,
        FINANCE_WORKSPACE_REPOSITORY_ENV,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    for name in FINANCE_STARTUP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    paths = RuntimePaths(_layout(tmp_path))
    private_book = tmp_path / "sample-private-book"
    monkeypatch.setenv(FINANCE_WORKSPACE_REPOSITORY_ENV, str(private_book))
    monkeypatch.setenv(FINANCE_WORKSPACE_DISABLE_ENV, "")
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40, "tag": "v0.104.0"})
    monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "same-version")
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda _state: True)
    monkeypatch.setattr(macos_runtime, "_next_available_port", lambda *_args: 8765)
    captured = []

    def spawn(*_args, **kwargs):
        captured.append(dict(kwargs["env"]))
        monkeypatch.setenv(FINANCE_WORKSPACE_DISABLE_ENV, "false")
        return SimpleNamespace(pid=222, poll=lambda: None)

    monkeypatch.setattr(macos_runtime.subprocess, "Popen", spawn)
    assert command_launch(paths, skip_update=True, no_browser=True) == 0
    state_text = paths.runtime_state.read_text(encoding="utf-8")
    state = json.loads(state_text)
    assert state[FINANCE_STARTUP_METADATA_KEY] == finance_startup_configuration_ref(captured[0])
    assert state[FINANCE_STARTUP_METADATA_KEY] != finance_startup_configuration_ref(os.environ)
    assert str(private_book) not in state_text
    assert not private_book.exists()


@pytest.mark.parametrize("condition", [
    "alive", "denied", "probe-error", "overflow", "invalid-pid", "bool-pid",
    "invalid-port", "invalid-nonce",
])
@pytest.mark.parametrize("configuration_changed", [False, True])
def test_packaged_unverified_runtime_cannot_lose_ownership_on_launch_or_stop(
    monkeypatch, tmp_path: Path, capsys, condition: str, configuration_changed: bool
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_ENV_NAMES,
        FINANCE_STARTUP_METADATA_KEY,
        FINANCE_WORKSPACE_DISABLE_ENV,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    for name in FINANCE_STARTUP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    state = {
        "schema_version": macos_runtime.RUNTIME_STATE_SCHEMA,
        "pid": 111, "port": 8765, "nonce": "a" * 32,
        "version_ref": "macos-version:same-version",
        FINANCE_STARTUP_METADATA_KEY: finance_startup_configuration_ref({}),
    }
    if condition == "invalid-pid":
        state["pid"] = "111"
    elif condition == "bool-pid":
        state["pid"] = True
    elif condition == "invalid-port":
        state["port"] = "8765"
    elif condition == "invalid-nonce":
        state["nonce"] = None
    paths.runtime_state.write_text(json.dumps(state), encoding="utf-8")
    original_state = paths.runtime_state.read_bytes()
    if configuration_changed:
        monkeypatch.setenv(FINANCE_WORKSPACE_DISABLE_ENV, "1")

    def probe(_pid, signal):
        assert signal == 0, "unverified ownership must never signal a process"
        if condition == "denied":
            raise PermissionError
        if condition == "probe-error":
            raise OSError
        if condition == "overflow":
            raise OverflowError

    monkeypatch.setattr(macos_runtime.os, "kill", probe)
    monkeypatch.setattr(macos_runtime, "_get_loopback_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: pytest.fail("unverified runtime must prevent bearer provisioning"))
    monkeypatch.setattr(macos_runtime, "command_update", lambda *_args, **_kwargs: pytest.fail("unverified runtime must prevent update"))
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("unverified runtime must prevent duplicate spawn"))
    monkeypatch.setattr(macos_runtime.webbrowser, "open", lambda *_args: pytest.fail("unverified runtime must prevent browser open"))

    assert command_launch(paths, skip_update=False, no_browser=False) == 1
    assert paths.runtime_state.read_bytes() == original_state
    assert macos_runtime.command_stop(paths, quiet=True) == 1
    assert paths.runtime_state.read_bytes() == original_state
    output = capsys.readouterr().out
    assert "ownership state was retained" in output.lower()
    assert "is ready" not in output
    assert "runtime stopped" not in output


def test_packaged_proven_dead_runtime_allows_stale_cleanup_and_fresh_start(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_METADATA_KEY,
        FINANCE_WORKSPACE_DISABLE_ENV,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    stale = {
        "schema_version": macos_runtime.RUNTIME_STATE_SCHEMA,
        "pid": 111, "port": 8765, "nonce": "a" * 32,
        "version_ref": "macos-version:old-version",
        FINANCE_STARTUP_METADATA_KEY: finance_startup_configuration_ref({}),
    }
    paths.runtime_state.write_text(json.dumps(stale), encoding="utf-8")

    def absent(_pid, signal):
        assert signal == 0
        raise ProcessLookupError

    monkeypatch.setattr(macos_runtime.os, "kill", absent)
    assert macos_runtime.command_stop(paths, quiet=True) == 0
    assert not paths.runtime_state.exists()
    paths.runtime_state.write_text(json.dumps(stale), encoding="utf-8")
    monkeypatch.setenv(FINANCE_WORKSPACE_DISABLE_ENV, "1")
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda state: state["pid"] == 222)
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40, "tag": "v0.104.0"})
    monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "same-version")
    monkeypatch.setattr(macos_runtime, "_next_available_port", lambda *_args: 8766)
    spawned = []

    def spawn(*_args, **kwargs):
        spawned.append(dict(kwargs["env"]))
        return SimpleNamespace(pid=222, poll=lambda: None)

    monkeypatch.setattr(macos_runtime.subprocess, "Popen", spawn)
    assert command_launch(paths, skip_update=True, no_browser=True) == 0
    current = json.loads(paths.runtime_state.read_text(encoding="utf-8"))
    assert current["pid"] == 222
    assert len(spawned) == 1
    assert current[FINANCE_STARTUP_METADATA_KEY] == finance_startup_configuration_ref(spawned[0])


def test_packaged_identity_loss_between_launch_probes_preserves_owner(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_METADATA_KEY,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    state = {
        "schema_version": macos_runtime.RUNTIME_STATE_SCHEMA,
        "pid": 111, "port": 8765, "nonce": "a" * 32,
        "version_ref": "macos-version:same-version",
        FINANCE_STARTUP_METADATA_KEY: finance_startup_configuration_ref(os.environ),
    }
    paths.runtime_state.write_text(json.dumps(state), encoding="utf-8")
    original_state = paths.runtime_state.read_bytes()
    identities = iter([True, False])
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda _state: next(identities))
    monkeypatch.setattr(macos_runtime, "_runtime_process_state", lambda _state: "alive")
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40})
    monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "same-version")
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("identity loss must prevent duplicate spawn"))
    monkeypatch.setattr(macos_runtime.webbrowser, "open", lambda *_args: pytest.fail("identity loss must prevent browser open"))
    assert command_launch(paths, skip_update=True, no_browser=False) == 1
    assert paths.runtime_state.read_bytes() == original_state


def test_packaged_stop_retains_owner_when_identity_is_lost_before_termination(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    state = {"schema_version": macos_runtime.RUNTIME_STATE_SCHEMA, "pid": 111}
    paths.runtime_state.write_text(json.dumps(state), encoding="utf-8")
    original_state = paths.runtime_state.read_bytes()
    identities = iter([True, False])
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda _state: next(identities))

    def probe(_pid, signal):
        assert signal == 0, "lost identity must prevent termination"

    monkeypatch.setattr(macos_runtime.os, "kill", probe)
    assert macos_runtime.command_stop(paths, quiet=True) == 1
    assert paths.runtime_state.read_bytes() == original_state


def test_packaged_launch_timeout_retains_unverified_live_child(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40, "tag": "v0.104.0"})
    monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "same-version")
    monkeypatch.setattr(macos_runtime, "_next_available_port", lambda *_args: 8765)
    monkeypatch.setattr(macos_runtime, "_get_loopback_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(macos_runtime, "START_TIMEOUT_SECONDS", 0)

    def probe(_pid, signal):
        assert signal == 0, "unverified child must never receive a termination signal"

    monkeypatch.setattr(macos_runtime.os, "kill", probe)
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: SimpleNamespace(pid=222, poll=lambda: None))
    assert command_launch(paths, skip_update=True, no_browser=True) == 1
    retained = paths.runtime_state.read_bytes()
    assert json.loads(retained)["pid"] == 222
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("retry must not spawn over live child"))
    assert command_launch(paths, skip_update=True, no_browser=True) == 1
    assert paths.runtime_state.read_bytes() == retained


@pytest.mark.parametrize("operation", ["update-relaunch", "rollback", "uninstall"])
def test_packaged_lifecycle_aborts_when_owned_stop_is_unverified(
    monkeypatch, tmp_path: Path, operation: str
) -> None:
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    monkeypatch.setattr(macos_runtime, "command_stop", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(macos_runtime.os, "execv", lambda *_args: pytest.fail("unverified stop must prevent exec"))
    monkeypatch.setattr(macos_runtime, "rollback", lambda *_args: pytest.fail("unverified stop must prevent rollback"))
    monkeypatch.setattr(macos_runtime, "uninstall", lambda *_args, **_kwargs: pytest.fail("unverified stop must prevent uninstall"))
    if operation == "update-relaunch":
        monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
        monkeypatch.setattr(macos_runtime, "command_update", lambda *_args, **_kwargs: 10)
        assert command_launch(paths, skip_update=False, no_browser=False) == 1
    elif operation == "rollback":
        assert macos_runtime.command_rollback(paths, relaunch=True) == 1
    else:
        assert macos_runtime.command_uninstall(paths, purge_versions=True) == 1


@pytest.mark.parametrize("condition", [
    "invalid-json", "wrong-schema", "non-object", "unreadable", "lstat-denied",
    "dangling-symlink",
])
def test_packaged_existing_unreadable_ownership_is_retained_and_reported_unverified(
    monkeypatch, tmp_path: Path, capsys, condition: str
) -> None:
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    payload = {
        "invalid-json": b"{invalid",
        "wrong-schema": b'{"schema_version":"unknown","pid":111}',
        "non-object": b"[]",
    }.get(condition, b"{}")
    if condition == "dangling-symlink":
        paths.runtime_state.symlink_to(paths.state_dir / "missing-owner")
    else:
        paths.runtime_state.write_bytes(payload)
    if condition == "unreadable":
        original_read = Path.read_text

        def read(path, *args, **kwargs):
            if path == paths.runtime_state:
                raise PermissionError
            return original_read(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read)
    if condition == "lstat-denied":
        original_lstat = Path.lstat

        def lstat(path, *args, **kwargs):
            if path == paths.runtime_state:
                raise PermissionError
            return original_lstat(path, *args, **kwargs)

        monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: pytest.fail("invalid ownership must prevent bearer provisioning"))
    monkeypatch.setattr(macos_runtime, "command_update", lambda *_args, **_kwargs: pytest.fail("invalid ownership must prevent update"))
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("invalid ownership must prevent spawn"))
    monkeypatch.setattr(macos_runtime.os, "kill", lambda *_args: pytest.fail("invalid ownership must not target a PID"))
    assert command_launch(paths, skip_update=False, no_browser=True) == 1
    assert macos_runtime.command_stop(paths, quiet=True) == 1
    capsys.readouterr()
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: None)
    monkeypatch.setattr(macos_runtime, "discover_github_token", lambda: None)
    assert macos_runtime.command_status(paths, as_json=True) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["runtime_status"] == "unverified"
    assert status["runtime_url"] is None
    if condition == "dangling-symlink":
        assert paths.runtime_state.is_symlink()
    else:
        assert paths.runtime_state.read_bytes() == payload


def test_packaged_genuinely_absent_ownership_is_reported_stopped(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    assert macos_runtime._load_runtime_state(paths) is None
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: None)
    monkeypatch.setattr(macos_runtime, "discover_github_token", lambda: None)
    assert macos_runtime.command_status(paths, as_json=True) == 0
    assert json.loads(capsys.readouterr().out)["runtime_status"] == "stopped"


def test_packaged_superseded_runtime_is_retained_if_exit_cannot_be_proven(
    monkeypatch, tmp_path: Path
) -> None:
    from ultimate_ai_agent.core.finance_startup import (
        FINANCE_STARTUP_METADATA_KEY,
        finance_startup_configuration_ref,
    )
    from ultimate_ai_agent.distribution.macos import runtime as macos_runtime

    paths = RuntimePaths(_layout(tmp_path))
    paths.state_dir.mkdir(parents=True)
    state = {
        "schema_version": macos_runtime.RUNTIME_STATE_SCHEMA,
        "pid": 111, "port": 8765, "nonce": "a" * 32,
        "version_ref": "macos-version:old-version",
        FINANCE_STARTUP_METADATA_KEY: finance_startup_configuration_ref(os.environ),
    }
    paths.runtime_state.write_text(json.dumps(state), encoding="utf-8")
    original_state = paths.runtime_state.read_bytes()
    monkeypatch.setattr(macos_runtime, "_runtime_identity_matches", lambda _state: True)
    monkeypatch.setattr(macos_runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer")
    monkeypatch.setattr(macos_runtime, "current_manifest", lambda _layout: {"source_commit": "a" * 40})
    monkeypatch.setattr(macos_runtime, "current_version_id", lambda _layout: "new-version")
    monkeypatch.setattr(macos_runtime, "STOP_TIMEOUT_SECONDS", 0)
    signals = []
    monkeypatch.setattr(macos_runtime.os, "kill", lambda pid, signal: signals.append((pid, signal)))
    monkeypatch.setattr(macos_runtime.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("prior exit must be proven before replacing runtime"))
    assert command_launch(paths, skip_update=True, no_browser=True) == 1
    assert paths.runtime_state.read_bytes() == original_state
    assert signals == [
        (111, macos_runtime.signal.SIGTERM),
        (111, macos_runtime.signal.SIGKILL),
        (111, 0),
    ]


def test_newest_channel_compares_stable_and_dev_by_tag_commit_time() -> None:
    stable = _candidate(
        tag="v0.104.0",
        channel="stable",
        source_timestamp="2026-06-23T12:28:59-07:00",
        published_at="2026-07-18T10:00:00Z",
        release_id=10,
    )
    dev = _candidate(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
        published_at="2026-07-18T09:00:00Z",
        release_id=11,
    )

    newest = select_release([stable, dev], "newest")
    stable_only = select_release([stable, dev], "stable")
    dev_only = select_release([stable, dev], "dev")

    assert newest.selected == dev
    assert newest.stable == stable
    assert newest.dev == dev
    assert stable_only.selected == stable
    assert dev_only.selected == dev


def test_backfilled_older_release_does_not_look_newer() -> None:
    older_but_published_later = _candidate(
        tag="v0.103.0",
        channel="stable",
        source_timestamp="2026-06-01T10:00:00Z",
        published_at="2026-07-18T12:00:00Z",
        release_id=22,
    )
    newer_but_published_earlier = _candidate(
        tag="v0.104.0",
        channel="stable",
        source_timestamp="2026-06-23T10:00:00Z",
        published_at="2026-07-18T11:00:00Z",
        release_id=21,
    )

    selection = select_release(
        [older_but_published_later, newer_but_published_earlier],
        "newest",
    )

    assert selection.selected == newer_but_published_earlier


def test_release_policy_excludes_historical_audit_tags() -> None:
    assert classify_tag("v0.104.0") == "stable"
    assert classify_tag("v0.105.1-web-hybrid") == "dev"
    with pytest.raises(ValueError, match="historical"):
        classify_tag("v2.0.0")
    with pytest.raises(ValueError, match="historical"):
        classify_tag("v1.7.2")
    with pytest.raises(ValueError, match="conflicts"):
        classify_tag("v0.104.0", requested_channel="dev")


def test_github_catalog_requires_active_descriptor_and_matching_assets() -> None:
    repository = "doncazper/ultimate-ai-agent"
    releases_url = f"https://api.github.com/repos/{repository}/releases?per_page=100"
    descriptor_url = f"https://api.github.com/repos/{repository}/releases/assets/101"
    artifact_url = f"https://api.github.com/repos/{repository}/releases/assets/102"
    descriptor = _descriptor(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
    )
    releases = [
        {
            "id": 55,
            "draft": False,
            "prerelease": True,
            "tag_name": descriptor.tag,
            "published_at": "2026-07-18T11:00:00Z",
            "assets": [
                {
                    "name": "uaa-macos-arm64.release.json",
                    "url": descriptor_url,
                    "size": len(descriptor.to_json_bytes()),
                    "digest": None,
                },
                {
                    "name": "uaa-macos-arm64.tar.gz",
                    "url": artifact_url,
                    "size": descriptor.artifact_size,
                    "digest": f"sha256:{descriptor.artifact_sha256}",
                },
            ],
        },
        {
            "id": 56,
            "draft": False,
            "prerelease": False,
            "tag_name": "v2.0.0",
            "published_at": "2026-07-18T12:00:00Z",
            "assets": [],
        },
    ]
    opener = _FakeOpener(
        {
            releases_url: json.dumps(releases).encode(),
            descriptor_url: descriptor.to_json_bytes(),
        }
    )

    catalog = GitHubReleaseClient(
        repository=repository,
        token="held-in-memory",
        opener=opener,
    ).fetch_catalog("arm64")

    assert len(catalog.candidates) == 1
    assert catalog.candidates[0].descriptor.tag == "v0.105.1-web-hybrid"
    assert catalog.ignored_release_count == 1
    assert catalog.authenticated is True
    assert "held-in-memory" not in repr(catalog)


def test_safe_extract_rejects_traversal_and_links(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.tar.gz"
    with tarfile.open(traversal, "w:gz") as tar:
        payload = b"unsafe"
        info = tarfile.TarInfo("../outside")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(InstallError, match="unsafe path"):
        safe_extract_archive(traversal, tmp_path / "extract-traversal")
    assert not (tmp_path / "outside").exists()

    linked = tmp_path / "linked.tar.gz"
    with tarfile.open(linked, "w:gz") as tar:
        info = tarfile.TarInfo("linked")
        info.type = tarfile.SYMTYPE
        info.linkname = "/tmp/outside"
        tar.addfile(info)
    with pytest.raises(InstallError, match="link or special"):
        safe_extract_archive(linked, tmp_path / "extract-linked")


def test_existing_app_location_wins_over_current_directory_writability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    system_applications = tmp_path / "system-applications"
    installed_app = system_applications / APP_BUNDLE_NAME
    installed_app.mkdir(parents=True)
    monkeypatch.setattr(
        "ultimate_ai_agent.distribution.macos.installer._directory_is_writable",
        lambda path: False,
    )

    selected = _select_applications_dir(
        home=home,
        system_applications=system_applications,
    )

    assert selected == system_applications


def test_atomic_install_idempotency_update_and_rollback(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    first_archive, first_descriptor = _tiny_release(
        tmp_path / "first",
        tag="v0.104.0",
        channel="stable",
        commit="1" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    second_archive, second_descriptor = _tiny_release(
        tmp_path / "second",
        tag="v0.105.1-web-hybrid",
        channel="dev",
        commit="2" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
    )

    def skip_signature(app: Path, descriptor: ReleaseDescriptor) -> None:
        _ = app, descriptor

    first = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    repeated = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    second = install_archive(
        second_archive,
        second_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )

    assert first.status == "installed"
    assert repeated.status == "already-current"
    assert second.status == "installed"
    assert current_version_id(layout) == second.version_id
    assert layout.current_link.is_symlink()
    assert layout.previous_link.is_symlink()
    assert layout.app_link.is_dir()
    assert not layout.app_link.is_symlink()
    assert layout.cli_path.is_file()
    assert CLI_MARKER in layout.cli_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in layout.cli_path.read_text(encoding="utf-8")
    assert current_manifest(layout)["tag"] == second_descriptor.tag

    rolled_back = rollback(
        layout,
        application_verifier=lambda app: None,
    )

    assert rolled_back.version_id == first.version_id
    assert current_version_id(layout) == first.version_id
    assert current_manifest(layout)["tag"] == first_descriptor.tag


def test_entrypoint_failures_restore_install_and_rollback_links(
    tmp_path: Path,
) -> None:
    layout = _layout(tmp_path)
    first_archive, first_descriptor = _tiny_release(
        tmp_path / "first",
        tag="v0.104.0",
        channel="stable",
        commit="1" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    second_archive, second_descriptor = _tiny_release(
        tmp_path / "second",
        tag="v0.105.1-web-hybrid",
        channel="dev",
        commit="2" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
    )

    def skip_signature(app: Path, descriptor: ReleaseDescriptor) -> None:
        _ = app, descriptor

    first = install_archive(
        first_archive,
        first_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )
    original_cli = layout.cli_path.read_bytes()

    def reject_applications_copy(
        app: Path,
        descriptor: ReleaseDescriptor,
    ) -> None:
        _ = descriptor
        if app.name.startswith(".Ultimate AI Agent"):
            raise InstallError("injected Applications promotion failure")

    with pytest.raises(InstallError, match="injected Applications"):
        install_archive(
            second_archive,
            second_descriptor,
            layout,
            code_signature_verifier=reject_applications_copy,
        )

    assert current_version_id(layout) == first.version_id
    assert not layout.previous_link.exists()
    assert layout.app_link.is_dir()
    assert layout.cli_path.read_bytes() == original_cli

    second = install_archive(
        second_archive,
        second_descriptor,
        layout,
        code_signature_verifier=skip_signature,
    )

    def reject_rollback_copy(app: Path) -> None:
        _ = app
        raise InstallError("injected rollback Applications failure")

    with pytest.raises(InstallError, match="injected rollback"):
        rollback(layout, application_verifier=reject_rollback_copy)

    assert current_version_id(layout) == second.version_id
    assert layout.previous_link.resolve().name == first.version_id
    assert layout.app_link.is_dir()
    assert layout.cli_path.read_bytes() == original_cli


def test_installer_refuses_unmanaged_app_or_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="3" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.applications_dir.mkdir(parents=True)
    layout.app_link.mkdir()

    with pytest.raises(InstallError, match="not owned"):
        install_archive(
            archive,
            descriptor,
            layout,
            code_signature_verifier=lambda app, release: None,
        )


def test_installer_migrates_only_the_exact_legacy_repo_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="6" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.bin_dir.mkdir(parents=True)
    layout.cli_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'exec "/workspace/ultimate-ai-agent/scripts/dev/uaa" "$@"\n',
        encoding="utf-8",
    )

    result = install_archive(
        archive,
        descriptor,
        layout,
        code_signature_verifier=lambda app, release: None,
    )

    assert result.status == "installed"
    assert CLI_MARKER in layout.cli_path.read_text(encoding="utf-8")
    assert "/workspace/" not in layout.cli_path.read_text(encoding="utf-8")


def test_installer_refuses_arbitrary_existing_cli(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "release",
        tag="v0.104.0",
        channel="stable",
        commit="7" * 40,
        source_timestamp="2026-06-23T12:28:59-07:00",
    )
    layout.bin_dir.mkdir(parents=True)
    layout.cli_path.write_text("#!/bin/sh\necho unrelated\n", encoding="utf-8")

    with pytest.raises(InstallError, match="not owned"):
        install_archive(
            archive,
            descriptor,
            layout,
            code_signature_verifier=lambda app, release: None,
        )


def test_packaged_bundle_has_native_app_verified_manifest_and_no_checkout_path(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    (runtime / "bin").mkdir(parents=True)
    fake_python = runtime / "bin" / "python3"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)
    frontend = tmp_path / "frontend"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text("<!doctype html><title>UAA</title>\n")
    output = tmp_path / "output"

    receipt = build_release_bundle(
        source_root=ROOT,
        python_runtime=runtime,
        output_dir=output,
        tag="local-test-build",
        channel="dev",
        source_commit="4" * 40,
        source_timestamp="2026-07-10T14:36:02-07:00",
        version="0.104.0",
        architecture="arm64",
        frontend_dist=frontend,
        signing_identity=None,
        notary_profile=None,
        skip_dependency_install=True,
        allow_dirty_local=True,
    )
    descriptor = ReleaseDescriptor.from_json_bytes(
        (output / "uaa-macos-arm64.release.json").read_bytes(),
        expected_architecture="arm64",
    )
    install_layout = _layout(tmp_path / "installed")

    result = install_archive(
        output / "uaa-macos-arm64.tar.gz",
        descriptor,
        install_layout,
    )
    executable = (
        install_layout.current_link
        / APP_BUNDLE_NAME
        / "Contents"
        / "MacOS"
        / APP_BUNDLE_NAME.removesuffix(".app")
    )
    installed_app = executable.parents[2]
    icon = installed_app / "Contents" / "Resources" / "UltimateAI-Agent.icns"
    with (installed_app / "Contents" / "Info.plist").open("rb") as handle:
        installed_plist = plistlib.load(handle)
    file_result = subprocess.run(
        ["/usr/bin/file", "-b", str(executable)],
        text=True,
        capture_output=True,
        check=True,
    )

    assert receipt["status"] == "built"
    assert receipt["signing_kind"] == "ad-hoc"
    assert result.status == "installed"
    assert "Mach-O" in file_result.stdout
    assert icon.is_file()
    assert icon.stat().st_size > 100_000
    assert installed_plist["CFBundleIconFile"] == "UltimateAI-Agent.icns"
    assert (
        subprocess.run(
            ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(installed_app)],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    for path in output.iterdir():
        if path.is_file() and path.stat().st_size < 10 * 1024 * 1024:
            assert str(ROOT).encode() not in path.read_bytes()
            assert b"/Users/" not in path.read_bytes()


def test_update_check_never_downgrades_a_newer_local_install(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    archive, descriptor = _tiny_release(
        tmp_path / "local",
        tag="worktree-local",
        channel="dev",
        commit="5" * 40,
        source_timestamp="2026-07-17T14:43:26-07:00",
    )
    install_archive(
        archive,
        descriptor,
        layout,
        code_signature_verifier=lambda app, release: None,
    )
    remote = _candidate(
        tag="v0.105.1-web-hybrid",
        channel="dev",
        source_timestamp="2026-07-10T14:36:02-07:00",
        published_at="2026-07-18T12:00:00Z",
        release_id=77,
    )
    client = SimpleNamespace(
        fetch_catalog=lambda architecture: SimpleNamespace(
            candidates=(remote,),
            ignored_release_count=0,
            authenticated=True,
        )
    )

    check = check_for_update(
        RuntimePaths(layout),
        client=client,
        channel="newest",
    )

    assert check.update_available is False
    assert check.reason_ref == "reason-ref:update:installed-is-current-or-newer"


def test_workflow_is_tag_bound_checksum_verified_and_does_not_move_tags() -> None:
    workflow = (ROOT / ".github" / "workflows" / "macos-release.yml").read_text(
        encoding="utf-8"
    )
    workflow_contract = yaml.safe_load(workflow)
    release_steps = workflow_contract["jobs"]["verify-source"]["steps"]
    checkout_steps = [
        step
        for step in release_steps
        if str(step.get("uses", "")).startswith("actions/checkout@")
    ]
    focused_installer_step = next(
        step
        for step in release_steps
        if step.get("name") == "Verify focused installer contracts"
    )
    focused_installer_run = focused_installer_step["run"]
    bundle_build_step = next(
        step
        for step in release_steps
        if step.get("name") == "Build and verify release assets"
    )
    bundle_build_run = bundle_build_step["run"]
    publication_block = next(
        step
        for step in release_steps
        if step.get("name") == "Reject unsupported hosted publication"
    )

    assert "refs/tags/${{ steps.source.outputs.tag }}" in workflow
    assert 'git rev-parse "refs/tags/$RELEASE_TAG^{commit}"' in workflow
    assert "scripts/macos/release_policy.py" in workflow
    assert "scripts/macos/prepare_python_runtime.sh" in workflow
    assert "build_release_bundle.py" in workflow
    assert "uaa-macos-arm64.release.json" in workflow
    assert '"$GH_CLI" release upload' not in workflow
    assert "GH_TOKEN" not in workflow
    assert "secrets." not in workflow
    assert "contents: write" not in workflow
    assert "scripts/macos/verify_installer_e2e.py" in workflow
    assert "git tag -f" not in workflow
    assert "git push --force" not in workflow
    assert "actions/setup-python" not in workflow
    assert [step["uses"] for step in checkout_steps] == [
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    ]
    assert checkout_steps[0]["with"]["ref"] == "${{ github.workflow_sha }}"
    assert checkout_steps[1]["with"]["ref"] == (
        "refs/tags/${{ steps.source.outputs.tag }}"
    )
    assert all(
        step["with"]["persist-credentials"] is False for step in checkout_steps
    )
    assert workflow_contract["permissions"] == {}
    assert workflow_contract["jobs"]["verify-source"]["permissions"] == {
        "contents": "read"
    }
    assert set(workflow_contract["jobs"]) == {"verify-source"}
    assert publication_block["if"] == (
        "github.event_name == 'workflow_dispatch' && "
        "(inputs.publish_release == true || "
        "inputs.publish_installer_bootstrap == true)"
    )
    assert "exit 1" in publication_block["run"]
    pinned_uv = (
        ".macos-build-venv/bin/python -m pip install "
        '--disable-pip-version-check "uv==0.11.21"'
    )
    assert pinned_uv in focused_installer_run
    assert ".macos-build-venv/bin/uv sync --frozen" in focused_installer_run
    assert "$GITHUB_PATH" not in focused_installer_run
    assert (
        'PATH="$GITHUB_WORKSPACE/.macos-build-venv/bin:$PATH"'
        in bundle_build_run
    )
    assert "command -v gh" not in workflow
    assert "\n          gh release " not in workflow
    assert "runs-on: macos-15" in workflow
    assert "uses: ./.github/actions/setup-toolchain" in workflow
    builder = (ROOT / "scripts" / "macos" / "build_release_bundle.py").read_text(
        encoding="utf-8"
    )
    assert "--no-build-isolation" in builder
    assert "setuptools==79.0.1" in builder
    assert "--require-hashes" in builder


def test_public_bootstrap_download_is_anonymous_bounded_and_checksum_bound() -> None:
    installer = (ROOT / "packaging" / "macos" / "install.sh").read_text(
        encoding="utf-8"
    )

    assert "gh auth status" not in installer
    assert "gh auth login" not in installer
    assert "gh release download" not in installer
    assert "https://github.com/$REPOSITORY/releases/download/" in installer
    for fragment in (
        "/usr/bin/curl -q",
        "--fail",
        "--location",
        "--proto '=https'",
        "--proto-redir '=https'",
        "--tlsv1.2",
        "--retry 3",
        "--connect-timeout 15",
        "--max-time 300",
        '--output "$destination.partial"',
        '/bin/mv "$destination.partial" "$destination"',
        'download_public_asset "$BOOTSTRAP_ASSET"',
        'download_public_asset "$CHECKSUM_ASSET"',
        '/usr/bin/shasum -a 256 -c "$CHECKSUM_ASSET"',
    ):
        assert fragment in installer


def test_public_bootstrap_curl_disables_hostile_user_configuration(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"safe")
    (tmp_path / ".curlrc").write_text(
        "max-filesize = 1\ninsecure\nlocation-trusted\n",
        encoding="utf-8",
    )
    env = {**os.environ, "HOME": str(tmp_path)}

    unsafe = subprocess.run(
        ["/usr/bin/curl", "--fail", "--output", str(tmp_path / "unsafe"), source.as_uri()],
        check=False,
        capture_output=True,
        env=env,
    )
    safe = subprocess.run(
        [
            "/usr/bin/curl",
            "-q",
            "--fail",
            "--output",
            str(tmp_path / "safe"),
            source.as_uri(),
        ],
        check=False,
        capture_output=True,
        env=env,
    )

    assert unsafe.returncode != 0
    assert safe.returncode == 0
    assert (tmp_path / "safe").read_bytes() == b"safe"


def test_installer_e2e_validators_fail_closed_on_status_and_receipt_drift(
    tmp_path: Path,
) -> None:
    valid_status = {
        "schema_version": "uaa.macos.status.v1",
        "installed": True,
        "tag_ref": "git-tag:v0.104.0",
        "version": "0.104.0",
        "runtime_status": "stopped",
        "raw_paths_included": False,
        "credentials_included": False,
    }
    validate_status_payload(
        valid_status,
        expected_tag="v0.104.0",
        expected_version="0.104.0",
        expected_runtime_status="stopped",
    )
    with pytest.raises(InstallerE2EError, match="status payload"):
        validate_status_payload(
            {**valid_status, "runtime_status": "unknown"},
            expected_tag="v0.104.0",
            expected_version="0.104.0",
            expected_runtime_status="stopped",
        )

    receipts = tmp_path / "receipts"
    receipts.mkdir()
    receipt = {
        "schema_version": "uaa.macos.install-receipt.v1",
        "status": "installed",
        "raw_paths_included": False,
        "credentials_included": False,
    }
    target = receipts / "one.json"
    target.write_text(json.dumps(receipt), encoding="utf-8")
    validate_receipts(receipts, forbidden_text=str(tmp_path))

    target.write_text(
        json.dumps({**receipt, "unsafe": str(tmp_path)}),
        encoding="utf-8",
    )
    with pytest.raises(InstallerE2EError, match="redaction"):
        validate_receipts(receipts, forbidden_text=str(tmp_path))


def test_macos_distribution_adapters_remain_exact_scoped() -> None:
    assert macos_distribution_policy_failures(ROOT) == []
    assert MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES == {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }


def test_macos_distribution_policy_rejects_shell_broadening() -> None:
    rel_path = "src/ultimate_ai_agent/distribution/macos/runtime.py"
    source = (ROOT / rel_path).read_text(encoding="utf-8")

    failures = macos_distribution_adapter_policy_failures(
        rel_path,
        source + "\nsubprocess.run(user_command, shell=True)\n",
    )

    assert failures
    assert any(
        "shell execution" in failure or "forbidden broad" in failure
        for failure in failures
    )
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        source + "\nsubprocess.run(user_command, shell=True)\n",
        "subprocess",
    )


def test_macos_distribution_policy_rejects_unreviewed_network_drift() -> None:
    rel_path = "src/ultimate_ai_agent/distribution/macos/runtime.py"
    source = (ROOT / rel_path).read_text(encoding="utf-8")

    assert macos_distribution_static_fragment_allowed(
        rel_path,
        source,
        "urllib.request.urlopen",
    )
    attribute_drift = source + "\nsocket.create_connection((host, port))\n"
    assert macos_distribution_adapter_policy_failures(rel_path, attribute_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        attribute_drift,
        "socket.",
    )
    endpoint_drift = source + '\nUNREVIEWED_ENDPOINT = "https://example.invalid"\n'
    assert macos_distribution_adapter_policy_failures(rel_path, endpoint_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        endpoint_drift,
        "https://",
    )
    alias_drift = source.replace("import socket\n", "import socket as network_socket\n")
    assert macos_distribution_adapter_policy_failures(rel_path, alias_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        alias_drift,
        "socket.",
    )
    indirect_drift = source + '\ngetattr(subprocess, "run")([])\n'
    assert macos_distribution_adapter_policy_failures(rel_path, indirect_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        indirect_drift,
        "subprocess",
    )
    process_drift = source + '\nos.spawnv(0, "/bin/echo", ["echo"])\n'
    assert macos_distribution_adapter_policy_failures(rel_path, process_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        process_drift,
        "subprocess",
    )
    dynamic_import_drift = source + '\n__import__("subprocess").Popen(["/bin/echo"])\n'
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        dynamic_import_drift,
    )
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        dynamic_import_drift,
        "subprocess",
    )
    module_registry_drift = (
        source + '\nsys.modules["subprocess"].Popen(["/bin/echo"])\n'
    )
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        module_registry_drift,
    )
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        module_registry_drift,
        "subprocess",
    )
    callable_alias_drift = source + "\nspawn = subprocess.Popen\nspawn([])\n"
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        callable_alias_drift,
    )
    command_argv_drift = source.replace(
        '["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)]',
        '[str(app), "--verify"]',
        1,
    )
    assert command_argv_drift != source
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        command_argv_drift,
    )
    shell_truthy_drift = source.replace(
        "            check=False,\n        )",
        "            check=False,\n            shell=1,\n        )",
        1,
    )
    assert shell_truthy_drift != source
    assert any(
        "shell execution must remain literal-false" in failure
        for failure in macos_distribution_adapter_policy_failures(
            rel_path,
            shell_truthy_drift,
        )
    )
    request_source_drift = source.replace(
        "            url,\n            headers={",
        '            os.environ["UNREVIEWED_URL"],\n            headers={',
        1,
    )
    assert request_source_drift != source
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        request_source_drift,
    )


def test_macos_distribution_policy_rejects_unreviewed_filesystem_call() -> None:
    rel_path = "src/ultimate_ai_agent/distribution/macos/installer.py"
    source = (ROOT / rel_path).read_text(encoding="utf-8")
    filesystem_drift = source + '\nPath("/").glob("**/*")\n'

    assert macos_distribution_adapter_policy_failures(rel_path, filesystem_drift)
    assert not macos_distribution_static_fragment_allowed(
        rel_path,
        filesystem_drift,
        "Path.home(",
    )
    path_instance_drift = source + "\nlayout.root.glob('**/*')\n"
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        path_instance_drift,
    )
    module_call_drift = source + "\ntempfile.mkdtemp()\n"
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        module_call_drift,
    )
    builtin_open_drift = source + '\nopen("/tmp/unreviewed", "w")\n'
    assert macos_distribution_adapter_policy_failures(
        rel_path,
        builtin_open_drift,
    )


def test_macos_distribution_policy_ignores_unrelated_fixture_roots_but_fails_partial_lane(
    tmp_path: Path,
) -> None:
    assert macos_distribution_policy_failures(tmp_path) == []

    lane_root = tmp_path / "src" / "ultimate_ai_agent" / "distribution" / "macos"
    lane_root.mkdir(parents=True)

    failures = macos_distribution_policy_failures(tmp_path)

    assert failures
    assert any("unavailable" in failure for failure in failures)

    partial = tmp_path / next(iter(MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES))
    partial.write_text("# partial distribution lane\n", encoding="utf-8")
    partial_failures = macos_distribution_policy_failures(tmp_path)

    assert partial_failures
    assert any("unavailable" in failure for failure in partial_failures)


def _layout(root: Path) -> InstallLayout:
    return InstallLayout(
        root=root / "Library" / "Ultimate AI Agent",
        applications_dir=root / "Applications",
        bin_dir=root / "bin",
    )


def _descriptor(
    *,
    tag: str,
    channel: str,
    source_timestamp: str,
    commit: str = "a" * 40,
    artifact_sha256: str = "b" * 64,
    artifact_size: int = 123,
) -> ReleaseDescriptor:
    return ReleaseDescriptor(
        schema_version=RELEASE_DESCRIPTOR_SCHEMA,
        product_line=PRODUCT_LINE,
        tag=tag,
        version="0.104.0",
        channel=channel,  # type: ignore[arg-type]
        source_commit=commit,
        source_timestamp=source_timestamp,
        platform="macos",
        architecture="arm64",
        artifact_name="uaa-macos-arm64.tar.gz",
        artifact_sha256=artifact_sha256,
        artifact_size=artifact_size,
        minimum_macos=MINIMUM_MACOS,
        signing_kind="ad-hoc",
        notarized=False,
    )


def _candidate(
    *,
    tag: str,
    channel: str,
    source_timestamp: str,
    published_at: str,
    release_id: int,
) -> ReleaseCandidate:
    descriptor = _descriptor(
        tag=tag,
        channel=channel,
        source_timestamp=source_timestamp,
    )
    return ReleaseCandidate(
        descriptor=descriptor,
        release_id=release_id,
        published_at=published_at,
        artifact_api_url=(
            f"https://api.github.com/repos/doncazper/ultimate-ai-agent/"
            f"releases/assets/{release_id * 10 + 1}"
        ),
        descriptor_api_url=(
            f"https://api.github.com/repos/doncazper/ultimate-ai-agent/"
            f"releases/assets/{release_id * 10 + 2}"
        ),
        github_asset_digest=f"sha256:{descriptor.artifact_sha256}",
    )


def _tiny_release(
    root: Path,
    *,
    tag: str,
    channel: str,
    commit: str,
    source_timestamp: str,
) -> tuple[Path, ReleaseDescriptor]:
    payload = root / "payload"
    app = payload / APP_BUNDLE_NAME
    executable = app / "Contents" / "MacOS" / APP_BUNDLE_NAME.removesuffix(".app")
    resources = app / "Contents" / "Resources"
    resources.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    shutil_source = Path("/usr/bin/true")
    executable.write_bytes(shutil_source.read_bytes())
    executable.chmod(0o755)
    with (app / "Contents" / "Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleIdentifier": APP_BUNDLE_IDENTIFIER,
                "CFBundleShortVersionString": "0.104.0",
                "CFBundleExecutable": APP_BUNDLE_NAME.removesuffix(".app"),
                "CFBundlePackageType": "APPL",
            },
            handle,
        )
    (resources / APP_MANAGED_MARKER).write_text(
        json.dumps(
            {
                "schema_version": "uaa.macos.install-ownership.v1",
                "product_line": PRODUCT_LINE,
            }
        )
    )
    files = []
    for path in sorted(item for item in payload.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(payload).as_posix(),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
                "mode": 0o755 if stat.S_IMODE(path.stat().st_mode) & 0o111 else 0o644,
            }
        )
    manifest = {
        "schema_version": BUNDLE_MANIFEST_SCHEMA,
        "product_line": PRODUCT_LINE,
        "tag": tag,
        "version": "0.104.0",
        "channel": channel,
        "source_commit": commit,
        "source_timestamp": source_timestamp,
        "platform": "macos",
        "architecture": "arm64",
        "app_bundle": APP_BUNDLE_NAME,
        "signing_kind": "ad-hoc",
        "notarized": False,
        "files": files,
    }
    (payload / "bundle-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    archive = root / "uaa-macos-arm64.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "w:gz") as tar:
        for path in sorted(payload.rglob("*")):
            tar.add(
                path,
                arcname=path.relative_to(payload).as_posix(),
                recursive=False,
            )
    descriptor = _descriptor(
        tag=tag,
        channel=channel,
        source_timestamp=source_timestamp,
        commit=commit,
        artifact_sha256=sha256_file(archive),
        artifact_size=archive.stat().st_size,
    )
    return archive, descriptor


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class _FakeOpener:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self.responses = responses

    def open(self, request: object, timeout: float) -> _FakeResponse:
        _ = timeout
        url = getattr(request, "full_url")
        return _FakeResponse(self.responses[url])
