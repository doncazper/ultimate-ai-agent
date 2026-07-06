from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.memory import (
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_CITATION_INTEGRITY_CONTRACT_REF,
    MEMORY_CONTEXT_MANIFEST_CONTRACT_REF,
    MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS,
    MEMORY_CONTEXT_PACK_PREVIEW_BLOCKED_STATE_REFS,
    MEMORY_CONTEXT_PACK_PREVIEW_CONTRACT_REF,
    MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_QUALITY_CONTRACT_REF,
    MEMORY_MAINTENANCE_RUN_CONTRACT_REF,
    MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from tests.authority_helpers import (
    issue_memory_write_authority_lease,
    memory_write_authority_lease,
)


ROOT = Path(__file__).resolve().parents[1]


def _accept_first_memory_candidate(repo: FounderLoopRepository) -> dict[str, object]:
    candidate_ref = str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )
    return repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:fcc-mem-016-test",
            source_refs=["source-ref:fcc-mem-016:test"],
            evidence_refs=["evidence-ref:fcc-mem-016:test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-016-accept",
    )


def test_fcc_mem_016_020_repository_read_models_are_safe(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accept_first_memory_candidate(repo)

    retrieval = repo.memory_retrieval_diagnostics(limit=10)
    citation = repo.memory_citation_integrity(limit=10)
    quality = repo.memory_quality_issues(limit=10)
    maintenance = repo.memory_maintenance_runs(limit=10)
    manifest = repo.memory_context_manifest(limit=10)

    assert retrieval["schema_version"] == "fcc_mem_016_retrieval_diagnostics.v1"
    assert retrieval["contract_ref"] == MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF
    assert retrieval["candidate_count"] >= 1
    assert retrieval["cache_key_ref"].startswith("cache-key-ref:fcc-mem-016:")
    assert retrieval["cache_hit"] is False
    assert retrieval["context_injection_authorized"] is False
    assert retrieval["memory_write_authorized"] is False
    assert retrieval["semantic_search_enabled"] is False
    assert retrieval["model_provider_authority_allowed"] is False

    assert citation["schema_version"] == "fcc_mem_017_citation_integrity.v1"
    assert citation["contract_ref"] == MEMORY_CITATION_INTEGRITY_CONTRACT_REF
    assert citation["safe_refs_only"] is True
    assert citation["context_injection_authorized"] is False
    assert citation["memory_write_authorized"] is False
    assert citation["truth_authority_enabled"] is False
    assert citation["proposal_count"] >= 1
    assert citation["blocked_proposal_count"] == 0

    assert quality["schema_version"] == "fcc_mem_018_feedback_quality_queue.v1"
    assert quality["contract_ref"] == MEMORY_FEEDBACK_QUALITY_CONTRACT_REF
    assert quality["proposal_only"] is True
    assert quality["memory_write_authorized"] is False
    assert quality["automatic_memory_write_authorized"] is False

    assert maintenance["schema_version"] == "fcc_mem_019_proposal_only_maintenance_run.v1"
    assert maintenance["contract_ref"] == MEMORY_MAINTENANCE_RUN_CONTRACT_REF
    assert maintenance["proposal_only"] is True
    assert maintenance["auto_merge_authorized"] is False
    assert maintenance["auto_forget_authorized"] is False
    assert maintenance["automatic_memory_write_authorized"] is False

    assert manifest["schema_version"] == "fcc_mem_020_context_manifest.v1"
    assert manifest["contract_ref"] == MEMORY_CONTEXT_MANIFEST_CONTRACT_REF
    assert manifest["proposal_only"] is True
    assert manifest["context_injection_authorized"] is False
    assert manifest["hidden_prompt_context_authorized"] is False
    assert manifest["runtime_prompt_context_injection_authorized"] is False
    assert manifest["live_model_context_injection_authorized"] is False
    assert manifest["automatic_context_injection_authorized"] is False
    assert manifest["automatic_memory_inclusion_authorized"] is False
    assert manifest["memory_write_authorized"] is False
    assert manifest["connector_derived_context_injection_authorized"] is False
    assert manifest["browser_web_derived_context_injection_authorized"] is False
    assert manifest["shell_file_derived_context_injection_authorized"] is False
    assert manifest["raw_payload_persistence_enabled"] is False
    assert manifest["provider_prompt_context_injection_authorized"] is False
    assert manifest["broad_autonomy_authorized"] is False
    assert manifest["public_beta_claim_authorized"] is False
    assert manifest["public_distribution_claim_authorized"] is False
    assert manifest["production_readiness_claim_authorized"] is False
    for blocked_ref in MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS:
        assert blocked_ref in manifest["blocked_state_refs"]
        assert blocked_ref in manifest["manifests"][0]["blocked_state_refs"]

    context_pack_ref = repo.memory_context_pack_proposals(limit=10)["proposals"][0][
        "context_pack_ref"
    ]
    preview = repo.memory_context_pack_preview(context_pack_ref=context_pack_ref)
    assert preview["schema_version"] == "fcc_mem_020_context_pack_preview.v1"
    assert preview["contract_ref"] == MEMORY_CONTEXT_PACK_PREVIEW_CONTRACT_REF
    assert preview["context_pack_ref"] == context_pack_ref
    assert preview["context_manifest_ref"] == manifest["manifests"][0][
        "context_manifest_ref"
    ]
    assert preview["context_pack_preview_ref"].startswith(
        "context-pack-preview-ref:fcc-mem-020:"
    )
    assert preview["source_memory_record_refs"]
    assert preview["memory_candidate_refs"]
    assert preview["l1_preview_refs"]
    assert preview["l2_projection_refs"]
    assert preview["l3_representation_refs"]
    assert preview["included_summary_refs"]
    assert preview["evidence_refs"]
    assert preview["receipt_refs"]
    assert preview["proof_refs"]
    assert preview["audit_refs"]
    assert preview["safe_refs_only"] is True
    assert preview["read_only_preview"] is True
    assert preview["preview_only"] is True
    assert preview["approval_required_before_use"] is True
    assert preview["live_injection_status"] == "blocked_planned"
    assert preview["context_injection_authorized"] is False
    assert preview["runtime_prompt_context_injection_authorized"] is False
    assert preview["live_model_context_injection_authorized"] is False
    assert preview["automatic_context_injection_authorized"] is False
    assert preview["automatic_memory_inclusion_authorized"] is False
    assert preview["memory_write_authorized"] is False
    assert preview["action_execution_authorized"] is False
    assert preview["connector_write_authorized"] is False
    assert preview["model_provider_authority_allowed"] is False
    assert preview["raw_payload_persistence_enabled"] is False
    assert preview["production_authority_enabled"] is False
    for blocked_ref in MEMORY_CONTEXT_PACK_PREVIEW_BLOCKED_STATE_REFS:
        assert blocked_ref in preview["blocked_state_refs"]

    serialized = json.dumps(
        {
            "retrieval": retrieval,
            "citation": citation,
            "quality": quality,
            "maintenance": maintenance,
            "manifest": manifest,
            "preview": preview,
        }
    ).lower()
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert str(tmp_path).lower() not in serialized


def test_memory_feedback_receipt_feeds_quality_queue_without_memory_write(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accept_first_memory_candidate(repo)
    target_ref = str(repo.memory_impact_graph(limit=10)["nodes"][0]["memory_ref"])

    receipt = repo.record_memory_feedback(
        request=MemoryFeedbackRequest(
            target_ref=target_ref,
            target_kind="impact_graph_node",
            feedback_kind="stale",
            reviewer_ref="actor-ref:fcc-mem-018-test",
            reason_refs=["reason-ref:fcc-mem-018:operator-stale"],
            blocked_state_refs=list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-018-feedback",
    )
    quality = repo.memory_quality_issues(limit=20)

    assert receipt["schema_version"] == "fcc_mem_018_memory_feedback_receipt.v1"
    assert receipt["memory_write_performed"] is False
    assert receipt["automatic_memory_write_authorized"] is False
    assert receipt["context_injection_authorized"] is False
    assert quality["feedback_count"] == 1
    assert receipt["receipt_ref"] in quality["feedback_receipt_refs"]
    assert any(
        receipt["receipt_ref"] in issue["feedback_receipt_refs"]
        for issue in quality["issues"]
    )


def test_memory_feedback_rejects_orphan_targets(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    with pytest.raises(Exception, match="FOUNDER_LOOP_MEMORY_FEEDBACK_TARGET_NOT_FOUND"):
        repo.record_memory_feedback(
            request=MemoryFeedbackRequest(
                target_ref="memory-ref:fcc-mem-018:missing",
                target_kind="memory_candidate",
                feedback_kind="wrong",
                reason_refs=["reason-ref:fcc-mem-018:missing-target"],
                blocked_state_refs=list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
            ),
            idempotency_key_ref="idempotency-ref:fcc-mem-018-missing-target",
        )


def test_control_center_memory_diagnostic_routes_and_feedback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "api_state"))
    authority_state_dir = tmp_path / "authority"
    issue_memory_write_authority_lease(authority_state_dir)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    repo = FounderLoopRepository.from_env()
    _accept_first_memory_candidate(repo)
    target_ref = str(repo.memory_impact_graph(limit=10)["nodes"][0]["memory_ref"])
    client = TestClient(app)

    for path, operation in [
        (
            "/control-center/memory/retrieval-diagnostics",
            "control_center_memory_retrieval_diagnostics",
        ),
        (
            "/control-center/memory/citation-integrity",
            "control_center_memory_citation_integrity",
        ),
        ("/control-center/memory/quality-issues", "control_center_memory_quality_issues"),
        (
            "/control-center/memory/maintenance-runs",
            "control_center_memory_maintenance_runs",
        ),
        (
            "/control-center/memory/context-manifest",
            "control_center_memory_context_manifest",
        ),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert "safe_refs_only" in body["redactions_applied"]
        assert body["data"]["safe_refs_only"] is True

    feedback_response = client.post(
        "/control-center/memory/feedback",
        json={
            "target_ref": target_ref,
            "target_kind": "impact_graph_node",
            "feedback_kind": "useful",
            "reviewer_ref": "actor-ref:fcc-mem-018-api-test",
            "reason_refs": ["reason-ref:fcc-mem-018:api-useful"],
            "blocked_state_refs": list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:fcc-mem-018-api"},
    )

    assert feedback_response.status_code == 200
    body = feedback_response.json()
    assert body["operation"] == "control_center_memory_feedback"
    assert body["data"]["memory_write_performed"] is False
    assert body["data"]["context_injection_authorized"] is False


def test_founder_loop_cli_memory_context_manifest_omits_raw_paths(
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
            "memory-context-manifest",
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
    assert output["command_ref"] == "repo-local-command:founder-loop-memory-context-manifest"
    assert output["safe_refs_only"] is True
    assert output["raw_paths_omitted"] is True
    assert output["context_manifest"]["schema_version"] == "fcc_mem_020_context_manifest.v1"
    assert str(state_dir) not in result.stdout


def test_founder_loop_cli_memory_context_pack_preview_omits_raw_paths(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "cli_preview_state"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accept_first_memory_candidate(repo)
    context_pack_ref = repo.memory_context_pack_proposals(limit=5)["proposals"][0][
        "context_pack_ref"
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "memory-context-pack-preview",
            "--context-pack-ref",
            context_pack_ref,
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    output = json.loads(result.stdout)
    assert (
        output["command_ref"]
        == "repo-local-command:founder-loop-memory-context-pack-preview"
    )
    assert output["safe_refs_only"] is True
    assert output["raw_paths_omitted"] is True
    assert (
        output["context_pack_preview"]["schema_version"]
        == "fcc_mem_020_context_pack_preview.v1"
    )
    assert output["context_pack_preview"]["context_pack_ref"] == context_pack_ref
    assert output["context_pack_preview"]["context_injection_authorized"] is False
    assert output["context_pack_preview"]["memory_write_authorized"] is False
    assert str(state_dir) not in result.stdout

    denied = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "memory-context-pack-preview",
            "--context-pack-ref",
            "raw_prompt",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert denied.returncode == 1
    denied_output = json.loads(denied.stdout)
    assert (
        denied_output["error_ref"]
        == "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_REF_DENIED"
    )
