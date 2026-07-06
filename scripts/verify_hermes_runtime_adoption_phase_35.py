#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS,
    build_runtime_preview_rail_read_model,
)


ROUTE = "/api/runtime/preview-rail"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_PREVIEW_RAIL.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/preview_rail.py"
TEST = ROOT / "tests/test_hermes_runtime_preview_rail.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_preview_rail_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("preview rail route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-preview-rail":
        failures.append("preview rail CLI ref is stale")
    if read_model.status != "safe_ref_preview_rail_posture":
        failures.append("preview rail posture is not safe-ref only")
    if read_model.slot_count != 6:
        failures.append("preview rail lacks expected preview slots")
    if read_model.safe_ref_ready_count != 2:
        failures.append("preview rail safe-ref count drifted")
    if read_model.execution_blocked_count != 1:
        failures.append("preview rail lacks blocked runtime event posture")
    unsafe_flags = {
        "browser automation": read_model.browser_automation_enabled,
        "raw sensitive file display": read_model.raw_sensitive_file_display_enabled,
        "direct runtime payload rendering": (
            read_model.direct_runtime_payload_rendering_enabled
        ),
        "screenshot capture": read_model.screenshot_capture_enabled,
        "file read": read_model.file_read_enabled,
        "file write": read_model.file_write_enabled,
        "shell execution": read_model.shell_execution_enabled,
        "provider call": read_model.provider_call_enabled,
        "control center authority mint": read_model.control_center_mints_authority,
        "raw path persistence": read_model.raw_path_persisted,
        "raw file content persistence": read_model.raw_file_content_persisted,
        "raw runtime payload persistence": read_model.raw_runtime_payload_persisted,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_PREVIEW_RAIL_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing preview rail blocked refs: {sorted(missing_blocked)}")
    for slot in read_model.slots:
        if slot.browser_automation_enabled or slot.screenshot_capture_enabled:
            failures.append(f"slot exposes browser/screenshot work: {slot.slot_ref}")
        if (
            slot.raw_sensitive_file_display_enabled
            or slot.direct_runtime_payload_rendering_enabled
        ):
            failures.append(f"slot exposes raw rendering: {slot.slot_ref}")
        if slot.file_read_enabled or slot.file_write_enabled:
            failures.append(f"slot exposes file access: {slot.slot_ref}")
        if slot.shell_execution_enabled or slot.provider_call_enabled:
            failures.append(f"slot exposes shell/provider: {slot.slot_ref}")
        if (
            slot.raw_path_persisted
            or slot.raw_file_content_persisted
            or slot.raw_runtime_payload_persisted
        ):
            failures.append(f"slot persists raw data: {slot.slot_ref}")

    manifest = build_api_manifest(app)
    route = next(
        (
            item
            for item in manifest.routes
            if item.path == ROUTE and item.method == "GET"
        ),
        None,
    )
    if route is None:
        failures.append("API manifest missing preview rail route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("preview rail route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("preview rail route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-preview-rail",
        "runtime_preview_rail",
        "bounded_preview_only",
        "raw_runtime_payloads_omitted",
        "browser_automation_performed",
        "screenshot_capture_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    for path in [DOC, CORE, TEST, UI]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    if DOC.exists():
        doc_text = DOC.read_text(encoding="utf-8")
        for expected in [
            "Full-Strength",
            "Repo-Safe",
            "Blocked / Needs Authority",
            "Exact Promotion Path",
            ROUTE,
            "inspect-preview-rail",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-preview-rail",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("preview rail CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_preview_rail"]
        if payload["browser_automation_performed"] is not False:
            failures.append("preview rail CLI claims browser automation")
        if payload["screenshot_capture_performed"] is not False:
            failures.append("preview rail CLI claims screenshot capture")
        if payload["file_read_performed"] is not False:
            failures.append("preview rail CLI claims file read")
        if payload["file_write_performed"] is not False:
            failures.append("preview rail CLI claims file write")
        if payload["shell_execution_performed"] is not False:
            failures.append("preview rail CLI claims shell execution")
        if payload["provider_call_performed"] is not False:
            failures.append("preview rail CLI claims provider call")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("preview rail CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 35 preview rail verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
