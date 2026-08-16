from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.founder_loop_product_proof import (
    FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
    FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE,
    FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS,
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER,
    FounderLoopProductProofReadModel,
)
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
)
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository

from scripts import verify_founder_loop_v1_product_proof


ROOT = Path(__file__).resolve().parents[1]


def _first_candidate_ref(repo: FounderLoopRepository) -> str:
    return str(repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"])


def _assert_product_proof(read_model: dict[str, Any]) -> None:
    parsed = FounderLoopProductProofReadModel(**read_model)
    assert parsed.contract_ref == FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
    assert parsed.source == FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE
    assert parsed.backend_owned is True
    assert parsed.local_read_model_only is True
    assert parsed.seeded_demo_safe is True
    assert parsed.safe_refs_only is True
    assert parsed.safe_summary_only is True
    assert parsed.raw_content_included is False
    assert "Start Here, Today, Action Inbox, Proof" in parsed.full_strength_goal
    assert "Backend owned safe refs" in parsed.repo_safe_scope
    assert "remain blocked" in parsed.blocked_authority_summary
    assert parsed.exact_promotion_path_refs
    assert parsed.productized_surface_order == list(
        FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
    )
    assert parsed.productized_surface_count == len(
        FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
    )
    assert [binding.surface_id for binding in parsed.productized_surface_bindings] == (
        list(FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER)
    )
    assert {
        binding.frontend_route_ref for binding in parsed.productized_surface_bindings
    } == {"/start", "/today", "/actions", "/proof", "/evidence", "/memory", "/trust", "/settings"}
    assert {
        binding.primary_proof_ref for binding in parsed.productized_surface_bindings
    } == {FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF}
    assert parsed.loop_order == list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)
    assert [step.step_id for step in parsed.steps] == list(
        FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER
    )
    assert parsed.supported_decision_actions == ["approve", "edit", "reject", "defer"]
    assert parsed.morning_briefing_refs
    assert parsed.today_refs
    assert parsed.action_inbox_refs
    assert parsed.evidence_timeline_refs
    assert parsed.evidence_event_refs
    assert parsed.memory_review_status == "candidate_available"
    assert parsed.memory_review_candidate_refs
    assert parsed.weekly_review_refs
    assert parsed.evidence_refs
    assert set(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS) <= set(
        parsed.blocked_authority_refs
    )
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "a2a_runtime_dispatch_enabled",
        "mcp_runtime_dispatch_enabled",
        "browser_execution_enabled",
        "live_web_enabled",
        "connector_write_enabled",
        "email_calendar_send_enabled",
        "crm_write_enabled",
        "account_sync_enabled",
        "shell_subprocess_execution_enabled",
        "background_autonomy_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "public_beta_claim_enabled",
        "public_release_claim_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False


