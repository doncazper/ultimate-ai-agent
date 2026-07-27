from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.routes import runtime_pilot_service
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    AcceptedLocalRunType,
    DurableRunEvent,
    DurableRunEventAppendRequest,
    DurableRunEventKind,
    GoalRuntimeError,
    GoalRuntimeService,
    capture_exact_goal_mutation_approval,
)


@pytest.fixture
def goal_runtime_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, GoalRuntimeService]:
    service = GoalRuntimeService.for_runtime_store(tmp_path)
    monkeypatch.setattr(
        runtime_pilot_service,
        "_goal_runtime_service_getter",
        lambda: service,
    )
    monkeypatch.setenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    return TestClient(app), service


def _create_payload() -> dict[str, object]:
    return {
        "objective": "Deliver one accepted local outcome.",
        "desired_outcome": "A proof-backed durable goal completion.",
        "success_criteria": ["A linked receipt and proof are present."],
        "constraints": ["No external runtime execution."],
        "in_scope_resource_refs": ["resource-ref:local-workspace:bounded"],
        "stop_condition": "Stop on cancellation or missing evidence.",
        "links": {
            "plan_refs": ["plan-ref:api-cli:one"],
            "run_refs": ["run-ref:api-cli:one"],
            "action_inbox_refs": ["action-inbox-ref:api-cli:one"],
            "work_board_refs": ["work-board-ref:api-cli:one"],
        },
        "evidence_refs": ["evidence-ref:api-cli:create"],
    }


def _append_event(
    service: GoalRuntimeService,
    request: DurableRunEventAppendRequest,
) -> DurableRunEvent:
    if request.event_kind == DurableRunEventKind.receipt_recorded.value:
        return service._events.append(request)  # noqa: SLF001
    approval = capture_exact_goal_mutation_approval(
        operation="append-run-event",
        subject_ref=request.run_ref,
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=request.idempotency_ref,
    )
    return service.append_run_event(request, approval_binding=approval)


