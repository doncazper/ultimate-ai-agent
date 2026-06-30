"""Static guardrails for WebAccessGateway boundary discipline.

These tests intentionally allow a small baseline exception list discovered during
review. The list should shrink over time. It should not grow without an explicit
security-review comment explaining the lane and milestone.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re

BANNED_PUBLIC_WEB_IMPORTS = {
    "apify",
    "apify_client",
    "browserbase",
    "bs4",
    "ddgs",
    "duckduckgo_search",
    "exa",
    "exa_py",
    "firecrawl",
    "http.client",
    "httpx",
    "newspaper",
    "newspaper3k",
    "playwright",
    "requests",
    "scrapy",
    "selenium",
    "serpapi",
    "tavily",
    "tavily_client",
    "trafilatura",
    "urllib.request",
    "urllib3",
}

APPROVED_ADAPTER_FILES = {
    "src/ultimate_ai_agent/core/web_access/adapters.py",
}

TEMPORARY_BASELINE_EXCEPTIONS = {
    "scripts/dev/uaa_launcher.py": (
        "lane=developer_loopback_launcher; "
        "scope=localhost readiness probes for local dev services only; "
        "authority=not_agent_public_web; migration=keep outside agent web access"
    ),
    "scripts/dev/uaa_setup.py": (
        "lane=developer_setup_bootstrap; "
        "scope=approved GitHub release bootstrap plus localhost probes only; "
        "authority=not_agent_public_web; migration=keep outside agent web access"
    ),
    "scripts/run_local_runtime_packaging_proof.py": (
        "lane=local_runtime_packaging_proof; "
        "scope=localhost packaging proof probes only; "
        "authority=not_agent_public_web; migration=keep outside agent web access"
    ),
    "src/ultimate_ai_agent/core/local_model_management/gateway.py": (
        "lane=local_model_loopback; "
        "scope=localhost model runtime management only; "
        "authority=not_agent_public_web; migration=separate local-model boundary"
    ),
    "src/ultimate_ai_agent/core/local_model_management/hf_search.py": (
        "lane=model_acquisition; "
        "scope=Hugging Face model search only; "
        "authority=not_agent_public_web; migration=review after gateway PR 3"
    ),
    "src/ultimate_ai_agent/core/local_model_management/model_acquisition.py": (
        "lane=model_acquisition; "
        "scope=Hugging Face model download only; "
        "authority=not_agent_public_web; migration=review after gateway PR 3"
    ),
    "src/ultimate_ai_agent/core/model_runtime/local_call_transport.py": (
        "lane=local_model_loopback; "
        "scope=manual local model call transport only; "
        "authority=not_agent_public_web; migration=separate local-model boundary"
    ),
    "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py": (
        "lane=local_model_loopback; "
        "scope=manual loopback smoke transport only; "
        "authority=not_agent_public_web; migration=separate local-model boundary"
    ),
    "src/ultimate_ai_agent/core/network/governed_web_evidence.py": (
        "lane=governed_web_evidence; "
        "scope=legacy governed evidence source wrapped by WebAccessGateway; "
        "authority=not_general_agent_web; migration=wrapped in PR 1"
    ),
    "src/ultimate_ai_agent/core/providers/live_invocation_adapter.py": (
        "lane=tiny_exact_approved_provider_invocation; "
        "scope=one provider/model scoped live adapter after exact approval and CostGovernor; "
        "authority=not_agent_public_web; migration=provider-runtime scoped adapter"
    ),
}

BANNED_PROVIDER_SURFACE_TERMS = {
    "apify",
    "browserbase",
    "bs4",
    "ddgs",
    "duckduckgo_search",
    "exa_py",
    "firecrawl",
    "newspaper",
    "newspaper3k",
    "playwright",
    "scrapy",
    "selenium",
    "serpapi",
    "tavily",
    "tavily_client",
    "trafilatura",
}

TEMPORARY_PROVIDER_SURFACE_EXCEPTIONS = {
    "apps/control-center/package.json": (
        "lane=control_center_visual_regression; "
        "scope=dev-only Playwright visual checks; "
        "authority=not_agent_public_web; migration=keep outside agent web access"
    ),
    "scripts/run_local_runtime_packaging_proof.py": (
        "lane=local_runtime_packaging_proof; "
        "scope=dev-only Playwright screenshot of local Control Center; "
        "authority=not_agent_public_web; migration=keep outside agent web access"
    ),
}

PROVIDER_EXECUTION_CALLS = {
    "_run_checked",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "subprocess.run",
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


def test_disabled_provider_shells_do_not_import_provider_sdks() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    adapter_file = repo_root / "src/ultimate_ai_agent/core/web_access/adapters.py"

    imported = _direct_imports(adapter_file)
    banned = sorted(module for module in imported if _is_banned(module))

    assert banned == []


def test_no_new_browser_search_provider_cli_surfaces_outside_exceptions() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    violations: list[str] = []

    for path in _iter_provider_surface_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        if rel in TEMPORARY_PROVIDER_SURFACE_EXCEPTIONS:
            continue

        terms = _provider_terms_in_text(path)
        if terms:
            violations.append(f"{rel}: {', '.join(terms)}")

    assert not violations, (
        "Browser/search/scrape provider CLI or package surfaces must be "
        "explicit temporary exceptions until routed through WebAccessGateway. "
        "Violations:\n" + "\n".join(violations)
    )


def test_temporary_exceptions_are_documented_with_lanes() -> None:
    for rel, note in {
        **TEMPORARY_BASELINE_EXCEPTIONS,
        **TEMPORARY_PROVIDER_SURFACE_EXCEPTIONS,
    }.items():
        assert "lane=" in note, rel
        assert "scope=" in note, rel
        assert "authority=" in note, rel
        assert "migration=" in note, rel


def _iter_python_files(repo_root: Path):  # type: ignore[no-untyped-def]
    for path in repo_root.rglob("*.py"):
        if any(part in IGNORED_DIR_NAMES for part in path.parts):
            continue
        yield path


def _is_approved(rel: str) -> bool:
    return rel in APPROVED_ADAPTER_FILES or rel in TEMPORARY_BASELINE_EXCEPTIONS


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
            imports.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imports


def _iter_provider_surface_files(repo_root: Path):  # type: ignore[no-untyped-def]
    script_root = repo_root / "scripts"
    if script_root.exists():
        yield from script_root.rglob("*.py")

    apps_root = repo_root / "apps"
    if apps_root.exists():
        yield from apps_root.glob("*/package.json")


def _provider_terms_in_text(path: Path) -> list[str]:
    if path.name == "package.json":
        return _provider_terms_in_string(path.read_text(encoding="utf-8", errors="ignore"))
    if path.suffix == ".py":
        return _provider_terms_in_python_execution_calls(path)
    return []


def _provider_terms_in_string(text: str) -> list[str]:
    normalized = text.lower()
    found: list[str] = []
    for term in sorted(BANNED_PROVIDER_SURFACE_TERMS):
        pattern = rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])"
        if re.search(pattern, normalized):
            found.append(term)
    return found


def _provider_terms_in_python_execution_calls(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) not in PROVIDER_EXECUTION_CALLS:
            continue
        for value in _string_constants(node):
            found.update(_provider_terms_in_string(value))
    return sorted(found)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _string_constants(node: ast.AST):  # type: ignore[no-untyped-def]
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value
