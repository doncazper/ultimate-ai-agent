#!/usr/bin/env python3
"""Verify Queue 01 item 06 without activating browser action or network access."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str, failures: list[str]) -> str:
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except OSError:
        failures.append(f"missing Queue 01 group 04 artifact: {relative}")
        return ""


def verify() -> list[str]:
    failures: list[str] = []
    actions = _read(
        "src/ultimate_ai_agent/core/governed_browser/browser_actions.py",
        failures,
    )
    broker = _read(
        "src/ultimate_ai_agent/core/governed_browser/broker.py",
        failures,
    )
    contracts = _read(
        "src/ultimate_ai_agent/core/governed_browser/contracts.py",
        failures,
    )
    package = _read(
        "src/ultimate_ai_agent/core/governed_browser/__init__.py",
        failures,
    )
    tests = _read("tests/test_governed_browser_queue01_group04.py", failures)
    doc = _read("docs/browser/GOVERNED_EXTERNAL_ACTIONS_QUEUE_01.md", failures)
    docs_index = _read("docs/DOCUMENTATION_INDEX.md", failures)
    board = _read("docs/kanban/current_board.md", failures)
    truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", failures)

    required_by_file = {
        "actions": (
            "GovernedBrowserActionRecipe",
            "GovernedBrowserActionRecipeRegistry",
            "GovernedBrowserActionKind",
            "ExactBrowserActionService",
            "visible_target_required: Literal[True]",
            "same_origin_required: Literal[True]",
            'method: Literal["GET"]',
            "request_body_allowed: Literal[False]",
            "browser_session_allowed: Literal[False]",
            "action_execution_allowed: Literal[False]",
            "live_network_allowed: Literal[False]",
            "real_external_targets_enabled: Literal[False]",
            "automatic_retry_allowed: Literal[False]",
            "WebAccessGateway",
            "GovernedExternalActionKernel",
        ),
        "broker": (
            "IsolatedBrowserActionDryRunBrokerAdapter",
            "LOCAL_BROWSER_ACTION_DRY_RUN",
            "TemporaryDirectory",
            "GOVERNED_BROWSER_ACTION_EXECUTION_INACTIVE",
            "GOVERNED_BROWSER_ACTION_CONTENT_BEARING_OUTPUT_DENIED",
            "self.external_mutation_enabled = False",
        ),
        "contracts": (
            "authority_capability: AuthorityCapability",
            "capability=AuthorityCapability(binding.authority_capability)",
        ),
        "package": (
            "GovernedBrowserActionRecipe",
            "ExactBrowserActionService",
            "build_governed_browser_action_recipe",
            "create_isolated_browser_action_dry_run_gateway",
        ),
        "tests": (
            "test_registered_same_origin_visible_action_is_governed_and_inactive",
            "test_unknown_recipe_is_blocked_before_authority_or_gateway",
            "test_approval_identifier_alone_grants_nothing",
            "test_revalidation_denies_before_action_plan",
            "test_action_plan_is_at_most_once_and_replay_is_content_free",
            "test_settlement_failure_suppresses_plan_and_forbids_retry",
            "test_hidden_cross_origin_or_executed_transport_output_fails_content_free",
            "test_real_external_target_cannot_create_an_action_recipe",
        ),
        "doc": (
            "06. Same-origin visible clicks and GET forms",
            "`implemented_inactive`",
            "injected action plan",
            "no browser session",
            "Queue 02",
        ),
    }
    values = {
        "actions": actions,
        "broker": broker,
        "contracts": contracts,
        "package": package,
        "tests": tests,
        "doc": doc,
    }
    for label, markers in required_by_file.items():
        for marker in markers:
            if marker not in values[label]:
                failures.append(f"Queue 01 group 04 {label} marker missing: {marker}")

    for marker, text, label in (
        ("Queue 01 items 01–06", docs_index, "documentation index"),
        ("Queue 01 items 01–06", board, "current board"),
        ("Queue 01 items 01–06", truth, "release truth"),
    ):
        if marker not in text:
            failures.append(f"Queue 01 group 04 {label} marker missing: {marker}")

    runtime_text = "\n".join((actions, broker, contracts, package)).lower()
    for fragment in (
        "import requests",
        "import httpx",
        "import playwright",
        "import selenium",
        "import browserbase",
        "import firecrawl",
        "subprocess.",
    ):
        if fragment in runtime_text:
            failures.append(f"Queue 01 group 04 forbidden runtime import: {fragment}")
    for fragment in ("/Users/", "file://", "Bearer ey", "access_token"):
        if fragment in doc:
            failures.append(
                f"Queue 01 group 04 doc contains forbidden data: {fragment}"
            )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Governed Browser Queue 01 group 04 verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Governed Browser Queue 01 group 04 verification PASSED")
    print(
        json.dumps(
            {
                "queue_items": [6],
                "classification": "implemented_inactive",
                "action_mode": "injected_plan_only",
                "browser_session_enabled": False,
                "live_network_enabled": False,
                "real_external_targets_enabled": False,
                "automatic_retry_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
