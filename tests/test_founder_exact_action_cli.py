import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.dev.uaa_founder_loop import main
from tests.test_control_center_founder_exact_action_api import _issue_exact_lease
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.dependencies import clear_founder_attention_workflow_cache
from ultimate_ai_agent.core.execution.mission_completion import (
    MISSION_COMPLETION_LEDGER_FILE,
)
from ultimate_ai_agent.core.storage.founder_loop_exact_action import (
    FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF,
)


TODAY_ITEM_REF = FOUNDER_LOOP_EXACT_ATTENTION_ACTION_REF


def test_exact_action_status_cli_is_human_readable_by_default(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder-loop"))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    result = main(
        [
            "--state-dir",
            str(tmp_path / "founder-loop"),
            "--authority-state-dir",
            str(tmp_path / "authority"),
            "exact-action-status",
            "--today-item-ref",
            TODAY_ITEM_REF,
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert "Exact Founder Loop action: review ready" in output
    assert "Execution: not performed" in output
    assert str(tmp_path) not in output
    clear_founder_attention_workflow_cache()


def test_exact_action_status_cli_json_matches_backend_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder-loop"))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    result = main(
        [
            "--state-dir",
            str(tmp_path / "founder-loop"),
            "--authority-state-dir",
            str(tmp_path / "authority"),
            "exact-action-status",
            "--today-item-ref",
            TODAY_ITEM_REF,
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["status"] == "review_ready"
    assert payload["mission_scoped_lease_required"] is True
    assert payload["exact_approval_required"] is True
    assert payload["execution_performed"] is False
    assert payload["required_inspected_source_refs"]
    assert str(tmp_path) not in json.dumps(payload)
    clear_founder_attention_workflow_cache()


def test_exact_action_cli_cannot_run_without_explicit_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder-loop"))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(tmp_path / "authority"))
    result = main(
        [
            "--state-dir",
            str(tmp_path / "founder-loop"),
            "--authority-state-dir",
            str(tmp_path / "authority"),
            "run-exact-action",
            "--workflow-ref",
            "founder-loop-attention-workflow:cli-blocked",
            "--today-item-ref",
            TODAY_ITEM_REF,
            "--source-ref",
            TODAY_ITEM_REF,
            "--mission-ref",
            "mission-ref:founder-loop-cli-blocked",
            "--run-ref",
            "run-ref:founder-loop-cli-blocked",
            "--lease-ref",
            "authority-lease:founder-loop-cli-blocked",
            "--idempotency-ref",
            "idempotency-ref:founder-loop-cli-blocked",
            "--approval-ref",
            "approval-ref:founder-loop-cli-blocked",
            "--proposal-ref",
            "action-proposal-ref:founder-loop-cli-blocked",
            "--approval-request-ref",
            "approval-request-ref:founder-loop-cli-blocked",
            "--source-review-receipt-ref",
            "source-review-receipt-ref:founder-loop-cli-blocked",
        ]
    )
    assert result == 1
    assert "explicit approval confirmation required" in capsys.readouterr().out
    clear_founder_attention_workflow_cache()


def test_exact_action_cli_success_matches_api_terminal_truth(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    founder_state = tmp_path / "founder-loop"
    authority_state = tmp_path / "authority"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(founder_state))
    monkeypatch.setenv("UAA_AUTHORITY_STATE_DIR", str(authority_state))
    state_args = [
        "--state-dir",
        str(founder_state),
        "--authority-state-dir",
        str(authority_state),
    ]
    assert (
        main(
            [
                *state_args,
                "exact-action-status",
                "--today-item-ref",
                TODAY_ITEM_REF,
                "--json",
            ]
        )
        == 0
    )
    status = json.loads(capsys.readouterr().out)
    mission_ref = "mission-ref:founder-loop-cli-success"
    lease = _issue_exact_lease(
        authority_state_dir=authority_state,
        status=status,
        mission_ref=mission_ref,
    )
    prepare_args = [
        *state_args,
        "prepare-exact-action",
        "--workflow-ref",
        "founder-loop-attention-workflow:cli-success",
        "--today-item-ref",
        TODAY_ITEM_REF,
    ]
    for source_ref in status["required_inspected_source_refs"]:
        prepare_args.extend(["--source-ref", source_ref])
    prepare_args.extend(
        [
            "--mission-ref",
            mission_ref,
            "--run-ref",
            "run-ref:founder-loop-cli-success",
            "--lease-ref",
            lease.lease_ref,
            "--idempotency-ref",
            "idempotency-ref:founder-loop-cli-success",
            "--json",
        ]
    )
    assert main(prepare_args) == 0
    prepared = json.loads(capsys.readouterr().out)
    assert prepared["status"] == "awaiting_exact_approval"
    assert prepared["execution_performed"] is False

    run_args = [
        *state_args,
        "run-exact-action",
        "--workflow-ref",
        "founder-loop-attention-workflow:cli-success",
        "--today-item-ref",
        TODAY_ITEM_REF,
    ]
    for source_ref in status["required_inspected_source_refs"]:
        run_args.extend(["--source-ref", source_ref])
    run_args.extend(
        [
            "--mission-ref",
            mission_ref,
            "--run-ref",
            "run-ref:founder-loop-cli-success",
            "--lease-ref",
            lease.lease_ref,
            "--idempotency-ref",
            "idempotency-ref:founder-loop-cli-success:execute",
            "--proposal-ref",
            prepared["proposal_ref"],
            "--approval-request-ref",
            prepared["approval_request_ref"],
            "--source-review-receipt-ref",
            prepared["source_review_receipt_ref"],
            "--approval-ref",
            "approval-ref:founder-loop-cli-success",
            "--confirm-exact-approval",
            "--json",
        ]
    )
    assert main(run_args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "receipt_recorded"

    api_status = TestClient(app).get(
        f"/control-center/today/exact-action/{TODAY_ITEM_REF}/status"
    ).json()["data"]
    assert api_status["execution_performed"] is True
    assert result["completion_ref"] in api_status["receipt_refs"]
    assert str(tmp_path) not in json.dumps(result)

    (authority_state / MISSION_COMPLETION_LEDGER_FILE).unlink()
    assert (
        main(
            [
                *state_args,
                "exact-action-status",
                "--today-item-ref",
                TODAY_ITEM_REF,
            ]
        )
        == 0
    )
    unknown_output = capsys.readouterr().out
    assert "Execution: unknown; recovery required" in unknown_output
    assert "Execution: not performed" not in unknown_output
    clear_founder_attention_workflow_cache()
