import ast
from pathlib import Path

from ultimate_ai_agent.core.remote_workers import (
    RemoteTransportDescriptor,
    RemoteTransportKind,
    RemoteTransportStatus,
)


def test_remote_worker_module_has_no_network_subprocess_or_background_imports():
    root = Path("src/ultimate_ai_agent/core/remote_workers")
    forbidden_roots = {"socket", "subprocess", "threading", "asyncio", "requests", "httpx", "urllib"}

    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                assert not forbidden_roots.intersection(imported), f"{path} imports {imported}"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_roots, f"{path} imports from {node.module}"


def test_transport_rejects_live_execution_capabilities_in_model_validation():
    for field in ["requires_network", "requires_credentials", "supports_dispatch", "supports_file_transfer", "supports_subagents"]:
        payload = {
            "transport_id": f"transport_{field}",
            "kind": RemoteTransportKind.manual,
            "status": RemoteTransportStatus.available,
            "display_name": "Transport",
            "description": "Unsafe capability should be rejected.",
            "enabled": True,
            field: True,
            "owner": "tests",
            "source": "fixture",
            "version": "0.0.0",
        }

        descriptor = RemoteTransportDescriptor(**payload)
        assert getattr(descriptor, field) is True

