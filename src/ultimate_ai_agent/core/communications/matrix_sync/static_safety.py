"""Exact static-scan profile for the macOS protected-cache helper."""

from __future__ import annotations

import hashlib


MATRIX_CACHE_CRYPTO_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_sync/macos_cache_crypto.py"
)
MATRIX_SYNC_TRANSPORT_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_sync/transport.py"
)
_SUBPROCESS_RUN = "subprocess" + ".run("
_SUBPROCESS_POPEN = "subprocess" + ".Popen("
_REVIEWED_MATRIX_SYNC_TRANSPORT_SHA256 = (
    "b0f22d2c3094ef2257663dd2a4e7f1750d26afb88e2c110653c90b9ab6172a15"
)
_REVIEWED_MATRIX_CACHE_CRYPTO_SHA256 = (
    "83462fb73886d2e2853e0556c29f4c8e25b963841eefed39c0b94be46b12c051"
)


def is_exact_matrix_sync_transport_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if rel_path != MATRIX_SYNC_TRANSPORT_REL or fragment != _SUBPROCESS_POPEN:
        return False
    if (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        != _REVIEWED_MATRIX_SYNC_TRANSPORT_SHA256
    ):
        return False
    required = (
        "start_new_session=True",
        "pass_fds=(read_fd,)",
        "stdin=" + "subprocess" + ".PIPE",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".PIPE",
        "shell=False",
        "cwd=runtime_snapshot.adapter_root",
        "env=matrix_node_runtime_environment(",
        "os.killpg(process.pid, signal.SIGTERM)",
        "os.killpg(process.pid, signal.SIGKILL)",
        "process.wait(timeout=grace_seconds)",
        '"--permission"',
        'f"--allow-fs-read={runtime_snapshot.adapter_root}"',
        "MATRIX_SYNC_MAX_BYTES",
        "validate_matrix_adapter_runtime_integrity(",
        "_validate_file(node_binary",
        "_validate_file(runner_path",
        '"allow_loopback_harness": self._allow_loopback_harness',
        '"credential_writer_binding_ref"',
        "node_runtime_binding_ref",
        "node_runtime_profile_ref",
        '"registry_binding_ref": self._registry.binding_ref',
        "resolve_approved_matrix_node_runtime_binding(",
        "MatrixCredentialWriter.write_once(",
        "InMemoryMatrixCredentialWriter.write_once(",
        "MatrixTransientBatchRegistry.register(",
        'getattr(process, "stdin", None)',
        'getattr(process, "stdout", None)',
        'getattr(process, "stderr", None)',
        "if stream is not None and not stream.closed:",
        "stream.close()",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".run(",
        "subprocess" + ".call(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
        '"--allow-child-process"',
        '"--allow-worker"',
        '"--allow-addons"',
        '"NODE_OPTIONS"',
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
    if (
        hashlib.sha256(source.encode("utf-8")).hexdigest()
        != _REVIEWED_MATRIX_CACHE_CRYPTO_SHA256
    ):
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
        "subprocess" + ".getoutput(",
        "subprocess" + ".getstatusoutput(",
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
        stripped_line == "import " + "subprocess" or "subprocess" + "." in stripped_line
    )


def is_exact_matrix_sync_transport_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path, source=source, fragment=_SUBPROCESS_POPEN
    ):
        return False
    return (
        stripped_line == "import " + "subprocess" or "subprocess" + "." in stripped_line
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
