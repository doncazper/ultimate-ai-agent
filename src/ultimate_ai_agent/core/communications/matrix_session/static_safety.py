"""Exact static-scan exception for the governed Matrix session adapter."""

from __future__ import annotations

import hashlib


MATRIX_SESSION_BACKEND_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_session/backend.py"
)
_REVIEWED_MATRIX_SESSION_BACKEND_SHA256 = (
    "b9b3902bbfc88cd861948eae7cabf5b8551d71eaee72863a6a861ca99aa5948a"
)
_POPEN = "subprocess" + ".Popen("
_HOME = "Path." + "home("
_RUNTIME_TREE_SCAN = ".rglob(" + '"*"' + ")"


def is_exact_matrix_session_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_SESSION_BACKEND_REL or fragment != _POPEN:
        return False
    if (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        != _REVIEWED_MATRIX_SESSION_BACKEND_SHA256
    ):
        return False
    required = (
        "start_new_session=True",
        'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}',
        "stdin=" + "subprocess" + ".PIPE",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".DEVNULL",
        "os.killpg(process.pid, signal.SIGTERM)",
        "os.killpg(process.pid, signal.SIGKILL)",
        "MATRIX_SESSION_ADAPTER_INPUT_MAX_BYTES = 128 * 1024",
        "MATRIX_SESSION_ADAPTER_RESPONSE_MAX_BYTES = 128 * 1024",
        "validate_transient_target",
        "_validate_runtime_integrity",
        'os.fspath(runtime_snapshot.node_binary)',
        '"--permission"',
        'f"--allow-fs-read={runtime_snapshot.adapter_root}"',
        "os.fspath(runtime_snapshot.runner_path)",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".call(",
        "subprocess" + ".run(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
    )
    return (
        source.count(_POPEN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def is_exact_matrix_session_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_session_subprocess_site(
        rel_path=rel_path, source=source, fragment=_POPEN
    ):
        return False
    return (
        stripped_line == "import " + "subprocess" or "subprocess" + "." in stripped_line
    )


def matrix_session_fragment_allowed(rel_path: str, source: str, fragment: str) -> bool:
    if fragment == "import " + "subprocess":
        fragment = _POPEN
    return is_exact_matrix_session_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )


def is_exact_matrix_session_bounded_filesystem_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_SESSION_BACKEND_REL:
        return False
    if not is_exact_matrix_session_subprocess_site(
        rel_path=rel_path, source=source, fragment=_POPEN
    ):
        return False
    if fragment == _HOME:
        return (
            source.count(_HOME) == 1
            and "Path." + 'home() / ".local" / "share" / "uaa" / "helpers"' in source
            and "_read_safe_private_metadata_file(metadata_path)" in source
        )
    if fragment == _RUNTIME_TREE_SCAN:
        required = (
            'for path in sorted(root.rglob("*"), reverse=True):',
            "os.chmod(path, 0o500 if path.is_dir() else 0o400)",
            'entries = tuple(root.rglob("*"))',
            "if len(entries) > 100_000:",
            'entries = sorted(root.rglob("*"))',
            "_validate_runtime_integrity(",
            "metadata = os.lstat(path)",
            "stat.S_ISLNK(metadata.st_mode)",
            "not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode))",
            "metadata.st_uid != os.getuid()",
            "metadata.st_mode & 0o022",
            "_require_safe_regular_file(path)",
            "relative = path.relative_to(root).as_posix().encode()",
            "shutil.rmtree(root)",
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_CLEANUP_LIMIT_EXCEEDED",
            "MATRIX_SESSION_RUNTIME_SNAPSHOT_CLEANUP_UNSAFE",
            "MATRIX_SESSION_RUNTIME_TREE_UNSAFE",
        )
        return source.count(_RUNTIME_TREE_SCAN) == 3 and all(
            marker in source for marker in required
        )
    return False


__all__ = (
    "MATRIX_SESSION_BACKEND_REL",
    "is_exact_matrix_session_bounded_filesystem_site",
    "is_exact_matrix_session_shell_scan_line",
    "is_exact_matrix_session_subprocess_site",
    "matrix_session_fragment_allowed",
)
