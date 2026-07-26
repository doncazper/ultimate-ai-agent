from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.backend_truth import (
    BACKEND_TRUTH_SOURCE_REF,
    CRITICAL_SURFACES,
    FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION,
    ControlCenterBackendTruth,
    backend_truth_integrity_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (
    DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,
    build_dogfood_live_loop_acceptance_read_model,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
    local_task_ref_for_action,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageError,
)


NOW = datetime(2026, 7, 22, 18, 0, tzinfo=UTC)
SHA = "1" * 40
ROOT = Path(__file__).resolve().parents[1]


def _identity():
    return build_identity(env={"UAA_BUILD_COMMIT": SHA})


def _workspace_write_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:test-backend-truth-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Test lease permits the exact local fixture commit.",
    )


def test_backend_truth_is_short_lived_revision_bound_and_fail_closed(
    tmp_path,
) -> None:
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "empty"),
        now=NOW,
        identity=_identity(),
    )

    assert truth["source_ref"] == BACKEND_TRUTH_SOURCE_REF
    assert truth["backend_revision_ref"] == f"commit-ref:git:{SHA}"
    assert truth["source_revision_bound"] is True
    assert [item["surface_ref"] for item in truth["critical_surfaces"]] == [
        item.surface_ref for item in CRITICAL_SURFACES
    ]
    assert truth["evidence_binding"]["status"] == "unverified_incomplete"
    assert truth["evidence_binding"]["issue_refs"] == [
        "issue-ref:founder-loop-durable-local-task-proof-unavailable"
    ]
    assert (
        truth["evidence_binding"]["acceptance_schema_version"]
        == FOUNDER_LOOP_DURABLE_EVIDENCE_SCHEMA_VERSION
    )
    assert truth["authority_posture"]["control_center_grants_authority"] is False
    assert truth["authority_posture"]["production_authority_enabled"] is False
    assert ControlCenterBackendTruth(**truth).model_dump(mode="json") == truth


def test_backend_truth_rejects_completion_when_source_revision_is_unbound(
    tmp_path,
) -> None:
    state_dir = tmp_path / "unbound"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    build_dogfood_live_loop_acceptance_read_model(repo=repo, seed_fixture=True)

    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(state_dir),
        now=NOW,
        identity=build_identity(env={}, repo_root=tmp_path / "not-a-repository"),
    )

    assert truth["source_revision_bound"] is False
    assert truth["evidence_binding"]["status"] == "invalid_evidence"
    assert "issue-ref:backend-source-revision-unbound" in truth[
        "evidence_binding"
    ]["issue_refs"]


def test_backend_truth_survives_reload_only_with_exact_durable_loop_proof(
    tmp_path,
) -> None:
    state_dir = tmp_path / "durable"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    build_dogfood_live_loop_acceptance_read_model(repo=repo, seed_fixture=True)

    reloaded = FounderLoopRepository(state_dir)
    truth = build_control_center_backend_truth(
        repo=reloaded,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "verified_complete"
    assert truth["evidence_binding"]["issue_refs"] == []
    assert truth["evidence_binding"]["receipt_refs"]
    assert truth["evidence_binding"]["proof_refs"]
    assert truth["evidence_binding"]["evidence_refs"]


def test_backend_truth_accepts_normal_durable_local_task_evidence(
    tmp_path,
) -> None:
    state_dir = tmp_path / "normal-durable"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:operator:approve-local-task",
            metadata_refs=["metadata-ref:operator:daily-loop"],
        ),
        idempotency_key_ref="idempotency-ref:operator:approve-local-task",
    )
    repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
            decision_reason_ref="decision-reason-ref:operator:commit-local-task",
            metadata_refs=["metadata-ref:operator:daily-loop"],
        ),
        idempotency_key_ref="idempotency-ref:operator:commit-local-task",
    )

    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(state_dir),
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "verified_complete"
    assert truth["evidence_binding"]["issue_refs"] == []
    assert (
        "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard:"
        "idempotency-ref-operator-commit-local-task"
        in truth["evidence_binding"]["receipt_refs"]
    )


