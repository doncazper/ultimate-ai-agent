from __future__ import annotations

from pathlib import Path

import scripts.verify_fcc_inbox_001_approval_envelope_ux as verifier
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def test_fcc_inbox_001_verifier_passes_current_repo() -> None:
    assert verifier.validate_fcc_inbox_001_approval_envelope_ux() == []


def test_fcc_inbox_001_doc_pins_action_inbox_boundary() -> None:
    text = (
        ROOT / "docs/control_center/FCC_INBOX_001_APPROVAL_ENVELOPE_UX.md"
    ).read_text(encoding="utf-8")

    assert "Status: Implemented" in text
    assert "Primary surface: `/actions` Action Inbox" in text
    assert "GET /control-center/actions/inbox" in text
    assert "python_core_action_inbox_read_model" in text
    assert "mock_fallback_non_authoritative" in text
    assert "does not add generic action execution" in text
    assert verifier.VERIFIER_REF in text


def test_action_inbox_read_model_exposes_backend_owned_envelope_and_receipts(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder-loop.sqlite3")
    inbox = repo.actions_inbox()
    assert inbox["items"]

    item = inbox["items"][0]
    envelope = item["approval_envelope"]
    visibility = item["receipt_visibility"]

    assert envelope["schema_version"] == "founder_loop_action_approval_envelope.v1"
    assert envelope["source"] == verifier.READ_MODEL_SOURCE
    assert envelope["backend_owned"] is True
    assert {"exact_scope", "approval_requirement", "idempotency_ref"} <= set(
        envelope
    )
    assert "expected_receipt_refs" in envelope
    assert "rollback_safe_disable_posture" in envelope
    assert visibility["schema_version"] == "founder_loop_action_receipt_visibility.v1"
    assert visibility["source"] == verifier.READ_MODEL_SOURCE
    assert visibility["backend_owned"] is True
    assert {
        "decision_receipt_ref",
        "local_task_ref",
        "local_task_commit_receipt_ref",
        "evidence_timeline_event_ref",
        "replay_posture",
        "conflict_posture",
    } <= set(visibility)


def test_action_inbox_maturity_rank_remains_bounded() -> None:
    manifest = (
        ROOT / "docs/control_center/operational_maturity_manifest.json"
    ).read_text(encoding="utf-8")

    assert '"module_id": "action_inbox"' in manifest
    assert '"current_rank": 3' in manifest
    assert '"lane_id": "local_task_create"' in manifest
    assert '"rank": 5' in manifest
    assert verifier.VERIFIER_REF in manifest
