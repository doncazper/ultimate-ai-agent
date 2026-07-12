import hashlib
import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.control_center.runtime_action_bridge import (
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    RuntimeActionSignedEvidenceEnvelope,
    RuntimeApprovalBindingRequest,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeInvocationStore,
    RuntimeSafeDisableRequest,
    build_runtime_action_signed_evidence,
    runtime_command_invocation_request,
    verify_runtime_action_signed_evidence,
)
from ultimate_ai_agent.core.time import utc_now
from tests.authority_helpers import workspace_execute_authority_lease


ROOT = Path(__file__).resolve().parents[1]


def _runtime_store_with_workspace_execute(tmp_path: Path) -> RuntimeInvocationStore:
    return RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[workspace_execute_authority_lease()],
    )


def _test_hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def _command_request(intent: str = "focused_pytest") -> RuntimeCommandExecutionRequest:
    return RuntimeCommandExecutionRequest(
        intent=intent,
        requested_profile="operator-approved",
        target_refs=[
            f"test-ref:runtime-action-signed-evidence-{intent.replace('_', '-')}"
        ],
        approval_ref=None,
        safe_summary=f"Run the exact {intent} runtime signed evidence test lane.",
    )


def _runtime_action_inbox_refs(record, *, decision: str = "approve") -> dict[str, str]:
    command_intent = str(record.request.action_ref).removeprefix(
        "action-ref:runtime-command-"
    )
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
            "command_intent": command_intent,
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


def _approve(store: RuntimeInvocationStore, request: RuntimeCommandExecutionRequest):
    command_intent = str(getattr(request.intent, "value", request.intent))
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref=(
            f"idempotency-ref:runtime-action-evidence-create-{command_intent}"
        ),
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
            command_intent=command_intent,
            risk_class="medium",
            expires_at=utc_now() + timedelta(minutes=30),
            safe_summary=f"Action Inbox approved exact {command_intent} runtime lane.",
        ),
        idempotency_ref=(
            f"idempotency-ref:runtime-action-evidence-approve-{command_intent}"
        ),
    )


def _execute_request(record) -> RuntimeExecuteRequest:
    assert record.action_inbox_envelope is not None
    return RuntimeExecuteRequest(
        approval_ref=record.action_inbox_envelope.approval_ref,
        action_envelope_ref=record.action_inbox_envelope.action_envelope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        safe_summary="Execute approved runtime command through exact bridge.",
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
            duration_ms=2,
            output_bytes=b"raw output must never persist",
        )

    return RuntimeGateway(
        store=store,
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
    )


@pytest.mark.parametrize(
    "intent",
    ["focused_pytest", "repo_verifier", "frontend_check", "repo_doctor"],
)
def test_runtime_action_signed_evidence_pass_path_is_verifiable(
    tmp_path: Path,
    intent: str,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request(intent)
    approved = _approve(store, request)
    result = _gateway_with_runner(store).execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref=f"idempotency-ref:runtime-action-evidence-execute-{intent}",
    )

    envelope = build_runtime_action_signed_evidence(result.record)
    verification = verify_runtime_action_signed_evidence(envelope)

    assert isinstance(envelope, RuntimeActionSignedEvidenceEnvelope)
    assert envelope.receipt_ref == result.record.receipt.receipt_ref
    assert envelope.action_envelope_ref == approved.action_inbox_envelope.action_envelope_ref
    assert envelope.approval_validated is True
    assert envelope.command_intent == intent
    assert envelope.execution_performed is True
    assert envelope.command_execution_performed is True
    assert envelope.route_decision_binding_ref.startswith("route-decision-binding-ref:")
    assert envelope.envelope_hash_ref.startswith("runtime-action-evidence-hash-ref:")
    assert envelope.signed_envelope_ref.startswith("runtime-action-signed-envelope-ref:")
    assert envelope.integrity_posture == "sha256_hash_only_not_a_cryptographic_signature"
    assert envelope.cryptographic_signature_present is False
    assert envelope.external_anchor_verified is False
    assert envelope.legacy_signed_envelope_ref_is_hash_only is True
    assert verification.verification_status == "passed"
    assert verification.tamper_detected is False
    assert verification.cryptographic_signature_verified is False

    payload = json.dumps(envelope.model_dump(mode="json"), sort_keys=True)
    assert "raw output must never persist" not in payload
    assert str(tmp_path) not in payload
    assert '"raw_command_output_persisted": false' in payload.lower()

    read_model = build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    assert read_model["signed_evidence_refs"] == [envelope.signed_envelope_ref]
    assert read_model["items"][0]["signed_evidence_ref"] == envelope.signed_envelope_ref
    assert read_model["items"][0]["signed_evidence_verification_status"] == "passed"


