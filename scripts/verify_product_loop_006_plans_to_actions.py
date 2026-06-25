#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/plans_to_actions.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
PLAN_ENVELOPES = ROOT / "src/ultimate_ai_agent/core/planning/action_envelopes.py"
CLI = ROOT / "scripts/inspect_plans_to_actions_bridge.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_006_PLANS_TO_ACTIONS.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
FOCUSED_TEST = ROOT / "tests/test_plans_to_actions_bridge.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for snippet in snippets:
        if snippet.lower() in text:
            failures.append(
                f"{path.relative_to(ROOT)} contains forbidden snippet {snippet!r}"
            )


def _validate_live_read_model(failures: list[str]) -> None:
    from ultimate_ai_agent.core.control_center.plans_to_actions import (
        PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF,
        PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS,
        PlansToActionsBridgeReadModel,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="product-loop-006-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()
        inbox = repo.actions_inbox()

    for surface, payload in {"today": today, "actions": inbox}.items():
        read_model = payload.get("plans_to_actions_bridge_read_model")
        if not isinstance(read_model, dict):
            failures.append(f"{surface} missing plans_to_actions_bridge_read_model")
            continue
        try:
            parsed = PlansToActionsBridgeReadModel(**read_model)
        except Exception as exc:
            failures.append(f"{surface} bridge model failed validation: {exc}")
            continue
        if parsed.contract_ref != PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF:
            failures.append(f"{surface} bridge contract ref drifted")
        if not parsed.items:
            failures.append(f"{surface} bridge has no items")
        if set(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS) - set(
            parsed.blocked_state_refs
        ):
            failures.append(f"{surface} bridge missing required blockers")
        if parsed.action_execution_enabled:
            failures.append(f"{surface} bridge enables action execution")
        if parsed.tool_execution_enabled or parsed.workflow_execution_enabled:
            failures.append(f"{surface} bridge enables tool/workflow execution")
        if parsed.provider_model_call_enabled:
            failures.append(f"{surface} bridge enables provider/model calls")
        if parsed.browser_execution_enabled or parsed.connector_runtime_enabled:
            failures.append(f"{surface} bridge enables browser/connector runtime")
        for item in parsed.items:
            if not item.expected_receipt_refs:
                failures.append(f"{surface} bridge item missing receipt refs")
            if not item.rollback_ref or not item.safe_disable_ref:
                failures.append(f"{surface} bridge item missing rollback/safe-disable")
            if item.action_execution_enabled or item.execution_authorized:
                failures.append(f"{surface} bridge item enables execution")
            if item.approval_alone_executes or item.approval_ref_authority:
                failures.append(f"{surface} bridge item treats approval as authority")


def main() -> int:
    failures: list[str] = []

    for path in [
        CONTRACT,
        STORAGE,
        PLAN_ENVELOPES,
        CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        DOC,
        BOARD,
        TRUTH_PACKET,
        INDEX,
        FOCUSED_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    forbidden_runtime_snippets = [
        "import subprocess",
        "subprocess.",
        "requests.",
        "httpx.",
        "urllib.request",
        "urllib3",
        "http.client",
        "playwright",
        "selenium",
        "firecrawl",
        "browserbase",
        "import provider_sdk",
        "provider_sdk.",
        "execute_action(",
        "execute_workflow(",
        "connector_write(",
        "connector_runtime(",
    ]
    for path in [CONTRACT, STORAGE, CLI, FRONTEND_CLIENT, FRONTEND_PANEL, DOC]:
        _require_absent(path, forbidden_runtime_snippets, failures)
    for path in [CONTRACT, STORAGE, CLI, FRONTEND_CLIENT, FRONTEND_PANEL]:
        _require_absent(
            path,
            [
                "raw_prompt_content",
                "raw_response_content",
                "provider_payload_content",
                "raw_local_path",
                "raw_log_content",
                "credential_value",
                "secret_value",
            ],
            failures,
        )

    _require(
        CONTRACT,
        [
            "PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF",
            "PlansToActionsBridgeReadModel",
            "PlansToActionsBridgeItem",
            "build_plans_to_actions_bridge_read_model",
            "blocked-state:plans-to-actions-no-tool-execution",
            "blocked-state:plans-to-actions-no-workflow-execution",
            "blocked-state:plans-to-actions-no-browser-execution",
            "blocked-state:plans-to-actions-no-connector-runtime",
            "approval_alone_executes: bool = False",
            "provider_model_call_enabled: bool = False",
        ],
        failures,
    )
    _require(
        PLAN_ENVELOPES,
        [
            "blocked-state:no-tool-execution",
            "blocked-state:no-workflow-execution",
            "blocked-state:no-browser-automation",
            "blocked-state:no-connector-runtime",
            "tool_execution_enabled: bool = False",
            "workflow_execution_enabled: bool = False",
            "browser_execution_enabled: bool = False",
            "connector_runtime_enabled: bool = False",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF",
            "build_plans_to_actions_bridge_read_model(",
            '"plans_to_actions_bridge_contract_ref"',
            '"plans_to_actions_bridge_read_model"',
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:inspect-plans-to-actions-bridge",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "raw_paths_omitted",
            '"action_execution_enabled": False',
            '"tool_execution_enabled": False',
            '"workflow_execution_enabled": False',
            '"provider_model_call_authorized": False',
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopPlansToActionsBridgeReadModel",
            "FounderLoopPlansToActionsBridgeItem",
            "plans_to_actions_bridge_contract_ref?: string",
            "plans_to_actions_bridge_read_model?: FounderLoopPlansToActionsBridgeReadModel",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafePlansToActionsBridgeReadModel",
            "python_core_plans_to_actions_bridge_read_model",
            "delete fallbackWithoutDigest.plans_to_actions_bridge_read_model",
            "delete normalized.plans_to_actions_bridge_read_model",
            "PLANS_TO_ACTIONS_BRIDGE_DENIED_FLAGS",
            "connector_runtime_enabled",
            "stripPlansActionEnvelopePosture",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "PlansToActionsBridgePanel",
            "Product Loop 006",
            "backend bridge missing",
            "Decision receipt options",
            "Expected receipts",
            "Rollback",
            "Safe disable",
            "Provider/browser/connector runtime",
            "approval refs remain identifiers",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
            "python_core_plans_to_actions_bridge_read_model",
            "backend bridge missing",
            "Plans to Actions",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1",
            "scripts/inspect_plans_to_actions_bridge.py",
            "Approval refs are identifiers",
            "proposal-only review metadata",
            "## Verification Lane",
            "tests/test_plans_to_actions_bridge.py",
            "tests/test_uaa_p1_073_plans_action_envelopes.py",
            "tests/test_uaa_p1_090_task_decomposition_proposal_engine.py",
            "scripts/verify_product_loop_006_plans_to_actions.py",
            "raw prompt content",
            "raw response content",
            "raw provider",
            "raw local path content",
            "raw log content",
            "account identifiers",
            "usernames",
            "hostnames",
            "credentials",
            "secrets",
            "no tool execution",
            "no provider/model calls",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "Product Loop 006 Plans To Reviewable Action Envelopes Upgrade",
            "`plans_to_actions_bridge_read_model`",
            "`scripts/inspect_plans_to_actions_bridge.py`",
            "proposal-only",
            "approval refs are identifiers",
            "decision receipts only",
            "no action execution",
            "no tool execution",
            "no workflow execution",
            "no provider/model calls",
            "no shell/browser execution",
            "no connector runtime",
            "no connector writes",
            "no memory writes",
            "no context injection",
            "no public beta",
            "no production authority",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "`plans_to_actions_bridge_read_model`",
            "scripts/inspect_plans_to_actions_bridge.py",
            "docs/control_center/PRODUCT_LOOP_006_PLANS_TO_ACTIONS.md",
            "plans proposal-only",
            "approval refs as decision-receipt identifiers only",
            "no action execution",
            "no tool execution",
            "no workflow execution",
            "no runtime model/provider calls",
            "no browser or shell execution",
            "no connector runtime",
            "no connector writes",
            "no hidden memory writes",
            "no context injection",
            "no public beta",
            "no production authority",
        ],
        failures,
    )
    _require(
        INDEX,
        ["docs/control_center/PRODUCT_LOOP_006_PLANS_TO_ACTIONS.md"],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_plans_to_actions_bridge_surfaces_from_today_and_actions",
            "test_today_bridge_uses_full_action_projection_when_display_limit_is_small",
            "test_plans_to_actions_bridge_marks_synthetic_fallback_refs_as_blocked",
            "test_plans_to_actions_bridge_rejects_authority_and_raw_content",
            "test_plans_to_actions_bridge_cli_is_read_only_and_redacted",
        ],
        failures,
    )

    panel_text = _read(FRONTEND_PANEL).lower()
    for forbidden in [
        "action execution enabled",
        "tool execution enabled",
        "workflow execution enabled",
        "provider calls enabled",
        "connector runtime enabled",
    ]:
        if forbidden in panel_text:
            failures.append(f"Control Center wording implies authority: {forbidden}")

    _validate_live_read_model(failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Product Loop 006 Plans-to-Actions verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
