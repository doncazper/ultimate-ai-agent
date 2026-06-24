from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_WORKBENCH_CONTRACT_REF,
    ManualMemoryCandidateRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:test-memory-reviewer",
        "source_refs": ["source-ref:manual-note:test"],
        "evidence_refs": ["evidence-ref:memory-review:test"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _manual_memory_candidate(repo: FounderLoopRepository, slug: str) -> dict[str, object]:
    return repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title=f"Manual {slug} candidate",
            safe_summary=f"A bounded safe {slug} summary for review only.",
            source_refs=[f"source-ref:manual-note:{slug}"],
            provenance_refs=[f"provenance-ref:manual-note:{slug}"],
            missing_evidence_refs=[f"missing-evidence-ref:manual-note:{slug}"],
        ),
        idempotency_key_ref=f"idempotency-ref:manual-memory-{slug}",
    )


def test_memory_workbench_read_model_groups_and_blocks_authority(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    workbench = repo.memory_workbench()

    assert workbench["schema_version"] == "fcc_mem_001_memory_workbench.v1"
    assert workbench["contract_ref"] == MEMORY_WORKBENCH_CONTRACT_REF
    assert workbench["safe_refs_only"] is True
    assert workbench["semantic_search_enabled"] is False
    assert workbench["vector_db_enabled"] is False
    assert workbench["embedding_search_enabled"] is False
    assert workbench["context_injection_authorized"] is False
    assert workbench["memory_truth_authority"] is False
    assert workbench["production_authority_enabled"] is False
    assert {group["group_id"] for group in workbench["groups"]} == {
        "needs_review",
        "conflict",
        "duplicate",
        "stale",
        "missing_evidence",
        "reviewed",
        "rejected",
    }
    assert workbench["health"]["pending_review_count"] >= 1
    assert workbench["health"]["needs_attention_refs"]
    first_item = workbench["items"][0]
    assert first_item["why_shown_refs"]
    assert first_item["quality_reason_refs"]
    serialized = json.dumps(workbench).lower()
    assert "raw_prompt" not in serialized
    assert "raw_response" not in serialized
    assert "provider_payload" not in serialized


@pytest.mark.parametrize(
    ("decision", "request_overrides", "receipt_field"),
    [
        ("defer", {}, "defer_ref"),
        (
            "merge",
            {"merge_refs": ["business-memory-candidate:preference:merge-peer"]},
            "merge_ref",
        ),
        (
            "supersede",
            {"supersedes_refs": ["business-memory-candidate:preference:older"]},
            "supersede_ref",
        ),
        ("forget_request", {}, "forget_request_ref"),
    ],
)
def test_memory_review_lifecycle_expansion_does_not_create_recall_records(
    tmp_path: Path,
    decision: str,
    request_overrides: dict[str, object],
    receipt_field: str,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)

    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision=decision,  # type: ignore[arg-type]
        request=_decision_request(**request_overrides),
        idempotency_key_ref=f"idempotency-ref:test-memory-{decision.replace('_', '-')}",
    )

    assert receipt["decision"] == decision
    assert receipt[receipt_field]
    assert receipt.get("reviewed_recall_record_ref") is None
    assert repo.list_memory_review_recall_records() == []
    queue_item = repo.list_memory_review_queue(limit=1)[0]
    assert queue_item["review_state"] in {
        "deferred",
        "merged",
        "superseded",
        "forget_requested",
    }
    assert receipt["receipt_ref"] in queue_item["evidence_refs"]
    assert receipt["context_injection_authorized"] is False
    assert receipt["connector_write_authorized"] is False
    assert receipt["production_authority_enabled"] is False


def test_manual_memory_candidate_intake_is_review_candidate_only(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    request = ManualMemoryCandidateRequest(
        candidate_kind="promise",
        title="Manual promise candidate",
        safe_summary="A bounded safe summary for review only.",
        source_refs=["source-ref:manual-note:test"],
        provenance_refs=["provenance-ref:manual-note:test"],
        missing_evidence_refs=["missing-evidence-ref:manual-note:test"],
        related_entity_refs=["person-ref:operator:test"],
        tag_refs=["tag-ref:memory-test"],
    )

    receipt = repo.record_manual_memory_candidate(
        request=request,
        idempotency_key_ref="idempotency-ref:test-manual-memory-candidate",
    )

    assert receipt["status"] == "review_candidate_created_no_recall_record"
    assert receipt["review_candidate_created"] is True
    assert receipt["approval_ref"].startswith("approval-ref:memory-review:")
    assert receipt["approval_status"] == "approved"
    assert receipt["approval_reason_refs"]
    assert receipt["reviewed_recall_record_created"] is False
    assert receipt["memory_write_performed"] is False
    assert receipt["memory_delete_performed"] is False
    assert receipt["memory_export_performed"] is False
    assert receipt["context_injection_authorized"] is False
    assert repo.list_memory_review_recall_records() == []

    workbench = repo.memory_workbench()
    manual_items = [
        item
        for item in workbench["items"]
        if item["review_ref"] == receipt["review_ref"]
    ]
    assert manual_items
    assert "missing_evidence" in manual_items[0]["group_ids"]
    assert workbench["health"]["missing_evidence_count"] >= 1

    replay = repo.record_manual_memory_candidate(
        request=request,
        idempotency_key_ref="idempotency-ref:test-manual-memory-candidate",
    )
    assert replay == receipt
    assert replay["replayed"] is False

    changed_request = request.model_copy(update={"title": "Changed safe title"})
    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_manual_memory_candidate(
            request=changed_request,
            idempotency_key_ref="idempotency-ref:test-manual-memory-candidate",
        )


def test_manual_memory_candidate_rejects_empty_required_refs() -> None:
    with pytest.raises(ValidationError):
        ManualMemoryCandidateRequest(
            candidate_kind="promise",
            title="Manual promise candidate",
            safe_summary="A bounded safe summary for review only.",
            source_refs=[""],
            provenance_refs=["provenance-ref:manual-note:test"],
            missing_evidence_refs=["missing-evidence-ref:manual-note:test"],
        )
    with pytest.raises(ValidationError):
        ManualMemoryCandidateRequest(
            candidate_kind="promise",
            title="Manual promise candidate",
            safe_summary="A bounded safe summary for review only.",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=[""],
            missing_evidence_refs=["missing-evidence-ref:manual-note:test"],
        )
    with pytest.raises(ValidationError):
        ManualMemoryCandidateRequest(
            candidate_kind="promise",
            title="Manual promise candidate",
            safe_summary="A bounded safe summary for review only.",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=["provenance-ref:manual-note:test"],
            missing_evidence_refs=[""],
        )


def test_merge_and_supersede_mark_local_peer_posture_without_deletion(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    first = repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title="Primary merge candidate",
            safe_summary="A bounded safe primary summary for review only.",
            source_refs=["source-ref:manual-note:merge-primary"],
            provenance_refs=["provenance-ref:manual-note:merge-primary"],
            missing_evidence_refs=["missing-evidence-ref:manual-note:merge-primary"],
        ),
        idempotency_key_ref="idempotency-ref:manual-memory-merge-primary",
    )
    second = repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title="Peer merge candidate",
            safe_summary="A bounded safe peer summary for review only.",
            source_refs=["source-ref:manual-note:merge-peer"],
            provenance_refs=["provenance-ref:manual-note:merge-peer"],
            missing_evidence_refs=["missing-evidence-ref:manual-note:merge-peer"],
        ),
        idempotency_key_ref="idempotency-ref:manual-memory-merge-peer",
    )

    merge_receipt = repo.record_memory_review_decision(
        candidate_ref=first["review_ref"],
        decision="merge",
        request=_decision_request(merge_refs=[second["review_ref"]]),
        idempotency_key_ref="idempotency-ref:test-memory-merge-local-peer",
    )

    peer = repo._memory_review_payload_for_ref(second["review_ref"])
    assert peer is not None
    assert peer["review_state"] == "merged"
    assert merge_receipt["receipt_ref"] in peer["evidence_refs"]
    assert repo.list_memory_review_recall_records() == []

    third = repo.record_manual_memory_candidate(
        request=ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title="Older superseded candidate",
            safe_summary="A bounded safe older summary for review only.",
            source_refs=["source-ref:manual-note:supersede-old"],
            provenance_refs=["provenance-ref:manual-note:supersede-old"],
            missing_evidence_refs=["missing-evidence-ref:manual-note:supersede-old"],
        ),
        idempotency_key_ref="idempotency-ref:manual-memory-supersede-old",
    )

    supersede_receipt = repo.record_memory_review_decision(
        candidate_ref=first["review_ref"],
        decision="supersede",
        request=_decision_request(supersedes_refs=[third["review_ref"]]),
        idempotency_key_ref="idempotency-ref:test-memory-supersede-local-peer",
    )

    superseded = repo._memory_review_payload_for_ref(third["review_ref"])
    assert superseded is not None
    assert superseded["review_state"] == "superseded"
    assert supersede_receipt["receipt_ref"] in superseded["evidence_refs"]
    assert repo.list_memory_review_recall_records() == []