def test_runtime_action_signed_evidence_requires_receipt_and_action_envelope(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request()
    created = store.create_invocation(
        runtime_command_invocation_request(request),
        idempotency_ref="idempotency-ref:runtime-action-evidence-missing-create",
    )

    with pytest.raises(ValueError, match="RUNTIME_ACTION_EVIDENCE_RECEIPT_REQUIRED"):
        build_runtime_action_signed_evidence(created.record)


def test_runtime_action_signed_evidence_detects_scope_drift_and_tamper(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request()
    approved = _approve(store, request)
    changed = _approved_command_request(request, approved).model_copy(
        update={"target_refs": ["test-ref:runtime-action-signed-evidence-drift"]}
    )
    result = _gateway_with_runner(store).execute_approved_command(
        approved.invocation_ref,
        changed,
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-evidence-scope-drift",
    )

    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    envelope = build_runtime_action_signed_evidence(result.record)
    verified = verify_runtime_action_signed_evidence(envelope)
    assert verified.verification_status == "passed"
    assert envelope.execution_performed is False
    assert "blocked-state:runtime-command-action-inbox-scope-changed" in (
        envelope.blocked_reason_refs
    )

    tampered = envelope.model_dump(mode="json") | {
        "exact_scope_ref": "runtime-approval-scope-ref:tampered"
    }
    tampered_result = verify_runtime_action_signed_evidence(tampered)
    assert tampered_result.verification_status == "failed"
    assert tampered_result.tamper_detected is True
    assert (
        "failure-reason-ref:runtime-action-evidence:envelope-hash-invalid"
        in tampered_result.failure_reason_refs
    )

    for unsafe in (
        envelope.model_dump(mode="json") | {"raw_prompt": "unsafe"},
        envelope.model_dump(mode="json") | {"cryptographic_signature_present": True},
        envelope.model_dump(mode="json") | {"envelope_ref": "/Users/private"},
    ):
        rejected = verify_runtime_action_signed_evidence(unsafe)
        assert rejected.verification_status == "failed"
        assert rejected.tamper_detected is True


def test_runtime_action_signed_evidence_idempotent_replay_is_stable(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request()
    approved = _approve(store, request)
    gateway = _gateway_with_runner(store)
    first = gateway.execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-evidence-replay",
    )
    replay = gateway.execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-evidence-replay",
    )

    first_envelope = build_runtime_action_signed_evidence(first.record)
    replay_envelope = build_runtime_action_signed_evidence(replay.record)
    assert replay.replayed is True
    assert first.record.receipt.receipt_ref == replay.record.receipt.receipt_ref
    assert first_envelope.receipt_ref == replay_envelope.receipt_ref
    assert verify_runtime_action_signed_evidence(replay_envelope).verification_status == "passed"


def test_runtime_action_signed_evidence_safe_disable_blocks_execution(
    tmp_path: Path,
) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request()
    approved = _approve(store, request)
    store.safe_disable(
        RuntimeSafeDisableRequest(reason_ref="reason-ref:runtime-action-evidence-disable"),
        idempotency_ref="idempotency-ref:runtime-action-evidence-disable",
    )
    result = _gateway_with_runner(store).execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-evidence-safe-disabled",
    )

    assert result.record.receipt is not None
    assert result.record.receipt.command_execution_performed is False
    envelope = build_runtime_action_signed_evidence(result.record)
    assert envelope.safe_disable_active is True
    assert envelope.execution_performed is False
    assert verify_runtime_action_signed_evidence(envelope).verification_status == "passed"


def test_runtime_action_signed_evidence_cli_export_and_verify(tmp_path: Path) -> None:
    store = _runtime_store_with_workspace_execute(tmp_path)
    request = _command_request()
    approved = _approve(store, request)
    result = _gateway_with_runner(store).execute_approved_command(
        approved.invocation_ref,
        _approved_command_request(request, approved),
        _execute_request(approved),
        idempotency_ref="idempotency-ref:runtime-action-evidence-cli-execute",
    )
    receipt_ref = result.record.receipt.receipt_ref

    export = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "--state-dir",
            str(tmp_path),
            "receipts",
            "evidence",
            receipt_ref,
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(export.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:governed-runtime-receipt-signed-evidence"
    )
    assert payload["safe_refs_only"] is True
    assert str(tmp_path) not in export.stdout

    envelope_path = tmp_path / "runtime-action-evidence.json"
    envelope_path.write_text(
        json.dumps(payload["runtime_action_signed_evidence"], sort_keys=True),
        encoding="utf-8",
    )
    verify = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "receipts",
            "verify-evidence",
            "--input",
            str(envelope_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    verification = json.loads(verify.stdout)["verification"]
    assert verification["verification_status"] == "passed"
    assert str(envelope_path) not in verify.stdout

    symlink_path = tmp_path / "runtime-action-evidence-symlink.json"
    symlink_path.symlink_to(envelope_path)
    rejected = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/dev/uaa_runtime.py"),
            "receipts",
            "verify-evidence",
            "--input",
            str(symlink_path),
            "--json",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert rejected.returncode == 1
    assert str(symlink_path) not in rejected.stdout
    assert str(symlink_path) not in rejected.stderr
