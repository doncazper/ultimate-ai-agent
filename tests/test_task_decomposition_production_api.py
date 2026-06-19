import json

import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.task_decomposition import (
    CapabilityCallContext,
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
    RiskLevel,
    TaskNode,
    TaskPlan,
)
from ultimate_ai_agent.core.task_decomposition.examples import build_echo_tool_capability
from ultimate_ai_agent.core.task_decomposition.runtime import (
    REGISTRY_SCHEMA_VERSION,
    TaskDecompositionRegisterRequest,
    TaskDecompositionRateLimiter,
    TaskDecompositionService,
    TaskPlanExecutionRequest,
)


TASK_API_BEARER = "test-task-decomposition-local"
TASK_API_HEADERS = {"Authorization": f"Bearer {TASK_API_BEARER}"}


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv(api_app.TASK_DECOMPOSITION_API_ENV, "1")
    monkeypatch.setenv(api_app.TASK_DECOMPOSITION_API_BEARER_ENV, TASK_API_BEARER)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    monkeypatch.setattr(api_app, "_task_decomposition_service", service)
    return TestClient(api_app.app), service


def test_task_decomposition_post_routes_are_disabled_without_local_authority(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv(api_app.TASK_DECOMPOSITION_API_ENV, raising=False)
    monkeypatch.delenv(api_app.TASK_DECOMPOSITION_API_BEARER_ENV, raising=False)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    monkeypatch.setattr(api_app, "_task_decomposition_service", TaskDecompositionService(registry_store=store))
    client = TestClient(api_app.app)

    response = client.post("/task-decomposition/run", json={"raw_request": "Summarize this request directly."})

    assert response.status_code == 403
    assert "disabled by default" in response.json()["detail"]

    read_response = client.get("/task-decomposition/status")

    assert read_response.status_code == 403
    assert "disabled by default" in read_response.json()["detail"]


def test_canonical_api_exposes_task_decomposition_surface(monkeypatch, tmp_path) -> None:
    client, _service = _client(monkeypatch, tmp_path)

    init_response = client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)
    assert init_response.status_code == 200
    assert init_response.json()["success"] is True

    status_response = client.get("/task-decomposition/status", headers=TASK_API_HEADERS)
    assert status_response.status_code == 200
    status = status_response.json()["data"]
    assert status["status"] == "ready"
    assert status["production_authority"] is False
    assert status["unrestricted_external_execution"] is False
    assert "registry_path" not in status
    assert status["registry_path_omitted"] is True

    catalog_response = client.get("/task-decomposition/catalog", headers=TASK_API_HEADERS)
    assert catalog_response.status_code == 200
    assert catalog_response.json()["data"]["capabilities"]

    export_response = client.get("/task-decomposition/registry/export", headers=TASK_API_HEADERS)
    assert export_response.status_code == 200
    assert export_response.json()["data"]["schema_version"] == REGISTRY_SCHEMA_VERSION

    decompose_response = client.post(
        "/task-decomposition/decompose",
        headers=TASK_API_HEADERS,
        json={"raw_request": "Summarize this request directly.", "context": {}},
    )
    assert decompose_response.status_code == 200
    assert decompose_response.json()["data"]["validation"]["valid"] is True
    assert "Summarize this request directly" not in decompose_response.text
    assert decompose_response.json()["data"]["intent"]["raw_request_omitted"] is True

    run_response = client.post(
        "/task-decomposition/run",
        headers=TASK_API_HEADERS,
        json={"raw_request": "Summarize this request directly."},
    )
    assert run_response.status_code == 200
    assert run_response.json()["success"] is True
    assert "Summarize this request directly" not in run_response.text

    manifest = client.get("/api/manifest").json()
    route = next(item for item in manifest["routes"] if item["path"] == "/task-decomposition/run")
    assert route["side_effect_class"] == "local_dev_workspace_only"
    assert "task_decomposition_canonical_local_runtime" in manifest["capabilities_declared"]

    audit = client.get("/task-decomposition/audit", headers=TASK_API_HEADERS).json()
    assert audit["success"] is True
    assert audit["data"]["events"]

    metrics = client.get("/task-decomposition/metrics", headers=TASK_API_HEADERS).json()
    assert metrics["success"] is True
    assert "capabilities" in metrics["data"]


