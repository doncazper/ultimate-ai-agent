import json
import subprocess
import sys
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.crm import (
    CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
    CrmLocalAuthorityError,
    CrmLocalCommandCenterDuplicateError,
    CrmLocalMutationRequest,
    CrmLocalStore,
    build_crm_local_command_center_read_model,
    crm_local_mutation_approval_request,
    expected_crm_local_mutation_approval_ref,
)
from tests.authority_helpers import contacts_write_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def test_crm_local_command_center_read_model_preserves_authority_boundaries() -> None:
    crm = build_crm_local_command_center_read_model()
    payload = crm.model_dump(mode="json")

    assert crm.contract_ref == CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF
    assert crm.backend_owned is True
    assert crm.safe_refs_only is True
    assert len(crm.relationships) >= 2
    assert len(crm.follow_ups) >= 3
    assert len(crm.smart_lists) >= 10
    assert len(crm.reports) >= 9
    assert crm.authority_posture.connector_runtime_enabled is False
    assert crm.authority_posture.connector_write_enabled is False
    assert crm.authority_posture.send_enabled is False
    assert crm.authority_posture.calendar_write_enabled is False
    assert crm.authority_posture.provider_model_call_enabled is False
    assert crm.authority_posture.live_web_enabled is False
    assert crm.authority_posture.browser_runtime_enabled is False
    assert crm.authority_posture.production_authority_enabled is False
    assert crm.connector_read_lanes.readiness_status == (
        "blocked_missing_exact_authority"
    )
    assert crm.connector_read_lanes.disabled_by_default is True
    assert crm.connector_read_lanes.connector_runtime_enabled is False
    assert crm.connector_read_lanes.live_connector_read_performed is False
    assert crm.connector_read_lanes.external_account_auth_enabled is False
    assert crm.connector_read_lanes.background_polling_enabled is False
    assert crm.connector_read_lanes.provider_model_call_enabled is False
    assert crm.connector_read_lanes.cli_inspection_ref in crm.cli_refs
    assert len(crm.connector_read_lanes.missing_prerequisite_refs) >= 5
    calendar_lane = next(
        lane
        for lane in crm.connector_read_lanes.lanes
        if lane["lane_ref"] == "lane-ref:crm-connector:calendar-metadata-read"
    )
    assert "calendar/read AuthorityLease scope" in calendar_lane["safe_summary"]
    assert "authority is graduated" not in calendar_lane["safe_summary"]
    assert payload["raw_contact_details_included"] is False
    assert payload["raw_message_bodies_included"] is False
    assert payload["raw_paths_included"] is False
    assert payload["provider_payloads_included"] is False


def test_crm_local_store_seed_clear_and_redacted_export(tmp_path: Path) -> None:
    store = CrmLocalStore(
        tmp_path,
        active_authority_leases=[contacts_write_authority_lease()],
    )

    seeded = store.seed_demo()
    assert seeded.state == "seeded_demo"
    assert seeded.initialized is True
    assert seeded.raw_paths_omitted is True

    exported = store.export_redacted_snapshot()
    serialized = json.dumps(exported, sort_keys=True)
    assert exported["safe_refs_only"] is True
    assert exported["raw_paths_omitted"] is True
    assert str(tmp_path) not in serialized

    cleared = store.clear_demo(confirm_local_only=True)
    assert cleared.state == "cleared_demo"
    assert cleared.record_counts["relationships"] == 0


