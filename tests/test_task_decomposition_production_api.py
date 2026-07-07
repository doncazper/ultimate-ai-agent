from typing import Any
from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.authority import (
    AUTHORITY_LEASE_KILL_SWITCH_ENV,
    AUTHORITY_STATE_DIR_ENV,
)
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
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionApprovalGrantRequest,
    TaskDecompositionRegisterRequest,
    TaskDecompositionRateLimiter,
    TaskDecompositionService,
    TaskPlanExecutionRequest,
)
from tests.authority_helpers import (
    issue_workspace_execute_authority_lease,
    workspace_execute_ask_authority_lease,
    workspace_execute_authority_lease,
)


TASK_API_BEARER = "test-task-decomposition-local"
TASK_API_HEADERS = {
    "Authorization": f"Bearer {TASK_API_BEARER}",
    "X-UAA-Idempotency-Key": "idempotency:task-decomposition-api",
}
TASK_API_IDEMPOTENCY_ONLY_HEADERS = {
    "X-UAA-Idempotency-Key": "idempotency:task-decomposition-disabled",
}


def _client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    grant_workspace_execute: bool = True,
) -> tuple[Any, ...]:
    monkeypatch.setenv(api_app.TASK_DECOMPOSITION_API_ENV, "1")
    monkeypatch.setenv(api_app.TASK_DECOMPOSITION_API_BEARER_ENV, TASK_API_BEARER)
    authority_state_dir = tmp_path / "authority"
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
    if grant_workspace_execute:
        issue_workspace_execute_authority_lease(authority_state_dir)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    monkeypatch.setattr(api_app, "_task_decomposition_service", service)
    return TestClient(api_app.app), service