def test_backend_truth_matches_proof_to_each_committed_action(
    tmp_path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "multiple-local-task-actions"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:operator:approve-local-task",
        ),
        idempotency_key_ref="idempotency-ref:operator:approve-local-task",
    )
    repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
        ),
        idempotency_key_ref="idempotency-ref:operator:commit-local-task",
    )
    reloaded = FounderLoopRepository(state_dir)
    today = reloaded.today_summary()
    older_item_ref = "founder-action:older-uncommitted-local-task"
    today["actions"] = [
        {
            "item_ref": older_item_ref,
            "action_kind": "local_task_create",
            "local_task_ref": local_task_ref_for_action(older_item_ref),
            "receipt_refs": [],
            "evidence_refs": ["evidence-ref:older-uncommitted-local-task"],
        },
        *today["actions"],
    ]
    monkeypatch.setattr(
        reloaded,
        "today_summary",
        lambda **_kwargs: today,
    )

    truth = build_control_center_backend_truth(
        repo=reloaded,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "verified_complete"
    assert truth["evidence_binding"]["issue_refs"] == []


def test_backend_truth_discovers_durable_commit_beyond_today_page(
    tmp_path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "durable-beyond-today-page"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:operator:approve-local-task",
        ),
        idempotency_key_ref="idempotency-ref:operator:approve-local-task",
    )
    repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
        ),
        idempotency_key_ref="idempotency-ref:operator:commit-local-task",
    )
    reloaded = FounderLoopRepository(state_dir)
    today = reloaded.today_summary(limit=50)
    today["actions"] = [
        {
            "item_ref": f"founder-action:uncommitted-{index}",
            "action_kind": "review_only",
        }
        for index in range(50)
    ]
    monkeypatch.setattr(reloaded, "today_summary", lambda **_kwargs: today)

    truth = build_control_center_backend_truth(
        repo=reloaded,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "verified_complete"
    assert truth["evidence_binding"]["receipt_refs"]


def test_backend_truth_rejects_one_corrupt_claim_among_valid_receipts(
    tmp_path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "valid-and-corrupt-local-task-actions"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:operator:approve-local-task",
        ),
        idempotency_key_ref="idempotency-ref:operator:approve-local-task",
    )
    repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
        ),
        idempotency_key_ref="idempotency-ref:operator:commit-local-task",
    )
    reloaded = FounderLoopRepository(state_dir)
    today = reloaded.today_summary()
    corrupt_item_ref = "founder-action:corrupt-second"
    corrupt_receipt_ref = (
        "receipt:founder-loop-local-task:corrupt-second:"
        "idempotency-ref-corrupt-second"
    )
    corrupt_action = {
        **today["actions"][0],
        "item_ref": corrupt_item_ref,
        "action_kind": "local_task_create",
        "local_task_ref": local_task_ref_for_action(corrupt_item_ref),
        "local_task_commit_receipt_ref": corrupt_receipt_ref,
        "receipt_refs": [corrupt_receipt_ref],
    }
    today["actions"] = [corrupt_action, *today["actions"]]
    monkeypatch.setattr(reloaded, "today_summary", lambda **_kwargs: today)

    truth = build_control_center_backend_truth(
        repo=reloaded,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "invalid_evidence"
    assert corrupt_receipt_ref in truth["evidence_binding"]["receipt_refs"]
    assert truth["evidence_binding"]["issue_refs"] == [
        "issue-ref:founder-loop-durable-proof-invalid"
    ]


def test_backend_truth_redacts_unsafe_claimed_receipt_ref(
    tmp_path,
    monkeypatch,
) -> None:
    repo = FounderLoopRepository(tmp_path / "unsafe-claim")
    today = repo.today_summary()
    today["actions"] = [
        {
            "item_ref": "founder-action:unsafe-claim",
            "action_kind": "local_task_create",
            "local_task_ref": "local-task:founder-loop:unsafe-claim",
            "local_task_commit_receipt_ref": "/Users/private/raw-receipt",
            "receipt_refs": ["/Users/private/raw-receipt"],
        },
    ]
    monkeypatch.setattr(repo, "today_summary", lambda **_kwargs: today)

    truth = build_control_center_backend_truth(
        repo=repo,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "invalid_evidence"
    assert truth["evidence_binding"]["receipt_refs"] == [
        "receipt-ref:founder-loop-durable-proof-invalid-claim"
    ]
    assert "/Users/" not in json.dumps(truth)


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("approval_ref", "approval-ref:tampered"),
        ("local_task_ref", "local-task:founder-loop:tampered"),
        ("idempotency_key_ref", "idempotency-ref:tampered"),
        (
            "payload_fingerprint_ref",
            "payload-fingerprint:founder-loop-local-task:" + "0" * 64,
        ),
        ("audit_ref", "audit:founder-loop-local-task:tampered"),
        (
            "evidence_timeline_event_ref",
            "evidence-timeline:local-task/tampered",
        ),
        ("evidence_refs", ["evidence-ref:tampered"]),
        ("approval_status", "pending"),
        ("approval_reason_refs", []),
        ("authority_decision_ref", None),
        (
            "authority_decision_ref",
            "authority-policy-decision-ref:sha256:" + "0" * 24,
        ),
        ("authority_decision_outcome", "deny"),
        ("authority_lease_ref", None),
        ("authority_lease_ref", "authority-lease-ref:substituted"),
        (
            "authority_audit_ref",
            "audit-ref:authority-policy:sha256:" + "0" * 24,
        ),
        (
            "authority_policy_receipt_ref",
            "receipt-ref:authority-policy:sha256:" + "0" * 24,
        ),
        ("authority_domain_ref", "authority-domain-ref:memory"),
        ("authority_capability_ref", "authority-capability-ref:read"),
        ("authority_required_mode_ref", "authority-mode-ref:read-only"),
        ("safe_disable_ref", "safe-disable-ref:tampered"),
        ("rollback_ref", "rollback-ref:tampered"),
        ("safe_disable_posture_ref", "safe-disable-posture-ref:tampered"),
    ],
)
def test_backend_truth_rejects_tampered_durable_receipt_bindings(
    tmp_path,
    field_name: str,
    replacement,
) -> None:
    state_dir = tmp_path / f"tampered-{field_name}"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    decision = repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref="decision-reason-ref:operator:approve-local-task",
        ),
        idempotency_key_ref="idempotency-ref:operator:approve-local-task",
    )
    committed = repo.commit_local_task(
        action_id="local-task-create-scorecard",
        request=FounderLoopLocalTaskCommitRequest(
            approval_ref=str(decision["approval_ref"]),
        ),
        idempotency_key_ref="idempotency-ref:operator:commit-local-task",
    )
    receipt_ref = str(committed["receipt_ref"])
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as connection:
        row = connection.execute(
            "SELECT receipt_json FROM local_task_commit_receipts "
            "WHERE receipt_ref = ?",
            (receipt_ref,),
        ).fetchone()
        assert row is not None
        receipt = json.loads(str(row[0]))
        receipt[field_name] = replacement
        connection.execute(
            "UPDATE local_task_commit_receipts SET receipt_json = ? "
            "WHERE receipt_ref = ?",
            (
                json.dumps(receipt, sort_keys=True, separators=(",", ":")),
                receipt_ref,
            ),
        )

    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(state_dir),
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "invalid_evidence"
    assert truth["evidence_binding"]["receipt_refs"] == [receipt_ref]
    assert truth["evidence_binding"]["issue_refs"] == [
        "issue-ref:founder-loop-durable-proof-invalid"
    ]