def test_task_decomposition_api_redacts_secret_like_raw_requests(monkeypatch, tmp_path) -> None:
    client, _service = _client(monkeypatch, tmp_path)
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)
    raw_request = "Summarize api_key='abcdefghijklmnop' without echoing it."

    for route in ("/task-decomposition/classify", "/task-decomposition/decompose", "/task-decomposition/run"):
        response = client.post(route, headers=TASK_API_HEADERS, json={"raw_request": raw_request, "context": {}})

        assert response.status_code == 200
        assert "abcdefghijklmnop" not in response.text
        assert "Summarize api_key" not in response.text
        assert "raw_request_omitted" in response.text


def test_canonical_api_captures_revokes_and_enforces_capability_approval(monkeypatch, tmp_path) -> None:
    client, service = _client(monkeypatch, tmp_path)
    base = build_echo_tool_capability()
    gated = base.model_copy(
        update={
            "card": base.card.model_copy(
                update={
                    "id": "capability:gated-summary-api",
                    "risk_level": RiskLevel.high,
                    "requires_approval": True,
                }
            ),
            "required_permissions": ["write:file"],
        }
    )
    register_response = client.post(
        "/task-decomposition/capabilities/register",
        headers=TASK_API_HEADERS,
        json={
            "contract": gated.model_dump(mode="json"),
            "handler_ref": "example.echo_summary_handler",
            "persist": True,
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    run_id = "task-decomposition-run:api-approval"
    plan = TaskPlan(
        plan_id=run_id,
        goal="Run gated summary capability.",
        nodes=[
            TaskNode(
                id="node:gated",
                title="Gated summary",
                objective="Run approved summary.",
                candidate_capabilities=["capability:gated-summary-api"],
                selected_capability="capability:gated-summary-api",
                input_bindings={"request": "approved summary"},
                success_criteria=["Approved summary succeeds."],
                risk_level=RiskLevel.high,
                requires_approval=True,
            )
        ],
        final_success_criteria=["Approved summary succeeds."],
    )

    blocked = client.post(
        "/task-decomposition/plans/execute",
        headers=TASK_API_HEADERS,
        json={"plan": plan.model_dump(mode="json")},
    )
    assert blocked.status_code == 200
    assert blocked.json()["data"]["status"] == "awaiting_approval"

    approval_request = client.post(
        "/task-decomposition/approval-requests",
        headers=TASK_API_HEADERS,
        json={
            "capability_id": "capability:gated-summary-api",
            "run_id": run_id,
            "actor_id": "local_actor",
        },
    ).json()["data"]
    grant_response = client.post(
        "/task-decomposition/approvals/grants/capture",
        headers=TASK_API_HEADERS,
        json={
            "approval_request_id": approval_request["approval_request_id"],
            "approved_by_actor_id": "local_user",
        },
    )
    assert grant_response.status_code == 200
    grant = grant_response.json()["data"]

    inline_grant_bypass = client.post(
        "/task-decomposition/plans/execute",
        headers=TASK_API_HEADERS,
        json={
            "plan": plan.model_dump(mode="json"),
            "approval_grants": [grant],
        },
    )
    assert inline_grant_bypass.status_code == 200
    assert inline_grant_bypass.json()["success"] is False
    assert inline_grant_bypass.json()["error"]["code"] == "TASK_DECOMPOSITION_INLINE_APPROVAL_GRANTS_DENIED"

    approval_shortcut_bypass = client.post(
        "/task-decomposition/plans/execute",
        headers=TASK_API_HEADERS,
        json={
            "plan": plan.model_dump(mode="json"),
            "call_context": CapabilityCallContext(
                run_id=run_id,
                actor_id="local_actor",
                approved_capability_ids=["capability:gated-summary-api"],
            ).model_dump(mode="json"),
        },
    )
    assert approval_shortcut_bypass.status_code == 200
    assert approval_shortcut_bypass.json()["data"]["status"] == "awaiting_approval"

    approved = client.post(
        "/task-decomposition/plans/execute",
        headers=TASK_API_HEADERS,
        json={
            "plan": plan.model_dump(mode="json"),
            "call_context": CapabilityCallContext(
                run_id=run_id,
                actor_id="local_actor",
                approval_refs={"capability:gated-summary-api": grant["approval_ref"]},
            ).model_dump(mode="json"),
        },
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "succeeded"

    revoked = client.post(
        "/task-decomposition/approvals/revoke",
        headers=TASK_API_HEADERS,
        json={"approval_ref": grant["approval_ref"], "reason": "local test revocation"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["success"] is True

    denied_after_revoke = service.execute_plan_sync(
        api_app.TaskPlanExecutionRequest(
            plan=plan,
            call_context=CapabilityCallContext(
                run_id=run_id,
                actor_id="local_actor",
                approval_refs={"capability:gated-summary-api": grant["approval_ref"]},
            ),
        )
    )
    assert denied_after_revoke.status == "awaiting_approval"


def test_registry_store_uses_versioned_tamper_evident_documents(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    store.ensure_example_registry()

    document = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert document["schema_version"] == REGISTRY_SCHEMA_VERSION
    assert document["capabilities"][0]["signature"]["digest"]

    document["capabilities"][0]["contract"]["card"]["summary"] = "tampered summary"
    (tmp_path / "registry.json").write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="SIGNATURE_MISMATCH"):
        store.load()


def test_top_level_handler_ref_persists_in_registered_contract(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    base = build_echo_tool_capability()
    contract = base.model_copy(
        update={
            "card": base.card.model_copy(update={"id": "capability:durable-handler-ref"}),
            "handler_ref": None,
        }
    )

    registered = service.register(
        TaskDecompositionRegisterRequest(
            contract=contract,
            handler_ref="example.echo_summary_handler",
        )
    )

    assert registered.handler_ref == "example.echo_summary_handler"

    reloaded = TaskDecompositionService(registry_store=store)
    plan = TaskPlan(
        plan_id="task-decomposition-run:durable-handler-ref",
        goal="Run reloaded handler.",
        nodes=[
            TaskNode(
                id="node:durable",
                title="Durable handler",
                objective="Run a persisted handler ref after reload.",
                candidate_capabilities=["capability:durable-handler-ref"],
                selected_capability="capability:durable-handler-ref",
                input_bindings={"request": "durable handler test"},
                success_criteria=["Durable handler succeeds."],
            )
        ],
        final_success_criteria=["Durable handler succeeds."],
    )

    result = reloaded.execute_plan_sync(TaskPlanExecutionRequest(plan=plan))

    assert result.status == "succeeded"


def test_register_rejects_conflicting_top_level_and_contract_handler_refs(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    contract = build_echo_tool_capability()

    with pytest.raises(ValueError, match="HANDLER_REF_MISMATCH"):
        service.register(
            TaskDecompositionRegisterRequest(
                contract=contract,
                handler_ref="example.validation_workflow_handler",
                persist=False,
            )
        )


def test_task_decomposition_rate_limiter_blocks_repeated_actor_events() -> None:
    limiter = TaskDecompositionRateLimiter(max_events=1, window_s=60)

    limiter.check("actor:local")

    with pytest.raises(ValueError, match="RATE_LIMIT"):
        limiter.check("actor:local")


def test_service_rejects_unallowlisted_handler_refs(tmp_path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    contract = build_echo_tool_capability().model_copy(update={"handler_ref": "unreviewed.dynamic_import"})

    with pytest.raises(ValueError, match="HANDLER_REF_NOT_ALLOWLISTED"):
        service.register(TaskDecompositionRegisterRequest(contract=contract, persist=False))
