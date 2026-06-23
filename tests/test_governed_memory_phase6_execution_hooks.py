from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.verify_governed_cognitive_memory_spine_v1 import (
    _append_phase6_static_authority_failures,
)
from ultimate_ai_agent.core.memory import (
    ContextPackProposal,
    MEMORY_EXECUTION_HOOK_CONTRACT_REF,
    MEMORY_EXECUTION_HOOK_REQUIRED_FLOW_REFS,
    MEMORY_EXECUTION_HOOK_STATUS,
    MemoryExecutionHookContract,
    MemoryExecutionHookProposal,
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

