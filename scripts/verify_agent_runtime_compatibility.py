#!/usr/bin/env python3
"""Verify the UAA-P2 Agent Runtime Compatibility boundary.

This verifier is static and inspection-only. It does not call providers, fetch
networks, open browsers, run shell/subprocess work, write connectors, mutate
memory, inject context, or execute actions.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    Path("docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md"),
    Path("docs/codex/UAA_P2_AGENT_RUNTIME_COMPATIBILITY_PROMPTS.md"),
    Path("src/ultimate_ai_agent/core/agent_runtime/__init__.py"),
    Path("src/ultimate_ai_agent/core/agent_runtime/contracts.py"),
    Path("src/ultimate_ai_agent/core/agent_runtime/handoffs.py"),
    Path("src/ultimate_ai_agent/core/agent_runtime/tracing.py"),
    Path("src/ultimate_ai_agent/core/agent_runtime/demo.py"),
    Path("tests/test_agent_runtime_adapter_contract.py"),
    Path("tests/test_agent_runtime_handoff_envelope.py"),
    Path("tests/test_agent_runtime_trace_contract.py"),
    Path("tests/test_agent_runtime_specialist_demo.py"),
)

SCANNED_PYTHON_PATHS = (
    Path("src/ultimate_ai_agent/core/agent_runtime"),
    Path("src/ultimate_ai_agent/core/capabilities/models.py"),
    Path("src/ultimate_ai_agent/core/capabilities/enums.py"),
    Path("src/ultimate_ai_agent/core/capabilities/adapters/openai_tools.py"),
    Path("src/ultimate_ai_agent/core/capabilities/adapters/mcp.py"),
)

FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "boto3",
    "httpx",
    "openai",
    "playwright",
    "requests",
    "selenium",
    "socket",
    "subprocess",
    "urllib",
    "webbrowser",
}

FORBIDDEN_RAW_FIELD_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "raw_provider_payload",
    "raw_path",
    "raw_log",
    "environment_dump",
    "credential_material",
)

FORBIDDEN_TRUE_DEFAULTS = (
    "execution_authorized: bool = True",
    "provider_runtime_authorized: bool = True",
    "network_authorized: bool = True",
    "browser_automation_authorized: bool = True",
    "shell_execution_authorized: bool = True",
    "connector_write_authorized: bool = True",
    "memory_write_authorized: bool = True",
    "context_injection_authorized: bool = True",
    "memory_write_allowed: bool = True",
    "context_injection_allowed: bool = True",
    "provider_runtime_allowed: bool = True",
    "browser_runtime_allowed: bool = True",
    "connector_write_allowed: bool = True",
    "dispatch_authorized\": True",
    "\"dispatch_authorized\": true",
)

REQUIRED_DOC_FRAGMENTS = (
    "does not adopt the OpenAI Agents SDK",
    "AgentRuntimeAdapter",
    "CapabilityManifest",
    "UAA trace refs are canonical",
    "Handoff approval is not execution approval",
    "Memory remains recall, not truth or authority",
)

REQUIRED_CONTRACT_FRAGMENTS = (
    "AgentRuntimeAuthorityPosture",
    "AgentRuntimeRequest",
    "AgentRuntimeDecision",
    "AgentRuntimeResult",
    "DeterministicNoopAgentRuntimeAdapter",
    "execution_authorized: bool = False",
    "memory_write_authorized: bool = False",
    "context_injection_authorized: bool = False",
    "connector_write_authorized: bool = False",
)

FORBIDDEN_API_ROUTE_FRAGMENTS = (
    '"/agent-runtime',
    '"/agents/runtime',
    '"/agents/remote/handoff"',
)


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_PATHS:
        if not (root / rel_path).exists():
            failures.append(f"missing agent runtime compatibility artifact: {rel_path}")

    if failures:
        return failures

    architecture_text = (root / "docs/architecture/UAA_P2_AGENT_RUNTIME_COMPATIBILITY.md").read_text(encoding="utf-8")
    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in architecture_text:
            failures.append(f"architecture charter missing fragment: {fragment}")

    contracts_text = (root / "src/ultimate_ai_agent/core/agent_runtime/contracts.py").read_text(encoding="utf-8")
    for fragment in REQUIRED_CONTRACT_FRAGMENTS:
        if fragment not in contracts_text:
            failures.append(f"agent runtime contracts missing fragment: {fragment}")

    for path in _iter_scanned_python_files(root):
        text = path.read_text(encoding="utf-8")
        failures.extend(_scan_imports(path, text))
        lowered = text.lower()
        for fragment in FORBIDDEN_RAW_FIELD_FRAGMENTS:
            if fragment in lowered:
                failures.append(f"{path.relative_to(root)} contains forbidden raw-content field fragment: {fragment}")
        for fragment in FORBIDDEN_TRUE_DEFAULTS:
            if fragment.lower() in lowered:
                failures.append(f"{path.relative_to(root)} enables forbidden authority default: {fragment}")

    api_root = root / "src/ultimate_ai_agent/api"
    if api_root.exists():
        for path in sorted(api_root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for fragment in FORBIDDEN_API_ROUTE_FRAGMENTS:
                if fragment in text:
                    failures.append(f"{path.relative_to(root)} exposes forbidden agent runtime route fragment: {fragment}")

    return failures


def _iter_scanned_python_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_path in SCANNED_PYTHON_PATHS:
        path = root / rel_path
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.py")))
        elif path.exists():
            paths.append(path)
    return paths


def _scan_imports(path: Path, text: str) -> list[str]:
    failures: list[str] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return [f"{path}: syntax error during static import scan: {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path}: forbidden import root: {root}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                failures.append(f"{path}: forbidden import root: {root}")
    return failures


def main() -> int:
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Agent runtime compatibility verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
