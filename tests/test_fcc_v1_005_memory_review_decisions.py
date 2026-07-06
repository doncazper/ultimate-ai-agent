from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts import verify_fcc_v1_005_memory_review_decisions as verifier
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF,
    MEMORY_BOUNDED_POSTURE_CONTRACT_REF,
    MemoryReviewDecisionReceipt,
    MemoryReviewDecisionRequest,
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)


def _safe_receipt(**overrides: object) -> MemoryReviewDecisionReceipt:
    data: dict[str, object] = {
        "candidate_ref": "memory-review:test",
        "review_ref": "memory-review:test",
        "decision": "accept",
        "source_refs": ["source-ref:manual-note:test"],
        "evidence_refs": ["evidence-ref:memory-review:test"],
        "reviewer_ref": "actor-ref:local-operator",
        "receipt_ref": "receipt:memory-review:accept:test",
        "decision_ref": "memory-review-decision:accept:test",
        "audit_ref": "audit-ref:memory-review:accept:test",
        "idempotency_key_ref": "idempotency-ref:memory-review:test",
        "payload_fingerprint_ref": "payload-fingerprint:memory-review-decision:test",
        "evidence_timeline_event_ref": "evidence-ref:memory-review:accept:test",
        "approval_ref": "approval-ref:memory-review:test",
        "approval_scope_ref": MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
        "approval_status": "approved",
        "approval_reason_refs": ["approval-reason:approval-validated"],
        "safe_disable_ref": MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
        "rollback_ref": MEMORY_REVIEW_WRITE_ROLLBACK_REF,
        "rollback_blocker_refs": [MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF],
        "reviewed_recall_ref": "reviewed-recall-ref:memory-review:test",
        "reviewed_recall_record_ref": "memory-record-ref:mem_test",
        "reviewed_recall_write_performed": True,
        "safe_summary_ref": "safe-summary-ref:memory-review:accept",
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionReceipt(**data)


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:test-reviewer",
        "source_refs": ["source-ref:manual-note:test"],
        "evidence_refs": ["evidence-ref:memory-review:test"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def test_memory_review_decision_receipt_accepts_safe_decision() -> None:
    receipt = _safe_receipt()

    assert receipt.contract_ref == FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert receipt.decision == "accept"
    assert receipt.context_injection_authorized is False
    assert receipt.source_truth_authority is False
    assert receipt.production_authority_enabled is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate_ref", "memory-review:raw-prompt"),
        ("reviewer_ref", "actor-ref:credential-material"),
        ("evidence_refs", ["evidence-ref:provider-payload"]),
        ("corrected_summary_ref", "safe-summary-ref:raw-private-content"),
        ("reviewed_recall_record_ref", "memory-record-ref:raw-private-content"),
        ("safe_summary_ref", "safe-summary-ref:username"),
    ],
)
def test_memory_review_decision_receipt_rejects_unsafe_content_refs(
    field: str,
    value: object,
) -> None:
    overrides: dict[str, object] = {field: value}
    if field == "corrected_summary_ref":
        overrides.update(
            {
                "decision": "correct",
                "correction_ref": "correction-ref:memory-review:test",
            }
        )
    with pytest.raises(ValidationError):
        _safe_receipt(**overrides)


@pytest.mark.parametrize(
    "flag",
    [
        "context_injection_authorized",
        "connector_write_authorized",
        "external_crm_sync_authorized",
        "account_sync_authorized",
        "automatic_action_execution_authorized",
        "model_provider_authority_allowed",
        "source_truth_authority",
        "memory_truth_authority",
        "production_authority_enabled",
    ],
)
def test_memory_review_decision_receipt_rejects_authority_flags(flag: str) -> None:
    with pytest.raises(ValidationError):
        _safe_receipt(**{flag: True})


