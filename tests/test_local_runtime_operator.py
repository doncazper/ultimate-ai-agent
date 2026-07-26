from __future__ import annotations

from pathlib import Path

import pytest

import scripts.dev.uaa_local_runtime as operator


SHA = "a" * 40
LOCAL_BEARER = "local-runtime-test-bearer"


def test_verified_operator_up_orders_source_proof_before_secret_handoff(
    monkeypatch,
    capsys,
) -> None:
    events: list[tuple[object, ...]] = []

    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda root: events.append(("verify", root)) or SHA,
    )
    monkeypatch.setattr(
        operator.secrets,
        "token_urlsafe",
        lambda length: events.append(("secret", length)) or LOCAL_BEARER,
    )
    monkeypatch.setattr(
        operator,
        "_write_private_text",
        lambda path, value: events.append(("write", path.name, value)),
    )
    monkeypatch.setattr(
        operator,
        "_run_compose",
        lambda arguments, *, commit: events.append(
            ("compose", arguments, commit)
        ),
    )
    monkeypatch.setattr(
        operator.webbrowser,
        "open",
        lambda url: events.append(("open", url)) or True,
    )

    operator._verified_up()

    assert events[0] == ("verify", operator.ROOT)
    compose_index = next(
        index for index, event in enumerate(events) if event[0] == "compose"
    )
    open_index = next(
        index for index, event in enumerate(events) if event[0] == "open"
    )
    assert open_index > compose_index > 0
    assert events[compose_index] == (
        "compose",
        ["up", "--build", "--detach", "--wait"],
        SHA,
    )
    opened_url = str(events[open_index][1])
    assert "#uaa-session-bearer=" in opened_url
    assert LOCAL_BEARER in opened_url
    assert LOCAL_BEARER not in capsys.readouterr().out


def test_verified_operator_up_keeps_healthy_stack_successful_without_browser(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda _root: SHA,
    )
    monkeypatch.setattr(operator.secrets, "token_urlsafe", lambda _length: LOCAL_BEARER)
    monkeypatch.setattr(operator, "_write_private_text", lambda _path, _value: None)
    monkeypatch.setattr(
        operator,
        "_run_compose",
        lambda _arguments, *, commit: None,
    )
    monkeypatch.setattr(operator.webbrowser, "open", lambda _url: False)

    operator._verified_up()

    captured = capsys.readouterr()
    assert "OK: local runtime started" in captured.out
    assert "browser handoff was unavailable" in captured.err
    assert LOCAL_BEARER not in captured.out
    assert LOCAL_BEARER not in captured.err


def test_verified_operator_up_keeps_healthy_stack_successful_on_browser_error(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda _root: SHA,
    )
    monkeypatch.setattr(operator.secrets, "token_urlsafe", lambda _length: LOCAL_BEARER)
    monkeypatch.setattr(operator, "_write_private_text", lambda _path, _value: None)
    monkeypatch.setattr(
        operator,
        "_run_compose",
        lambda _arguments, *, commit: None,
    )

    def fail_browser_handoff(_url):
        raise operator.webbrowser.Error("browser unavailable")

    monkeypatch.setattr(operator.webbrowser, "open", fail_browser_handoff)

    operator._verified_up()

    captured = capsys.readouterr()
    assert "OK: local runtime started" in captured.out
    assert "browser handoff was unavailable" in captured.err
    assert LOCAL_BEARER not in captured.out
    assert LOCAL_BEARER not in captured.err


def test_verified_operator_up_restores_existing_runtime_state_on_startup_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    secret_file = tmp_path / "state" / "secret"
    source_file = tmp_path / "state" / "source"
    secret_file.parent.mkdir()
    secret_file.write_bytes(b"prior-secret\n")
    source_file.write_bytes(b"b" * 40 + b"\n")
    secret_file.chmod(0o640)
    source_file.chmod(0o600)
    monkeypatch.setattr(operator, "SECRET_FILE", secret_file)
    monkeypatch.setattr(operator, "SOURCE_COMMIT_FILE", source_file)
    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda _root: SHA,
    )
    monkeypatch.setattr(operator.secrets, "token_urlsafe", lambda _length: LOCAL_BEARER)

    def fail_startup(_arguments, *, commit):
        raise RuntimeError("compose failed")

    monkeypatch.setattr(operator, "_run_compose", fail_startup)

    with pytest.raises(RuntimeError, match="compose failed"):
        operator._verified_up()

    assert secret_file.read_bytes() == b"prior-secret\n"
    assert source_file.read_bytes() == b"b" * 40 + b"\n"
    assert secret_file.stat().st_mode & 0o777 == 0o640
    assert source_file.stat().st_mode & 0o777 == 0o600


def test_verified_operator_up_restores_partial_state_write_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    secret_file = tmp_path / "state" / "secret"
    source_file = tmp_path / "state" / "source"
    secret_file.parent.mkdir()
    secret_file.write_bytes(b"prior-secret\n")
    source_file.write_bytes(b"b" * 40 + b"\n")
    monkeypatch.setattr(operator, "SECRET_FILE", secret_file)
    monkeypatch.setattr(operator, "SOURCE_COMMIT_FILE", source_file)
    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda _root: SHA,
    )
    monkeypatch.setattr(operator.secrets, "token_urlsafe", lambda _length: LOCAL_BEARER)
    real_write = operator._write_private_text

    def fail_second_write(path, value):
        if path == source_file:
            raise OSError("source state write failed")
        real_write(path, value)

    monkeypatch.setattr(operator, "_write_private_text", fail_second_write)

    with pytest.raises(OSError, match="source state write failed"):
        operator._verified_up()

    assert secret_file.read_bytes() == b"prior-secret\n"
    assert source_file.read_bytes() == b"b" * 40 + b"\n"


def test_verified_operator_up_removes_new_runtime_state_on_startup_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    secret_file = tmp_path / "state" / "secret"
    source_file = tmp_path / "state" / "source"
    monkeypatch.setattr(operator, "SECRET_FILE", secret_file)
    monkeypatch.setattr(operator, "SOURCE_COMMIT_FILE", source_file)
    monkeypatch.setattr(
        operator,
        "verified_clean_source_commit",
        lambda _root: SHA,
    )
    monkeypatch.setattr(operator.secrets, "token_urlsafe", lambda _length: LOCAL_BEARER)

    def fail_startup(_arguments, *, commit):
        raise RuntimeError("compose failed")

    monkeypatch.setattr(operator, "_run_compose", fail_startup)

    with pytest.raises(RuntimeError, match="compose failed"):
        operator._verified_up()

    assert not secret_file.exists()
    assert not source_file.exists()
