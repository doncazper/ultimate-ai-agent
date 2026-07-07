import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF,
    RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_CLI_REF,
    RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS,
    RUNTIME_BACKGROUND_JOBS_CONTRACT_REF,
    RuntimeBackgroundJobProposalReadModel,
    RuntimeBackgroundJobsReadModel,
    build_runtime_background_jobs_read_model,
)


client = TestClient(app)


def test_background_jobs_are_durable_proposals_only() -> None:
    read_model = build_runtime_background_jobs_read_model()

    assert read_model.schema_version == "runtime_background_jobs.v1"
    assert read_model.contract_ref == RUNTIME_BACKGROUND_JOBS_CONTRACT_REF
    assert read_model.status == "durable_job_proposal_posture"
    assert read_model.route_ref == "GET /api/runtime/background-jobs"
    assert read_model.cli_ref == "uaa runtime inspect-background-jobs"
    assert (
        read_model.authority_state_route_ref
        == RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_ROUTE_REF
    )
    assert (
        read_model.authority_state_cli_ref
        == RUNTIME_BACKGROUND_JOBS_AUTHORITY_STATE_CLI_REF
    )
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_decision_ref.startswith(
        "authority-policy-decision-ref:"
    )
    assert read_model.authority_state_decision_outcome == "deny"
    assert read_model.authority_state_status == "planned_unsupported_adapter"
    assert read_model.authority_state_reason_refs == [
        "reason-ref:authority:adapter-unsupported"
    ]
    assert "adapter-ref:background-worker-runtime:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.job_count == 4
    assert read_model.proposal_count == 1
    assert read_model.paused_count == 1
    assert read_model.approval_required_count == 1
    assert read_model.execution_blocked_count == 1
    assert read_model.reviewable_job_count == 3
    assert read_model.durable_job_refs_visible is True
    assert read_model.schedule_policy_visible is True
    assert read_model.approval_scope_visible is True
    assert read_model.idempotency_visible is True
    assert read_model.safe_disable_visible is True
    assert read_model.receipt_plan_visible is True
    assert read_model.failure_handling_visible is True
    assert read_model.pause_enabled is False
    assert read_model.resume_enabled is False
    assert read_model.run_now_enabled is False
    assert read_model.scheduler_enabled is False
    assert read_model.background_worker_enabled is False
    assert read_model.autonomous_background_execution_enabled is False
    assert read_model.autonomous_retry_enabled is False
    assert read_model.external_delivery_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_job_payload_persisted is False
    assert set(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_background_job_records_show_reviewable_and_blocked_states() -> None:
    read_model = build_runtime_background_jobs_read_model()
    statuses_by_label = {job.display_label: job.status for job in read_model.jobs}

    assert statuses_by_label == {
        "Runtime doctor check": "approval_required",
        "Proof pack export": "proposal",
        "Context budget review": "paused",
        "Connector delivery follow-up": "execution_blocked",
    }
    for job in read_model.jobs:
        assert job.job_ref.startswith("background-job-ref:")
        assert job.approval_scope_ref.startswith("approval-scope-ref:background-job:")
        assert job.idempotency_ref.startswith("idempotency-ref:background-job:")
        assert job.safe_disable_ref.startswith("safe-disable-ref:background-job:")
        assert job.receipt_plan_ref.startswith("receipt-plan-ref:background-job:")
        assert job.pause_enabled is False
        assert job.resume_enabled is False
        assert job.run_now_enabled is False
        assert job.scheduler_enabled is False
        assert job.background_worker_enabled is False
        assert job.autonomous_retry_enabled is False
        assert job.external_delivery_enabled is False
        assert job.provider_call_enabled is False
        assert job.shell_execution_enabled is False
        assert job.connector_write_enabled is False
        assert job.raw_job_payload_persisted is False
        assert set(RUNTIME_BACKGROUND_JOBS_BLOCKED_AUTHORITY_REFS).issubset(
            set(job.blocked_authority_refs)
        )


@pytest.mark.parametrize(
    "field",
    [
        "pause_enabled",
        "resume_enabled",
        "run_now_enabled",
        "scheduler_enabled",
        "background_worker_enabled",
        "autonomous_background_execution_enabled",
        "autonomous_retry_enabled",
        "external_delivery_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_job_payload_persisted",
    ],
)
def test_background_jobs_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_background_jobs_read_model().model_dump(mode="json")
    payload[field] = True

    with pytest.raises(ValueError, match="RUNTIME_BACKGROUND_JOBS_AUTHORITY_DENIED"):
        RuntimeBackgroundJobsReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "pause_enabled",
        "resume_enabled",
        "run_now_enabled",
        "scheduler_enabled",
        "background_worker_enabled",
        "autonomous_retry_enabled",
        "external_delivery_enabled",
        "provider_call_enabled",
        "shell_execution_enabled",
        "connector_write_enabled",
        "raw_job_payload_persisted",
    ],
)
def test_background_job_proposal_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_background_jobs_read_model().jobs[0].model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_BACKGROUND_JOB_EXECUTION_AUTHORITY_DENIED",
    ):
        RuntimeBackgroundJobProposalReadModel(**payload)


def test_background_jobs_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/background-jobs")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_background_jobs"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/background-jobs"
    assert data["authority_state_route_ref"] == "GET /api/runtime/authority-state"
    assert (
        data["authority_state_mapping_ref"]
        == RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
    )
    assert data["authority_state_decision_outcome"] == "deny"
    assert "adapter-ref:background-worker-runtime:not-implemented" in (
        data["unsupported_adapter_refs"]
    )
    assert data["job_count"] == 4
    assert data["scheduler_enabled"] is False
    assert data["background_worker_enabled"] is False
    assert data["autonomous_background_execution_enabled"] is False
    assert data["connector_write_enabled"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "raw_prompt_value" not in serialized
    assert "provider_payload_value" not in serialized
    assert "raw_job_payload_value" not in serialized


def test_background_jobs_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-background-jobs",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_background_jobs"]
    assert payload["safe_refs_only"] is True
    assert payload["proposal_only"] is True
    assert payload["pause_performed"] is False
    assert payload["resume_performed"] is False
    assert payload["run_now_performed"] is False
    assert payload["scheduler_started"] is False
    assert payload["background_worker_started"] is False
    assert payload["autonomous_retry_performed"] is False
    assert payload["external_delivery_performed"] is False
    assert payload["provider_call_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["connector_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/background-jobs"
    assert read_model["cli_ref"] == "uaa runtime inspect-background-jobs"
    assert (
        read_model["authority_state_mapping_ref"]
        == RUNTIME_BACKGROUND_JOBS_AUTHORITY_MAPPING_REF
    )
    assert read_model["authority_state_decision_outcome"] == "deny"
    assert read_model["authority_state_reason_refs"] == [
        "reason-ref:authority:adapter-unsupported"
    ]
    assert read_model["job_count"] == 4
