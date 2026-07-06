from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.core.runtime_gateway.command as command_module
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS,
    RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CONTRACT_REF,
    RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE,
    GovernedCommandRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeHardlineCommandBlocklistReadModel,
    RuntimeHardlineCommandClassification,
    RuntimeInvocationStore,
    build_runtime_hardline_command_blocklist_read_model,
    classify_hardline_command_argv,
    hardline_block_reason_for_argv,
    runtime_command_invocation_request,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeApprovalBindingRequest,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_hardline_command_blocklist_is_read_only_posture() -> None:
    read_model = build_runtime_hardline_command_blocklist_read_model()

    assert read_model.schema_version == "runtime_hardline_command_blocklist.v1"
    assert read_model.contract_ref == RUNTIME_HARDLINE_COMMAND_BLOCKLIST_CONTRACT_REF
    assert read_model.status == "read_only_hardline_command_blocklist_floor"
    assert read_model.route_ref == "GET /api/runtime/hardline-command-blocklist"
    assert read_model.cli_ref == "uaa runtime inspect-hardline-command-blocklist"
    assert read_model.non_overridable_floor is True
    assert read_model.override_bypass_permitted is False
    assert read_model.command_execution_performed is False
    assert read_model.raw_command_text_persisted is False
    assert read_model.raw_command_output_persisted is False
    assert read_model.classification_count == len(read_model.classifications)
    assert read_model.denied_classification_count >= 10
    assert read_model.allowed_classification_count == 3
    assert set(RUNTIME_HARDLINE_COMMAND_BLOCKLIST_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


@pytest.mark.parametrize(
    ("argv", "category"),
    [
        (("git", "status", "&&", "shape-ref"), "shell_metachar"),
        (("bash", "-c", "shape-ref"), "shell_interpreter"),
        (("python", "-c", "shape-ref"), "inline_code"),
        (("rm", "-rf", "shape-ref"), "destructive_filesystem"),
        (("dd", "if=shape-ref", "of=shape-ref"), "disk_writer"),
        (("curl", "https://example.invalid"), "network_transfer"),
        (("ssh", "host-ref:example"), "remote_access"),
        (("sudo", "shape-ref"), "privilege_escalation"),
        (("git", "push"), "git_mutation"),
        (("python", "-m", "pip", "install"), "package_install"),
        (("kubectl", "apply"), "production_orchestration"),
        (("playwright", "test"), "browser_automation"),
    ],
)
def test_hardline_classifier_denies_catastrophic_command_shapes(
    argv: tuple[str, ...],
    category: str,
) -> None:
    classification = classify_hardline_command_argv(argv)

    assert classification.denied is True
    assert classification.status == "hardline_denied"
    assert classification.denial_category == category
    assert classification.non_overridable is True
    assert classification.override_bypass_permitted is False
    assert classification.raw_command_text_persisted is False
    assert classification.raw_command_output_persisted is False
    assert classification.command_execution_performed is False
    assert hardline_block_reason_for_argv(argv) == (
        f"{RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE}:{category}"
    )


@pytest.mark.parametrize(
    "argv",
    [
        (
            "git",
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "status",
            "--short",
            "--branch",
            "--no-renames",
            "--untracked-files=no",
        ),
        ("python", "-m", "pytest", "tests/test_governed_runtime_contracts.py", "-q"),
        ("make", "frontend-check"),
        ("make", "doctor"),
    ],
)
def test_hardline_classifier_allows_current_exact_command_shapes(
    argv: tuple[str, ...],
) -> None:
    classification = classify_hardline_command_argv(argv)

    assert classification.denied is False
    assert classification.status == "allowed_shape"
    assert classification.denial_category == "allowed"
    assert hardline_block_reason_for_argv(argv) is None


@pytest.mark.parametrize(
    "field",
    [
        "non_overridable_floor",
        "override_bypass_permitted",
        "command_execution_performed",
        "raw_command_text_persisted",
        "raw_command_output_persisted",
    ],
)
def test_hardline_read_model_denies_weakened_floor_or_execution(field: str) -> None:
    payload = build_runtime_hardline_command_blocklist_read_model().model_dump(
        mode="json"
    )
    payload[field] = False if field == "non_overridable_floor" else True

    with pytest.raises(ValueError):
        RuntimeHardlineCommandBlocklistReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "non_overridable",
        "override_bypass_permitted",
        "raw_command_text_persisted",
        "raw_command_output_persisted",
        "command_execution_performed",
    ],
)
def test_hardline_classification_denies_weakened_flags(field: str) -> None:
    payload = classify_hardline_command_argv(("rm", "-rf", "shape-ref")).model_dump(
        mode="json"
    )
    payload[field] = False if field == "non_overridable" else True

    with pytest.raises(ValueError):
        RuntimeHardlineCommandClassification(**payload)


def test_runtime_gateway_hardline_floor_blocks_before_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"should-not-run",
        )

    monkeypatch.setattr(
        command_module,
        "_argv_for_entry",
        lambda *_args, **_kwargs: ("rm", "-rf", "shape-ref"),
    )
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(tmp_path),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        safe_summary="Inspect repo status through the exact command lane.",
    )

    result = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:runtime-command-hardline-block",
    )

    assert result.record.status == "execution_blocked"
    assert result.command_execution_enabled is False
    assert result.error_category == (
        f"{RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE}:destructive_filesystem"
    )
    assert calls == []
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.record.receipt.command_receipt_metadata is not None
    assert (
        result.record.receipt.command_receipt_metadata.command_execution_attempted
        is False
    )


