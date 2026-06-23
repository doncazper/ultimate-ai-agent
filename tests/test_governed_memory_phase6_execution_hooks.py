from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.verify_governed_cognitive_memory_spine_v1 import (
    _append_phase6_static_authority_failures,
)
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.rate_limits import route_rate_limit_group
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.memory import (
    ContextPackProposal,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF,
    MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE_REF,
    MEMORY_EXECUTION_HOOK_CONTRACT_REF,
    MEMORY_EXECUTION_HOOK_REQUIRED_FLOW_REFS,
    MEMORY_EXECUTION_HOOK_STATUS,
    MemoryContextPackActionProposalReceipt,
    MemoryContextPackActionProposalRequest,
    MemoryExecutionHookContract,
    MemoryExecutionHookProposal,
    MemoryReviewDecisionRequest,
    memory_context_pack_action_approval_request,
    memory_context_pack_action_scope_ref,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


def _contract_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "source_context_pack_ref": "context-pack-ref:phase6-future-safe-pack",
        "action_envelope_ref": "action-envelope-ref:phase6-future-envelope",
        "exact_approval_scope_ref": "approval-scope-ref:phase6-future-exact-scope",
        "idempotency_ref": "idempotency-ref:phase6-future-required-key",
        "rollback_ref": "rollback-ref:phase6-future-rollback",
        "safe_disable_ref": "safe-disable-ref:phase6-hooks-disabled",
        "durable_receipt_ref": "receipt-ref:phase6-future-required-receipt",
        "evidence_timeline_event_ref": "evidence-event-ref:phase6-future-event",
    }
    data.update(overrides)
    return data


def _proposal_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "proposal_ref": "proposal-ref:phase6-future-hook",
        "context_pack_ref": "context-pack-ref:phase6-future-safe-pack",
        "action_envelope_ref": "action-envelope-ref:phase6-future-envelope",
        "exact_approval_scope_ref": "approval-scope-ref:phase6-future-exact-scope",
        "idempotency_ref": "idempotency-ref:phase6-future-required-key",
        "rollback_ref": "rollback-ref:phase6-future-rollback",
        "safe_disable_ref": "safe-disable-ref:phase6-hooks-disabled",
        "durable_receipt_ref": "receipt-ref:phase6-future-required-receipt",
        "evidence_timeline_event_ref": "evidence-event-ref:phase6-future-event",
        "source_memory_record_refs": ["memory-record-ref:phase6-reviewed-record"],
        "context_pack_proposal_refs": ["proposal-ref:context-pack:phase6-safe"],
    }
    data.update(overrides)
    return data


def _context_pack_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "context_pack_ref": "context-pack-ref:proposal:phase6-safe",
        "proposal_ref": "proposal-ref:context-pack:phase6-safe",
        "purpose_ref": "purpose-ref:founder-loop:phase6-safe-review",
        "source_memory_record_refs": ["memory-record-ref:phase6-reviewed-record"],
        "l1_preview_refs": ["l1-preview-ref:phase6-safe"],
        "l2_projection_refs": ["fact-ref:phase6-safe"],
        "l3_representation_refs": ["l3-item-ref:phase6-safe"],
        "included_summary_refs": ["safe-summary-ref:phase6-safe"],
        "inclusion_reason_refs": [
            "inclusion-reason-ref:context-pack-reviewed-l1-preview"
        ],
        "source_refs": ["source-ref:manual-note:phase6-safe"],
        "evidence_refs": ["evidence-ref:phase6-safe"],
        "receipt_refs": ["receipt:memory-review:accept:phase6-safe"],
    }
    data.update(overrides)
    return data


def _decision_request() -> MemoryReviewDecisionRequest:
    return MemoryReviewDecisionRequest(
        reviewer_ref="actor-ref:phase6-1-reviewer",
        source_refs=["source-ref:manual-note:phase6-1"],
        evidence_refs=["evidence-ref:phase6-1-memory-review"],
        metadata_refs=["metadata-ref:phase6-1-internal-action"],
    )


def _repo_with_context_pack(tmp_path: Path) -> tuple[FounderLoopRepository, dict[str, object]]:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=True)
    candidate_ref = str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:phase6-1-memory-accept",
    )
    context_packs = repo.memory_context_pack_proposals()
    assert context_packs["context_pack_count"] == 1
    return repo, dict(context_packs["proposals"][0])


