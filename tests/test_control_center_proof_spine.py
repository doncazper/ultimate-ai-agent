from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
)
from ultimate_ai_agent.core.control_center.proof import (
    ControlCenterProofRecord,
    _operator_run_event_ref,
    _run_detail_ref,
    _with_run_detail,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.storage.founder_loop import FounderLoopActionRecord


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def _assert_no_runtime_authority(payload: dict) -> None:
    text = json.dumps(payload, sort_keys=True)
    for forbidden in [
        "provider_model_call_enabled\": true",
        "runtime_model_call_enabled\": true",
        "connector_write_enabled\": true",
        "connector_send_enabled\": true",
        "browser_execution_enabled\": true",
        "shell_subprocess_execution_enabled\": true",
        "background_autonomy_enabled\": true",
        "production_authority_enabled\": true",
        "raw_content_included\": true",
    ]:
        assert forbidden not in text


def _assert_run_detail_matches_record(record: dict) -> None:
    run_detail = record["run_detail"]
    assert run_detail["schema_version"] == "control-center-proof-run-detail.v1"
    assert run_detail["source"] == "python_core_control_center_proof_run_detail"
    assert run_detail["proof_ref"] == record["proof_ref"]
    assert run_detail["proof_kind"] == record["proof_kind"]
    assert run_detail["run_ref"] in run_detail["related_run_refs"]
    assert run_detail["safe_refs_only"] is True
    assert run_detail["raw_content_included"] is False
    assert run_detail["control_center_presentation_only"] is True
    assert run_detail["full_strength_goal"].startswith("Every action")
    assert "Backend-owned safe refs" in run_detail["repo_safe_scope"]
    assert "remain blocked" in run_detail["blocked_authority_summary"]
    assert run_detail["exact_promotion_path_refs"]
    assert run_detail["operator_run_event_refs"]
    assert run_detail["blocked_authority_refs"]
    assert run_detail["next_safe_action"]


def _seed_blocked_actions_with_late_approved_local_task(
    repo: FounderLoopRepository,
    *,
    blocked_count: int,
) -> None:
    for index in range(blocked_count):
        repo.upsert_action(
            FounderLoopActionRecord(
                item_ref=f"founder-action:bounded-review-{index}",
                title=f"Bounded review action {index}",
                safe_summary="Blocked bounded action used for proof-index coverage.",
                surface="Actions",
                action_kind="blocked_test_action",
                approval_required=True,
                state_change_contract_ref=f"contract-ref:blocked-test:{index}",
                state_change_readiness="blocked_needs_authority",
                blocked_state="Blocked until a scoped authority lane exists.",
                next_safe_action="Inspect the safe refs only.",
            )
        )
    repo.upsert_action(
        FounderLoopActionRecord(
            item_ref="founder-action:late-approved-local-task",
            title="Late approved local task",
            safe_summary="Approved local task after the initial bounded action rows.",
            surface="Actions",
            action_kind=FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
            status="approved",
            approval_required=True,
            approval_envelope_ref="approval-envelope:founder-loop:late-approved-local-task",
            approval_envelope_status="approved_exact_scope",
            state_change_contract_ref=FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
            state_change_readiness="local_task_commit_contract_ready",
            rollback_ref="rollback-not-applicable:late-approved-local-task",
            safe_disable_ref="safe-disable:late-approved-local-task",
            next_safe_action="Inspect or commit the exact approved local task lane.",
        )
    )


def test_proof_index_covers_universal_product_event_kinds(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    index = service.proof_index()

    assert index["schema_version"] == "control-center-proof-index.v1"
    assert index["source"] == "python_core_control_center_proof_index"
    assert index["backend_owned"] is True
    assert index["safe_refs_only"] is True
    assert index["raw_content_included"] is False
    assert index["proof_count"] == len(index["records"])
    assert index["proof_refs"] == [record["proof_ref"] for record in index["records"]]
    assert {
        "daily_loop",
        "action_decision",
        "local_task_commit",
        "memory_decision",
        "evidence_event",
        "web_evidence",
        "provider_draft_preview",
        "connector_draft_proposal",
        "operator_workspace_spine",
        "source_readiness",
        "approval",
        "setup_package",
    }.issubset({record["proof_kind"] for record in index["records"]})
    for record in index["records"]:
        assert record["proof_ref"].startswith("proof-ref:")
        assert record["safe_refs_only"] is True
        assert record["raw_content_included"] is False
        assert record["blocked_authority_refs"]
        assert record["next_safe_action"]
        _assert_run_detail_matches_record(record)
    _assert_no_runtime_authority(index)


def test_provider_draft_preview_proof_is_backend_owned_and_non_invoking(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    detail = service.proof_detail("proof-ref:provider-draft-summarize:exact")
    record = detail["record"]

    assert record["proof_kind"] == "provider_draft_preview"
    assert record["status"] == "exact_core_cli_fixture_proven_default_ui_blocked"
    assert "transient draft preview" in record["safe_summary"]
    assert "safe refs only" in record["safe_summary"]
    assert "Default Control Center invocation" in record["authority_posture"]
    assert "blocked-state:provider-draft-summarize:no-default-control-center-invocation" in (
        record["blocked_authority_refs"]
    )
    assert "blocked-state:provider-draft-summarize:no-default-live-provider-network" in (
        record["blocked_authority_refs"]
    )
    assert "safe-disable-ref:provider-draft-summarize:disable-exact-lane" in (
        record["safe_disable_refs"]
    )
    assert "python scripts/inspect_provider_draft_summarize_lane.py" in (
        record["next_safe_action"]
    )
    assert record["safe_refs_only"] is True
    assert record["raw_content_included"] is False
    _assert_run_detail_matches_record(record)
    _assert_no_runtime_authority(detail)


def test_connector_draft_proposal_proof_is_backend_owned_and_non_sending(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    detail = service.proof_detail("proof-ref:connector-draft-only-proposals:v1")
    record = detail["record"]

    assert record["proof_kind"] == "connector_draft_proposal"
    assert record["status"] == "draft_proposals_ready_no_send_write"
    assert "safe refs" in record["safe_summary"]
    assert "no connector payload" in record["safe_summary"]
    assert "Connector runtime, sends, writes" in record["authority_posture"]
    assert (
        "GET /control-center/sources/readiness"
        in record["backend_route_refs"]
    )
    assert (
        "blocked-state:connector-draft-only:no-connector-send"
        in record["blocked_authority_refs"]
    )
    assert (
        "blocked-state:connector-draft-only:no-connector-write"
        in record["blocked_authority_refs"]
    )
    assert (
        "blocked-state:connector-draft-only:no-oauth"
        in record["blocked_authority_refs"]
    )
    assert (
        "safe-disable-ref:connector-draft-only:disable-local-draft-surface"
        in record["safe_disable_refs"]
    )
    assert "python scripts/inspect_connector_draft_proposals.py" in record[
        "next_safe_action"
    ]
    assert record["safe_refs_only"] is True
    assert record["raw_content_included"] is False
    _assert_run_detail_matches_record(record)
    _assert_no_runtime_authority(detail)


def test_operator_workspace_spine_proof_is_backend_owned_and_read_only(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    detail = service.proof_detail("proof-ref:operator-workspace-spine:read-model")
    record = detail["record"]

    assert record["proof_kind"] == "operator_workspace_spine"
    assert record["status"] == "implemented_read_only_operator_workspace_spine"
    assert "Git posture" in record["safe_summary"]
    assert "read-only posture" in record["authority_posture"]
    assert (
        "GET /control-center/today/summary#operator_workspace_spine"
        in record["backend_route_refs"]
    )
    assert (
        "blocked-state:operator-workspace:no-git-mutation"
        in record["blocked_authority_refs"]
    )
    assert (
        "blocked-state:operator-workspace:no-shell-subprocess-execution"
        in record["blocked_authority_refs"]
    )
    assert (
        "safe-disable-ref:operator-workspace-spine:disable-read-model"
        in record["safe_disable_refs"]
    )
    assert "python scripts/inspect_operator_workspace_spine.py" in record[
        "next_safe_action"
    ]
    assert record["safe_refs_only"] is True
    assert record["raw_content_included"] is False
    _assert_run_detail_matches_record(record)
    _assert_no_runtime_authority(detail)


def test_local_task_commit_proof_blocks_until_commit_receipt(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    local_task_record = next(
        record
        for record in service.proof_index()["records"]
        if record["proof_kind"] == "local_task_commit"
    )

    assert local_task_record["status"] == "blocked_no_local_task_commit_receipt"
    assert (
        "blocked-state:proof-detail:local-task-commit-receipt-missing"
        in local_task_record["blocked_authority_refs"]
    )
    assert not any(
        ref.startswith("receipt:founder-loop-local-task:")
        for ref in local_task_record["receipt_refs"]
    )
    _assert_run_detail_matches_record(local_task_record)


def test_run_detail_derived_refs_include_digest_for_long_safe_ref_collisions() -> None:
    first = (
        "proof-ref:action-decision:"
        "same-long-prefix-that-would-otherwise-collide-"
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:first"
    )
    second = (
        "proof-ref:action-decision:"
        "same-long-prefix-that-would-otherwise-collide-"
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:second"
    )

    first_detail_ref = _run_detail_ref(first)
    second_detail_ref = _run_detail_ref(second)
    first_event_ref = _operator_run_event_ref(first, "action_decision")
    second_event_ref = _operator_run_event_ref(second, "action_decision")

    assert first_detail_ref != second_detail_ref
    assert first_event_ref != second_event_ref
    assert "sha256" in first_detail_ref
    assert "sha256" in second_detail_ref
    assert "sha256" in first_event_ref
    assert "sha256" in second_event_ref


def test_run_detail_attachment_backfills_parent_run_ref_for_parity() -> None:
    record = ControlCenterProofRecord(
        proof_ref="proof-ref:test:run-detail-backfill",
        proof_kind="daily_loop",
        status="read_only",
        title="Run Detail Backfill",
        safe_summary="Safe test proof record.",
        authority_posture="Read-only proof inspection only.",
        route_refs=["route-ref:control-center:proof"],
        backend_route_refs=["GET /control-center/proof/index"],
        run_refs=[],
        evidence_refs=["evidence-ref:test:proof"],
        blocked_authority_refs=["blocked-state:proof-detail:no-runtime-execution"],
        next_safe_action="Inspect safe refs only.",
    )

    attached = _with_run_detail(record)

    assert attached.run_refs
    assert attached.run_detail is not None
    assert attached.run_detail.run_ref in attached.run_refs


def test_daily_loop_surface_proof_refs_resolve_to_universal_proof_index(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    proof_refs = set(service.proof_index()["proof_refs"])
    start_here = service.start_here_summary()
    actions_inbox = service.actions_inbox()
    trust = service.trust_authority_matrix()
    product_proof = service.today_summary()[
        "founder_loop_v1_product_proof_read_model"
    ]

    assert start_here["primary_proof_ref"] in proof_refs
    assert {
        step["proof_ref"] for step in start_here["steps"]
    } <= proof_refs
    next_item = actions_inbox["action_inbox_work_queue_read_model"]["next_item"]
    work_items = actions_inbox["action_inbox_work_queue_read_model"]["work_items"]
    assert next_item["proof_ref"] in proof_refs
    assert {item["proof_ref"] for item in work_items} <= proof_refs
    for item in work_items:
        detail = service.proof_detail(item["proof_ref"])
        assert detail["record"]["proof_ref"] == item["proof_ref"]
        assert detail["record"]["run_detail"]["proof_ref"] == item["proof_ref"]
    core_loop_lane_refs = {
        "trust-lane:start-here-read",
        "trust-lane:today-loop-read",
        "trust-lane:proof-detail-read",
        "trust-lane:action-inbox-work-queue",
        "trust-lane:local-task-commit",
        "trust-lane:memory-review-read",
        "trust-lane:reviewed-memory-write",
        "trust-lane:evidence-timeline-read",
        "trust-lane:provider-draft-summarize",
    }
    for lane in trust["lanes"]:
        if lane["lane_ref"] in core_loop_lane_refs:
            assert set(lane["proof_refs"]) <= proof_refs
    assert {
        binding["primary_proof_ref"]
        for binding in product_proof["productized_surface_bindings"]
    } <= proof_refs


def test_proof_index_covers_action_inbox_next_item_after_initial_bound(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop", seed_defaults=False)
    _seed_blocked_actions_with_late_approved_local_task(repo, blocked_count=6)
    service = FounderLoopControlCenterService(repo)

    next_item = service.actions_inbox()["action_inbox_work_queue_read_model"][
        "next_item"
    ]
    work_items = service.actions_inbox()["action_inbox_work_queue_read_model"][
        "work_items"
    ]
    proof_refs = set(service.proof_index()["proof_refs"])

    assert next_item["item_ref"] == "founder-action:late-approved-local-task"
    assert next_item["proof_ref"] in proof_refs
    assert {item["proof_ref"] for item in work_items} <= proof_refs


def test_proof_cli_default_covers_action_inbox_next_item_after_default_bound(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder_loop"
    repo = FounderLoopRepository(state_dir, seed_defaults=False)
    _seed_blocked_actions_with_late_approved_local_task(repo, blocked_count=12)

    action_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-action-work-queue",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    proof_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-proof",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    action_payload = json.loads(action_result.stdout)
    proof_payload = json.loads(proof_result.stdout)
    next_item = action_payload["action_inbox_work_queue_read_model"]["next_item"]
    work_items = action_payload["action_inbox_work_queue_read_model"]["work_items"]
    proof_refs = set(proof_payload["proof_index"]["proof_refs"])

    assert next_item["item_ref"] == "founder-action:late-approved-local-task"
    assert next_item["proof_ref"] in proof_refs
    assert {item["proof_ref"] for item in work_items} <= proof_refs
    _assert_no_runtime_authority(action_payload)
    _assert_no_runtime_authority(proof_payload)


def test_proof_detail_returns_same_backend_owned_record(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )
    index = service.proof_index()
    proof_ref = index["proof_refs"][0]

    detail = service.proof_detail(proof_ref)

    assert detail["schema_version"] == "control-center-proof-detail.v1"
    assert detail["source"] == "python_core_control_center_proof_detail"
    assert detail["backend_owned"] is True
    assert detail["requested_proof_ref"] == proof_ref
    assert detail["record"]["proof_ref"] == proof_ref
    assert detail["record"] == index["records"][0]
    _assert_run_detail_matches_record(detail["record"])
    _assert_no_runtime_authority(detail)


def test_proof_api_routes_are_read_only_safe_refs() -> None:
    index_response = client.get("/control-center/proof/index")
    assert index_response.status_code == 200
    index_payload = index_response.json()["data"]
    proof_ref = index_payload["proof_refs"][0]

    detail_response = client.get(f"/control-center/proof/{proof_ref}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]

    assert index_payload["backend_owned"] is True
    assert detail_payload["record"]["proof_ref"] == proof_ref
    _assert_run_detail_matches_record(detail_payload["record"])
    assert index_response.json()["redactions_applied"] == [
        "safe_refs_only",
        "bounded_summaries_only",
        "raw_content_omitted",
        "read_only_control_center_projection",
    ]
    _assert_no_runtime_authority(index_payload)
    _assert_no_runtime_authority(detail_payload)


def test_proof_detail_missing_ref_fails_closed() -> None:
    proof_ref = "proof-ref:test:not-present"
    response = client.get(f"/control-center/proof/{proof_ref}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["requested_proof_ref"] == proof_ref
    assert payload["record"]["status"] == "missing_proof_ref"
    _assert_run_detail_matches_record(payload["record"])
    assert "blocked-state:proof-detail:proof-ref-not-found" in (
        payload["record"]["blocked_authority_refs"]
    )
    _assert_no_runtime_authority(payload)


def test_proof_cli_inspects_index_and_detail() -> None:
    index_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "inspect-proof",
            "--limit",
            "4",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    index_payload = json.loads(index_result.stdout)
    proof_ref = index_payload["proof_index"]["proof_refs"][0]

    detail_result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "inspect-proof",
            proof_ref,
            "--limit",
            "4",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    detail_payload = json.loads(detail_result.stdout)

    assert index_payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-proof-index"
    )
    assert detail_payload["command_ref"] == (
        "repo-local-command:founder-loop-inspect-proof-detail"
    )
    assert detail_payload["proof_detail"]["record"]["proof_ref"] == proof_ref
    _assert_no_runtime_authority(index_payload)
    _assert_no_runtime_authority(detail_payload)