def test_run_events_get_is_strictly_read_only(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, service = goal_runtime_client
    sync_calls = 0

    def reject_sync(_records: object) -> list[DurableRunEvent]:
        nonlocal sync_calls
        sync_calls += 1
        raise AssertionError("GET must not reconcile durable runtime events")

    monkeypatch.setattr(service, "sync_runtime_invocations", reject_sync)
    response = client.get("/api/runtime/run-events")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert sync_calls == 0
    assert not (service.state_dir / "run_events.jsonl").exists()
    assert not (service.state_dir / "run_event_idempotency.jsonl").exists()
    assert not (
        service.state_dir / "run_event_projection_reservations.jsonl"
    ).exists()


@pytest.mark.parametrize(
    ("path", "payload", "operation"),
    [
        (
            "/api/runtime/local-model/call",
            {
                "base_url": "http://127.0.0.1:9",
                "model_ref": "uaa-local-runtime",
                "messages": [
                    {"role": "user", "content": "projection failure test"}
                ],
                "requested_profile": "local-runtime",
                "safe_summary": "Exercise the redacted projection failure envelope.",
                "timeout_seconds": 0.1,
                "max_response_bytes": 1024,
            },
            "api_runtime_local_model_call",
        ),
        (
            "/api/runtime/command/run",
            {
                "intent": "git_status",
                "safe_summary": "Exercise the redacted command projection failure.",
            },
            "api_runtime_command_run",
        ),
        (
            "/api/runtime/invocations/invocation-ref:test/execute",
            {
                "command_request": {
                    "intent": "git_status",
                    "safe_summary": (
                        "Exercise the redacted approved projection failure."
                    ),
                },
            },
            "api_runtime_invocation_execute",
        ),
    ],
)
@pytest.mark.parametrize(
    ("projection_exception", "expected_code"),
    [
        (
            GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED"),
            "RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED",
        ),
        (
            OSError("raw storage failure must stay redacted"),
            "GOAL_RUNTIME_STORAGE_UNAVAILABLE",
        ),
    ],
)
def test_runtime_projection_failures_keep_the_public_result_envelope(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    payload: dict[str, object],
    operation: str,
    projection_exception: Exception,
    expected_code: str,
) -> None:
    client, _service = goal_runtime_client

    class FailingProjectionGateway:
        @staticmethod
        def invoke_local_model(*_args: object, **_kwargs: object) -> None:
            raise projection_exception

        @staticmethod
        def invoke_command(*_args: object, **_kwargs: object) -> None:
            raise projection_exception

        @staticmethod
        def execute_approved_command(
            *_args: object,
            **_kwargs: object,
        ) -> None:
            raise projection_exception

    monkeypatch.setattr(
        runtime_pilot_service,
        "_runtime_gateway",
        lambda: FailingProjectionGateway(),
    )
    response = client.post(
        path,
        json=payload,
        headers={
            "x-uaa-idempotency-key": (
                f"idempotency-ref:projection-envelope:{operation}"
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["operation"] == operation
    assert body["error"]["code"] == expected_code
    assert body["error"]["details_redacted"] is True


def test_goal_get_rejects_malformed_path_ref_with_safe_envelope(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    response = client.get("/api/runtime/goals/not-a-ref")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["operation"] == "api_runtime_goal"
    assert body["error"]["code"] == "GOAL_REQUEST_REF_INVALID"
    assert body["error"]["details_redacted"] is True


def test_run_events_rejects_malformed_run_ref_with_safe_envelope(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    response = client.get(
        "/api/runtime/run-events",
        params={"run_ref": "abcdefgh"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["operation"] == "api_runtime_run_events"
    assert body["error"]["code"] == "RUN_EVENT_REQUEST_REF_INVALID"
    assert body["error"]["details_redacted"] is True


def test_goal_api_is_idempotent_versioned_and_receipt_verified(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, service = goal_runtime_client

    missing_idempotency = client.post("/api/runtime/goals", json=_create_payload())
    assert missing_idempotency.status_code == 428
    assert missing_idempotency.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    malformed_idempotency = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={"x-uaa-idempotency-key": "abcdefgh"},
    )
    assert malformed_idempotency.status_code == 200
    assert malformed_idempotency.json()["success"] is False
    assert (
        malformed_idempotency.json()["error"]["code"]
        == "GOAL_REQUEST_REF_INVALID"
    )
    malformed_preferred_ref = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:valid-key",
            "x-uaa-idempotency-ref": "abcdefgh",
        },
    )
    assert malformed_preferred_ref.status_code == 200
    assert malformed_preferred_ref.json()["success"] is False
    assert (
        malformed_preferred_ref.json()["error"]["code"]
        == "GOAL_REQUEST_REF_INVALID"
    )

    headers = {"x-uaa-idempotency-key": "idempotency-ref:api-goal-create"}
    created_response = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers=headers,
    )
    assert created_response.status_code == 200
    created_body = created_response.json()
    assert created_body["success"] is True
    goal = created_body["data"]["goal"]
    assert goal["state"] == "active"
    assert created_body["data"]["approval_binding"]["approval_validated"] is True
    assert (
        created_body["data"]["approval_binding"]["standing_authority_granted"]
        is False
    )

    replay = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers=headers,
    ).json()
    assert replay["data"]["goal"] == goal

    stale_edit = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/edit",
        json={"expected_version": 99, "objective": "A stale edit."},
        headers={"x-uaa-idempotency-key": "idempotency-ref:api-goal-stale-edit"},
    ).json()
    assert stale_edit["success"] is False
    assert stale_edit["error"]["code"] == "GOAL_VERSION_CONFLICT"

    requested = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/transition",
        json={
            "expected_version": 1,
            "transition": "request_completion",
            "reason_ref": "reason-ref:api-goal-completion-request",
        },
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:api-goal-completion-request"
            )
        },
    ).json()["data"]["goal"]
    assert requested["state"] == "complete_requested"

    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:api-cli:one",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="Accepted local task recorded a redacted receipt.",
            proof_refs=["proof-ref:api-cli:one"],
            receipt_refs=["receipt-ref:api-cli:one"],
            goal_ref=goal["goal_ref"],
            plan_ref="plan-ref:api-cli:one",
            idempotency_ref="idempotency-ref:api-cli-event-receipt",
            authority_decision_ref="authority-decision-ref:api-cli:accepted-local",
        )
    )
    verified = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/transition",
        json={
            "expected_version": 2,
            "transition": "verify_completion",
            "reason_ref": "reason-ref:api-goal-verifier",
            "completion_evidence": {
                "goal_ref": goal["goal_ref"],
                "goal_version": 2,
                "run_ref": "run-ref:api-cli:one",
                "receipt_ref": "receipt-ref:api-cli:one",
                "proof_ref": "proof-ref:api-cli:one",
                "evidence_ref": "evidence-ref:api-cli:one",
                "verifier_ref": "verifier-ref:receipt-binding:v1",
            },
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:api-goal-verify"},
    ).json()["data"]["goal"]
    assert verified["state"] == "verified_complete"

    goals = client.get("/api/runtime/goals").json()["data"]
    assert goals["verified_complete_count"] == 1
    inspected = client.get(
        f"/api/runtime/goals/{goal['goal_ref']}"
    ).json()["data"]
    assert inspected == verified

    replay_response = client.get(
        "/api/runtime/run-events",
        params={"run_ref": "run-ref:api-cli:one", "after_sequence": 0},
    ).json()
    assert replay_response["success"] is True
    read_model = replay_response["data"]
    assert read_model["status"] == "durable_local_replay"
    assert read_model["durable_event_source"] is True
    assert read_model["replay"]["status"] == "ok"
    assert read_model["event_previews"][0]["receipt_refs"] == [
        "receipt-ref:api-cli:one"
    ]
    assert [event["event_kind"] for event in read_model["event_previews"]] == [
        "receipt_recorded",
        "completion_verified",
    ]
    assert read_model["completed_run_count"] == 1
    assert read_model["goal_lifecycle"]["verified_complete_count"] == 1
    assert read_model["live_event_stream_enabled"] is False


