from typing import Any
from pathlib import Path
import json

from ultimate_ai_agent.core.file_review import (
    FileReviewApprovalCaptureDecisionStatus,
    FileReviewApprovalDecisionKind,
    FileReviewApprovalRecord,
    FileReviewApprovalStore,
)
from ultimate_ai_agent.core.time import utc_now


def _record(**overrides: Any) -> Any:
    data = {
        "approval_ref": "file-review-approval-capture:store",
        "actor_ref": "user:store",
        "review_packet_ref": "file-review-packet:store",
        "preview_result_ref": "redacted-file-preview-output:store",
        "redaction_summary_ref": "file-review-redaction-summary:store",
        "file_ref": "file-ref:store",
        "safe_path_ref": "filesystem-preview-path:safe-root_store/docs/review.md",
        "decision": FileReviewApprovalDecisionKind.approve_review_only,
        "status": FileReviewApprovalCaptureDecisionStatus.approved_for_review_only,
        "idempotency_key": "file-review-approval-idempotency:store",
        "created_at": utc_now(),
    }
    data.update(overrides)
    return FileReviewApprovalRecord(**data)


def test_file_review_approval_store_writes_safe_jsonl_only(tmp_path: Path) -> None:
    store_path = tmp_path / "review_approvals.jsonl"
    store = FileReviewApprovalStore(store_path)
    record = _record()

    decision = store.persist(record)

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.approved_for_review_only
    assert decision.persisted is True
    assert store_path.exists()
    payload = json.loads(store_path.read_text(encoding="utf-8").strip())
    assert payload["review_packet_ref"] == "file-review-packet:store"
    assert "raw_content" not in payload
    assert "full_file_content" not in payload
    assert "unredacted_preview" not in payload
    assert "absolute_path" not in payload
    assert "/Users/" not in store_path.read_text(encoding="utf-8")


def test_file_review_approval_store_idempotent_same_record_is_safe(tmp_path: Path) -> None:
    store = FileReviewApprovalStore(tmp_path / "review_approvals.jsonl")
    record = _record()

    first = store.persist(record)
    second = store.persist(record)

    assert first.persisted is True
    assert second.persisted is True
    assert second.reason_codes == ["FILE_REVIEW_APPROVAL_CAPTURE_IDEMPOTENT_REPLAY"]


def test_file_review_approval_store_rejects_conflicting_replay(tmp_path: Path) -> None:
    store = FileReviewApprovalStore(tmp_path / "review_approvals.jsonl")
    record = _record()
    changed = _record(file_ref="file-ref:changed")

    store.persist(record)
    decision = store.persist(changed)

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert decision.persisted is False
    assert "FILE_REVIEW_APPROVAL_CAPTURE_REPLAY_MISMATCH" in decision.reason_codes


def test_file_review_approval_record_model_copy_raw_extra_is_denied(tmp_path: Path) -> None:
    store = FileReviewApprovalStore(tmp_path / "review_approvals.jsonl")
    record = _record().model_copy(update={"raw_content": "secret raw text"})

    decision = store.persist(record)

    assert decision.status == FileReviewApprovalCaptureDecisionStatus.rejected
    assert decision.persisted is False
    assert "FILE_REVIEW_APPROVAL_CAPTURE_RAW_CONTENT_DENIED" in decision.reason_codes
    assert "secret raw text" not in decision.safe_message
