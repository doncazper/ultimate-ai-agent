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
    "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
    "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
    "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
    "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
    "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
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
    "docs/control_center/EVIDENCE_VIEWER.md",
    "docs/control_center/FILE_REFERENCE_VIEWER.md",
    "docs/control_center/MEMORY_VIEWER.md",
    "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
    "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
    "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
    "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
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
    "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
    "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
    "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
    "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_NON_GOALS.md",
    "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
    "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
    "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
    "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
    "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
    "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
    "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
    "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
    "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
    "docs/mobile/MOBILE_API_PLANNING.md",
    "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
    "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
    "docs/mobile/MOBILE_SECURITY_MODEL.md",
    "docs/mobile/MOBILE_CAPTURE_POLICY.md",
    "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
    "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
    "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
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

REQUIRED_OPENWEBUI_BRIDGE_DOCS = [
    "docs/openwebui/OPENWEBUI_BRIDGE_CONTRACT.md",
    "docs/openwebui/CHAT_SHELL_INTEGRATION_CONTRACT.md",
    "docs/openwebui/SESSION_TRANSCRIPT_REF_POLICY.md",
    "docs/openwebui/OPENWEBUI_SECURITY_MODEL.md",
    "docs/openwebui/OPENWEBUI_AUTHORITY_BOUNDARY.md",
    "docs/openwebui/OPENWEBUI_NON_GOALS.md",
    "docs/openwebui/OPENWEBUI_FUTURE_INTEGRATION_STAGES.md",
]

REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS = [
    "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
    "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
    "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
    "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
    "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
]

REQUIRED_MOBILE_DOCS = [
    "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
    "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
    "docs/mobile/MOBILE_API_PLANNING.md",
    "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
    "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
    "docs/mobile/MOBILE_SECURITY_MODEL.md",
    "docs/mobile/MOBILE_CAPTURE_POLICY.md",
    "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
    "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
    "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
]

REQUIRED_POST_M20_ROADMAP_DOCS = [
    "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
    "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
    "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
    "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
    "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
]

