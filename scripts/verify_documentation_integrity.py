#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


REQUIRED_ACTIVE_DOCS = [
    "docs/DOCUMENTATION_INDEX.md",
    "docs/canonical/CANONICAL_DOC_MAP.md",
    "docs/maintenance/documentation_integrity_checklist.md",
    "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
    "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
    "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
    "docs/backlog/mobile_companion_backlog.md",
    "docs/backlog/device_capability_broker_backlog.md",
    "docs/backlog/codex_plugin_enablement_backlog.md",
    "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
    "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
    "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
    "docs/remote/TAILNET_TRANSPORT_POLICY.md",
    "docs/remote/REMOTE_WORKER_FOUNDATION.md",
    "docs/runtime/RUNTIME_READINESS.md",
    "docs/runtime/MANUAL_SMOKE_REPORTS.md",
    "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
    "docs/control_center/CONTROL_CENTER_CONTRACT.md",
    "docs/control_center/DASHBOARD_SNAPSHOT.md",
    "docs/control_center/ACTION_PREVIEW_POLICY.md",
    "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
    "docs/control_center/FRONTEND_SAFETY_POLICY.md",
    "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
    "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
    "docs/control_center/APPROVAL_QUEUE_UI.md",
    "docs/control_center/RECEIPT_EVENT_VIEWER.md",
    "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
    "docs/control_center/EVENT_TIMELINE_UI.md",
    "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
    "docs/control_center/TRACE_REDACTION_POLICY.md",
    "docs/design/OPEN_DESIGN_SYSTEM.md",
    "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
    "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
    "docs/design/ACCESSIBILITY_BASELINE.md",
    "docs/design/DESIGN_TOOLING_POLICY.md",
    "docs/design/DESIGN_TOKEN_ROADMAP.md",
    "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
    "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
    "docs/design/COMPONENT_TAXONOMY.md",
    "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
    "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
    "docs/ui/CLIENT_SURFACE_ROLES.md",
    "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
    "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
    "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
    "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
    "docs/roadmap/MILESTONE_CHARTERS.md",
    "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
]

REQUIRED_DESIGN_DOCS = [
    "docs/design/OPEN_DESIGN_SYSTEM.md",
    "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
    "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
    "docs/design/ACCESSIBILITY_BASELINE.md",
    "docs/design/DESIGN_TOOLING_POLICY.md",
    "docs/design/DESIGN_TOKEN_ROADMAP.md",
    "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
    "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
    "docs/design/COMPONENT_TAXONOMY.md",
    "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
]

REQUIRED_UI_STRATEGY_DOCS = [
    "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
    "docs/ui/CLIENT_SURFACE_ROLES.md",
    "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
    "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
]

REQUIRED_POST_M20_ROADMAP_DOCS = [
    "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
    "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
]

UNSAFE_IMPLEMENTATION_CLAIMS = [
    "tailscale integration is implemented",
    "headscale integration is implemented",
    "remote execution is supported",
    "mobile camera access is implemented",
    "microphone capture is implemented",
    "gps access is implemented",
    "skill factory is implemented",
    "scanner runtime is implemented",
    "production_ready=true",
    "real_model_runtime_ready=true",
    "remote_execution_ready=true",
    "mobile_sensor_ready=true",
    "plugin_or_native_build_ready=true",
    "production control center is implemented",
    "control center executes actions",
    "control center enables plugins",
    "control center dispatches remote workers",
    "control center calls models",
    "control center controls native builds",
    "control center accesses mobile sensors",
    "web control center has production authority",
]

