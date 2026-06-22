from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.openwebui_bridge.local_test_shell import (
    DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY,
    UAA_OPENWEBUI_TEST_GATEWAY_ENV,
    UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV,
    UAA_OPENWEBUI_TEST_MODEL_ID,
)
from ultimate_ai_agent.core.local_model_management.gateway import UAA_LLAMA_CPP_GATEWAY_ENV
from ultimate_ai_agent.core.task_decomposition import CapabilityCallContext, RiskLevel, TaskNode, TaskPlan
from ultimate_ai_agent.core.task_decomposition.api_safety import (
    TASK_DECOMPOSITION_API_BEARER_ENV,
    TASK_DECOMPOSITION_API_ENV,
)
from ultimate_ai_agent.core.task_decomposition.examples import build_echo_tool_capability
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionService,
)


TASK_BEARER = "uaa-p1-011-local-placeholder"


def test_uaa_p1_011_first_product_loop_is_locally_inspectable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(UAA_LLAMA_CPP_GATEWAY_ENV, raising=False)
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_ENV, "1")
    monkeypatch.setenv(UAA_OPENWEBUI_TEST_GATEWAY_KEY_ENV, DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY)
    monkeypatch.setenv(TASK_DECOMPOSITION_API_ENV, "1")
    monkeypatch.setenv(TASK_DECOMPOSITION_API_BEARER_ENV, TASK_BEARER)

    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "task-registry.json"))
    )
    monkeypatch.setattr(api_app, "_task_decomposition_service", TaskDecompositionService(registry_store=store))
    client = TestClient(api_app.app)
    task_headers = {
        "Authorization": f"Bearer {TASK_BEARER}",
        "X-UAA-Idempotency-Key": "idempotency:operator-loop-task",
    }
    model_headers = {
        "Authorization": f"Bearer {DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY}",
        "X-UAA-Idempotency-Key": "idempotency:operator-loop-model",
    }

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    readiness = client.get("/runtime/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["success"] is True
    assert readiness.json()["data"]["production_ready"] is False

    dashboard = client.get("/control-center/dashboard")
    assert dashboard.status_code == 200
    loop_summary = dashboard.json()["data"]["operator_loop_summary"]
    assert loop_summary["milestone_ref"] == "UAA-P1-011"
    assert loop_summary["frontend_authority"] is False
    assert loop_summary["model_output_authoritative"] is False

    models = client.get("/v1/models", headers=model_headers)
    assert models.status_code == 200
    assert models.json()["data"][0]["id"] == UAA_OPENWEBUI_TEST_MODEL_ID

    chat = client.post(
        "/v1/chat/completions",
        headers=model_headers,
        json={
            "model": UAA_OPENWEBUI_TEST_MODEL_ID,
            "messages": [{"role": "user", "content": "Local readiness smoke."}],
            "stream": False,
            "max_tokens": 32,
        },
    )
    assert chat.status_code == 200
    chat_body = chat.json()
    assert chat_body["model"] == UAA_OPENWEBUI_TEST_MODEL_ID
    assert chat_body["uaa_safety"]["tool_executed"] is False
    assert chat_body["uaa_safety"]["memory_written"] is False
    assert "Local readiness smoke" not in chat_body["choices"][0]["message"]["content"]

    init_examples = client.post("/task-decomposition/examples/init", headers=task_headers)
    assert init_examples.status_code == 200
    assert init_examples.json()["success"] is True

    decompose = client.post(
        "/task-decomposition/decompose",
        headers=task_headers,
        json={
            "raw_request": "Summarize the first local operator loop.",
            "context": {"actor_id": "local_operator"},
            "idempotency_key": "uaa-p1-011-decompose",
        },
    )
    assert decompose.status_code == 200
    decompose_data = decompose.json()["data"]
    assert decompose_data["validation"]["valid"] is True
    assert decompose_data["durable_binding"]["receipt_refs"]
    assert decompose_data["durable_binding"]["rollback_refs"]

    capability_id = "capability:uaa-p1-011-safe-echo"
    base_contract = build_echo_tool_capability()
    gated_contract = base_contract.model_copy(
        update={
            "card": base_contract.card.model_copy(
                update={
                    "id": capability_id,
                    "name": "UAA P1 011 Safe Echo",
                    "requires_approval": True,
                    "risk_level": RiskLevel.low,
                }
            ),
            "required_permissions": ["compute"],
        }
    )
    register = client.post(
        "/task-decomposition/capabilities/register",
        headers=task_headers,
        json={
            "contract": gated_contract.model_dump(mode="json"),
            "handler_ref": "example.echo_summary_handler",
            "persist": False,
        },
    )
    assert register.status_code == 200
    assert register.json()["success"] is True

    run_id = "task-decomposition-run:uaa-p1-011"
    approval_request = client.post(
        "/task-decomposition/approval-requests",
        headers=task_headers,
        json={"capability_id": capability_id, "run_id": run_id, "actor_id": "local_operator"},
    )
    assert approval_request.status_code == 200
    approval_request_id = approval_request.json()["data"]["approval_request_id"]

    grant = client.post(
        "/task-decomposition/approvals/grants/capture",
        headers=task_headers,
        json={"approval_request_id": approval_request_id, "approved_by_actor_id": "local_user"},
    )
    assert grant.status_code == 200
    approval_ref = grant.json()["data"]["approval_ref"]

    plan = TaskPlan(
        plan_id=run_id,
        goal="Exercise one approved local safe capability.",
        nodes=[
            TaskNode(
                id="node:uaa-p1-011-safe-echo",
                title="Approved safe echo",
                objective="Return a local safe summary.",
                candidate_capabilities=[capability_id],
                selected_capability=capability_id,
                input_bindings={"request": "local loop"},
                success_criteria=["Safe summary returned."],
                risk_level=RiskLevel.low,
                requires_approval=True,
            )
        ],
        final_success_criteria=["Safe summary returned."],
    )
    call_context = CapabilityCallContext(
        run_id=run_id,
        actor_id="local_operator",
        approval_refs={capability_id: approval_ref},
    )
    execute = client.post(
        "/task-decomposition/plans/execute",
        headers=task_headers,
        json={
            "plan": plan.model_dump(mode="json"),
            "call_context": call_context.model_dump(mode="json"),
            "persist_reflections": True,
            "idempotency_key": "uaa-p1-011-approved-execute",
        },
    )
    assert execute.status_code == 200
    execute_data = execute.json()["data"]
    assert execute_data["status"] == "succeeded"
    assert execute_data["durable_binding"]["receipt_refs"]
    assert execute_data["durable_binding"]["audit_refs"]
    assert execute_data["durable_binding"]["replay_refs"]
    assert execute_data["durable_binding"]["rollback_refs"]
    assert execute_data["durable_binding"]["approval_refs"]

    audit = client.get("/task-decomposition/audit", headers=task_headers)
    assert audit.status_code == 200
    audit_events = audit.json()["data"]["events"]
    assert any(event["event_type"] == "approval_granted" for event in audit_events)
    assert any(event["event_type"] == "plan_executed" and event["receipt_ref"] for event in audit_events)

    metrics = client.get("/task-decomposition/metrics", headers=task_headers)
    assert metrics.status_code == 200
    capability_metrics = metrics.json()["data"]["capabilities"][capability_id]
    assert capability_metrics["succeeded"] == 1
    assert capability_metrics["average_latency_ms"] is not None
