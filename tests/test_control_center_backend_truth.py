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
    ControlCenterBackendTruth,
    backend_truth_integrity_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (
    DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF,
    build_dogfood_live_loop_acceptance_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


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
        "issue-ref:dogfood-live-loop-durable-proof-unavailable"
    ]
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
    env = os.environ.copy()
    env["UAA_FOUNDER_LOOP_STATE_DIR"] = str(tmp_path / "cli-state")
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

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-backend-truth"
    )
    assert payload["backend_truth"]["backend_revision_ref"] == (
        f"commit-ref:git:{SHA}"
    )
    assert payload["backend_truth"]["authority_posture"][
        "control_center_grants_authority"
    ] is False
    assert payload["safe_refs_only"] is True