ACTIVE_DOCS_TO_SCAN = [
    "README.md",
    "VERSION.md",
    "AGENTS.md",
    "docs/DOCUMENTATION_INDEX.md",
    "docs/canonical/CANONICAL_DOC_MAP.md",
    "docs/canonical/09_roadmap.md",
    "docs/roadmap/MILESTONE_CHARTERS.md",
    "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
    *REQUIRED_POST_M20_ROADMAP_DOCS,
    "docs/api/README.md",
    "docs/api/openapi_contract.md",
    "docs/api/route_inventory.md",
    "docs/runtime/model_runtime_adapter_harness.md",
    "docs/runtime/local_loopback_model_runtime.md",
    "docs/runtime/RUNTIME_READINESS.md",
    "docs/runtime/MANUAL_SMOKE_REPORTS.md",
    "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
    "docs/control_center/CONTROL_CENTER_CONTRACT.md",
    "docs/control_center/DASHBOARD_SNAPSHOT.md",
    "docs/control_center/ACTION_PREVIEW_POLICY.md",
    "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
    "docs/control_center/FRONTEND_SAFETY_POLICY.md",
    "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
    "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE.md",
    "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
    "docs/control_center/APPROVAL_QUEUE_UI.md",
    "docs/control_center/RECEIPT_EVENT_VIEWER.md",
    "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
    "docs/control_center/EVENT_TIMELINE_UI.md",
    "docs/control_center/RUN_RECEIPT_TRACE_VIEWER.md",
    "docs/control_center/TRACE_REDACTION_POLICY.md",
    *REQUIRED_DESIGN_DOCS,
    *REQUIRED_UI_STRATEGY_DOCS,
    "docs/remote/REMOTE_WORKER_FOUNDATION.md",
    "docs/remote/REMOTE_NODE_SECURITY_MODEL.md",
    "docs/remote/REMOTE_JOB_ENVELOPE.md",
    "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
    "docs/remote/TAILNET_TRANSPORT_POLICY.md",
    "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
    "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
    "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
    "docs/backlog/mobile_companion_backlog.md",
    "docs/backlog/device_capability_broker_backlog.md",
    "docs/backlog/codex_plugin_enablement_backlog.md",
    "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
    "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _active_version(root: Path) -> str | None:
    match = re.search(r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*", _read(root / "VERSION.md"))
    return match.group(1) if match else None


def _version_tuple(version: str | None) -> tuple[int, int, int]:
    if not version:
        return (0, 0, 0)
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    version = _active_version(root)
    if not version:
        return ["VERSION.md active baseline is missing or malformed"]

    version_key = version.replace(".", "_")
    pyproject = _read(root / "pyproject.toml")
    init = _read(root / "src/ultimate_ai_agent/__init__.py")
    readme = _read(root / "README.md")

    if f'version = "{version}"' not in pyproject:
        failures.append("pyproject.toml version does not match VERSION.md")
    if f'__version__ = "{version}"' not in init:
        failures.append("package __version__ does not match VERSION.md")

    active_import = f"README_IMPORT_v{version_key}.md"
    active_master = f"ultimate_ai_agent_master_plan_v{version_key}.md"
    active_release_notes = f"docs/release_notes/v{version_key}.md"
    active_gate_plan = f"docs/implementation/foundation_gate_implementation_plan_v{version_key}.md"
    for rel_path in [active_import, active_master, active_release_notes, active_gate_plan, *REQUIRED_ACTIVE_DOCS]:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    if active_import not in readme:
        failures.append("README.md does not point to active README_IMPORT")
    if active_master not in readme:
        failures.append("README.md does not point to active master plan")
    if "docs/DOCUMENTATION_INDEX.md" not in readme:
        failures.append("README.md does not point to documentation index")
    if "docs/canonical/CANONICAL_DOC_MAP.md" not in readme:
        failures.append("README.md does not point to canonical doc map")

    documentation_index = _read(root / "docs/DOCUMENTATION_INDEX.md")
    expected_current_notes = f"Current release notes: `{active_release_notes}`"
    if expected_current_notes not in documentation_index:
        failures.append("docs/DOCUMENTATION_INDEX.md current release notes pointer does not match active version")

    release_notes_dir = root / "docs/release_notes"
    for release_note in release_notes_dir.glob("v*.md"):
        rel_path = release_note.relative_to(root).as_posix()
        if rel_path == active_release_notes:
            continue
        lowered = _read(release_note).lower()
        if "status: current release notes" in lowered:
            failures.append(f"historical release notes claim current status: {rel_path}")

    for rel_path in ACTIVE_DOCS_TO_SCAN:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing active scan target: {rel_path}")
            continue
        lowered = _read(path).lower()
        for phrase in UNSAFE_IMPLEMENTATION_CLAIMS:
            if phrase in lowered:
                failures.append(f"unsafe implemented-capability claim in {rel_path}: {phrase}")

    failures.extend(_verify_roadmap_milestone_charters(root))
    failures.extend(_verify_open_design_governance(root))
    failures.extend(_verify_openwebui_ccc_strategy(root))
    failures.extend(_verify_post_m20_roadmap_projection(root))

    policy_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md",
            "docs/tooling/CODEX_PLUGIN_RISK_POLICY.md",
            "docs/canonical/66_external_tooling_and_codex_plugin_governance.md",
            "docs/backlog/codex_plugin_enablement_backlog.md",
        ]
        if (root / rel_path).exists()
    )
    policy_expectations = {
        "iOS/macOS build plugins disabled or future-only": ["build ios apps", "build macos apps", "disabled"],
        "Computer Use disabled or approval-only": ["computer use", "disabled"],
        "Chrome authenticated profile disabled or approval-only": ["chrome authenticated", "disabled"],
        "plugin/skill installers disabled": ["plugin/skill installers", "disabled"],
        "Browser + Build Web Apps future approval": ["browser + build web apps", "approval"],
    }
    for label, required_fragments in policy_expectations.items():
        if not all(fragment in policy_text for fragment in required_fragments):
            failures.append(f"missing Codex plugin governance policy: {label}")

    return failures


def _verify_open_design_governance(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_DESIGN_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    design_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_DESIGN_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "design docs must say no design tools are enabled": "no design tools are enabled",
        "design docs must say design source of truth is repo-owned": "repo-owned source of truth",
        "design docs must say screenshots/design artifacts must not contain secrets": (
            "screenshots and design artifacts must not contain secrets"
        ),
        "design docs must say no automatic design-to-code": "no automatic design-to-code",
        "design docs must say no automatic design sync": "no automatic design sync",
        "design docs must say design SaaS is not authority": "no design saas is authority",
    }
    for failure, fragment in expectations.items():
        if fragment not in design_text:
            failures.append(failure)

    control_center_text = "\n".join(
        _read(root / rel_path)
        for rel_path in [
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
            "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
        ]
        if (root / rel_path).exists()
    )
    for rel_path in [
        "docs/design/OPEN_DESIGN_SYSTEM.md",
        "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
        "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
        "docs/design/ACCESSIBILITY_BASELINE.md",
        "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
        "docs/design/COMPONENT_TAXONOMY.md",
        "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
    ]:
        if rel_path not in control_center_text:
            failures.append(f"Control Center docs missing design doc link: {rel_path}")

    roadmap_text = ""
    roadmap_path = root / "docs/canonical/09_roadmap.md"
    if roadmap_path.exists():
        roadmap_text = _read(roadmap_path).lower()
    if "v0.18.2" not in roadmap_text or "open design system" not in roadmap_text:
        failures.append("roadmap must mention v0.18.2 Open Design implementation")

    return failures


