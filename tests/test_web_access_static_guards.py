"""Static guardrails for WebAccessGateway boundary discipline.

These tests intentionally allow a small baseline exception list discovered during
review. The list should shrink over time. It should not grow without an explicit
security-review comment explaining the lane and milestone.
"""

from __future__ import annotations

import ast
from pathlib import Path

BANNED_PUBLIC_WEB_IMPORTS = {
    "http.client",
    "httpx",
    "requests",
    "urllib.request",
    "urllib3",
    "playwright",
    "selenium",
    "firecrawl",
    "browserbase",
}

APPROVED_PREFIXES = (
    "src/ultimate_ai_agent/core/web_access/",
    "tests/",
)

TEMPORARY_BASELINE_EXCEPTIONS = {
    "src/ultimate_ai_agent/core/local_model_management/hf_search.py": "model_acquisition_exception",
    "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py": "model_acquisition_exception",
    "src/ultimate_ai_agent/core/local_model_management/gateway.py": "local_model_loopback_exception",
    "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py": "local_model_loopback_exception",
    "src/ultimate_ai_agent/core/network/governed_web_evidence.py": "governed_web_evidence_legacy_wrapper_source",
    "src/ultimate_ai_agent/core/tools/runtime/http_fetch.py": "tool_runtime_legacy_to_migrate_pr3",
    "src/ultimate_ai_agent/core/browser/observe.py": "browser_observe_legacy_to_wrap_pr4",
    "src/ultimate_ai_agent/core/browser/action_dry_run.py": "browser_dry_run_legacy_to_wrap_pr5",
    "src/ultimate_ai_agent/core/browser/low_risk_click.py": "m94_future_blocked_existing_module",
}

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "build",
    "dist",
    "node_modules",
}


def test_no_new_direct_public_web_or_browser_imports_outside_gateway() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    violations: list[str] = []

    for path in _iter_python_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        if _is_approved(rel):
            continue

        imported = _direct_imports(path)
        banned = sorted(module for module in imported if _is_banned(module))
        if banned:
            violations.append(f"{rel}: {', '.join(banned)}")

    assert not violations, (
        "Direct public-web/browser imports must go through "
        "ultimate_ai_agent.core.web_access adapters or an explicit temporary "
        "exception. Violations:\n" + "\n".join(violations)
    )


def _iter_python_files(repo_root: Path):  # type: ignore[no-untyped-def]
    for path in repo_root.rglob("*.py"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        yield path


def _is_approved(rel: str) -> bool:
    return rel.startswith(APPROVED_PREFIXES) or rel in TEMPORARY_BASELINE_EXCEPTIONS


def _is_banned(module: str) -> bool:
    return any(module == banned or module.startswith(f"{banned}.") for banned in BANNED_PUBLIC_WEB_IMPORTS)


def _direct_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports
