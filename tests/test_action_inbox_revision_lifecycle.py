from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.dev import uaa_founder_loop
from tests.authority_helpers import (
    issue_workspace_write_authority_lease,
    workspace_write_authority_lease,
)
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.control_center.action_decisions import (
    FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF,
    FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
    FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM,
    FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF,
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.storage import founder_loop as founder_loop_storage
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopActionRecord,
    FounderLoopActionRevisionConflict,
)


ACTION_ID = "local-task-create-scorecard"
ITEM_REF = "founder-action:local-task-create-scorecard"


def _repo(tmp_path: Path) -> FounderLoopRepository:
    return FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[workspace_write_authority_lease()],
    )


def _item(repo: FounderLoopRepository) -> dict[str, object]:
    return next(
        item for item in repo.list_action_inbox() if item["item_ref"] == ITEM_REF
    )


def _request(revision_ref: str, **updates: object) -> FounderLoopActionDecisionRequest:
    return FounderLoopActionDecisionRequest(
        expected_revision_ref=revision_ref,
        decision_reason_ref=str(
            updates.pop(
                "decision_reason_ref",
                "decision-reason-ref:test-action-revision-lifecycle",
            )
        ),
        **updates,
    )


def _stored_action_record(repo: FounderLoopRepository) -> FounderLoopActionRecord:
    payload = repo._action_payload_for_item_ref(ITEM_REF, include_generated=False)
    assert payload is not None
    return FounderLoopActionRecord.model_validate(
        {
            field_name: payload[field_name]
            for field_name in FounderLoopActionRecord.model_fields
            if field_name in payload
        }
    )


def _approve(repo: FounderLoopRepository, *, key: str) -> dict[str, object]:
    item = _item(repo)
    return repo.record_action_decision(
        action_id=ACTION_ID,
        decision="approve",
        request=_request(str(item["action_revision_ref"])),
        idempotency_key_ref=key,
    )


def test_action_read_model_exposes_authoritative_revision_contract(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    item = _item(repo)
    envelope = item["approval_envelope"]

    assert item["action_revision_contract_ref"] == (
        FOUNDER_LOOP_ACTION_REVISION_CONTRACT_REF
    )
    assert item["action_generation"] == 1
    assert item["action_generation_ref"].startswith("action-generation:")
    assert item["action_revision_ref"].startswith("action-revision:")
    assert item["expected_revision_ref"] == item["action_revision_ref"]
    assert item["action_revision_decision_eligible"] is True
    assert envelope["revision_ref"] == item["action_revision_ref"]
    assert envelope["expected_revision_required"] is True
    generated = next(
        candidate
        for candidate in repo.list_action_inbox(limit=200)
        if candidate.get("action_kind") == "task_decomposition_proposal"
    )
    assert generated["action_revision_decision_eligible"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"expected_revision_ref": ""},
        {"expected_revision_ref": "revision ref with spaces"},
    ],
)
def test_action_decision_request_rejects_missing_empty_or_malformed_revision(
    payload: dict[str, str],
) -> None:
    with pytest.raises(ValidationError):
        FounderLoopActionDecisionRequest(**payload)


@pytest.mark.parametrize(
    "body",
    [
        {"decision_reason_ref": "decision-reason-ref:test-missing-revision"},
        {
            "expected_revision_ref": "",
            "decision_reason_ref": "decision-reason-ref:test-empty-revision",
        },
        {
            "expected_revision_ref": "revision ref with spaces",
            "decision_reason_ref": "decision-reason-ref:test-malformed-revision",
        },
    ],
)
def test_action_decision_api_rejects_missing_empty_or_malformed_revision(
    body: dict[str, str],
) -> None:
    response = TestClient(app).post(
        f"/control-center/actions/{ACTION_ID}/cancel",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-invalid-revision"},
    )
    assert response.status_code == 422