def test_founder_loop_product_proof_binds_full_loop_after_receipts(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    action_receipt = repo.record_action_decision(
        action_id="setup-assistant-hardening",
        decision="defer",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:setup-assistant-hardening"
            ),
            decision_reason_ref="decision-reason-ref:product-proof-action-defer"
        ),
        idempotency_key_ref="idempotency-ref:product-proof-action-defer",
    )
    memory_receipt = repo.record_memory_review_decision(
        candidate_ref=_first_candidate_ref(repo),
        decision="defer",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:product-proof-test",
            source_refs=["source-ref:manual-note:product-proof-test"],
            evidence_refs=["evidence-ref:memory-review:product-proof-test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:product-proof-memory-defer",
    )

    today = repo.today_summary()
    briefing = repo.morning_briefing()
    proof = repo.founder_loop_product_proof()
    evidence = repo.evidence_timeline()
    weekly = repo.weekly_ceo_review()
    read_model = today["founder_loop_v1_product_proof_read_model"]

    assert today["founder_loop_v1_product_proof_contract_ref"] == (
        FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
    )
    assert briefing["founder_loop_v1_product_proof_contract_ref"] == (
        FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
    )
    assert briefing["founder_loop_v1_product_proof_read_model"] == read_model
    assert proof["founder_loop_v1_product_proof_read_model"] == read_model
    _assert_product_proof(read_model)
    assert read_model["decision_receipt_status"] == (
        "receipt_backed_decision_path_visible"
    )
    assert action_receipt["receipt_ref"] in read_model["action_decision_receipt_refs"]
    assert memory_receipt["receipt_ref"] in read_model["memory_review_receipt_refs"]
    assert action_receipt["receipt_ref"] in read_model["receipt_refs"]
    assert memory_receipt["receipt_ref"] in read_model["receipt_refs"]
    assert action_receipt["receipt_ref"] in evidence["receipt_refs"]
    assert memory_receipt["receipt_ref"] in evidence["receipt_refs"]
    assert action_receipt["receipt_ref"] in weekly["weekly_ceo_review_v1_read_model"][
        "receipt_refs"
    ]
    assert memory_receipt["receipt_ref"] in weekly["weekly_ceo_review_v1_read_model"][
        "receipt_refs"
    ]
    assert proof["read_only"] is True
    assert proof["raw_content_included"] is False
    assert proof["provider_model_call_enabled"] is False
    assert proof["production_authority_enabled"] is False


def test_founder_loop_product_proof_defaults_to_candidate_or_none(
    tmp_path: Path,
) -> None:
    seeded_repo = FounderLoopRepository(tmp_path / "seeded")
    seeded = seeded_repo.today_summary()["founder_loop_v1_product_proof_read_model"]
    _assert_product_proof(seeded)
    assert seeded["decision_receipt_status"] == "ready_no_receipt_recorded"
    assert seeded["receipt_refs"] == []

    empty_repo = FounderLoopRepository(tmp_path / "empty", seed_defaults=False)
    empty = empty_repo.today_summary()["founder_loop_v1_product_proof_read_model"]
    FounderLoopProductProofReadModel(**empty)
    assert empty["memory_review_status"] == "none"
    assert empty["memory_review_candidate_refs"] == []


def test_founder_loop_product_proof_rejects_authority_and_raw_content(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.today_summary()["founder_loop_v1_product_proof_read_model"]

    payload = dict(read_model)
    payload["provider_model_call_enabled"] = True
    with pytest.raises(ValidationError, match="provider_model_call_enabled"):
        FounderLoopProductProofReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw prompt material."
    with pytest.raises(ValidationError, match="unsafe/private content"):
        FounderLoopProductProofReadModel(**payload)

    payload = dict(read_model)
    payload["loop_order"] = list(reversed(payload["loop_order"]))
    with pytest.raises(ValidationError, match="loop order"):
        FounderLoopProductProofReadModel(**payload)

    payload = dict(read_model)
    payload["productized_route_refs"] = ["/wrong"]
    with pytest.raises(ValidationError, match="productized route refs"):
        FounderLoopProductProofReadModel(**payload)

    payload = dict(read_model)
    payload["productized_backend_route_refs"] = ["GET /wrong"]
    with pytest.raises(ValidationError, match="productized backend route refs"):
        FounderLoopProductProofReadModel(**payload)


def test_founder_loop_product_proof_cli_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.today_summary()
    state_dir = tmp_path / "founder_loop"
    recall_db = state_dir / "memory_review_recall.sqlite3"
    if recall_db.exists():
        recall_db.unlink()
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_founder_loop_v1_product_proof.py"),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["founder_loop_v1_product_proof_read_model"]
    _assert_product_proof(read_model)
    assert payload["raw_paths_omitted"] is True
    assert str(state_dir) not in result.stdout
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    assert after_files == before_files


def test_founder_loop_dev_cli_inspects_loop_spine_without_raw_paths(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    FounderLoopRepository(state_dir).today_summary()
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_founder_loop.py"),
            "--state-dir",
            str(state_dir),
            "inspect-loop-spine",
            "--limit",
            "7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-loop-spine"
    )
    assert payload["loop_order"] == list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)
    assert payload["productized_surface_order"] == list(
        FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
    )
    assert payload["productized_surface_count"] == len(
        FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
    )
    assert [
        binding["surface_id"] for binding in payload["productized_surface_bindings"]
    ] == list(FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER)
    assert [step["step_id"] for step in payload["steps"]] == list(
        FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER
    )
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["provider_model_call_enabled"] is False
    assert payload["browser_execution_enabled"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["production_authority_enabled"] is False
    assert str(state_dir) not in result.stdout
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    assert after_files == before_files

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_founder_loop.py"),
            "--state-dir",
            str(missing_state_dir),
            "inspect-loop-spine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing_result.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["steps"] == []
    assert missing_payload["loop_order"] == list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)
    assert missing_payload["productized_surface_bindings"] == []
    assert missing_payload["productized_surface_order"] == list(
        FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
    )
    assert missing_payload["raw_paths_omitted"] is True
    assert str(missing_state_dir) not in missing_result.stdout
    assert not missing_state_dir.exists()


def test_founder_loop_product_proof_static_verifier_passes() -> None:
    assert verify_founder_loop_v1_product_proof.verify() == []
