"""Exact static-scan profile for the macOS protected-cache helper."""

from __future__ import annotations


MATRIX_CACHE_CRYPTO_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_sync/macos_cache_crypto.py"
)
MATRIX_SYNC_TRANSPORT_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_sync/transport.py"
)
_SUBPROCESS_RUN = "subprocess" + ".run("
_SUBPROCESS_POPEN = "subprocess" + ".Popen("


def is_exact_matrix_sync_transport_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_SYNC_TRANSPORT_REL or fragment != _SUBPROCESS_POPEN:
        return False
    required = (
        "start_new_session=True",
        "pass_fds=(read_fd,)",
        "stdin=" + "subprocess" + ".PIPE",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".PIPE",
        "shell=False",
        "cwd=self._adapter_root",
        "env=_MINIMAL_SUBPROCESS_ENV",
        "os.killpg(process.pid, signal.SIGTERM)",
        "os.killpg(process.pid, signal.SIGKILL)",
        "process.wait(timeout=grace_seconds)",
        "MATRIX_SYNC_MAX_BYTES",
        "validate_matrix_adapter_runtime_integrity(",
        "_validate_file(node_binary",
        "_validate_file(runner_path",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".run(",
        "subprocess" + ".call(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
    )
    return (
        source.count(_SUBPROCESS_POPEN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def is_exact_matrix_cache_crypto_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_CACHE_CRYPTO_REL or fragment != _SUBPROCESS_RUN:
        return False
    required = (
        "shell=False",
        "start_new_session=True",
        'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}',
        "input=encoded",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".PIPE",
        "timeout=self._timeout_seconds",
        "MACOS_MATRIX_CACHE_HELPER_MAX_INPUT_BYTES",
        "MACOS_MATRIX_CACHE_HELPER_MAX_OUTPUT_BYTES",
        "self._open_validated_helper()",
        "os.O_EXCL",
        'getattr(os, "O_NOFOLLOW", 0)',
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".Popen(",
        "subprocess" + ".call(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
    )
    return (
        source.count(_SUBPROCESS_RUN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def is_exact_matrix_cache_crypto_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_cache_crypto_subprocess_site(
        rel_path=rel_path, source=source, fragment=_SUBPROCESS_RUN
    ):
        return False
    return (
        stripped_line == "import " + "subprocess"
        or "subprocess" + "." in stripped_line
    )


def is_exact_matrix_sync_transport_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path, source=source, fragment=_SUBPROCESS_POPEN
    ):
        return False
    return (
        stripped_line == "import " + "subprocess"
        or "subprocess" + "." in stripped_line
    )


def matrix_sync_fragment_allowed(rel_path: str, source: str, fragment: str) -> bool:
    """Accept only either complete MSG-MX-006 subprocess profile."""
    if fragment == "import " + "subprocess":
        if rel_path == MATRIX_CACHE_CRYPTO_REL:
            fragment = _SUBPROCESS_RUN
        elif rel_path == MATRIX_SYNC_TRANSPORT_REL:
            fragment = _SUBPROCESS_POPEN
    return is_exact_matrix_cache_crypto_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ) or is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )


__all__ = (
    "MATRIX_CACHE_CRYPTO_REL",
    "MATRIX_SYNC_TRANSPORT_REL",
    "is_exact_matrix_cache_crypto_shell_scan_line",
    "is_exact_matrix_cache_crypto_subprocess_site",
    "is_exact_matrix_sync_transport_shell_scan_line",
    "is_exact_matrix_sync_transport_subprocess_site",
    "matrix_sync_fragment_allowed",
)
