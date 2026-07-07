from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_REMOTE_EXECUTION_POSTURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-remote-execution-posture:v1"
)
RUNTIME_REMOTE_EXECUTION_POSTURE_CLI_REF = (
    "uaa runtime inspect-remote-execution-posture"
)
RUNTIME_REMOTE_EXECUTION_POSTURE_DOC_REF = (
    "docs/runtime/UAA_HERMES_RUNTIME_REMOTE_EXECUTION_POSTURE.md"
)
RUNTIME_REMOTE_EXECUTION_POSTURE_SNAPSHOT_REF = (
    "remote-execution-posture-snapshot-ref:runtime:phase-43"
)
RUNTIME_REMOTE_EXECUTION_POSTURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-43:remote-execution-posture"
)
RUNTIME_REMOTE_EXECUTION_POSTURE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-43:remote-execution-posture"
)

RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:remote-execution-no-secure-host",
    "blocked-authority:remote-execution-no-cloud-sandbox",
    "blocked-authority:remote-execution-no-remote-shell",
    "blocked-authority:remote-execution-no-file-sync",
    "blocked-authority:remote-execution-no-protected-material",
    "blocked-authority:remote-execution-no-remote-process-control",
    "blocked-authority:remote-execution-no-credential-persistence",
    "blocked-authority:remote-execution-no-control-center-authority-mint",
)


class RuntimeExecutionBackendKind(str, Enum):
    local_workspace = "local_workspace"
    local_container = "local_container"
    secure_host = "secure_host"
    cloud_sandbox = "cloud_sandbox"
    serverless_worker = "serverless_worker"
    remote_gpu = "remote_gpu"


class RuntimeExecutionBackendStatus(str, Enum):
    capability_map_only = "capability_map_only"
    blocked_until_authority = "blocked_until_authority"