def test_edit_advances_revision_and_atomically_invalidates_earlier_approval(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    first_approval = _approve(
        repo, key="idempotency-ref:test-revision-edit-approve-first"
    )
    second_approval = _approve(
        repo, key="idempotency-ref:test-revision-edit-approve-second"
    )
    current = _item(repo)

    edited = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="edit",
        request=_request(
            str(current["action_revision_ref"]),
            edited_envelope_ref="approval-envelope:test-action-revision-v2",
        ),
        idempotency_key_ref="idempotency-ref:test-revision-edit",
    )

    assert edited["status"] == "edited"
    assert edited["revision_advanced"] is True
    assert edited["result_generation"] == edited["generation"] + 1
    assert set(edited["invalidated_approval_refs"]) == {
        first_approval["approval_ref"],
        second_approval["approval_ref"],
    }
    assert edited["invalidated_approval_count"] == 2
    assert repo._latest_approved_action_decision_receipt_for_item_ref(ITEM_REF) is None
    refreshed = _item(repo)
    assert refreshed["action_revision_ref"] == edited["result_revision_ref"]

    with pytest.raises(FounderLoopActionRevisionConflict) as stale:
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(str(first_approval["result_revision_ref"])),
            idempotency_key_ref="idempotency-ref:test-stale-after-edit",
        )
    assert stale.value.current_revision_ref == edited["result_revision_ref"]


def test_cancel_is_idempotent_invalidates_approval_and_distinguishes_conflict(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-revision-cancel-approve")
    revision_ref = str(_item(repo)["action_revision_ref"])
    request = _request(revision_ref)

    cancelled = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="cancel",
        request=request,
        idempotency_key_ref="idempotency-ref:test-revision-cancel",
    )
    replay = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="cancel",
        request=request,
        idempotency_key_ref="idempotency-ref:test-revision-cancel",
    )

    assert cancelled["status"] == "cancelled"
    assert cancelled["revision_advanced"] is True
    assert cancelled["invalidated_approval_refs"] == [approval["approval_ref"]]
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == cancelled["receipt_ref"]

    with pytest.raises(FounderLoopStorageDuplicateError):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="cancel",
            request=_request(
                revision_ref,
                decision_reason_ref="decision-reason-ref:test-cancel-changed",
            ),
            idempotency_key_ref="idempotency-ref:test-revision-cancel",
        )
    with pytest.raises(FounderLoopActionRevisionConflict):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(revision_ref),
            idempotency_key_ref="idempotency-ref:test-stale-after-cancel",
        )


def test_revision_binding_receipt_covers_scope_route_adapter_deadline_and_authority(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    receipt = _approve(repo, key="idempotency-ref:test-revision-bindings")

    assert receipt["expected_revision_ref"] == receipt["revision_ref"]
    assert receipt["approval_scope_ref"].startswith(
        "approval-scope:action-inbox-revision:"
    )
    assert receipt["decision_route_ref"].endswith("/approve")
    assert receipt["decision_route_binding_ref"].endswith(":approve")
    assert receipt["decision_adapter_ref"] == FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF
    assert receipt["decision_deadline_ref"].startswith(
        "deadline-ref:action-inbox-decision:"
    )
    assert receipt["authority_input_refs"] == list(
        FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS
    )


@pytest.mark.parametrize(
    "binding_kind",
    [
        "scope",
        "route",
        "adapter",
        "deadline",
        "authority",
        "rollback",
        "safe_disable",
    ],
)
def test_revision_binding_changes_make_prior_approval_stale(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    binding_kind: str,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key=f"idempotency-ref:test-binding-{binding_kind}")
    approved_revision_ref = str(approval["result_revision_ref"])

    if binding_kind == "scope":
        with repo._connect() as conn:
            conn.execute(
                "UPDATE action_inbox SET approval_envelope_ref = ? WHERE item_ref = ?",
                ("approval-envelope:substituted-scope", ITEM_REF),
            )
    elif binding_kind == "route":
        monkeypatch.setattr(
            founder_loop_storage,
            "FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS",
            (
                *founder_loop_storage.FOUNDER_LOOP_ACTION_DECISION_ROUTE_REFS,
                "POST /control-center/actions/{action_id}/substituted",
            ),
        )
    elif binding_kind == "adapter":
        monkeypatch.setattr(
            founder_loop_storage,
            "FOUNDER_LOOP_ACTION_DECISION_ADAPTER_REF",
            "adapter-ref:python-core:substituted-action-decisions",
        )
    elif binding_kind == "deadline":
        monkeypatch.setattr(
            founder_loop_storage,
            "action_decision_deadline_ref",
            lambda _item_ref, generation, _expiry=None: (
                f"deadline-ref:action-inbox-decision:substituted:{generation:08d}"
            ),
        )
    elif binding_kind == "authority":
        monkeypatch.setattr(
            founder_loop_storage,
            "FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS",
            (
                *FOUNDER_LOOP_ACTION_DECISION_AUTHORITY_INPUT_REFS,
                "authority-input-ref:substituted",
            ),
        )
    else:
        with repo._connect() as conn:
            column = (
                "rollback_ref" if binding_kind == "rollback" else "safe_disable_ref"
            )
            conn.execute(
                f"UPDATE action_inbox SET {column} = ? WHERE item_ref = ?",
                (f"{binding_kind}-ref:substituted-recovery-control", ITEM_REF),
            )

    current = repo.action_revision(ACTION_ID)
    assert current["revision_ref"] != approved_revision_ref
    assert repo._latest_approved_action_decision_receipt_for_item_ref(ITEM_REF) is None
    with pytest.raises(FounderLoopActionRevisionConflict):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(approved_revision_ref),
            idempotency_key_ref=f"idempotency-ref:test-binding-stale-{binding_kind}",
        )


