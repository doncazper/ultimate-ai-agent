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
    RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_MAPPING_REF,
    RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_STATE_CLI_REF,
    RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS,
    build_runtime_mcp_catalog_filtering_read_model,
)


ROUTE = "/api/runtime/mcp-catalog-filtering"
DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_MCP_CATALOG_FILTERING.md"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/mcp_catalog_filtering.py"
TEST = ROOT / "tests/test_hermes_runtime_mcp_catalog_filtering.py"
UI = ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_mcp_catalog_filtering_read_model()

    if read_model.route_ref != f"GET {ROUTE}":
        failures.append("MCP catalog route ref is stale")
    if read_model.cli_ref != "uaa runtime inspect-mcp-catalog-filtering":
        failures.append("MCP catalog CLI ref is stale")
    if read_model.status != "metadata_catalog_filtering_posture":
        failures.append("MCP catalog posture is not metadata filtering")
    if (
        read_model.authority_state_route_ref
        != RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_STATE_ROUTE_REF
    ):
        failures.append("MCP catalog AuthorityState route ref drifted")
    if (
        read_model.authority_state_cli_ref
        != RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_STATE_CLI_REF
    ):
        failures.append("MCP catalog AuthorityState CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_MAPPING_REF
    ):
        failures.append("MCP catalog AuthorityState mapping ref drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("MCP catalog read model must allow read-only inspection")
    if (
        "adapter-ref:mcp-catalog-tool-invocation:not-implemented"
        not in read_model.unsupported_adapter_refs
    ):
        failures.append("MCP catalog unsupported tool-invocation adapter missing")
    if read_model.server_count != 3 or read_model.tool_slice_count != 6:
        failures.append("MCP catalog lacks expected metadata fixtures")
    if read_model.filtered_blocked_tool_count < 4:
        failures.append("MCP catalog lacks filtered blocked tool slices")
    if read_model.grant_required_tool_count < 1:
        failures.append("MCP catalog lacks grant-required posture")
    unsafe_flags = {
        "server install": read_model.install_enabled,
        "subprocess runtime": read_model.subprocess_runtime_enabled,
        "login": read_model.oauth_login_enabled,
        "tool invocation": read_model.tool_invocation_enabled,
        "connector write": read_model.connector_write_enabled,
        "raw manifest persistence": read_model.raw_manifest_persisted,
        "control center authority mint": read_model.control_center_mints_authority,
    }
    for label, enabled in unsafe_flags.items():
        if enabled:
            failures.append(f"{label} became enabled")
    missing_blocked = set(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing MCP catalog blocked refs: {sorted(missing_blocked)}")
    for server in read_model.servers:
        if server.install_enabled or server.subprocess_runtime_enabled:
            failures.append(f"server enables runtime launch: {server.server_ref}")
        if server.oauth_login_enabled or server.tool_invocation_enabled:
            failures.append(f"server enables login or invocation: {server.server_ref}")
        if server.connector_write_enabled or server.raw_manifest_persisted:
            failures.append(f"server persists or writes externally: {server.server_ref}")
        for tool in server.tool_slices:
            if tool.invocation_enabled or tool.runtime_dispatch_enabled:
                failures.append(f"tool enables invocation: {tool.tool_ref}")
            if tool.connector_write_enabled or tool.raw_schema_persisted:
                failures.append(f"tool persists schema or writes externally: {tool.tool_ref}")

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
        failures.append("API manifest missing MCP catalog route")
    elif route.side_effect_class != "local_dev_workspace_only":
        failures.append("MCP catalog route side-effect classification drifted")
    elif route.route_classification != "local_sensitive":
        failures.append("MCP catalog route classification drifted")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-mcp-catalog-filtering",
        "runtime_mcp_catalog_filtering",
        "metadata_only",
        "install_performed",
        "tool_invocation_performed",
        "connector_write_performed",
        "authority_state",
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
            "inspect-mcp-catalog-filtering",
        ]:
            if expected not in doc_text:
                failures.append(f"doc missing {expected}")

    cli_result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "inspect-mcp-catalog-filtering",
            "--json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("MCP catalog CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        read_model_payload = payload["runtime_mcp_catalog_filtering"]
        authority_state = payload.get("authority_state", {})
        if (
            authority_state.get("mapping_ref")
            != RUNTIME_MCP_CATALOG_FILTERING_AUTHORITY_MAPPING_REF
        ):
            failures.append("MCP catalog CLI AuthorityState mapping drifted")
        if authority_state.get("decision_outcome") != "allow":
            failures.append("MCP catalog CLI AuthorityState outcome drifted")
        if payload["install_performed"] is not False:
            failures.append("MCP catalog CLI claims install")
        if payload["subprocess_runtime_performed"] is not False:
            failures.append("MCP catalog CLI claims subprocess runtime")
        if payload["tool_invocation_performed"] is not False:
            failures.append("MCP catalog CLI claims tool invocation")
        if payload["connector_write_performed"] is not False:
            failures.append("MCP catalog CLI claims connector write")
        if read_model_payload["route_ref"] != f"GET {ROUTE}":
            failures.append("MCP catalog CLI returned stale route ref")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 30 MCP catalog filtering verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
