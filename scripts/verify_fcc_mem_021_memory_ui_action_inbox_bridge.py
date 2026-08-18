#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.repo import (  # noqa: E402
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.health_recommendations import (  # noqa: E402
    FCC_HEALTH_RECOMMENDATION_ACTION_KIND,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "FCC-MEM-021 verification passed."
SPEC_DOC = (
    "docs/control_center/"
    "FCC_MEM_021_MEMORY_READ_MODELS_UI_ACTION_INBOX_BRIDGE.md"
)
PROMPT_DOC = (
    "docs/prompts/fcc_memory_module_sequence/"
    "21_fcc_mem_021_memory_read_models_ui_action_inbox_bridge.prompt.md"
)
REQUIRED_FILES = [
    SPEC_DOC,
    PROMPT_DOC,
    "apps/control-center/src/api/client.ts",
    "apps/control-center/src/api/endpoints.ts",
    "apps/control-center/src/api/types.ts",
    "apps/control-center/src/components/FounderLoopPanels.tsx",
    "apps/control-center/src/mocks/controlCenterData.ts",
    "apps/control-center/src/routes.tsx",
    "apps/control-center/src/App.test.tsx",
    "src/ultimate_ai_agent/core/control_center/health_recommendations.py",
    "src/ultimate_ai_agent/core/storage/founder_loop.py",
    "tests/test_fcc_mem_021_memory_ui_action_inbox_bridge.py",
]
MEMORY_READ_ENDPOINTS = [
    ("founderMemoryRetrievalDiagnostics", "/control-center/memory/retrieval-diagnostics"),
    ("founderMemoryCitationIntegrity", "/control-center/memory/citation-integrity"),
    ("founderMemoryQualityIssues", "/control-center/memory/quality-issues"),
    ("founderMemoryMaintenanceRuns", "/control-center/memory/maintenance-runs"),
    ("founderMemoryContextManifest", "/control-center/memory/context-manifest"),
]
REQUIRED_SNIPPETS = {
    "apps/control-center/src/api/endpoints.ts": [
        "founderMemoryRetrievalDiagnostics",
        "founderMemoryCitationIntegrity",
        "founderMemoryQualityIssues",
        "founderMemoryFeedback",
        "founderMemoryMaintenanceRuns",
        "founderMemoryContextManifest",
        "/control-center/memory/feedback",
    ],
    "apps/control-center/src/api/client.ts": [
        "fetchFounderMemoryRetrievalDiagnostics",
        "fetchFounderMemoryCitationIntegrity",
        "fetchFounderMemoryQualityIssues",
        "fetchFounderMemoryMaintenanceRuns",
        "fetchFounderMemoryContextManifest",
        "recordMemoryFeedback",
        "memoryFeedbackIdempotencyRef",
        "founderMemoryRetrievalDiagnostics:",
        "founderMemoryContextManifest:",
    ],
    "apps/control-center/src/api/types.ts": [
        "FounderLoopMemoryRetrievalDiagnostics",
        "FounderLoopMemoryCitationIntegrity",
        "FounderLoopMemoryQualityIssues",
        "FounderLoopMemoryMaintenanceRuns",
        "FounderLoopMemoryContextManifest",
        "MemoryFeedbackRequest",
        "MemoryFeedbackReceipt",
        "health_recommendation_memory_write_authorized",
        "health_recommendation_context_injection_authorized",
    ],
    "apps/control-center/src/components/FounderLoopPanels.tsx": [
        "MemoryRetrievalDiagnosticsPanel",
        "MemoryCitationIntegrityPanel",
        "MemoryQualityIssuePanel",
        "MemoryMaintenanceRunPanel",
        "MemoryContextManifestPanel",
        "MemoryFeedbackControls",
        "HealthRecommendationItemDetails",
        "isMemoryRecommendationProposal",
        "recordMemoryFeedback",
        'decisions={["approve", "reject", "defer"]}',
        "Memory proposal receipt controls require the local backend Action Inbox",
    ],
    "apps/control-center/src/routes.tsx": [
        "retrievalDiagnostics={data.founderMemoryRetrievalDiagnostics}",
        "citationIntegrity={data.founderMemoryCitationIntegrity}",
        "qualityIssues={data.founderMemoryQualityIssues}",
        "maintenanceRuns={data.founderMemoryMaintenanceRuns}",
        "contextManifest={data.founderMemoryContextManifest}",
    ],
    "apps/control-center/src/mocks/controlCenterData.ts": [
        "founderMemoryRetrievalDiagnostics",
        "founderMemoryCitationIntegrity",
        "founderMemoryQualityIssues",
        "founderMemoryMaintenanceRuns",
        "founderMemoryContextManifest",
        "cache-key-ref:fcc-mem-016:mock-preferences",
        "memory-quality-issue:fcc-mem-018:mock-stale",
        "memory-maintenance-proposal:fcc-mem-019:mock-stale",
        "context-manifest-ref:fcc-mem-020:mock-preferences",
    ],
    "apps/control-center/src/App.test.tsx": [
        "records Memory quality feedback without memory writes or context injection",
        "renders memory self-heal recommendations as proposal-only Action Inbox items",
        "GET /control-center/memory/retrieval-diagnostics",
        "GET /control-center/memory/context-manifest",
        "idempotency-ref:control-center-memory-feedback",
    ],
    "src/ultimate_ai_agent/core/control_center/health_recommendations.py": [
        "memory_quality_issue",
        "docs/control_center/FCC_MEM_021_MEMORY_READ_MODELS_UI_ACTION_INBOX_BRIDGE.md",
        "scripts/verify_fcc_mem_021_memory_ui_action_inbox_bridge.py",
    ],
    "src/ultimate_ai_agent/core/storage/founder_loop.py": [
        "_memory_action_inbox_signal_refs",
        "memory-proposal-bridge-ref:fcc-mem-021-action-inbox",
        "health_recommendation_memory_write_authorized",
        "health_recommendation_context_injection_authorized",
    ],
    "tests/test_fcc_mem_021_memory_ui_action_inbox_bridge.py": [
        "test_fcc_mem_021_projects_memory_quality_into_action_inbox",
        "test_fcc_mem_021_memory_proposal_decision_receipt_does_not_mutate_memory",
        "test_fcc_mem_021_context_manifest_stays_preview_only",
    ],
    SPEC_DOC: [
        "FCC-MEM-021 Memory Read Models UI + Proposal Bridge",
        "retrieval diagnostics",
        "citation integrity",
        "quality issues",
        "proposal-only maintenance",
        "context manifest",
        "self_heal_recommendation",
        "no context injection",
        "no auto-maintenance",
    ],
    PROMPT_DOC: [
        "FCC-MEM-021 Memory Read Models UI + Proposal Bridge",
        "MEM-016",
        "MEM-020",
        "proposal-only",
        "no hidden context use",
    ],
}
FORBIDDEN_UI_SNIPPETS = [
    "Apply context manifest",
    "Use context manifest",
    "Inject context",
    "Run maintenance",
    "Execute maintenance",
    "Auto-merge memory",
    "Auto-forget memory",
    "Write memory now",
]
FORBIDDEN_TRUE_FLAGS = [
    "context_injection_authorized: true",
    "hidden_prompt_context_authorized: true",
    "automatic_context_injection_authorized: true",
    "memory_write_authorized: true",
    "automatic_memory_write_authorized: true",
    "auto_merge_authorized: true",
    "auto_forget_authorized: true",
    "action_execution_authorized: true",
    "production_authority_enabled: true",
]


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _append_required_file_failures(failures, root)
    append_missing_doc_snippets(failures, REQUIRED_SNIPPETS)
    _append_endpoint_failures(failures)
    _append_forbidden_frontend_failures(failures)
    _append_repository_contract_failures(failures)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in REQUIRED_FILES:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-MEM-021 file: {rel_path}")


def _append_endpoint_failures(failures: list[str]) -> None:
    endpoint_text = read_text("apps/control-center/src/api/endpoints.ts")
    for endpoint_name, endpoint in MEMORY_READ_ENDPOINTS:
        if endpoint not in endpoint_text:
            failures.append(f"missing MEM-021 endpoint string: {endpoint}")
        if f"API_ENDPOINTS.{endpoint_name}" not in endpoint_text:
            failures.append(f"missing MEM-021 endpoint constant use: {endpoint_name}")
    read_block = endpoint_text.split("export const READ_ENDPOINTS", 1)[-1]
    for endpoint_name, _endpoint in MEMORY_READ_ENDPOINTS:
        if f"API_ENDPOINTS.{endpoint_name}" not in read_block:
            failures.append(f"MEM-021 read endpoint not registered: {endpoint_name}")
    if "API_ENDPOINTS.founderMemoryFeedback" in read_block:
        failures.append("memory feedback POST route must not be a READ_ENDPOINT")


def _append_forbidden_frontend_failures(failures: list[str]) -> None:
    for rel_path in [
        "apps/control-center/src/components/FounderLoopPanels.tsx",
        "apps/control-center/src/mocks/controlCenterData.ts",
        "apps/control-center/src/App.test.tsx",
    ]:
        text = read_text(rel_path)
        for snippet in FORBIDDEN_UI_SNIPPETS:
            if snippet in text:
                failures.append(f"{rel_path} exposes forbidden MEM-021 UI control: {snippet}")
        compact = " ".join(text.split())
        for snippet in FORBIDDEN_TRUE_FLAGS:
            if snippet in compact:
                failures.append(f"{rel_path} enables forbidden MEM-021 flag: {snippet}")


def _append_repository_contract_failures(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="uaa-fcc-mem-021-") as tmp:
        repo = FounderLoopRepository(Path(tmp) / "state")
        try:
            item = _memory_recommendation_item(repo)
            _assert_memory_action_item(failures, item)
            before = repo.storage_status()["counts"]
            receipt = repo.record_action_decision(
                action_id=str(item["item_ref"]),
                decision="defer",
                request=FounderLoopActionDecisionRequest(
                    expected_revision_ref=str(item["action_revision_ref"]),
                    decision_reason_ref=(
                        "decision-reason-ref:fcc-mem-021-verifier-defer"
                    ),
                    defer_until_ref="defer-until-ref:fcc-mem-021-verifier",
                    metadata_refs=[
                        "metadata-ref:fcc-mem-021-verifier",
                        str(item["item_ref"]),
                    ],
                ),
                idempotency_key_ref="idempotency-ref:fcc-mem-021-verifier-defer",
            )
            after = repo.storage_status()["counts"]
            _assert_decision_receipt(failures, receipt, before, after)
            _assert_context_manifest(failures, repo.memory_context_manifest(limit=5))
            _assert_maintenance_runs(failures, repo.memory_maintenance_runs(limit=5))
        except Exception as exc:  # pragma: no cover - verifier failure reporting
            failures.append(f"repository contract smoke failed: {type(exc).__name__}: {exc}")


def _memory_recommendation_item(repo: FounderLoopRepository) -> dict[str, Any]:
    return next(
        item
        for item in repo.actions_inbox()["items"]
        if item.get("action_kind") == FCC_HEALTH_RECOMMENDATION_ACTION_KIND
        and item.get("health_recommendation_kind") == "memory_quality_issue"
    )


def _assert_memory_action_item(failures: list[str], item: dict[str, Any]) -> None:
    if item.get("action_group_id") != "proposal_only_no_execution_path":
        failures.append("memory recommendation is not in proposal-only Action Inbox lane")
    if item.get("approval_required") is not False:
        failures.append("memory recommendation should not require execution approval")
    for route_ref in [
        "GET /control-center/memory/quality-issues",
        "GET /control-center/memory/maintenance-runs",
        "GET /control-center/actions/inbox",
    ]:
        if route_ref not in item.get("health_recommendation_source_route_refs", []):
            failures.append(f"memory recommendation missing route ref: {route_ref}")
    if (
        "memory-proposal-bridge-ref:fcc-mem-021-action-inbox"
        not in item.get("health_recommendation_source_signal_refs", [])
    ):
        failures.append("memory recommendation missing MEM-021 bridge signal ref")
    for field in [
        "health_recommendation_auto_apply_authorized",
        "health_recommendation_auto_code_authorized",
        "health_recommendation_memory_write_authorized",
        "health_recommendation_context_injection_authorized",
        "health_recommendation_action_execution_authorized",
        "health_recommendation_production_authority_enabled",
    ]:
        if item.get(field) is not False:
            failures.append(f"memory recommendation authority flag drifted: {field}")
    serialized = json.dumps(item, sort_keys=True).lower()
    for unsafe in ["raw_prompt", "provider_payload", "secret", "credential"]:
        if unsafe in serialized:
            failures.append(f"memory recommendation serialized unsafe content: {unsafe}")


def _assert_decision_receipt(
    failures: list[str],
    receipt: dict[str, Any],
    before: dict[str, int],
    after: dict[str, int],
) -> None:
    if receipt.get("status") != "deferred":
        failures.append("memory proposal decision receipt did not defer")
    for field in [
        "action_executed",
        "memory_write_performed",
        "connector_write_performed",
        "raw_content_stored",
    ]:
        if receipt.get(field) is not False:
            failures.append(f"memory proposal decision performed forbidden work: {field}")
    if after.get("action_receipts") != before.get("action_receipts", 0) + 1:
        failures.append("memory proposal decision did not create exactly one action receipt")
    for count_name in [
        "memory_review_decisions",
        "memory_feedback_receipts",
        "local_tasks",
    ]:
        if after.get(count_name) != before.get(count_name):
            failures.append(f"memory proposal decision mutated {count_name}")


def _assert_context_manifest(failures: list[str], manifest: dict[str, Any]) -> None:
    if manifest.get("proposal_only") is not True:
        failures.append("context manifest must remain proposal-only")
    for field in [
        "context_injection_authorized",
        "hidden_prompt_context_authorized",
        "automatic_context_injection_authorized",
        "memory_write_authorized",
        "action_execution_authorized",
        "model_provider_authority_allowed",
    ]:
        if manifest.get(field) is not False:
            failures.append(f"context manifest authority flag drifted: {field}")


def _assert_maintenance_runs(failures: list[str], maintenance: dict[str, Any]) -> None:
    if maintenance.get("proposal_only") is not True:
        failures.append("maintenance runs must remain proposal-only")
    for field in [
        "auto_merge_authorized",
        "auto_forget_authorized",
        "automatic_memory_write_authorized",
        "memory_write_authorized",
        "action_execution_authorized",
    ]:
        if field in maintenance and maintenance.get(field) is not False:
            failures.append(f"maintenance run authority flag drifted: {field}")


def main() -> int:
    return print_failures_or_success(
        failures=verify(),
        success_message=SUCCESS_MESSAGE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
