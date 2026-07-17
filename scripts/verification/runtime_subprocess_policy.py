"""Exact subprocess exceptions shared by the legacy runtime safety scans."""

from __future__ import annotations

from ultimate_ai_agent.core.evidence_signing.static_safety import (
    is_exact_portable_evidence_helper_home_path,
    is_exact_portable_evidence_helper_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_harness.static_safety import (
    is_exact_matrix_harness_shell_scan_line,
    is_exact_matrix_harness_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_session.static_safety import (
    is_exact_matrix_session_bounded_filesystem_site,
    is_exact_matrix_session_shell_scan_line,
    is_exact_matrix_session_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_sync.static_safety import (
    is_exact_matrix_cache_crypto_shell_scan_line,
    is_exact_matrix_cache_crypto_subprocess_site,
    is_exact_matrix_sync_transport_shell_scan_line,
    is_exact_matrix_sync_transport_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_messaging.static_safety import (
    is_exact_matrix_messaging_broker_shell_scan_line,
    is_exact_matrix_messaging_broker_subprocess_site,
    is_exact_matrix_messaging_notifier_shell_scan_line,
    is_exact_matrix_messaging_notifier_subprocess_site,
)
from ultimate_ai_agent.core.sandbox_calculation.static_safety import (
    is_exact_sealed_calculation_subprocess_site,
)


GOVERNED_RUNTIME_COMMAND_ADAPTER_REL = (
    "src/ultimate_ai_agent/core/runtime_gateway/command.py"
)
PORTABLE_EVIDENCE_KEYCHAIN_ADAPTER_REL = (
    "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py"
)
__all__ = (
    "is_exact_matrix_session_bounded_filesystem_site",
    "is_exact_portable_evidence_helper_home_path",
)


def _is_exact_governed_runtime_command_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    if is_exact_sealed_calculation_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_portable_evidence_helper_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_session_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_cache_crypto_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_messaging_broker_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if is_exact_matrix_messaging_notifier_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    ):
        return True
    if rel_path != GOVERNED_RUNTIME_COMMAND_ADAPTER_REL:
        return False
    if fragment != "subprocess.run(":
        return False
    return (
        source.count("subprocess.run(") == 1
        and "subprocess.Popen(" not in source
        and "shell" + "=True" not in source
        and "shell=False" in source
        and "os.system(" not in source
        and "popen(" not in source.lower().replace("subprocess.Popen(", "")
    )


def _is_exact_governed_runtime_command_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if is_exact_matrix_harness_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if is_exact_matrix_session_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if is_exact_matrix_cache_crypto_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if is_exact_matrix_sync_transport_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if is_exact_matrix_messaging_broker_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if is_exact_matrix_messaging_notifier_shell_scan_line(
        rel_path=rel_path,
        source=source,
        stripped_line=stripped_line,
    ):
        return True
    if not _is_exact_governed_runtime_command_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.run(",
    ):
        return False
    return (
        stripped_line == "import subprocess"
        or (
            rel_path == "src/ultimate_ai_agent/core/sandbox_calculation/backend.py"
            and "subprocess." in stripped_line
        )
        or (
            rel_path == PORTABLE_EVIDENCE_KEYCHAIN_ADAPTER_REL
            and "subprocess." in stripped_line
        )
        or "subprocess.run(" in stripped_line
        or "subprocess.TimeoutExpired" in stripped_line
    )
