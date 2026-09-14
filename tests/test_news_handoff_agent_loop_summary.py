from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.control_center.agent_loop import (
    build_external_information_handling_posture,
)
from ultimate_ai_agent.core.secrets import BlockedCredentialVaultAdapter
from ultimate_ai_agent.core.secrets.vault_readiness import (
    build_provider_credential_vault_adapter_readiness,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def test_external_intake_summary_is_renderable_without_relaxing_content_guard() -> None:
    posture = build_external_information_handling_posture()
    intake = next(
        row
        for row in posture["rows"]
        if row["category_id"] == "operator_supplied_external_metadata"
    )
    assert "without retaining source bodies" in intake["safe_summary"]
    assert not re.search(
        r"raw[_ -]?(?:prompt|response|page|payload|log)", intake["safe_summary"], re.I
    )
    assert intake["raw_content_included"] is False
    assert intake["external_content_can_grant_authority"] is False


def test_built_vault_readiness_preserves_dashboard_blocked_reason() -> None:
    report = BlockedCredentialVaultAdapter().inspect_capabilities()
    original_codes = list(report.blocker_codes)
    readiness = build_provider_credential_vault_adapter_readiness(report)

    assert "VAULT_ADAPTER_NOT_SCOPED" in readiness.blocker_codes
    assert set(original_codes).issubset(readiness.blocker_codes)
    assert report.blocker_codes == original_codes
    assert readiness.adapter_available is False
    assert readiness.adapter_runtime_enabled is False
    assert readiness.raw_key_visible is False
    assert readiness.credential_material_stored_by_repo is False
    assert readiness.readiness_status == "blocked_no_approved_backend"

    report_with_reason = report.model_copy(
        update={"blocker_codes": [*original_codes, "VAULT_ADAPTER_NOT_SCOPED"]}
    )
    assert (
        build_provider_credential_vault_adapter_readiness(
            report_with_reason
        ).blocker_codes.count("VAULT_ADAPTER_NOT_SCOPED")
        == 1
    )


@pytest.mark.parametrize("status", [None, "rejected", "deferred"])
def test_unapproved_read_does_not_rebuild_generated_action(
    tmp_path, monkeypatch, status
):
    repository = FounderLoopRepository(tmp_path)
    receipts = [] if status is None else [{"status": status}]
    monkeypatch.setattr(
        repository,
        "_action_decision_receipts_for_item_ref",
        lambda *args, **kwargs: receipts,
    )

    def unexpected_payload_lookup(*args, **kwargs):
        raise AssertionError("Unapproved read rebuilt the generated action")

    monkeypatch.setattr(
        repository, "_action_payload_for_item_ref", unexpected_payload_lookup
    )
    assert (
        repository._latest_approved_action_decision_receipt_for_item_ref(
            "founder-action:q34-read"
        )
        is None
    )


@pytest.mark.parametrize(
    "posture", ["valid", "stale_revision", "missing_grant", "revoked_grant"]
)
def test_read_cost_optimization_preserves_exact_approval_validation(
    tmp_path, monkeypatch, posture
):
    repository = FounderLoopRepository(tmp_path)
    receipt = {
        "status": "approved",
        "approval_ref": "approval-ref:q34-read",
        "result_revision_ref": "revision-ref:old"
        if posture == "stale_revision"
        else "revision-ref:current",
        "approval_scope_ref": "scope-ref:q34-read",
        "idempotency_key_ref": "idempotency-ref:q34-read",
    }
    monkeypatch.setattr(
        repository,
        "_action_decision_receipts_for_item_ref",
        lambda *args, **kwargs: [receipt],
    )
    calls = []

    def lookup_action(*args, **kwargs):
        calls.append("action")
        return {"item_ref": "founder-action:q34-read"}

    monkeypatch.setattr(repository, "_action_payload_for_item_ref", lookup_action)
    monkeypatch.setattr(
        repository,
        "_action_revision_state_for_action",
        lambda *args, **kwargs: {"revision_ref": "revision-ref:current"},
    )

    def lookup_grant(**kwargs):
        calls.append("grant")
        assert kwargs["subject_ref"] == "founder-action:q34-read"
        assert kwargs["exact_scope_ref"] == "scope-ref:q34-read"
        assert kwargs["idempotency_key_ref"] == "idempotency-ref:q34-read"
        return (
            None
            if posture == "missing_grant"
            else SimpleNamespace(
                revoked_at="time-ref:revoked" if posture == "revoked_grant" else None
            )
        )

    monkeypatch.setattr(repository, "_internal_approval_grant_for_ref", lookup_grant)
    result = repository._latest_approved_action_decision_receipt_for_item_ref(
        "founder-action:q34-read"
    )
    assert result == (receipt if posture == "valid" else None)
    assert calls == (["action"] if posture == "stale_revision" else ["action", "grant"])


@pytest.mark.parametrize("limit", [1, 6])
def test_action_read_materializes_only_its_returned_window(tmp_path, monkeypatch, limit):
    import sys

    from ultimate_ai_agent.core.storage import founder_loop as storage_module

    repository = FounderLoopRepository(tmp_path)
    complete = repository.list_action_inbox(limit=100)
    expected_refs = [item["item_ref"] for item in complete[:limit]]
    assert len(complete) > limit
    original = storage_module._action_envelope_contract_payload
    materialized = []

    def observe_projection(action):
        # Source/approval construction can also call this helper. Keep that work
        # intact and count only final detail projection for the returned window.
        if sys._getframe(1).f_code is repository.list_action_inbox.__func__.__code__:
            materialized.append(action["item_ref"])
        return original(action)

    monkeypatch.setattr(
        storage_module, "_action_envelope_contract_payload", observe_projection
    )
    result = repository.list_action_inbox(limit=limit)

    # Diagnostic cost IDs and source observation times legitimately rotate;
    # order and identity remain stable across otherwise identical window reads.
    assert [item["item_ref"] for item in result] == expected_refs
    assert materialized == [item["item_ref"] for item in result]


def test_action_read_still_validates_every_returned_detail(tmp_path, monkeypatch):
    import sys

    from ultimate_ai_agent.core.storage import founder_loop as storage_module

    repository = FounderLoopRepository(tmp_path)
    original = storage_module._action_envelope_contract_payload

    def reject_detail(action):
        if sys._getframe(1).f_code is repository.list_action_inbox.__func__.__code__:
            raise ValueError("ACTION_DETAIL_VALIDATION_SENTINEL")
        return original(action)

    monkeypatch.setattr(
        storage_module, "_action_envelope_contract_payload", reject_detail
    )
    with pytest.raises(ValueError, match="ACTION_DETAIL_VALIDATION_SENTINEL"):
        repository.list_action_inbox(limit=1)


def test_agent_loop_compound_read_preserves_projection_and_reads_each_window_once(
    tmp_path, monkeypatch
):
    from copy import deepcopy

    from ultimate_ai_agent.core.control_center.agent_loop import (
        build_agent_loop_thread_read_model,
    )
    from ultimate_ai_agent.core.control_center.founder_loop import (
        FounderLoopControlCenterService,
    )

    repository = FounderLoopRepository(tmp_path)
    service = FounderLoopControlCenterService(repository)
    # Fix only the volatile diagnostic data for exact assembly parity. Each
    # consumer receives an independent copy, so mutation is also observable.
    windows = {limit: repository.today_summary(limit=limit) for limit in (6, 12, 50)}
    calls = []

    def read_window(*, limit=6):
        calls.append(limit)
        return deepcopy(windows[limit])

    monkeypatch.setattr(repository, "today_summary", read_window)
    expected = build_agent_loop_thread_read_model(
        today_summary=repository.today_summary(limit=12),
        actions_inbox=repository.actions_inbox(limit=50),
        evidence_timeline=repository.evidence_timeline(limit=50),
        memory_review=repository.memory_review(limit=20),
        proof_index=service.proof_index(),
        trust_authority_matrix=service.trust_authority_matrix(),
    )
    calls.clear()
    before = deepcopy(windows)
    actual = service.agent_loop_thread()
    assert actual == expected
    assert sorted(calls) == [6, 12, 50]
    assert windows == before

    # A subsequent read must rebuild every window and observe new source data,
    # not reuse a repository, service or cross-request projection cache.
    windows[12]["plans"][0]["title"] = "Inspect the newly reviewed local item."
    calls.clear()
    refreshed = service.agent_loop_thread()
    assert sorted(calls) == [6, 12, 50]
    assert refreshed != actual
    assert "Inspect the newly reviewed local item." in str(refreshed)


@pytest.mark.parametrize("failed_limit", [6, 12, 50])
def test_agent_loop_compound_read_propagates_required_window_failure(
    tmp_path, monkeypatch, failed_limit
):
    from ultimate_ai_agent.core.control_center.founder_loop import (
        FounderLoopControlCenterService,
    )

    repository = FounderLoopRepository(tmp_path)
    original = repository.today_summary

    def read_window(*, limit=6):
        if limit == failed_limit:
            raise ValueError("REQUIRED_WINDOW_VALIDATION_SENTINEL")
        return original(limit=limit)

    monkeypatch.setattr(repository, "today_summary", read_window)
    with pytest.raises(ValueError, match="REQUIRED_WINDOW_VALIDATION_SENTINEL"):
        FounderLoopControlCenterService(repository).agent_loop_thread()
