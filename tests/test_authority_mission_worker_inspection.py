from __future__ import annotations

import argparse
import json
from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from scripts.dev.uaa_runtime_mission_worker_inspection import inspect
from scripts.dev.uaa_runtime import main as runtime_main
from tests.test_authority_mission_orchestrator import _orchestration_fixture
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority.contracts import AUTHORITY_STATE_DIR_ENV
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    LocalMissionWorker,
    LocalMissionWorkerConfiguration,
    MissionWorkerPlatform,
    MissionWorkerStore,
    MissionWorkerJobStatus,
    build_mission_worker_read_model,
    mission_worker_identity_ref,
    mission_worker_job_binding,
)
from ultimate_ai_agent.core.execution.mission_worker_inspection import (
    build_local_mission_worker_inspection,
)
from ultimate_ai_agent.core.time import utc_now


def _seed(tmp_path):
    orchestrator, _, _, _, request, _ = _orchestration_fixture(
        tmp_path,
        suffix="worker-inspection",
        dependency_graph=[[]],
        shared_state=True,
    )
    with patch("platform.system", return_value="Darwin"):
        configuration = LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
        )
    worker = LocalMissionWorker(
        orchestrator=orchestrator,
        store=MissionWorkerStore(orchestrator.step_store.state_dir),
        configuration=configuration,
    )
    worker.enqueue(request)
    return orchestrator.step_store.state_dir


def test_cli_and_api_expose_same_backend_owned_safe_worker_truth(
    tmp_path, monkeypatch, capsys
) -> None:
    state_dir = _seed(tmp_path)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(state_dir))
    expected = build_local_mission_worker_inspection(state_dir=state_dir).model_dump(
        mode="json"
    )

    assert inspect(argparse.Namespace(state_dir=str(state_dir), json=True)) == 0
    cli = json.loads(capsys.readouterr().out)["authority_mission_worker"]
    response = TestClient(app).get("/api/runtime/authority-missions/worker-state")

    assert response.status_code == 200
    api = response.json()["data"]
    for value in (cli, api, expected):
        value.pop("checked_at")
    assert cli == api == expected
    assert api["jobs"][0]["recovery_status"] == "pending"
    assert api["jobs"][0]["request_payload_persisted"] is False
    assert api["execution_authority_granted"] is False
    assert api["linux_surface_posture"] == "render_placeholder"
    assert api["windows_surface_posture"] == "render_placeholder"
    rendered = json.dumps(api)
    assert str(tmp_path) not in rendered
    assert "relative_path" not in rendered


def test_human_cli_is_primary_and_uninitialized_state_is_truthful(
    tmp_path, capsys
) -> None:
    state_dir = tmp_path / "uninitialized"

    assert inspect(argparse.Namespace(state_dir=str(state_dir), json=False)) == 0

    output = capsys.readouterr().out
    assert "Authority mission worker inspection" in output
    assert "Configured: false" in output
    assert "Queue: 0/16" in output
    assert "Inspection grants execution authority: false" in output
    assert not state_dir.exists()


def test_registered_runtime_cli_command_uses_the_same_inspection_contract(
    tmp_path, capsys
) -> None:
    state_dir = _seed(tmp_path)

    assert (
        runtime_main(
            [
                "--state-dir",
                str(state_dir),
                "inspect-authority-mission-worker",
                "--json",
            ]
        )
        == 0
    )

    payload = json.loads(capsys.readouterr().out)
    assert (
        payload["command_ref"]
        == "repo-local-command:uaa-runtime-inspect-authority-mission-worker"
    )
    assert payload["execution_performed"] is False
    assert (
        payload["authority_mission_worker"]["jobs"][0]["request_payload_persisted"]
        is False
    )


def test_worker_route_is_protected_read_only_and_non_authorizing() -> None:
    route = next(
        item
        for item in build_api_manifest(app).routes
        if item.path == "/api/runtime/authority-missions/worker-state"
    )

    assert route.operation_id == "get_api_runtime_authority_missions_worker_state"
    assert route.route_classification == "local_sensitive"
    assert route.side_effect_class == "local_dev_workspace_only"
    assert route.protected_route is True
    assert route.approval_posture == "not_required_for_route_classification"
    assert route.idempotency_required is False
    assert route.rate_limit_targeted is False
    assert "without starting a worker" in route.classification_reason


def test_api_manifest_declares_exact_worker_truth_and_denials() -> None:
    manifest = build_api_manifest(app)

    for capability in {
        "authority_mission_worker_fenced_claim_heartbeats",
        "authority_mission_worker_boot_reconciliation",
        "authority_mission_worker_read_only_inspection",
        "authority_mission_worker_graceful_shutdown_and_kill_switch",
    }:
        assert capability in manifest.capabilities_declared
    for capability in {
        "authority_mission_worker_remote_queue_or_public_daemon",
        "authority_mission_worker_default_enabled_execution",
        "authority_mission_worker_cached_or_minted_authority",
    }:
        assert capability in manifest.capabilities_blocked