def test_backend_truth_marks_a_corrupt_durable_receipt_invalid(tmp_path) -> None:
    state_dir = tmp_path / "corrupt-durable"
    repo = FounderLoopRepository(
        state_dir,
        active_authority_leases=[_workspace_write_lease()],
    )
    build_dogfood_live_loop_acceptance_read_model(repo=repo, seed_fixture=True)
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as connection:
        row = connection.execute(
            "SELECT receipt_json FROM local_task_commit_receipts WHERE receipt_ref = ?",
            (DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,),
        ).fetchone()
        assert row is not None
        receipt = json.loads(str(row[0]))
        receipt["receipt_ref"] = "receipt:founder-loop-local-task:corrupt-test-proof"
        connection.execute(
            "UPDATE local_task_commit_receipts SET receipt_json = ? WHERE receipt_ref = ?",
            (
                json.dumps(receipt, sort_keys=True, separators=(",", ":")),
                DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,
            ),
        )

    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(state_dir),
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "invalid_evidence"
    assert truth["evidence_binding"]["issue_refs"]
    assert truth["evidence_binding"]["receipt_refs"]
    assert truth["authority_posture"]["control_center_grants_authority"] is False


def test_backend_truth_distinguishes_storage_failure_from_first_run(
    tmp_path,
    monkeypatch,
) -> None:
    repo = FounderLoopRepository(tmp_path / "storage-failure")

    def fail_storage(**_kwargs):
        raise FounderLoopStorageError("FOUNDER_LOOP_STORAGE_CORRUPT")

    monkeypatch.setattr(
        "ultimate_ai_agent.core.control_center.backend_truth."
        "_build_founder_loop_durable_evidence",
        fail_storage,
    )

    truth = build_control_center_backend_truth(
        repo=repo,
        now=NOW,
        identity=_identity(),
    )

    assert truth["evidence_binding"]["status"] == "storage_unavailable"
    assert truth["evidence_binding"]["issue_refs"] == [
        "issue-ref:backend-truth-storage-unavailable"
    ]
    assert truth["evidence_binding"]["receipt_refs"] == []


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda value: value.update(schema_version="backend-truth.v0"),
            "literal_error",
        ),
        (
            lambda value: value.update(
                backend_revision_ref="commit-ref:git:untrusted"
            ),
            "envelope integrity mismatch",
        ),
        (
            lambda value: value["critical_surfaces"].reverse(),
            "surface binding drift",
        ),
        (
            lambda value: value["critical_surfaces"][0].update(
                frontend_paths=["/substituted"]
            ),
            "surface binding drift",
        ),
        (
            lambda value: value["authority_posture"].update(
                production_authority_enabled=True
            ),
            "literal_error",
        ),
        (
            lambda value: value["evidence_binding"].update(
                status="verified_complete",
                issue_refs=["issue-ref:proof-corrupt"],
            ),
            "Verified evidence cannot retain validation issues",
        ),
        (
            lambda value: value["evidence_binding"].update(
                acceptance_schema_version="dogfood-live-loop-acceptance.v1",
            ),
            "literal_error",
        ),
        (
            lambda value: value["evidence_binding"].update(
                acceptance_integrity_ref=(
                    "proof-ref:founder-loop-durable-evidence:sha256:not-a-digest"
                ),
            ),
            "Durable evidence integrity ref is invalid",
        ),
        (
            lambda value: value.update(
                envelope_integrity_ref=(
                    "proof-ref:backend-truth-envelope:sha256:" + "0" * 64
                )
            ),
            "envelope integrity mismatch",
        ),
    ],
)
def test_backend_truth_rejects_contract_authority_and_integrity_tampering(
    tmp_path,
    mutate,
    expected: str,
) -> None:
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "tamper"),
        now=NOW,
        identity=_identity(),
    )
    mutate(truth)

    with pytest.raises(ValidationError, match=expected):
        ControlCenterBackendTruth(**truth)