def _verify_openwebui_ccc_strategy(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_UI_STRATEGY_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    ui_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_UI_STRATEGY_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "UI strategy docs must say OpenWebUI is the preferred conversational web shell": (
            "openwebui is the preferred conversational web shell"
        ),
        "UI strategy docs must say OpenWebUI is not the agent brain": "openwebui is not the agent brain",
        "UI strategy docs must say OpenWebUI must not bypass Python Agent Core": (
            "openwebui must not bypass python agent core"
        ),
        "UI strategy docs must say no OpenWebUI integration is implemented yet": (
            "no openwebui integration is implemented"
        ),
        "UI strategy docs must say no OpenWebUI deployment config is added": (
            "no openwebui deployment config is added"
        ),
        "UI strategy docs must say CCC means Control Center Clients": "ccc means control center clients",
        "UI strategy docs must say CCC is the governance/control layer": "ccc is the governance/control layer",
        "UI strategy docs must say Open Design does not replace OpenWebUI": "open design does not replace openwebui",
        "CCC docs must define CCC Web": "ccc web is the current typescript web control center",
        "CCC docs must define CCC iOS": "ccc ios is a future native mobile control client",
        "CCC docs must define CCC Android": "ccc android is a future native mobile control client",
        "CCC docs must define CCC macOS": "ccc macos is a future desktop/local companion client",
        "CCC docs must say all clients are control surfaces": (
            "all ccc clients are control surfaces, not the agent brain"
        ),
        "CCC docs must say all clients use Python Agent Core authority": (
            "all ccc clients must use python agent core authority"
        ),
        "CCC native strategy must say no Android app is implemented": "no android app is implemented yet",
        "CCC native strategy must say no iOS app is implemented": "no ios app is implemented yet",
        "CCC native strategy must say no macOS app is implemented": "no macos app is implemented yet",
        "CCC native strategy must say no CCC native implementation is added": (
            "no ccc native implementation is added"
        ),
        "CCC native strategy must say no native build workflow is added": "no native build workflow is added",
        "CCC native strategy must say no mobile sensor access is added": "no mobile sensor access is added",
        "CCC native strategy must say no OS permission integration is added": (
            "no os permission integration is added"
        ),
        "CCC native strategy must say no signing/store workflow is added": (
            "no signing, keystore, provisioning, app store, or play store workflow is added"
        ),
    }
    for failure, fragment in expectations.items():
        if fragment not in ui_text:
            failures.append(failure)

    return failures


def _verify_post_m20_roadmap_projection(root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_POST_M20_ROADMAP_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    roadmap_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_POST_M20_ROADMAP_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "Post-M20 roadmap docs must mention M21": "m21",
        "Post-M20 roadmap docs must mention M22": "m22",
        "Post-M20 roadmap docs must mention M23": "m23",
        "Post-M20 roadmap docs must mention M24": "m24",
        "Post-M20 roadmap docs must mention M25": "m25",
        "Post-M20 roadmap docs must mention M26": "m26",
        "Post-M20 roadmap docs must mention M27": "m27",
        "Post-M20 roadmap docs must mention M28": "m28",
        "Post-M20 roadmap docs must mention M29": "m29",
        "Post-M20 roadmap docs must mention M30": "m30",
        "Post-M20 roadmap docs must mention M31": "m31",
        "Post-M20 roadmap docs must mention M32": "m32",
        "Post-M20 roadmap docs must mention M33": "m33",
        "Post-M20 roadmap docs must mention M34": "m34",
        "Post-M20 roadmap docs must mention M35": "m35",
        "Post-M20 roadmap docs must mention M36": "m36",
        "Post-M20 roadmap docs must mention M37": "m37",
        "Post-M20 roadmap docs must mention M38": "m38",
        "Post-M20 roadmap docs must mention M39": "m39",
        "Post-M20 roadmap docs must mention M40": "m40",
        "M21 must be OpenWebUI Bridge + Chat Shell Integration Contract": (
            "openwebui bridge + chat shell integration contract"
        ),
        "M22 must be Local Model Runtime Activation Contract": "local model runtime activation contract",
        "M23 must be First Real Local LLM Call": "first real local llm call",
        "M24 must be Memory Provider Abstraction": "memory provider abstraction",
        "M26 must be Tool Execution Sandbox Contract": "tool execution sandbox contract",
        "M27 must mention MCP / Agent Skills / AGENTS.md": "mcp / agent skills / agents.md",
        "M31 must mention iOS / Android / macOS": "ios / android / macos",
        "M35 must mention Device Capability Broker Implementation, No Sensors": (
            "device capability broker implementation, no sensors"
        ),
        "M38 must be Browser Automation Contract, No Execution": "browser automation contract, no execution",
        "M39 must be Observability Export Adapters": "observability export adapters",
        "M40 must be Agent Evaluation + Regression Harness": "agent evaluation + regression harness",
        "Post-M20 roadmap docs must say planned/provisional": "planned/provisional",
        "Post-M20 roadmap docs must say no integration is added": "no integration",
        "Post-M20 roadmap docs must say no dependency is added": "no dependency",
        "Post-M20 roadmap docs must say no implementation is added": "no implementation",
    }
    for failure, fragment in expectations.items():
        if fragment not in roadmap_text:
            failures.append(failure)

    implemented_claims = [
        f"m{number} is implemented" for number in range(21, 41)
    ] + [
        "m21-m40 are implemented",
        "m21 through m40 are implemented",
        "post-m20 capabilities are implemented",
    ]
    if any(claim in roadmap_text for claim in implemented_claims):
        failures.append("M21-M40 docs must not claim implementation")

    return failures


