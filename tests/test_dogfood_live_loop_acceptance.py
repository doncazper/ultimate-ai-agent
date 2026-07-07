from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (
    DOGFOOD_LIVE_LOOP_ACTION_REF,
    DOGFOOD_LIVE_LOOP_FIXTURE_REF,
    DogfoodLiveLoopAcceptanceReadModel,
    build_dogfood_live_loop_acceptance_read_model,
    validate_dogfood_live_loop_acceptance,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository, FounderLoopStorageError


ROOT = Path(__file__).resolve().parents[1]


def _workspace_write_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-dogfood-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary=(
            "Test lease grants Workspace write for dogfood local task commit."
        ),
    )


def _issue_workspace_write_lease(state_dir: Path) -> None:
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.write],
            },
            decision_reason_ref="decision-reason-ref:test-dogfood-authority-lease",
            safe_summary=(
                "Test session lease grants Workspace write for dogfood CLI seeding."
            ),
        ),
        idempotency_ref="idempotency-ref:test-dogfood-authority-lease",
        approval_ref="approval-ref:test-authority:dogfood-authority-lease",
    )


def _assert_no_broad_runtime_authority(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for forbidden in [
        'provider_model_call_enabled": true',
        'runtime_model_call_enabled": true',
        'connector_write_enabled": true',
        'connector_send_enabled": true',
        'browser_execution_enabled": true',
        'shell_subprocess_execution_enabled": true',
        'background_autonomy_enabled": true',
        'production_authority_enabled": true',
        'external_side_effect_performed": true',
        'raw_content_included": true',
        'raw_paths_included": true',
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential material",
        "bearer ",
        "secret",
    ]:
        assert forbidden not in text


def test_dogfood_live_loop_acceptance_seeds_one_complete_local_loop(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[_workspace_write_lease()],
    )

    read_model = build_dogfood_live_loop_acceptance_read_model(
        repo=repo,
        seed_fixture=True,
    )
    parsed = DogfoodLiveLoopAcceptanceReadModel(**read_model)

    assert parsed.fixture_ref == DOGFOOD_LIVE_LOOP_FIXTURE_REF
    assert parsed.status == "complete_local_dogfood_loop_proven"
    assert parsed.backend_owned is True
    assert parsed.local_only is True
    assert parsed.fixture_seeded is True
    assert parsed.action_ref == DOGFOOD_LIVE_LOOP_ACTION_REF
    assert parsed.local_task_was_actionable_before_commit is True
    assert parsed.local_task_receipt_recorded is True
    assert parsed.local_task_ref == (
        "local-task:founder-loop:founder-action-local-task-create-scorecard"
    )
    assert parsed.local_task_commit_receipt_ref == (
        "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard:"
        "idempotency-ref-dogfood-live-loop-local-task-commit"
    )
    assert parsed.local_task_commit_proof_ref == (
        "proof-ref:local-task-commit:founder-action-local-task-create-scorecard"
    )
    assert DOGFOOD_LIVE_LOOP_ACTION_REF in parsed.action_refs
    assert parsed.run_ref in parsed.run_refs
    assert parsed.primary_proof_ref in parsed.proof_refs
    assert parsed.local_task_commit_proof_ref in parsed.proof_refs
    assert parsed.local_task_commit_receipt_ref in parsed.receipt_refs
    assert "evidence-ref:founder-loop:local-task-commit" in parsed.evidence_refs
    assert parsed.memory_candidate_refs
    assert "trust-lane:local-task-commit" in parsed.trust_approval_required_lane_refs
    assert "trust-lane:connector-write-low-risk" in (
        parsed.trust_blocked_lane_refs
    )
    assert "trust-lane:production-authority-gate" in (
        parsed.trust_blocked_lane_refs
    )
    assert validate_dogfood_live_loop_acceptance(read_model) == []
    assert {
        "dogfood-live-loop-section:start-here",
        "dogfood-live-loop-section:today",
        "dogfood-live-loop-section:action-inbox",
        "dogfood-live-loop-section:proof-detail",
        "dogfood-live-loop-section:evidence-memory",
        "dogfood-live-loop-section:trust",
    } <= {section.section_ref for section in parsed.sections}
    _assert_no_broad_runtime_authority(read_model)


def test_dogfood_live_loop_fixture_is_replay_safe(tmp_path: Path) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[_workspace_write_lease()],
    )

    first = build_dogfood_live_loop_acceptance_read_model(
        repo=repo,
        seed_fixture=True,
    )
    second = build_dogfood_live_loop_acceptance_read_model(
        repo=repo,
        seed_fixture=True,
    )

    assert first["local_task_commit_receipt_ref"] == second[
        "local_task_commit_receipt_ref"
    ]
    assert first["local_task_ref"] == second["local_task_ref"]
    assert second["status"] == "complete_local_dogfood_loop_proven"
    assert validate_dogfood_live_loop_acceptance(second) == []