def test_recomputed_hash_cannot_promote_unverified_evidence(tmp_path) -> None:
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "optimistic"),
        now=NOW,
        identity=_identity(),
    )
    truth["evidence_binding"]["status"] = "verified_complete"
    truth["envelope_integrity_ref"] = backend_truth_integrity_ref(
        {key: value for key, value in truth.items() if key != "envelope_integrity_ref"}
    )

    with pytest.raises(ValidationError, match="validation issues"):
        ControlCenterBackendTruth(**truth)


def test_backend_truth_contains_only_redacted_safe_refs(tmp_path) -> None:
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "redaction"),
        now=NOW,
        identity=_identity(),
    )
    serialized = json.dumps(truth, sort_keys=True).lower()

    assert "/users/" not in serialized
    assert "raw prompt" not in serialized
    assert "raw response" not in serialized
    assert "provider payload" not in serialized
    assert '"runtime_model_call_enabled": true' not in serialized
    assert '"browser_or_web_execution_enabled": true' not in serialized
    assert '"connector_write_enabled": true' not in serialized


def test_backend_truth_cli_matches_the_core_contract(tmp_path) -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    env = os.environ.copy()
    env["UAA_FOUNDER_LOOP_STATE_DIR"] = str(tmp_path / "cli-state")
    env["UAA_BUILD_COMMIT"] = head
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_founder_loop.py"),
            "inspect-backend-truth",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-backend-truth"
    )
    assert payload["backend_truth"]["backend_revision_ref"] == (
        f"commit-ref:git:{head}"
    )
    assert payload["backend_truth"]["authority_posture"][
        "control_center_grants_authority"
    ] is False
    assert payload["safe_refs_only"] is True


def test_backend_truth_cli_rejects_stale_prebound_revision(tmp_path) -> None:
    env = os.environ.copy()
    env["UAA_FOUNDER_LOOP_STATE_DIR"] = str(tmp_path / "stale-cli-state")
    env["UAA_BUILD_COMMIT"] = "f" * 40

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_founder_loop.py"),
            "inspect-backend-truth",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked"
    assert payload["error_ref"] == "CONTROL_CENTER_BACKEND_TRUTH_STORAGE_BLOCKED"
    assert completed.stderr == ""


def test_backend_truth_cli_redacts_repository_initialization_failure(
    tmp_path,
) -> None:
    state_dir = tmp_path / "corrupt-cli-state"
    state_dir.mkdir()
    (state_dir / "founder_loop.sqlite3").write_bytes(b"not-a-sqlite-database")
    env = os.environ.copy()
    env["UAA_FOUNDER_LOOP_STATE_DIR"] = str(state_dir)
    env["UAA_BUILD_COMMIT"] = SHA

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dev" / "uaa_founder_loop.py"),
            "inspect-backend-truth",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["status"] == "blocked"
    assert payload["error_ref"] == "CONTROL_CENTER_BACKEND_TRUTH_STORAGE_BLOCKED"
    serialized = json.dumps(payload)
    assert str(state_dir) not in serialized
    assert completed.stderr == ""