def test_goal_cli_and_api_read_identical_state_after_restart(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    tmp_path: Path,
) -> None:
    client, _service = goal_runtime_client
    created = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={"x-uaa-idempotency-key": "idempotency-ref:cli-parity-create"},
    ).json()["data"]["goal"]

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    command = [
        sys.executable,
        "scripts/dev/uaa_runtime.py",
        "--state-dir",
        str(tmp_path),
        "goals-list",
        "--json",
    ]
    cli = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    cli_goals = json.loads(cli.stdout)["goal_lifecycle"]
    api_goals = client.get("/api/runtime/goals").json()["data"]

    assert cli_goals == api_goals
    assert cli_goals["goals"][0]["goal_ref"] == created["goal_ref"]
    assert cli_goals["goals"][0]["version"] == 1

    shown = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-show",
            created["goal_ref"],
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert json.loads(shown.stdout)["goal"] == created


def test_goal_cli_state_directory_failure_is_redacted(tmp_path: Path) -> None:
    blocked_state_dir = tmp_path / "not-a-directory"
    blocked_state_dir.write_text("bounded fixture", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    command = [
        sys.executable,
        "scripts/dev/uaa_runtime.py",
        "--state-dir",
        str(blocked_state_dir),
        "goals-list",
        "--json",
    ]

    cli = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    assert cli.stdout == ""
    assert cli.stderr.strip() == "Goal lifecycle could not be read safely."
    assert str(blocked_state_dir) not in cli.stderr
    assert "Traceback" not in cli.stderr


def test_goal_cli_mutation_uses_exact_non_standing_approval(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    created = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-create",
            "--request-json",
            json.dumps(_create_payload()),
            "--idempotency-ref",
            "idempotency-ref:cli-goal-create",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(created.stdout)
    assert payload["goal"]["state"] == "active"
    assert payload["approval_binding"]["approval_validated"] is True
    assert payload["standing_authority_granted"] is False
    assert payload["runtime_execution_performed"] is False


def test_goal_event_lifecycle_e2e_reconnect_restart_and_second_run_cancel(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    tmp_path: Path,
) -> None:
    client, service = goal_runtime_client
    created = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={"x-uaa-idempotency-key": "idempotency-ref:e2e-goal-create"},
    ).json()["data"]["goal"]
    run_ref = "run-ref:api-cli:one"
    event_specs = [
        (DurableRunEventKind.goal_linked, "Goal linkage was recorded."),
        (DurableRunEventKind.plan_linked, "Plan linkage was recorded."),
        (DurableRunEventKind.run_started, "Accepted local run started."),
        (
            DurableRunEventKind.approval_wait_entered,
            "The exact local run entered approval wait.",
        ),
    ]
    for index, (kind, summary) in enumerate(event_specs, start=1):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=kind,
                safe_summary=summary,
                goal_ref=created["goal_ref"],
                plan_ref="plan-ref:api-cli:one",
                idempotency_ref=f"idempotency-ref:e2e:event:{index}",
                authority_decision_ref=(
                    "authority-decision-ref:e2e:accepted-local"
                ),
            )
        )

    disconnected = client.get(
        "/api/runtime/run-events",
        params={"run_ref": run_ref, "after_sequence": 0, "limit": 2},
    ).json()["data"]["replay"]
    assert [event["sequence"] for event in disconnected["events"]] == [1, 2]
    assert disconnected["next_cursor"] == 2

    restored = GoalRuntimeService.for_runtime_store(tmp_path)
    resumed_specs = [
        (
            DurableRunEventKind.approval_resumed,
            "The exact approval wait resumed without standing authority.",
        ),
        (
            DurableRunEventKind.worker_restart_recovered,
            "The durable local worker recovered after a controlled restart.",
        ),
        (
            DurableRunEventKind.allowed_local_action_recorded,
            "The accepted read-only local action was recorded.",
        ),
    ]
    for offset, (kind, summary) in enumerate(resumed_specs, start=5):
        _append_event(
            restored,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=kind,
                safe_summary=summary,
                proof_refs=[f"proof-ref:e2e:event:{offset}"],
                goal_ref=created["goal_ref"],
                plan_ref="plan-ref:api-cli:one",
                idempotency_ref=f"idempotency-ref:e2e:event:{offset}",
                authority_decision_ref=(
                    "authority-decision-ref:e2e:accepted-local"
                ),
            )
        )
    _append_event(
        restored,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The accepted local read recorded a redacted receipt.",
            proof_refs=["proof-ref:e2e:accepted-local"],
            receipt_refs=["receipt-ref:e2e:accepted-local"],
            goal_ref=created["goal_ref"],
            plan_ref="plan-ref:api-cli:one",
            idempotency_ref="idempotency-ref:e2e:event:receipt",
            authority_decision_ref="authority-decision-ref:e2e:accepted-local",
        )
    )
    _append_event(
        restored,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.evidence_linked,
            safe_summary="The redacted receipt was linked to durable Evidence.",
            proof_refs=["proof-ref:e2e:accepted-local"],
            receipt_refs=["receipt-ref:e2e:accepted-local"],
            goal_ref=created["goal_ref"],
            plan_ref="plan-ref:api-cli:one",
            idempotency_ref="idempotency-ref:e2e:event:evidence",
            authority_decision_ref="authority-decision-ref:e2e:accepted-local",
        )
    )

    requested = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json={
            "expected_version": 1,
            "transition": "request_completion",
            "reason_ref": "reason-ref:e2e:completion-request",
        },
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:e2e:completion-request"
        },
    ).json()["data"]["goal"]
    verified = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json={
            "expected_version": requested["version"],
            "transition": "verify_completion",
            "reason_ref": "reason-ref:e2e:deterministic-verifier",
            "completion_evidence": {
                "goal_ref": created["goal_ref"],
                "goal_version": requested["version"],
                "run_ref": run_ref,
                "receipt_ref": "receipt-ref:e2e:accepted-local",
                "proof_ref": "proof-ref:e2e:accepted-local",
                "evidence_ref": "evidence-ref:e2e:accepted-local",
                "verifier_ref": "verifier-ref:e2e:receipt-binding:v1",
            },
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:e2e:verify"},
    ).json()["data"]["goal"]
    assert verified["state"] == "verified_complete"

    reconnected = client.get(
        "/api/runtime/run-events",
        params={
            "run_ref": run_ref,
            "after_sequence": disconnected["next_cursor"],
            "limit": 100,
        },
    ).json()["data"]["replay"]
    assert reconnected["status"] == "ok"
    assert [event["sequence"] for event in reconnected["events"]] == list(
        range(3, 11)
    )
    assert reconnected["events"][-1]["event_kind"] == "completion_verified"

    cancelled_payload = _create_payload()
    cancelled_payload["links"] = {
        **cancelled_payload["links"],
        "run_refs": ["run-ref:e2e:cancelled"],
    }
    cancelled_goal = client.post(
        "/api/runtime/goals",
        json=cancelled_payload,
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:e2e:cancel-goal-create"
        },
    ).json()["data"]["goal"]
    cancelled = client.post(
        f"/api/runtime/goals/{cancelled_goal['goal_ref']}/transition",
        json={
            "expected_version": 1,
            "transition": "cancel",
            "reason_ref": "reason-ref:e2e:operator-cancel",
        },
        headers={"x-uaa-idempotency-key": "idempotency-ref:e2e:goal-cancel"},
    ).json()["data"]["goal"]
    assert cancelled["state"] == "cancelled"
    for index, kind in enumerate(
        (
            DurableRunEventKind.cancellation_requested,
            DurableRunEventKind.cancelled,
        ),
        start=1,
    ):
        _append_event(
            restored,
            DurableRunEventAppendRequest(
                run_ref="run-ref:e2e:cancelled",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=kind,
                safe_summary=f"Cancellation lifecycle stage {index} was recorded.",
                proof_refs=(
                    ["proof-ref:e2e:operator-cancel"]
                    if kind == DurableRunEventKind.cancelled
                    else []
                ),
                receipt_refs=(
                    ["receipt-ref:e2e:operator-cancel"]
                    if kind == DurableRunEventKind.cancelled
                    else []
                ),
                goal_ref=cancelled_goal["goal_ref"],
                idempotency_ref=f"idempotency-ref:e2e:cancel-event:{index}",
                authority_decision_ref=(
                    "authority-decision-ref:e2e:operator-cancel"
                ),
            )
        )

    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "inspect-run-events",
            "--run-ref",
            "run-ref:e2e:cancelled",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    cli_read_model = json.loads(cli.stdout)["runtime_run_events"]
    api_read_model = client.get(
        "/api/runtime/run-events",
        params={"run_ref": "run-ref:e2e:cancelled"},
    ).json()["data"]
    assert cli_read_model == api_read_model
    assert cli_read_model["stream_summaries"][-1]["terminal_event_kind"] == (
        "cancelled"
    )
