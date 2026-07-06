from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS,
    MEMORY_LEARNING_POSTURE_CONTRACT_REF,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import memory_write_authority_lease


DENIED_FLAGS = [
    "forget_execution_authorized",
    "broad_memory_write_authorized",
    "automatic_memory_write_authorized",
    "hidden_context_injection_authorized",
    "automatic_context_injection_authorized",
    "memory_truth_authority",
    "policy_override_authorized",
    "action_execution_authorized",
    "connector_write_authorized",
    "model_provider_call_authorized",
    "live_web_fetch_authorized",
    "background_autonomy_authorized",
    "hard_delete_authorized",
    "export_execution_authorized",
    "production_authority_enabled",
]


def _decision_request(**overrides: object) -> MemoryReviewDecisionRequest:
    data: dict[str, object] = {
        "reviewer_ref": "actor-ref:test-memory-learning-reviewer",
        "source_refs": ["source-ref:memory-learning:test"],
        "evidence_refs": ["evidence-ref:memory-learning:test"],
        "blocked_state_refs": list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
    }
    data.update(overrides)
    return MemoryReviewDecisionRequest(**data)


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def test_memory_learning_posture_is_backend_owned_and_denies_broad_authority(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    posture = repo.memory_workbench()["learning_posture"]

    assert posture["schema_version"] == (
        "goatcitadel-catchup-memory-learning-posture.v1"
    )
    assert posture["contract_ref"] == MEMORY_LEARNING_POSTURE_CONTRACT_REF
    assert posture["source"] == "python_core_memory_workbench_learning_posture"
    assert posture["backend_owned"] is True
    assert posture["control_center_presentation_only"] is True
    assert posture["safe_refs_only"] is True
    assert posture["raw_content_included"] is False
    assert posture["proposal_first_intake"] is True
    assert posture["review_required_before_recall"] is True
    assert set(MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS) <= set(
        posture["blocked_state_refs"]
    )
    for flag in DENIED_FLAGS:
        assert posture[flag] is False

    lifecycle_counts = posture["lifecycle_state_counts"]
    assert set(lifecycle_counts) == {
        "proposed",
        "active",
        "needs_review",
        "corrected",
        "rejected",
        "stale",
        "forgotten",
        "blocked",
    }
    assert lifecycle_counts["needs_review"] >= 1
    assert lifecycle_counts["blocked"] >= 1
    assert posture["context_pack_posture"]["context_injection_authorized"] is False
    assert posture["context_pack_posture"]["prompt_context_written"] is False
    assert posture["quality_posture"]["semantic_search_enabled"] is False
    assert posture["quality_posture"]["vector_db_enabled"] is False
    assert posture["quality_posture"]["embedding_search_enabled"] is False
    assert posture["provenance_posture"]["source_refs_required"] is True
    assert posture["provenance_posture"]["evidence_refs_required"] is True

    serialized = json.dumps(posture, sort_keys=True).lower()
    for forbidden in [
        "raw prompt",
        "raw response",
        "provider payload",
        "raw log",
        "api key",
        "/users/",
        "/home/",
        "/var/",
        "/etc/",
    ]:
        assert forbidden not in serialized


def test_memory_learning_posture_tracks_correction_rejection_and_forget_receipts(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    candidate_ref = _first_candidate_ref(repo)

    correct_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="correct",
        request=_decision_request(
            corrected_summary_ref="safe-summary-ref:memory-learning:correction",
            corrected_safe_summary="Corrected bounded safe summary for review only.",
        ),
        idempotency_key_ref="idempotency-ref:memory-learning-correct",
    )
    reject_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="reject",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:memory-learning-reject",
    )
    forget_receipt = repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="forget_request",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:memory-learning-forget",
    )

    posture = repo.memory_workbench()["learning_posture"]
    receipts = posture["receipt_posture"]

    assert correct_receipt["receipt_ref"] in receipts["corrected_receipt_refs"]
    assert reject_receipt["receipt_ref"] in receipts["rejected_receipt_refs"]
    assert forget_receipt["receipt_ref"] in receipts["forget_request_receipt_refs"]
    assert posture["lifecycle_state_counts"]["corrected"] >= 1
    assert posture["lifecycle_state_counts"]["rejected"] >= 1
    assert posture["lifecycle_state_counts"]["forgotten"] >= 1
    assert correct_receipt["context_injection_authorized"] is False
    assert reject_receipt["context_injection_authorized"] is False
    assert forget_receipt["context_injection_authorized"] is False


def test_memory_learning_posture_cli_inspects_same_backend_read_model(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "cli-founder-loop"
    cli = Path(__file__).resolve().parents[1] / "scripts/dev/uaa_founder_loop.py"

    result = subprocess.run(
        [
            sys.executable,
            str(cli),
            "--state-dir",
            str(data_dir),
            "memory-learning-posture",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    posture = payload["learning_posture"]

    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-memory-learning-posture"
    )
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert posture["contract_ref"] == MEMORY_LEARNING_POSTURE_CONTRACT_REF
    assert posture["broad_memory_write_authorized"] is False
    assert posture["automatic_context_injection_authorized"] is False