@pytest.mark.parametrize(
    "updates",
    [
        {"title": "Reviewed Action title changed"},
        {"safe_summary": "Reviewed safe summary changed without raw content."},
        {
            "estimated_cost_usd": 1.25,
            "max_approved_cost_usd": 2.0,
            "cost_estimate_ref": "cost-estimate-ref:test-reviewed-posture",
        },
        {
            "provider_ref": "provider-ref:test-reviewed-posture",
            "model_profile_ref": "model-profile-ref:test-reviewed-posture",
        },
    ],
)
def test_reviewed_content_cost_and_provider_drift_invalidates_revision(
    tmp_path: Path,
    updates: dict[str, object],
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-reviewed-drift-approve")
    approved_revision = str(approval["result_revision_ref"])
    approved_generation = int(approval["result_generation"])

    repo.upsert_action(_stored_action_record(repo).model_copy(update=updates))

    current = _item(repo)
    assert current["action_revision_ref"] != approved_revision
    assert current["action_generation"] == approved_generation + 1
    assert repo._latest_approved_action_decision_receipt_for_item_ref(ITEM_REF) is None


def test_source_revision_advance_is_persisted_and_resists_aba_restore(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-source-aba-approve")
    original = _stored_action_record(repo)
    approved_revision = str(approval["result_revision_ref"])
    approved_generation = int(approval["result_generation"])

    repo.upsert_action(
        original.model_copy(update={"title": "Transient reviewed Action title"})
    )
    transient = _item(repo)
    repo.upsert_action(original)
    restored = _item(repo)

    assert transient["action_generation"] == approved_generation + 1
    assert restored["action_generation"] == approved_generation + 2
    assert restored["action_revision_ref"] != approved_revision
    assert restored["action_revision_ref"] != transient["action_revision_ref"]
    assert repo._latest_approved_action_decision_receipt_for_item_ref(ITEM_REF) is None
    with repo._connect() as conn:
        persisted = json.loads(
            conn.execute(
                "SELECT state_json FROM action_revision_state WHERE item_ref = ?",
                (ITEM_REF,),
            ).fetchone()[0]
        )
    assert persisted["generation"] == approved_generation + 2
    assert persisted["revision_ref"] == restored["action_revision_ref"]


def test_changed_payload_cannot_reuse_an_earlier_approval_scope(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-payload-original")
    current_revision_ref = str(_item(repo)["action_revision_ref"])

    substituted = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="approve",
        request=_request(
            current_revision_ref,
            approval_ref=str(approval["approval_ref"]),
            decision_reason_ref="decision-reason-ref:test-payload-substituted",
        ),
        idempotency_key_ref="idempotency-ref:test-payload-substituted",
    )

    assert substituted["status"] == "blocked"
    assert substituted["approval_status"] != "approved"


def test_action_decision_partial_failure_rolls_back_revision_receipt_and_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    initial_revision = str(_item(repo)["action_revision_ref"])

    def fail_projection(**_: object) -> None:
        raise RuntimeError("projection-write-failed")

    monkeypatch.setattr(
        repo, "_update_action_projection_after_decision", fail_projection
    )
    with pytest.raises(RuntimeError, match="projection-write-failed"):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="approve",
            request=_request(initial_revision),
            idempotency_key_ref="idempotency-ref:test-atomic-rollback",
        )

    assert repo.latest_action_receipt(ACTION_ID) is None
    assert _item(repo)["action_revision_ref"] == initial_revision
    with repo._connect() as conn:
        persisted_revision = json.loads(
            conn.execute(
                "SELECT state_json FROM action_revision_state WHERE item_ref = ?",
                (ITEM_REF,),
            ).fetchone()[0]
        )
        assert persisted_revision["revision_ref"] == initial_revision
        assert conn.execute("SELECT COUNT(*) FROM action_receipts").fetchone()[0] == 0
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM founder_loop_internal_approval_grants"
            ).fetchone()[0]
            == 0
        )