class RuntimeExecutionBackendCapability(BaseModel):
    backend_ref: str
    backend_kind: RuntimeExecutionBackendKind
    display_label: str
    status: RuntimeExecutionBackendStatus
    safe_summary: str
    workspace_boundary_ref: str
    credential_policy_ref: str
    network_policy_ref: str
    receipt_plan_ref: str
    budget_ref: str
    rollback_ref: str
    kill_switch_ref: str
    proof_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    remote_execution_enabled: bool = False
    ssh_enabled: bool = False
    cloud_sandbox_enabled: bool = False
    remote_shell_enabled: bool = False
    file_sync_enabled: bool = False
    remote_secret_access_enabled: bool = False
    remote_process_control_enabled: bool = False
    credential_material_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_backend(self) -> "RuntimeExecutionBackendCapability":
        for value, field_name in [
            (self.backend_ref, "backend_ref"),
            (self.workspace_boundary_ref, "workspace_boundary_ref"),
            (self.credential_policy_ref, "credential_policy_ref"),
            (self.network_policy_ref, "network_policy_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.budget_ref, "budget_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (str(self.backend_kind), "backend_kind"),
            (self.display_label, "display_label"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "remote_execution_enabled": self.remote_execution_enabled,
            "ssh_enabled": self.ssh_enabled,
            "cloud_sandbox_enabled": self.cloud_sandbox_enabled,
            "remote_shell_enabled": self.remote_shell_enabled,
            "file_sync_enabled": self.file_sync_enabled,
            "remote_secret_access_enabled": self.remote_secret_access_enabled,
            "remote_process_control_enabled": self.remote_process_control_enabled,
            "credential_material_persisted": self.credential_material_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_REMOTE_EXECUTION_BACKEND_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_REMOTE_EXECUTION_BACKEND_BLOCKERS_REQUIRED")
        return self


class RuntimeRemoteExecutionPostureReadModel(BaseModel):
    schema_version: str = "runtime_remote_execution_posture.v1"
    contract_ref: str = RUNTIME_REMOTE_EXECUTION_POSTURE_CONTRACT_REF
    status: str = "capability_map_only"
    snapshot_ref: str = RUNTIME_REMOTE_EXECUTION_POSTURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:remote-execution-posture:pending"
    cli_ref: str = RUNTIME_REMOTE_EXECUTION_POSTURE_CLI_REF
    doc_ref: str = RUNTIME_REMOTE_EXECUTION_POSTURE_DOC_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Execution backends are represented as capability-map posture only; "
        "remote execution, secure host access, cloud sandboxes, file sync, "
        "protected material access, and remote process control remain blocked."
    )
    backends: list[RuntimeExecutionBackendCapability] = Field(default_factory=list)
    backend_count: int = 0
    blocked_backend_count: int = 0
    remote_execution_enabled: bool = False
    ssh_enabled: bool = False
    cloud_sandbox_enabled: bool = False
    remote_shell_enabled: bool = False
    file_sync_enabled: bool = False
    remote_secret_access_enabled: bool = False
    remote_process_control_enabled: bool = False
    credential_material_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "credential_material_omitted",
            "remote_paths_omitted",
            "remote_logs_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeRemoteExecutionPostureReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.cli_ref, "cli_ref"),
            (self.doc_ref, "doc_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        denied_flags = {
            "remote_execution_enabled": self.remote_execution_enabled,
            "ssh_enabled": self.ssh_enabled,
            "cloud_sandbox_enabled": self.cloud_sandbox_enabled,
            "remote_shell_enabled": self.remote_shell_enabled,
            "file_sync_enabled": self.file_sync_enabled,
            "remote_secret_access_enabled": self.remote_secret_access_enabled,
            "remote_process_control_enabled": self.remote_process_control_enabled,
            "credential_material_persisted": self.credential_material_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_REMOTE_EXECUTION_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_REMOTE_EXECUTION_BLOCKERS_REQUIRED")
        if self.backend_count != len(self.backends):
            raise ValueError("RUNTIME_REMOTE_EXECUTION_COUNT_MISMATCH")
        if self.blocked_backend_count != len(
            [
                backend
                for backend in self.backends
                if backend.status == RuntimeExecutionBackendStatus.blocked_until_authority
            ]
        ):
            raise ValueError("RUNTIME_REMOTE_EXECUTION_BLOCKED_COUNT_MISMATCH")
        return self


def _backend(
    backend_kind: RuntimeExecutionBackendKind,
    display_label: str,
    summary: str,
) -> RuntimeExecutionBackendCapability:
    token = backend_kind.value.replace("_", "-")
    return RuntimeExecutionBackendCapability(
        backend_ref=f"execution-backend-ref:runtime:{token}",
        backend_kind=backend_kind,
        display_label=display_label,
        status=RuntimeExecutionBackendStatus.blocked_until_authority,
        safe_summary=summary,
        workspace_boundary_ref=f"workspace-boundary-ref:execution-backend:{token}",
        credential_policy_ref=f"credential-policy-ref:execution-backend:{token}",
        network_policy_ref=f"network-policy-ref:execution-backend:{token}",
        receipt_plan_ref=f"receipt-plan-ref:execution-backend:{token}",
        budget_ref=f"budget-ref:execution-backend:{token}",
        rollback_ref=f"rollback-ref:execution-backend:{token}",
        kill_switch_ref=f"kill-switch-ref:execution-backend:{token}",
        proof_ref=f"proof-ref:remote-execution:{token}",
        blocked_authority_refs=list(RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:remote-execution:{token}:policy",
            f"promotion-path-ref:remote-execution:{token}:credential-ref",
            f"promotion-path-ref:remote-execution:{token}:receipt-budget",
            f"promotion-path-ref:remote-execution:{token}:kill-switch",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:remote-execution:{token}:backend-contract"
        ],
    )


def build_runtime_remote_execution_posture_read_model() -> (
    RuntimeRemoteExecutionPostureReadModel
):
    backends = [
        _backend(
            RuntimeExecutionBackendKind.local_workspace,
            "Local workspace",
            "Local workspace execution authority remains limited to active "
            "AuthorityLease-gated capabilities; this abstraction grants no "
            "generic execution.",
        ),
        _backend(
            RuntimeExecutionBackendKind.local_container,
            "Local container",
            "Container execution remains blocked until workspace boundary, network "
            "policy, receipt, budget, and kill-switch controls are proven.",
        ),
        _backend(
            RuntimeExecutionBackendKind.secure_host,
            "Secure host",
            "Secure host execution remains blocked until remote policy, credential "
            "refs, network policy, receipt, and kill-switch controls are proven.",
        ),
        _backend(
            RuntimeExecutionBackendKind.cloud_sandbox,
            "Cloud sandbox",
            "Cloud sandbox execution remains blocked until credential refs, "
            "workspace boundary, cost, receipt, and rollback posture are proven.",
        ),
        _backend(
            RuntimeExecutionBackendKind.serverless_worker,
            "Serverless worker",
            "Serverless execution remains blocked until remote policy, deployment "
            "boundary, budget, receipt, and revoke posture are proven.",
        ),
        _backend(
            RuntimeExecutionBackendKind.remote_gpu,
            "Remote GPU",
            "Remote GPU execution remains blocked until credential refs, cost "
            "budget, data boundary, receipt, and safe-disable controls are proven.",
        ),
    ]
    payload = {
        "backends": backends,
        "backend_count": len(backends),
        "blocked_backend_count": len(backends),
        "blocked_authority_refs": list(RUNTIME_REMOTE_EXECUTION_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:remote-execution:remote-policy",
            "promotion-path-ref:remote-execution:credential-refs",
            "promotion-path-ref:remote-execution:workspace-boundary",
            "promotion-path-ref:remote-execution:network-policy",
            "promotion-path-ref:remote-execution:receipt-budget",
            "promotion-path-ref:remote-execution:rollback-kill-switch",
        ],
        "proof_refs": [RUNTIME_REMOTE_EXECUTION_POSTURE_PROOF_REF],
        "verifier_refs": [RUNTIME_REMOTE_EXECUTION_POSTURE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:remote-execution:backend-contract",
            "next-safe-action-ref:remote-execution:credential-boundary",
        ],
    }
    snapshot_material = {
        "contract_ref": RUNTIME_REMOTE_EXECUTION_POSTURE_CONTRACT_REF,
        "cli_ref": RUNTIME_REMOTE_EXECUTION_POSTURE_CLI_REF,
        "backend_refs": [backend.backend_ref for backend in backends],
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:remote-execution-posture:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeRemoteExecutionPostureReadModel(**payload)