def _approved_action_request(
    context_pack: dict[str, object],
    *,
    approval_ref: str = "approval-ref:phase6-1-action-proposal",
) -> MemoryContextPackActionProposalRequest:
    context_pack_ref = str(context_pack["context_pack_ref"])
    scope_ref = memory_context_pack_action_scope_ref(context_pack_ref)
    request = MemoryContextPackActionProposalRequest(
        exact_approval_scope_ref=scope_ref,
        approval_ref=approval_ref,
        metadata_refs=["metadata-ref:phase6-1-action-proposal"],
    )
    approval_request = memory_context_pack_action_approval_request(
        context_pack_ref=context_pack_ref,
        context_pack_proposal_ref=str(context_pack["proposal_ref"]),
        actor_context=request.actor_context,
        risk_class=request.risk_class,
        exact_approval_scope_ref=scope_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local_test_fixture",
        approval_ref=approval_ref,
    )
    return request.model_copy(update={"approval_grants": [grant]})


def test_phase6_contract_accepts_safe_future_blocked_state() -> None:
    contract = MemoryExecutionHookContract(**_contract_data())

    assert contract.contract_ref == MEMORY_EXECUTION_HOOK_CONTRACT_REF
    assert contract.status == MEMORY_EXECUTION_HOOK_STATUS
    assert contract.contract_only is True
    assert contract.safe_refs_only is True
    assert contract.runtime_execution_authorized is False
    assert contract.runtime_route_registered is False
    assert set(MEMORY_EXECUTION_HOOK_REQUIRED_FLOW_REFS).issubset(
        contract.required_flow_refs
    )
    assert contract.blocked_states


def test_phase6_proposal_accepts_safe_proposal_only_blocked_refs() -> None:
    proposal = MemoryExecutionHookProposal(**_proposal_data())

    assert proposal.proposal_only is True
    assert proposal.execution_blocked is True
    assert proposal.action_execution_authorized is False
    assert proposal.connector_write_authorized is False
    assert proposal.provider_model_call_authorized is False
    assert proposal.production_authority_enabled is False