def test_merge_suppresses_primary_and_peer_recall_projections(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    primary = _manual_memory_candidate(repo, "merge-primary-recall")
    peer = _manual_memory_candidate(repo, "merge-peer-recall")
    primary_accept = repo.record_memory_review_decision(
        candidate_ref=str(primary["review_ref"]),
        decision="accept",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-merge-primary-accept",
    )
    peer_accept = repo.record_memory_review_decision(
        candidate_ref=str(peer["review_ref"]),
        decision="accept",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-merge-peer-accept",
    )
    assert repo.memory_l1_hot_index()["preview_count"] == 2

    merge_receipt = repo.record_memory_review_decision(
        candidate_ref=str(primary["review_ref"]),
        decision="merge",
        request=_decision_request(merge_refs=[str(peer["review_ref"])]),
        idempotency_key_ref="idempotency-ref:test-memory-merge-suppresses-peer",
    )

    assert set(merge_receipt["suppressed_recall_record_refs"]) == {
        primary_accept["reviewed_recall_record_ref"],
        peer_accept["reviewed_recall_record_ref"],
    }
    records_by_ref = {
        f"memory-record-ref:{record['memory_id']}": record
        for record in repo.list_memory_review_recall_records()
    }
    for record_ref in merge_receipt["suppressed_recall_record_refs"]:
        assert records_by_ref[record_ref]["status"] == "superseded"
        assert records_by_ref[record_ref]["retention_state"] == "blocked"
        assert merge_receipt["receipt_ref"] in records_by_ref[record_ref]["receipt_refs"]
    assert repo.memory_l1_hot_index()["preview_count"] == 0


def test_manual_memory_candidate_rejects_raw_content_markers() -> None:
    with pytest.raises(ValidationError):
        ManualMemoryCandidateRequest(
            candidate_kind="preference",
            title="Raw content candidate",
            safe_summary="Contains raw_prompt material.",
            source_refs=["source-ref:manual-note:test"],
            provenance_refs=["provenance-ref:manual-note:test"],
            missing_evidence_refs=["missing-evidence-ref:manual-note:test"],
        )


def test_memory_search_filters_safe_refs_without_semantic_search(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    result = repo.memory_search(
        kind="preference",
        source_ref="source-ref:manual-note:founder-loop-storage",
        review_state="review_needed",
        quality_state="business-memory-quality:stale-expired",
    )

    assert result["schema_version"] == "fcc_mem_001_memory_search.v1"
    assert result["safe_refs_only"] is True
    assert result["semantic_search_enabled"] is False
    assert result["vector_db_enabled"] is False
    assert result["embedding_search_enabled"] is False
    assert result["context_injection_authorized"] is False
    assert result["count"] >= 1
    assert all(item["candidate_kind"] == "preference" for item in result["items"])


def test_memory_workbench_api_routes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)

    workbench_response = client.get("/control-center/memory/workbench")
    assert workbench_response.status_code == 200
    workbench = workbench_response.json()["data"]
    assert workbench["schema_version"] == "fcc_mem_001_memory_workbench.v1"

    search_response = client.get("/control-center/memory/search?kind=preference")
    assert search_response.status_code == 200
    assert search_response.json()["data"]["semantic_search_enabled"] is False

    manual_response = client.post(
        "/control-center/memory/review/manual-candidate",
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:api-manual-memory:test"},
        json={
            "candidate_kind": "preference",
            "title": "Manual safe memory candidate",
            "safe_summary": "A bounded safe summary for review only.",
            "source_refs": ["source-ref:manual-note:test"],
            "provenance_refs": ["provenance-ref:manual-note:test"],
            "missing_evidence_refs": ["missing-evidence-ref:manual-note:test"],
        },
    )
    assert manual_response.status_code == 200
    assert (
        manual_response.json()["data"]["status"]
        == "review_candidate_created_no_recall_record"
    )

    unsafe_receipt_lookup = client.get(
        "/control-center/memory/review/raw_prompt/receipt"
    )
    assert unsafe_receipt_lookup.status_code == 400
    assert (
        unsafe_receipt_lookup.json()["detail"]["code"]
        == "FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_REF_DENIED"
    )
    assert "raw_prompt" not in unsafe_receipt_lookup.text


def test_memory_cli_parity_uses_safe_ref_outputs(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder_loop"
    command = [
        sys.executable,
        "scripts/dev/uaa_founder_loop.py",
        "--state-dir",
        str(state_dir),
        "memory-workbench",
        "--limit",
        "3",
    ]

    result = subprocess.run(
        command,
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["command_ref"] == "repo-local-command:founder-loop-memory-workbench"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["workbench"]["schema_version"] == "fcc_mem_001_memory_workbench.v1"
    assert str(state_dir) not in result.stdout


def test_memory_cli_rejects_unsafe_inputs_without_traceback(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder_loop"
    command = [
        sys.executable,
        "scripts/dev/uaa_founder_loop.py",
        "--state-dir",
        str(state_dir),
        "memory-manual-candidate",
        "--candidate-kind",
        "preference",
        "--title",
        "Rejected unsafe memory candidate",
        "--safe-summary",
        "Contains raw_prompt material.",
        "--idempotency-ref",
        "idempotency-ref:manual-memory-cli-unsafe",
        "--source-ref",
        "source-ref:manual-note:cli",
        "--provenance-ref",
        "provenance-ref:manual-note:cli",
        "--missing-evidence-ref",
        "missing-evidence-ref:manual-note:cli",
    ]

    result = subprocess.run(
        command,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["status"] == "blocked"
    assert payload["error_ref"] == "FOUNDER_LOOP_MANUAL_MEMORY_CANDIDATE_REF_DENIED"
    combined = f"{result.stdout}\n{result.stderr}"
    assert "Traceback" not in combined
    assert "input_value" not in combined
    assert "raw_prompt" not in combined
    assert str(state_dir) not in combined
