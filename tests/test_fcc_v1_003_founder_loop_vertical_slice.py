from __future__ import annotations

import copy
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from scripts import verify_fcc_v1_003_founder_loop_vertical_slice as verifier
from scripts.dev import uaa_founder_loop
from scripts.verification.repo import load_json
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF,
    FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF,
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
    today_item_to_action_item_ref,
)
from ultimate_ai_agent.core.storage import FounderLoopAuthorityError, FounderLoopRepository
from tests.authority_helpers import issue_workspace_write_authority_lease


client = TestClient(app)


def _approve_local_task_seed_action(state_dir: Path) -> None:
    repo = FounderLoopRepository(state_dir)
    receipt = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:local-task-create-scorecard"
            ),
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
    assert promoted["receipt"]["authority_decision_outcome"] == "allow"
    assert promoted["receipt"]["authority_lease_ref"]
    assert (
        promoted["receipt"]["authority_capability_ref"]
        == FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
    )

    rc = uaa_founder_loop.main(["--state-dir", str(state_dir), "inspect", "--limit", "4"])
    assert rc == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["safe_refs_only"] is True
    assert inspected["raw_paths_omitted"] is True
    assert inspected["actions"][0]["receipt_refs"]
    assert "state_dir" not in inspected


def test_today_action_envelope_requires_workspace_draft_authority_before_mutation(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[],
    )
    item_ref = today_item_to_action_item_ref(verifier.TODAY_ITEM_REF)

    with pytest.raises(FounderLoopAuthorityError) as exc_info:
        repo.promote_today_item_to_action_envelope(
            request=FounderLoopActionEnvelopePromotionRequest(
                today_item_ref=verifier.TODAY_ITEM_REF,
                metadata_refs=["metadata-ref:test-today-envelope-authority-denied"],
            ),
            idempotency_key_ref="idempotency-ref:test-today-envelope-authority-denied",
            active_authority_leases=[],
        )

    assert exc_info.value.code == "FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DENIED"
    assert (
        exc_info.value.required_refs["required_domain_ref"]
        == FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DOMAIN_REF
    )
    assert all(item["item_ref"] != item_ref for item in repo.list_action_inbox())


def test_today_action_envelope_api_requires_workspace_draft_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    AuthorityLeaseStore(authority_state_dir).issue_lease(
        AuthorityLeaseIssueRequest(
            mode=TrustMode.read_only,
            requested_domains={
                AuthorityDomain.memory: [AuthorityCapability.read],
            },
            decision_reason_ref="reason-ref:test-today-envelope-memory-only",
            safe_summary="Memory-only read lease must not grant Workspace draft.",
        ),
        idempotency_ref="idempotency-ref:test-today-envelope-memory-only",
    )

    response = client.post(
        "/control-center/today/action-envelope",
        json={
            "today_item_ref": verifier.TODAY_ITEM_REF,
            "metadata_refs": ["metadata-ref:test-today-envelope-api-denied"],
        },
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:test-today-envelope-api-denied"
        },
    )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_DENIED"
    assert (
        detail["required_refs"]["required_capability_ref"]
        == FOUNDER_LOOP_ACTION_ENVELOPE_AUTHORITY_CAPABILITY_REF
    )
    repo = FounderLoopRepository.from_env()
    item_ref = today_item_to_action_item_ref(verifier.TODAY_ITEM_REF)
    assert all(item["item_ref"] != item_ref for item in repo.list_action_inbox())


def test_founder_loop_cli_commits_local_task_with_safe_refs(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "founder_loop"
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    issue_workspace_write_authority_lease(authority_state_dir)
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "founder_loop"
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    issue_workspace_write_authority_lease(authority_state_dir)
    expected_revision_ref = str(
        FounderLoopRepository(state_dir).action_revision(
            "local-task-create-scorecard"
        )["revision_ref"]
    )
    rc = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "record-action-decision",
            "--action-id",
            "local-task-create-scorecard",
            "--decision",
            "approve",
            "--expected-revision-ref",
            expected_revision_ref,
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
