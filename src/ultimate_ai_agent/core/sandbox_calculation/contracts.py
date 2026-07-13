from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.safe_refs import hash_text


SEALED_CALCULATION_SCHEMA_VERSION = "uaa-sealed-calculation.v1"
SEALED_CALCULATION_LANE_REF = "lane-ref:sealed-arithmetic-exact-lease"
SEALED_CALCULATION_CAPABILITY_REF = "authority-capability-ref:sealed-arithmetic-v1"
SEALED_CALCULATION_ADAPTER_REF = "authority-adapter-ref:sealed-arithmetic-docker-v1"
SEALED_CALCULATION_TOOL_REF = "tool:sealed_calculation.v1"
SEALED_CALCULATION_TOOL_NAME = "sealed_calculation"
SEALED_CALCULATION_TARGET_REF = "target-ref:sealed-calculation-runtime-v1"
SEALED_CALCULATION_SAFE_DISABLE_REF = "safe-disable-ref:sealed-calculation-runtime-v1"
SEALED_CALCULATION_ROLLBACK_REF = "rollback-ref:sealed-calculation-no-side-effects"
SEALED_CALCULATION_KILL_SWITCH_REF = "kill-switch-ref:sealed-calculation-local"
SEALED_CALCULATION_RECEIPT_CONTRACT_REF = (
    "receipt-contract-ref:sealed-calculation-execution-v1"
)


class SealedCalculationStatus(str, Enum):
    succeeded = "succeeded"
    denied = "denied"
    timed_out = "timed_out"
    output_limit_exceeded = "output_limit_exceeded"
    backend_unavailable = "backend_unavailable"
    killed = "killed"
    recovery_required = "recovery_required"
    failed = "failed"


class _SealedCalculationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SealedCalculationLimits(_SealedCalculationModel):
    wall_time_seconds: Literal[2.0] = 2.0
    startup_time_seconds: Literal[3.0] = 3.0
    memory_bytes: Literal[67108864] = 64 * 1024 * 1024
    cpu_quota: Literal[0.25] = 0.25
    pids_limit: Literal[1] = 1
    tmpfs_bytes: Literal[1048576] = 1024 * 1024
    stdout_limit_bytes: Literal[2048] = 2048
    stderr_limit_bytes: Literal[1024] = 1024
    expression_limit_bytes: Literal[512] = 512


class SealedCalculationRequest(_SealedCalculationModel):
    schema_version: Literal["uaa-sealed-calculation.v1"] = (
        SEALED_CALCULATION_SCHEMA_VERSION
    )
    request_ref: str
    input_ref: str
    expression: str = Field(
        ...,
        min_length=1,
        max_length=512,
        exclude=True,
        repr=False,
    )
    expression_sha256: str
    target_ref: Literal["target-ref:sealed-calculation-runtime-v1"] = (
        SEALED_CALCULATION_TARGET_REF
    )
    limits: SealedCalculationLimits = Field(default_factory=SealedCalculationLimits)

    @model_validator(mode="after")
    def validate_request(self) -> "SealedCalculationRequest":
        validate_execution_ref(self.request_ref, "sealed_calculation_request_ref")
        validate_execution_ref(self.input_ref, "sealed_calculation_input_ref")
        validate_execution_ref(self.target_ref, "sealed_calculation_target_ref")
        if self.expression_sha256 != hash_text(self.expression):
            raise ValueError("SEALED_CALCULATION_EXPRESSION_HASH_MISMATCH")
        if len(self.expression.encode("utf-8")) > self.limits.expression_limit_bytes:
            raise ValueError("SEALED_CALCULATION_EXPRESSION_SIZE_LIMIT_EXCEEDED")
        return self


class SealedCalculationBackendAttestation(_SealedCalculationModel):
    attestation_ref: str
    image_ref: str
    image_id_ref: str
    seccomp_profile_ref: str
    runner_contract_ref: str
    runner_source_ref: str
    backend_ref: str
    platform_ref: str
    docker_cli_ref: str
    docker_daemon_ref: str
    container_config_ref: str
    limits_ref: str
    no_invocation_pull: Literal[True] = True
    no_host_mounts: Literal[True] = True
    network_disabled: Literal[True] = True
    read_only_root: Literal[True] = True
    non_root_user: Literal[True] = True
    no_new_privileges: Literal[True] = True
    capabilities_dropped: Literal[True] = True
    one_process_limit: Literal[True] = True
    safe_summary: str = (
        "Sealed calculation backend attested with exact local runtime bindings."
    )

    @model_validator(mode="after")
    def validate_attestation(self) -> "SealedCalculationBackendAttestation":
        for ref in (
            self.attestation_ref,
            self.image_ref,
            self.image_id_ref,
            self.seccomp_profile_ref,
            self.runner_contract_ref,
            self.runner_source_ref,
            self.backend_ref,
            self.platform_ref,
            self.docker_cli_ref,
            self.docker_daemon_ref,
            self.container_config_ref,
            self.limits_ref,
        ):
            validate_execution_ref(ref, "sealed_calculation_attestation_ref")
        validate_safe_execution_text(self.safe_summary, "sealed_calculation_summary")
        return self


class SealedCalculationResult(_SealedCalculationModel):
    schema_version: Literal["uaa-sealed-calculation.v1"] = (
        SEALED_CALCULATION_SCHEMA_VERSION
    )
    execution_ref: str
    request_ref: str
    input_ref: str
    status: SealedCalculationStatus
    expression_sha256: str
    output_sha256: str | None = None
    result_preview: str | None = Field(default=None, max_length=128)
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(..., min_length=1)
    receipt_ref: str
    attestation_ref: str
    output_truncated: bool = False
    redaction_status: Literal["safe_numeric_preview_only"] = "safe_numeric_preview_only"
    code_output_is_evidence_not_authority: Literal[True] = True
    raw_expression_persisted: Literal[False] = False
    raw_environment_persisted: Literal[False] = False
    raw_paths_persisted: Literal[False] = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_result(self) -> "SealedCalculationResult":
        for ref in (
            self.execution_ref,
            self.request_ref,
            self.input_ref,
            self.receipt_ref,
            self.attestation_ref,
            *self.evidence_refs,
        ):
            validate_execution_ref(ref, "sealed_calculation_result_ref")
        validate_safe_execution_text(self.safe_summary, "sealed_calculation_summary")
        if self.status == SealedCalculationStatus.succeeded:
            if self.output_sha256 is None or self.result_preview is None:
                raise ValueError("SEALED_CALCULATION_SUCCESS_OUTPUT_REQUIRED")
            if self.reason_codes:
                raise ValueError("SEALED_CALCULATION_SUCCESS_REASONS_FORBIDDEN")
        elif not self.reason_codes:
            raise ValueError("SEALED_CALCULATION_FAILURE_REASON_REQUIRED")
        return self
