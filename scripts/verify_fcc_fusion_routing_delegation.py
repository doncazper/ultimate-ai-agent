#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.fusion_routing import (  # noqa: E402
    FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF,
    FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS,
    build_fusion_routing_delegation_read_model,
    forbidden_fusion_claims,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


DOC_PATHS = (
    ROOT / "docs/control_center/FCC_FUSION_ROUTING_DELEGATION.md",
    ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
    ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx",
)


def main() -> int:
    failures: list[str] = []
    read_model = build_fusion_routing_delegation_read_model().model_dump(mode="json")
    _check_read_model(read_model, failures)
    _check_repository_binding(failures)
    _check_documents(failures)

    if failures:
        print("FCC fusion routing/delegation verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("FCC fusion routing/delegation verification passed.")
    return 0


def _check_read_model(read_model: dict[str, object], failures: list[str]) -> None:
    if read_model.get("contract_ref") != FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF:
        failures.append("read model contract ref is missing or wrong")
    if read_model.get("backend_owned") is not True:
        failures.append("read model must be backend-owned")
    if read_model.get("safe_refs_only") is not True:
        failures.append("read model must be safe-ref-only")
    if read_model.get("raw_content_included") is not False:
        failures.append("read model must not include raw content")
    for flag in (
        "action_execution_enabled",
        "sidekick_execution_enabled",
        "provider_model_call_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "connector_write_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "background_dispatch_enabled",
        "production_authority_enabled",
    ):
        if read_model.get(flag) is not False:
            failures.append(f"{flag} must remain false")
    blocked = set(read_model.get("blocked_state_refs") or [])
    missing = set(FCC_FUSION_ROUTING_REQUIRED_BLOCKED_REFS) - blocked
    if missing:
        failures.append("read model missing required blocked refs")


def _check_repository_binding(failures: list[str]) -> None:
    with TemporaryDirectory(prefix="uaa-fusion-routing-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir))
        today = repo.today_summary()
        actions = repo.actions_inbox()

    if today.get("fusion_routing_delegation_contract_ref") != (
        FCC_FUSION_ROUTING_DELEGATION_CONTRACT_REF
    ):
        failures.append("Today summary missing fusion contract ref")
    fusion = today.get("fusion_routing_delegation_read_model")
    if not isinstance(fusion, dict) or fusion.get("backend_owned") is not True:
        failures.append("Today summary missing backend-owned fusion read model")
    if not actions.get("items"):
        failures.append("Action Inbox has no items to inspect")
    else:
        first = actions["items"][0]
        if "work_classification" not in first:
            failures.append("Action Inbox item missing work classification")
        if "delegation_proposal" not in first:
            failures.append("Action Inbox item missing delegation proposal")
        if "cache_context_economics" not in first:
            failures.append("Action Inbox item missing cache/context economics")
    timeline = today.get("evidence_timeline") or []
    if not any(
        item.get("item_kind") == "fusion_routing_delegation_read_model_ref"
        for item in timeline
        if isinstance(item, dict)
    ):
        failures.append("Evidence Timeline missing fusion visibility item")


def _check_documents(failures: list[str]) -> None:
    for path in DOC_PATHS:
        if not path.exists():
            failures.append(f"missing required artifact: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        findings = forbidden_fusion_claims(text)
        if findings:
            failures.append(
                f"{path.relative_to(ROOT)} contains forbidden fusion claim(s)"
            )


if __name__ == "__main__":
    raise SystemExit(main())
