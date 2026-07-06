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
    MEMORY_BOUNDED_POSTURE_CONTRACT_REF,
    MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF,
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
    return str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )


def _manual_memory_candidate(
    repo: FounderLoopRepository, slug: str
) -> dict[str, object]:
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


def test_memory_workbench_read_model_groups_and_blocks_authority(
    tmp_path: Path,
) -> None:
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
    lifecycle_posture = workbench["lifecycle_posture"]
    assert lifecycle_posture["contract_ref"] == MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF
    assert lifecycle_posture["review_only"] is True
    assert lifecycle_posture["safe_refs_only"] is True
    assert lifecycle_posture["hard_delete_authorized"] is False
    assert lifecycle_posture["memory_export_authorized"] is False
    assert lifecycle_posture["automatic_merge_authorized"] is False
    assert lifecycle_posture["automatic_supersede_authorized"] is False
    assert lifecycle_posture["automatic_forget_authorized"] is False
    assert lifecycle_posture["hidden_memory_write_authorized"] is False
    assert lifecycle_posture["context_injection_authorized"] is False
    assert lifecycle_posture["connector_write_authorized"] is False
    assert lifecycle_posture["model_provider_call_authorized"] is False
    assert lifecycle_posture["production_authority_enabled"] is False
    assert lifecycle_posture["receipt_truncation_posture"] == (
        "bounded_by_workbench_limit_safe_refs_only"
    )
    bounded_posture = workbench["bounded_memory_posture"]
    assert bounded_posture["contract_ref"] == MEMORY_BOUNDED_POSTURE_CONTRACT_REF
    assert bounded_posture["backend_owned"] is True
    assert bounded_posture["control_center_presentation_only"] is True
    assert bounded_posture["safe_refs_only"] is True
    assert bounded_posture["raw_content_included"] is False
    assert bounded_posture["target_posture"]["supported_target_kinds"] == [
        "user",
        "profile",
        "project",
    ]
    assert (
        bounded_posture["target_posture"]["operator_selected_context_required"] is True
    )
    assert bounded_posture["capacity_posture"]["visible_item_count"] == len(
        workbench["items"]
    )
    assert bounded_posture["capacity_posture"]["max_visible_items"] == 80
    assert bounded_posture["capacity_posture"]["token_estimate"] >= 1
    assert bounded_posture["source_posture"]["safe_summary_only"] is True
    assert bounded_posture["source_posture"]["source_refs_required"] is True
    assert bounded_posture["source_posture"]["source_refs"]
    assert bounded_posture["staleness_posture"]["stale_count"] >= 1
    assert bounded_posture["staleness_posture"]["stale_item_refs"]
    assert bounded_posture["why_shown_posture"]["why_shown_required"] is True
    assert bounded_posture["why_shown_posture"]["why_shown_refs"]
    assert (
        bounded_posture["quality_review_posture"]["review_required_before_recall"]
        is True
    )
    assert bounded_posture["quality_review_posture"]["correction_supported"] is True
    assert bounded_posture["quality_review_posture"]["rejection_supported"] is True
    assert (
        bounded_posture["quality_review_posture"][
            "memory_write_requires_review_receipt"
        ]
        is True
    )
    assert bounded_posture["automatic_memory_write_authorized"] is False
    assert bounded_posture["autonomous_memory_write_authorized"] is False
    assert bounded_posture["hidden_prompt_injection_authorized"] is False
    assert bounded_posture["external_memory_provider_write_authorized"] is False
    assert bounded_posture["context_injection_authorized"] is False
    assert bounded_posture["memory_truth_authority"] is False
    assert bounded_posture["model_provider_call_authorized"] is False
    assert bounded_posture["production_authority_enabled"] is False
    assert (
        "blocked-state:bounded-memory-no-autonomous-memory-write"
        in (bounded_posture["blocked_state_refs"])
    )
    assert {lane["lane_id"] for lane in lifecycle_posture["lanes"]} == {
        "duplicate_review",
        "stale_review",
        "conflict_review",
        "corrected",
        "merged",
        "superseded",
        "forget_requested",
    }
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
    assert first_item["lifecycle_state_refs"]
    assert first_item["available_lifecycle_decisions"]
    assert first_item["reversible_review_posture"] == (
        "later_receipt_can_update_review_posture_no_rollback_execution"
    )
    assert first_item["hard_delete_authorized"] is False
    assert first_item["automatic_merge_authorized"] is False
    assert first_item["automatic_supersede_authorized"] is False
    assert first_item["automatic_forget_authorized"] is False
    assert first_item["hidden_memory_write_authorized"] is False
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

    workbench = repo.memory_workbench(limit=20)
    lifecycle_posture = workbench["lifecycle_posture"]
    receipt_refs_by_kind = lifecycle_posture["decision_receipt_refs_by_kind"]
    assert merge_receipt["receipt_ref"] in receipt_refs_by_kind["merge"]
    assert supersede_receipt["receipt_ref"] in receipt_refs_by_kind["supersede"]
    assert "merge" in lifecycle_posture["receipt_backed_decision_kinds"]
    assert "supersede" in lifecycle_posture["receipt_backed_decision_kinds"]
    lanes = {lane["lane_id"]: lane for lane in lifecycle_posture["lanes"]}
    assert lanes["merged"]["receipt_backed"] is True
    items_by_ref = {item["review_ref"]: item for item in workbench["items"]}
    assert (
        items_by_ref[second["review_ref"]]["memory_ref"] in lanes["merged"]["item_refs"]
    )
    assert lanes["superseded"]["receipt_backed"] is True
    assert (
        items_by_ref[third["review_ref"]]["memory_ref"]
        in lanes["superseded"]["item_refs"]
    )
    for lane in lanes.values():
        assert lane["review_only"] is True
        assert (
            "blocked-state:memory-lifecycle-no-hard-delete"
            in lane["blocked_state_refs"]
        )
    assert (
        merge_receipt["receipt_ref"]
        in items_by_ref[second["review_ref"]]["lifecycle_receipt_refs"]
    )
    assert (
        supersede_receipt["receipt_ref"]
        in items_by_ref[third["review_ref"]]["lifecycle_receipt_refs"]
    )


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
        assert (
            merge_receipt["receipt_ref"] in records_by_ref[record_ref]["receipt_refs"]
        )
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