@pytest.mark.parametrize(
    "override",
    [
        {"runtime_execution_authorized": True},
        {"automatic_execution_authorized": True},
        {"action_execution_authorized": True},
        {"automatic_action_execution_authorized": True},
        {"automatic_memory_write_authorized": True},
        {"connector_write_authorized": True},
        {"external_crm_sync_authorized": True},
        {"account_sync_authorized": True},
        {"shell_subprocess_authorized": True},
        {"browser_automation_authorized": True},
        {"provider_model_call_authorized": True},
        {"hidden_context_injection_authorized": True},
        {"automatic_context_injection_authorized": True},
        {"context_pack_injection_authorized": True},
        {"memory_truth_authority_enabled": True},
        {"unreviewed_recall_allowed": True},
        {"broad_autonomy_enabled": True},
        {"public_beta_enabled": True},
        {"production_authority_enabled": True},
        {"runtime_route_registered": True},
        {"background_agent_enabled": True},
        {"automatic_scheduling_enabled": True},
        {"context_pack_ref": "context-pack-ref:raw-prompt"},
        {"proposal_only": False},
        {"execution_blocked": False},
    ],
)
def test_phase6_proposal_rejects_unsafe_authority_or_raw_refs(
    override: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        MemoryExecutionHookProposal(**_proposal_data(**override))


def test_context_pack_proposals_do_not_execute_actions() -> None:
    pack = ContextPackProposal(**_context_pack_data())

    assert pack.proposal_only is True
    assert pack.review_required is True
    assert pack.automatic_action_execution_authorized is False
    assert pack.phase6_execution_hooks_enabled is False

    with pytest.raises(ValidationError):
        ContextPackProposal(
            **_context_pack_data(phase6_execution_hooks_enabled=True)
        )


def test_phase6_1_receipt_rejects_execution_authority_flags() -> None:
    safe = {
        "context_pack_ref": "context-pack-ref:phase6-1-safe-pack",
        "context_pack_proposal_ref": "proposal-ref:phase6-1-safe-pack",
        "internal_action_proposal_ref": "proposal-ref:phase6-1-internal-action",
        "item_ref": "founder-action:memory-context-pack:phase6-1-safe",
        "action_envelope_ref": "action-envelope:memory-context-pack:phase6-1-safe",
        "exact_approval_scope_ref": "scope-ref:memory-context-pack-action:phase6-1-safe",
        "approval_ref": "approval-ref:phase6-1-safe",
        "approval_status": "approved",
        "receipt_ref": "receipt:memory-context-pack-action:phase6-1-safe",
        "audit_ref": "audit:memory-context-pack-action:phase6-1-safe",
        "idempotency_key_ref": "idempotency-ref:phase6-1-safe",
        "payload_fingerprint_ref": "payload-fingerprint:memory-context-pack-action:safe",
        "evidence_timeline_event_ref": "evidence-timeline:memory-context-pack-action/safe",
        "rollback_ref": "rollback-ref:memory-context-pack-action:safe",
        "safe_disable_ref": "safe-disable-ref:memory-context-pack-action:safe",
        "safe_summary": "Internal Action proposal receipt only; execution remains blocked.",
    }
    receipt = MemoryContextPackActionProposalReceipt(**safe)

    assert receipt.contract_ref == MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF
    assert receipt.action_proposal_created is True
    assert receipt.action_executed is False

    with pytest.raises(ValidationError):
        MemoryContextPackActionProposalReceipt(**{**safe, "action_executed": True})
    with pytest.raises(ValidationError):
        MemoryContextPackActionProposalReceipt(
            **{**safe, "connector_write_authorized": True}
        )


def test_phase6_1_storage_creates_internal_action_proposal_only(
    tmp_path: Path,
) -> None:
    repo, context_pack = _repo_with_context_pack(tmp_path)
    request = _approved_action_request(context_pack)
    context_pack_ref = str(context_pack["context_pack_ref"])

    receipt = repo.record_memory_context_pack_action_proposal(
        context_pack_ref=context_pack_ref,
        request=request,
        idempotency_key_ref="idempotency-ref:phase6-1-action-proposal",
    )

    assert receipt["contract_ref"] == MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_CONTRACT_REF
    assert receipt["route_ref"] == MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_ROUTE_REF
    assert receipt["context_pack_ref"] == context_pack_ref
    assert receipt["context_pack_proposal_ref"] == context_pack["proposal_ref"]
    assert receipt["internal_action_proposal_ref"].startswith(
        "proposal-ref:memory-context-pack-action:"
    )
    assert receipt["action_proposal_created"] is True
    assert receipt["action_executed"] is False
    assert receipt["connector_write_performed"] is False
    assert receipt["provider_model_call_performed"] is False
    assert receipt["context_injection_performed"] is False
    assert receipt["memory_write_performed"] is False
    assert context_pack_ref in receipt["evidence_refs"]

    action = next(
        item
        for item in repo.actions_inbox()["items"]
        if item["item_ref"] == receipt["item_ref"]
    )
    assert action["surface"] == "Memory"
    assert action["status"] == "proposed"
    assert action["action_envelope_ref"] == receipt["action_envelope_ref"]
    assert action["action_scope_ref"] == receipt["exact_approval_scope_ref"]
    assert action["action_envelope_execution_enabled"] is False
    assert receipt["receipt_ref"] in action["receipt_refs"]

    memory_packs = repo.memory_context_pack_proposals()
    memory_pack = memory_packs["proposals"][0]
    assert receipt["internal_action_proposal_ref"] in (
        memory_pack["internal_action_proposal_refs"]
    )
    assert receipt["receipt_ref"] in memory_pack["internal_action_receipt_refs"]
    assert (
        memory_pack["phase6_1_internal_action_proposal_status"]
        == "proposal_receipt_recorded_execution_blocked"
    )

    timeline = repo.today_summary()["evidence_timeline"]
    event = next(
        item
        for item in timeline
        if item["title"] == "Action proposal from Memory context pack"
    )
    assert context_pack_ref in event["history_answers"]["proposed"]["refs"]
    assert receipt["receipt_ref"] in event["history_answers"]["happened"]["refs"]
    assert event["history_answers"]["blocked"]["status"] == "blocked"


def test_phase6_1_storage_requires_exact_scope_approval_replay_and_conflict(
    tmp_path: Path,
) -> None:
    repo, context_pack = _repo_with_context_pack(tmp_path)
    context_pack_ref = str(context_pack["context_pack_ref"])

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_APPROVAL_REQUIRED",
    ):
        repo.record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=MemoryContextPackActionProposalRequest(
                exact_approval_scope_ref=memory_context_pack_action_scope_ref(
                    context_pack_ref
                ),
                approval_ref="approval-ref:missing-grant",
            ),
            idempotency_key_ref="idempotency-ref:phase6-1-missing-approval",
        )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_SCOPE_MISMATCH",
    ):
        repo.record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=MemoryContextPackActionProposalRequest(
                exact_approval_scope_ref="scope-ref:memory-context-pack-action:wrong",
                approval_ref="approval-ref:wrong-scope",
            ),
            idempotency_key_ref="idempotency-ref:phase6-1-wrong-scope",
        )

    request = _approved_action_request(context_pack)
    first = repo.record_memory_context_pack_action_proposal(
        context_pack_ref=context_pack_ref,
        request=request,
        idempotency_key_ref="idempotency-ref:phase6-1-replay",
    )
    replay = repo.record_memory_context_pack_action_proposal(
        context_pack_ref=context_pack_ref,
        request=request,
        idempotency_key_ref="idempotency-ref:phase6-1-replay",
    )
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == first["receipt_ref"]

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=_approved_action_request(
                context_pack,
                approval_ref="approval-ref:phase6-1-conflict",
            ),
            idempotency_key_ref="idempotency-ref:phase6-1-replay",
        )


