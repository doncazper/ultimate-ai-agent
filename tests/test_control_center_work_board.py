from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
    build_default_authority_leases,
)
from ultimate_ai_agent.core.control_center import (
    WORK_BOARD_BACKEND_ROUTE_REF,
    WORK_BOARD_BOARD_REF,
    WORK_BOARD_CARD_CREATE_ROUTE_REF,
    WORK_BOARD_CLI_REF,
    WORK_BOARD_CONTRACT_REF,
    WORK_BOARD_FRONTEND_ROUTE_REF,
    WORK_BOARD_REQUIRED_BLOCKED_REFS,
    WorkBoardReadModel,
    build_work_board_read_model,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.control_center.work_board import (
    WORK_BOARD_STATE_DIR_ENV,
    WorkBoardAuthorityError,
    WorkBoardCardCreateRequest,
    WorkBoardReorderRequest,
    WorkBoardStateStore,
    WorkBoardStorageConflictError,
    prepare_work_board_card_create_approval,
    prepare_work_board_reorder_approval,
)


ROOT = Path(__file__).resolve().parents[1]


def _workspace_write_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-work-board-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary=(
            "Test lease grants Workspace write for exact approved Work Board mutations."
        ),
    )


def test_work_board_read_model_is_backend_owned_safe_refs_only() -> None:
    board = build_work_board_read_model()
    payload = board.model_dump(mode="json")

    assert board.schema_version == "uaa-work-board-read-model.v1"
    assert board.contract_ref == WORK_BOARD_CONTRACT_REF
    assert board.board_ref == WORK_BOARD_BOARD_REF
    assert board.backend_route_refs == [WORK_BOARD_BACKEND_ROUTE_REF]
    assert board.frontend_route_refs == [WORK_BOARD_FRONTEND_ROUTE_REF]
    assert board.cli_inspection_refs == [WORK_BOARD_CLI_REF]
    assert board.backend_owned is True
    assert board.read_only is True
    assert board.safe_refs_only is True
    assert board.non_authoritative_mock_fallback is False
    assert board.raw_paths_included is False
    assert board.raw_content_included is False
    assert board.board_mutation_enabled is False
    assert board.durable_drag_drop_enabled is False
    assert board.issue_tracker_write_enabled is False
    assert board.connector_write_enabled is False
    assert board.shell_subprocess_execution_enabled is False
    assert board.browser_automation_enabled is False
    assert board.background_autonomy_enabled is False
    assert board.production_authority_enabled is False
    assert board.durable_reorder_persistence_enabled is True
    assert board.approval_required_for_reorder is True
    assert board.latest_reorder_receipt_ref is None
    assert board.local_card_create_enabled is True
    assert board.card_create_route_ref == WORK_BOARD_CARD_CREATE_ROUTE_REF
    assert board.local_card_create_contract_available is True
    assert board.approval_required_for_card_create is True
    assert board.card_create_route_available is True
    assert board.latest_card_create_receipt_ref is None
    assert board.drag_drop_posture.local_preview_enabled is True
    assert board.drag_drop_posture.keyboard_reorder_preview_enabled is True
    assert board.drag_drop_posture.durable_reorder_enabled is True
    assert board.drag_drop_posture.backend_mutation_route_available is True
    assert board.drag_drop_posture.approval_required is True
    assert board.drag_drop_posture.rollback_available is True
    assert board.columns
    assert board.cards
    assert set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
        board.blocked_authority_refs
    )
    assert {column.column_ref for column in board.columns} >= {
        "work-board-column:triage",
        "work-board-column:doing",
        "work-board-column:blocked",
        "work-board-column:done",
    }
    assert "work-board-card:work-board-kanban-shell" in {
        card.card_ref for card in board.cards
    }
    assert "/Users/" not in json.dumps(payload)
    assert "credential" not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    "flag_name",
    [
        "board_mutation_enabled",
        "durable_drag_drop_enabled",
        "issue_tracker_write_enabled",
        "connector_write_enabled",
        "shell_subprocess_execution_enabled",
        "browser_automation_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ],
)
def test_work_board_rejects_runtime_and_mutation_authority(flag_name: str) -> None:
    payload = build_work_board_read_model().model_dump(mode="json")
    payload[flag_name] = True

    with pytest.raises(ValidationError, match=flag_name):
        WorkBoardReadModel(**payload)


def test_work_board_rejects_raw_paths_and_card_mutation() -> None:
    payload = build_work_board_read_model().model_dump(mode="json")
    payload["raw_paths_included"] = True
    with pytest.raises(ValidationError, match="raw_paths_included"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["cards"][0]["mutation_enabled"] = True
    with pytest.raises(ValidationError, match="mutation"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["drag_drop_posture"]["receipt_created"] = True
    with pytest.raises(ValidationError, match="receipt"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["card_create_route_ref"] = "POST /control-center/work-board/cardz"
    with pytest.raises(ValidationError, match="route ref"):
        WorkBoardReadModel(**payload)

    payload = build_work_board_read_model().model_dump(mode="json")
    payload["card_create_route_available"] = False
    with pytest.raises(ValidationError, match="card create route"):
        WorkBoardReadModel(**payload)


def test_control_center_work_board_route_returns_safe_read_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/work-board")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_work_board"
    assert body["service"] == "ControlCenterWorkBoardAPI"
    assert body["trace_id"] == WORK_BOARD_BOARD_REF
    assert body["redactions_applied"] == [
        "redaction-ref:safe-refs-only",
        "redaction-ref:raw-paths-omitted",
        "redaction-ref:raw-content-omitted",
    ]
    data = body["data"]
    assert data["backend_owned"] is True
    assert data["read_only"] is True
    assert data["safe_refs_only"] is True
    assert data["board_mutation_enabled"] is False
    assert data["durable_drag_drop_enabled"] is False
    assert data["durable_reorder_persistence_enabled"] is True
    assert data["approval_required_for_reorder"] is True
    assert data["local_card_create_enabled"] is True
    assert data["card_create_route_ref"] == WORK_BOARD_CARD_CREATE_ROUTE_REF
    assert data["local_card_create_contract_available"] is True
    assert data["approval_required_for_card_create"] is True
    assert data["card_create_route_available"] is True
    assert data["drag_drop_posture"]["local_preview_enabled"] is True
    assert data["drag_drop_posture"]["durable_reorder_enabled"] is True
    assert data["drag_drop_posture"]["backend_mutation_route_available"] is True
    assert set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
        data["blocked_authority_refs"]
    )


def test_control_center_work_board_reorder_route_requires_exact_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WORK_BOARD_STATE_DIR_ENV, str(tmp_path / "work_board"))
    client = TestClient(app)
    base_board = build_work_board_read_model(apply_persisted_state=False)
    ready_column = next(
        column
        for column in base_board.columns
        if column.column_ref == "work-board-column:ready"
    )
    reordered_columns = []
    for column in base_board.columns:
        card_refs = list(column.card_refs)
        if column.column_ref == ready_column.column_ref:
            card_refs = list(reversed(card_refs))
        reordered_columns.append(
            {"column_ref": column.column_ref, "card_refs": card_refs}
        )
    payload = {
        "decision_reason_ref": "decision-reason-ref:work-board-test-reorder",
        "columns": reordered_columns,
    }
    headers = {"X-UAA-Idempotency-Key": "idempotency-ref:work-board-test-reorder"}

    response = client.post("/control-center/work-board/reorder", json=payload, headers=headers)

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "WORK_BOARD_REORDER_APPROVAL_DENIED"
    assert "blocked-state:work-board-reorder-approval-required" in (
        detail["reason_refs"]
    )
    assert detail["required_refs"]["approval_ref"].startswith(
        "work-board-approval-ref:sha256:"
    )
    assert not (tmp_path / "work_board" / "work_board_state.json").exists()


def test_control_center_work_board_card_create_route_requires_exact_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WORK_BOARD_STATE_DIR_ENV, str(tmp_path / "work_board"))
    client = TestClient(app)
    payload = {
        "decision_reason_ref": "decision-reason-ref:work-board-test-card-create",
        "column_ref": "work-board-column:triage",
        "title": "Local approved board item",
        "safe_summary": "Safe local board item created through the exact card-create lane.",
        "priority": "medium",
        "tags": ["local", "approved"],
    }
    headers = {"X-UAA-Idempotency-Key": "idempotency-ref:work-board-test-card-create"}

    response = client.post("/control-center/work-board/cards", json=payload, headers=headers)

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "WORK_BOARD_CARD_CREATE_APPROVAL_DENIED"
    assert "blocked-state:work-board-card-create-approval-required" in (
        detail["reason_refs"]
    )
    assert detail["required_refs"]["approval_ref"].startswith(
        "work-board-card-create-approval-ref:sha256:"
    )
    assert detail["required_refs"]["card_ref"].startswith(
        "work-board-card:local:sha256:"
    )
    assert not (tmp_path / "work_board" / "work_board_state.json").exists()


