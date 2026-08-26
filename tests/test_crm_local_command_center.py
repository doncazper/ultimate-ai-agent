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