def test_dogfood_live_loop_fixture_blocks_preexisting_non_dogfood_receipt(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:test:preexisting-approval",
            metadata_refs=["metadata-ref:test:preexisting-local-task"],
        ),
        idempotency_key_ref="idempotency-ref:test-preexisting-local-task-approval",
    )
    repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
            decision_reason_ref="decision-reason-ref:test:preexisting-commit",
            metadata_refs=["metadata-ref:test:preexisting-local-task"],
        ),
        idempotency_key_ref="idempotency-ref:test-preexisting-local-task-commit",
    )

    try:
        build_dogfood_live_loop_acceptance_read_model(repo=repo, seed_fixture=True)
    except FounderLoopStorageError as exc:
        assert str(exc) == (
            "DOGFOOD_LIVE_LOOP_PREEXISTING_NON_DOGFOOD_LOCAL_TASK_RECEIPT"
        )
    else:  # pragma: no cover - failure message is clearer than pytest.raises match.
        raise AssertionError("preexisting non-dogfood local task receipt was accepted")


def test_dogfood_live_loop_validator_rejects_incomplete_or_nondeterministic_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(
        tmp_path / "founder_loop",
        active_authority_leases=[_workspace_write_lease()],
    )
    read_model = build_dogfood_live_loop_acceptance_read_model(
        repo=repo,
        seed_fixture=True,
    )
    mutated = json.loads(json.dumps(read_model))
    mutated["status"] = "partial_local_dogfood_loop_unseeded_or_incomplete"
    mutated["local_task_commit_receipt_ref"] = (
        "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard:"
        "idempotency-ref-other-local-task-commit"
    )
    mutated["sections"][1]["receipt_refs"] = []

    issues = validate_dogfood_live_loop_acceptance(mutated)

    assert "dogfood-live-loop-status-not-complete" in issues
    assert "dogfood-live-loop-nondeterministic-commit-receipt" in issues
    assert (
        "dogfood-live-loop-section-receipt-ref-missing:"
        "dogfood-live-loop-section:today"
    ) in issues


def test_dogfood_live_loop_cli_inspects_full_loop_with_safe_refs(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    authority_state_dir = tmp_path / "authority"
    _issue_workspace_write_lease(authority_state_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-dogfood-live-loop",
            "--seed-fixture",
        ],
        cwd=ROOT,
        env={**os.environ, AUTHORITY_STATE_DIR_ENV: str(authority_state_dir)},
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["dogfood_live_loop_acceptance"]
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-dogfood-live-loop"
    )
    assert payload["safe_refs_only"] is True
    assert payload["raw_paths_omitted"] is True
    assert read_model["status"] == "complete_local_dogfood_loop_proven"
    assert read_model["local_task_commit_receipt_ref"].startswith(
        "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard"
    )
    assert validate_dogfood_live_loop_acceptance(read_model) == []
    assert str(state_dir).lower() not in result.stdout.lower()
    _assert_no_broad_runtime_authority(payload)
