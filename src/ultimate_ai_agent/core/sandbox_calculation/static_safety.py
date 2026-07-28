from __future__ import annotations

import ast
import hashlib


_RUN_FRAGMENT = "subprocess" + ".run("
_POPEN_FRAGMENT = "subprocess" + ".Popen("
_IMPORT_FRAGMENT = "import " + "subprocess"
_SHELL_TRUE_FRAGMENT = "shell" + "=True"
_OS_SYSTEM_FRAGMENT = "os." + "system("
_BACKEND_REL = "src/ultimate_ai_agent/core/sandbox_calculation/backend.py"
_BACKEND_SOURCE_SHA256 = (
    "149e1795a22abc6cb68c327537ccc9889e7b4b69a1152358d83c3a27321d0e5d"
)
_ALLOWED_SUBPROCESS_ATTRIBUTES = frozenset(
    {
        "CompletedProcess",
        "PIPE",
        "Popen",
        "SubprocessError",
        "TimeoutExpired",
        "run",
    }
)
_UNRELATED_FORBIDDEN_MARKERS = (
    "import " + "requests",
    "from " + "requests import",
    "requests" + ".",
    "import " + "httpx",
    "from " + "httpx import",
    "httpx" + ".",
    "urllib" + ".request",
    "network_access_enabled" + "=True",
    "browser_automation_enabled" + "=True",
    "provider_call_enabled" + "=True",
    "os" + ".environ",
    "os" + ".getenv(",
)
_REQUIRED_MARKERS = (
    '"--pull",',
    '"never",',
    '"--network",',
    '"--read-only",',
    '"--cap-drop",',
    '"no-new-privileges:true",',
    '"--pids-limit",',
    '"--memory",',
    '"--user",',
    '"65532:65532",',
    "start_new_session=True",
    "SEALED_CALCULATION_INPUT_ACCEPTANCE_INVALID",
    "SEALED_CALCULATION_COMMIT_AUTHORITY_FENCE_DENIED",
    "SEALED_CALCULATION_CLEANUP_UNCONFIRMED",
)


def is_exact_sealed_calculation_subprocess_site(
    *,
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    if (
        rel_path != _BACKEND_REL
        or fragment not in {_RUN_FRAGMENT, _POPEN_FRAGMENT}
        or hashlib.sha256(source.encode("utf-8")).hexdigest()
        != _BACKEND_SOURCE_SHA256
        or source.count(_RUN_FRAGMENT) != 5
        or source.count(_POPEN_FRAGMENT) != 1
        or _SHELL_TRUE_FRAGMENT in source
        or _OS_SYSTEM_FRAGMENT in source
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
    popen_calls = 0
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
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ):
            continue
        if node.func.attr == "run":
            run_calls += 1
        elif node.func.attr == "Popen":
            popen_calls += 1
        elif node.func.attr == "TimeoutExpired":
            continue
        else:
            return False
        for keyword in node.keywords:
            if (
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                return False
    return subprocess_imports == 1 and run_calls == 5 and popen_calls == 1


def is_exact_sealed_calculation_forbidden_fragment_exception(
    *,
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    """Permit only the two reviewed subprocess call fragments in the exact backend."""

    if fragment not in {_IMPORT_FRAGMENT, _RUN_FRAGMENT, _POPEN_FRAGMENT}:
        return False
    validation_fragment = _RUN_FRAGMENT if fragment == _IMPORT_FRAGMENT else fragment
    return is_exact_sealed_calculation_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=validation_fragment,
    )


def sealed_backend_fragment_allowed(
    rel_path: str, source: str, fragment: str
) -> bool:
    """Short positional facade for legacy static-scan loops."""

    return is_exact_sealed_calculation_forbidden_fragment_exception(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )
