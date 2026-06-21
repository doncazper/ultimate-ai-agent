import ast
from pathlib import Path


RUNTIME_READINESS_ROOT = Path("src/ultimate_ai_agent/core/runtime_readiness")


def test_runtime_readiness_package_has_no_execution_or_network_imports() -> None:
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
        "tiktoken",
        "tokenizers",
    }
    forbidden_calls = {"eval", "exec"}
    failures = []

    for path in RUNTIME_READINESS_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in forbidden_import_roots:
                        failures.append(f"{path}: forbidden import {alias.name}")
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in forbidden_import_roots:
                    failures.append(f"{path}: forbidden import {node.module}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                failures.append(f"{path}: forbidden call {node.func.id}")

    assert failures == []
