from datetime import timedelta

from fastapi.testclient import TestClient

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.task_decomposition import (
    CapabilityCallContext,
    DAGExecutionStatus,
    RiskLevel,
    TaskDecompositionRunRequest,
    TaskDecompositionService,
    TaskNode,
    TaskPlan,
    build_example_registry,
)
from ultimate_ai_agent.core.task_decomposition.api_safety import (
    TASK_DECOMPOSITION_API_BEARER_ENV,
    TASK_DECOMPOSITION_API_ENV,
)
from ultimate_ai_agent.core.task_decomposition.cli import main as cli_main
from ultimate_ai_agent.core.task_decomposition.examples import build_echo_tool_capability
from ultimate_ai_agent.core.task_decomposition.kernel_adapter import TaskDecompositionKernelAdapter
from ultimate_ai_agent.core.task_decomposition.dev_api import build_task_decomposition_dev_app
from ultimate_ai_agent.core.task_decomposition.runtime import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    TaskDecompositionRegisterRequest,
    TaskCapabilityApprovalRequestPayload,
    TaskPlanExecutionRequest,
)
from ultimate_ai_agent.core.time import utc_now


DEV_API_BEARER = "test-task-decomposition-dev"
DEV_API_HEADERS = {"Authorization": f"Bearer {DEV_API_BEARER}"}


def test_json_registry_store_persists_and_reloads_example_handlers(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    registry = build_example_registry()
    store.save(registry)

    loaded = store.load()
    result = loaded.validate_call("capability:example-echo-summary", {"request": "hello"})

    assert result.valid is True
    assert loaded.get("capability:example-validation-workflow") is not None


def test_service_decompose_and_run_uses_persistent_registry(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()

    result = service.run_sync(TaskDecompositionRunRequest(raw_request="Summarize this request directly."))

    assert result.validation.valid is True
    assert result.execution is not None
    assert result.execution.status == DAGExecutionStatus.succeeded


def test_local_approval_authority_grant_authorizes_gated_capability(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    contract = build_echo_tool_capability().model_copy(
        update={
            "card": build_echo_tool_capability().card.model_copy(
                update={
                    "id": "capability:gated-summary",
                    "risk_level": RiskLevel.high,
                    "requires_approval": True,
                }
            ),
            "required_permissions": ["write:file"],
        }
    )
    service.register(
        TaskDecompositionRegisterRequest(
            contract=contract,
            handler_ref="example.echo_summary_handler",
            persist=False,
        )
    )

    plan = TaskPlan(
        plan_id="task-decomposition-plan:gated",
        goal="Run gated capability.",
        nodes=[
            TaskNode(
                id="node:gated",
                title="Gated",
                objective="Gated",
                candidate_capabilities=["capability:gated-summary"],
                selected_capability="capability:gated-summary",
                input_bindings={"request": "approved"},
                success_criteria=["Approved run succeeds."],
                risk_level=RiskLevel.high,
                requires_approval=True,
            )
        ],
        final_success_criteria=["Approved run succeeds."],
    )
    approval_request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:gated-summary",
            run_id="task-decomposition-run:approval",
            actor_id="local_actor",
        )
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local_user",
        expires_at=utc_now() + timedelta(minutes=10),
    )

    service.approval_authority.load_grant_for_validation(grant)
    service.registry.approval_authority = service.approval_authority
    result = service.execute_plan_sync(
        TaskPlanExecutionRequest(
            plan=plan,
            call_context=CapabilityCallContext(
                run_id="task-decomposition-run:approval",
                actor_id="local_actor",
                approval_refs={"capability:gated-summary": grant.approval_ref},
            ),
        )
    )

    assert result.status == DAGExecutionStatus.succeeded


def test_kernel_adapter_previews_local_decomposition(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()
    adapter = TaskDecompositionKernelAdapter(service)

    preview = adapter.preview("Summarize this request directly.")

    assert preview.validation.valid is True
    assert preview.plan.nodes[0].selected_capability == "capability:example-echo-summary"


def test_cli_init_catalog_decompose_and_run(tmp_path, capsys) -> None:
    registry_path = str(tmp_path / "registry.json")

    assert cli_main(["--registry", registry_path, "init-examples"]) == 0
    assert cli_main(["--registry", registry_path, "catalog"]) == 0
    assert cli_main(["--registry", registry_path, "decompose", "Summarize this request."]) == 0
    assert cli_main(["--registry", registry_path, "run", "Summarize this request."]) == 0

    output = capsys.readouterr().out
    assert "capability:example-echo-summary" in output


def test_api_routes_initialize_decompose_and_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(TASK_DECOMPOSITION_API_ENV, "1")
    monkeypatch.setenv(TASK_DECOMPOSITION_API_BEARER_ENV, DEV_API_BEARER)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    client = TestClient(build_task_decomposition_dev_app(service))

    init_response = client.post("/task-decomposition/examples/init", headers=DEV_API_HEADERS)
    assert init_response.status_code == 200
    assert init_response.json()["success"] is True

    catalog_response = client.get("/task-decomposition/catalog", headers=DEV_API_HEADERS)
    assert catalog_response.status_code == 200
    assert catalog_response.json()["success"] is True

    decompose_response = client.post(
        "/task-decomposition/decompose",
        headers=DEV_API_HEADERS,
        json={"raw_request": "Summarize this request directly.", "context": {}},
    )
    assert decompose_response.status_code == 200
    assert decompose_response.json()["data"]["validation"]["valid"] is True
    assert "Summarize this request directly" not in decompose_response.text

    run_response = client.post(
        "/task-decomposition/run",
        headers=DEV_API_HEADERS,
        json={"raw_request": "Summarize this request directly."},
    )
    assert run_response.status_code == 200
    assert run_response.json()["success"] is True


def test_dev_api_is_disabled_without_local_authority(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(TASK_DECOMPOSITION_API_ENV, raising=False)
    monkeypatch.delenv(TASK_DECOMPOSITION_API_BEARER_ENV, raising=False)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    client = TestClient(build_task_decomposition_dev_app(service))

    response = client.get("/task-decomposition/catalog")

    assert response.status_code == 403
    assert "disabled by default" in response.json()["detail"]
