"""Exact static-scan exception for the governed Matrix session adapter."""

from __future__ import annotations


MATRIX_SESSION_BACKEND_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_session/backend.py"
)
_POPEN = "subprocess" + ".Popen("
_HOME = "Path." + "home("
_RUNTIME_TREE_SCAN = ".rglob(" + '"*"' + ")"


def is_exact_matrix_session_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_SESSION_BACKEND_REL or fragment != _POPEN:
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
            "if not root.is_dir() or root.is_symlink()",
            "_require_safe_regular_file(path)",
            "relative = path.relative_to(root)",
            "len(trees) > 64",
            'set(item) != {"root", "sha256"}',
            '".." in Path(relative).parts',
            "root.resolve().is_relative_to(adapter_root) is False",
        )
        return source.count(_RUNTIME_TREE_SCAN) == 1 and all(
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
