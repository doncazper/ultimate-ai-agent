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


def test_documentation_integrity_verifier_requires_openwebui_bridge_contract_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.25.0")
    (tmp_path / "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md").unlink(missing_ok=True)

    failures = verifier.verify(tmp_path)

    assert any("docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md" in failure for failure in failures)


def test_documentation_integrity_verifier_blocks_openwebui_runtime_claims(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.25.0")
    bridge = tmp_path / "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md"
    bridge.write_text(
        bridge.read_text(encoding="utf-8") + "\nOpenWebUI integration is implemented.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("OpenWebUI integration" in failure or "openwebui integration" in failure for failure in failures)


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


def test_documentation_integrity_verifier_rejects_active_m34_label_mismatch(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.37.3")
    expected = "v0.38.0 / M34 - Broader File Capability Review"
    active_docs = {
        "README.md": "| v0.38.0 | M34 - Broader File Capability Review | Planned/provisional |\n",
        "docs/canonical/09_roadmap.md": f"{expected}, planned/provisional\n",
        "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md": (
            "| v0.38.0 | M34 | Broader File Capability Review | planned/provisional |\n"
        ),
        "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md": (
            "## v0.38.0 / M34 - macOS Local Companion Contract / Prototype\n"
            "Status: planned/provisional.\n"
        ),
        "scripts/dev/README.md": (
            "local developer launcher localhost-only not a production installer "
            "execution authority uaa stop .uaa/dev backend routes M34\n"
        ),
        "docs/release_notes/v0_37_2.md": (
            "local developer launcher localhost-only not a production installer "
            "execution authority uaa stop .uaa/dev backend routes M34\n"
        ),
        "docs/archive/releases/v0_37_2/README_IMPORT.md": (
            "local developer launcher localhost-only not a production installer "
            "execution authority uaa stop .uaa/dev backend routes M34\n"
        ),
        "docs/archive/releases/v0_37_2/master_plan.md": (
            "local developer launcher localhost-only not a production installer "
            "execution authority uaa stop .uaa/dev backend routes M34\n"
        ),
    }
    for rel_path, content in active_docs.items():
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any(
        "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md" in failure
        and "expected v0.38.0 / M34 - Broader File Capability Review" in failure
        for failure in failures
    )


def test_documentation_integrity_verifier_requires_m34_m60_supersession_labels(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.37.4")
    _write_m34_m60_active_docs(tmp_path)
    roadmap = tmp_path / "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "v0.64.0 / M60 - Local Developer Beta Freeze",
            "v0.64.0 / M60 - Wrong Future Label",
        ),
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any(
        "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md" in failure
        and "expected v0.64.0 / M60 - Local Developer Beta Freeze" in failure
        for failure in failures
    )


def test_documentation_integrity_verifier_rejects_stale_m35_m40_projection(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.37.4")
    _write_m34_m60_active_docs(tmp_path)
    roadmap = tmp_path / "docs/canonical/09_roadmap.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8")
        + "\nv0.39.0 / M35 - Device Capability Broker Implementation, No Sensors Yet\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any(
        "superseded active M35-M40 roadmap label still present" in failure
        and "device capability broker implementation" in failure
        for failure in failures
    )


def test_documentation_integrity_verifier_requires_m34_review_docs(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.38.0")
    _write_m34_m60_active_docs(tmp_path, m34_released=True)
    _write_m34_review_docs(tmp_path)
    (tmp_path / "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md").unlink()

    failures = verifier.verify(tmp_path)

    assert any("missing active M34 file capability doc" in failure for failure in failures)
    assert any("BROADER_FILE_CAPABILITY_REVIEW.md" in failure for failure in failures)


def test_documentation_integrity_verifier_rejects_m34_runtime_capability_claim(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.38.0")
    _write_m34_m60_active_docs(tmp_path, m34_released=True)
    _write_m34_review_docs(tmp_path)
    review = tmp_path / "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md"
    review.write_text(
        review.read_text(encoding="utf-8")
        + "\nM34 implements Safe File Review Workflow Contracts and file review UI.\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("M34 docs must not claim M35 implementation" in failure for failure in failures)
    assert any("M34 docs must not claim file review UI implementation" in failure for failure in failures)


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


def test_documentation_integrity_verifier_rejects_active_historical_verifiers(tmp_path: Path):
    _write_minimal_repo(tmp_path, version="0.29.4")
    (tmp_path / "verify_ultimate_ai_agent_v0_5_4.py").write_text(
        "REQ = ['README_IMPORT_v0_5_4.md']\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/verify_ultimate_ai_agent_v0_5_5.py").write_text(
        "REQ = ['README_IMPORT_v0_5_5.md']\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("root historical verifier must be archived" in failure for failure in failures)
    assert any("scripts historical verifier must be archived" in failure for failure in failures)


def _write_m34_m60_active_docs(root: Path, *, m34_released: bool = False) -> None:
    labels = "\n".join(
        (
            f"{version} / {milestone} - {title}, implemented/released planning/docs/verifier only"
            if m34_released and milestone == "M34"
            else f"{version} / {milestone} - {title}, planned/provisional"
        )
        for version, milestone, title in verifier.EXPECTED_M34_M60_LABELS
    )
    m34_status = (
        "M34 is implemented/released as planning/docs/verifier only.\n"
        if m34_released
        else "M34 is planning/docs/verifier only.\n"
    )
    future_status = "M35-M60 remain planned/provisional.\n" if m34_released else "M34-M60 remain planned/provisional.\n"
    body = (
        "M21 is implemented/released by v0.25.0 as OpenWebUI Bridge + Chat Shell Integration Contract.\n"
        "M22 is implemented/released by v0.26.0 as Local Model Runtime Activation Contract.\n"
        "M23 is implemented/released by v0.27.0 as First Real Local LLM Call.\n"
        "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
        "M25 is implemented/released by v0.29.0 as Truth Source Router + Evidence Claim Checker.\n"
        "M26 is implemented/released by v0.30.0 as Grounded Recall Router + Evidence-Linked Context Pack Builder.\n"
        "M27 is implemented/released by v0.31.0 as Tool Broker v2 + Safe Tool Intent Contracts.\n"
        "M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion.\n"
        "M29 is implemented/released by v0.33.0 as Agent Task Planning Engine.\n"
        "M30 is implemented/released by v0.34.0 as Multi-Step Execution Framework.\n"
        "M31 is implemented/released by v0.35.0 as Real Tool Runtime Adapter, Single Safe No-Op Tool.\n"
        "M32 is implemented/released by v0.36.0 as Safe Local Filesystem Metadata Tool.\n"
        "M33 is implemented/released by v0.37.0 as First Safe Local File Read Proposal, Redacted Preview Only.\n"
        f"{m34_status}"
        "M35 is the first implementation after supersession.\n"
        "M42 is mobile planning refresh. M44 is the first iOS skeleton.\n"
        "M47 is the TestFlight-capable pipeline. M48 is the first internal TestFlight build.\n"
        "M49-M50 are mobile approval capture and audit work.\n"
        f"{future_status}"
        "Archive docs are not the active source of truth.\n"
        "No integration is added. No dependency is added.\n"
        f"{labels}\n"
    )
    boundary_text = (
        body
        + "arbitrary raw file browsing\n"
        "arbitrary caller-selected filesystem roots\n"
        "raw file export\n"
        "full-file reads\n"
        "arbitrary shell/subprocess\n"
        "unrestricted network tools\n"
        "provider/model calls as authority\n"
        "background workers\n"
        "mobile sensors\n"
        "plugin enablement\n"
        "production authority\n"
        "unreviewed memory writes\n"
        "automatic context injection\n"
        "raw prompt/provider payload exposure\n"
        "external SaaS/analytics SDKs\n"
        "credentials/cookie handling\n"
        "remote execution\n"
        "browser automation execution\n"
        "approval refs as authority\n"
        "Media Color Pipeline is not core before M60 except for M54.\n"
        "OCIO deterministic transform preview belongs after M60.\n"
        "AI gamut expansion is much later and never truth recovery.\n"
    )
    for rel_path in {
        "README.md",
        "docs/canonical/09_roadmap.md",
        "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
        "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        *getattr(verifier, "REQUIRED_POST_M20_ROADMAP_DOCS", []),
    }:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(boundary_text, encoding="utf-8")
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\ndocs/archive/releases/v0_37_4/README_IMPORT.md\n"
        "docs/archive/releases/v0_37_4/master_plan.md\n"
        "docs/DOCUMENTATION_INDEX.md\n"
        "docs/canonical/CANONICAL_DOC_MAP.md\n",
        encoding="utf-8",
    )


def _write_m34_review_docs(root: Path) -> None:
    docs = {
        "docs/files/BROADER_FILE_CAPABILITY_REVIEW.md": (
            "M34 Broader File Capability Review. planning/review only. no raw file reads. "
            "no file review UI. no approval persistence. no context injection. no memory writes. "
            "no export. no execution. no backend routes. no dependencies. "
            "M35 remains planned/provisional. M36 remains planned/provisional."
        ),
        "docs/files/FILE_CAPABILITY_BOUNDARY_MATRIX.md": (
            "File Capability Boundary Matrix. planning/review only. no raw file reads. "
            "no file review UI. no approval persistence. no context injection. no memory writes. "
            "no export. no execution. raw read blocked. full read blocked. M35 remains planned/provisional."
        ),
        "docs/files/FILE_CAPABILITY_RISK_REGISTER.md": (
            "File Capability Risk Register. raw-content leakage. path traversal. redaction bypass. "
            "model_copy mutation bypass. no context injection. no memory writes. no export. no execution."
        ),
        "docs/files/FILE_CAPABILITY_DECISION_RECORD.md": (
            "File Capability Decision Record. M35 = contracts only. M36 = review-only UI. "
            "M37 = review-only approval persistence. M38 = safe context proposal, no injection. "
            "M40 = context handoff approval, no injection. no raw file reads. no execution."
        ),
        "docs/files/M35_SAFE_FILE_REVIEW_WORKFLOW_READINESS.md": (
            "M35 Safe File Review Workflow readiness. exact M35 implementation scope. "
            "required contracts. required tests. required verifiers. strict non-goals. "
            "no file review UI. no approval persistence. no context injection. no memory writes. "
            "no export. no execution. M35 remains planned/provisional until implemented."
        ),
        "docs/files/M34_TO_M35_BOUNDARY.md": (
            "M34 is planning/review only. M35 starts implementation. no M35 implementation in M34. "
            "no approval persistence until M37. no UI until M36. no context proposal until M38. "
            "no context injection through M40. no raw file reads. no memory writes. no export. no execution."
        ),
    }
    for rel_path, content in docs.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _write_minimal_repo(root: Path, version: str = "0.14.6") -> None:
    version_key = version.replace(".", "_")
    files = {
        "VERSION.md": f"# Version\n\nCurrent active baseline: **v{version}**\n",
        "pyproject.toml": f'[project]\nversion = "{version}"\n',
        "src/ultimate_ai_agent/__init__.py": f'__version__ = "{version}"\n',
        "README.md": (
            f"docs/archive/releases/v{version_key}/README_IMPORT.md\n"
            f"docs/archive/releases/v{version_key}/master_plan.md\n"
            "docs/DOCUMENTATION_INDEX.md\n"
            "docs/canonical/CANONICAL_DOC_MAP.md\n"
            "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md\n"
        ),
        f"docs/archive/releases/v{version_key}/README_IMPORT.md": "active import\n",
        f"docs/archive/releases/v{version_key}/master_plan.md": "active master\n",
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
    version_tuple = tuple(int(part) for part in version.split("."))
    if version_tuple >= (0, 37, 2):
        launcher_placeholder = (
            "local developer launcher localhost-only not a production installer "
            "execution authority uaa stop .uaa/dev backend routes M34\n"
        )
        files.update(
            {
                "scripts/dev/README.md": launcher_placeholder,
                "docs/release_notes/v0_37_2.md": launcher_placeholder,
                "docs/archive/releases/v0_37_2/README_IMPORT.md": launcher_placeholder,
                "docs/archive/releases/v0_37_2/master_plan.md": launcher_placeholder,
            }
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
    for rel_path in getattr(verifier, "REQUIRED_OPENWEBUI_BRIDGE_DOCS", []):
        files.setdefault(
            rel_path,
            "M21 is contract-only.\n"
            "OpenWebUI is the preferred conversational web shell.\n"
            "OpenWebUI is not the agent brain.\n"
            "Python Agent Core remains authority.\n"
            "No OpenWebUI integration is implemented.\n"
            "No deployment config is added.\n"
            "No direct tool execution.\n"
            "No direct memory write.\n"
            "No runtime execution.\n"
            "No provider call.\n"
            "No backend API route.\n"
            "Refs are identifiers only.\n"
            "M22 is implemented/released contract-only by v0.26.0.\n"
            "M23 remains planned/provisional.\n",
        )
    for rel_path in getattr(verifier, "REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS", []):
        files.setdefault(
            rel_path,
            "M22 is contract-only.\n"
            "No model was called.\n"
            "No runtime was activated.\n"
            "No endpoint was contacted.\n"
            "No backend API route.\n"
            "OpenAPI path count remains 74.\n"
            "No runtime execution.\n"
            "No provider call.\n"
            "No endpoint probe.\n"
            "No user prompt processing.\n"
            "No tool execution.\n"
            "No memory write.\n"
            "No dependency.\n"
            "M23 remains future.\n",
        )
    if version_tuple >= (0, 32, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
            "M25 is implemented/released by v0.29.0 as deterministic truth/evidence contracts.\n"
            "M26 is implemented/released by v0.30.0 as deterministic grounded recall/context-pack contracts.\n"
            "M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts.\n"
            "M28 is implemented/released by v0.32.0 as Approval Authority v2 + Action Policy Expansion.\n"
            "M29-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 31, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
            "M25 is implemented/released by v0.29.0 as deterministic truth/evidence contracts.\n"
            "M26 is implemented/released by v0.30.0 as deterministic grounded recall/context-pack contracts.\n"
            "M27 is implemented/released by v0.31.0 as validation-only Tool Broker v2 contracts.\n"
            "M28-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 30, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
            "M25 is implemented/released by v0.29.0 as deterministic truth/evidence contracts.\n"
            "M26 is implemented/released by v0.30.0 as deterministic grounded recall/context-pack contracts.\n"
            "M27-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 29, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
            "M25 is implemented/released by v0.29.0 as deterministic truth/evidence contracts.\n"
            "M26-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 28, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24 is implemented/released by v0.28.0 as Memory Provider Abstraction.\n"
            "M25-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 27, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.\n"
            "M24-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 26, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22 is implemented/released by v0.26.0 as contract-only.\n"
            "M23-M40 remain planned/provisional.\n"
        )
    elif version_tuple >= (0, 25, 0):
        post_m20_status = (
            "M21 is implemented/released by v0.25.0 as contract-only.\n"
            "M22-M40 remain planned/provisional.\n"
        )
    else:
        post_m20_status = "M21-M40 remain planned/provisional.\n"
    m21_status = (
        "M21 - OpenWebUI Bridge + Chat Shell Integration Contract, implemented/released contract-only.\n"
        if version_tuple >= (0, 25, 0)
        else "M21 - OpenWebUI Bridge + Chat Shell Integration Contract, planned/provisional.\n"
    )
    no_implementation_line = (
        "M21 contract-only implementation is added; no OpenWebUI integration is added; no dependency is added.\n"
        if version_tuple >= (0, 25, 0)
        else "watchlist only; no integration is added; no dependency is added; no implementation is added.\n"
    )
    for rel_path in getattr(verifier, "REQUIRED_POST_M20_ROADMAP_DOCS", []):
        files.setdefault(
            rel_path,
            m21_status
            + (
                "M22 - Local Model Runtime Activation Contract, implemented/released contract-only.\n"
                if version_tuple >= (0, 26, 0)
                else "M22 - Local Model Runtime Activation Contract, planned/provisional.\n"
            )
            + (
                "M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative, implemented/released.\n"
                if version_tuple >= (0, 27, 0)
                else "M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative, planned/provisional.\n"
            )
            + (
                "M24 - Memory Provider Abstraction + Local Memory Store, implemented/released.\n"
                if version_tuple >= (0, 28, 0)
                else "M24 - Memory Provider Abstraction + Local Memory Store, planned/provisional.\n"
            )
            + (
                "M25 - Truth Source Router + Evidence Claim Checker, implemented/released.\n"
                if version_tuple >= (0, 29, 0)
                else "M25 - Truth Source Router + Evidence Claim Checker, planned/provisional.\n"
            )
            + (
                "M26 - Grounded Recall Router + Evidence-Linked Context Pack Builder, implemented/released.\n"
                if version_tuple >= (0, 30, 0)
                else "M26 - Grounded Recall Router + Evidence-Linked Context Pack Builder, planned/provisional.\n"
            )
            + (
                "M27 - Tool Broker v2 + Safe Tool Intent Contracts, implemented/released.\n"
                if version_tuple >= (0, 31, 0)
                else "M27 - Tool Broker v2 + Safe Tool Intent Contracts, planned/provisional.\n"
            )
            + (
                "M28 - Approval Authority v2 + Action Policy Expansion, implemented/released.\n"
                if version_tuple >= (0, 32, 0)
                else "M28 - Approval Authority v2 + Action Policy Expansion, planned/provisional.\n"
            )
            + "M29 - First Low-Risk Tool Dry-Run + Approval Preview, planned/provisional.\n"
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
            f"{post_m20_status}"
            f"{no_implementation_line}",
        )
    if version_tuple >= (0, 29, 4):
        files["docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md"] = (
            "Root directory policy.\n"
            "Historical verifiers belong in docs/archive/releases/vX_Y_Z/.\n"
            "Legacy historical verifiers are not current release gates.\n"
            "Legacy verifiers are not current release gates.\n"
            "Use docs/archive/releases/vX_Y_Z/README_IMPORT.md.\n"
            "Update scripts/verify_documentation_integrity.py when docs move.\n"
        )
        policy_ref = "docs/maintenance/DOCUMENTATION_ORGANIZATION_POLICY.md\n"
        files["docs/README.md"] = (
            policy_ref
            + f"docs/archive/releases/v{version_key}/README_IMPORT.md\n"
            + f"docs/archive/releases/v{version_key}/master_plan.md\n"
            + "v0.29.4 repairs documentation archive references.\n"
            + "Legacy historical verifiers are not current release gates.\n"
            + "Stale Ruff excludes were removed.\n"
            + "M26 remains future.\n"
        )
        files["docs/DOCUMENTATION_INDEX.md"] = (
            policy_ref
            + f"docs/archive/releases/v{version_key}/README_IMPORT.md\n"
            + f"docs/archive/releases/v{version_key}/master_plan.md\n"
            + "v0.29.4 repairs documentation archive references.\n"
            + "Legacy historical verifiers are not current release gates.\n"
            + "Stale Ruff excludes were removed.\n"
            + "M26 remains future.\n"
        )
        for legacy_key in ["v0_5_4", "v0_5_5", "v0_5_6", "v0_5_8"]:
            files[f"docs/archive/releases/{legacy_key}/legacy_verifier_{legacy_key}.py"] = (
                '"""Historical verifier; not part of current validation."""\n'
            )
    files["docs/roadmap/MILESTONE_CHARTERS.md"] = (
        "version\nmilestone code\ntitle\nstatus\npurpose\nallowed scope\nmust not add\n"
        "dependencies\nacceptance criteria\nreview prompt required\nhardening patch expectation\n"
        "source-of-truth docs\nnotes\n"
    )
    files["docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"] = (
        "Status: historical roadmap projection\n"
        "Current roadmap: docs/canonical/09_roadmap.md\n"
        "v0.17.4 - local browser smoke / UX polish, not M14\n"
        "M14 - Web Control Center Local Backend Connection Stabilization\n"
        "M15 - Approval Queue + Receipt/Event Viewer UI\n"
    )
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