def test_boot_recovery_read_model_classifies_every_required_posture(
    tmp_path, monkeypatch
) -> None:
    current = [utc_now()]
    with patch("platform.system", return_value="Darwin"):
        enabled = LocalMissionWorkerConfiguration(
            enabled=True,
            observed_platform=MissionWorkerPlatform.macos,
            claim_ttl_seconds=5,
            heartbeat_interval_seconds=1,
        )
    claimed_orchestrator, _, _, _, claimed_request, _ = _orchestration_fixture(
        tmp_path / "claimed",
        suffix="worker-classifier-claimed",
        dependency_graph=[[]],
        shared_state=True,
    )
    claimed_orchestrator.step_store._clock = lambda: current[0]  # noqa: SLF001
    claimed_store = MissionWorkerStore(
        claimed_orchestrator.step_store.state_dir,
        clock=lambda: current[0],
    )
    claimed_worker = LocalMissionWorker(
        orchestrator=claimed_orchestrator,
        store=claimed_store,
        configuration=enabled,
    )
    claimed_worker.enqueue(claimed_request)
    claimed_binding = mission_worker_job_binding(claimed_request)
    claimed_store.claim(
        claimed_binding.job_ref,
        worker_ref=mission_worker_identity_ref(
            "mission-worker-ref:test:classifier-claimed"
        ),
        ttl_seconds=5,
    )
    active = build_mission_worker_read_model(
        store=claimed_store,
        orchestrator=claimed_orchestrator,
    )
    assert active.jobs[0].recovery_status == "actively_claimed"
    current[0] += timedelta(seconds=5)
    stale = build_mission_worker_read_model(
        store=claimed_store,
        orchestrator=claimed_orchestrator,
    )
    assert stale.jobs[0].recovery_status == "stale_claim"

    succeeded_orchestrator, _, _, _, succeeded_request, _ = _orchestration_fixture(
        tmp_path / "succeeded",
        suffix="worker-classifier-succeeded",
        dependency_graph=[[]],
        shared_state=True,
    )
    succeeded_store = MissionWorkerStore(succeeded_orchestrator.step_store.state_dir)
    succeeded_worker = LocalMissionWorker(
        orchestrator=succeeded_orchestrator,
        store=succeeded_store,
        configuration=enabled,
    )
    assert (
        succeeded_worker.run_once(
            succeeded_request,
            worker_ref="mission-worker-ref:test:classifier-succeeded",
        ).status
        == "succeeded"
    )
    succeeded = build_mission_worker_read_model(
        store=succeeded_store,
        orchestrator=succeeded_orchestrator,
    )
    assert succeeded.jobs[0].recovery_status == "succeeded"

    recovery_orchestrator, _, _, _, recovery_request, _ = _orchestration_fixture(
        tmp_path / "recovery",
        suffix="worker-classifier-recovery",
        dependency_graph=[[]],
        shared_state=True,
    )
    recovery_store = MissionWorkerStore(recovery_orchestrator.step_store.state_dir)
    recovery_worker = LocalMissionWorker(
        orchestrator=recovery_orchestrator,
        store=recovery_store,
        configuration=enabled,
    )
    recovery_worker.enqueue(recovery_request)
    recovery_binding = mission_worker_job_binding(recovery_request)
    recovery_owner = mission_worker_identity_ref(
        "mission-worker-ref:test:classifier-recovery"
    )
    recovery_claim = recovery_store.claim(
        recovery_binding.job_ref,
        worker_ref=recovery_owner,
        ttl_seconds=5,
    )
    recovery_store.complete(
        recovery_binding.job_ref,
        worker_ref=recovery_owner,
        claim_ref=recovery_claim.claim_ref or "",
        generation=recovery_claim.generation,
        status=MissionWorkerJobStatus.recovery_required,
        reason_refs=["reason-ref:mission-worker:classifier-recovery"],
        evidence_refs=[],
    )
    recovery = build_mission_worker_read_model(
        store=recovery_store,
        orchestrator=recovery_orchestrator,
    )
    assert recovery.jobs[0].recovery_status == "recovery_required"

    blocked_orchestrator, blocked_dispatcher, _, _, blocked_request, _ = (
        _orchestration_fixture(
            tmp_path / "blocked",
            suffix="worker-classifier-blocked",
            dependency_graph=[[], [0]],
            shared_state=True,
        )
    )
    adapter = next(iter(blocked_dispatcher.adapters.values()))
    original_invoke = adapter.invoke

    def fail_first(request):
        return original_invoke(request).model_copy(
            update={
                "succeeded": False,
                "safe_summary": "The deterministic test adapter reported failure.",
            }
        )

    monkeypatch.setattr(adapter, "invoke", fail_first)
    blocked_store = MissionWorkerStore(blocked_orchestrator.step_store.state_dir)
    blocked_worker = LocalMissionWorker(
        orchestrator=blocked_orchestrator,
        store=blocked_store,
        configuration=enabled,
    )
    blocked_worker.run_once(
        blocked_request,
        worker_ref="mission-worker-ref:test:classifier-blocked",
    )
    blocked = build_mission_worker_read_model(
        store=blocked_store,
        orchestrator=blocked_orchestrator,
    )
    assert blocked.jobs[0].recovery_status == "dependency_blocked"
