from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts import verify_fcc_v1_003_founder_loop_vertical_slice as verifier
from scripts.dev import uaa_founder_loop
from scripts.verification.repo import load_json
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    action_approval_request,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def _approve_local_task_seed_action(state_dir: Path) -> None:
    repo = FounderLoopRepository(state_dir)
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:test-cli-local-task-action-approval"
    )
    approval_request = action_approval_request(
        item_ref=str(action["item_ref"]),
        actor_context=request.actor_context,
        risk_class=str(action["risk_class"]),
        resource_refs=[
            str(action["item_ref"]),
            str(action["action_envelope_ref"]),
            str(action["action_scope_ref"]),
            str(action["action_approval_requirement_ref"]),
        ],
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local-test-reviewer",
        approval_ref="approval-ref:test-cli-local-task-action-approve",
    )
    receipt = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            approval_ref=grant.approval_ref,
            approval_grants=[grant],
            decision_reason_ref="decision-reason-ref:test-cli-local-task-action-approval",
        ),
        idempotency_key_ref="idempotency-ref:test-cli-local-task-action-approval",
    )
    assert receipt["status"] == "approved"


def test_founder_loop_cli_promotes_and_inspects_safe_refs(
    tmp_path: Path,
    capsys,
) -> None:
    state_dir = tmp_path / "founder_loop"
    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "promote-action-envelope",
            "--today-item-ref",
            verifier.TODAY_ITEM_REF,
            "--idempotency-ref",
            "idempotency-ref:test-fcc-v1-003-cli",
        ]
    )
    assert rc == 0
    promoted = json.loads(capsys.readouterr().out)
    assert promoted["receipt"]["action_executed"] is False
    assert promoted["receipt"]["action_envelope_ref"].startswith("action-envelope:")

    rc = uaa_founder_loop.main(["--state-dir", str(state_dir), "inspect", "--limit", "4"])
    assert rc == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["safe_refs_only"] is True
    assert inspected["raw_paths_omitted"] is True
    assert inspected["actions"][0]["receipt_refs"]
    assert "state_dir" not in inspected


def test_founder_loop_cli_commits_local_task_with_safe_refs(
    tmp_path: Path,
    capsys,
) -> None:
    state_dir = tmp_path / "founder_loop"
    _approve_local_task_seed_action(state_dir)
    repo = FounderLoopRepository(state_dir)
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    approval_ref = str(action["local_task_commit_approval_ref"])

    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "commit-local-task",
            "--action-id",
            "local-task-create-scorecard",
            "--idempotency-ref",
            "idempotency-ref:test-cli-local-task-commit",
            "--approval-ref",
            approval_ref,
            "--metadata-ref",
            "metadata-ref:test-cli-local-task-commit",
        ]
    )

    assert rc == 0
    committed = json.loads(capsys.readouterr().out)
    assert committed["safe_refs_only"] is True
    assert committed["raw_content_omitted"] is True
    assert committed["raw_paths_omitted"] is True
    assert committed["receipt"]["status"] == "local_task_created"
    assert committed["receipt"]["local_task_created"] is True
    assert committed["receipt"]["connector_write_performed"] is False
    assert committed["receipt"]["external_side_effect_performed"] is False
    assert str(state_dir) not in json.dumps(committed)
    assert "raw_prompt" not in json.dumps(committed).lower()

    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "commit-local-task",
            "--action-id",
            "local-task-create-scorecard",
            "--idempotency-ref",
            "idempotency-ref:test-cli-local-task-commit",
            "--approval-ref",
            approval_ref,
            "--metadata-ref",
            "metadata-ref:test-cli-local-task-commit",
        ]
    )
    assert rc == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["receipt"]["replayed"] is True
    assert replay["receipt"]["receipt_ref"] == committed["receipt"]["receipt_ref"]


def test_founder_loop_cli_records_approval_then_commits_local_task(
    tmp_path: Path,
    capsys,
) -> None:
    state_dir = tmp_path / "founder_loop"
    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "record-action-decision",
            "--action-id",
            "local-task-create-scorecard",
            "--decision",
            "approve",
            "--idempotency-ref",
            "idempotency-ref:test-cli-record-local-task-approval",
            "--metadata-ref",
            "metadata-ref:test-cli-record-local-task-approval",
        ]
    )
    assert rc == 0
    approval = json.loads(capsys.readouterr().out)
    assert approval["safe_refs_only"] is True
    assert approval["receipt"]["status"] == "approved"
    assert approval["receipt"]["approval_ref"].startswith(
        "approval-ref:founder-loop-action:"
    )
    assert approval["receipt"]["action_executed"] is False
    assert approval["receipt"]["approval_grants_execution"] is False
    assert "approval_grants" not in approval["receipt"]

    rc = uaa_founder_loop.main(["--state-dir", str(state_dir), "inspect", "--limit", "6"])
    assert rc == 0
    inspected = json.loads(capsys.readouterr().out)
    action = next(
        item
        for item in inspected["actions"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert action["local_task_commit_eligible"] is True
    approval_ref = str(action["local_task_commit_approval_ref"])

    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "commit-local-task",
            "--action-id",
            "local-task-create-scorecard",
            "--idempotency-ref",
            "idempotency-ref:test-cli-record-then-commit-local-task",
            "--approval-ref",
            approval_ref,
        ]
    )
    assert rc == 0
    committed = json.loads(capsys.readouterr().out)
    assert committed["receipt"]["status"] == "local_task_created"
    assert committed["receipt"]["local_task_created"] is True
    assert committed["receipt"]["external_side_effect_performed"] is False


def test_fcc_v1_003_verifier_passes_current_repo() -> None:
    assert verifier.verify() == []


def test_fcc_v1_003_verifier_flags_release_surface_missing_today_route() -> None:
    release_surface = copy.deepcopy(load_json(verifier.RELEASE_SURFACE_PATH))
    today = next(route for route in release_surface["routes"] if route["path"] == "/today")
    today["backend_routes"] = [
        route
        for route in today["backend_routes"]
        if route["path"] != "/control-center/today/action-envelope"
    ]

    failures = verifier.verify(
        release_surface=release_surface,
        check_files=False,
        check_behavior=False,
    )

    assert any("/today missing route" in failure for failure in failures)


def test_fcc_v1_003_verifier_flags_milestone_overclaim() -> None:
    milestone_status = copy.deepcopy(load_json(verifier.MILESTONE_STATUS_PATH))
    milestone = next(
        item for item in milestone_status["milestones"] if item["id"] == "FCC-V1-003"
    )
    milestone["status"] = "planned"

    failures = verifier.verify(
        milestone_status=milestone_status,
        check_files=False,
        check_behavior=False,
    )

    assert any("FCC-V1-003 milestone status must be implemented" in failure for failure in failures)
