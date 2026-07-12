from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF,
    MEMORY_IMPACT_GRAPH_CONTRACT_REF,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.memory.workbench import (
    build_memory_follow_up_queue,
    build_memory_impact_graph,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import memory_write_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def _accept_first_memory_candidate(repo: FounderLoopRepository) -> dict[str, object]:
    candidate_ref = str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )
    return repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:fcc-mem-015-test",
            source_refs=["source-ref:manual-note:fcc-mem-015"],
            evidence_refs=["evidence-ref:fcc-mem-015:test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-015-accept",
    )


def test_repository_memory_impact_graph_followups_and_health_are_safe(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accept_first_memory_candidate(repo)

    impact_graph = repo.memory_impact_graph(limit=10)
    follow_ups = dict(impact_graph["follow_up_queue"])
    recall_health = dict(impact_graph["health_v2"])

    assert impact_graph["schema_version"] == "fcc_mem_015_memory_impact_graph.v1"
    assert impact_graph["contract_ref"] == MEMORY_IMPACT_GRAPH_CONTRACT_REF
    assert impact_graph["route_ref"] == "GET /control-center/memory/impact-graph"
    assert impact_graph["safe_refs_only"] is True
    assert impact_graph["memory_truth_authority"] is False
    assert impact_graph["context_injection_authorized"] is False
    assert impact_graph["action_execution_authorized"] is False
    assert impact_graph["connector_write_authorized"] is False
    assert impact_graph["crm_sync_authorized"] is False
    assert impact_graph["semantic_search_enabled"] is False
    assert impact_graph["vector_db_enabled"] is False
    assert impact_graph["embedding_search_enabled"] is False
    assert impact_graph["model_provider_authority_allowed"] is False
    assert impact_graph["production_authority_enabled"] is False
    assert impact_graph["nodes"]

    first_node = impact_graph["nodes"][0]
    assert first_node["memory_ref"]
    assert first_node["review_ref"]
    assert first_node["what_this_affects_refs"]
    assert "surface-ref:today" in first_node["affected_surface_refs"]
    assert first_node["stayed_blocked_refs"]
    assert "blocked-state:memory-impact-graph-no-context-injection" in (
        first_node["blocked_state_refs"]
    )

    assert follow_ups["schema_version"] == "fcc_mem_015_memory_follow_up_queue.v1"
    assert follow_ups["contract_ref"] == MEMORY_FOLLOW_UP_QUEUE_CONTRACT_REF
    assert follow_ups["route_ref"] == "GET /control-center/memory/follow-ups"
    assert follow_ups["safe_refs_only"] is True
    assert follow_ups["proposal_only"] is True
    assert follow_ups["action_execution_authorized"] is False
    assert follow_ups["connector_write_authorized"] is False
    assert follow_ups["memory_write_authorized"] is False
    assert follow_ups["context_injection_authorized"] is False
    assert follow_ups["production_authority_enabled"] is False
    assert follow_ups["candidates"]
    assert all(candidate["proposal_only"] is True for candidate in follow_ups["candidates"])
    assert all(
        candidate["action_execution_authorized"] is False
        and candidate["memory_write_authorized"] is False
        for candidate in follow_ups["candidates"]
    )

    assert recall_health["schema_version"] == "fcc_mem_015_recall_health_v2.v1"
    assert recall_health["reviewed_recall_count"] >= 1
    assert recall_health["top_memory_refs_driving_current_loop"]
    assert recall_health["safe_refs_only"] is True
    assert recall_health["semantic_search_enabled"] is False
    assert recall_health["vector_db_enabled"] is False
    assert recall_health["model_provider_authority_allowed"] is False
    assert recall_health["production_authority_enabled"] is False

    serialized = json.dumps(impact_graph).lower()
    assert "raw_prompt" not in serialized
    assert "raw_response" not in serialized
    assert "provider_payload" not in serialized


def test_control_center_memory_impact_graph_routes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "api_state"))
    client = TestClient(app)

    for path, operation in [
        ("/control-center/memory/impact-graph", "control_center_memory_impact_graph"),
        ("/control-center/memory/follow-ups", "control_center_memory_follow_ups"),
        (
            "/control-center/memory/recall-health",
            "control_center_memory_recall_health",
        ),
    ]:
        response = client.get(path)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert "safe_refs_only" in body["redactions_applied"]
        assert body["data"]["safe_refs_only"] is True


def test_founder_loop_cli_memory_impact_graph_omits_raw_paths(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "cli_state"
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "memory-impact-graph",
            "--limit",
            "5",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    output = json.loads(result.stdout)
    assert output["command_ref"] == "repo-local-command:founder-loop-memory-impact-graph"
    assert output["safe_refs_only"] is True
    assert output["raw_paths_omitted"] is True
    assert output["impact_graph"]["schema_version"] == (
        "fcc_mem_015_memory_impact_graph.v1"
    )
    assert str(state_dir) not in result.stdout


def test_memory_impact_graph_rejects_unsafe_context_pack_refs() -> None:
    with pytest.raises(ValueError, match="context_pack_ref"):
        build_memory_impact_graph(
            workbench={"items": [], "decision_receipts": []},
            today_summary={},
            actions_inbox={},
            morning_briefing={},
            evidence_timeline={},
            context_packs={
                "proposals": [
                    {
                        "context_pack_ref": "/Users/example/private-context.md",
                        "proposal_ref": "context-pack-proposal-ref:test",
                    }
                ]
            },
        )


def test_memory_follow_up_queue_rejects_unsafe_direct_action_refs() -> None:
    with pytest.raises(ValueError, match="action_proposal_ref"):
        build_memory_follow_up_queue(
            impact_graph_nodes=[
                {
                    "memory_ref": "memory-ref:fcc-mem-015:test",
                    "review_ref": "memory-review:fcc-mem-015:test",
                    "action_proposal_refs": ["/Users/example/private-action"],
                    "relationship_refs": [],
                    "commitment_refs": [],
                    "promise_refs": [],
                    "stale_state_refs": [],
                    "quality_state_refs": [],
                    "what_this_affects_refs": [],
                    "why_shown_refs": [],
                }
            ],
            workbench={"decision_receipts": []},
        )
