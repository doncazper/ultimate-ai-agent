import hashlib
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.control_center.runtime_parity_loop import (
    RUNTIME_PARITY_LOOP_API_ROUTE_REF,
    RUNTIME_PARITY_LOOP_CLI_REF,
    RUNTIME_PARITY_LOOP_CONTRACT_REF,
    build_runtime_parity_loop_read_model,
)
from ultimate_ai_agent.core.decision_router import prepare_turn
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    RuntimeApprovalBindingRequest,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeInvocationStore,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


def _command_request() -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:runtime-parity-loop"],
        approval_ref=None,
        safe_summary="Run the exact focused runtime parity loop test lane.",
    )


def _approve(store: RuntimeInvocationStore, request: RuntimeCommandExecutionRequest):
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref="idempotency-ref:runtime-parity-loop-create",
    )
    exact_scope_ref = _test_hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "payload_fingerprint_ref": created.record.payload_fingerprint_ref,
            "policy_decision_ref": created.record.policy_decision.policy_decision_ref,
            "requested_authority": created.record.request.requested_authority,
        },
    )
    approval_ref = _test_hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "requested_authority": created.record.request.requested_authority,
            "requested_profile": created.record.request.requested_profile,
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": created.record.payload_fingerprint_ref,
            "policy_decision_ref": created.record.policy_decision.policy_decision_ref,
        },
    )
    action_envelope_ref = _test_hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": created.record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision="approve",
            action_envelope_ref=action_envelope_ref,
            exact_scope_ref=exact_scope_ref,
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Action Inbox approved exact runtime parity loop lane.",
        ),
        idempotency_ref="idempotency-ref:runtime-parity-loop-approve",
    )


def _execute_request(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    return RuntimeExecuteRequest(
        approval_ref=record.action_inbox_envelope.approval_ref,
        action_envelope_ref=record.action_inbox_envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        safe_summary="Execute approved runtime command through exact parity loop.",
    )


def _approved_command_request(
    request: RuntimeCommandExecutionRequest,
    record,
) -> RuntimeCommandExecutionRequest:
    assert record.action_inbox_envelope is not None
    return request.model_copy(
        update={"approval_ref": record.action_inbox_envelope.approval_ref}
    )


def _gateway_with_runner(store: RuntimeInvocationStore) -> RuntimeGateway:
    def runner(**_: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=3,
            output_bytes=b"raw runtime parity loop output must not persist",
        )

    return RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )


def test_runtime_parity_loop_read_model_is_backend_owned_and_safe_ref_only() -> None:
    read_model = build_runtime_parity_loop_read_model([])
    prepared = prepare_turn(sample_id="order-materials")
    chain = prepared.turn_run_approval_chain
    assert chain is not None

    assert read_model["contract_ref"] == RUNTIME_PARITY_LOOP_CONTRACT_REF
    assert read_model["source"] == "python_core_runtime_parity_loop_read_model"
    assert read_model["backend_owned"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["api_route_ref"] == RUNTIME_PARITY_LOOP_API_ROUTE_REF
    assert read_model["cli_ref"] == RUNTIME_PARITY_LOOP_CLI_REF
    assert read_model["runtime_invocation_count"] == 0
    assert read_model["runtime_receipt_count"] == 0
    assert read_model["runtime_signed_evidence_count"] == 0
    assert read_model["prepared_turn_ref"] == prepared.prepared_turn_ref
    assert read_model["route_decision_binding_ref"] == (
        prepared.route_decision_binding.binding_ref
    )
    assert read_model["durable_run_ref"] == chain.linkage.durable_run_ref.ref
    assert read_model["approval_ref"] == chain.linkage.approval_ref.ref
    assert read_model["implemented_stage_count"] >= 6
    assert "runtime-loop-stage-ref:signed-evidence" in read_model["stage_refs"]
    assert read_model["broad_runtime_authority_enabled"] is False
    assert read_model["provider_model_call_enabled"] is False
    assert read_model["browser_automation_enabled"] is False
    assert read_model["connector_write_enabled"] is False
    assert read_model["unrestricted_shell_enabled"] is False
    assert read_model["production_authority_enabled"] is False


def test_runtime_parity_loop_links_receipt_and_signed_evidence(tmp_path: Path) -> None:
    store = RuntimeInvocationStore(tmp_path)
    request = _command_request()
    approved = _approve(store, request)
    _gateway_with_runner(store).execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-parity-loop-execute",
    )

    read_model = build_runtime_parity_loop_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )

    assert read_model["runtime_invocation_count"] == 1
    assert read_model["runtime_receipt_count"] == 1
    assert read_model["runtime_signed_evidence_count"] == 1
    assert read_model["runtime_timeline_event_count"] > 0
    assert any(
        stage["stage_ref"] == "runtime-loop-stage-ref:exact-action-receipt"
        and stage["status"] == "implemented"
        for stage in read_model["stages"]
    )
    assert any(
        stage["stage_ref"] == "runtime-loop-stage-ref:signed-evidence"
        and stage["status"] == "implemented"
        for stage in read_model["stages"]
    )
    payload = json.dumps(read_model, sort_keys=True)
    assert "raw runtime parity loop output must not persist" not in payload
    assert str(tmp_path) not in payload


def test_runtime_parity_loop_api_and_cli_are_safe_ref_inspection() -> None:
    response = TestClient(app).get("/api/runtime/parity-loop")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_parity_loop"
    assert body["data"]["contract_ref"] == RUNTIME_PARITY_LOOP_CONTRACT_REF
    assert body["data"]["execution_performed_by_read_model"] is False
    assert body["data"]["control_center_mints_authority"] is False

    cli = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "inspect-parity-loop",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(cli.stdout)
    assert payload["command_ref"] == "repo-local-command:uaa-runtime-inspect-parity-loop"
    assert payload["execution_performed"] is False
    assert payload["runtime_parity_loop_read_model"]["contract_ref"] == (
        RUNTIME_PARITY_LOOP_CONTRACT_REF
    )


def test_runtime_action_bridge_projects_runtime_parity_loop_refs() -> None:
    bridge = build_runtime_action_inbox_bridge_read_model([])

    assert bridge["runtime_parity_loop_api_ref"] == RUNTIME_PARITY_LOOP_API_ROUTE_REF
    assert bridge["runtime_parity_loop_cli_ref"] == RUNTIME_PARITY_LOOP_CLI_REF
    assert bridge["runtime_parity_loop_status"] == (
        "backend_owned_runtime_parity_loop_available"
    )
    assert "runtime-loop-stage-ref:prepared-turn" in bridge[
        "runtime_parity_loop_stage_refs"
    ]
