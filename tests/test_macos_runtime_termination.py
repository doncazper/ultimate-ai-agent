"""Deterministic ownership checks while a killed runtime exits asynchronously."""

from __future__ import annotations

import pytest


@pytest.fixture
def stopping_runtime(monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace

    from ultimate_ai_agent.distribution.macos import runtime
    from ultimate_ai_agent.distribution.macos.installer import InstallLayout

    paths = runtime.RuntimePaths(
        InstallLayout(
            root=tmp_path / "installation",
            applications_dir=tmp_path / "applications",
            bin_dir=tmp_path / "bin",
        )
    )
    paths.state_dir.mkdir(parents=True)
    paths.runtime_state.write_text(
        json.dumps({"schema_version": runtime.RUNTIME_STATE_SCHEMA, "pid": 111}),
        encoding="utf-8",
    )
    harness = SimpleNamespace(
        runtime=runtime,
        paths=paths,
        original_state=paths.runtime_state.read_bytes(),
        now=0.0,
        sleeps=[],
        signals=[],
        killed_at=None,
        exit_delay=None,
        permission_error_at=None,
        disappears_during_kill=False,
        post_kill_alive_probes=0,
        proven_dead=False,
    )

    def sleep(seconds):
        assert seconds == 0.1
        assert paths.runtime_state.read_bytes() == harness.original_state
        harness.sleeps.append(seconds)
        harness.now = round(harness.now + seconds, 10)
        assert harness.now <= 0.6, "termination must stop at its bounded deadlines"

    def kill(pid, requested_signal):
        assert pid == 111
        assert paths.runtime_state.read_bytes() == harness.original_state
        if requested_signal == runtime.signal.SIGTERM:
            harness.signals.append(requested_signal)
        elif requested_signal == runtime.signal.SIGKILL:
            harness.signals.append(requested_signal)
            if harness.permission_error_at == "delivery":
                raise PermissionError
            if harness.disappears_during_kill:
                harness.proven_dead = True
                raise ProcessLookupError
            harness.killed_at = harness.now
        else:
            assert requested_signal == 0
            if harness.killed_at is None:
                return
            if harness.permission_error_at == "probe":
                raise PermissionError
            if (
                harness.exit_delay is not None
                and harness.now
                >= round(harness.killed_at + harness.exit_delay, 10)
            ):
                harness.proven_dead = True
                raise ProcessLookupError
            harness.post_kill_alive_probes += 1

    # Replace only runtime's module references: never signal or sleep for real.
    monkeypatch.setattr(runtime, "os", SimpleNamespace(kill=kill))
    monkeypatch.setattr(
        runtime, "time", SimpleNamespace(monotonic=lambda: harness.now, sleep=sleep)
    )
    monkeypatch.setattr(runtime, "STOP_TIMEOUT_SECONDS", 0.3)
    monkeypatch.setattr(runtime, "_runtime_identity_matches", lambda _state: True)
    return harness


@pytest.mark.parametrize("exit_delay", [0.1, 0.2, 0.3])
def test_stop_waits_for_proven_exit_after_sigkill(stopping_runtime, exit_delay):
    harness = stopping_runtime
    harness.exit_delay = exit_delay

    assert harness.runtime.command_stop(harness.paths, quiet=True) == 0

    assert harness.signals == [
        harness.runtime.signal.SIGTERM,
        harness.runtime.signal.SIGKILL,
    ]
    assert harness.killed_at == pytest.approx(0.3)
    assert harness.now == pytest.approx(0.3 + exit_delay)
    assert harness.post_kill_alive_probes >= 1
    assert harness.proven_dead
    assert not harness.paths.runtime_state.exists()


@pytest.mark.parametrize("disappears_during_kill", [False, True])
def test_stop_accepts_immediately_proven_exit(stopping_runtime, disappears_during_kill):
    harness = stopping_runtime
    harness.exit_delay = 0.0
    harness.disappears_during_kill = disappears_during_kill

    assert harness.runtime.command_stop(harness.paths, quiet=True) == 0

    assert harness.signals == [
        harness.runtime.signal.SIGTERM,
        harness.runtime.signal.SIGKILL,
    ]
    assert harness.now == pytest.approx(0.3)
    assert harness.post_kill_alive_probes == 0
    assert harness.proven_dead
    assert not harness.paths.runtime_state.exists()


def test_stop_retains_owner_when_sigkill_exit_deadline_expires(stopping_runtime):
    harness = stopping_runtime

    assert harness.runtime.command_stop(harness.paths, quiet=True) == 1

    assert harness.signals == [
        harness.runtime.signal.SIGTERM,
        harness.runtime.signal.SIGKILL,
    ]
    assert harness.now == pytest.approx(0.6)
    assert harness.post_kill_alive_probes >= 1
    assert not harness.proven_dead
    assert harness.paths.runtime_state.read_bytes() == harness.original_state


@pytest.mark.parametrize("permission_error_at", ["delivery", "probe"])
def test_stop_retains_owner_when_sigkill_exit_is_unverified(
    stopping_runtime, permission_error_at
):
    harness = stopping_runtime
    harness.permission_error_at = permission_error_at

    assert harness.runtime.command_stop(harness.paths, quiet=True) == 1

    assert harness.signals == [
        harness.runtime.signal.SIGTERM,
        harness.runtime.signal.SIGKILL,
    ]
    assert not harness.proven_dead
    assert harness.paths.runtime_state.read_bytes() == harness.original_state


def test_stop_never_sends_sigkill_after_identity_loss(stopping_runtime, monkeypatch):
    harness = stopping_runtime
    monkeypatch.setattr(
        harness.runtime,
        "_runtime_identity_matches",
        lambda _state: not harness.signals,
    )

    assert harness.runtime.command_stop(harness.paths, quiet=True) == 1

    assert harness.signals == [harness.runtime.signal.SIGTERM]
    assert harness.killed_at is None
    assert not harness.proven_dead
    assert harness.paths.runtime_state.read_bytes() == harness.original_state


@pytest.mark.parametrize("child_exit", [0, -9, None])
def test_launch_timeout_clears_owner_only_when_exact_child_proves_exit(
    monkeypatch, tmp_path, child_exit
):
    import json
    from types import SimpleNamespace

    from ultimate_ai_agent.distribution.macos import runtime
    from ultimate_ai_agent.distribution.macos.installer import InstallLayout

    paths = runtime.RuntimePaths(
        InstallLayout(
            root=tmp_path / "installation",
            applications_dir=tmp_path / "applications",
            bin_dir=tmp_path / "bin",
        )
    )
    polls = []

    def poll():
        polls.append("owned-child")
        assert json.loads(paths.runtime_state.read_text(encoding="utf-8"))["pid"] == 222
        return child_exit

    def probe(pid, requested_signal):
        assert pid == 222
        assert requested_signal == 0, "unverified identity cannot authorize a signal"

    child = SimpleNamespace(pid=222, poll=poll)
    monkeypatch.setattr(
        runtime, "_ensure_local_bearer", lambda _paths: "local-session-bearer"
    )
    monkeypatch.setattr(
        runtime,
        "current_manifest",
        lambda _layout: {"source_commit": "a" * 40, "tag": "v0.104.0"},
    )
    monkeypatch.setattr(runtime, "current_version_id", lambda _layout: "same-version")
    monkeypatch.setattr(runtime, "_next_available_port", lambda *_args: 8765)
    monkeypatch.setattr(runtime, "_runtime_environment", lambda **_kwargs: {})
    monkeypatch.setattr(runtime, "_runtime_identity_matches", lambda _state: False)
    monkeypatch.setattr(runtime, "START_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(runtime.os, "kill", probe)
    monkeypatch.setattr(
        runtime,
        "subprocess",
        SimpleNamespace(Popen=lambda *_args, **_kwargs: child, DEVNULL=-3),
    )
    monkeypatch.setattr(
        runtime,
        "time",
        SimpleNamespace(
            monotonic=lambda: 0.0,
            sleep=lambda _seconds: pytest.fail("zero startup grace must not sleep"),
        ),
    )

    assert runtime.command_launch(paths, skip_update=True, no_browser=True) == 1

    assert polls == ["owned-child"]
    if child_exit is None:
        assert json.loads(paths.runtime_state.read_text(encoding="utf-8"))["pid"] == 222
    else:
        assert not paths.runtime_state.exists()
