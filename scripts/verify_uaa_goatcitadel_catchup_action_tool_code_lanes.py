#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center.action_tool_code_catalog import (  # noqa: E402
    ACTION_TOOL_CODE_CATALOG_CONTRACT_REF,
    ACTION_TOOL_CODE_CATALOG_SOURCE,
    build_action_tool_code_lane_catalog_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


BROAD_AUTHORITY_FLAGS = (
    "generic_tool_execution_enabled",
    "unrestricted_shell_execution_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "plugin_runtime_import_enabled",
    "remote_execution_enabled",
    "provider_model_call_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="uaa-action-tool-code-") as temp:
        repo = FounderLoopRepository(Path(temp) / "founder-loop")
        inbox = repo.actions_inbox(limit=50)
        catalog = inbox.get("action_tool_code_lane_catalog_read_model") or {}

    direct_catalog = build_action_tool_code_lane_catalog_read_model().model_dump(
        mode="json"
    )
    for source_name, model in [
        ("direct", direct_catalog),
        ("repository", catalog),
    ]:
        if model.get("contract_ref") != ACTION_TOOL_CODE_CATALOG_CONTRACT_REF:
            failures.append(f"{source_name} catalog contract ref drifted")
        if model.get("source") != ACTION_TOOL_CODE_CATALOG_SOURCE:
            failures.append(f"{source_name} catalog source drifted")
        for field in [
            "backend_owned",
            "control_center_presentation_only",
            "safe_refs_only",
        ]:
            if model.get(field) is not True:
                failures.append(f"{source_name} catalog {field} must be true")
        if model.get("raw_content_included") is not False:
            failures.append(f"{source_name} catalog raw content must be omitted")
        for flag in BROAD_AUTHORITY_FLAGS:
            if model.get(flag) is not False:
                failures.append(f"{source_name} catalog broadened {flag}")
        if model.get("entry_count") != len(model.get("entries") or []):
            failures.append(f"{source_name} catalog entry count drifted")
        if model.get("preview_only_count") != 4:
            failures.append(f"{source_name} catalog preview count drifted")
        if model.get("exact_local_mutation_count") != 1:
            failures.append(f"{source_name} catalog exact local lane count drifted")
        if model.get("exact_runtime_lane_count") != 4:
            failures.append(f"{source_name} catalog exact runtime lane count drifted")
        if model.get("blocked_count") != 4:
            failures.append(f"{source_name} catalog blocked count drifted")
        entries = model.get("entries") or []
        for entry in entries:
            if not isinstance(entry, dict):
                failures.append(f"{source_name} catalog contains non-dict entry")
                continue
            for flag in BROAD_AUTHORITY_FLAGS:
                if entry.get(flag) is not False:
                    failures.append(
                        f"{source_name} entry {entry.get('capability_id')} broadened {flag}"
                    )
            if entry.get("operator_visible") is not True:
                failures.append(
                    f"{source_name} entry {entry.get('capability_id')} hidden"
                )
            if entry.get("inspectable_now") is not True:
                failures.append(
                    f"{source_name} entry {entry.get('capability_id')} not inspectable"
                )

    manifest = build_api_manifest(app)
    route_index = {(route.method, route.path): route for route in manifest.routes}
    route = route_index.get(("GET", "/control-center/actions/inbox"))
    if route is None:
        failures.append("GET /control-center/actions/inbox missing from manifest")
    else:
        if route.side_effect_class != "local_dev_workspace_only":
            failures.append("Action Inbox route side-effect class drifted")
        if route.route_classification != "local_sensitive":
            failures.append("Action Inbox route classification drifted")

    docs = [
        ROOT / "docs/control_center/UAA_GOATCITADEL_CATCHUP_ACTION_TOOL_CODE_LANES.md",
        ROOT / "docs/control_center/UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md",
    ]
    for doc in docs:
        if not doc.exists():
            failures.append(f"required doc missing: {doc.name}")
            continue
        text = doc.read_text(encoding="utf-8")
        if ACTION_TOOL_CODE_CATALOG_CONTRACT_REF not in text:
            failures.append(f"catalog contract ref missing from {doc.name}")
        if "inspect-action-tool-code-catalog" not in text:
            failures.append(f"CLI inspection ref missing from {doc.name}")
        if "generic tool execution remains blocked" not in text.lower():
            failures.append(f"generic tool execution blocker missing from {doc.name}")

    cli_text = (ROOT / "scripts/dev/uaa_founder_loop.py").read_text(
        encoding="utf-8"
    )
    if "inspect-action-tool-code-catalog" not in cli_text:
        failures.append("Founder Loop CLI catalog command missing")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA GoatCitadel catch-up action/tool/code lane verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