def test_work_board_state_store_persists_with_external_exact_approval(
    tmp_path: Path,
) -> None:
    base_board = build_work_board_read_model(apply_persisted_state=False)
    ready_column = next(
        column
        for column in base_board.columns
        if column.column_ref == "work-board-column:ready"
    )
    reordered_columns = []
    for column in base_board.columns:
        card_refs = list(column.card_refs)
        if column.column_ref == ready_column.column_ref:
            card_refs = list(reversed(card_refs))
        reordered_columns.append(
            {"column_ref": column.column_ref, "card_refs": card_refs}
        )
    request = WorkBoardReorderRequest(
        decision_reason_ref="decision-reason-ref:work-board-test-reorder",
        columns=reordered_columns,
    )
    idempotency_ref = "idempotency-ref:work-board-test-reorder"
    store = WorkBoardStateStore(
        tmp_path / "work_board",
        active_authority_leases=[_workspace_write_lease()],
    )
    approval_preview = prepare_work_board_reorder_approval(
        request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_preview.approval_request)
    authority.grant(
        approval_preview.approval_request.approval_request_id,
        approved_by_actor_id=approval_preview.approval_request.actor_context.actor_id,
        approval_ref=approval_preview.expected_approval_ref,
    )
    approved_request = request.model_copy(
        update={
            "approval_ref": approval_preview.expected_approval_ref,
            "exact_scope_ref": approval_preview.exact_scope_ref,
            "action_envelope_ref": approval_preview.action_envelope_ref,
        }
    )
    receipt = store.persist_reorder(
        approved_request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )

    assert receipt.status == "applied"
    assert receipt.replayed is False
    assert receipt.raw_paths_included is False
    assert receipt.raw_content_included is False
    assert receipt.connector_write_performed is False
    assert receipt.provider_model_call_performed is False
    assert receipt.production_authority_enabled is False
    assert receipt.authority_decision_ref is not None
    assert receipt.authority_decision_outcome == "ask"
    assert receipt.authority_lease_ref == "authority-lease-ref:test-work-board-write"
    assert receipt.authority_domain_ref == "authority-domain-ref:workspace"
    assert receipt.authority_capability_ref == "authority-capability-ref:write"
    receipt_ref = receipt.receipt_ref

    replay = store.persist_reorder(
        approved_request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )
    assert replay.status == "replayed"
    assert replay.receipt_ref == receipt_ref

    board = build_work_board_read_model(
        store=store,
    ).model_dump(mode="json")
    assert board["latest_reorder_receipt_ref"] == receipt_ref
    persisted_ready = next(
        column
        for column in board["columns"]
        if column["column_ref"] == ready_column.column_ref
    )
    assert persisted_ready["card_refs"] == list(reversed(ready_column.card_refs))

    changed_request = approved_request.model_copy(
        update={"metadata_refs": ["metadata-ref:work-board-reorder-conflict"]}
    )
    with pytest.raises(
        WorkBoardStorageConflictError,
        match="WORK_BOARD_REORDER_IDEMPOTENCY_CONFLICT",
    ):
        store.persist_reorder(
            changed_request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )


def test_work_board_reorder_requires_active_workspace_write_lease(
    tmp_path: Path,
) -> None:
    base_board = build_work_board_read_model(apply_persisted_state=False)
    ready_column = next(
        column
        for column in base_board.columns
        if column.column_ref == "work-board-column:ready"
    )
    reordered_columns = []
    for column in base_board.columns:
        card_refs = list(column.card_refs)
        if column.column_ref == ready_column.column_ref:
            card_refs = list(reversed(card_refs))
        reordered_columns.append(
            {"column_ref": column.column_ref, "card_refs": card_refs}
        )
    request = WorkBoardReorderRequest(
        decision_reason_ref="decision-reason-ref:work-board-test-reorder-denied",
        columns=reordered_columns,
    )
    idempotency_ref = "idempotency-ref:work-board-test-reorder-denied"
    approval_preview = prepare_work_board_reorder_approval(
        request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_preview.approval_request)
    authority.grant(
        approval_preview.approval_request.approval_request_id,
        approved_by_actor_id=approval_preview.approval_request.actor_context.actor_id,
        approval_ref=approval_preview.expected_approval_ref,
    )
    approved_request = request.model_copy(
        update={
            "approval_ref": approval_preview.expected_approval_ref,
            "exact_scope_ref": approval_preview.exact_scope_ref,
            "action_envelope_ref": approval_preview.action_envelope_ref,
        }
    )
    store = WorkBoardStateStore(
        tmp_path / "work_board",
        active_authority_leases=build_default_authority_leases(),
    )

    with pytest.raises(WorkBoardAuthorityError) as exc_info:
        store.persist_reorder(
            approved_request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )

    assert "blocked-state:work-board-authority-lease-required" in (
        exc_info.value.reason_refs
    )
    assert (
        exc_info.value.required_refs["required_domain_ref"]
        == "authority-domain-ref:workspace"
    )
    assert (
        exc_info.value.required_refs["required_capability_ref"]
        == "authority-capability-ref:write"
    )
    assert not (tmp_path / "work_board" / "work_board_state.json").exists()


def test_work_board_state_store_persists_card_create_with_external_exact_approval(
    tmp_path: Path,
) -> None:
    base_board = build_work_board_read_model(apply_persisted_state=False)
    request = WorkBoardCardCreateRequest(
        decision_reason_ref="decision-reason-ref:work-board-test-card-create",
        column_ref="work-board-column:triage",
        title="Local approved board item",
        safe_summary="Safe local board item created through the exact card-create lane.",
        priority="medium",
        tags=["local", "approved"],
    )
    idempotency_ref = "idempotency-ref:work-board-test-card-create"
    store = WorkBoardStateStore(
        tmp_path / "work_board",
        active_authority_leases=[_workspace_write_lease()],
    )
    approval_preview = prepare_work_board_card_create_approval(
        request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_preview.approval_request)
    authority.grant(
        approval_preview.approval_request.approval_request_id,
        approved_by_actor_id=approval_preview.approval_request.actor_context.actor_id,
        approval_ref=approval_preview.expected_approval_ref,
    )
    approved_request = request.model_copy(
        update={
            "approval_ref": approval_preview.expected_approval_ref,
            "exact_scope_ref": approval_preview.exact_scope_ref,
            "action_envelope_ref": approval_preview.action_envelope_ref,
        }
    )
    receipt = store.persist_card_create(
        approved_request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )

    assert receipt.status == "applied"
    assert receipt.replayed is False
    assert receipt.card_ref == approval_preview.card_ref
    assert receipt.raw_paths_included is False
    assert receipt.raw_content_included is False
    assert receipt.connector_write_performed is False
    assert receipt.provider_model_call_performed is False
    assert receipt.production_authority_enabled is False
    assert receipt.authority_decision_ref is not None
    assert receipt.authority_decision_outcome == "ask"
    assert receipt.authority_lease_ref == "authority-lease-ref:test-work-board-write"
    assert receipt.authority_domain_ref == "authority-domain-ref:workspace"
    assert receipt.authority_capability_ref == "authority-capability-ref:write"
    receipt_ref = receipt.receipt_ref

    replay = store.persist_card_create(
        approved_request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
        approval_authority=authority,
    )
    assert replay.status == "replayed"
    assert replay.receipt_ref == receipt_ref

    board = build_work_board_read_model(store=store).model_dump(mode="json")
    assert board["latest_card_create_receipt_ref"] == receipt_ref
    assert receipt.card_ref in {card["card_ref"] for card in board["cards"]}
    triage = next(
        column
        for column in board["columns"]
        if column["column_ref"] == "work-board-column:triage"
    )
    assert receipt.card_ref in triage["card_refs"]

    changed_request = approved_request.model_copy(
        update={"safe_summary": "Different safe local board item payload."}
    )
    with pytest.raises(
        WorkBoardStorageConflictError,
        match="WORK_BOARD_CARD_CREATE_IDEMPOTENCY_CONFLICT",
    ):
        store.persist_card_create(
            changed_request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )


def test_work_board_card_create_requires_active_workspace_write_lease(
    tmp_path: Path,
) -> None:
    base_board = build_work_board_read_model(apply_persisted_state=False)
    request = WorkBoardCardCreateRequest(
        decision_reason_ref="decision-reason-ref:work-board-test-card-create-denied",
        column_ref="work-board-column:triage",
        title="Local approved board item",
        safe_summary="Safe local board item created through the exact card-create lane.",
        priority="medium",
        tags=["local", "approved"],
    )
    idempotency_ref = "idempotency-ref:work-board-test-card-create-denied"
    approval_preview = prepare_work_board_card_create_approval(
        request,
        columns=base_board.columns,
        cards=base_board.cards,
        idempotency_ref=idempotency_ref,
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_preview.approval_request)
    authority.grant(
        approval_preview.approval_request.approval_request_id,
        approved_by_actor_id=approval_preview.approval_request.actor_context.actor_id,
        approval_ref=approval_preview.expected_approval_ref,
    )
    approved_request = request.model_copy(
        update={
            "approval_ref": approval_preview.expected_approval_ref,
            "exact_scope_ref": approval_preview.exact_scope_ref,
            "action_envelope_ref": approval_preview.action_envelope_ref,
        }
    )
    store = WorkBoardStateStore(
        tmp_path / "work_board",
        active_authority_leases=build_default_authority_leases(),
    )

    with pytest.raises(WorkBoardAuthorityError) as exc_info:
        store.persist_card_create(
            approved_request,
            columns=base_board.columns,
            cards=base_board.cards,
            idempotency_ref=idempotency_ref,
            approval_authority=authority,
        )

    assert "blocked-state:work-board-authority-lease-required" in (
        exc_info.value.reason_refs
    )
    assert (
        exc_info.value.required_refs["required_domain_ref"]
        == "authority-domain-ref:workspace"
    )
    assert (
        exc_info.value.required_refs["required_capability_ref"]
        == "authority-capability-ref:write"
    )
    assert not (tmp_path / "work_board" / "work_board_state.json").exists()


def test_work_board_route_is_local_sensitive_and_side_effect_bounded() -> None:
    manifest = build_api_manifest(app)
    route = next(
        item
        for item in manifest.routes
        if item.path == "/control-center/work-board" and item.method == "GET"
    )

    assert route.tags == ["control-center"]
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.protected_route is True
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_posture == "not_required_for_route_classification"
    assert route.rate_limit_posture == "not_targeted_for_route"

    card_create_route = next(
        item
        for item in manifest.routes
        if item.path == "/control-center/work-board/cards" and item.method == "POST"
    )
    assert card_create_route.route_classification == "mutating_requires_authority"
    assert card_create_route.side_effect_class == "local_dev_workspace_only"
    assert card_create_route.protected_route is True
    assert card_create_route.approval_posture == "required_before_mutation_authority"
    assert card_create_route.idempotency_posture == "required_before_mutation_authority"


def test_work_board_cli_inspection_prints_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_work_board.py"),
            "inspect-board",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["board_ref"] == WORK_BOARD_BOARD_REF
    assert payload["backend_owned"] is True
    assert payload["board_mutation_enabled"] is False
    assert payload["durable_reorder_persistence_enabled"] is True
    assert "/Users/" not in result.stdout


def test_work_board_cli_card_create_receipt_inspection_prints_safe_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WORK_BOARD_STATE_DIR_ENV, str(tmp_path / "work_board"))
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_work_board.py"),
            "inspect-card-create-receipt",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "missing"
    assert payload["receipt_ref"] is None
    assert payload["card_ref"] is None
    assert payload["raw_paths_included"] is False
    assert payload["raw_content_included"] is False
    assert "/Users/" not in result.stdout
