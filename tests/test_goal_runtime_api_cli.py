from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from scripts.dev import uaa_runtime
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state
from ultimate_ai_agent.api.routes import runtime_pilot_service
from ultimate_ai_agent.core.runtime_gateway import goal_runtime as goal_runtime_module
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeAuthority,
    RuntimeCriterionVerificationBinding,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
)
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    AcceptedLocalRunType,
    DurableCriterionVerifierBinding,
    DurableRunEvent,
    DurableRunEventAppendRequest,
    DurableRunEventKind,
    GOAL_COMPLETION_VERIFIER_REF,
    GoalCreateRequest,
    GoalEditRequest,
    GoalRuntimeError,
    GoalRuntimeService,
    GoalTransitionRequest,
    PersistentGoal,
    build_goal_criterion_ref,
    build_goal_completion_evidence_ref,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStore


def _criterion_bindings(
    goal: PersistentGoal,
    proof_refs: list[str],
    *,
    evaluator_prefix: str,
) -> list[DurableCriterionVerifierBinding]:
    return [
        DurableCriterionVerifierBinding(
            goal_ref=goal.goal_ref,
            goal_version=goal.version,
            criterion_ref=build_goal_criterion_ref(
                goal,
                criterion_index=index,
                criterion_summary=criterion,
            ),
            proof_ref=proof_ref,
            verifier_ref=GOAL_COMPLETION_VERIFIER_REF,
            evaluator_receipt_ref=f"{evaluator_prefix}:{index + 1}",
        )
        for index, (criterion, proof_ref) in enumerate(
            zip(goal.success_criteria, proof_refs, strict=True)
        )
    ]


@pytest.fixture
def goal_runtime_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, GoalRuntimeService]]:
    service = GoalRuntimeService.for_runtime_store(tmp_path)
    monkeypatch.setattr(
        runtime_pilot_service,
        "_goal_runtime_service_getter",
        lambda: service,
    )
    monkeypatch.setenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    reset_api_rate_limit_state()
    client = TestClient(app)
    try:
        yield client, service
    finally:
        client.close()
        reset_api_rate_limit_state()


def _create_payload() -> dict[str, object]:
    return {
        "text_redaction_posture": "operator_authored_redacted_summary_only",
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


def _approved_mutation_ref(
    service: GoalRuntimeService,
    *,
    operation: str,
    goal_ref: str | None,
    request: GoalCreateRequest | GoalEditRequest | GoalTransitionRequest | DurableRunEventAppendRequest,
    idempotency_ref: str,
) -> str:
    spec = service.prepare_goal_mutation_approval(
        operation=operation,
        goal_ref=goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    service.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:test-explicit-goal-mutation-approval",
    )
    return spec.approval_ref


def _api_approval_ref(
    client: TestClient,
    *,
    operation: str,
    request: dict[str, object],
    idempotency_ref: str,
    goal_ref: str | None = None,
    submission_ref: str | None = None,
) -> str:
    endpoint = (
        "/api/runtime/goals/approval-requests/create"
        if operation == "create"
        else f"/api/runtime/goals/{goal_ref}/approval-requests/{operation}"
    )
    headers = {"x-uaa-idempotency-key": idempotency_ref}
    if submission_ref is not None:
        headers["x-uaa-goal-submission-ref"] = submission_ref
    prepared = client.post(
        endpoint,
        json=request,
        headers=headers,
    ).json()
    spec = prepared["data"]["approval_request"]
    decided = client.post(
        (
            "/api/runtime/goals/approval-requests/"
            f"{spec['approval_request_ref']}/decision"
        ),
        json={
            "decision": "approve",
            "decision_reason_ref": "reason-ref:test-explicit-goal-mutation-approval",
        },
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:goal-approval-decision:"
                f"{spec['approval_request_ref']}"
            )
        },
    ).json()
    assert decided.get("success") is True, decided
    return str(spec["approval_ref"])


def test_goal_approval_decision_and_revoke_bind_exact_idempotency_headers(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    prepared = client.post(
        "/api/runtime/goals/approval-requests/create",
        json=_create_payload(),
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:approval-route-header-binding"
            )
        },
    ).json()
    spec = prepared["data"]["approval_request"]
    decision_path = (
        "/api/runtime/goals/approval-requests/"
        f"{spec['approval_request_ref']}/decision"
    )
    decision_payload = {
        "decision": "approve",
        "decision_reason_ref": "reason-ref:approval-route-header-binding",
    }

    missing = client.post(decision_path, json=decision_payload)
    assert missing.status_code == 428
    assert missing.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    malformed = client.post(
        decision_path,
        json=decision_payload,
        headers={"x-uaa-idempotency-key": "short"},
    )
    assert malformed.status_code == 400
    assert malformed.json()["code"] == "API_IDEMPOTENCY_INVALID"
    mismatched = client.post(
        decision_path,
        json=decision_payload,
        headers={"x-uaa-idempotency-key": "idempotency-ref:wrong-decision"},
    ).json()
    assert mismatched["success"] is False
    assert mismatched["error"]["code"] == (
        "GOAL_MUTATION_APPROVAL_IDEMPOTENCY_MISMATCH"
    )
    decision_idempotency_ref = (
        "idempotency-ref:goal-approval-decision:"
        f"{spec['approval_request_ref']}"
    )
    decided = client.post(
        decision_path,
        json=decision_payload,
        headers={"x-uaa-idempotency-key": decision_idempotency_ref},
    ).json()
    assert decided["success"] is True

    revoke_payload = {
        "approval_ref": spec["approval_ref"],
        "decision_reason_ref": "reason-ref:approval-route-revoke-binding",
    }
    revoke_path = "/api/runtime/goals/approval-requests/revoke"
    missing_revoke = client.post(revoke_path, json=revoke_payload)
    assert missing_revoke.status_code == 428
    mismatched_revoke = client.post(
        revoke_path,
        json=revoke_payload,
        headers={"x-uaa-idempotency-key": "idempotency-ref:wrong-revoke"},
    ).json()
    assert mismatched_revoke["success"] is False
    assert mismatched_revoke["error"]["code"] == (
        "GOAL_MUTATION_APPROVAL_IDEMPOTENCY_MISMATCH"
    )
    revoked = client.post(
        revoke_path,
        json=revoke_payload,
        headers={
            "x-uaa-idempotency-key": (
                "idempotency-ref:goal-approval-revoke:"
                f"{spec['approval_ref']}"
            )
        },
    ).json()
    assert revoked["success"] is True
    assert revoked["data"]["approval_decision"]["status"] == "revoked"