def test_memory_merge_supersede_cli_inspection_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    repo = FounderLoopRepository(state_dir)
    first = _manual_memory_candidate(repo, "cli-merge-primary")
    second = _manual_memory_candidate(repo, "cli-merge-peer")
    receipt = repo.record_memory_review_decision(
        candidate_ref=str(first["review_ref"]),
        decision="merge",
        request=_decision_request(merge_refs=[str(second["review_ref"])]),
        idempotency_key_ref="idempotency-ref:test-memory-merge-cli-inspection",
    )
    state_files_before = sorted(
        path.relative_to(state_dir).as_posix()
        for path in state_dir.rglob("*")
        if path.is_file()
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/inspect_memory_merge_supersede_posture.py")),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["contract_ref"] == MEMORY_LIFECYCLE_POSTURE_CONTRACT_REF
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["hard_delete_authorized"] is False
    assert payload["automatic_merge_authorized"] is False
    assert payload["hidden_memory_write_authorized"] is False
    lifecycle_posture = payload["lifecycle_posture"]
    assert (
        receipt["receipt_ref"]
        in lifecycle_posture["decision_receipt_refs_by_kind"]["merge"]
    )
    assert "merge" in lifecycle_posture["receipt_backed_decision_kinds"]
    serialized = json.dumps(payload).lower()
    assert "raw_prompt" not in serialized
    assert "raw_response" not in serialized
    assert "provider_payload" not in serialized
    assert str(tmp_path).lower() not in serialized
    state_files_after = sorted(
        path.relative_to(state_dir).as_posix()
        for path in state_dir.rglob("*")
        if path.is_file()
    )
    assert state_files_after == state_files_before

    no_recall_state_dir = tmp_path / "no_recall_state"
    repo_without_recall = FounderLoopRepository(no_recall_state_dir)
    _manual_memory_candidate(repo_without_recall, "cli-no-recall-store")
    assert not (no_recall_state_dir / "memory_review_recall.sqlite3").exists()
    no_recall_files_before = sorted(
        path.relative_to(no_recall_state_dir).as_posix()
        for path in no_recall_state_dir.rglob("*")
        if path.is_file()
    )
    no_recall = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/inspect_memory_merge_supersede_posture.py")),
            "--state-dir",
            str(no_recall_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(no_recall.stdout)["storage_state"] == "existing_state_read_only"
    assert not (no_recall_state_dir / "memory_review_recall.sqlite3").exists()
    no_recall_files_after = sorted(
        path.relative_to(no_recall_state_dir).as_posix()
        for path in no_recall_state_dir.rglob("*")
        if path.is_file()
    )
    assert no_recall_files_after == no_recall_files_before

    missing_state_dir = tmp_path / "missing_state"
    missing = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/inspect_memory_merge_supersede_posture.py")),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert not missing_state_dir.exists()
    missing_payload = json.loads(missing.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["lifecycle_posture"]["safe_refs_only"] is True

    broken_state_dir = tmp_path / "broken_state"
    broken_state_dir.mkdir()
    (broken_state_dir / "founder_loop.sqlite3").write_text(
        "not a sqlite database",
        encoding="utf-8",
    )
    broken = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/inspect_memory_merge_supersede_posture.py")),
            "--state-dir",
            str(broken_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    broken_payload = json.loads(broken.stdout)
    assert broken_payload["storage_state"] == "existing_state_unreadable_redacted"
    assert broken_payload["inspection_error_ref"] == (
        "error-ref:memory-merge-supersede-posture:read-failed-redacted"
    )
    assert broken.stderr == ""
    assert "Traceback" not in broken.stdout
    assert str(broken_state_dir) not in broken.stdout


def test_memory_search_filters_safe_refs_without_semantic_search(
    tmp_path: Path,
) -> None:
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


def test_memory_workbench_api_routes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)

    workbench_response = client.get("/control-center/memory/workbench")
    assert workbench_response.status_code == 200
    workbench = workbench_response.json()["data"]
    assert workbench["schema_version"] == "fcc_mem_001_memory_workbench.v1"
    assert workbench["bounded_memory_posture"]["contract_ref"] == (
        MEMORY_BOUNDED_POSTURE_CONTRACT_REF
    )

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
    assert payload["workbench"]["bounded_memory_posture"]["contract_ref"] == (
        MEMORY_BOUNDED_POSTURE_CONTRACT_REF
    )
    assert str(state_dir) not in result.stdout

    bounded_command = [
        sys.executable,
        "scripts/dev/uaa_founder_loop.py",
        "--state-dir",
        str(state_dir),
        "memory-bounded-posture",
        "--limit",
        "3",
    ]
    bounded_result = subprocess.run(
        bounded_command,
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    bounded_payload = json.loads(bounded_result.stdout)
    posture = bounded_payload["bounded_memory_posture"]
    assert bounded_payload["command_ref"] == (
        "repo-local-command:founder-loop-memory-bounded-posture"
    )
    assert posture["contract_ref"] == MEMORY_BOUNDED_POSTURE_CONTRACT_REF
    assert posture["safe_refs_only"] is True
    assert posture["automatic_memory_write_authorized"] is False
    assert posture["hidden_prompt_injection_authorized"] is False
    assert posture["external_memory_provider_write_authorized"] is False
    assert bounded_payload["raw_prompt_omitted"] is True
    assert bounded_payload["raw_response_omitted"] is True
    assert bounded_payload["raw_provider_payload_omitted"] is True
    assert str(state_dir) not in bounded_result.stdout


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