def test_task_decomposition_post_routes_are_disabled_without_local_authority(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(api_app.TASK_DECOMPOSITION_API_ENV, raising=False)
    monkeypatch.delenv(api_app.TASK_DECOMPOSITION_API_BEARER_ENV, raising=False)
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    monkeypatch.setattr(api_app, "_task_decomposition_service", TaskDecompositionService(registry_store=store))
    client = TestClient(api_app.app)

    response = client.post(
        "/task-decomposition/run",
        headers=TASK_API_IDEMPOTENCY_ONLY_HEADERS,
        json={"raw_request": "Summarize this request directly."},
    )

    assert response.status_code == 403
    assert "disabled by default" in response.json()["detail"]

    read_response = client.get("/task-decomposition/status")

    assert read_response.status_code == 403
    assert "disabled by default" in read_response.json()["detail"]


def test_canonical_api_exposes_task_decomposition_surface(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


def test_task_decomposition_api_redacts_secret_like_raw_requests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, _service = _client(monkeypatch, tmp_path)
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)
    raw_request = "Summarize api_key='abcdefghijklmnop' without echoing it."

    for route in ("/task-decomposition/classify", "/task-decomposition/decompose", "/task-decomposition/run"):
        response = client.post(route, headers=TASK_API_HEADERS, json={"raw_request": raw_request, "context": {}})

        assert response.status_code == 200
        assert "abcdefghijklmnop" not in response.text
        assert "Summarize api_key" not in response.text
        assert "raw_request_omitted" in response.text


def test_task_decomposition_api_returns_safe_durable_binding(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, _service = _client(monkeypatch, tmp_path)
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)

    response = client.post(
        "/task-decomposition/run",
        headers=TASK_API_HEADERS,
        json={
            "raw_request": "Summarize this request directly.",
            "context": {},
            "idempotency_key": "p1-027-safe-run",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    binding = data["durable_binding"]
    assert binding["run_id"].startswith("task-decomposition-plan:")
    assert binding["state"] == "succeeded"
    assert binding["receipt_refs"]
    assert binding["replay_refs"]
    assert binding["rollback_refs"]
    assert binding["evidence_refs"]
    assert binding["no_runtime_authority"] is True
    assert all(":" in ref for ref in binding["receipt_refs"])
    assert "Summarize this request directly" not in response.text

    lifecycle_response = client.get(
        f"/task-decomposition/runs/{binding['run_id']}/lifecycle",
        headers=TASK_API_HEADERS,
    )
    assert lifecycle_response.status_code == 200
    lifecycle = lifecycle_response.json()["data"]
    assert lifecycle["run_id"] == binding["run_id"]
    assert lifecycle["status"] == "succeeded"
    assert lifecycle["events"]
    assert lifecycle["receipt_hash_refs"]
    assert lifecycle["safe_refs_only"] is True
    assert lifecycle["raw_payloads_persisted"] is False
    assert lifecycle["approval_refs_are_identifiers_only"] is True
    assert lifecycle["execution_authority_enabled"] is False
    assert lifecycle["execution_performed"] is False
    assert lifecycle["scheduler_enabled"] is False
    assert lifecycle["background_worker_enabled"] is False
    assert lifecycle["provider_model_calls_enabled"] is False
    assert lifecycle["tool_execution_expansion_enabled"] is False
    assert lifecycle["connector_writes_enabled"] is False
    assert lifecycle["streaming_runtime_enabled"] is False
    assert lifecycle["api_mutation_routes_added"] is False
    assert "Summarize this request directly" not in lifecycle_response.text

    approvals_response = client.get(
        f"/task-decomposition/runs/{binding['run_id']}/approvals",
        headers=TASK_API_HEADERS,
    )
    assert approvals_response.status_code == 200
    approvals = approvals_response.json()["data"]
    assert approvals["schema_version"] == "run_attached_approval_queue.v1"
    assert approvals["safe_refs_only"] is True
    assert approvals["raw_payloads_persisted"] is False
    assert approvals["approval_refs_are_identifiers_only"] is True
    assert approvals["approval_authority_enabled"] is False
    assert approvals["execution_authority_enabled"] is False
    assert approvals["ui_mutation_controls_enabled"] is False
    assert "Summarize this request directly" not in approvals_response.text


def test_task_decomposition_run_requires_workspace_execute_authority_lease(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _service = _client(monkeypatch, tmp_path, grant_workspace_execute=False)
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)

    response = client.post(
        "/task-decomposition/run",
        headers=TASK_API_HEADERS,
        json={
            "raw_request": "Summarize this request directly.",
            "context": {},
            "idempotency_key": "p1-027-authority-lease-required",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    execution = body["data"]["execution"]
    assert execution["status"] == "awaiting_approval"
    assert execution["authority_decision_outcome"] == "degrade_to_draft"
    assert execution["authority_lease_ref"] is None
    assert execution["authority_audit_record_ref"].startswith("audit-ref:authority-policy:")
    assert execution["authority_required_domain_refs"] == ["authority-domain-ref:workspace"]
    assert execution["authority_required_capability_refs"] == [
        "authority-capability-ref:execute"
    ]
    assert "TASK_DECOMPOSITION_WORKSPACE_EXECUTE_AUTHORITY_REQUIRED" in execution["reason_codes"]
    assert "Summarize this request directly" not in response.text


def test_task_decomposition_run_rechecks_authority_kill_switch_before_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client, _service = _client(monkeypatch, tmp_path)
    monkeypatch.setenv(AUTHORITY_LEASE_KILL_SWITCH_ENV, "1")
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)

    response = client.post(
        "/task-decomposition/run",
        headers=TASK_API_HEADERS,
        json={
            "raw_request": "Summarize this request directly.",
            "context": {},
            "idempotency_key": "p1-027-authority-kill-switch",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    execution = body["data"]["execution"]
    assert execution["status"] == "awaiting_approval"
    assert execution["authority_decision_outcome"] == "deny"
    assert execution["authority_lease_ref"] is None
    assert "reason-ref:authority:kill-switch-engaged" in execution["reason_codes"]
    assert "TASK_DECOMPOSITION_WORKSPACE_EXECUTE_AUTHORITY_REQUIRED" in execution["reason_codes"]
    assert "Summarize this request directly" not in response.text


def test_task_decomposition_ask_authority_does_not_execute_plan(
    tmp_path: Path,
) -> None:
    store = CapabilityRegistryStore(
        CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json"))
    )
    service = TaskDecompositionService(
        registry_store=store,
        active_authority_leases=[workspace_execute_ask_authority_lease()],
    )
    service.ensure_examples()
    plan = TaskPlan(
        plan_id="task-decomposition-run:ask-authority-no-execute",
        goal="Run ask-mode task plan.",
        nodes=[
            TaskNode(
                id="node:ask-authority",
                title="Ask authority node",
                objective="This node must not execute under ask authority alone.",
                candidate_capabilities=["capability:example-echo-summary"],
                selected_capability="capability:example-echo-summary",
                input_bindings={"request": "ask authority should not execute"},
                success_criteria=["Handler would return a summary."],
            )
        ],
        final_success_criteria=["Ask authority should not execute handler."],
    )

    result = service.execute_plan_sync(
        TaskPlanExecutionRequest(
            plan=plan,
            idempotency_key="p1-027-ask-authority-no-execute",
        )
    )

    assert result.status == "awaiting_approval"
    assert result.node_records == []
    assert result.outputs == {}
    assert result.authority_decision_outcome == "ask"
    assert result.authority_lease_ref == "authority-lease-ref:test-workspace-execute-ask"
    assert "reason-ref:authority:ask-before-changes-mode" in result.reason_codes
    assert "TASK_DECOMPOSITION_WORKSPACE_EXECUTE_AUTHORITY_REQUIRED" in result.reason_codes


def test_task_decomposition_explicit_idempotency_key_denies_duplicate_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, _service = _client(monkeypatch, tmp_path)
    client.post("/task-decomposition/examples/init", headers=TASK_API_HEADERS)
    payload = {
        "raw_request": "Summarize this request directly.",
        "context": {},
        "idempotency_key": "p1-027-duplicate-run",
    }

    first = client.post("/task-decomposition/run", headers=TASK_API_HEADERS, json=payload)
    second = client.post("/task-decomposition/run", headers=TASK_API_HEADERS, json=payload)

    assert first.status_code == 200
    assert first.json()["success"] is True
    assert second.status_code == 200
    assert second.json()["success"] is False
    assert second.json()["error"]["code"] == "TASK_DECOMPOSITION_IDEMPOTENCY_REPLAY_DENIED"


def test_task_decomposition_durable_run_binds_approval_receipt_replay_and_restart(tmp_path: Path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(
        registry_store=store,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    base = build_echo_tool_capability()
    gated = base.model_copy(
        update={
            "card": base.card.model_copy(
                update={
                    "id": "capability:p1-027-gated-summary",
                    "risk_level": RiskLevel.high,
                    "requires_approval": True,
                }
            ),
            "required_permissions": ["write:file"],
        }
    )
    service.register(
        TaskDecompositionRegisterRequest(
            contract=gated,
            handler_ref="example.echo_summary_handler",
        )
    )
    run_id = "task-decomposition-run:p1-027-binding"
    plan = TaskPlan(
        plan_id=run_id,
        goal="Run gated summary capability.",
        nodes=[
            TaskNode(
                id="node:gated-p1-027",
                title="Gated summary",
                objective="Run approved summary.",
                candidate_capabilities=["capability:p1-027-gated-summary"],
                selected_capability="capability:p1-027-gated-summary",
                input_bindings={"request": "approved summary"},
                success_criteria=["Approved summary succeeds."],
                risk_level=RiskLevel.high,
                requires_approval=True,
            )
        ],
        final_success_criteria=["Approved summary succeeds."],
    )

    blocked = service.execute_plan_sync(
        TaskPlanExecutionRequest(
            plan=plan,
            call_context=CapabilityCallContext(run_id=run_id, actor_id="local_actor"),
            idempotency_key="p1-027-blocked-execute",
        )
    )
    assert blocked.status == "awaiting_approval"
    assert blocked.durable_binding is not None
    assert blocked.durable_binding.state == "blocked"
    assert blocked.durable_binding.receipt_refs

    approval_request = service.build_approval_request(
        TaskCapabilityApprovalRequestPayload(
            capability_id="capability:p1-027-gated-summary",
            run_id=run_id,
            actor_id="local_actor",
        )
    )
    grant = service.grant_approval(
        TaskDecompositionApprovalGrantRequest(
            approval_request_id=approval_request.approval_request_id,
            approved_by_actor_id="local_user",
        )
    )
    approved = service.execute_plan_sync(
        TaskPlanExecutionRequest(
            plan=plan,
            call_context=CapabilityCallContext(
                run_id=run_id,
                actor_id="local_actor",
                approval_refs={"capability:p1-027-gated-summary": grant.approval_ref},
            ),
            idempotency_key="p1-027-approved-execute",
        )
    )

    assert approved.status == "succeeded"
    assert approved.durable_binding is not None
    assert approved.durable_binding.state == "succeeded"
    assert approved.durable_binding.approval_refs
    assert approved.durable_binding.handler_refs
    audit_events = service.audit_events()
    plan_audit = [event for event in audit_events if event["event_type"] == "plan_executed"][-1]
    assert plan_audit["durable_run_ref"]
    assert plan_audit["receipt_ref"]

    replay_binding = service.validate_replay(run_id)
    assert replay_binding.replay_validation_ref is not None
    assert replay_binding.replay_validation_ref in replay_binding.replay_refs

    restart_binding = service.record_restart_visibility(run_id, restart_ref="restart:p1-027")
    assert "restart:p1-027" in restart_binding.restart_refs

    reloaded = TaskDecompositionService(
        registry_store=store,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    reloaded_binding = reloaded.durable_binding(run_id)
    assert reloaded_binding is not None
    assert reloaded_binding.state == "succeeded"
    assert reloaded_binding.receipt_refs


def test_canonical_api_captures_revokes_and_enforces_capability_approval(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


def test_registry_store_uses_versioned_tamper_evident_documents(tmp_path: Path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    store.ensure_example_registry()

    document = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
    assert document["schema_version"] == REGISTRY_SCHEMA_VERSION
    assert document["capabilities"][0]["signature"]["digest"]

    document["capabilities"][0]["contract"]["card"]["summary"] = "tampered summary"
    (tmp_path / "registry.json").write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="SIGNATURE_MISMATCH"):
        store.load()


def test_top_level_handler_ref_persists_in_registered_contract(tmp_path: Path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(
        registry_store=store,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
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

    reloaded = TaskDecompositionService(
        registry_store=store,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
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


def test_register_rejects_conflicting_top_level_and_contract_handler_refs(tmp_path: Path) -> None:
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


def test_service_rejects_unallowlisted_handler_refs(tmp_path: Path) -> None:
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    contract = build_echo_tool_capability().model_copy(update={"handler_ref": "unreviewed.dynamic_import"})

    with pytest.raises(ValueError, match="HANDLER_REF_NOT_ALLOWLISTED"):
        service.register(TaskDecompositionRegisterRequest(contract=contract, persist=False))
