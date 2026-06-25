#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.core.memory import (  # noqa: E402
    MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "FCC-MEM-001 Memory Workbench verification passed."
DOC_PATH = "docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md"
BASELINE_AUDIT_PATH = "docs/control_center/FCC_MEM_001_MEMORY_BASELINE_AUDIT.md"
ROADMAP_PATH = "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md"
TRUTH_PACKET_PATH = "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
CURRENT_BOARD_PATH = "docs/kanban/current_board.md"
FCC_BOARD_PATH = "docs/kanban/founder_command_center_board.md"
DOC_INDEX_PATH = "docs/DOCUMENTATION_INDEX.md"
DOCS_README_PATH = "docs/README.md"
PROMPT_README_PATH = "docs/prompts/README.md"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
FRONTEND_PANEL_PATH = "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_CLIENT_PATH = "apps/control-center/src/api/client.ts"
FRONTEND_TEST_PATH = "apps/control-center/src/App.test.tsx"
CLI_PATH = "scripts/dev/uaa_founder_loop.py"
LIFECYCLE_CLI_PATH = "scripts/inspect_memory_merge_supersede_posture.py"
TEST_PATH = "tests/test_fcc_mem_001_memory_workbench.py"

ROUTE_EXPECTATIONS: dict[tuple[str, str], dict[str, Any]] = {
    ("GET", "/control-center/memory/workbench"): {
        "operation_id": "get_control_center_memory_workbench",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    },
    ("GET", "/control-center/memory/search"): {
        "operation_id": "get_control_center_memory_search",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
        "rate_limit_group": None,
    },
    ("POST", "/control-center/memory/review/manual-candidate"): {
        "operation_id": "post_control_center_memory_review_manual_candidate",
        "route_classification": "mutating_requires_authority",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": True,
        "rate_limit_group": "memory_review_decision",
    },
}

DECISION_ROUTES = {
    "/control-center/memory/review/{candidate_ref}/accept",
    "/control-center/memory/review/{candidate_ref}/correct",
    "/control-center/memory/review/{candidate_ref}/reject",
    "/control-center/memory/review/{candidate_ref}/defer",
    "/control-center/memory/review/{candidate_ref}/merge",
    "/control-center/memory/review/{candidate_ref}/supersede",
    "/control-center/memory/review/{candidate_ref}/forget-request",
}

REQUIRED_DOC_SNIPPETS = {
    DOC_PATH: [
        "Status: implemented local functional memory workbench slice",
        "GET /control-center/memory/workbench",
        "GET /control-center/memory/search",
        "POST /control-center/memory/review/manual-candidate",
        "accept`, `correct`, `reject`, `defer`, `merge`, `supersede`, and `forget_request",
        "`lifecycle_posture` adds the Product Loop 002 merge/supersede/forget posture",
        "scripts/inspect_memory_merge_supersede_posture.py",
        "No memory delete execution",
        "No semantic search, vector DB, embeddings, or provider/model extraction",
        "scripts/verify_fcc_mem_001_memory_workbench.py",
    ],
    BASELINE_AUDIT_PATH: [
        "backend-owned Memory Review now has a FCC-MEM-001 workbench read model",
        "Memory remains governed recall, not truth or authority",
    ],
    ROADMAP_PATH: [
        "FCC-MEM-001",
        "Memory Workbench V1",
        "no delete/export execution",
    ],
    TRUTH_PACKET_PATH: [
        "FCC-MEM-001 extends Memory Review",
        "delete/export memory",
        "semantic-search",
    ],
    DOCS_README_PATH: ["Memory Workbench V1"],
    DOC_INDEX_PATH: ["FCC-MEM-001"],
    CURRENT_BOARD_PATH: ["FCC-MEM-001 Memory Workbench V1"],
    FCC_BOARD_PATH: ["FCC-MEM-001` Memory Workbench V1"],
    PROMPT_README_PATH: ["fcc_memory_module_sequence"],
}

FORBIDDEN_CLAIMS = [
    "memory workbench is production ready",
    "memory workbench grants production authority",
    "memory delete execution is implemented",
    "memory export execution is implemented",
    "semantic search is implemented",
    "vector db is implemented",
    "context injection is authorized",
    "connector writes are enabled",
    "public beta ready",
]