REQUIRED_DEVICE_CAPABILITY_DOCS = [
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
    "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
    "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
    "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
    "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
    "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
    "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
    "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
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
    *REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS,
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
    "docs/control_center/EVIDENCE_VIEWER.md",
    "docs/control_center/FILE_REFERENCE_VIEWER.md",
    "docs/control_center/MEMORY_VIEWER.md",
    "docs/control_center/EVIDENCE_FILE_MEMORY_VIEWER_SAFETY.md",
    "docs/control_center/LOCAL_RUNTIME_STATUS_UI.md",
    "docs/control_center/MANUAL_SMOKE_CONTROL_SURFACE.md",
    "docs/control_center/RUNTIME_SMOKE_UI_SAFETY.md",
    *REQUIRED_DESIGN_DOCS,
    *REQUIRED_UI_STRATEGY_DOCS,
    *REQUIRED_OPENWEBUI_BRIDGE_DOCS,
    *REQUIRED_DEVICE_CAPABILITY_DOCS,
    *REQUIRED_MOBILE_DOCS,
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
    failures.extend(_verify_openwebui_bridge_contract_docs(root, version))
    failures.extend(_verify_local_runtime_activation_docs(root, version))
    failures.extend(_verify_mobile_companion_contract_docs(root, version))
    failures.extend(_verify_m20_device_capability_docs(root, version))
    failures.extend(_verify_post_m20_roadmap_projection(root))
    failures.extend(_verify_m19_roadmap_currentness(root, version))
    failures.extend(_verify_post_m18_roadmap_status_labels(root))

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


def _verify_m19_roadmap_currentness(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 23, 1):
        return failures

    canonical_path = root / "docs/canonical/09_roadmap.md"
    post_m20_path = root / "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md"
    m21_m40_path = root / "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md"
    canonical = _read(canonical_path).lower() if canonical_path.exists() else ""
    post_m20 = _read(post_m20_path).lower() if post_m20_path.exists() else ""
    m21_m40 = _read(m21_m40_path).lower() if m21_m40_path.exists() else ""
    active_roadmaps = "\n".join([canonical, post_m20, m21_m40])

    if "active accepted baseline is v0.22.1" in canonical:
        failures.append("canonical roadmap must not claim active baseline v0.22.1 after v0.23.1")
    if "maintained through v0.22.1" in active_roadmaps:
        failures.append("active roadmap docs must not be maintained only through v0.22.1 after v0.23.1")

    m19_released = re.search(
        r"v0\.23\.0\s*/\s*m19[^\n]*(implemented|released)",
        canonical,
    )
    if _version_tuple(version) >= (0, 24, 0):
        m20_current = re.search(
            r"v0\.24\.0\s*/\s*m20[^\n]*(implemented|released)",
            canonical,
        )
        if _version_tuple(version) >= (0, 26, 0):
            m21_planned = True
            m21_current = re.search(
                r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_current = re.search(
                r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_planned = True
            m23_planned = re.search(
                r"(v0\.27\.0[^\n]*m23|m23[^\n]*v0\.27\.0|m23)[^\n]*planned/provisional",
                active_roadmaps,
            )
        elif _version_tuple(version) >= (0, 25, 0):
            m21_planned = True
            m21_current = re.search(
                r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
                active_roadmaps,
            )
            m22_current = True
            m22_planned = re.search(
                r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*planned/provisional",
                active_roadmaps,
            )
            m23_planned = re.search(
                r"(v0\.27\.0[^\n]*m23|m23[^\n]*v0\.27\.0|m23)[^\n]*planned/provisional",
                active_roadmaps,
            )
        else:
            m21_planned = re.search(
                r"v0\.25\.0\s*/\s*m21[^\n]*planned/provisional",
                active_roadmaps,
            )
            m21_current = True
            m22_current = True
            m22_planned = True
            m23_planned = True
    else:
        m20_current = re.search(
            r"v0\.24\.0\s*/\s*m20[^\n]*planned/provisional",
            canonical,
        )
        m21_planned = True
        m21_current = True
        m22_current = True
        m22_planned = True
        m23_planned = True
    if not m19_released:
        failures.append("canonical roadmap must mark M19/v0.23.0 as implemented/released")
    if not m20_current:
        if _version_tuple(version) >= (0, 24, 0):
            failures.append("canonical roadmap must mark M20/v0.24.0 as implemented/released")
        else:
            failures.append("canonical roadmap must keep M20/v0.24.0 planned/provisional")
    if not m21_planned:
        failures.append("active roadmap docs must keep M21/v0.25.0 planned/provisional")
    if _version_tuple(version) >= (0, 25, 0):
        if not m21_current:
            failures.append("active roadmap docs must mark M21/v0.25.0 as implemented/released")
        if _version_tuple(version) >= (0, 26, 0):
            if not m22_current:
                failures.append("active roadmap docs must mark M22/v0.26.0 as implemented/released")
        elif not m22_planned:
            failures.append("active roadmap docs must keep M22/v0.26.0 planned/provisional")
        if not m23_planned:
            failures.append("active roadmap docs must keep M23/v0.27.0 planned/provisional")

    forbidden_claims = [
        "mobile app is implemented",
        "android app is implemented",
        "ios app is implemented",
        "mobile sensor access is implemented",
        "os permission integration is implemented",
    ]
    if _version_tuple(version) < (0, 24, 0):
        forbidden_claims.extend(
            [
                "m20 is implemented",
                "m20 has implemented",
                "device capability broker is implemented",
                "device capability broker implementation is complete",
            ]
        )
    for claim in forbidden_claims:
        if claim in active_roadmaps:
            failures.append(f"active roadmap docs must not claim future mobile capability implementation: {claim}")

    if _version_tuple(version) >= (0, 26, 0):
        if "m23-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M23-M40 planned/provisional")
    elif _version_tuple(version) >= (0, 25, 0):
        if "m22-m40 remain planned/provisional" not in active_roadmaps:
            failures.append("post-M20 roadmap docs must keep M22-M40 planned/provisional")
    elif "m21-m40 remain planned/provisional" not in active_roadmaps:
        failures.append("post-M20 roadmap docs must keep M21-M40 planned/provisional")

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


def _verify_openwebui_bridge_contract_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 25, 0):
        return failures

    for rel_path in REQUIRED_OPENWEBUI_BRIDGE_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    bridge_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_OPENWEBUI_BRIDGE_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M21 docs must say contract-only": "contract-only",
        "M21 docs must say OpenWebUI is preferred conversational web shell": (
            "openwebui is the preferred conversational web shell"
        ),
        "M21 docs must say OpenWebUI is not the agent brain": "openwebui is not the agent brain",
        "M21 docs must say Python Agent Core remains authority": "python agent core remains authority",
        "M21 docs must say no OpenWebUI integration is implemented": (
            "no openwebui integration is implemented"
        ),
        "M21 docs must say no deployment config is added": "no deployment config is added",
        "M21 docs must say no direct tool execution": "no direct tool execution",
        "M21 docs must say no direct memory write": "no direct memory write",
        "M21 docs must say no runtime execution": "no runtime execution",
        "M21 docs must say no provider call": "no provider call",
        "M21 docs must say no backend API route": "no backend api route",
        "M21 docs must say refs are identifiers only": "refs are identifiers only",
        "M21 docs must mention M22": "m22",
        "M21 docs must mention M23": "m23",
    }
    for failure, fragment in expectations.items():
        if fragment not in bridge_text:
            failures.append(failure)

    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "README.md",
            "VERSION.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    active_expectations = {
        "active docs must mark M21/v0.25.0 as implemented/released": "v0.25.0",
        "active docs must mark M22/v0.26.0 as implemented/released": "v0.26.0",
        "active docs must keep M23 planned/provisional": "m23",
        "active docs must link OpenWebUI bridge docs": "docs/openwebui/openwebui_bridge_contract.md",
    }
    for failure, fragment in active_expectations.items():
        if fragment not in active_docs:
            failures.append(failure)

    forbidden_active_claims = [
        "openwebui integration is implemented",
        "openwebui deployment config is implemented",
        "openwebui docker config is implemented",
        "openwebui plugin is enabled",
        "openwebui tool bridge is enabled",
        "openwebui admin workflow is enabled",
        "m23 is implemented",
        "local llm call is implemented",
    ]
    if _version_tuple(version) < (0, 26, 0):
        forbidden_active_claims.append("m22 is implemented")
    for claim in forbidden_active_claims:
        if re.search(rf"(?<!no ){re.escape(claim)}", active_docs):
            failures.append(f"active docs must not claim M21+ runtime implementation: {claim}")

    return failures