def test_crm_local_mutation_requires_exact_approval_and_replays(
    tmp_path: Path,
) -> None:
    store = CrmLocalStore(
        tmp_path,
        active_authority_leases=[contacts_write_authority_lease()],
    )
    target_ref = "follow-up-ref:crm-local:alpha:due"
    idempotency_ref = "idempotency-ref:crm-local-test-001"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="mark_follow_up_complete",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )
    approval_request = crm_local_mutation_approval_request(
        request=request,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=request.actor_context.actor_id,
        approval_ref=approval_ref,
    )

    receipt = store.record_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )
    assert receipt.approval_status == "approved"
    assert receipt.authority_decision_outcome == "ask"
    assert receipt.authority_lease_ref == "authority-lease-ref:test-contacts-write"
    assert receipt.authority_domain_ref == "authority-domain-ref:contacts"
    assert receipt.authority_capability_ref == "authority-capability-ref:write"
    assert receipt.local_mutation_performed is True
    assert receipt.send_performed is False
    assert receipt.connector_write_performed is False
    assert receipt.external_crm_write_performed is False
    assert store.read_model().follow_ups[0].status == "completed"

    replay = store.record_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    assert replay.replayed is True

    changed_request = CrmLocalMutationRequest(
        mutation_kind="update_follow_up",
        target_ref=target_ref,
        approval_ref=approval_ref,
        follow_up_status="blocked",
    )
    try:
        store.record_local_mutation(
            request=changed_request,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )
    except CrmLocalCommandCenterDuplicateError as exc:
        assert str(exc) == "CRM_LOCAL_MUTATION_IDEMPOTENCY_CONFLICT"
    else:
        raise AssertionError("expected idempotency conflict")


def test_crm_social_context_selection_uses_governed_local_mutation(
    tmp_path: Path,
) -> None:
    store = CrmLocalStore(
        tmp_path,
        active_authority_leases=[contacts_write_authority_lease()],
    )
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-select-beta"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
        safe_summary="Select the reviewed Beta relationship for Social context.",
    )
    approval_request = crm_local_mutation_approval_request(
        request=request,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=request.actor_context.actor_id,
        approval_ref=approval_ref,
    )

    receipt = store.record_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )

    assert receipt.local_mutation_performed is True
    assert {
        item.relationship_ref
        for item in store.read_model().social_relationship_projection.items
    } >= {"relationship-ref:crm-local:beta"}


def test_crm_confirmed_operator_lane_captures_exact_approval_and_lease(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-confirmed-beta"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
        safe_summary="Select reviewed Beta context with exact confirmation.",
    )

    with pytest.raises(
        CrmLocalCommandCenterError,
        match="CRM_LOCAL_MUTATION_OPERATOR_CONFIRMATION_REQUIRED",
    ):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=False,
        )

    receipt = store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert receipt.approval_status == "approved"
    assert receipt.authority_domain_ref == "authority-domain-ref:contacts"
    assert receipt.authority_capability_ref == "authority-capability-ref:write"
    assert receipt.local_mutation_performed is True
    assert receipt.connector_write_performed is False
    assert receipt.external_crm_write_performed is False
    assert {
        item.relationship_ref
        for item in store.read_model().social_relationship_projection.items
    } >= {"relationship-ref:crm-local:beta"}


