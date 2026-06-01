from datetime import UTC, datetime, timedelta

from tests.m7_helpers import classification
from tests.m8_helpers import runtime_request, simulated_manifest
from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)


def loopback_endpoint(**overrides):
    from ultimate_ai_agent.core.model_runtime import LoopbackRuntimeEndpoint, ModelRuntimeKind

    payload = {
        "endpoint_id": "loop_local",
        "base_url": "http://127.0.0.1:11434/api/generate",
        "allowed_hosts": ["127.0.0.1", "localhost", "::1"],
        "runtime_kind": ModelRuntimeKind.local_stub,
        "model_id": "local_coder_model",
        "enabled": True,
        "owner": "tests",
        "source": "fixture",
        "version": "0.0.0",
        "metadata": {},
    }
    payload.update(overrides)
    return LoopbackRuntimeEndpoint(**payload)


def loopback_policy(**overrides):
    from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

    payload = {
        "policy_id": "m9_policy",
        "allow_real_loopback_execution": True,
        "max_input_tokens": 4096,
        "max_output_tokens": 1024,
    }
    payload.update(overrides)
    return LoopbackRuntimePolicy(**payload)


def local_manifest(**overrides):
    manifest = simulated_manifest()
    payload = manifest.model_dump()
    payload.update(
        {
            "adapter_id": "local_loopback_adapter",
            "runtime_kind": "local_stub",
            "safety_mode": "local_loopback_dev",
            "accepts_model_profile_ids": ["local_coder"],
            "requires_credential_ref": False,
            "allowed_credential_refs": [],
        }
    )
    payload.update(overrides)
    from ultimate_ai_agent.core.model_runtime import ModelRuntimeAdapterManifest

    return ModelRuntimeAdapterManifest(**payload)


def local_runtime_request(**overrides):
    payload = runtime_request(secret_handle_refs=[]).model_dump()
    payload.update(
        {
            "adapter_id": "local_loopback_adapter",
            "safety_mode": "local_loopback_dev",
            "route_decision_ref": "mroute_selected",
            "metadata": {"route_reason_codes": ["SELECTED_PROFILE"]},
        }
    )
    payload.update(overrides)
    from ultimate_ai_agent.core.model_runtime import ModelRuntimeRequest

    return ModelRuntimeRequest(**payload)


def approval_for_runtime(request=None, *, action="execute_local_loopback_model"):
    runtime_request = request or local_runtime_request()
    approval_request = ApprovalRequest(
        approval_request_id=f"areq_{runtime_request.runtime_request_id}",
        run_id=runtime_request.run_id,
        subject_type=ApprovalSubjectType.model_runtime_request,
        subject_id=runtime_request.runtime_request_id,
        actor_context=runtime_request.actor_context,
        requested_action=action,
        purpose="Approve local loopback model runtime execution.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=classification(),
        resource_refs=[runtime_request.adapter_id, runtime_request.model_profile_id],
        consent_refs=runtime_request.consent_refs,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    return authority, approval_request, grant, authority.validate_for_request(approval_request, grant.approval_ref)