def test_goal_approval_prepare_persists_exact_submission_before_response(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, service = goal_runtime_client
    submission_ref = (
        "submission-ref:control-center-goal-mutation:prepare-response-loss"
    )
    idempotency_ref = "idempotency-ref:approval-prepare-response-loss"
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:"
        + "a" * 64
    )
    payload = {
        **_create_payload(),
        "evidence_refs": [submission_evidence_ref],
    }
    headers = {
        "x-uaa-idempotency-key": idempotency_ref,
        "x-uaa-goal-submission-ref": submission_ref,
    }

    first = client.post(
        "/api/runtime/goals/approval-requests/create",
        json=payload,
        headers=headers,
    ).json()
    assert first["success"] is True, json.dumps(first, sort_keys=True)
    recovery = first["data"]["submission_recovery"]
    assert recovery["submission_ref"] == submission_ref
    assert recovery["idempotency_ref"] == idempotency_ref
    assert recovery["submission_evidence_ref"] == submission_evidence_ref
    assert recovery["request_payload"] == GoalCreateRequest.model_validate(
        payload
    ).model_dump(mode="json")

    restarted = GoalRuntimeService(service.state_dir)
    aggregate = restarted.aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=50,
    )
    [durable_recovery] = aggregate[4].records
    assert durable_recovery.submission_ref == recovery["submission_ref"]
    assert durable_recovery.operation == recovery["operation"]
    assert durable_recovery.goal_ref == recovery["goal_ref"]
    assert durable_recovery.request_payload == recovery["request_payload"]
    assert durable_recovery.idempotency_ref == recovery["idempotency_ref"]
    assert (
        durable_recovery.submission_evidence_ref
        == recovery["submission_evidence_ref"]
    )
    assert (
        durable_recovery.request_fingerprint_ref
        == recovery["request_fingerprint_ref"]
    )
    assert durable_recovery.status == "pending"

    retried = client.post(
        "/api/runtime/goals/approval-requests/create",
        json=payload,
        headers=headers,
    ).json()
    assert retried["success"] is True
    assert (
        retried["data"]["approval_request"]
        == first["data"]["approval_request"]
    )
    assert retried["data"]["submission_recovery"] == recovery
    assert GoalRuntimeService(service.state_dir).aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=50,
    )[4].pending_count == 1


def test_goal_mutation_route_durably_rejects_terminal_failure_without_wedging(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    create_payload = _create_payload()
    create_idempotency_ref = "idempotency-ref:submission-base"
    create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=create_payload,
        idempotency_ref=create_idempotency_ref,
    )
    created = client.post(
        "/api/runtime/goals",
        json=create_payload,
        headers={
            "x-uaa-idempotency-key": create_idempotency_ref,
            "x-uaa-goal-approval-ref": create_approval_ref,
        },
    ).json()["data"]["goal"]
    submission_ref = "submission-ref:control-center-goal-mutation:api-pending"
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "c" * 64
    )
    edit_payload = {
        "expected_version": 99,
        "text_redaction_posture": ("operator_authored_redacted_summary_only"),
        "objective": "A safely retained ambiguous edit.",
        "evidence_refs": [submission_evidence_ref],
    }
    edit_idempotency_ref = "idempotency-ref:submission-edit"
    edit_approval_ref = _api_approval_ref(
        client,
        operation="edit",
        goal_ref=created["goal_ref"],
        request=edit_payload,
        idempotency_ref=edit_idempotency_ref,
        submission_ref=submission_ref,
    )
    response = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/edit",
        json=edit_payload,
        headers={
            "x-uaa-idempotency-key": edit_idempotency_ref,
            "x-uaa-goal-submission-ref": submission_ref,
            "x-uaa-goal-approval-ref": edit_approval_ref,
        },
    )
    assert response.json()["success"] is False

    recovery = client.get("/api/runtime/run-events").json()["data"][
        "goal_mutation_submissions"
    ]
    assert recovery["pending_count"] == 0
    assert recovery["rejected_count"] == 1
    assert recovery["records"][0]["submission_ref"] == submission_ref
    assert recovery["records"][0]["submission_evidence_ref"] == (
        submission_evidence_ref
    )
    assert recovery["records"][0]["status"] == "rejected"
    assert recovery["records"][0]["rejection_reason_ref"] == (
        "reason-ref:goal-mutation-rejected:goal-version-conflict"
    )
    assert recovery["records"][0]["resolved_at"] is not None

    exact_retry = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/edit",
        json=edit_payload,
        headers={
            "x-uaa-idempotency-key": edit_idempotency_ref,
            "x-uaa-goal-submission-ref": submission_ref,
            "x-uaa-goal-approval-ref": edit_approval_ref,
        },
    ).json()
    assert exact_retry["success"] is False
    assert exact_retry["error"]["code"] == "GOAL_SUBMISSION_PREVIOUSLY_REJECTED"

    corrected_evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "d" * 64
    )
    corrected_payload = {
        "expected_version": 1,
        "text_redaction_posture": ("operator_authored_redacted_summary_only"),
        "objective": "A corrected bounded edit.",
        "evidence_refs": [corrected_evidence_ref],
    }
    corrected_idempotency_ref = "idempotency-ref:submission-edit-corrected"
    corrected_approval_ref = _api_approval_ref(
        client,
        operation="edit",
        goal_ref=created["goal_ref"],
        request=corrected_payload,
        idempotency_ref=corrected_idempotency_ref,
        submission_ref=(
            "submission-ref:control-center-goal-mutation:api-corrected"
        ),
    )
    corrected = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/edit",
        json=corrected_payload,
        headers={
            "x-uaa-idempotency-key": corrected_idempotency_ref,
            "x-uaa-goal-submission-ref": (
                "submission-ref:control-center-goal-mutation:api-corrected"
            ),
            "x-uaa-goal-approval-ref": corrected_approval_ref,
        },
    ).json()
    assert corrected["success"] is True
    final_recovery = client.get("/api/runtime/run-events").json()["data"][
        "goal_mutation_submissions"
    ]
    assert final_recovery["pending_count"] == 0
    assert final_recovery["rejected_count"] == 1
    assert final_recovery["committed_count"] == 1


def _append_event(
    service: GoalRuntimeService,
    request: DurableRunEventAppendRequest,
) -> DurableRunEvent:
    if request.event_kind in {
        DurableRunEventKind.receipt_recorded.value,
        DurableRunEventKind.cancelled.value,
        DurableRunEventKind.failed_terminal.value,
        DurableRunEventKind.dead_lettered.value,
    }:
        request_fingerprint_ref = service._events._request_fingerprint(  # noqa: SLF001
            request
        )
        runtime_store = RuntimeInvocationStore(
            service.state_dir / "trusted_evaluator_runtime"
        )
        invocation_idempotency_ref = goal_runtime_module._sha256_ref(  # noqa: SLF001
            "idempotency-ref:trusted-evaluator-receipt",
            {"request_fingerprint_ref": request_fingerprint_ref},
        )
        created = runtime_store.create_invocation(
            RuntimeInvocationRequest(
                requested_authority=RuntimeAuthority.local_model,
                input_ref=request_fingerprint_ref,
                safe_summary=(
                    "Record one exact trusted evaluator receipt projection."
                ),
                mission_ref=request.goal_ref,
                action_ref=request.run_ref,
                metadata_refs=[request_fingerprint_ref],
            ),
            idempotency_ref=invocation_idempotency_ref,
            local_model_gateway_validated=True,
        ).record
        receipt = RuntimeInvocationReceipt(
            receipt_ref=request.receipt_refs[0],
            invocation_ref=created.invocation_ref,
            policy_decision_ref=created.policy_decision.policy_decision_ref,
            invocation_status=RuntimeInvocationStatus.receipt_recorded,
            evidence_refs=[request_fingerprint_ref],
            criterion_verification_bindings=[
                RuntimeCriterionVerificationBinding.model_validate(
                    binding.model_dump(mode="json")
                )
                for binding in request.criterion_verifier_bindings
            ],
            safe_summary=request.safe_summary,
        )
        runtime_store.record_receipt(
            created.invocation_ref,
            receipt,
            idempotency_ref=goal_runtime_module._sha256_ref(  # noqa: SLF001
                "idempotency-ref:trusted-evaluator-receipt-record",
                {"request_fingerprint_ref": request_fingerprint_ref},
            ),
        )
        return service._events.append(  # noqa: SLF001
            request,
            trusted_source=goal_runtime_module.TrustedRunEventSourceBinding(
                source_kind="runtime_evaluator_receipt",
                source_ref=created.invocation_ref,
                source_fingerprint_ref=request_fingerprint_ref,
            ),
        )
    if request.event_kind in {
        DurableRunEventKind.completion_verified.value,
    }:
        return service._events.append(request)  # noqa: SLF001
    approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=request,
        idempotency_ref=request.idempotency_ref,
    )
    return service.append_run_event(request, approval_ref=approval_ref)