def test_crm_confirmed_lane_rejects_non_human_or_unbound_operator(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError
    from ultimate_ai_agent.core.hygiene.actor_context import (
        ActorContext,
        ActorType,
        AuthoritySource,
    )

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-non-human"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )

    for actor_context in (
        ActorContext(
            actor_type=ActorType.subagent,
            actor_id="agent-ref:reviewer",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        ActorContext(
            actor_type=ActorType.human_user,
            actor_id="request-controlled-human-alias",
            authority_source=AuthoritySource.explicit_user_request,
        ),
    ):
        request = CrmLocalMutationRequest(
            actor_context=actor_context,
            mutation_kind="select_social_context",
            target_ref=target_ref,
            approval_ref=approval_ref,
        )
        with pytest.raises(
            CrmLocalCommandCenterError,
            match="CRM_LOCAL_MUTATION_HUMAN_OPERATOR_REQUIRED",
        ):
            store.record_confirmed_local_mutation(
                request=request,
                idempotency_ref=idempotency_ref,
                confirmed=True,
            )

    assert not (tmp_path / "authority").exists()


def test_crm_confirmed_lane_checks_replay_before_issuing_authority(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-replay-authority"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    initial = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )
    store.record_confirmed_local_mutation(
        request=initial,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    lease_refs_before = [lease.lease_ref for lease in lease_store.list_leases()]

    conflicting = CrmLocalMutationRequest(
        mutation_kind="clear_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )
    with pytest.raises(
        CrmLocalCommandCenterDuplicateError,
        match="CRM_LOCAL_MUTATION_IDEMPOTENCY_CONFLICT",
    ):
        store.record_confirmed_local_mutation(
            request=conflicting,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert [lease.lease_ref for lease in lease_store.list_leases()] == lease_refs_before


def test_crm_confirmed_lease_cannot_authorize_another_contacts_action(
    tmp_path: Path,
) -> None:
    from ultimate_ai_agent.core.authority import (
        AuthorityActionRequest,
        AuthorityCapability,
        AuthorityConstraintClaim,
        AuthorityConstraintKind,
        AuthorityDecisionOutcome,
        AuthorityDomain,
        AuthorityLeaseStore,
        TrustMode,
        evaluate_authority_request,
    )

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-exact-action"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )
    store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    leases = AuthorityLeaseStore(tmp_path / "authority").list_leases()
    assert len(leases) == 1
    resource_constraint = next(
        constraint
        for constraint in leases[0].authority_constraints
        if constraint.kind == AuthorityConstraintKind.resource_refs.value
    )

    decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="authority-action-ref:other-contacts-write",
            domain=AuthorityDomain.contacts,
            capability=AuthorityCapability.write,
            safe_summary="Attempt another Contacts write with copied CRM scope.",
            resource_refs=resource_constraint.allowed_refs,
            route_ref="POST /control-center/crm/local-mutations",
            lane_ref="lane-ref:crm-local-mutation",
            requested_mode=TrustMode.ask_before_changes,
            constraint_claims=[
                AuthorityConstraintClaim(
                    kind=AuthorityConstraintKind.operation_budget,
                    value=1,
                )
            ],
        ),
        leases,
    )

    assert decision.outcome == AuthorityDecisionOutcome.deny.value
    assert decision.lease_ref is None


def test_crm_confirmed_lane_supports_maximum_length_idempotency_refs(
    tmp_path: Path,
) -> None:
    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:" + ("x" * 170)
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )

    receipt = store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert approval_ref.startswith("approval-ref:crm-local:sha256:")
    for value in (
        receipt.mutation_ref,
        receipt.receipt_ref,
        receipt.audit_ref,
        receipt.before_ref,
        receipt.after_ref,
        receipt.rollback_ref,
        receipt.proof_ref,
    ):
        assert len(value) <= 191


def test_crm_local_mutations_serialize_replay_and_state_transactions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor

    store = CrmLocalStore(
        tmp_path,
        active_authority_leases=[contacts_write_authority_lease()],
    )
    target_ref = "follow-up-ref:crm-local:alpha:due"
    idempotency_ref = "idempotency-ref:crm-local-concurrent-conflict"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    requests = [
        CrmLocalMutationRequest(
            mutation_kind="mark_follow_up_complete",
            target_ref=target_ref,
            approval_ref=approval_ref,
        ),
        CrmLocalMutationRequest(
            mutation_kind="update_follow_up",
            target_ref=target_ref,
            approval_ref=approval_ref,
            follow_up_status="blocked",
        ),
    ]
    authorities: list[LocalApprovalAuthority] = []
    for request in requests:
        approval_request = crm_local_mutation_approval_request(
            request=request,
            idempotency_ref=idempotency_ref,
        )
        authority = LocalApprovalAuthority()
        authority.create_request(approval_request)
        authority.grant(
            approval_request.approval_request_id,
            approved_by_actor_id=request.actor_context.actor_id,
            approval_ref=approval_ref,
        )
        authorities.append(authority)

    original_read = store._read_state
    read_guard = threading.Lock()
    second_read_seen = threading.Event()
    read_count = 0

    def coordinated_read() -> dict[str, object]:
        nonlocal read_count
        state = original_read()
        with read_guard:
            read_index = read_count
            read_count += 1
        if read_index == 0:
            second_read_seen.wait(timeout=0.2)
        elif read_index == 1:
            second_read_seen.set()
        return state

    monkeypatch.setattr(store, "_read_state", coordinated_read)

    def mutate(index: int) -> str:
        try:
            store.record_local_mutation(
                request=requests[index],
                idempotency_ref=idempotency_ref,
                approval_authority=authorities[index],
            )
        except CrmLocalCommandCenterDuplicateError:
            return "conflict"
        return "committed"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(mutate, range(2)))

    assert sorted(outcomes) == ["committed", "conflict"]
    state = json.loads(store.snapshot_file.read_text(encoding="utf-8"))
    assert len(state["mutation_receipts"]) == 1
    assert len(state["mutation_replays"]) == 1
    assert not list(tmp_path.glob(".crm-local-snapshot-*.tmp"))


def test_crm_social_selection_validates_prospective_owner_links_before_write(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore
    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    store.seed_demo()
    before = json.loads(store.snapshot_file.read_text(encoding="utf-8"))
    before["people"][1]["relationship_refs"] = ["relationship-ref:crm-local:missing"]
    store.snapshot_file.write_text(
        json.dumps(before, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-invalid-link"
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        ),
    )

    with pytest.raises(
        CrmLocalCommandCenterError,
        match="CRM_LOCAL_MUTATION_PROSPECTIVE_STATE_INVALID",
    ):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    persisted = json.loads(store.snapshot_file.read_text(encoding="utf-8"))
    assert "social-context" not in persisted["people"][1]["tags"]
    assert persisted["mutation_receipts"] == []
    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    assert lease_store.list_leases(active_only=True) == []
    assert [lease.status for lease in lease_store.list_leases()] == ["revoked"]

    repaired = json.loads(store.snapshot_file.read_text(encoding="utf-8"))
    repaired["people"][1]["relationship_refs"] = ["relationship-ref:crm-local:beta"]
    store.snapshot_file.write_text(
        json.dumps(repaired, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )
    assert receipt.replayed is False
    leases = lease_store.list_leases()
    assert [lease.status for lease in leases] == ["revoked", "active"]
    assert leases[0].lease_ref != leases[1].lease_ref


def test_crm_confirmed_lane_revokes_lease_when_target_is_missing(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore
    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:missing"
    idempotency_ref = "idempotency-ref:crm-social-missing-target"
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        ),
    )

    with pytest.raises(
        CrmLocalCommandCenterError,
        match="CRM_LOCAL_PERSON_NOT_FOUND",
    ):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    assert lease_store.list_leases(active_only=True) == []
    assert [lease.status for lease in lease_store.list_leases()] == ["revoked"]


def test_crm_confirmed_lane_rejects_missing_opportunity_without_success_receipt(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore
    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    target_ref = "opportunity-ref:crm-local:missing"
    idempotency_ref = "idempotency-ref:crm-opportunity-missing-target"
    request = CrmLocalMutationRequest(
        mutation_kind="move_opportunity_stage",
        target_ref=target_ref,
        approval_ref=expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        ),
        stage_ref="stage-ref:crm-local:operator:qualified",
    )

    with pytest.raises(
        CrmLocalCommandCenterError,
        match="CRM_LOCAL_OPPORTUNITY_NOT_FOUND",
    ):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert store._read_state()["mutation_receipts"] == []
    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    assert lease_store.list_leases(active_only=True) == []
    assert [lease.status for lease in lease_store.list_leases()] == ["revoked"]


def test_crm_confirmed_lane_advances_past_denied_lease_receipt(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore
    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-denied-then-repaired"
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        ),
    )

    monkeypatch.setenv("UAA_AUTHORITY_LEASE_KILL_SWITCH", "1")
    with pytest.raises(
        CrmLocalCommandCenterError,
        match="CRM_LOCAL_MUTATION_EXACT_LEASE_ISSUANCE_DENIED",
    ):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    assert lease_store.list_leases() == []
    assert [item.status for item in lease_store.list_receipts()] == ["denied"]

    monkeypatch.delenv("UAA_AUTHORITY_LEASE_KILL_SWITCH")
    receipt = store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert receipt.replayed is False
    assert [item.status for item in lease_store.list_receipts()] == [
        "denied",
        "issued",
    ]
    assert len(lease_store.list_leases(active_only=True)) == 1


def test_crm_confirmed_lane_rejects_missing_relationship_targets(
    tmp_path: Path,
) -> None:
    import pytest

    from ultimate_ai_agent.core.authority import AuthorityLeaseStore
    from ultimate_ai_agent.core.crm import CrmLocalCommandCenterError

    store = CrmLocalStore(tmp_path)
    for mutation_kind, target_ref in (
        ("create_follow_up", "follow-up-ref:crm-local:new"),
        ("add_note_summary_ref", "relationship-ref:crm-local:missing"),
    ):
        idempotency_ref = f"idempotency-ref:crm-missing-relationship:{mutation_kind}"
        request = CrmLocalMutationRequest(
            mutation_kind=mutation_kind,
            target_ref=target_ref,
            relationship_ref="relationship-ref:crm-local:missing",
            approval_ref=expected_crm_local_mutation_approval_ref(
                target_ref=target_ref,
                idempotency_ref=idempotency_ref,
            ),
        )
        with pytest.raises(
            CrmLocalCommandCenterError,
            match="CRM_LOCAL_RELATIONSHIP_NOT_FOUND",
        ):
            store.record_confirmed_local_mutation(
                request=request,
                idempotency_ref=idempotency_ref,
                confirmed=True,
            )

    assert store._read_state()["mutation_receipts"] == []
    lease_store = AuthorityLeaseStore(tmp_path / "authority")
    assert lease_store.list_leases(active_only=True) == []
    assert [item.status for item in lease_store.list_leases()] == [
        "revoked",
        "revoked",
    ]


def test_crm_state_write_recovers_without_duplicate_audit_after_snapshot_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import pytest

    store = CrmLocalStore(tmp_path)
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-audit-transaction-repair"
    request = CrmLocalMutationRequest(
        mutation_kind="select_social_context",
        target_ref=target_ref,
        approval_ref=expected_crm_local_mutation_approval_ref(
            target_ref=target_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    original_replace = Path.replace
    snapshot_failure_pending = True

    def fail_first_snapshot_replace(source: Path, target: Path) -> Path:
        nonlocal snapshot_failure_pending
        if snapshot_failure_pending and Path(target) == store.snapshot_file:
            snapshot_failure_pending = False
            raise OSError("simulated snapshot replacement failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_first_snapshot_replace)

    with pytest.raises(OSError, match="simulated snapshot replacement failure"):
        store.record_confirmed_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            confirmed=True,
        )

    assert store.snapshot_file.exists() is False
    audit_events = [
        json.loads(line)
        for line in store.events_file.read_text(encoding="utf-8").splitlines()
    ]
    assert len(audit_events) == 1

    receipt = store.record_confirmed_local_mutation(
        request=request,
        idempotency_ref=idempotency_ref,
        confirmed=True,
    )

    assert store.snapshot_file.exists() is True
    assert receipt.audit_ref == audit_events[0]["event_ref"]
    repaired_events = [
        json.loads(line)
        for line in store.events_file.read_text(encoding="utf-8").splitlines()
    ]
    assert len(repaired_events) == 1


def test_crm_local_mutation_requires_contacts_write_lease(tmp_path: Path) -> None:
    store = CrmLocalStore(tmp_path)
    target_ref = "follow-up-ref:crm-local:alpha:due"
    idempotency_ref = "idempotency-ref:crm-local-authority-denied"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    request = CrmLocalMutationRequest(
        mutation_kind="mark_follow_up_complete",
        target_ref=target_ref,
        approval_ref=approval_ref,
    )
    approval_request = crm_local_mutation_approval_request(
        request=request,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=request.actor_context.actor_id,
        approval_ref=approval_ref,
    )

    try:
        store.record_local_mutation(
            request=request,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )
    except CrmLocalAuthorityError as exc:
        assert str(exc) == "CRM_LOCAL_MUTATION_AUTHORITY_DENIED"
        assert "blocked-state:crm-local-mutation-authority-lease-required" in (
            exc.reason_refs
        )
        assert (
            exc.required_refs["required_domain_ref"] == "authority-domain-ref:contacts"
        )
        assert (
            exc.required_refs["required_capability_ref"]
            == "authority-capability-ref:write"
        )
    else:
        raise AssertionError("expected CRM local mutation authority denial")

    assert store.read_model().follow_ups[0].status == "due"


def test_crm_import_preview_is_review_only_and_does_not_echo_rows(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "contacts.csv"
    csv_path.write_text(
        "name,email,notes\nExample Person,person@example.test,private note\n",
        encoding="utf-8",
    )

    preview = CrmLocalStore(tmp_path / "state").import_preview_from_csv(csv_path)
    serialized = json.dumps(preview, sort_keys=True)

    assert preview["commit_enabled"] is False
    assert preview["exact_approval_required_before_commit"] is True
    assert preview["raw_path_persisted"] is False
    assert preview["raw_contact_details_persisted"] is False
    assert "person@example.test" not in serialized
    assert "private note" not in serialized
    assert str(csv_path) not in serialized


def test_crm_cli_inspects_backend_read_model(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_crm.py"),
            "inspect-follow-ups",
            "--state-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["contract_ref"] == CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF
    assert len(payload["follow_ups"]) >= 3


def test_crm_cli_inspects_connector_read_readiness(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_crm.py"),
            "inspect-connector-read-lanes",
            "--state-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    connector = payload["connector_read_lanes"]

    assert payload["contract_ref"] == CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF
    assert connector["readiness_status"] == "blocked_missing_exact_authority"
    assert connector["disabled_by_default"] is True
    assert connector["connector_runtime_enabled"] is False
    assert connector["live_connector_read_performed"] is False
    assert connector["external_account_auth_enabled"] is False
    assert connector["background_polling_enabled"] is False
    assert connector["provider_model_call_enabled"] is False
    assert payload["authority_posture"]["connector_runtime_enabled"] is False
    assert payload["authority_posture"]["connector_write_enabled"] is False


def test_crm_cli_can_capture_one_confirmed_social_selection(tmp_path: Path) -> None:
    target_ref = "person-ref:crm-local:relationship-beta"
    idempotency_ref = "idempotency-ref:crm-social-cli-confirmed"
    approval_ref = expected_crm_local_mutation_approval_ref(
        target_ref=target_ref,
        idempotency_ref=idempotency_ref,
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_crm.py"),
            "mutate-local",
            "--state-dir",
            str(tmp_path),
            "--kind",
            "select_social_context",
            "--target-ref",
            target_ref,
            "--approval-ref",
            approval_ref,
            "--idempotency-ref",
            idempotency_ref,
            "--confirm",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["local_mutation_performed"] is True
    assert receipt["external_crm_write_performed"] is False
    selected = CrmLocalStore(tmp_path).read_model().social_relationship_projection
    assert {item.relationship_ref for item in selected.items} >= {
        "relationship-ref:crm-local:beta"
    }