def test_memory_review_decisions_persist_append_first_replay_and_conflict(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)
    request = _decision_request()

    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=request,
        idempotency_key_ref="idempotency-ref:test-memory-accept",
    )

    assert receipt["contract_ref"] == FCC_MEMORY_REVIEW_DECISION_CONTRACT_REF
    assert receipt["decision"] == "accept"
    assert receipt["reviewed_recall_ref"].startswith("reviewed-recall-ref:")
    assert receipt["reviewed_recall_record_ref"].startswith("memory-record-ref:")
    assert receipt["reviewed_recall_write_performed"] is True
    assert receipt["approval_scope_ref"] == MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
    assert receipt["safe_disable_ref"] == MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF
    assert receipt["rollback_ref"] == MEMORY_REVIEW_WRITE_ROLLBACK_REF
    assert receipt["rollback_execution_enabled"] is False
    assert MEMORY_REVIEW_WRITE_ROLLBACK_BLOCKED_REF in receipt["rollback_blocker_refs"]
    assert receipt["context_injection_authorized"] is False
    assert receipt["connector_write_authorized"] is False
    assert receipt["external_crm_sync_authorized"] is False
    assert receipt["automatic_action_execution_authorized"] is False
    assert receipt["source_truth_authority"] is False
    assert (
        repo.list_memory_review_decisions()[0]["receipt_ref"] == receipt["receipt_ref"]
    )
    recall_records = repo.list_memory_review_recall_records()
    assert len(recall_records) == 1
    recall_record = recall_records[0]
    assert (
        f"memory-record-ref:{recall_record['memory_id']}"
        == receipt["reviewed_recall_record_ref"]
    )
    assert recall_record["authority_level"] == "recall_only"
    assert recall_record["review_state"] == "user_reviewed"
    assert recall_record["safe_summary"]
    assert receipt["receipt_ref"] in recall_record["receipt_refs"]
    assert recall_record["recall_metadata"]["context_pack_eligible"] is False
    assert recall_record["recall_metadata"]["injection_priority"] == 0
    assert recall_record["metadata"]["context_injection_authorized"] is False
    assert recall_record["metadata"]["source_truth_authority"] is False

    replay = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=request,
        idempotency_key_ref="idempotency-ref:test-memory-accept",
    )
    assert replay == receipt
    assert replay["replayed"] is False

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="accept",
            request=_decision_request(reviewer_ref="actor-ref:changed-reviewer"),
            idempotency_key_ref="idempotency-ref:test-memory-accept",
        )


def test_memory_review_accept_correct_denied_when_write_lane_safe_disabled(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)

    posture = repo._disable_memory_review_write_lane_for_test(
        disabled_reason_refs=["safe-disable-reason:test-memory-review-write"]
    )
    assert posture["safe_disable_active"] is True
    assert posture["memory_review_writes_enabled"] is False

    with pytest.raises(
        Exception,
        match="FOUNDER_LOOP_MEMORY_WRITE_SAFE_DISABLED",
    ):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="accept",
            request=_decision_request(),
            idempotency_key_ref="idempotency-ref:test-memory-safe-disabled-accept",
        )
    assert repo.list_memory_review_recall_records() == []

    reject_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-safe-disabled-reject",
    )
    assert reject_receipt["decision"] == "reject"
    assert reject_receipt["reviewed_recall_write_performed"] is False
    assert reject_receipt.get("reviewed_recall_record_ref") is None