def test_run_events_get_does_not_reconcile_without_durable_sources(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, service = goal_runtime_client
    sync_calls = 0

    def reject_sync(_records: object) -> list[DurableRunEvent]:
        nonlocal sync_calls
        sync_calls += 1
        raise AssertionError("empty GET must not reconcile runtime events")

    monkeypatch.setattr(service, "sync_runtime_invocations", reject_sync)
    response = client.get("/api/runtime/run-events")

    assert response.status_code == 200
    assert response.json()["success"] is True
    completion_posture = response.json()["data"]["goal_lifecycle"]
    assert completion_posture["completion_verification_available"] is False
    assert completion_posture["completion_verification_state"] == (
        "blocked_missing_trusted_criterion_evaluator"
    )
    assert sync_calls == 0
    assert not service.state_dir.exists()
    assert not (service.state_dir / "run_events.jsonl").exists()
    assert not (service.state_dir / "run_event_idempotency.jsonl").exists()
    assert not (service.state_dir / "run_event_projection_reservations.jsonl").exists()


@pytest.mark.parametrize(
    "path",
    [
        "/api/runtime/goals",
        "/api/runtime/goals/goal-ref:read-only:missing",
        "/api/runtime/run-events",
    ],
)
def test_goal_runtime_get_routes_do_not_initialize_state(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    path: str,
) -> None:
    client, service = goal_runtime_client

    response = client.get(path)

    assert response.status_code == 200
    assert not service.state_dir.exists()


def test_run_events_read_model_keeps_cleared_goals_restorable(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    create_payload = _create_payload()
    create_idempotency_ref = "idempotency-ref:restorable-goal-create"
    create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=create_payload,
        idempotency_ref=create_idempotency_ref,
    )
    created = client.post(
        "/api/runtime/goals",
        json=create_payload,
        headers={
            "x-uaa-idempotency-key": create_idempotency_ref,
            "x-uaa-goal-approval-ref": create_approval_ref,
        },
    ).json()["data"]["goal"]
    clear_payload = {
        "expected_version": created["version"],
        "transition": "clear",
        "reason_ref": "reason-ref:restorable-goal-clear",
    }
    clear_idempotency_ref = "idempotency-ref:restorable-goal-clear"
    clear_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=created["goal_ref"],
        request=clear_payload,
        idempotency_ref=clear_idempotency_ref,
    )
    cleared = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json=clear_payload,
        headers={
            "x-uaa-idempotency-key": clear_idempotency_ref,
            "x-uaa-goal-approval-ref": clear_approval_ref,
        },
    ).json()["data"]["goal"]
    assert cleared["state"] == "cleared"

    default_goals = client.get("/api/runtime/goals").json()["data"]["goals"]
    assert default_goals == []
    operator_goals = client.get("/api/runtime/run-events").json()["data"][
        "goal_lifecycle"
    ]["goals"]
    assert operator_goals == [cleared]

    restore_payload = {
        "expected_version": cleared["version"],
        "transition": "restore",
        "reason_ref": "reason-ref:restorable-goal-restore",
    }
    restore_idempotency_ref = "idempotency-ref:restorable-goal-restore"
    restore_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=created["goal_ref"],
        request=restore_payload,
        idempotency_ref=restore_idempotency_ref,
    )
    restored = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json=restore_payload,
        headers={
            "x-uaa-idempotency-key": restore_idempotency_ref,
            "x-uaa-goal-approval-ref": restore_approval_ref,
        },
    ).json()["data"]["goal"]
    assert restored["state"] == "active"