def _verify_roadmap_milestone_charters(root: Path) -> list[str]:
    failures: list[str] = []
    charter_path = root / "docs/roadmap/MILESTONE_CHARTERS.md"
    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    if not charter_path.exists():
        failures.append("missing roadmap milestone charter doc: docs/roadmap/MILESTONE_CHARTERS.md")
    if not sequence_path.exists():
        failures.append("missing roadmap next sequence doc: docs/roadmap/NEXT_SEQUENCE_v0_17_5.md")
    if failures:
        return failures

    charter = _read(charter_path).lower()
    sequence = _read(sequence_path).lower()
    required_fields = [
        "version",
        "milestone code",
        "title",
        "status",
        "purpose",
        "allowed scope",
        "must not add",
        "dependencies",
        "acceptance criteria",
        "review prompt required",
        "hardening patch expectation",
        "source-of-truth docs",
        "notes",
    ]
    for field in required_fields:
        if field not in charter:
            failures.append(f"milestone charter template missing field: {field}")

    if "m14" not in sequence or "web control center local backend connection stabilization" not in sequence:
        failures.append("roadmap sequence must define M14 as Web Control Center Local Backend Connection Stabilization")
    if "m15" not in sequence or "approval queue + receipt/event viewer ui" not in sequence:
        failures.append("roadmap sequence must define M15 as Approval Queue + Receipt/Event Viewer UI")
    if "v0.17.4" not in sequence or "local browser smoke" not in sequence or "not m14" not in sequence:
        failures.append("roadmap sequence must keep v0.17.4 as local browser smoke / UX polish, not M14")

    forbidden_m14_smoke_patterns = [
        "m14 - local browser smoke",
        "m14 — local browser smoke",
        "m14: local browser smoke",
        "m14 - web control center local browser smoke",
        "m14 — web control center local browser smoke",
        "m14: web control center local browser smoke",
        "m14 - ux polish",
        "m14 — ux polish",
        "m14: ux polish",
    ]
    if any(pattern in sequence for pattern in forbidden_m14_smoke_patterns):
        failures.append("M14 must not be local browser smoke / UX polish")

    if _version_tuple(_active_version(root)) < (0, 19, 0):
        implemented_m15_claims = [
            "m15 is implemented",
            "m15 has been implemented",
            "implemented m15",
            "m15 implementation complete",
            "approval queue is implemented",
            "receipt/event viewer ui is implemented",
        ]
        for rel_path in ACTIVE_DOCS_TO_SCAN:
            path = root / rel_path
            if not path.exists():
                continue
            lowered = _read(path).lower()
            for claim in implemented_m15_claims:
                if claim in lowered:
                    failures.append(f"active docs claim M15 is already implemented: {rel_path}")
    else:
        docs_text = "\n".join(
            _read(root / rel_path).lower()
            for rel_path in [
                "docs/control_center/APPROVAL_QUEUE_UI.md",
                "docs/control_center/RECEIPT_EVENT_VIEWER.md",
                "docs/control_center/APPROVAL_RECEIPT_UI_SAFETY.md",
            ]
            if (root / rel_path).exists()
        )
        for fragment in [
            "read-only",
            "preview-only",
            "redacted",
            "no backend route",
            "approval authority remains",
        ]:
            if fragment not in docs_text:
                failures.append(f"M15 active docs missing safety fragment: {fragment}")
    return failures


def main() -> int:
    print("=== Ultimate AI Agent Documentation Integrity Verification ===")
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Documentation integrity verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
