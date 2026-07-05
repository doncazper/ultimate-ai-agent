import json
import subprocess
import sys
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.crm import (
    CRM_LOCAL_COMMAND_CENTER_CONTRACT_REF,
    CrmLocalCommandCenterDuplicateError,
    CrmLocalMutationRequest,
    CrmLocalStore,
    build_crm_local_command_center_read_model,
    crm_local_mutation_approval_request,
    expected_crm_local_mutation_approval_ref,
)


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
    assert payload["raw_contact_details_included"] is False
    assert payload["raw_message_bodies_included"] is False
    assert payload["raw_paths_included"] is False
    assert payload["provider_payloads_included"] is False


def test_crm_local_store_seed_clear_and_redacted_export(tmp_path: Path) -> None:
    store = CrmLocalStore(tmp_path)

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
    store = CrmLocalStore(tmp_path)
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