def test_memory_review_correction_stores_bounded_safe_summary_and_ref(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)

    with pytest.raises(Exception, match="FOUNDER_LOOP_MEMORY_CORRECTION_REF_REQUIRED"):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="correct",
            request=_decision_request(),
            idempotency_key_ref="idempotency-ref:test-memory-correct-missing",
        )
    with pytest.raises(
        Exception,
        match="FOUNDER_LOOP_MEMORY_CORRECTION_SUMMARY_REQUIRED",
    ):
        repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="correct",
            request=_decision_request(
                corrected_summary_ref="safe-summary-ref:memory-review-correction:test"
            ),
            idempotency_key_ref="idempotency-ref:test-memory-correct-summary-missing",
        )

    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="correct",
        request=_decision_request(
            corrected_summary_ref="safe-summary-ref:memory-review-correction:test",
            corrected_safe_summary="Corrected bounded safe summary for review only.",
        ),
        idempotency_key_ref="idempotency-ref:test-memory-correct",
    )

    assert receipt["decision"] == "correct"
    assert (
        receipt["corrected_summary_ref"]
        == "safe-summary-ref:memory-review-correction:test"
    )
    assert (
        receipt["corrected_safe_summary"]
        == "Corrected bounded safe summary for review only."
    )
    assert "raw" not in str(receipt).lower()
    assert receipt["approval_ref"].startswith("approval-ref:memory-review:")
    assert receipt["reviewed_recall_write_performed"] is True
    assert receipt["reviewed_recall_record_ref"].startswith("memory-record-ref:")
    recall_records = repo.list_memory_review_recall_records()
    assert len(recall_records) == 1
    recall_record = recall_records[0]
    assert recall_record["memory_kind"] == "correction"
    assert (
        "Corrected bounded safe summary for review only."
        in recall_record["safe_summary"]
    )
    assert receipt["receipt_ref"] in recall_record["receipt_refs"]
    assert "raw" not in str(recall_record).lower()
    queue_item = repo.list_memory_review_queue(limit=1)[0]
    assert (
        queue_item["correction_posture"]
        == "corrected_summary_ref_recorded_no_raw_content"
    )


def test_rejected_candidate_is_preserved_and_evidence_visible(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)

    receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-reject",
    )

    queue_item = repo.list_memory_review_queue(limit=1)[0]
    assert queue_item["review_state"] == "rejected"
    assert (
        queue_item["rejection_posture"] == "rejected_candidate_preserved_with_receipt"
    )
    assert queue_item["business_memory_candidate_ref"] == candidate_ref
    assert receipt["receipt_ref"] in queue_item["evidence_refs"]
    assert receipt.get("reviewed_recall_record_ref") is None
    assert receipt["reviewed_recall_write_performed"] is False
    assert repo.list_memory_review_recall_records() == []

    timeline = repo.today_summary()["evidence_timeline"]
    memory_event = next(
        item
        for item in timeline
        if item.get("item_kind") == "memory_review_evidence_ref"
        and queue_item["review_ref"] in item.get("source_refs", [])
    )
    assert receipt["receipt_ref"] in memory_event["receipt_refs"]
    history = memory_event["history_answers"]
    assert history["approved"]["status"] == "decision_receipt_recorded"
    assert (
        "Memory Review accept, correct, reject, defer, merge, supersede, "
        "and forget-request decisions" in history["happened"]["answer"]
    )
    assert "context injection" in history["blocked"]["answer"]


def test_terminal_memory_review_decision_suppresses_prior_recall_projection(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    candidate_ref = _first_candidate_ref(repo)
    accept_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-accept-before-reject",
    )
    assert repo.memory_l1_hot_index()["preview_count"] == 1

    reject_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:test-memory-reject-after-accept",
    )

    assert reject_receipt["suppressed_recall_record_refs"] == [
        accept_receipt["reviewed_recall_record_ref"]
    ]
    recall_record = repo.list_memory_review_recall_records()[0]
    assert recall_record["status"] == "revoked"
    assert recall_record["retention_state"] == "blocked"
    assert reject_receipt["receipt_ref"] in recall_record["receipt_refs"]
    assert repo.memory_l1_hot_index()["preview_count"] == 0
    assert all(
        item["source"] != "l1_reviewed_recall_projection"
        for item in repo.memory_workbench()["items"]
    )