def _verify_local_runtime_activation_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 26, 0):
        return failures

    for rel_path in REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    runtime_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_LOCAL_RUNTIME_ACTIVATION_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M22 docs must say contract-only": "contract-only",
        "M22 docs must say no model was called": "no model was called",
        "M22 docs must say no runtime was activated": "no runtime was activated",
        "M22 docs must say no endpoint was contacted": "no endpoint was contacted",
        "M22 docs must say no backend API route": "no backend api route",
        "M22 docs must say OpenAPI path count remains 74": "openapi path count",
        "M22 docs must say no runtime execution": "no runtime execution",
        "M22 docs must say no provider call": "no provider call",
        "M22 docs must say no endpoint probe": "no endpoint probe",
        "M22 docs must say no user prompt processing": "no user prompt",
        "M22 docs must say no tool execution": "no tool",
        "M22 docs must say no memory write": "no memory",
        "M22 docs must say no dependency": "no dependency",
        "M22 docs must say M23 remains future": "m23 remains future",
    }
    for failure, fragment in expectations.items():
        if fragment not in runtime_text:
            failures.append(failure)

    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "README.md",
            "VERSION.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    active_expectations = {
        "active docs must mark M22/v0.26.0 as implemented/released": "v0.26.0",
        "active docs must keep M23 planned/provisional": "m23",
        "active docs must link M22 activation docs": "docs/runtime/local_model_runtime_activation_contract.md",
    }
    for failure, fragment in active_expectations.items():
        if fragment not in active_docs:
            failures.append(failure)

    forbidden_claims = [
        "m23 is implemented",
        "first real local llm call is implemented",
        "local llm call is implemented",
        "runtime activation is implemented",
        "endpoint probe is implemented",
        "model runtime call is implemented",
    ]
    for claim in forbidden_claims:
        if re.search(rf"(?<!no ){re.escape(claim)}", active_docs):
            failures.append(f"active docs must not claim M23+ runtime implementation: {claim}")

    return failures


def _verify_mobile_companion_contract_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_MOBILE_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    mobile_text = "\n".join(
        _read(root / rel_path).lower() for rel_path in REQUIRED_MOBILE_DOCS if (root / rel_path).exists()
    )
    expectations = {
        "mobile docs must say M19 is contract/API planning only": "contract/api planning only",
        "mobile docs must mention iOS": "ios",
        "mobile docs must mention Android": "android",
        "mobile docs must say no mobile app": "no mobile app",
        "mobile docs must say no Android app": "no android app",
        "mobile docs must say no iOS app": "no ios app",
        "mobile docs must say no native build workflow": "no native build workflow",
        "mobile docs must say no OS permission integration": "no os permission integration",
        "mobile docs must say no mobile sensor access": "no mobile sensor access",
        "mobile docs must say Device Capability Broker is required before sensors": (
            "device capability broker is required before sensors"
        ),
        "mobile docs must say capture cannot silently become memory": (
            "capture cannot silently become memory"
        ),
        "mobile docs must say phone/mobile is not the agent brain": "phone/mobile is not the agent brain",
        "mobile docs must say phone output is not trusted control input": (
            "phone output is not trusted control input"
        ),
        "mobile docs must say no native build workflow is added": "no native build workflow is added",
    }
    if _version_tuple(version) >= (0, 25, 0):
        expectations["mobile docs must say M20 is contract-only"] = (
            "m20 device capability broker contract as contract-only"
        )
    elif _version_tuple(version) >= (0, 24, 0):
        expectations["mobile docs must say M20 is contract-only"] = (
            "m20 device capability broker contract as contract-only"
        )
        expectations["mobile docs must keep M21 planned/provisional"] = "m21 remains planned/provisional"
    else:
        expectations["mobile docs must say M20 remains planned"] = "m20 remains planned"
    for failure, fragment in expectations.items():
        if fragment not in mobile_text:
            failures.append(failure)

    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    sequence = _read(sequence_path).lower() if sequence_path.exists() else ""
    m19_section = _milestone_section(sequence, "v0.23.0 / m19")
    m20_section = _milestone_section(sequence, "v0.24.0 / m20")
    if "status: implemented" not in m19_section:
        failures.append("roadmap sequence must mark M19/v0.23.0 as implemented")
    if _version_tuple(version) >= (0, 24, 0):
        if "status: implemented" not in m20_section:
            failures.append("roadmap sequence must mark M20/v0.24.0 as implemented")
    elif "status: planned/provisional" not in m20_section:
        failures.append("roadmap sequence must keep M20/v0.24.0 planned/provisional")

    active_docs = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/canonical/09_roadmap.md",
            "docs/canonical/64_mobile_companion_and_device_capability_broker.md",
            "docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/maintenance/documentation_integrity_checklist.md",
        ]
        if (root / rel_path).exists()
    )
    for fragment in [
        "m19",
        "contract/api planning only",
        "no mobile app",
        "no android app",
        "no ios app",
        "no native build workflow",
        "no os permission integration",
        "no mobile sensor access",
        "device capability broker is required before sensors",
        "capture cannot silently become memory",
        "phone/mobile is not the agent brain",
    ]:
        if fragment not in active_docs:
            failures.append(f"active docs missing M19 mobile boundary fragment: {fragment}")
    if _version_tuple(version) >= (0, 25, 0):
        for fragment in [
            "v0.24.0 implements m20 device capability broker contract",
            "contract-only planning and validation",
            "v0.25.0",
            "m21",
        ]:
            if fragment not in active_docs:
                failures.append(f"active docs missing M21 bridge fragment: {fragment}")
    elif _version_tuple(version) >= (0, 24, 0):
        for fragment in [
            "v0.24.0 implements m20 device capability broker contract",
            "contract-only planning and validation",
            "m21 remains planned/provisional",
        ]:
            if fragment not in active_docs:
                failures.append(f"active docs missing M20 device contract fragment: {fragment}")
    elif "m20 remains planned" not in active_docs:
        failures.append("active docs missing M19 mobile boundary fragment: m20 remains planned")

    return failures


def _verify_m20_device_capability_docs(root: Path, version: str | None) -> list[str]:
    failures: list[str] = []
    if _version_tuple(version) < (0, 24, 0):
        return failures

    for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS:
        if not (root / rel_path).exists():
            failures.append(f"missing active documentation file: {rel_path}")

    device_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS
        if (root / rel_path).exists()
    )
    expectations = {
        "M20 device docs must be contract-only": "contract-only",
        "M20 device docs must say no sensor access": "no sensor access",
        "M20 device docs must say no OS permission integration": "no os permission integration",
        "M20 device docs must say no native app": "no native app",
        "M20 device docs must say no backend API route": "no backend api route",
        "M20 device docs must say no Device Capability Broker runtime implementation": (
            "no device capability broker runtime implementation"
        ),
        "M20 device docs must say capture cannot silently become memory": (
            "capture cannot silently become memory"
        ),
        "M20 device docs must say broker output is not trusted control input": (
            "device capability broker output is not trusted control input by default"
        ),
        "M20 device docs must block external sends": "external sends are not allowed",
        "M20 device docs must say no capabilities are enabled": "no capabilities are enabled",
        "M20 device docs must say no capabilities are implemented": "no capabilities are implemented",
        "M20 device docs must say raw payloads are blocked": "raw payloads are blocked",
        "M20 device docs must say user gesture is future contract metadata": (
            "user gesture is future contract metadata"
        ),
        "M20 device docs must say notification runtime is blocked": "notification runtime is blocked",
        "M20 device docs must say background services are blocked": "background services are blocked",
        "M20 device docs must say device pairing runtime is future": "device pairing runtime is future",
        "M20 device docs must say receipts remain redacted": "receipts remain redacted",
    }
    if _version_tuple(version) >= (0, 25, 0):
        expectations["M20 device docs must mention M21"] = "m21"
    else:
        expectations["M20 device docs must mention M21 remains planned/provisional"] = (
            "m21 remains planned/provisional"
        )
    for failure, fragment in expectations.items():
        if fragment not in device_text:
            failures.append(f"{failure}: docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md")

    active_roadmaps = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
        ]
        if (root / rel_path).exists()
    )
    m20_released = re.search(r"v0\.24\.0\s*/\s*m20[^\n]*(implemented|released)", active_roadmaps)
    if _version_tuple(version) >= (0, 26, 0):
        m21_current = re.search(
            r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_current = re.search(
            r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_planned = True
        m21_planned = True
    elif _version_tuple(version) >= (0, 25, 0):
        m21_current = re.search(
            r"(v0\.25\.0[^\n]*m21|m21[^\n]*v0\.25\.0|m21)[^\n]*(implemented|released)",
            active_roadmaps,
        )
        m22_current = True
        m22_planned = re.search(
            r"(v0\.26\.0[^\n]*m22|m22[^\n]*v0\.26\.0|m22)[^\n]*planned/provisional",
            active_roadmaps,
        )
        m21_planned = True
    else:
        m21_current = True
        m22_current = True
        m22_planned = True
        m21_planned = re.search(r"v0\.25\.0\s*/\s*m21[^\n]*planned/provisional", active_roadmaps)
    if not m20_released:
        failures.append("active roadmap docs must mark M20/v0.24.0 as implemented/released")
    if not m21_planned:
        failures.append("active roadmap docs must keep M21/v0.25.0 planned/provisional")
    if _version_tuple(version) >= (0, 25, 0):
        if not m21_current:
            failures.append("active roadmap docs must mark M21/v0.25.0 as implemented/released")
        if _version_tuple(version) >= (0, 26, 0):
            if not m22_current:
                failures.append("active roadmap docs must mark M22/v0.26.0 as implemented/released")
        elif not m22_planned:
            failures.append("active roadmap docs must keep M22/v0.26.0 planned/provisional")

    linked_docs_text = "\n".join(
        _read(root / rel_path).lower()
        for rel_path in [
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
        ]
        if (root / rel_path).exists()
    )
    for rel_path in REQUIRED_DEVICE_CAPABILITY_DOCS:
        if rel_path.lower() not in linked_docs_text:
            failures.append(f"device capability docs must be linked from active indexes: {rel_path}")

    forbidden_claims = [
        "openwebui integration is implemented",
        "mobile app is implemented",
        "android app is implemented",
        "ios app is implemented",
        "macos app is implemented",
        "sensor access is implemented",
        "os permission integration is implemented",
    ]
    if _version_tuple(version) < (0, 25, 0):
        forbidden_claims.extend(["m21 is implemented", "m21 has implemented"])
    for claim in forbidden_claims:
        if claim in active_roadmaps:
            failures.append(f"active roadmap docs must not claim future M21/native capability implementation: {claim}")

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
    }
    active_version_tuple = _version_tuple(_active_version(root))
    if active_version_tuple >= (0, 26, 0):
        expectations["Post-M20 roadmap docs must keep M23-M40 planned/provisional"] = (
            "m23-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M22 is implemented/released"] = (
            "m22 is implemented/released"
        )
    elif active_version_tuple >= (0, 25, 0):
        expectations["Post-M20 roadmap docs must keep M22-M40 planned/provisional"] = (
            "m22-m40 remain planned/provisional"
        )
        expectations["Post-M20 roadmap docs must say M21 is implemented/released"] = (
            "m21 is implemented/released"
        )
    else:
        expectations["Post-M20 roadmap docs must say no implementation is added"] = "no implementation"
    for failure, fragment in expectations.items():
        if fragment not in roadmap_text:
            failures.append(failure)

    if active_version_tuple >= (0, 26, 0):
        implemented_claim_start = 23
    elif active_version_tuple >= (0, 25, 0):
        implemented_claim_start = 22
    else:
        implemented_claim_start = 21
    implemented_claims = [
        f"m{number} is implemented" for number in range(implemented_claim_start, 41)
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


def _verify_post_m18_roadmap_status_labels(root: Path) -> list[str]:
    active = _version_tuple(_active_version(root))
    if active < (0, 22, 1):
        return []

    failures: list[str] = []
    sequence_path = root / "docs/roadmap/NEXT_SEQUENCE_v0_17_5.md"
    roadmap_path = root / "docs/canonical/09_roadmap.md"
    if not sequence_path.exists() or not roadmap_path.exists():
        return failures

    sequence = _read(sequence_path).lower()
    roadmap = _read(roadmap_path).lower()
    m18_section = _milestone_section(sequence, "v0.22.0 / m18")
    if not m18_section or "status: implemented" not in m18_section:
        failures.append("roadmap sequence must mark M18/v0.22.0 as implemented after accepted v0.22.0")
    if "v0.22.0 has implemented m18" not in roadmap:
        failures.append("canonical roadmap must mention accepted M18 implementation after v0.22.0")
    milestone_expectations = {
        "v0.23.0 / m19": "implemented",
        "v0.24.0 / m20": "implemented" if active >= (0, 24, 0) else "planned/provisional",
    }
    for milestone, expected_status in milestone_expectations.items():
        section = _milestone_section(sequence, milestone)
        if not section:
            failures.append(f"roadmap sequence missing {milestone.upper()} status")
            continue
        if f"status: {expected_status}" not in section:
            failures.append(f"roadmap sequence must mark {milestone.upper()} {expected_status}")
    if active >= (0, 26, 0):
        if "m23-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M23-M40 planned/provisional")
    elif active >= (0, 25, 0):
        if "m22-m40" not in sequence or "planned/provisional" not in sequence:
            failures.append("roadmap sequence must keep M22-M40 planned/provisional")
    elif "m21-m40 remain planned/provisional" not in sequence:
        failures.append("roadmap sequence must keep M21-M40 planned/provisional")
    return failures


def _milestone_section(text: str, milestone: str) -> str:
    heading_marker = "## "
    index = text.find(f"{heading_marker}{milestone}")
    if index == -1:
        index = text.find(f"{heading_marker}")
        while index != -1 and milestone not in text[index : text.find("\n", index) if text.find("\n", index) != -1 else None]:
            index = text.find(f"{heading_marker}", index + len(heading_marker))
    if index == -1:
        return ""
    next_heading = text.find("##", index + 1)
    return text[index : next_heading if next_heading != -1 else None]


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
