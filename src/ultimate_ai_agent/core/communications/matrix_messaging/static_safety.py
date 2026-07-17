"""Exact static-scan profiles for MSG-MX-008 native process boundaries."""

from __future__ import annotations

import hashlib


MATRIX_MESSAGING_BROKER_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_messaging/broker.py"
)
MATRIX_MESSAGING_NOTIFIER_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_messaging/notifier.py"
)
_POPEN = "subprocess" + ".Popen("
_RUN = "subprocess" + ".run("
_SOCKET = "socket" + "."
_SUBPROCESS_PREFIX = "subprocess" + "."
_REVIEWED_BROKER_SHA256 = (
    "f7297f0cb0263e8e803333409b2c538c865fa2d217f2f8ef5b582de1d1d3a2b9"
)
_REVIEWED_NOTIFIER_SHA256 = (
    "c82c1bf407b83059269d12bb7e2ed0d62ae407eb1027aed4cfd9c3497dd1f4ed"
)


def is_exact_matrix_messaging_broker_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_MESSAGING_BROKER_REL or fragment not in {
        _POPEN,
        _SOCKET,
    }:
        return False
    if hashlib.sha256(source.encode()).hexdigest() != _REVIEWED_BROKER_SHA256:
        return False
    required = (
        "MATRIX_BROKER_MAX_EXECUTABLE_BYTES = 64 * 1024 * 1024",
        "_open_validated_binary(",
        "_staged_broker_binary(",
        'prefix="uaa-matrix-rust-broker-"',
        'dir="/tmp"',
        'getattr(os, "O_NOFOLLOW", 0)',
        "os.fstat(descriptor)",
        "(opened.st_dev, opened.st_ino)",
        "copied.hexdigest() != digest",
        "stdin=subprocess" + ".DEVNULL",
        "stdout=subprocess" + ".PIPE",
        "stderr=subprocess" + ".DEVNULL",
        "cwd=executable.parent",
        "shell=False",
        "close_fds=True",
        "pass_fds=(auth_read_fd, root_read_fd)",
        "start_new_session=True",
        '"PATH": "/usr/bin:/bin"',
        '"RUST_BACKTRACE": "0"',
        '"TMPDIR": "/tmp"',
        "def signal_process(value: signal.Signals)",
        "os.killpg(process.pid, value)",
        "process.send_signal(value)",
        "signal_process(signal.SIGTERM)",
        "signal_process(signal.SIGKILL)",
        "MATRIX_BROKER_PROCESS_CLEANUP_FAILED",
        "process.wait(timeout=2)",
        '("127.0.0.1", port)',
        "hmac.compare_digest(expected_tag, response_envelope.auth_tag)",
        "_validate_response_binding(response, invocation)",
        "MATRIX_BROKER_RESPONSE_BINDING_MISMATCH",
        "MATRIX_BROKER_STATE_ROOT_SUBSTITUTION_DENIED",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".run(",
        "subprocess" + ".call(",
        "subprocess" + ".getoutput(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
        "env=os.environ",
    )
    return (
        source.count(_POPEN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def is_exact_matrix_messaging_notifier_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_MESSAGING_NOTIFIER_REL or fragment != _RUN:
        return False
    if hashlib.sha256(source.encode()).hexdigest() != _REVIEWED_NOTIFIER_SHA256:
        return False
    required = (
        '_OSASCRIPT = Path("/usr/bin/osascript")',
        'display notification "New Matrix activity" with title "UAA Messenger"',
        "MATRIX_DESKTOP_NOTIFICATION_EXECUTABLE_SUBSTITUTION_DENIED",
        "info.st_uid != 0",
        "info.st_mode & 0o022",
        "stdin=subprocess" + ".DEVNULL",
        "stdout=subprocess" + ".DEVNULL",
        "stderr=subprocess" + ".DEVNULL",
        "timeout=5",
        "check=False",
        "shell=False",
        "start_new_session=True",
        'env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"}',
        "command.notification_target_ref",
        "command.notification_policy_ref",
        "command.notification_disclosure_ref",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".Popen(",
        "subprocess" + ".call(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
        "command.body",
        "formatted_body",
    )
    return (
        source.count(_RUN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def matrix_messaging_fragment_allowed(
    rel_path: str, source: str, fragment: str
) -> bool:
    if fragment == "import " + "subprocess":
        if rel_path == MATRIX_MESSAGING_BROKER_REL:
            fragment = _POPEN
        elif rel_path == MATRIX_MESSAGING_NOTIFIER_REL:
            fragment = _RUN
    return is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ) or is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )


def is_exact_matrix_messaging_broker_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_POPEN,
    ):
        return False
    return (
        stripped_line == "import " + "subprocess" or _SUBPROCESS_PREFIX in stripped_line
    )


def is_exact_matrix_messaging_notifier_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_RUN,
    ):
        return False
    return (
        stripped_line == "import " + "subprocess" or _SUBPROCESS_PREFIX in stripped_line
    )


__all__ = (
    "MATRIX_MESSAGING_BROKER_REL",
    "MATRIX_MESSAGING_NOTIFIER_REL",
    "is_exact_matrix_messaging_broker_subprocess_site",
    "is_exact_matrix_messaging_broker_shell_scan_line",
    "is_exact_matrix_messaging_notifier_subprocess_site",
    "is_exact_matrix_messaging_notifier_shell_scan_line",
    "matrix_messaging_fragment_allowed",
)