def test_memory_review_decision_api_requires_idempotency_replays_and_conflicts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    client = TestClient(app)
    candidate_ref = (
        "business-memory-candidate:preference:memory-review-founder-loop-preferences"
    )
    body = {
        "reviewer_ref": "actor-ref:test-api-reviewer",
        "source_refs": ["source-ref:manual-note:test-api"],
        "evidence_refs": ["evidence-ref:memory-review:test-api"],
    }

    missing = client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json=body,
    )
    assert missing.status_code == 428
    assert missing.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    response = client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-memory-reject"},
    )
    assert response.status_code == 200
    receipt = response.json()["data"]
    assert receipt["decision"] == "reject"
    assert receipt["replayed"] is False
    assert receipt["context_injection_authorized"] is False
    assert receipt.get("reviewed_recall_record_ref") is None

    lookup = client.get(
        f"/control-center/memory/review/{candidate_ref}/receipt",
    )
    assert lookup.status_code == 200
    assert lookup.json()["data"]["receipt_ref"] == receipt["receipt_ref"]

    missing_lookup = client.get(
        "/control-center/memory/review/business-memory-candidate:missing/receipt",
    )
    assert missing_lookup.status_code == 404
    assert (
        missing_lookup.json()["detail"]["code"]
        == "FOUNDER_LOOP_MEMORY_DECISION_RECEIPT_NOT_FOUND"
    )

    replay = client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-memory-reject"},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is False

    conflict = client.post(
        f"/control-center/memory/review/{candidate_ref}/reject",
        json={**body, "reviewer_ref": "actor-ref:test-api-reviewer-changed"},
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-memory-reject"},
    )
    assert conflict.status_code == 409
    assert (
        conflict.json()["detail"]["code"]
        == "FOUNDER_LOOP_MEMORY_DECISION_IDEMPOTENCY_CONFLICT"
    )

    review = client.get("/control-center/memory/review")
    assert review.status_code == 200
    data = review.json()["data"]
    assert receipt["receipt_ref"] in data["decision_receipt_refs"]
    assert data["bounded_memory_posture_contract_ref"] == (
        MEMORY_BOUNDED_POSTURE_CONTRACT_REF
    )
    assert data["bounded_memory_posture"]["context_injection_authorized"] is False
    assert (
        data["bounded_memory_posture"]["external_memory_provider_write_authorized"]
        is False
    )
    assert data["context_injection_authorized"] is False
    assert data["raw_content_stored"] is False


def test_memory_review_cli_records_and_inspects_reviewed_recall_write(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    repo = FounderLoopRepository(state_dir)
    candidate_ref = _first_candidate_ref(repo)

    decision = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/dev/uaa_founder_loop.py")),
            "--state-dir",
            str(state_dir),
            "record-memory-decision",
            "--candidate-ref",
            candidate_ref,
            "--decision",
            "accept",
            "--idempotency-ref",
            "idempotency-ref:test-memory-cli-accept",
            "--reviewer-ref",
            "actor-ref:test-memory-cli-reviewer",
            "--source-ref",
            "source-ref:test-memory-cli",
            "--evidence-ref",
            "evidence-ref:test-memory-cli",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    decision_payload = json.loads(decision.stdout)
    receipt = decision_payload["receipt"]
    assert receipt["decision"] == "accept"
    assert receipt["reviewed_recall_write_performed"] is True
    assert receipt["approval_scope_ref"] == MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
    assert receipt["safe_disable_ref"] == MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF
    assert receipt["rollback_execution_enabled"] is False
    assert decision_payload["safe_refs_only"] is True
    assert str(state_dir) not in decision.stdout

    inspect = subprocess.run(
        [
            sys.executable,
            str(Path("scripts/dev/uaa_founder_loop.py")),
            "--state-dir",
            str(state_dir),
            "memory-receipts",
            "--limit",
            "5",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    inspect_payload = json.loads(inspect.stdout)
    assert (
        inspect_payload["exact_write_scope_ref"] == MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
    )
    assert (
        inspect_payload["approval_binding"]
        == "local_approval_authority_exact_scope_validated"
    )
    assert inspect_payload["reviewed_recall_record_count"] == 1
    assert receipt["receipt_ref"] in inspect_payload["decision_receipt_refs"]
    assert (
        inspect_payload["write_safe_disable_posture"]["rollback_execution_enabled"]
        is False
    )
    assert inspect_payload["safe_refs_only"] is True
    serialized = json.dumps(inspect_payload).lower()
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert str(state_dir).lower() not in serialized


def test_fcc_v1_005_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []
