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


def test_documentation_integrity_verifier_requires_openwebui_ccc_strategy_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    (tmp_path / "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md").unlink(missing_ok=True)

    failures = verifier.verify(tmp_path)

    assert any("docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_ccc_native_client_boundaries(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    native_strategy = tmp_path / "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md"
    native_strategy.parent.mkdir(parents=True, exist_ok=True)
    native_strategy.write_text(
        "CCC means Control Center Clients.\n"
        "CCC Web is ready. CCC iOS is ready. CCC Android is ready. CCC macOS is ready.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("CCC docs must define CCC Android" in failure for failure in failures)
    assert any("CCC native strategy must say no Android app is implemented" in failure for failure in failures)
    assert any("CCC native strategy must say no native build workflow is added" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_post_m20_roadmap_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    (tmp_path / "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md").unlink(missing_ok=True)
    (tmp_path / "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md").unlink(missing_ok=True)
    (tmp_path / "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md").unlink(missing_ok=True)

    failures = verifier.verify(tmp_path)

    assert any("docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md" in failure for failure in failures)
    assert any("docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md" in failure for failure in failures)
    assert any("docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md" in failure for failure in failures)


def test_documentation_integrity_verifier_rejects_implemented_post_m20_claims(tmp_path: Path):
    _write_minimal_repo(tmp_path)
    roadmap = tmp_path / "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md"
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    roadmap.write_text(
        "M21 is implemented.\n"
        "M22 is planned/provisional.\n"
        "M23 is planned/provisional.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("M21-M40 docs must not claim implementation" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_post_m18_status_labels(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.22.1")
    sequence = tmp_path / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    sequence.write_text(
        "M14 is Web Control Center Local Backend Connection Stabilization.\n"
        "M15 is Approval Queue + Receipt/Event Viewer UI.\n"
        "v0.17.4 local browser smoke was not M14.\n"
        "v0.22.0 / M18 - Local Runtime Status + Manual Smoke Control Surface\n"
        "Status: planned/provisional.\n"
        "v0.23.0 / M19 - Mobile Companion Contract/API Planning\n"
        "Status: planned/provisional.\n"
        "v0.24.0 / M20 - Device Capability Broker Contract\n"
        "Status: planned/provisional.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("roadmap sequence must mark M18/v0.22.0 as implemented" in failure for failure in failures)


def test_documentation_integrity_verifier_rejects_stale_v023_roadmap_currentness(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.23.1")
    roadmap = tmp_path / "docs/canonical/09_roadmap.md"
    roadmap.write_text(
        "The active accepted baseline is v0.22.1.\n"
        "v0.23.0 / M19 - Mobile Companion Contract/API Planning, planned/provisional.\n"
        "v0.24.0 / M20 - Device Capability Broker Contract, planned/provisional.\n",
        encoding="utf-8",
    )
    post_m20 = tmp_path / "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md"
    post_m20.write_text(
        "Status: Active roadmap projection maintained through v0.22.1.\n"
        "M21 - OpenWebUI Bridge + Chat Shell Integration Contract, planned/provisional.\n"
        "M40 - Agent Evaluation + Regression Harness, planned/provisional.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("canonical roadmap must not claim active baseline v0.22.1" in failure for failure in failures)
    assert any("canonical roadmap must mark M19/v0.23.0 as implemented" in failure for failure in failures)
    assert any("active roadmap docs must not be maintained only through v0.22.1" in failure for failure in failures)


def test_documentation_integrity_verifier_requires_m20_device_capability_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.24.0")
    roadmap = tmp_path / "docs/canonical/09_roadmap.md"
    roadmap.write_text(
        "The active accepted baseline is v0.24.0.\n"
        "v0.24.0 / M20 - Device Capability Broker Contract, planned/provisional.\n"
        "v0.25.0 / M21 - OpenWebUI Bridge + Chat Shell Integration Contract, implemented.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md" in failure for failure in failures)
    assert any("M20/v0.24.0 as implemented/released" in failure for failure in failures)
    assert any("M21/v0.25.0 planned/provisional" in failure for failure in failures)


def _write_minimal_repo(root: Path, version: str = "0.14.6") -> None:
    version_key = version.replace(".", "_")
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
    for rel_path in getattr(verifier, "REQUIRED_UI_STRATEGY_DOCS", []):
        files.setdefault(
            rel_path,
            "OpenWebUI is the preferred conversational web shell.\n"
            "OpenWebUI is not the agent brain.\n"
            "OpenWebUI must not bypass Python Agent Core.\n"
            "No OpenWebUI integration is implemented in this patch.\n"
            "No OpenWebUI deployment config is added in this patch.\n"
            "CCC means Control Center Clients.\n"
            "CCC is the governance/control layer.\n"
            "CCC Web is the current TypeScript web Control Center.\n"
            "CCC iOS is a future native mobile control client.\n"
            "CCC Android is a future native mobile control client.\n"
            "CCC macOS is a future desktop/local companion client.\n"
            "Open Design does not replace OpenWebUI.\n"
            "all CCC clients are control surfaces, not the agent brain.\n"
            "all CCC clients must use Python Agent Core authority.\n"
            "no Android app is implemented yet.\n"
            "no iOS app is implemented yet.\n"
            "no macOS app is implemented yet.\n"
            "no CCC native implementation is added.\n"
            "no native build workflow is added.\n"
            "no mobile sensor access is added.\n"
            "no OS permission integration is added.\n"
            "no signing, keystore, provisioning, App Store, or Play Store workflow is added.\n",
        )
    for rel_path in getattr(verifier, "REQUIRED_POST_M20_ROADMAP_DOCS", []):
        files.setdefault(
            rel_path,
            "M21 - OpenWebUI Bridge + Chat Shell Integration Contract, planned/provisional.\n"
            "M22 - Local Model Runtime Activation Contract, planned/provisional.\n"
            "M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative, planned/provisional.\n"
            "M24 - Memory Provider Abstraction + Local Memory Store, planned/provisional.\n"
            "M25 - Truth Source Router + Evidence Claim Checker, planned/provisional.\n"
            "M26 - Tool Execution Sandbox Contract, Dry-Run Only, planned/provisional.\n"
            "M27 - MCP / Agent Skills / AGENTS.md Trust Registry, Quarantine-Only, planned/provisional.\n"
            "M28 - Local Sandbox Backend Abstraction, planned/provisional.\n"
            "M29 - First Low-Risk Tool Dry-Run + Approval Preview, planned/provisional.\n"
            "M30 - First Approved Low-Risk Local Tool Execution, planned/provisional.\n"
            "M31 - CCC Native Client Contract: iOS / Android / macOS, planned/provisional.\n"
            "M32 - Device Pairing + Trust Handshake Contract, planned/provisional.\n"
            "M33 - Mobile Approval Surface Prototype, No Sensors, planned/provisional.\n"
            "M34 - macOS Local Companion Contract / Prototype, planned/provisional.\n"
            "M35 - Device Capability Broker Implementation, No Sensors Yet, planned/provisional.\n"
            "M36 - Mobile Capture Inbox, Selected Input Only, planned/provisional.\n"
            "M37 - One Governed Sensor Capability, planned/provisional.\n"
            "M38 - Browser Automation Contract, No Execution, planned/provisional.\n"
            "M39 - Observability Export Adapters, planned/provisional.\n"
            "M40 - Agent Evaluation + Regression Harness, planned/provisional.\n"
            "watchlist only; no integration is added; no dependency is added; no implementation is added.\n",
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