def test_cancel_partial_failure_preserves_prior_revision_and_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-cancel-rollback-approve")
    initial_revision = str(_item(repo)["action_revision_ref"])

    def fail_projection(**_: object) -> None:
        raise RuntimeError("cancel-projection-write-failed")

    monkeypatch.setattr(
        repo, "_update_action_projection_after_decision", fail_projection
    )
    with pytest.raises(RuntimeError, match="cancel-projection-write-failed"):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="cancel",
            request=_request(initial_revision),
            idempotency_key_ref="idempotency-ref:test-cancel-atomic-rollback",
        )

    assert _item(repo)["action_revision_ref"] == initial_revision
    assert (
        repo.latest_action_receipt(ACTION_ID)["receipt_ref"] == approval["receipt_ref"]
    )
    assert (
        repo._latest_approved_action_decision_receipt_for_item_ref(ITEM_REF)[
            "approval_ref"
        ]
        == approval["approval_ref"]
    )


def test_cancel_openapi_contract_requires_revision_and_keeps_stable_operation_id() -> (
    None
):
    schema = app.openapi()
    for decision in ("approve", "edit", "reject", "defer", "cancel"):
        operation = schema["paths"][
            f"/control-center/actions/{{action_id}}/{decision}"
        ]["post"]
        request_schema_ref = operation["requestBody"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        request_schema_name = request_schema_ref.rsplit("/", 1)[-1]
        conflict_schema_ref = operation["responses"]["409"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        conflict_schema_name = conflict_schema_ref.rsplit("/", 1)[-1]

        assert (
            "expected_revision_ref"
            in schema["components"]["schemas"][request_schema_name]["required"]
        )
        assert conflict_schema_name == "FounderLoopActionDecisionConflictResponse"
    conflict_detail_schema = schema["components"]["schemas"][
        "FounderLoopActionDecisionConflictResponse"
    ]["properties"]["detail"]
    assert {
        ref.rsplit("/", 1)[-1]
        for ref in (variant["$ref"] for variant in conflict_detail_schema["anyOf"])
    } == {
        "FounderLoopActionRevisionConflictDetail",
        "FounderLoopActionIdempotencyConflictDetail",
        "FounderLoopActionReceiptCapacityConflictDetail",
        "FounderLoopActionStateConflictDetail",
    }
    assert (
        schema["components"]["schemas"]["FounderLoopActionRevisionConflictDetail"][
            "properties"
        ]["refresh_required"]["const"]
        is True
    )
    assert (
        schema["paths"]["/control-center/actions/{action_id}/cancel"]["post"][
            "operationId"
        ]
        == "post_control_center_actions_action_id_cancel"
    )


def test_authoritative_expiry_changes_revision_and_expired_decision_is_denied(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    initial_revision = str(_item(repo)["action_revision_ref"])
    expired_at = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    with repo._connect() as conn:
        conn.execute(
            "UPDATE action_inbox SET expires_at = ? WHERE item_ref = ?",
            (expired_at, ITEM_REF),
        )

    refreshed = _item(repo)
    assert refreshed["action_revision_ref"] != initial_revision
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_DECISION_DEADLINE_EXPIRED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(str(refreshed["action_revision_ref"])),
            idempotency_key_ref="idempotency-ref:test-expired-decision",
        )


def test_malformed_nonempty_deadline_fails_closed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with repo._connect() as conn:
        conn.execute(
            "UPDATE action_inbox SET expires_at = ? WHERE item_ref = ?",
            ("malformed-deadline", ITEM_REF),
        )
    revision = repo.action_revision(ACTION_ID)

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_DECISION_DEADLINE_EXPIRED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(str(revision["revision_ref"])),
            idempotency_key_ref="idempotency-ref:test-malformed-deadline",
        )


def test_historical_deadline_marker_is_normalized_during_upgrade(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    initial_generation = int(_item(repo)["action_generation"])
    with repo._connect() as conn:
        conn.execute(
            "UPDATE action_inbox SET expires_at = ? WHERE item_ref = ?",
            ("review_required_before_local_task_commit", ITEM_REF),
        )
    marker_generation = int(_item(repo)["action_generation"])
    assert marker_generation == initial_generation + 1

    reopened = _repo(tmp_path)
    refreshed = _item(reopened)
    assert refreshed["expires_at"] is None
    assert int(refreshed["action_generation"]) == marker_generation + 1

    receipt = reopened.record_action_decision(
        action_id=ACTION_ID,
        decision="reject",
        request=_request(str(refreshed["action_revision_ref"])),
        idempotency_key_ref="idempotency-ref:test-historical-deadline-upgrade",
    )
    assert receipt["status"] == "rejected"


@pytest.mark.parametrize("decision", ["reject", "defer"])
def test_successful_decisions_advance_revision_and_block_cross_client_overwrite(
    tmp_path: Path,
    decision: str,
) -> None:
    repo = _repo(tmp_path)
    displayed_revision = str(_item(repo)["action_revision_ref"])
    updates = (
        {"defer_until_ref": "defer-until-ref:test-cross-client"}
        if decision == "defer"
        else {}
    )
    receipt = repo.record_action_decision(
        action_id=ACTION_ID,
        decision=decision,
        request=_request(displayed_revision, **updates),
        idempotency_key_ref=f"idempotency-ref:test-cross-client-{decision}",
    )

    assert (
        receipt["status"]
        == {
            "reject": "rejected",
            "defer": "deferred",
        }[decision]
    )
    assert receipt["revision_advanced"] is True
    assert receipt["result_generation"] == receipt["generation"] + 1
    with pytest.raises(FounderLoopActionRevisionConflict):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="approve",
            request=_request(displayed_revision),
            idempotency_key_ref=f"idempotency-ref:test-stale-after-{decision}",
        )


def test_non_local_approve_advances_revision_and_blocks_stale_overwrite(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    action_id = "setup-assistant-hardening"
    item_ref = f"founder-action:{action_id}"
    item = next(
        item for item in repo.list_action_inbox() if item["item_ref"] == item_ref
    )
    displayed_revision = str(item["action_revision_ref"])

    receipt = repo.record_action_decision(
        action_id=action_id,
        decision="approve",
        request=_request(displayed_revision),
        idempotency_key_ref="idempotency-ref:test-non-local-approve",
    )

    assert receipt["status"] == "approved"
    assert receipt["revision_advanced"] is True
    with pytest.raises(FounderLoopActionRevisionConflict):
        repo.record_action_decision(
            action_id=action_id,
            decision="reject",
            request=_request(displayed_revision),
            idempotency_key_ref="idempotency-ref:test-stale-non-local-approve",
        )


def test_generated_approval_ref_is_stable_and_schema_bounded(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    revision_ref = str(_item(repo)["action_revision_ref"])
    key_ref = "idempotency-ref:test-max-length:" + "x" * 220

    receipt = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="approve",
        request=_request(revision_ref),
        idempotency_key_ref=key_ref,
    )
    replay = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="approve",
        request=_request(revision_ref),
        idempotency_key_ref=key_ref,
    )

    approval_ref = str(receipt["approval_ref"])
    assert approval_ref.startswith("approval-ref:founder-loop-action:")
    assert len(approval_ref) <= 160
    assert "x" * 20 not in approval_ref
    assert replay["approval_ref"] == approval_ref
    assert replay["replayed"] is True


def test_action_is_read_under_the_decision_write_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    revision_ref = str(_item(repo)["action_revision_ref"])
    original = repo._action_payload_for_item_ref
    observed_transaction_reads: list[bool] = []

    def observe_read(
        item_ref: str,
        *,
        conn=None,
        include_generated: bool = True,
    ):
        observed_transaction_reads.append(conn is not None)
        return original(
            item_ref,
            conn=conn,
            include_generated=include_generated,
        )

    monkeypatch.setattr(repo, "_action_payload_for_item_ref", observe_read)
    repo.record_action_decision(
        action_id=ACTION_ID,
        decision="reject",
        request=_request(revision_ref),
        idempotency_key_ref="idempotency-ref:test-locked-action-read",
    )

    assert observed_transaction_reads
    assert observed_transaction_reads[0] is True


def test_generated_proposal_only_action_cannot_record_cancel_receipt(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    generated = next(
        item
        for item in repo.list_action_inbox(limit=200)
        if str(item["item_ref"]).startswith("action-item:fcc-health-001:")
    )
    assert generated["action_revision_decision_eligible"] is False

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_NOT_FOUND",
    ):
        repo.record_action_decision(
            action_id=str(generated["item_ref"]),
            decision="cancel",
            request=_request(str(generated["action_revision_ref"])),
            idempotency_key_ref="idempotency-ref:test-generated-cancel-blocked",
        )

    assert repo.latest_action_receipt(str(generated["item_ref"])) is None


def test_generated_proposal_defer_materializes_one_authoritative_projection(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    generated = next(
        item
        for item in repo.list_action_inbox(limit=200)
        if str(item["item_ref"]).startswith("action-item:fcc-health-001:")
    )
    item_ref = str(generated["item_ref"])

    with pytest.raises(FounderLoopActionRevisionConflict):
        repo.record_action_decision(
            action_id=item_ref,
            decision="defer",
            request=_request(
                "action-revision:test-stale-generated",
                defer_until_ref="defer-until-ref:test-generated-review-later",
            ),
            idempotency_key_ref="idempotency-ref:test-generated-defer-stale",
        )
    assert repo._action_payload_for_item_ref(item_ref, include_generated=False) is None

    receipt = repo.record_action_decision(
        action_id=item_ref,
        decision="defer",
        request=_request(
            str(generated["action_revision_ref"]),
            defer_until_ref="defer-until-ref:test-generated-review-later",
        ),
        idempotency_key_ref="idempotency-ref:test-generated-defer",
    )

    matching_items = [
        item
        for item in repo.list_action_inbox(limit=200)
        if item["item_ref"] == item_ref
    ]
    assert len(matching_items) == 1
    deferred = matching_items[0]
    assert deferred["status"] == "deferred"
    assert deferred["action_revision_decision_eligible"] is True
    assert (
        deferred["receipt_visibility"]["decision_receipt_ref"] == receipt["receipt_ref"]
    )
    assert deferred["health_recommendation_action_execution_authorized"] is False


def test_legacy_replay_receipt_returns_typed_conflict_instead_of_crashing(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    revision_ref = str(_item(repo)["action_revision_ref"])
    receipt_ref = "receipt:founder-loop-action:legacy-replay"
    key_ref = "idempotency-ref:test-legacy-action-replay"
    with repo._connect() as conn:
        conn.execute(
            """
            INSERT INTO action_receipts (
                receipt_ref, item_ref, decision_ref, receipt_json, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                receipt_ref,
                ITEM_REF,
                "action-decision:test-legacy-action-replay",
                json.dumps({"receipt_ref": receipt_ref, "status": "rejected"}),
                "2026-08-15T00:00:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO action_idempotency_replays (
                key_ref, item_ref, decision, payload_fingerprint_ref,
                receipt_ref, decision_ref, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key_ref,
                ITEM_REF,
                "reject",
                "payload-fingerprint:founder-loop-action:legacy",
                receipt_ref,
                "action-decision:test-legacy-action-replay",
                "2026-08-15T00:00:00+00:00",
            ),
        )

    with pytest.raises(
        FounderLoopStorageDuplicateError,
        match="FOUNDER_LOOP_ACTION_IDEMPOTENCY_LEGACY_CONFLICT",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(revision_ref),
            idempotency_key_ref=key_ref,
        )


def test_local_task_commit_revalidates_approval_after_concurrent_cancel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-commit-race-approve")
    original_authority_decision = repo._local_task_authority_decision

    def cancel_before_commit(**kwargs):
        current_revision = str(_item(repo)["action_revision_ref"])
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="cancel",
            request=_request(current_revision),
            idempotency_key_ref="idempotency-ref:test-commit-race-cancel",
        )
        return original_authority_decision(**kwargs)

    monkeypatch.setattr(
        repo,
        "_local_task_authority_decision",
        cancel_before_commit,
    )
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_APPROVAL_REQUIRED",
    ):
        repo.commit_local_task(
            action_id=ACTION_ID,
            request=FounderLoopLocalTaskCommitRequest(
                approval_ref=str(approval["approval_ref"]),
                decision_reason_ref="decision-reason-ref:test-commit-race",
            ),
            idempotency_key_ref="idempotency-ref:test-commit-race",
        )
    with repo._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM local_tasks").fetchone()[0] == 0


def test_local_task_commit_reloads_safe_disable_posture_under_write_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-safe-disable-race-approve")
    original_authority_decision = repo._local_task_authority_decision

    def disable_before_write_lock(**kwargs):
        repo._disable_local_task_create_lane_for_test(
            disabled_reason_refs=["safe-disable-reason:test-concurrent-disable"],
        )
        return original_authority_decision(**kwargs)

    monkeypatch.setattr(
        repo,
        "_local_task_authority_decision",
        disable_before_write_lock,
    )
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED",
    ):
        repo.commit_local_task(
            action_id=ACTION_ID,
            request=FounderLoopLocalTaskCommitRequest(
                approval_ref=str(approval["approval_ref"]),
                decision_reason_ref="decision-reason-ref:test-safe-disable-race",
            ),
            idempotency_key_ref="idempotency-ref:test-safe-disable-race",
        )

    with repo._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM local_tasks").fetchone()[0] == 0
        assert (
            conn.execute("SELECT COUNT(*) FROM local_task_commit_receipts").fetchone()[
                0
            ]
            == 0
        )


def test_action_decisions_reject_terminal_committed_local_task(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-terminal-approve")
    commit_receipt = repo.commit_local_task(
        action_id=ACTION_ID,
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(approval["approval_ref"]),
            decision_reason_ref="decision-reason-ref:test-terminal-commit",
        ),
        idempotency_key_ref="idempotency-ref:test-terminal-commit",
    )
    committed = _item(repo)
    assert committed["status"] == "receipt_recorded"

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_TERMINAL_LOCAL_TASK_COMMITTED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="cancel",
            request=_request(str(committed["action_revision_ref"])),
            idempotency_key_ref="idempotency-ref:test-terminal-cancel",
        )

    still_committed = _item(repo)
    assert still_committed["status"] == "receipt_recorded"
    assert (
        still_committed["local_task_commit_receipt_ref"]
        == commit_receipt["receipt_ref"]
    )


def test_action_receipt_capacity_exhaustion_preserves_current_revision(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    revision_ref = str(_item(repo)["action_revision_ref"])
    with repo._connect() as conn:
        for index in range(FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM):
            receipt_ref = f"receipt:test-capacity:{index:02d}"
            conn.execute(
                """
                INSERT INTO action_receipts (
                    receipt_ref, item_ref, decision_ref, receipt_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_ref,
                    ITEM_REF,
                    f"action-decision:test-capacity:{index:02d}",
                    json.dumps({"receipt_ref": receipt_ref}),
                    f"2026-08-15T00:00:{index:02d}+00:00",
                ),
            )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="reject",
            request=_request(revision_ref),
            idempotency_key_ref="idempotency-ref:test-capacity-exhausted",
        )
    assert _item(repo)["action_revision_ref"] == revision_ref


def test_receipt_capacity_reserves_one_atomic_active_approval_invalidation(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    approval = _approve(repo, key="idempotency-ref:test-capacity-approve")
    approved_revision = str(_item(repo)["action_revision_ref"])
    with repo._connect() as conn:
        for index in range(FOUNDER_LOOP_ACTION_DECISION_RECEIPT_LIMIT_PER_ITEM - 1):
            receipt_ref = f"receipt:test-invalidation-capacity:{index:02d}"
            conn.execute(
                """
                INSERT INTO action_receipts (
                    receipt_ref, item_ref, decision_ref, receipt_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_ref,
                    ITEM_REF,
                    f"action-decision:test-invalidation-capacity:{index:02d}",
                    json.dumps({"receipt_ref": receipt_ref}),
                    f"2026-08-15T00:00:{index:02d}+00:00",
                ),
            )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="edit",
            request=_request(approved_revision),
            idempotency_key_ref="idempotency-ref:test-capacity-invalid-edit",
        )

    cancelled = repo.record_action_decision(
        action_id=ACTION_ID,
        decision="cancel",
        request=_request(approved_revision),
        idempotency_key_ref="idempotency-ref:test-capacity-cancel",
    )

    assert cancelled["status"] == "cancelled"
    assert cancelled["invalidated_approval_refs"] == [approval["approval_ref"]]
    assert cancelled["invalidated_approval_count"] == 1
    cancelled_item = _item(repo)
    assert (
        cancelled_item["receipt_visibility"]["decision_receipt_ref"]
        == cancelled["receipt_ref"]
    )
    current_revision = str(cancelled_item["action_revision_ref"])
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_ACTION_RECEIPT_CAPACITY_EXHAUSTED",
    ):
        repo.record_action_decision(
            action_id=ACTION_ID,
            decision="edit",
            request=_request(
                current_revision,
                edited_envelope_ref="action-envelope:test-capacity-edit",
            ),
            idempotency_key_ref="idempotency-ref:test-capacity-edit-blocked",
        )


def test_cancel_api_returns_typed_stale_conflict_and_safe_refs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    issue_workspace_write_authority_lease(authority_dir)
    client = TestClient(app)
    item = next(
        item
        for item in client.get("/control-center/actions/inbox").json()["data"]["items"]
        if item["item_ref"] == ITEM_REF
    )
    body = {
        "expected_revision_ref": item["action_revision_ref"],
        "decision_reason_ref": "decision-reason-ref:test-api-cancel",
        "metadata_refs": ["metadata-ref:test-api-cancel"],
    }

    cancelled = client.post(
        f"/control-center/actions/{ACTION_ID}/cancel",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-cancel"},
    )
    assert cancelled.status_code == 200
    receipt = cancelled.json()["data"]
    assert receipt["status"] == "cancelled"
    assert body["decision_reason_ref"] not in cancelled.text

    stale = client.post(
        f"/control-center/actions/{ACTION_ID}/reject",
        json=body,
        headers={"x-uaa-idempotency-key": "idempotency-ref:test-api-stale"},
    )
    assert stale.status_code == 409
    detail = stale.json()["detail"]
    assert detail == {
        "code": "FOUNDER_LOOP_ACTION_STALE_REVISION",
        "safe_message": (
            "The Action changed after this decision was prepared; refresh the "
            "authoritative Action Inbox before retrying."
        ),
        "refresh_required": True,
        "current_revision_ref": receipt["result_revision_ref"],
        "current_generation_ref": receipt["result_generation_ref"],
        "refresh_route_ref": "GET /control-center/actions/inbox",
    }


def test_cancel_cli_requires_revision_and_reports_typed_conflict(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    authority_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_dir))
    issue_workspace_write_authority_lease(authority_dir)
    repo = FounderLoopRepository(state_dir)
    revision_ref = str(_item(repo)["action_revision_ref"])

    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "cancel-action",
            "--action-id",
            ACTION_ID,
            "--expected-revision-ref",
            revision_ref,
            "--idempotency-ref",
            "idempotency-ref:test-cli-cancel",
        ]
    )
    receipt = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert receipt["command_ref"] == "repo-local-command:founder-loop-cancel-action"
    assert receipt["receipt"]["status"] == "cancelled"

    stale_rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "cancel-action",
            "--action-id",
            ACTION_ID,
            "--expected-revision-ref",
            revision_ref,
            "--idempotency-ref",
            "idempotency-ref:test-cli-cancel-stale",
        ]
    )
    conflict = json.loads(capsys.readouterr().out)
    assert stale_rc == 1
    assert conflict["status"] == "conflict"
    assert conflict["error_ref"] == "FOUNDER_LOOP_ACTION_STALE_REVISION"
    assert conflict["refresh_required"] is True
    assert conflict["current_revision_ref"] == receipt["receipt"]["result_revision_ref"]


def test_action_decision_cli_redacts_malformed_revision_validation(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    sentinel = "SENTINEL-REVISION-RAW-VALUE with spaces"
    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(tmp_path / "founder_loop"),
            "cancel-action",
            "--action-id",
            ACTION_ID,
            "--expected-revision-ref",
            sentinel,
            "--idempotency-ref",
            "idempotency-ref:test-cli-malformed-revision",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 1
    assert captured.err == ""
    assert sentinel not in captured.out
    assert "Traceback" not in captured.out
    assert payload == {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-cancel-action",
        "status": "blocked",
        "error_ref": "FOUNDER_LOOP_ACTION_DECISION_UNSAFE_INPUT",
        "safe_message": (
            "The Action decision input failed safe-ref validation and was not recorded."
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
