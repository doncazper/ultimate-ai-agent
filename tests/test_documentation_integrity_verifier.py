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


def test_documentation_integrity_verifier_requires_milestone_charter_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    (tmp_path / "docs/roadmap/MILESTONE_CHARTERS.md").unlink()
    (tmp_path / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md").unlink()

    failures = verifier.verify(tmp_path)

    assert any("MILESTONE_CHARTERS" in failure for failure in failures)
    assert any("NEXT_SEQUENCE_v0_17_5" in failure for failure in failures)


def test_documentation_integrity_verifier_flags_m14_browser_smoke_claim(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    sequence = tmp_path / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    sequence.parent.mkdir(parents=True, exist_ok=True)
    sequence.write_text(
        "M14 - local browser smoke / UX polish\n"
        "M15 - Approval Queue + Receipt/Event Viewer UI\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/roadmap/MILESTONE_CHARTERS.md").write_text(
        "version\nmilestone code\ntitle\nstatus\npurpose\nallowed scope\nmust not add\n"
        "dependencies\nacceptance criteria\nreview prompt required\nhardening patch expectation\n"
        "source-of-truth docs\nnotes\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("M14 must not be local browser smoke" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_open_design_governance_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    design_doc = tmp_path / "docs/design/OPEN_DESIGN_SYSTEM.md"
    design_doc.unlink(missing_ok=True)

    failures = verifier.verify(tmp_path)

    assert any("docs/design/OPEN_DESIGN_SYSTEM.md" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_design_tooling_safety_language(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    tooling_policy = tmp_path / "docs/design/DESIGN_TOOLING_POLICY.md"
    tooling_policy.parent.mkdir(parents=True, exist_ok=True)
    tooling_policy.write_text("Design tools are available for automatic design sync.\n", encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any("design docs must say no design tools are enabled" in failure for failure in failures)
    assert any("design docs must say no automatic design sync" in failure for failure in failures)


def _write_minimal_repo(root: Path) -> None:
    version = "0.14.6"
    version_key = "0_14_6"
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
    policy_placeholder = (
        "Browser + Build Web Apps may be used with approval.\n"
        "Build iOS Apps and Build macOS Apps remain disabled.\n"
        "Computer Use remains disabled.\n"
        "Chrome authenticated profile control remains disabled.\n"
        "Plugin/skill installers remain disabled.\n"
        "v0.17.4 is Web Control Center local browser smoke polish.\n"
        "M14 is Web Control Center Local Backend Connection Stabilization.\n"
        "M15 is Approval Queue + Receipt/Event Viewer UI.\n"
    )
    for rel_path in [*verifier.REQUIRED_ACTIVE_DOCS, *verifier.ACTIVE_DOCS_TO_SCAN]:
        files.setdefault(rel_path, policy_placeholder)
    for rel_path in getattr(verifier, "REQUIRED_DESIGN_DOCS", []):
        files.setdefault(
            rel_path,
            "repo-owned source of truth\n"
            "no design tools are enabled\n"
            "no design SaaS is authority\n"
            "no automatic design-to-code\n"
            "no automatic design sync\n"
            "screenshots and design artifacts must not contain secrets\n"
            "Control Center design governance\n"
            "Mobile Companion design governance\n",
        )
    files["docs/roadmap/MILESTONE_CHARTERS.md"] = (
        "version\nmilestone code\ntitle\nstatus\npurpose\nallowed scope\nmust not add\n"
        "dependencies\nacceptance criteria\nreview prompt required\nhardening patch expectation\n"
        "source-of-truth docs\nnotes\n"
    )
    files["docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"] = (
        "v0.17.4 - local browser smoke / UX polish, not M14\n"
        "M14 - Web Control Center Local Backend Connection Stabilization\n"
        "M15 - Approval Queue + Receipt/Event Viewer UI\n"
    )
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