def verify(
    root: Path = ROOT,
    *,
    context: ApiVerifierContext | None = None,
    check_files: bool = True,
    check_behavior: bool = True,
) -> list[str]:
    failures: list[str] = []
    context = context or default_api_verifier_context()
    if check_files:
        _append_required_file_failures(failures, root)
    _append_manifest_failures(failures, context)
    _append_behavior_failures(failures, root, check_behavior=check_behavior)
    if check_files:
        append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
        append_forbidden_claims(
            failures,
            [
                DOC_PATH,
                BASELINE_AUDIT_PATH,
                ROADMAP_PATH,
                TRUTH_PACKET_PATH,
                CURRENT_BOARD_PATH,
                FCC_BOARD_PATH,
                FRONTEND_PANEL_PATH,
            ],
            FORBIDDEN_CLAIMS,
        )
        _append_static_fragment_failures(failures)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        DOC_PATH,
        BASELINE_AUDIT_PATH,
        ROADMAP_PATH,
        ROUTE_STATUS_PATH,
        RELEASE_SURFACE_PATH,
        FRONTEND_PANEL_PATH,
        FRONTEND_CLIENT_PATH,
        FRONTEND_TEST_PATH,
        CLI_PATH,
        LIFECYCLE_CLI_PATH,
        TEST_PATH,
        "docs/prompts/fcc_memory_module_sequence/README.md",
        "docs/prompts/fcc_memory_module_sequence/14_memory_tests_verifiers_docs.prompt.md",
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-MEM-001 file: {rel_path}")


def _append_manifest_failures(
    failures: list[str],
    context: ApiVerifierContext,
) -> None:
    manifest = context.manifest
    for capability in [
        "control_center_memory_workbench_read_model",
        "control_center_memory_search_filters",
        "control_center_manual_memory_candidate_intake",
    ]:
        if capability not in manifest.get("capabilities_declared", []):
            failures.append(f"/api/manifest missing capability {capability}")
    for blocked in [
        "control_center_manual_memory_candidate_as_recall_record",
        "control_center_manual_memory_candidate_delete_or_export_execution",
        "control_center_memory_workbench_ui_only_truth",
        "control_center_memory_search_embeddings",
        "control_center_memory_search_vector_db",
        "control_center_memory_search_semantic_search",
        "control_center_memory_search_context_injection",
    ]:
        if blocked not in manifest.get("capabilities_blocked", []):
            failures.append(f"/api/manifest missing blocked capability {blocked}")
    for key, expected in ROUTE_EXPECTATIONS.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing FCC-MEM-001 route: {key[0]} {key[1]}")
            continue
        for field_name, expected_value in expected.items():
            if route.get(field_name) != expected_value:
                failures.append(f"{key[0]} {key[1]} {field_name} drifted")
    for route_path in DECISION_ROUTES:
        route = context.routes_by_key.get(("POST", route_path))
        if route is None:
            failures.append(f"missing Memory Review lifecycle route: POST {route_path}")
            continue
        if route.get("idempotency_required") is not True:
            failures.append(f"POST {route_path} missing idempotency requirement")
        if route.get("rate_limit_group") != "memory_review_decision":
            failures.append(f"POST {route_path} rate-limit group drifted")


