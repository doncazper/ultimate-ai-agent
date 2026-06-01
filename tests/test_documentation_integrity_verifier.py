from pathlib import Path

import scripts.verify_documentation_integrity as verifier


def test_documentation_integrity_verifier_passes_current_repo():
    assert verifier.verify() == []


def test_documentation_integrity_verifier_flags_unsafe_active_claim(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nRemote execution is supported.\n", encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any("remote execution is supported" in failure for failure in failures)


def _write_minimal_repo(root: Path) -> None:
    version = "0.14.5"
    version_key = "0_14_5"
    files = {
        "VERSION.md": f"# Version\n\nCurrent active baseline: **v{version}**\n",
        "pyproject.toml": f'[project]\nversion = "{version}"\n',
        "src/ultimate_ai_agent/__init__.py": f'__version__ = "{version}"\n',
        "README.md": (
            f"README_IMPORT_v{version_key}.md\n"
            f"ultimate_ai_agent_master_plan_v{version_key}.md\n"
            "docs/DOCUMENTATION_INDEX.md\n"
            "docs/canonical/CANONICAL_DOC_MAP.md\n"
        ),
        f"README_IMPORT_v{version_key}.md": "active import\n",
        f"ultimate_ai_agent_master_plan_v{version_key}.md": "active master\n",
        f"docs/release_notes/v{version_key}.md": "active release notes\n",
        f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md": "active gate plan\n",
    }
    for rel_path in [*verifier.REQUIRED_ACTIVE_DOCS, *verifier.ACTIVE_DOCS_TO_SCAN]:
        files.setdefault(rel_path, "active documentation placeholder\n")
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
