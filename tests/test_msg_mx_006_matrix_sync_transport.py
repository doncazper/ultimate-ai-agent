from __future__ import annotations

import errno
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ultimate_ai_agent.core.communications.matrix_sync import transport as matrix_transport
from ultimate_ai_agent.core.communications.matrix_sync import (
    InMemoryMatrixCredentialWriter,
    MatrixCredentialWriter,
    MatrixSyncCommand,
    MatrixSyncOperation,
    MatrixSyncTransientTarget,
    MatrixSyncTransport,
    MatrixSyncTransportError,
    MatrixTransientBatchError,
    MatrixTransientBatchRegistry,
    matrix_sync_private_ref,
    matrix_sync_request_fingerprint_ref,
    operation_result_from_transport,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync.transport import (
    _terminate_process_group,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
HARNESS_ORIGIN = "http://127.0.0.1:18008"
PSEUDONYMIZATION_SALT = b"s" * 32
_HARNESS_PORT_WAIT_SECONDS = 60
PYTEST_EXCLUSIVE_RESOURCE_MATRIX_LOOPBACK = True


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _command(
    operation: MatrixSyncOperation = MatrixSyncOperation.sync_read,
    **overrides: object,
) -> MatrixSyncCommand:
    now = utc_now()
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": "request-ref:msg-mx-006:transport",
        "task_ref": "task-ref:msg-mx-006:transport",
        "mission_ref": "mission-ref:msg-mx-006:transport",
        "run_ref": "run-ref:msg-mx-006:transport",
        "dispatch_ref": "dispatch-ref:msg-mx-006:transport",
        "idempotency_ref": "idempotency-ref:msg-mx-006:transport",
        "lease_ref": "authority-lease-ref:msg-mx-006:transport",
        "homeserver_ref": matrix_homeserver_ref(HARNESS_ORIGIN),
        "endpoint_class_ref": "endpoint-class-ref:matrix:local-harness",
        "account_ref": "account-ref:matrix:transport",
        "device_ref": "device-ref:matrix:transport",
        "session_ref": "session-ref:matrix:transport",
        "session_generation_ref": "session-generation-ref:matrix:transport:1",
        "credential_item_ref": "credential-item-ref:matrix:transport",
        "credential_version_ref": "credential-version-ref:matrix:transport:1",
        "room_refs": (),
        "event_class_refs": ("event-class-ref:matrix:message",),
        "sync_cursor_ref": "sync-cursor-ref:matrix:initial",
        "cache_ref": "cache-ref:matrix:transport",
        "cache_generation_ref": "cache-generation-ref:matrix:transport:0",
        "cache_key_item_ref": "cache-key-item-ref:matrix:transport",
        "cache_key_version_ref": "cache-key-version-ref:matrix:transport:1",
        "readiness_ref": "readiness-ref:matrix-sync:transport",
        "rollback_ref": "rollback-ref:matrix-sync:transport",
        "request_created_at": now,
        "start_deadline": now + timedelta(minutes=2),
    }
    if operation == MatrixSyncOperation.timeline_paginate_read:
        raw_room_id = "!private-room:example.invalid"
        raw_pagination_token = "private-page-token"
        values.update(
            room_refs=(
                matrix_sync_private_ref(
                    "room-ref:matrix", PSEUDONYMIZATION_SALT, raw_room_id
                ),
            ),
            pagination_cursor_ref=matrix_sync_private_ref(
                "pagination-cursor-ref:matrix",
                PSEUDONYMIZATION_SALT,
                raw_pagination_token,
            ),
        )
    values.update(overrides)
    values["request_fingerprint_ref"] = matrix_sync_request_fingerprint_ref(**values)
    return MatrixSyncCommand(**values)


class _Handler(BaseHTTPRequestHandler):
    server_version = "UAAMatrixSyncTest/1"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        if (
            self.path.startswith("/_matrix/client/v3/sync")
            and self.headers.get("Authorization") == "Bearer private-test-token"
        ):
            events = [
                {
                    "event_id": "$private-event",
                    "sender": "@private-sender:example.invalid",
                    "origin_server_ts": 1,
                    "type": "m.room.message",
                    "content": {
                        "msgtype": "m.text",
                        "body": "private body",
                    },
                }
            ]
            if getattr(self.server, "include_extra_event", False):
                events.append(
                    {
                        "event_id": "$private-event-two",
                        "sender": "@private-sender:example.invalid",
                        "origin_server_ts": 2,
                        "type": "m.room.message",
                        "content": {
                            "msgtype": "m.text",
                            "body": "second private body",
                        },
                    }
                )
            body = json.dumps(
                {
                    "next_batch": "private-next-token",
                    "rooms": {
                        "join": {
                            "!private-room:example.invalid": {
                                "timeline": {"events": events}
                            }
                        }
                    },
                    "account_data": {
                        "events": [
                            {
                                "type": "m.direct",
                                "content": {
                                    "@private-sender:example.invalid": [
                                        "!private-room:example.invalid"
                                    ]
                                },
                            }
                        ]
                    },
                },
                separators=(",", ":"),
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(403)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


@pytest.fixture
def loopback_server():  # type: ignore[no-untyped-def]
    server = _bind_loopback_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _bind_loopback_server() -> ThreadingHTTPServer:
    deadline = time.monotonic() + _HARNESS_PORT_WAIT_SECONDS
    while True:
        try:
            return ThreadingHTTPServer(("127.0.0.1", 18008), _Handler)
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            if time.monotonic() >= deadline:
                raise TimeoutError("MATRIX_TEST_HARNESS_PORT_BUSY") from exc
            time.sleep(0.05)


def test_loopback_server_binding_retries_bounded_port_contention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = sys.modules[__name__]
    expected = object()
    attempts = 0

    def bind_once_available(*_args: object, **_kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError(errno.EADDRINUSE, "busy")
        return expected

    monkeypatch.setattr(module, "ThreadingHTTPServer", bind_once_available)
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    assert _bind_loopback_server() is expected
    assert attempts == 2


def test_loopback_server_binding_rejects_persistent_port_contention(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = sys.modules[__name__]
    attempts = 0

    def always_busy(*_args: object, **_kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        raise OSError(errno.EADDRINUSE, "busy")

    monotonic_values = iter((0.0, _HARNESS_PORT_WAIT_SECONDS + 1.0))
    monkeypatch.setattr(module, "ThreadingHTTPServer", always_busy)
    monkeypatch.setattr(time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    with pytest.raises(TimeoutError, match="MATRIX_TEST_HARNESS_PORT_BUSY"):
        _bind_loopback_server()

    assert attempts == 1


def test_loopback_server_binding_preserves_non_contention_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = sys.modules[__name__]
    attempts = 0

    def denied(*_args: object, **_kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        raise OSError(errno.EACCES, "denied")

    monkeypatch.setattr(module, "ThreadingHTTPServer", denied)

    with pytest.raises(OSError) as caught:
        _bind_loopback_server()

    assert caught.value.errno == errno.EACCES
    assert attempts == 1


def _transport(
    writer: MatrixCredentialWriter,
    *,
    allow_loopback_harness: bool = True,
) -> MatrixSyncTransport:
    node = Path(shutil.which("node") or "")
    runner = ROOT / "integrations/matrix-client-adapter/src/sync-runner.mjs"
    return MatrixSyncTransport(
        node_binary=node.resolve(),
        runner_path=runner.resolve(),
        expected_node_sha256=_sha256(node.resolve()),
        expected_runner_sha256=_sha256(runner.resolve()),
        credential_writer=writer,
        registry=MatrixTransientBatchRegistry(),
        allow_loopback_harness=allow_loopback_harness,
    )


def test_transport_hands_credential_over_fd_and_keeps_raw_batch_transient(
    loopback_server: None,
) -> None:
    command = _command()
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    result = transport.execute(
        command,
        target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
        pseudonymization_salt=PSEUDONYMIZATION_SALT,
    )
    serialized_result = repr(result)
    assert result.event_count == 1
    assert "private-test-token" not in serialized_result
    assert "private body" not in serialized_result
    batch = transport.consume_batch(
        result.batch_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
    )
    assert batch.events[0].body == "private body"
    assert batch.rooms[0].is_direct is True
    with pytest.raises(
        MatrixTransientBatchError, match="MATRIX_TRANSIENT_BATCH_EXPIRED"
    ):
        transport.consume_batch(
            result.batch_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
        )


def test_transient_batch_scope_mismatch_does_not_destroy_owned_batch(
    loopback_server: None,
) -> None:
    command = _command()
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    result = transport.execute(
        command,
        target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
        pseudonymization_salt=PSEUDONYMIZATION_SALT,
    )

    with pytest.raises(
        MatrixTransientBatchError,
        match="MATRIX_TRANSIENT_BATCH_SCOPE_MISMATCH",
    ):
        transport.consume_batch(
            result.batch_ref,
            request_fingerprint_ref="request-fingerprint-ref:matrix-sync:other",
        )

    batch = transport.consume_batch(
        result.batch_ref,
        request_fingerprint_ref=command.request_fingerprint_ref,
    )
    assert batch.events[0].body == "private body"


def test_transport_result_owns_abort_cleanup_without_exposing_registry(
    loopback_server: None,
) -> None:
    command = _command()
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    transport_result = transport.execute(
        command,
        target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
        pseudonymization_salt=PSEUDONYMIZATION_SALT,
    )
    operation_result = operation_result_from_transport(result=transport_result)

    assert operation_result.abort_callback is not None
    assert "_discard_callback" not in repr(transport_result)
    operation_result.abort_callback()

    with pytest.raises(
        MatrixTransientBatchError,
        match="MATRIX_TRANSIENT_BATCH_EXPIRED",
    ):
        transport.consume_batch(
            transport_result.batch_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
        )


def test_pipe_creation_failure_releases_validated_runtime_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command()
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    snapshot = object()
    removed: list[object] = []
    monkeypatch.setattr(
        matrix_transport,
        "create_matrix_runtime_snapshot",
        lambda **_kwargs: snapshot,
    )
    monkeypatch.setattr(
        matrix_transport,
        "remove_matrix_runtime_snapshot",
        removed.append,
    )
    monkeypatch.setattr(os, "pipe", lambda: (_ for _ in ()).throw(OSError("denied")))

    with pytest.raises(OSError, match="denied"):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )

    assert removed == [snapshot]


def test_post_spawn_descriptor_failure_reaps_process_and_releases_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command()
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    original_pipe = os.pipe
    original_close = os.close
    original_popen = subprocess.Popen
    original_create_snapshot = matrix_transport.create_matrix_runtime_snapshot
    read_descriptors: list[int] = []
    processes: list[subprocess.Popen[bytes]] = []
    snapshots: list[object] = []
    injected = False

    def capture_pipe() -> tuple[int, int]:
        read_fd, write_fd = original_pipe()
        read_descriptors.append(read_fd)
        return read_fd, write_fd

    def fail_parent_read_close_once(descriptor: int) -> None:
        nonlocal injected
        original_close(descriptor)
        if read_descriptors and descriptor == read_descriptors[0] and not injected:
            injected = True
            raise OSError("injected post-spawn close failure")

    def capture_popen(*args, **kwargs):  # type: ignore[no-untyped-def]
        process = original_popen(*args, **kwargs)
        processes.append(process)
        return process

    def capture_snapshot(**kwargs):  # type: ignore[no-untyped-def]
        snapshot = original_create_snapshot(**kwargs)
        snapshots.append(snapshot)
        return snapshot

    monkeypatch.setattr(os, "pipe", capture_pipe)
    monkeypatch.setattr(os, "close", fail_parent_read_close_once)
    monkeypatch.setattr(matrix_transport.subprocess, "Popen", capture_popen)
    monkeypatch.setattr(
        matrix_transport,
        "create_matrix_runtime_snapshot",
        capture_snapshot,
    )

    with pytest.raises(OSError, match="injected post-spawn close failure"):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )

    assert injected is True
    assert len(processes) == 1
    assert processes[0].poll() is not None
    assert processes[0].stdin is not None and processes[0].stdin.closed
    assert processes[0].stdout is not None and processes[0].stdout.closed
    assert processes[0].stderr is not None and processes[0].stderr.closed
    assert len(snapshots) == 1
    assert not snapshots[0].root.exists()  # type: ignore[attr-defined]


def test_unavailable_credential_writer_fails_before_network(
    loopback_server: None,
) -> None:
    command = _command()
    transport = _transport(MatrixCredentialWriter())
    with pytest.raises(
        MatrixTransientBatchError,
        match="MATRIX_SYNC_CREDENTIAL_BROKER_UNAVAILABLE",
    ):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


def test_loopback_harness_is_disabled_by_default_before_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = _command()
    transport = _transport(
        InMemoryMatrixCredentialWriter(b"private-test-token"),
        allow_loopback_harness=False,
    )
    monkeypatch.setattr(
        os, "pipe", lambda: pytest.fail("pipe created before scope check")
    )
    with pytest.raises(
        MatrixSyncTransportError,
        match="MATRIX_SYNC_LOOPBACK_HARNESS_DISABLED",
    ):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


@pytest.mark.parametrize(
    ("command", "target", "expected"),
    [
        (
            _command(homeserver_ref="homeserver-ref:matrix:sha256:wrong"),
            MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            "MATRIX_SESSION_HOMESERVER_BINDING_MISMATCH",
        ),
        (
            _command(),
            MatrixSyncTransientTarget(
                base_url=HARNESS_ORIGIN,
                since_token="private-unbound-token",
            ),
            "MATRIX_SYNC_CURSOR_BINDING_MISMATCH",
        ),
        (
            _command(
                room_refs=(
                    matrix_sync_private_ref(
                        "room-ref:matrix",
                        PSEUDONYMIZATION_SALT,
                        "!private-room:example.invalid",
                    ),
                )
            ),
            MatrixSyncTransientTarget(
                base_url=HARNESS_ORIGIN,
                room_ids=("!different-room:example.invalid",),
            ),
            "MATRIX_SYNC_ROOM_BINDING_MISMATCH",
        ),
        (
            _command(event_class_refs=("event-class-ref:matrix:unknown",)),
            MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            "MATRIX_SYNC_EVENT_SCOPE_DENIED",
        ),
    ],
)
def test_transient_scope_drift_is_denied_before_any_pipe_or_process(
    monkeypatch: pytest.MonkeyPatch,
    command: MatrixSyncCommand,
    target: MatrixSyncTransientTarget,
    expected: str,
) -> None:
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    monkeypatch.setattr(
        os, "pipe", lambda: pytest.fail("pipe created before scope check")
    )
    with pytest.raises(MatrixSyncTransportError, match=expected):
        transport.execute(
            command,
            target=target,
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


def test_exact_pagination_room_and_cursor_are_bound_before_network(
    loopback_server: None,
) -> None:
    command = _command(MatrixSyncOperation.timeline_paginate_read)
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    with pytest.raises(
        MatrixSyncTransportError, match="MATRIX_SYNC_CURSOR_BINDING_MISMATCH"
    ):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(
                base_url=HARNESS_ORIGIN,
                room_id="!private-room:example.invalid",
                pagination_token="different-private-page-token",
            ),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


def test_untrusted_response_cannot_expand_event_scope(loopback_server: None) -> None:
    command = _command(
        event_class_refs=("event-class-ref:matrix:encrypted-placeholder",)
    )
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    with pytest.raises(ValueError, match="MATRIX_SYNC_EVENT_SCOPE_DENIED"):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


def test_untrusted_response_cannot_exceed_exact_event_budget(
    loopback_server: ThreadingHTTPServer,
) -> None:
    loopback_server.include_extra_event = True  # type: ignore[attr-defined]
    command = _command(max_events=2)
    transport = _transport(InMemoryMatrixCredentialWriter(b"private-test-token"))
    with pytest.raises(ValueError, match="MATRIX_SYNC_EVENT_LIMIT_EXCEEDED"):
        transport.execute(
            command,
            target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
            pseudonymization_salt=PSEUDONYMIZATION_SALT,
        )


class _FakeProcess:
    def __init__(self) -> None:
        self.pid = 73_001
        self.returncode: int | None = None
        self.wait_calls = 0

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, *, timeout: float) -> int:
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise subprocess.TimeoutExpired("matrix-sync", timeout)
        self.returncode = -signal.SIGKILL
        return self.returncode


def test_process_cleanup_escalates_term_to_kill_and_reaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _FakeProcess()
    signals: list[int] = []
    monkeypatch.setattr(os, "killpg", lambda _pid, sent: signals.append(sent))
    _terminate_process_group(process)  # type: ignore[arg-type]
    assert signals == [signal.SIGTERM, signal.SIGKILL]
    assert process.wait_calls == 2


def test_node_permission_mode_denies_child_process_runtime(tmp_path: Path) -> None:
    node = Path(shutil.which("node") or "").resolve()
    script = tmp_path / "child-process-denied.mjs"
    script.write_text(
        (
            'import { spawnSync } from "node:child_process";\n'
            'spawnSync("/usr/bin/true");\n'
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            str(node),
            "--permission",
            f"--allow-fs-read={tmp_path}",
            str(script),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "HOME": "/var/empty",
            "LANG": "C",
            "PATH": "/usr/bin:/bin",
            "TMPDIR": "/tmp",
        },
        start_new_session=True,
        shell=False,
        timeout=5,
        check=False,
    )
    assert completed.returncode != 0
    assert b"ERR_ACCESS_DENIED" in completed.stderr
    assert b"ChildProcess" in completed.stderr


def test_transport_uses_minimal_environment_and_adapter_working_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _CompletedProcess:
        pid = 73_002
        returncode = 0

        def communicate(
            self, _payload: bytes, *, timeout: float
        ) -> tuple[bytes, bytes]:
            assert timeout > 0
            return b'{"next_batch":"private-next-token","rooms":{}}', b""

        def poll(self) -> int:
            return 0

    def fake_popen(*args: object, **kwargs: object) -> _CompletedProcess:
        captured["args"] = args
        captured.update(kwargs)
        return _CompletedProcess()

    class _NoopCredentialWriter(MatrixCredentialWriter):
        def write_once(self, fd: int, **_kwargs: str) -> None:
            del fd

    transport = _transport(_NoopCredentialWriter())
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    result = transport.execute(
        _command(),
        target=MatrixSyncTransientTarget(base_url=HARNESS_ORIGIN),
        pseudonymization_salt=PSEUDONYMIZATION_SALT,
    )
    assert result.event_count == 0
    assert captured["shell"] is False
    argv = captured["args"][0]  # type: ignore[index]
    assert Path(argv[0]).name == "node-runtime"
    assert argv[1] == "--permission"
    assert argv[2] == f"--allow-fs-read={Path(argv[3]).parent.parent}"
    assert Path(argv[3]).parts[-3:] == ("adapter", "src", "sync-runner.mjs")
    assert captured["cwd"] == Path(argv[3]).parent.parent
    assert captured["env"] == {
        "HOME": "/var/empty",
        "LANG": "C",
        "PATH": "/usr/bin:/bin",
        "TMPDIR": "/tmp",
    }