@pytest.mark.parametrize(
    ("path", "payload", "operation"),
    [
        (
            "/api/runtime/local-model/call",
            {
                "base_url": "http://127.0.0.1:9",
                "model_ref": "uaa-local-runtime",
                "messages": [{"role": "user", "content": "projection failure test"}],
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
@pytest.mark.parametrize("durable_truth", ["receipt", "missing", "unreadable"])
def test_runtime_projection_failures_keep_the_public_result_envelope(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    payload: dict[str, object],
    operation: str,
    projection_exception: Exception,
    expected_code: str,
    durable_truth: str,
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

    class ProjectionTruthStore:
        @staticmethod
        def get_invocation_for_idempotency(
            _idempotency_ref: str,
        ) -> object | None:
            if durable_truth == "unreadable":
                raise OSError("raw durable ledger failure must stay redacted")
            if durable_truth == "missing":
                return None
            return SimpleNamespace(
                invocation_ref="invocation-ref:api-projection-failure",
                receipt=SimpleNamespace(
                    receipt_ref="receipt-ref:api-projection-failure",
                    execution_performed=True,
                    model_call_performed=(operation == "api_runtime_local_model_call"),
                    command_execution_performed=(
                        operation != "api_runtime_local_model_call"
                    ),
                ),
            )

    monkeypatch.setattr(
        runtime_pilot_service,
        "_runtime_store",
        lambda: ProjectionTruthStore(),
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
    assert "raw durable ledger failure" not in json.dumps(body)
    if durable_truth == "receipt":
        assert body["data"] == {
            "execution_outcome": "durable_receipt_recovered",
            "execution_performed": True,
            "model_call_performed": operation == "api_runtime_local_model_call",
            "command_execution_performed": (
                operation != "api_runtime_local_model_call"
            ),
            "invocation_ref": "invocation-ref:api-projection-failure",
            "receipt_ref": "receipt-ref:api-projection-failure",
            "retry_allowed": False,
        }
        assert body["error"]["retryable"] is False
    elif durable_truth == "missing":
        assert body["data"] == {
            "execution_outcome": "not_started",
            "execution_performed": False,
            "model_call_performed": False,
            "command_execution_performed": False,
            "invocation_ref": None,
            "receipt_ref": None,
            "retry_allowed": True,
        }
        assert body["error"]["retryable"] is True
    else:
        assert body["data"] == {
            "execution_outcome": "unknown_after_projection_failure",
            "execution_performed": None,
            "model_call_performed": None,
            "command_execution_performed": None,
            "invocation_ref": None,
            "receipt_ref": None,
            "retry_allowed": False,
        }
        assert body["error"]["retryable"] is False


def test_goal_get_rejects_malformed_path_ref_with_safe_envelope(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
) -> None:
    client, _service = goal_runtime_client
    response = client.get("/api/runtime/goals/not-a-ref")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["operation"] == "api_runtime_goal"
    assert body["trace_id"] == "failure-trace-ref:goal-runtime:goal-read"
    assert body["error"]["code"] == "GOAL_REQUEST_REF_INVALID"
    assert body["error"]["details_redacted"] is True

    run_response = client.get(
        "/api/runtime/run-events",
        params={"run_ref": "not-a-ref"},
    )
    run_body = run_response.json()
    assert run_body["success"] is False
    assert run_body["trace_id"] == ("failure-trace-ref:goal-runtime:run-event-read")
    assert "not-a-ref" not in json.dumps(run_body)


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
        headers={
            "x-uaa-idempotency-key": "abcdefgh",
            "x-uaa-goal-approval-ref": "approval-ref:untrusted",
        },
    )
    assert malformed_idempotency.status_code == 200
    assert malformed_idempotency.json()["success"] is False
    assert malformed_idempotency.json()["error"]["code"] == "GOAL_REQUEST_REF_INVALID"
    malformed_preferred_ref = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:valid-key",
            "x-uaa-idempotency-ref": "abcdefgh",
            "x-uaa-goal-approval-ref": "approval-ref:untrusted",
        },
    )
    assert malformed_preferred_ref.status_code == 200
    assert malformed_preferred_ref.json()["success"] is False
    assert malformed_preferred_ref.json()["error"]["code"] == "GOAL_REQUEST_REF_INVALID"

    missing_approval = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers={"x-uaa-idempotency-key": "idempotency-ref:missing-approval"},
    )
    assert missing_approval.status_code == 200
    assert missing_approval.json()["success"] is False
    assert missing_approval.json()["error"]["code"] == (
        "GOAL_MUTATION_APPROVAL_REQUIRED"
    )

    create_payload = _create_payload()
    create_idempotency_ref = "idempotency-ref:api-goal-create"
    create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=create_payload,
        idempotency_ref=create_idempotency_ref,
    )
    headers = {
        "x-uaa-idempotency-key": create_idempotency_ref,
        "x-uaa-goal-approval-ref": create_approval_ref,
    }
    created_response = client.post(
        "/api/runtime/goals",
        json=create_payload,
        headers=headers,
    )
    assert created_response.status_code == 200
    created_body = created_response.json()
    assert created_body["success"] is True
    goal = created_body["data"]["goal"]
    assert goal["state"] == "active"
    assert created_body["data"]["approval_binding"]["approval_validated"] is True
    assert (
        created_body["data"]["approval_binding"]["standing_authority_granted"] is False
    )

    replay = client.post(
        "/api/runtime/goals",
        json=_create_payload(),
        headers=headers,
    ).json()
    assert replay["data"]["goal"] == goal

    stale_edit_payload = {
        "expected_version": 99,
        "text_redaction_posture": ("operator_authored_redacted_summary_only"),
        "objective": "A stale edit.",
    }
    stale_edit_idempotency_ref = "idempotency-ref:api-goal-stale-edit"
    stale_edit_approval_ref = _api_approval_ref(
        client,
        operation="edit",
        goal_ref=goal["goal_ref"],
        request=stale_edit_payload,
        idempotency_ref=stale_edit_idempotency_ref,
    )
    stale_edit = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/edit",
        json=stale_edit_payload,
        headers={
            "x-uaa-idempotency-key": stale_edit_idempotency_ref,
            "x-uaa-goal-approval-ref": stale_edit_approval_ref,
        },
    ).json()
    assert stale_edit["success"] is False
    assert stale_edit["error"]["code"] == "GOAL_VERSION_CONFLICT"

    request_completion_payload = {
        "expected_version": 1,
        "transition": "request_completion",
        "reason_ref": "reason-ref:api-goal-completion-request",
    }
    request_completion_idempotency_ref = (
        "idempotency-ref:api-goal-completion-request"
    )
    request_completion_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=goal["goal_ref"],
        request=request_completion_payload,
        idempotency_ref=request_completion_idempotency_ref,
    )
    requested = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/transition",
        json=request_completion_payload,
        headers={
            "x-uaa-idempotency-key": request_completion_idempotency_ref,
            "x-uaa-goal-approval-ref": request_completion_approval_ref,
        },
    ).json()["data"]["goal"]
    assert requested["state"] == "complete_requested"

    requested_goal = service.goals.get(goal["goal_ref"])
    criterion_bindings = _criterion_bindings(
        requested_goal,
        ["proof-ref:api-cli:one"],
        evaluator_prefix="evaluator-receipt-ref:api-cli",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:api-cli:one",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="Accepted local task recorded a redacted receipt.",
            proof_refs=[
                "proof-ref:api-cli:one",
                *(binding.evaluator_receipt_ref for binding in criterion_bindings),
            ],
            receipt_refs=["receipt-ref:api-cli:one"],
            criterion_verifier_bindings=criterion_bindings,
            goal_ref=goal["goal_ref"],
            plan_ref="plan-ref:api-cli:one",
            idempotency_ref="idempotency-ref:api-cli-event-receipt",
            authority_decision_ref="authority-decision-ref:api-cli:accepted-local",
        ),
    )
    completion_evidence_ref = build_goal_completion_evidence_ref(
        requested_goal,
        run_ref="run-ref:api-cli:one",
        receipt_ref="receipt-ref:api-cli:one",
        proof_ref="proof-ref:api-cli:one",
        criterion_verifier_bindings=criterion_bindings,
        plan_ref="plan-ref:api-cli:one",
    )
    blocked_submission_ref = (
        "submission-ref:control-center-goal-mutation:blocked-completion"
    )
    blocked_submission_evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:"
        "transition:sha256:" + "9" * 64
    )
    blocked_completion_payload = {
        "expected_version": 2,
        "transition": "verify_completion",
        "reason_ref": "reason-ref:api-goal-verifier",
        "evidence_refs": [blocked_submission_evidence_ref],
        "completion_evidence": {
            "goal_ref": goal["goal_ref"],
            "goal_version": 2,
            "run_ref": "run-ref:api-cli:one",
            "receipt_ref": "receipt-ref:api-cli:one",
            "proof_ref": "proof-ref:api-cli:one",
            "criterion_proof_refs": ["proof-ref:api-cli:one"],
            "evidence_ref": completion_evidence_ref,
            "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
        },
    }
    blocked_completion_idempotency_ref = "idempotency-ref:api-goal-verify"
    blocked_completion_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=goal["goal_ref"],
        request=blocked_completion_payload,
        idempotency_ref=blocked_completion_idempotency_ref,
        submission_ref=blocked_submission_ref,
    )
    blocked_completion = client.post(
        f"/api/runtime/goals/{goal['goal_ref']}/transition",
        json=blocked_completion_payload,
        headers={
            "x-uaa-idempotency-key": blocked_completion_idempotency_ref,
            "x-uaa-goal-submission-ref": blocked_submission_ref,
            "x-uaa-goal-approval-ref": blocked_completion_approval_ref,
        },
    ).json()
    assert blocked_completion["success"] is False
    assert blocked_completion["error"]["code"] == (
        "GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE"
    )
    assert service.goals.get(goal["goal_ref"]).state == "complete_requested"
    blocked_recovery = client.get("/api/runtime/run-events").json()["data"][
        "goal_mutation_submissions"
    ]
    assert blocked_recovery["rejected_count"] == 1
    assert blocked_recovery["records"][0]["submission_ref"] == (blocked_submission_ref)
    assert blocked_recovery["records"][0]["status"] == "rejected"

    transition_request = runtime_pilot_service.GoalTransitionRequest.model_validate(
        {
            "expected_version": 2,
            "transition": "verify_completion",
            "reason_ref": "reason-ref:trusted-internal-goal-verifier",
            "completion_evidence": {
                "goal_ref": goal["goal_ref"],
                "goal_version": 2,
                "run_ref": "run-ref:api-cli:one",
                "receipt_ref": "receipt-ref:api-cli:one",
                "proof_ref": "proof-ref:api-cli:one",
                "criterion_proof_refs": ["proof-ref:api-cli:one"],
                "evidence_ref": completion_evidence_ref,
                "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
            },
        }
    )
    approval_ref = _approved_mutation_ref(
        service,
        operation="transition",
        goal_ref=goal["goal_ref"],
        request=transition_request,
        idempotency_ref="idempotency-ref:trusted-internal-goal-verify",
    )
    verified, _approval = service.transition_goal(
        goal["goal_ref"],
        transition_request,
        idempotency_ref="idempotency-ref:trusted-internal-goal-verify",
        approval_ref=approval_ref,
    )
    verified = verified.model_dump(mode="json")
    assert verified["state"] == "verified_complete"

    goals = client.get("/api/runtime/goals").json()["data"]
    assert goals["verified_complete_count"] == 1
    inspected = client.get(f"/api/runtime/goals/{goal['goal_ref']}").json()["data"]
    assert inspected["goal"] == verified
    assert inspected["mutation_provenance"]["entry_count"] == 3

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
    create_payload = _create_payload()
    create_idempotency_ref = "idempotency-ref:cli-parity-create"
    create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=create_payload,
        idempotency_ref=create_idempotency_ref,
    )
    created = client.post(
        "/api/runtime/goals",
        json=create_payload,
        headers={
            "x-uaa-idempotency-key": create_idempotency_ref,
            "x-uaa-goal-approval-ref": create_approval_ref,
        },
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
    shown_payload = json.loads(shown.stdout)
    assert shown_payload["goal"] == created
    assert shown_payload["mutation_provenance"]["entry_count"] == 1
    api_shown = client.get(f"/api/runtime/goals/{created['goal_ref']}").json()["data"]
    assert api_shown == {
        "goal": shown_payload["goal"],
        "mutation_provenance": shown_payload["mutation_provenance"],
    }


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
    payload = json.loads(cli.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "GOAL_RUNTIME_STORAGE_UNAVAILABLE"
    assert payload["raw_error_omitted"] is True
    assert cli.stderr == ""
    assert str(blocked_state_dir) not in cli.stdout
    assert "Traceback" not in cli.stdout


def test_goal_show_json_rejects_malformed_ref_without_traceback(
    tmp_path: Path,
) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-show",
            "not-a-ref",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    payload = json.loads(cli.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "GOAL_REQUEST_VALIDATION_FAILED"
    assert payload["raw_error_omitted"] is True
    assert cli.stderr == ""
    assert "Traceback" not in cli.stdout
    assert str(tmp_path) not in cli.stdout


@pytest.mark.parametrize(
    ("command_name", "extra_args"),
    [
        ("goal-create", []),
        ("goal-edit", ["goal-ref:json-failure"]),
        ("goal-transition", ["goal-ref:json-failure"]),
    ],
)
def test_goal_cli_mutation_validation_failures_honor_json(
    tmp_path: Path,
    command_name: str,
    extra_args: list[str],
) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            command_name,
            *extra_args,
            "--request-json",
            "{}",
            "--idempotency-ref",
            f"idempotency-ref:{command_name}:json-failure",
            "--approval-ref",
            "approval-ref:untrusted",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    payload = json.loads(cli.stdout)
    assert payload["success"] is False
    assert payload["error"]["code"] == "GOAL_REQUEST_VALIDATION_FAILED"
    assert payload["raw_error_omitted"] is True
    assert cli.stderr == ""


def test_goal_cli_verified_completion_is_explicitly_blocked(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    request = {
        "expected_version": 2,
        "transition": "verify_completion",
        "reason_ref": "reason-ref:cli-evaluator-blocked",
        "completion_evidence": {
            "goal_ref": "goal-ref:cli-evaluator-blocked",
            "goal_version": 2,
            "run_ref": "run-ref:cli-evaluator-blocked",
            "receipt_ref": "receipt-ref:cli-evaluator-blocked",
            "proof_ref": "proof-ref:cli-evaluator-blocked",
            "criterion_proof_refs": ["proof-ref:cli-evaluator-blocked"],
            "evidence_ref": "evidence-ref:cli-evaluator-blocked",
            "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
        },
    }
    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-transition",
            "goal-ref:cli-evaluator-blocked",
            "--request-json",
            json.dumps(request),
            "--idempotency-ref",
            "idempotency-ref:cli-evaluator-blocked",
            "--approval-ref",
            "approval-ref:untrusted",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    payload = json.loads(cli.stdout)
    assert payload["error"]["code"] == ("GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE")
    assert cli.stderr == ""


@pytest.mark.parametrize(
    ("failure_mode", "expected_code"),
    [
        ("invalid-run-ref", "RUN_EVENT_INSPECTION_FAILED"),
        ("corrupt-journal", "RUN_EVENT_STORE_CORRUPT"),
    ],
)
def test_run_event_cli_inspection_failures_are_redacted(
    tmp_path: Path,
    failure_mode: str,
    expected_code: str,
) -> None:
    run_ref = "run-ref:cli-inspection:bounded"
    if failure_mode == "invalid-run-ref":
        run_ref = "abcdefgh"
    else:
        service = GoalRuntimeService.for_runtime_store(tmp_path)
        service.state_dir.mkdir(parents=True, mode=0o700)
        (service.state_dir / "run_events.jsonl").write_text(
            "{not-valid-json}\n",
            encoding="utf-8",
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
            run_ref,
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    payload = json.loads(cli.stdout)
    assert payload == {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-run-events",
        "success": False,
        "error": {
            "code": expected_code,
            "safe_summary": "Durable run events could not be read safely.",
        },
        "safe_refs_only": True,
        "raw_error_omitted": True,
        "runtime_execution_performed": False,
        "standing_authority_granted": False,
    }
    assert cli.stderr == ""
    assert "Traceback" not in cli.stdout
    assert str(tmp_path) not in cli.stdout


def test_run_event_cli_plain_inspection_failure_remains_redacted(
    tmp_path: Path,
) -> None:
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
            "abcdefgh",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert cli.returncode == 1
    assert cli.stdout == ""
    assert cli.stderr.strip() == "Durable run events could not be read safely."
    assert "Traceback" not in cli.stderr
    assert str(tmp_path) not in cli.stderr


def test_goal_cli_mutation_uses_exact_non_standing_approval(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    request_json = json.dumps(_create_payload())
    prepared = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-approval-prepare",
            "create",
            "--request-json",
            request_json,
            "--idempotency-ref",
            "idempotency-ref:cli-goal-create",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    approval_request = json.loads(prepared.stdout)["approval_request"]
    subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-approval-decide",
            approval_request["approval_request_ref"],
            "approve",
            "--reason-ref",
            "reason-ref:cli-explicit-goal-approval",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    created = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "--state-dir",
            str(tmp_path),
            "goal-create",
            "--request-json",
            request_json,
            "--idempotency-ref",
            "idempotency-ref:cli-goal-create",
            "--approval-ref",
            approval_request["approval_ref"],
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


@pytest.mark.parametrize("operation", ["create", "edit", "transition"])
def test_goal_cli_exact_retry_persists_terminal_submission_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    goal_ref = "goal-ref:cli-terminal-rejection:missing"
    idempotency_ref = f"idempotency-ref:cli-terminal-rejection:{operation}"
    if operation == "create":
        evidence_ref = (
            "evidence-ref:control-center-goal-create-submission:sha256:" + "1" * 64
        )
        payload = {**_create_payload(), "evidence_refs": [evidence_ref]}
        request = GoalCreateRequest.model_validate(payload)
        goal_binding = None
    elif operation == "edit":
        evidence_ref = (
            "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "2" * 64
        )
        payload = {
            "expected_version": 1,
            "text_redaction_posture": "operator_authored_redacted_summary_only",
            "objective": "A bounded CLI retry edit.",
            "evidence_refs": [evidence_ref],
        }
        request = GoalEditRequest.model_validate(payload)
        goal_binding = goal_ref
    else:
        evidence_ref = (
            "evidence-ref:control-center-goal-update-submission:"
            "transition:sha256:" + "3" * 64
        )
        payload = {
            "expected_version": 1,
            "transition": "pause",
            "reason_ref": "reason-ref:cli-terminal-rejection",
            "evidence_refs": [evidence_ref],
        }
        request = GoalTransitionRequest.model_validate(payload)
        goal_binding = goal_ref
    prepared = service.record_goal_mutation_submission(
        submission_ref=f"submission-ref:cli-terminal-rejection:{operation}",
        operation=operation,
        goal_ref=goal_binding,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    monkeypatch.setattr(uaa_runtime, "_goal_runtime_service", lambda _args: service)
    approval_spec = service.prepare_goal_mutation_approval(
        operation=operation,
        goal_ref=goal_binding,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    if operation == "create":
        service.decide_goal_mutation_approval(
            approval_request_ref=approval_spec.approval_request_ref,
            decision="deny",
            decision_reason_ref="reason-ref:test-terminal-cli-denial",
        )
    else:
        service.decide_goal_mutation_approval(
            approval_request_ref=approval_spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:test-terminal-cli-approval",
        )
    args = argparse.Namespace(
        request_json=json.dumps(payload),
        idempotency_ref=idempotency_ref,
        goal_ref=goal_ref,
        approval_ref=approval_spec.approval_ref,
        json=True,
    )
    handler = {
        "create": uaa_runtime._goal_create,
        "edit": uaa_runtime._goal_edit,
        "transition": uaa_runtime._goal_transition,
    }[operation]

    assert handler(args) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["success"] is False
    recovery = GoalRuntimeService(tmp_path)._submissions.recovery_read_model(  # noqa: SLF001
        GoalRuntimeService(tmp_path).goals._load_consistent_entries()  # noqa: SLF001
    )
    exact = next(
        item
        for item in recovery.records
        if item.submission_ref == prepared.submission_ref
    )
    assert exact.status == "rejected"
    assert exact.rejection_reason_ref is not None


def test_goal_cli_version_overflow_persists_request_ref_rejection_across_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = GoalRuntimeService(tmp_path)
    create_request = GoalCreateRequest.model_validate(_create_payload())
    create_idempotency_ref = "idempotency-ref:cli-version-overflow:create"
    create_approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=create_request,
        idempotency_ref=create_idempotency_ref,
    )
    goal, _approval = service.create_goal(
        create_request,
        idempotency_ref=create_idempotency_ref,
        approval_ref=create_approval_ref,
    )

    with service.goals.mutation_entries() as journal_entries:
        seed = journal_entries[0]
        expanded_entries = [seed]
        previous_entry_hash_ref = seed.entry_hash_ref
        for version in range(2, 4097):
            synthetic_request = GoalEditRequest(
                expected_version=version - 1,
                text_redaction_posture=(
                    "operator_authored_redacted_summary_only"
                ),
                objective=seed.goal.objective,
            )
            request_payload = synthetic_request.model_dump(mode="json")
            versioned_goal = seed.goal.model_copy(
                update={"version": version}
            )
            draft = seed.model_copy(
                update={
                    "entry_ref": goal_runtime_module._sha256_ref(  # noqa: SLF001
                        "goal-journal-entry-ref",
                        {
                            "goal_ref": seed.goal_ref,
                            "version": version,
                            "operation": "edit",
                        },
                    ),
                    "operation": "edit",
                    "goal_version": version,
                    "idempotency_ref": (
                        f"idempotency-ref:cli-version-overflow:seed:{version}"
                    ),
                    "request_fingerprint_ref": (
                        goal_runtime_module._sha256_ref(  # noqa: SLF001
                            "request-fingerprint-ref:goal-edit",
                            {
                                "goal_ref": seed.goal_ref,
                                "request": request_payload,
                            },
                        )
                    ),
                    "request_payload": request_payload,
                    "goal_submission_fingerprint_ref": None,
                    "transition_reason_ref": None,
                    "goal": versioned_goal,
                    "previous_entry_hash_ref": previous_entry_hash_ref,
                    "entry_hash_ref": "entry-hash-ref:pending",
                }
            )
            entry = draft.model_copy(
                update={
                    "entry_hash_ref": service.goals._entry_hash(draft)  # noqa: SLF001
                }
            )
            expanded_entries.append(entry)
            previous_entry_hash_ref = entry.entry_hash_ref
        service.goals._write_entries(expanded_entries)  # noqa: SLF001

    monkeypatch.setattr(service, "_repair_goal_read_generation", lambda: None)
    evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:"
        + "9" * 64
    )
    payload = {
        "expected_version": 4096,
        "text_redaction_posture": "operator_authored_redacted_summary_only",
        "objective": "A bounded edit that cannot exceed the version cap.",
        "evidence_refs": [evidence_ref],
    }
    request = GoalEditRequest.model_validate(payload)
    idempotency_ref = "idempotency-ref:cli-version-overflow:edit"
    submission = service.record_goal_mutation_submission(
        submission_ref="submission-ref:cli-version-overflow:edit",
        operation="edit",
        goal_ref=goal.goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    approval_ref = _approved_mutation_ref(
        service,
        operation="edit",
        goal_ref=goal.goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    monkeypatch.setattr(
        service._submissions,  # noqa: SLF001
        "terminal_commit_guard",
        lambda **_kwargs: nullcontext(),
    )
    monkeypatch.setattr(service, "reconcile_durable_events", lambda: None)
    monkeypatch.setattr(uaa_runtime, "_goal_runtime_service", lambda _args: service)
    args = argparse.Namespace(
        request_json=json.dumps(payload),
        idempotency_ref=idempotency_ref,
        goal_ref=goal.goal_ref,
        approval_ref=approval_ref,
        json=True,
    )

    assert uaa_runtime._goal_edit(args) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["error"]["code"] == "GOAL_REQUEST_REF_INVALID"

    restarted = GoalRuntimeService(tmp_path)
    monkeypatch.setattr(restarted, "_repair_goal_read_generation", lambda: None)
    monkeypatch.setattr(restarted, "reconcile_durable_events", lambda: None)
    recovery = restarted._submissions.recovery_read_model(  # noqa: SLF001
        restarted.goals._load_consistent_entries()  # noqa: SLF001
    )
    exact = next(
        record
        for record in recovery.records
        if record.submission_ref == submission.submission_ref
    )
    assert exact.status == "rejected"
    assert exact.rejection_reason_ref == (
        "reason-ref:goal-mutation-rejected:goal-request-ref-invalid"
    )
    monkeypatch.setattr(
        uaa_runtime,
        "_goal_runtime_service",
        lambda _args: restarted,
    )
    assert uaa_runtime._goal_edit(args) == 1
    retry = json.loads(capsys.readouterr().out)
    assert retry["error"]["code"] == "GOAL_SUBMISSION_PREVIOUSLY_REJECTED"
    retry_recovery = restarted._submissions.recovery_read_model(  # noqa: SLF001
        restarted.goals._load_consistent_entries()  # noqa: SLF001
    )
    assert retry_recovery == recovery


def test_plain_run_event_cli_renders_durable_goal_submission_and_event_sections(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService.for_runtime_store(tmp_path)
    create_request = GoalCreateRequest.model_validate(_create_payload())
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=create_request,
        idempotency_ref="idempotency-ref:plain-cli:create",
    )
    goal, _approval = service.create_goal(
        create_request,
        idempotency_ref="idempotency-ref:plain-cli:create",
        approval_ref=approval_ref,
    )
    evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "4" * 64
    )
    edit_request = GoalEditRequest(
        expected_version=goal.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="A pending bounded edit remains inspectable.",
        evidence_refs=[evidence_ref],
    )
    submission = service.record_goal_mutation_submission(
        submission_ref="submission-ref:plain-cli:pending-edit",
        operation="edit",
        goal_ref=goal.goal_ref,
        request=edit_request,
        idempotency_ref="idempotency-ref:plain-cli:pending-edit",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:plain-cli:visible",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="A bounded local run is visible to the operator.",
            idempotency_ref="idempotency-ref:plain-cli:event",
            authority_decision_ref="authority-decision-ref:plain-cli:event",
        ),
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
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert "Durable goals: 1" in cli.stdout
    assert goal.goal_ref in cli.stdout
    assert "Goal mutation submissions: pending=1 committed=0 rejected=0" in (cli.stdout)
    assert submission.submission_ref in cli.stdout
    assert "Durable retained events: 1" in cli.stdout
    assert "runtime-run-event-ref:" in cli.stdout
    assert "A bounded local run is visible to the operator." in cli.stdout


def test_goal_cli_uses_effective_runtime_gateway_state_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_state_dir = tmp_path / "configured-runtime"
    monkeypatch.setenv("UAA_RUNTIME_GATEWAY_STATE_DIR", str(runtime_state_dir))
    monkeypatch.delenv("UAA_GOAL_RUNTIME_STATE_DIR", raising=False)

    service = uaa_runtime._goal_runtime_service(
        argparse.Namespace(state_dir=None),
    )

    assert service.state_dir == runtime_state_dir / "goal_runtime"


@pytest.mark.parametrize("durable_truth", ["receipt", "missing", "unreadable"])
def test_command_cli_projection_failure_preserves_execution_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    durable_truth: str,
) -> None:
    class ProjectionFailingStore:
        @staticmethod
        def list_invocations() -> list[object]:
            return []

        @staticmethod
        def get_invocation_for_idempotency(_idempotency_ref: str) -> object | None:
            if durable_truth == "unreadable":
                raise OSError("raw durable ledger failure must stay redacted")
            if durable_truth == "missing":
                return None
            return SimpleNamespace(
                invocation_ref="invocation-ref:cli-projection-failure",
                receipt=SimpleNamespace(
                    receipt_ref="receipt-ref:cli-projection-failure",
                    execution_performed=True,
                    command_execution_performed=True,
                ),
            )

    class ProjectionAcceptingGoalRuntime:
        @staticmethod
        def sync_runtime_invocations(
            _records: object,
            *,
            invocation_store: object,
        ) -> None:
            del invocation_store

    class ProjectionFailingGateway:
        def __init__(self, **_kwargs: object) -> None:
            pass

        @staticmethod
        def invoke_command(
            _request: object,
            *,
            idempotency_ref: str,
        ) -> None:
            del idempotency_ref
            raise GoalRuntimeError("RUNTIME_DURABLE_EVENT_PROJECTION_FAILED")

    monkeypatch.setattr(
        uaa_runtime,
        "_runtime_store",
        lambda _args: ProjectionFailingStore(),
    )
    monkeypatch.setattr(
        uaa_runtime,
        "_goal_runtime_service",
        lambda _args: ProjectionAcceptingGoalRuntime(),
    )
    monkeypatch.setattr(uaa_runtime, "RuntimeGateway", ProjectionFailingGateway)
    args = argparse.Namespace(
        intent="git_status",
        profile="local-runtime",
        mission_ref=None,
        target_ref=[],
        summary="Inspect current repo status with redacted output.",
        timeout_seconds=5.0,
        output_byte_limit=4096,
        metadata_ref=[],
        idempotency_ref="idempotency-ref:runtime-command-cli-projection-failure",
        state_dir=str(tmp_path / "cli-state"),
        json=True,
    )

    assert uaa_runtime._command_run(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False
    assert payload["error_category"] == "RUNTIME_DURABLE_EVENT_PROJECTION_FAILED"
    assert "Traceback" not in json.dumps(payload)
    assert "raw durable ledger failure" not in json.dumps(payload)
    if durable_truth == "receipt":
        assert payload["execution_outcome"] == "durable_receipt_recovered"
        assert payload["execution_performed"] is True
        assert payload["command_execution_performed"] is True
        assert payload["invocation_ref"] == ("invocation-ref:cli-projection-failure")
        assert payload["receipt_ref"] == "receipt-ref:cli-projection-failure"
        assert payload["retry_allowed"] is False
    elif durable_truth == "missing":
        assert payload["execution_outcome"] == "not_started"
        assert payload["execution_performed"] is False
        assert payload["command_execution_performed"] is False
        assert payload["invocation_ref"] is None
        assert payload["receipt_ref"] is None
        assert payload["retry_allowed"] is True
    else:
        assert payload["execution_outcome"] == "unknown_after_projection_failure"
        assert payload["execution_performed"] is None
        assert payload["command_execution_performed"] is None
        assert payload["invocation_ref"] is None
        assert payload["receipt_ref"] is None
        assert payload["retry_allowed"] is False


def test_command_cli_projection_failure_store_unavailable_blocks_retry() -> None:
    assert uaa_runtime._command_projection_failure_truth(
        None,
        idempotency_ref="idempotency-ref:runtime-command-cli-store-unavailable",
    ) == {
        "execution_outcome": "unknown_after_projection_failure",
        "execution_performed": None,
        "command_execution_performed": None,
        "invocation_ref": None,
        "receipt_ref": None,
        "retry_allowed": False,
    }


def test_goal_event_lifecycle_e2e_reconnect_restart_and_second_run_cancel(
    goal_runtime_client: tuple[TestClient, GoalRuntimeService],
    tmp_path: Path,
) -> None:
    client, service = goal_runtime_client
    create_payload = _create_payload()
    create_idempotency_ref = "idempotency-ref:e2e-goal-create"
    create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=create_payload,
        idempotency_ref=create_idempotency_ref,
    )
    created = client.post(
        "/api/runtime/goals",
        json=create_payload,
        headers={
            "x-uaa-idempotency-key": create_idempotency_ref,
            "x-uaa-goal-approval-ref": create_approval_ref,
        },
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
                authority_decision_ref=("authority-decision-ref:e2e:accepted-local"),
            ),
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
                authority_decision_ref=("authority-decision-ref:e2e:accepted-local"),
            ),
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
        ),
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
        ),
    )

    completion_request_payload = {
        "expected_version": 1,
        "transition": "request_completion",
        "reason_ref": "reason-ref:e2e:completion-request",
    }
    completion_request_idempotency_ref = (
        "idempotency-ref:e2e:completion-request"
    )
    completion_request_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=created["goal_ref"],
        request=completion_request_payload,
        idempotency_ref=completion_request_idempotency_ref,
    )
    requested_http_response = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json=completion_request_payload,
        headers={
            "x-uaa-idempotency-key": completion_request_idempotency_ref,
            "x-uaa-goal-approval-ref": completion_request_approval_ref,
        },
    )
    assert requested_http_response.status_code == 200, requested_http_response.text
    requested_response = requested_http_response.json()
    assert requested_response["success"] is True, requested_response
    requested = requested_response["data"]["goal"]
    requested_goal = restored.goals.get(created["goal_ref"])
    criterion_bindings = _criterion_bindings(
        requested_goal,
        ["proof-ref:e2e:accepted-local"],
        evaluator_prefix="evaluator-receipt-ref:e2e",
    )
    _append_event(
        restored,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary=("The trusted evaluator bound the exact requested criterion."),
            proof_refs=[
                "proof-ref:e2e:accepted-local",
                *(binding.evaluator_receipt_ref for binding in criterion_bindings),
            ],
            receipt_refs=["receipt-ref:e2e:accepted-local"],
            criterion_verifier_bindings=criterion_bindings,
            goal_ref=created["goal_ref"],
            plan_ref="plan-ref:api-cli:one",
            idempotency_ref="idempotency-ref:e2e:event:criterion-verification",
            authority_decision_ref="authority-decision-ref:e2e:accepted-local",
        ),
    )
    completion_evidence_ref = build_goal_completion_evidence_ref(
        requested_goal,
        run_ref=run_ref,
        receipt_ref="receipt-ref:e2e:accepted-local",
        proof_ref="proof-ref:e2e:accepted-local",
        criterion_verifier_bindings=criterion_bindings,
        plan_ref="plan-ref:api-cli:one",
    )
    blocked_completion_payload = {
        "expected_version": requested["version"],
        "transition": "verify_completion",
        "reason_ref": "reason-ref:e2e:deterministic-verifier",
        "completion_evidence": {
            "goal_ref": created["goal_ref"],
            "goal_version": requested["version"],
            "run_ref": run_ref,
            "receipt_ref": "receipt-ref:e2e:accepted-local",
            "proof_ref": "proof-ref:e2e:accepted-local",
            "criterion_proof_refs": ["proof-ref:e2e:accepted-local"],
            "evidence_ref": completion_evidence_ref,
            "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
        },
    }
    blocked_completion_idempotency_ref = "idempotency-ref:e2e:verify"
    blocked_completion_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=created["goal_ref"],
        request=blocked_completion_payload,
        idempotency_ref=blocked_completion_idempotency_ref,
    )
    blocked = client.post(
        f"/api/runtime/goals/{created['goal_ref']}/transition",
        json=blocked_completion_payload,
        headers={
            "x-uaa-idempotency-key": blocked_completion_idempotency_ref,
            "x-uaa-goal-approval-ref": blocked_completion_approval_ref,
        },
    ).json()
    assert blocked["error"]["code"] == ("GOAL_COMPLETION_TRUSTED_EVALUATOR_UNAVAILABLE")
    trusted_request = GoalTransitionRequest.model_validate(
        {
            "expected_version": requested["version"],
            "transition": "verify_completion",
            "reason_ref": "reason-ref:e2e:trusted-internal-verifier",
            "completion_evidence": {
                "goal_ref": created["goal_ref"],
                "goal_version": requested["version"],
                "run_ref": run_ref,
                "receipt_ref": "receipt-ref:e2e:accepted-local",
                "proof_ref": "proof-ref:e2e:accepted-local",
                "criterion_proof_refs": ["proof-ref:e2e:accepted-local"],
                "evidence_ref": completion_evidence_ref,
                "verifier_ref": GOAL_COMPLETION_VERIFIER_REF,
            },
        }
    )
    trusted_approval_ref = _approved_mutation_ref(
        restored,
        operation="transition",
        goal_ref=created["goal_ref"],
        request=trusted_request,
        idempotency_ref="idempotency-ref:e2e:trusted-internal-verify",
    )
    verified, _approval = restored.transition_goal(
        created["goal_ref"],
        trusted_request,
        idempotency_ref="idempotency-ref:e2e:trusted-internal-verify",
        approval_ref=trusted_approval_ref,
    )
    verified = verified.model_dump(mode="json")
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
    assert [event["sequence"] for event in reconnected["events"]] == list(range(3, 12))
    assert reconnected["events"][-1]["event_kind"] == "completion_verified"

    cancelled_payload = _create_payload()
    cancelled_payload["links"] = {
        **cancelled_payload["links"],
        "run_refs": ["run-ref:e2e:cancelled"],
    }
    cancelled_create_idempotency_ref = "idempotency-ref:e2e:cancel-goal-create"
    cancelled_create_approval_ref = _api_approval_ref(
        client,
        operation="create",
        request=cancelled_payload,
        idempotency_ref=cancelled_create_idempotency_ref,
    )
    cancelled_goal = client.post(
        "/api/runtime/goals",
        json=cancelled_payload,
        headers={
            "x-uaa-idempotency-key": cancelled_create_idempotency_ref,
            "x-uaa-goal-approval-ref": cancelled_create_approval_ref,
        },
    ).json()["data"]["goal"]
    cancel_payload = {
        "expected_version": 1,
        "transition": "cancel",
        "reason_ref": "reason-ref:e2e:operator-cancel",
    }
    cancel_idempotency_ref = "idempotency-ref:e2e:goal-cancel"
    cancel_approval_ref = _api_approval_ref(
        client,
        operation="transition",
        goal_ref=cancelled_goal["goal_ref"],
        request=cancel_payload,
        idempotency_ref=cancel_idempotency_ref,
    )
    cancelled = client.post(
        f"/api/runtime/goals/{cancelled_goal['goal_ref']}/transition",
        json=cancel_payload,
        headers={
            "x-uaa-idempotency-key": cancel_idempotency_ref,
            "x-uaa-goal-approval-ref": cancel_approval_ref,
        },
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
                authority_decision_ref=("authority-decision-ref:e2e:operator-cancel"),
            ),
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