def _append_behavior_failures(
    failures: list[str],
    root: Path,
    *,
    check_behavior: bool,
) -> None:
    if not check_behavior:
        return
    with tempfile.TemporaryDirectory(prefix="uaa-fcc-mem-001-") as tmp_dir:
        repo = FounderLoopRepository(Path(tmp_dir) / "founder_loop")
        workbench = repo.memory_workbench(limit=5)
    if workbench.get("schema_version") != "fcc_mem_001_memory_workbench.v1":
        failures.append("memory workbench schema_version drifted")
    for flag in [
        "semantic_search_enabled",
        "vector_db_enabled",
        "embedding_search_enabled",
        "context_injection_authorized",
        "memory_truth_authority",
        "production_authority_enabled",
    ]:
        if workbench.get(flag) is not False:
            failures.append(f"memory workbench unsafe flag enabled: {flag}")
    group_ids = {group.get("group_id") for group in workbench.get("groups", [])}
    for group_id in [
        "needs_review",
        "conflict",
        "duplicate",
        "stale",
        "missing_evidence",
        "reviewed",
        "rejected",
    ]:
        if group_id not in group_ids:
            failures.append(f"memory workbench missing group {group_id}")
    lifecycle_posture = workbench.get("lifecycle_posture") or {}
    if lifecycle_posture.get("contract_ref") != MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF:
        failures.append("memory lifecycle posture contract_ref drifted")
    for flag in [
        "hard_delete_authorized",
        "memory_export_authorized",
        "automatic_merge_authorized",
        "automatic_supersede_authorized",
        "automatic_forget_authorized",
        "hidden_memory_write_authorized",
        "context_injection_authorized",
        "connector_write_authorized",
        "model_provider_call_authorized",
        "production_authority_enabled",
    ]:
        if lifecycle_posture.get(flag) is not False:
            failures.append(f"memory lifecycle posture unsafe flag enabled: {flag}")
    lane_ids = {lane.get("lane_id") for lane in lifecycle_posture.get("lanes", [])}
    for lane_id in [
        "duplicate_review",
        "stale_review",
        "conflict_review",
        "corrected",
        "merged",
        "superseded",
        "forget_requested",
    ]:
        if lane_id not in lane_ids:
            failures.append(f"memory lifecycle posture missing lane {lane_id}")
    for item in workbench.get("items", []):
        if "available_lifecycle_decisions" not in item:
            failures.append("memory workbench item missing lifecycle decisions")
            break
        for flag in [
            "hard_delete_authorized",
            "automatic_merge_authorized",
            "automatic_supersede_authorized",
            "automatic_forget_authorized",
            "hidden_memory_write_authorized",
        ]:
            if item.get(flag) is not False:
                failures.append(f"memory workbench item unsafe flag enabled: {flag}")
                break


def _append_static_fragment_failures(failures: list[str]) -> None:
    frontend_panel = read_text(FRONTEND_PANEL_PATH)
    frontend_client = read_text(FRONTEND_CLIENT_PATH)
    frontend_tests = read_text(FRONTEND_TEST_PATH)
    cli_text = read_text(CLI_PATH)
    lifecycle_cli_text = read_text(LIFECYCLE_CLI_PATH)
    tests = read_text(TEST_PATH)
    for fragment in [
        "MemoryWorkbenchHealthPanel",
        "MemoryLifecyclePosturePanel",
        "MemoryWorkbenchItemCard",
        "reviewLifecycleAvailable = item.source === \"memory_review_queue\"",
        "available_lifecycle_decisions ?? []",
        "memoryDecisionReceiptLabel",
        "Approval scope ref",
    ]:
        if fragment not in frontend_panel:
            failures.append(f"Control Center memory workbench missing {fragment}")
    for fragment in [
        "safeHashSuffix(`${request.title}|${request.safe_summary}`)",
        "normalizeFounderMemoryWorkbench",
        "delete workbenchWithoutMockPosture.lifecycle_posture",
    ]:
        if fragment not in frontend_client:
            failures.append(f"Control Center memory client missing {fragment}")
    for command in [
        "memory-workbench",
        "memory-search",
        "memory-receipts",
        "record-memory-decision",
        "memory-manual-candidate",
    ]:
        if command not in cli_text:
            failures.append(f"Founder Loop CLI missing {command}")
    for fragment in [
        "repo-local-command:inspect-memory-merge-supersede-posture",
        "state_not_found_no_write",
        "existing_state_unreadable_redacted",
        "raw_paths_omitted",
    ]:
        if fragment not in lifecycle_cli_text:
            failures.append(f"lifecycle CLI inspection missing {fragment}")
    for test_fragment in [
        "test_memory_workbench_read_model_groups_and_blocks_authority",
        "test_merge_and_supersede_mark_local_peer_posture_without_deletion",
        "test_memory_merge_supersede_cli_inspection_is_read_only_and_redacted",
        "test_memory_cli_rejects_unsafe_inputs_without_traceback",
    ]:
        if test_fragment not in tests:
            failures.append(f"FCC-MEM-001 tests missing {test_fragment}")
    if "does not backfill lifecycle posture or decisions from mocks" not in frontend_tests:
        failures.append("Control Center tests missing lifecycle fallback regression")


def main() -> int:
    return print_failures_or_success(
        failures=verify(),
        success_message=SUCCESS_MESSAGE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
