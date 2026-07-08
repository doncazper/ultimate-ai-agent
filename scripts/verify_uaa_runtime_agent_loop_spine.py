#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center.agent_loop import (  # noqa: E402
    AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS,
    AGENT_LOOP_THREAD_CONTRACT_REF,
    AGENT_LOOP_THREAD_ROUTE_REF,
    HIGH_MATURITY_COMPONENT_IDS,
    HIGH_MATURITY_SPINE_CONTRACT_REF,
    build_agent_loop_thread_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


def main() -> int:
    failures: list[str] = []
    temp_dir = tempfile.TemporaryDirectory(prefix="uaa-agent-loop-verifier-")
    repo = FounderLoopRepository(Path(temp_dir.name) / "founder-loop")
    today = repo.today_summary(limit=12)
    thread = build_agent_loop_thread_read_model(
        today_summary=today,
        actions_inbox=repo.actions_inbox(limit=50),
        evidence_timeline=repo.evidence_timeline(limit=50),
        memory_review=repo.memory_review(limit=20),
        proof_index={"items": []},
        trust_authority_matrix={"lanes": []},
    )

    if thread.get("contract_ref") != AGENT_LOOP_THREAD_CONTRACT_REF:
        failures.append("Agent Loop contract ref drifted")
    if thread.get("route_ref") != AGENT_LOOP_THREAD_ROUTE_REF:
        failures.append("Agent Loop route ref drifted")
    for field in [
        "backend_owned",
        "local_read_model_only",
        "safe_refs_only",
    ]:
        if thread.get(field) is not True:
            failures.append(f"Agent Loop {field} must be true")
    if thread.get("raw_content_included") is not False:
        failures.append("Agent Loop must not include raw content")

    high_maturity = thread.get("high_maturity_spine_readiness")
    if not isinstance(high_maturity, dict):
        failures.append("High-Maturity Agent Spine readiness map missing")
    else:
        if high_maturity.get("contract_ref") != HIGH_MATURITY_SPINE_CONTRACT_REF:
            failures.append("High-Maturity Agent Spine contract ref drifted")
        if high_maturity.get("route_ref") != AGENT_LOOP_THREAD_ROUTE_REF:
            failures.append("High-Maturity Agent Spine route ref drifted")
        if not str(high_maturity.get("cli_ref", "")).endswith(
            "inspect-high-maturity-spine"
        ):
            failures.append("High-Maturity Agent Spine CLI ref missing")
        for field in [
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
        ]:
            if high_maturity.get(field) is not True:
                failures.append(f"High-Maturity Agent Spine {field} must be true")
        if high_maturity.get("raw_content_included") is not False:
            failures.append("High-Maturity Agent Spine must not include raw content")
        rows = high_maturity.get("rows")
        if not isinstance(rows, list):
            failures.append("High-Maturity Agent Spine rows missing")
        else:
            weakness_ids = [row.get("weakness_id") for row in rows if isinstance(row, dict)]
            if weakness_ids != list(HIGH_MATURITY_COMPONENT_IDS):
                failures.append("High-Maturity Agent Spine W1-W13 coverage drifted")
            for row in rows:
                if not isinstance(row, dict):
                    failures.append("High-Maturity Agent Spine row is not an object")
                    continue
                if row.get("safe_refs_only") is not True:
                    failures.append(
                        f"High-Maturity Agent Spine row not safe-ref-only: {row.get('weakness_id')}"
                    )
                for forbidden_flag in [
                    "authority_broadened",
                    "runtime_model_calls_added",
                    "provider_sdk_calls_added",
                    "live_web_fetching_added",
                    "browser_automation_added",
                    "connector_writes_added",
                    "unrestricted_shell_added",
                    "plugin_runtime_import_added",
                    "production_authority_added",
                ]:
                    if row.get(forbidden_flag) is not False:
                        failures.append(
                            "High-Maturity Agent Spine broadened authority: "
                            f"{row.get('weakness_id')} {forbidden_flag}"
                        )
                for required_list in ["evidence_refs", "test_refs"]:
                    if not row.get(required_list):
                        failures.append(
                            "High-Maturity Agent Spine row missing "
                            f"{required_list}: {row.get('weakness_id')}"
                        )

    authority = thread.get("authority_posture")
    if not isinstance(authority, dict):
        failures.append("Agent Loop authority posture missing")
    else:
        for denied_flag in [
            "control_center_mints_authority",
            "runtime_model_calls_enabled",
            "provider_sdk_calls_enabled",
            "live_web_fetching_enabled",
            "browser_automation_enabled",
            "connector_writes_enabled",
            "unrestricted_shell_enabled",
            "plugin_runtime_import_enabled",
            "memory_write_authority_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ]:
            if authority.get(denied_flag) is not False:
                failures.append(f"Agent Loop broadened authority: {denied_flag}")

    blocked_refs = set(thread.get("blocked_authority_refs") or [])
    missing_blocked_refs = set(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS) - blocked_refs
    if missing_blocked_refs:
        failures.append(
            "Agent Loop missing blocked authority refs: "
            + ", ".join(sorted(missing_blocked_refs))
        )

    manifest = build_api_manifest(app)
    route_index = {(route.method, route.path): route for route in manifest.routes}
    route = route_index.get(("GET", "/control-center/agent-loop/thread"))
    if route is None:
        failures.append("GET /control-center/agent-loop/thread missing from manifest")
    else:
        if route.side_effect_class != "local_dev_workspace_only":
            failures.append("Agent Loop route side-effect class drifted")
        if route.route_classification != "local_sensitive":
            failures.append("Agent Loop route classification drifted")
    if (
        "control_center_agent_loop_thread_read_model"
        not in manifest.capabilities_declared
    ):
        failures.append("Agent Loop manifest capability missing")

    docs = [
        ROOT / "docs/control_center/UAA_RUNTIME_AGENT_LOOP_SPINE.md",
        ROOT / "docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md",
    ]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        compact_text = " ".join(text.split())
        if AGENT_LOOP_THREAD_CONTRACT_REF not in text:
            failures.append(f"Agent Loop contract ref missing from {doc}")
        if doc.name == "UAA_RUNTIME_AGENT_LOOP_SPINE.md":
            for fragment in [
                "exact AuthorityLease scope",
                "AuthorityLease-gated capabilities",
                "High-Maturity Agent Spine",
                "W1-W13",
            ]:
                if fragment not in compact_text:
                    failures.append(
                        f"AuthorityLease capability wording missing from {doc}: {fragment}"
                    )
            for stale in ["graduated lanes"]:
                if stale in compact_text:
                    failures.append(f"stale authority wording remains in {doc}: {stale}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA runtime Agent Loop Spine verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
