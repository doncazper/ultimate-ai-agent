from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api import founder_loop as founder_loop_api
from ultimate_ai_agent.api.app import app
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
from scripts.dev.uaa_founder_loop import render_memory_context_manifest_readable
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
            reviewer_ref="actor-ref:fcc-mem-016-test",
            source_refs=["source-ref:fcc-mem-016:test"],
            evidence_refs=["evidence-ref:fcc-mem-016:test"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-016-accept",
    )


@pytest.fixture(scope="module")
def memory_diagnostic_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, Any]:
    state_dir = tmp_path_factory.mktemp("fcc-memory-diagnostics") / "founder_loop"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[memory_write_authority_lease()],
    )
    _accept_first_memory_candidate(repo)
    retrieval = repo.memory_retrieval_diagnostics(limit=10)
    citation = repo.memory_citation_integrity(limit=10)
    quality = repo.memory_quality_issues(limit=10)
    maintenance = repo.memory_maintenance_runs(limit=10)
    manifest = repo.memory_context_manifest(limit=10)
    context_pack_ref = repo.memory_context_pack_proposals(limit=10)["proposals"][0][
        "context_pack_ref"
    ]
    preview = repo.memory_context_pack_preview(context_pack_ref=context_pack_ref)
    target_ref = str(repo.memory_impact_graph(limit=10)["nodes"][0]["memory_ref"])
    feedback_receipt = repo.record_memory_feedback(
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
    quality_after_feedback = repo.memory_quality_issues(limit=20)
    return {
        "repo": repo,
        "state_dir": state_dir,
        "retrieval": retrieval,
        "citation": citation,
        "quality": quality,
        "maintenance": maintenance,
        "manifest": manifest,
        "context_pack_ref": context_pack_ref,
        "preview": preview,
        "target_ref": target_ref,
        "feedback_receipt": feedback_receipt,
        "quality_after_feedback": quality_after_feedback,
    }


def test_fcc_mem_016_020_repository_read_models_are_safe(
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    retrieval = memory_diagnostic_bundle["retrieval"]
    citation = memory_diagnostic_bundle["citation"]
    quality = memory_diagnostic_bundle["quality"]
    maintenance = memory_diagnostic_bundle["maintenance"]
    manifest = memory_diagnostic_bundle["manifest"]
    context_pack_ref = memory_diagnostic_bundle["context_pack_ref"]
    preview = memory_diagnostic_bundle["preview"]

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
    governed = manifest["governed_context"]
    assert governed["contract_ref"] == (
        "contract-ref:governed-memory-context-manifest:v1"
    )
    assert governed["context_manifest_ref"] == manifest[
        "governed_context_manifest_ref"
    ]
    assert governed["context_receipt_ref"] == manifest[
        "governed_context_receipt_ref"
    ]
    assert governed["budget"]["used_tokens"] <= governed["budget"]["max_tokens"]
    assert governed["budget"]["selected_items"] == governed["selection_count"]
    assert governed["context_injection_authorized"] is False
    assert governed["memory_truth_authority"] is False
    assert governed["raw_content_persisted"] is False
    for blocked_ref in MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS:
        assert blocked_ref in manifest["blocked_state_refs"]
        assert blocked_ref in manifest["manifests"][0]["blocked_state_refs"]

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
    assert str(memory_diagnostic_bundle["state_dir"]).lower() not in serialized


def test_memory_feedback_receipt_feeds_quality_queue_without_memory_write(
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    receipt = memory_diagnostic_bundle["feedback_receipt"]
    quality = memory_diagnostic_bundle["quality_after_feedback"]

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


def test_memory_feedback_rejects_orphan_targets(
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    repo = memory_diagnostic_bundle["repo"]
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
    monkeypatch: pytest.MonkeyPatch,
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    target_ref = memory_diagnostic_bundle["target_ref"]
    client = TestClient(app)

    class ReadModelService:
        def memory_retrieval_diagnostics(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["retrieval"]

        def memory_citation_integrity(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["citation"]

        def memory_quality_issues(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["quality"]

        def memory_maintenance_runs(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["maintenance"]

        def memory_context_manifest(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["manifest"]

        def record_memory_feedback(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["feedback_receipt"]

    with monkeypatch.context() as route_patch:
        route_patch.setattr(
            founder_loop_api,
            "get_founder_loop_service",
            lambda: ReadModelService(),
        )
        for path, operation in [
            (
                "/control-center/memory/retrieval-diagnostics",
                "control_center_memory_retrieval_diagnostics",
            ),
            (
                "/control-center/memory/citation-integrity",
                "control_center_memory_citation_integrity",
            ),
            (
                "/control-center/memory/quality-issues",
                "control_center_memory_quality_issues",
            ),
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
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    state_dir = memory_diagnostic_bundle["state_dir"]

    class ContextManifestRepo:
        def memory_context_manifest(self, **_kwargs: Any) -> dict[str, Any]:
            return memory_diagnostic_bundle["manifest"]

    monkeypatch.setattr(
        "scripts.dev.uaa_founder_loop._repository",
        lambda _args: ContextManifestRepo(),
    )
    from scripts.dev import uaa_founder_loop

    assert uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "memory-context-manifest",
            "--limit",
            "5",
            "--json",
        ]
    ) == 0

    stdout = capsys.readouterr().out
    output = json.loads(stdout)
    assert output["command_ref"] == "repo-local-command:founder-loop-memory-context-manifest"
    assert output["safe_refs_only"] is True
    assert output["raw_paths_omitted"] is True
    assert output["context_manifest"]["schema_version"] == "fcc_mem_020_context_manifest.v1"
    assert str(state_dir) not in stdout


def test_founder_loop_cli_memory_context_manifest_is_readable_by_default(
    memory_diagnostic_bundle: dict[str, Any],
) -> None:
    output = render_memory_context_manifest_readable(
        memory_diagnostic_bundle["manifest"]
    )

    assert output.startswith("Memory context manifest\n")
    assert "Context injection: blocked (preview only)" in output
    assert str(memory_diagnostic_bundle["state_dir"]) not in output


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
