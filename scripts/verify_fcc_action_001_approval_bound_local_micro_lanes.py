#!/usr/bin/env python3
"""Validate FCC-ACTION-001 approval-bound local authority capability truth."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-ACTION-001"
DOC = ROOT / "docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md"
MATURITY_MANIFEST = ROOT / "docs/control_center/operational_maturity_manifest.json"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
LOCAL_TASKS = ROOT / "src/ultimate_ai_agent/core/control_center/local_tasks.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_ROUTE = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FOCUSED_TEST = ROOT / "tests/test_fcc_action_001_approval_bound_local_micro_lanes.py"

DOC_REF = "docs/control_center/FCC_ACTION_001_APPROVAL_BOUND_LOCAL_MICRO_LANES.md"
VERIFIER_REF = "scripts/verify_fcc_action_001_approval_bound_local_micro_lanes.py"
TEST_REF = "tests/test_fcc_action_001_approval_bound_local_micro_lanes.py"
LOCAL_TASK_KIND = "local_task_create"
LOCAL_TASK_AUTHORITY_CAPABILITY_ID = (
    "authority-capability:action-inbox:local-task-create"
)
LOCAL_TASK_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
LOCAL_TASK_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
LOCAL_TASK_AUTHORITY_MODE_REF = "authority-mode-ref:ask-before-changes"
LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF = (
    "authority-lease-requirement-ref:local-task-commit:workspace:write"
)
LOCAL_TASK_ROUTE = "POST /control-center/actions/{action_id}/local-task/commit"
LOCAL_TASK_CLI = "scripts/dev/uaa_founder_loop.py commit-local-task"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing FCC-ACTION-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented for the existing `local_task_create` AuthorityLease-gated local capability",
            LOCAL_TASK_ROUTE,
            LOCAL_TASK_CLI,
            "only current rank 5 Action Inbox local write authority capability",
            "AuthorityLease",
            "FCC-ACTION-002",
            "rollback_execution` blocked",
            "Action Inbox module: rank 3 overall",
            "no generic action execution",
            "no connector writes",
            "no shell/subprocess execution",
            "no provider/model authority",
            "no production authority",
            VERIFIER_REF,
            TEST_REF,
        ],
        failures,
    )


def _validate_manifest(root: Path, failures: list[str]) -> None:
    text = _read_text(root, MATURITY_MANIFEST, failures)
    if not text:
        return
    manifest = json.loads(text)
    action_module = next(
        (
            module
            for module in manifest.get("modules", [])
            if module.get("module_id") == "action_inbox"
        ),
        None,
    )
    if not action_module:
        failures.append("operational maturity manifest missing action_inbox module")
        return
    capabilities = action_module.get("authority_capabilities", [])
    rank5_capabilities = [
        capability for capability in capabilities if capability.get("rank") == 5
    ]
    if [capability.get("capability_id") for capability in rank5_capabilities] != [
        LOCAL_TASK_AUTHORITY_CAPABILITY_ID
    ]:
        failures.append(
            "local_task_create must be the only rank 5 Action Inbox authority capability"
        )
    capability = rank5_capabilities[0] if rank5_capabilities else {}
    expected_fragments = [
        ("rank", 5),
        ("capability_id", LOCAL_TASK_AUTHORITY_CAPABILITY_ID),
        ("legacy_lane_id", LOCAL_TASK_KIND),
        ("authority_domain_ref", LOCAL_TASK_AUTHORITY_DOMAIN_REF),
        ("authority_capability_ref", LOCAL_TASK_AUTHORITY_CAPABILITY_REF),
        ("required_mode_ref", LOCAL_TASK_AUTHORITY_MODE_REF),
        ("authority_lease_requirement_ref", LOCAL_TASK_AUTHORITY_LEASE_REQUIREMENT_REF),
        ("active_lease_required", True),
        ("exact_approval_required", True),
        ("idempotency_required", True),
        ("receipts_required", True),
        ("audit_required", True),
        ("redaction_required", True),
        ("repeatability_gate_ref", "FCC-ACTION-002"),
        ("cli_parity_ref", LOCAL_TASK_CLI),
    ]
    for key, expected in expected_fragments:
        if capability.get(key) != expected:
            failures.append(
                "local_task_create authority capability "
                f"{key} drifted from {expected!r}"
            )
    required_lists = {
        "backend_routes": [LOCAL_TASK_ROUTE],
        "rollback_or_safe_disable_refs": [
            "rollback-not-applicable:local-task-safe-disable",
            "safe-disable:founder-loop:local-task-create-scorecard",
        ],
        "blocked_authorities": [
            "rollback_execution",
            "connector_write",
            "shell_subprocess_execution",
            "model_provider_authority",
            "memory_write",
            "context_injection",
            "external_side_effect",
            "production_authority",
        ],
        "focused_test_refs": [
            "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_requires_exact_approval_and_records_evidence",
            "tests/test_founder_loop_storage_actions.py::test_action_inbox_local_task_commit_denies_when_safe_disabled",
            "tests/test_control_center_api_routes.py::test_control_center_action_local_task_commit_requires_exact_approval_and_receipts",
        ],
    }
    for key, expected_values in required_lists.items():
        actual = set(capability.get(key, []))
        for expected in expected_values:
            if expected not in actual:
                failures.append(
                    "local_task_create authority capability missing "
                    f"{expected} in {key}"
                )


def _validate_code_and_tests(root: Path, failures: list[str]) -> None:
    requirements = {
        LOCAL_TASKS: [
            "FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND = \"local_task_create\"",
            "FOUNDER_LOOP_LOCAL_TASK_COMMIT_ROUTE_REF",
            "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF",
            "FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF",
            "FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF",
            "connector_write_performed: bool = False",
            "shell_subprocess_execution_performed: bool = False",
            "model_provider_authority_used: bool = False",
            "memory_write_performed: bool = False",
            "context_injection_performed: bool = False",
            "external_side_effect_performed: bool = False",
            "rollback_execution_enabled: bool = False",
        ],
        STORAGE: [
            "def commit_local_task(",
            "FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND",
            "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF",
            "FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF",
            "local_task_created",
        ],
        API_ROUTE: [
            '@router.post("/actions/{action_id}/local-task/commit"',
            "control_center_action_local_task_commit",
            "commit_local_task(",
            "evidence-ref:founder-loop:local-task-commit",
        ],
        CLI: [
            "commit-local-task",
            "Commit an approved local_task_create Action Inbox item",
        ],
        FOCUSED_TEST: [
            "test_local_task_create_is_only_rank5_action_authority_capability",
            "test_local_task_commit_receipt_denies_broader_authority",
            "test_fcc_action_001_verifier_passes_current_repo",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-ACTION-001 Approval-Bound Local Authority Capability",
            DOC_REF,
            "FCC-POLISH-001 Native And Apple-Grade UX Layer",
        ],
        FCC_BOARD: [
            "FCC-ACTION-001",
            "Approval-bound Local Authority Capability",
            DOC_REF,
            "local_task_create",
        ],
        PRODUCT_TRUTH: [
            "FCC-ACTION-001",
            DOC_REF,
            "local_task_create",
            "only rank 5 Action Inbox local write authority capability",
            "no generic action execution",
            "no connector writes",
            "no shell/subprocess execution",
            "no production authority",
        ],
        GAP_MAP: [
            "Action Inbox `local_task_create` remains the only rank 5 local write authority capability",
            "FCC-ACTION-002",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_action_001_approval_bound_local_micro_lanes(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_manifest(root, failures)
    _validate_code_and_tests(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate FCC-ACTION-001 approval-bound local authority capability."
        )
    )
    parser.parse_args(argv)
    failures = validate_fcc_action_001_approval_bound_local_micro_lanes()
    if failures:
        print(f"{TASK_REF} verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"{TASK_REF} verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