def test_runtime_gateway_approved_command_hardline_floor_blocks_before_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def runner(**kwargs: object) -> RuntimeCommandRunResult:
        calls.append(kwargs)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"should-not-run",
        )

    store = RuntimeInvocationStore(tmp_path)
    command_request = _approved_runtime_command_request()
    approved = _bind_runtime_action_inbox_approval(
        store,
        command_request=command_request,
    )
    execute_command_request = command_request.model_copy(
        update={"approval_ref": approved.action_inbox_envelope.approval_ref}
    )
    execute_request = _runtime_execute_request(approved)
    monkeypatch.setattr(
        command_module,
        "_argv_for_entry",
        lambda *_args, **_kwargs: ("rm", "-rf", "shape-ref"),
    )
    gateway = RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )

    result = gateway.execute_approved_command(
        approved.invocation_ref,
        execute_command_request,
        execute_request,
        idempotency_ref="idempotency-ref:runtime-command-approved-hardline-block",
    )

    assert result.record.status == "execution_blocked"
    assert result.command_execution_enabled is False
    assert result.error_category == (
        f"{RUNTIME_HARDLINE_COMMAND_BLOCKLIST_DENY_CODE}:destructive_filesystem"
    )
    assert calls == []
    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    assert result.record.receipt.command_receipt_metadata is not None
    assert (
        result.record.receipt.command_receipt_metadata.command_execution_attempted
        is False
    )


def test_hardline_command_blocklist_api_returns_read_only_posture() -> None:
    response = client.get("/api/runtime/hardline-command-blocklist")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_hardline_command_blocklist"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/hardline-command-blocklist"
    assert data["non_overridable_floor"] is True
    assert data["override_bypass_permitted"] is False
    assert data["command_execution_performed"] is False
    assert data["raw_command_text_persisted"] is False
    serialized = json.dumps(body).lower()
    assert "/users/" not in serialized
    assert "should-not-run" not in serialized


def test_hardline_command_blocklist_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-hardline-command-blocklist",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_hardline_command_blocklist"]
    assert payload["safe_refs_only"] is True
    assert payload["raw_command_text_omitted"] is True
    assert payload["raw_command_output_omitted"] is True
    assert payload["command_execution_performed"] is False
    assert payload["runner_invocation_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/hardline-command-blocklist"
    assert read_model["cli_ref"] == "uaa runtime inspect-hardline-command-blocklist"
    assert read_model["override_bypass_permitted"] is False


def _approved_runtime_command_request() -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent="focused_pytest",
        requested_profile="operator-approved",
        target_refs=["test-ref:governed-runtime-contracts"],
        approval_ref=None,
        safe_summary="Run the exact focused governed runtime contract test lane.",
    )


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def _runtime_action_inbox_refs(record, *, decision: str = "approve") -> dict[str, str]:
    exact_scope_ref = _test_hash_ref(
        "runtime-approval-scope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
            "requested_authority": record.request.requested_authority,
        },
    )
    approval_ref = _test_hash_ref(
        "runtime-action-inbox-approval-ref",
        {
            "invocation_ref": record.invocation_ref,
            "requested_authority": record.request.requested_authority,
            "requested_profile": record.request.requested_profile,
            "adapter_id": "governed-command-runtime-adapter",
            "command_intent": "focused_pytest",
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
    )
    action_envelope_ref = _test_hash_ref(
        "runtime-action-envelope-ref",
        {
            "invocation_ref": record.invocation_ref,
            "approval_ref": approval_ref,
            "decision": decision,
            "exact_scope_ref": exact_scope_ref,
        },
    )
    return {
        "approval_ref": approval_ref,
        "action_envelope_ref": action_envelope_ref,
        "exact_scope_ref": exact_scope_ref,
    }


def _runtime_execute_request(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    envelope = record.action_inbox_envelope
    return RuntimeExecuteRequest(
        approval_ref=envelope.approval_ref,
        action_envelope_ref=envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
    )


def _bind_runtime_action_inbox_approval(
    store: RuntimeInvocationStore,
    *,
    command_request: RuntimeCommandExecutionRequest,
):
    created = store.create_invocation(
        runtime_command_invocation_request(command_request),
        idempotency_ref="idempotency-ref:runtime-action-inbox-hardline-create",
    )
    refs = _runtime_action_inbox_refs(created.record)
    return store.bind_approval(
        created.record.invocation_ref,
        RuntimeApprovalBindingRequest(
            decision="approve",
            action_envelope_ref=refs["action_envelope_ref"],
            exact_scope_ref=refs["exact_scope_ref"],
            expected_payload_fingerprint_ref=created.record.payload_fingerprint_ref,
            expected_policy_decision_ref=created.record.policy_decision.policy_decision_ref,
            adapter_id="governed-command-runtime-adapter",
            command_intent="focused_pytest",
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary="Action Inbox approved exact focused pytest runtime lane.",
        ),
        idempotency_ref="idempotency-ref:runtime-action-inbox-hardline-approve",
    )
