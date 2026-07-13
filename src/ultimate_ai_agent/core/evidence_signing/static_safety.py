from __future__ import annotations

import ast
import hashlib


_RUN_FRAGMENT = "subprocess" + ".run("
_IMPORT_FRAGMENT = "import " + "subprocess"
_HOME_FRAGMENT = "Path." + "home("
_HOME_ROOT_MARKER = 'Path.' + 'home() / ".local" / "share" / "uaa" / "helpers"'
_BACKEND_REL = "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py"
_BACKEND_SOURCE_SHA256 = (
    "1a3dbfd0def12c8a20eb06d24edbff779315493cc259c21dc8c3d5e3d101a7b1"
)
_ALLOWED_SUBPROCESS_ATTRIBUTES = frozenset({"PIPE", "TimeoutExpired", "run"})
_UNRELATED_FORBIDDEN_MARKERS = (
    "subprocess" + ".Popen(",
    "subprocess" + ".call(",
    "subprocess" + ".check_call(",
    "subprocess" + ".check_output(",
    "os." + "system(",
    "shell" + "=True",
    "import " + "requests",
    "from " + "requests import",
    "requests" + ".",
    "import " + "httpx",
    "from " + "httpx import",
    "httpx" + ".",
    "urllib" + ".request",
    "socket" + ".",
    "os" + ".environ",
    "os" + ".getenv(",
)
_REQUIRED_MARKERS = (
    'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}',
    "input=encoded",
    "cwd=temporary_dir",
    "timeout=self._timeout_seconds",
    "check=False",
    "shell=False",
    "start_new_session=True",
    "MACOS_KEYCHAIN_HELPER_MAX_INPUT_BYTES",
    "MACOS_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES",
    "PORTABLE_EVIDENCE_HELPER_COPY_FINGERPRINT_MISMATCH",
)


def is_exact_portable_evidence_helper_subprocess_site(
    *,
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    """Admit only the hash-pinned, bounded macOS Keychain helper invocation."""

    if (
        rel_path != _BACKEND_REL
        or fragment != _RUN_FRAGMENT
        or hashlib.sha256(source.encode("utf-8")).hexdigest() != _BACKEND_SOURCE_SHA256
        or source.count(_RUN_FRAGMENT) != 1
        or source.count("subprocess" + ".PIPE") != 2
        or source.count("subprocess" + ".TimeoutExpired") != 1
        or any(marker in source for marker in _UNRELATED_FORBIDDEN_MARKERS)
        or not all(marker in source for marker in _REQUIRED_MARKERS)
    ):
        return False
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    subprocess_imports = 0
    run_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            subprocess_imports += sum(
                alias.name == "subprocess" and alias.asname is None
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            return False
        if not (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "subprocess"
        ):
            continue
        if node.attr not in _ALLOWED_SUBPROCESS_ATTRIBUTES:
            return False
        if isinstance(node.ctx, ast.Store):
            return False
        if node.attr == "run" and isinstance(node.ctx, ast.Load):
            run_calls += 1
    return subprocess_imports == 1 and run_calls == 1


def portable_evidence_helper_fragment_allowed(
    rel_path: str, source: str, fragment: str
) -> bool:
    """Permit only reviewed import/run fragments at the exact helper site."""

    if fragment not in {_IMPORT_FRAGMENT, _RUN_FRAGMENT}:
        return False
    return is_exact_portable_evidence_helper_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_RUN_FRAGMENT,
    )


def is_exact_portable_evidence_helper_home_path(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    """Admit only the fixed per-user helper install root, never a broad scan."""

    return (
        fragment == _HOME_FRAGMENT
        and source.count(_HOME_FRAGMENT) == 1
        and _HOME_ROOT_MARKER in source
        and is_exact_portable_evidence_helper_subprocess_site(
            rel_path=rel_path,
            source=source,
            fragment=_RUN_FRAGMENT,
        )
    )
