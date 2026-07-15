"""Exact static-scan exception for the bounded Matrix harness backend."""

from __future__ import annotations


MATRIX_HARNESS_BACKEND_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_harness/backend.py"
)
_SUBPROCESS_POPEN = "subprocess" + ".Popen("


def is_exact_matrix_harness_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    """Allow only the reviewed fixed-argv, local Docker harness boundary."""

    if rel_path != MATRIX_HARNESS_BACKEND_REL:
        return False
    if fragment != _SUBPROCESS_POPEN:
        return False
    required = (
        '"--project-name",\n            "uaa-matrix-harness",',
        '"--pull",\n                "never",',
        "start_new_session=True",
        "shell=False",
        "stdin=" + "subprocess" + ".DEVNULL",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".PIPE",
        "os.killpg(process.pid, signal.SIGTERM)",
        "os.killpg(process.pid, signal.SIGKILL)",
        "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES = 64 * 1024",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".call(",
        "subprocess" + ".check_call(",
        "subprocess" + ".check_output(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
        "socket" + ".socket(",
    )
    return (
        source.count(_SUBPROCESS_POPEN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
    )


def is_exact_matrix_harness_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_SUBPROCESS_POPEN,
    ):
        return False
    return (
        stripped_line == "import " + "subprocess"
        or "subprocess" + "." in stripped_line
    )


def matrix_harness_fragment_allowed(
    rel_path: str, source: str, fragment: str
) -> bool:
    if fragment == "import " + "subprocess":
        fragment = _SUBPROCESS_POPEN
    return is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )


__all__ = (
    "MATRIX_HARNESS_BACKEND_REL",
    "is_exact_matrix_harness_shell_scan_line",
    "is_exact_matrix_harness_subprocess_site",
    "matrix_harness_fragment_allowed",
)
