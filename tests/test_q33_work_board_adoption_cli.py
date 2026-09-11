from __future__ import annotations

import json
from pathlib import Path

from scripts.dev.uaa_work_board import main
from ultimate_ai_agent.core.control_center.work_board_adoption import (
    WorkBoardAdoptionApprovalCaptureRequest,
    WorkBoardAdoptionCardDraft,
    WorkBoardAdoptionCommitRequest,
    WorkBoardAdoptionMutationRequest,
    WorkBoardAdoptionStore,
)


def _seed_private_card(state_dir: Path) -> None:
    store = WorkBoardAdoptionStore(state_dir)
    mutation = WorkBoardAdoptionMutationRequest(
        action="create",
        expected_revision=0,
        draft=WorkBoardAdoptionCardDraft(
            title="Q33 private operator title",
            description="Q33 private operator description",
        ),
    )
    idempotency_ref = "idempotency-ref:q33-work-board-cli:seed"
    preview = store.preview_mutation(mutation, idempotency_ref=idempotency_ref)
    store.capture_approval(
        WorkBoardAdoptionApprovalCaptureRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )
    store.commit_mutation(
        WorkBoardAdoptionCommitRequest(
            mutation=mutation,
            preview_ref=preview.preview_ref,
            approval_ref=preview.approval_ref,
        ),
        idempotency_ref=idempotency_ref,
    )


def test_work_board_adoption_cli_omits_private_values_by_default(
    tmp_path: Path,
    capsys,
) -> None:
    _seed_private_card(tmp_path)

    assert main(["inspect-adoption", "--state-dir", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "ready"
    assert payload["active_card_count"] == 1
    assert payload["private_values_included"] is False
    assert payload["raw_paths_included"] is False
    assert "Q33 private operator title" not in json.dumps(payload)


def test_work_board_adoption_cli_private_view_is_explicit(
    tmp_path: Path,
    capsys,
) -> None:
    _seed_private_card(tmp_path)

    assert main(
        ["inspect-adoption", "--state-dir", str(tmp_path), "--include-private"]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["private_values_included"] is True
    assert payload["active_cards"][0]["title"] == "Q33 private operator title"
