"""Exact static exception for the sealed governed-browser Keychain helper."""

from __future__ import annotations

import ast
import hashlib


_RUN_FRAGMENT = "subprocess" + ".run("
_IMPORT_FRAGMENT = "import " + "subprocess"
_ADAPTER_REL = (
    "src/ultimate_ai_agent/core/governed_browser/browser_keychain.py"
)
_ADAPTER_SOURCE_SHA256 = (
    "daf894902fe4e4d2820876a41575939417589eb6a67e65331a81806f392d84d6"
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
    "Path." + "home(",
)
_REQUIRED_MARKERS = (
    'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}',
    "input=encoded",
    "cwd=temporary_dir",
    "timeout=self._timeout_seconds",
    "check=False",
    "shell=False",
    "start_new_session=True",
    "GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_INPUT_BYTES",
    "GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES",
    "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_FINGERPRINT_MISMATCH",
)


def is_exact_governed_browser_keychain_subprocess_site(
    *,
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    """Admit only the reviewed hash-pinned, bounded local helper invocation."""

    if (
        rel_path != _ADAPTER_REL
        or fragment != _RUN_FRAGMENT
        or hashlib.sha256(source.encode("utf-8")).hexdigest()
        != _ADAPTER_SOURCE_SHA256
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


def governed_browser_keychain_fragment_allowed(
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    """Permit only the reviewed import/run fragments at the exact adapter."""

    if fragment not in {_IMPORT_FRAGMENT, _RUN_FRAGMENT}:
        return False
    return is_exact_governed_browser_keychain_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_RUN_FRAGMENT,
    )