def test_phase6_1_api_route_requires_idempotency_and_exact_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    repo = FounderLoopRepository.from_env()
    candidate_ref = str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=_decision_request(),
        idempotency_key_ref="idempotency-ref:phase6-1-api-memory-accept",
    )
    context_pack = repo.memory_context_pack_proposals()["proposals"][0]
    context_pack_ref = str(context_pack["context_pack_ref"])
    request = _approved_action_request(context_pack)
    payload = request.model_dump(mode="json")
    client = TestClient(app)

    missing_idempotency = client.post(
        f"/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        json=payload,
    )
    assert missing_idempotency.status_code == 428

    response = client.post(
        f"/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        json=payload,
        headers={"x-uaa-idempotency-key": "idempotency-ref:phase6-1-api"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["context_pack_ref"] == context_pack_ref
    assert data["action_executed"] is False

    replay = client.post(
        f"/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        json=payload,
        headers={"x-uaa-idempotency-key": "idempotency-ref:phase6-1-api"},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["replayed"] is True

    conflict_payload = _approved_action_request(
        context_pack,
        approval_ref="approval-ref:phase6-1-api-conflict",
    ).model_dump(mode="json")
    conflict = client.post(
        f"/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        json=conflict_payload,
        headers={"x-uaa-idempotency-key": "idempotency-ref:phase6-1-api"},
    )
    assert conflict.status_code == 409


def test_phase6_1_route_manifest_and_rate_limit_truth() -> None:
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}
    route = routes["/control-center/memory/context-packs/{context_pack_ref}/action-proposal"]

    assert route.method == "POST"
    assert route.route_classification == "mutating_requires_authority"
    assert route.idempotency_required is True
    assert route.approval_posture == "required_before_mutation_authority"
    assert route.rate_limit_targeted is True
    assert route.rate_limit_group == "memory_context_pack_action_proposal"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert "control_center_memory_context_pack_internal_action_proposal" in (
        manifest.capabilities_declared
    )
    assert "control_center_memory_context_pack_action_execution" in (
        manifest.capabilities_blocked
    )
    assert "control_center_memory_context_pack_internal_action_proposal_as_execution" in (
        manifest.capabilities_blocked
    )
    assert (
        route_rate_limit_group(
            "POST",
            "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
        )
        == "memory_context_pack_action_proposal"
    )


def test_phase6_verifier_catches_fake_memory_execution_route(tmp_path: Path) -> None:
    fake_api = tmp_path / "src/ultimate_ai_agent/api/fake_phase6.py"
    fake_api.parent.mkdir(parents=True)
    fake_api.write_text(
        '@router.post("/control-center/memory/execute")\n'
        "def execute_from_memory():\n"
        "    return {}\n",
        encoding="utf-8",
    )
    failures: list[str] = []

    _append_phase6_static_authority_failures(failures, tmp_path)

    assert any("forbidden Phase 6 runtime fragment" in failure for failure in failures)


def test_phase6_docs_keep_execution_blocked() -> None:
    root = Path(__file__).resolve().parents[1]
    spine = root / "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md"
    roadmap = root / "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md"
    truth = root / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in [spine, roadmap, truth]
    )

    assert "phase 6 remains future blocked" in combined
    assert "memoryexecutionhookcontract" in combined
    assert "contract/proof lane only" in combined
    assert "phase 6 is shipped" not in combined
    assert "memory-derived execution is enabled" not in combined
