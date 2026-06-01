from pathlib import Path

from ultimate_ai_agent import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_agents_md_declares_workspace_and_api_boundary_standards():
    content = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Ultimate AI Agent" in content
    assert "/api/manifest" in content
    assert "OpenAPI" in content
    assert "Do not add runtime model calls" in content
    assert "Do not add web fetching" in content
    assert f"v{__version__}" in content


def test_api_boundary_docs_exist_for_openapi_and_route_inventory():
    required = [
        "docs/api/README.md",
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "docs/standards/agents_md_support.md",
    ]

    for rel_path in required:
        path = ROOT / rel_path
        assert path.exists(), f"missing {rel_path}"
        assert path.read_text(encoding="utf-8").strip()
