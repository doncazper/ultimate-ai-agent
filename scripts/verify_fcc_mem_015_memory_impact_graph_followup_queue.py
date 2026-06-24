#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.memory import (  # noqa: E402
    MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF,
    MEMORY_IMPACT_GRAPH_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


REQUIRED_SNIPPETS: dict[str, list[str]] = {
    "docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md": [
        "GET /control-center/memory/impact-graph",
        "GET /control-center/memory/follow-ups",
        "GET /control-center/memory/recall-health",
        "proposal-only",
        "Context injection",
        "Semantic/vector search",
    ],
    "src/ultimate_ai_agent/core/memory/workbench.py": [
        "build_memory_impact_graph",
        "build_memory_follow_up_queue",
        "build_recall_health_v2",
        "MEMORY_IMPACT_GRAPH_BLOCKED_STATE_REFS",
    ],
    "src/ultimate_ai_agent/core/storage/founder_loop.py": [
        "def memory_impact_graph",
        "def memory_follow_up_queue",
        "def memory_recall_health_v2",
    ],
    "src/ultimate_ai_agent/api/founder_loop.py": [
        "/memory/impact-graph",
        "/memory/follow-ups",
        "/memory/recall-health",
    ],
    "scripts/dev/uaa_founder_loop.py": [
        "memory-impact-graph",
        "memory-follow-ups",
        "memory-recall-health",
    ],
    "apps/control-center/src/components/FounderLoopPanels.tsx": [
        "MemoryImpactGraphPanel",
        "MemoryMergeSupersedePanel",
        "MemoryFollowUpQueuePanel",
        "MemoryContextPackPreviewPanel",
    ],
    "apps/control-center/src/api/types.ts": [
        "FounderLoopMemoryImpactGraph",
        "FounderLoopMemoryFollowUpQueue",
        "FounderLoopRecallHealthV2",
    ],
    "tests/test_fcc_mem_015_memory_impact_graph_followup_queue.py": [
        "test_repository_memory_impact_graph_followups_and_health_are_safe",
        "test_control_center_memory_impact_graph_routes",
        "test_founder_loop_cli_memory_impact_graph_omits_raw_paths",
    ],
}

REQUIRED_CAPABILITIES = [
    "control_center_memory_impact_graph_read_model",
    "control_center_memory_follow_up_queue_proposals",
    "control_center_memory_recall_health_v2",
]

REQUIRED_BLOCKED_CAPABILITIES = [
    "control_center_memory_impact_graph_context_injection",
    "control_center_memory_impact_graph_action_execution",
    "control_center_memory_impact_graph_semantic_search",
    "control_center_memory_follow_up_queue_action_execution",
    "control_center_memory_follow_up_queue_memory_writes",
    "control_center_memory_recall_health_provider_model_calls",
]

ROUTE_EXPECTATIONS: dict[tuple[str, str], dict[str, Any]] = {
    ("GET", "/control-center/memory/impact-graph"): {
        "operation_id": "get_control_center_memory_impact_graph",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
    },
    ("GET", "/control-center/memory/follow-ups"): {
        "operation_id": "get_control_center_memory_follow_ups",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
    },
    ("GET", "/control-center/memory/recall-health"): {
        "operation_id": "get_control_center_memory_recall_health",
        "route_classification": "local_sensitive",
        "side_effect_class": "local_dev_workspace_only",
        "idempotency_required": False,
    },
}

DENIED_IMPACT_FLAGS = [
    "memory_truth_authority",
    "context_injection_authorized",
    "action_execution_authorized",
    "connector_write_authorized",
    "crm_sync_authorized",
    "semantic_search_enabled",
    "vector_db_enabled",
    "embedding_search_enabled",
    "model_provider_authority_allowed",
    "production_authority_enabled",
]

DENIED_FOLLOW_UP_FLAGS = [
    "action_execution_authorized",
    "connector_write_authorized",
    "memory_write_authorized",
    "context_injection_authorized",
    "production_authority_enabled",
]


def verify() -> list[str]:
    failures: list[str] = []
    _append_file_failures(failures)
    _append_manifest_failures(failures)
    _append_behavior_failures(failures)
    return failures


def _append_file_failures(failures: list[str]) -> None:
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        path = ROOT / rel_path
        if not path.exists():
            failures.append(f"missing FCC-MEM-015 file: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"{rel_path} missing {snippet!r}")


def _append_manifest_failures(failures: list[str]) -> None:
    manifest = build_api_manifest(app)
    declared = set(manifest.capabilities_declared)
    blocked = set(manifest.capabilities_blocked)
    for capability in REQUIRED_CAPABILITIES:
        if capability not in declared:
            failures.append(f"/api/manifest missing capability {capability}")
    for capability in REQUIRED_BLOCKED_CAPABILITIES:
        if capability not in blocked:
            failures.append(f"/api/manifest missing blocked capability {capability}")

    routes = {(route.method, route.path): route for route in manifest.routes}
    for key, expected in ROUTE_EXPECTATIONS.items():
        route = routes.get(key)
        if route is None:
            failures.append(f"missing route {key[0]} {key[1]}")
            continue
        payload = route.model_dump(mode="json")
        for field_name, expected_value in expected.items():
            if payload.get(field_name) != expected_value:
                failures.append(f"{key[0]} {key[1]} {field_name} drifted")


def _append_behavior_failures(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="uaa-fcc-mem-015-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        impact_graph = repo.memory_impact_graph(limit=10)
        follow_ups = repo.memory_follow_up_queue(limit=10)
        recall_health = repo.memory_recall_health_v2(limit=10)

    if impact_graph.get("contract_ref") != MEMORY_IMPACT_GRAPH_CONTRACT_REF:
        failures.append("memory impact graph contract ref drifted")
    if follow_ups.get("contract_ref") != MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF:
        failures.append("memory follow-up queue contract ref drifted")
    if impact_graph.get("safe_refs_only") is not True:
        failures.append("memory impact graph is not safe-ref-only")
    if follow_ups.get("proposal_only") is not True:
        failures.append("memory follow-up queue is not proposal-only")
    if recall_health.get("schema_version") != "fcc_mem_015_recall_health_v2.v1":
        failures.append("recall health v2 schema drifted")

    for flag in DENIED_IMPACT_FLAGS:
        if impact_graph.get(flag) is not False:
            failures.append(f"memory impact graph unsafe flag enabled: {flag}")
    for flag in DENIED_FOLLOW_UP_FLAGS:
        if follow_ups.get(flag) is not False:
            failures.append(f"memory follow-up queue unsafe flag enabled: {flag}")
    for candidate in follow_ups.get("candidates", []):
        if candidate.get("proposal_only") is not True:
            failures.append("memory follow-up candidate is not proposal-only")
        for flag in DENIED_FOLLOW_UP_FLAGS:
            if candidate.get(flag) is not False:
                failures.append(f"memory follow-up candidate unsafe flag: {flag}")


def main() -> int:
    failures = verify()
    if failures:
        print("FCC-MEM-015 verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("FCC-MEM-015 Memory Impact Graph and Follow-Up Queue verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
