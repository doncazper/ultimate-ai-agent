from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.local_model_management.gateway import (
    DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
    FakeM164GatewayTransport,
    M164ChatCompletionRequest,
    M164GatewayTransport,
    M164LocalGatewayModel,
    build_m164_chat_completion_response,
    build_m164_local_models_response,
    llama_cpp_gateway_authorized,
)
from ultimate_ai_agent.core.local_model_management.llama_cpp_supervisor import (
    M163LlamaCppServerPreset,
    M163LlamaCppSupervisor,
    M163ProcessFactory,
    validate_m163_llama_cpp_supervisor_result,
)
from ultimate_ai_agent.core.openwebui_bridge.local_test_shell import (
    DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY,
    UAA_OPENWEBUI_TEST_MODEL_ID,
    OpenWebUILocalChatCompletionRequest,
    build_openwebui_local_chat_completion_response,
    build_openwebui_local_models_response,
    openwebui_test_gateway_authorized,
)


class LocalModelE2ESmokeStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    blocked = "blocked"
    skipped = "skipped"


class LocalModelE2ESmokeStep(str, Enum):
    approved_gguf_readiness = "approved_gguf_readiness"
    llama_cpp_supervisor = "llama_cpp_supervisor"
    v1_models = "v1_models"
    v1_chat_completions = "v1_chat_completions"
    openwebui_shell_compatibility = "openwebui_shell_compatibility"
    auth_failure = "auth_failure"
    safe_failure = "safe_failure"
    rollback = "rollback"
    tools_functions_streaming_denial = "tools_functions_streaming_denial"


class _LocalModelE2ESmokeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LocalModelE2ESmokePrerequisites(_LocalModelE2ESmokeModel):
    approved_gguf_ref: str | None = None
    reviewer_ref: str | None = None
    llama_server_path_hint: str | None = None
    model_path_hint: str | None = None
    llama_cpp_lifecycle_allowed: bool = False
    gateway_model_ref: str = "model-ref:p0-005:local-llama-cpp"
    rollback_plan_ref: str = "rollback-ref:p0-005:known-good-local-model"
    openwebui_shell_ref: str = "openwebui-shell-ref:p0-005:local-test-shell"

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.gateway_model_ref, "gateway_model_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.openwebui_shell_ref, "openwebui_shell_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for value, field_name in [
            (self.approved_gguf_ref, "approved_gguf_ref"),
            (self.reviewer_ref, "reviewer_ref"),
        ]:
            if value is not None:
                _validate_m61_ref(value, field_name)
        return self


class LocalModelE2ESmokeStepResult(_LocalModelE2ESmokeModel):
    step: LocalModelE2ESmokeStep
    status: LocalModelE2ESmokeStatus
    evidence_ref: str
    result_ref: str
    safe_summary: str
    reviewer_ref: str | None = None
    blocker_ref: str | None = None
    skipped_ref: str | None = None
    redacted_summary_only: bool = True
    safe_refs_only: bool = True
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    raw_log_included: bool = False
    raw_path_included: bool = False
    credential_material_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.evidence_ref, "evidence_ref"),
            (self.result_ref, "result_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for value, field_name in [
            (self.reviewer_ref, "reviewer_ref"),
            (self.blocker_ref, "blocker_ref"),
            (self.skipped_ref, "skipped_ref"),
        ]:
            if value is not None:
                _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class LocalModelE2ESmokeReport(_LocalModelE2ESmokeModel):
    report_ref: str = "local-model-e2e-smoke-report:p0-005"
    source_checkpoint_ref: str = "checkpoint:m167"
    authority_gate_ref: str = "checkpoint:m166"
    status: LocalModelE2ESmokeStatus
    step_results: list[LocalModelE2ESmokeStepResult]
    evidence_refs: list[str]
    blocker_refs: list[str] = Field(default_factory=list)
    skipped_refs: list[str] = Field(default_factory=list)
    rollback_plan_ref: str = "rollback-ref:p0-005:known-good-local-model"
    safe_summary: str
    redacted_summary_only: bool = True
    safe_refs_only: bool = True
    local_dev_only: bool = True
    loopback_only: bool = True
    openwebui_shell_only: bool = True
    m166_exact_scope_bound: bool = True
    tools_enabled: bool = False
    functions_enabled: bool = False
    streaming_enabled: bool = False
    new_production_authority_granted: bool = False
    public_distribution_claimed: bool = False
    raw_prompt_exported: bool = False
    raw_response_exported: bool = False
    raw_provider_payload_exported: bool = False
    raw_log_exported: bool = False
    raw_path_exported: bool = False
    credential_material_exported: bool = False
    side_effect_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.source_checkpoint_ref, "source_checkpoint_ref"),
            (self.authority_gate_ref, "authority_gate_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in [
            *self.evidence_refs,
            *self.blocker_refs,
            *self.skipped_refs,
            *self.side_effect_refs,
        ]:
            _validate_m61_ref(ref, "smoke_report_ref")
        _validate_safe_payload(self.safe_summary)
        if self.evidence_refs != [step.evidence_ref for step in self.step_results]:
            raise ValueError("P0_005_EVIDENCE_REFS_MISMATCH")
        return self


def run_local_model_e2e_smoke_harness(
    prerequisites: LocalModelE2ESmokePrerequisites | None = None,
    *,
    process_factory: M163ProcessFactory | None = None,
    gateway_transport: M164GatewayTransport | None = None,
) -> LocalModelE2ESmokeReport:
    prereq = prerequisites or LocalModelE2ESmokePrerequisites()
    steps: list[LocalModelE2ESmokeStepResult] = []
    side_effect_refs: list[str] = []
    supervisor: M163LlamaCppSupervisor | None = None

    def add(
        step: LocalModelE2ESmokeStep,
        status: LocalModelE2ESmokeStatus,
        safe_summary: str,
        *,
        blocker_ref: str | None = None,
        skipped_ref: str | None = None,
    ) -> None:
        steps.append(
            LocalModelE2ESmokeStepResult(
                step=step,
                status=status,
                evidence_ref=f"evidence-ref:p0-005:{step.value}",
                result_ref=f"result-ref:p0-005:{step.value}:{status.value}",
                safe_summary=safe_summary,
                reviewer_ref=prereq.reviewer_ref,
                blocker_ref=blocker_ref,
                skipped_ref=skipped_ref,
            )
        )

    if prereq.approved_gguf_ref is None:
        add(
            LocalModelE2ESmokeStep.approved_gguf_readiness,
            LocalModelE2ESmokeStatus.skipped,
            "Approved GGUF readiness was skipped because no approved model ref was provided.",
            skipped_ref="skipped-ref:p0-005:approved-gguf-unavailable",
        )
    else:
        add(
            LocalModelE2ESmokeStep.approved_gguf_readiness,
            LocalModelE2ESmokeStatus.passed,
            "Approved GGUF readiness has an exact safe model ref.",
        )

    if prereq.llama_cpp_lifecycle_allowed:
        if not (prereq.llama_server_path_hint and prereq.model_path_hint):
            add(
                LocalModelE2ESmokeStep.llama_cpp_supervisor,
                LocalModelE2ESmokeStatus.blocked,
                "llama.cpp supervisor check is blocked until safe local runtime hints are reviewed.",
                blocker_ref="blocker-ref:p0-005:llama-cpp-runtime-hints-missing",
            )
        else:
            try:
                supervisor = M163LlamaCppSupervisor(process_factory=process_factory)
                result = supervisor.start(
                    M163LlamaCppServerPreset(
                        preset_ref="llama-cpp-preset:p0-005-smoke",
                        llama_server_path=prereq.llama_server_path_hint,
                        model_path=prereq.model_path_hint,
                    )
                )
                validate_m163_llama_cpp_supervisor_result(result)
                side_effect_refs.append("side-effect-ref:p0-005:llama-cpp-lifecycle-started")
                add(
                    LocalModelE2ESmokeStep.llama_cpp_supervisor,
                    LocalModelE2ESmokeStatus.passed,
                    "llama.cpp supervisor lifecycle produced a redacted loopback status.",
                )
            except Exception:
                add(
                    LocalModelE2ESmokeStep.llama_cpp_supervisor,
                    LocalModelE2ESmokeStatus.failed,
                    "llama.cpp supervisor lifecycle failed with details redacted.",
                )
    else:
        add(
            LocalModelE2ESmokeStep.llama_cpp_supervisor,
            LocalModelE2ESmokeStatus.skipped,
            "llama.cpp lifecycle was skipped because live lifecycle approval was not provided.",
            skipped_ref="skipped-ref:p0-005:llama-cpp-lifecycle-not-approved",
        )

    if prereq.approved_gguf_ref is None:
        add(
            LocalModelE2ESmokeStep.v1_models,
            LocalModelE2ESmokeStatus.skipped,
            "Local /v1 model list check was skipped because approved GGUF readiness is unavailable.",
            skipped_ref="skipped-ref:p0-005:v1-models-prerequisite-unavailable",
        )
        add(
            LocalModelE2ESmokeStep.v1_chat_completions,
            LocalModelE2ESmokeStatus.skipped,
            "Local /v1 chat completion check was skipped because approved GGUF readiness is unavailable.",
            skipped_ref="skipped-ref:p0-005:v1-chat-prerequisite-unavailable",
        )
    else:
        model_response = build_m164_local_models_response(M164LocalGatewayModel())
        chat_response = build_m164_chat_completion_response(
            M164ChatCompletionRequest(
                model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
                messages=[{"role": "user", "content": "local smoke request sample"}],
            ),
            gateway_model=M164LocalGatewayModel(),
            transport=gateway_transport or FakeM164GatewayTransport("local smoke response sample"),
        )
        if model_response["data"][0]["id"] == DEFAULT_UAA_LLAMA_CPP_MODEL_ID:
            add(
                LocalModelE2ESmokeStep.v1_models,
                LocalModelE2ESmokeStatus.passed,
                "Local /v1 model list returned the approved local model ref.",
            )
        else:
            add(
                LocalModelE2ESmokeStep.v1_models,
                LocalModelE2ESmokeStatus.failed,
                "Local /v1 model list did not return the approved local model ref.",
            )
        if chat_response["uaa_safety"]["tools_enabled"] is False:
            add(
                LocalModelE2ESmokeStep.v1_chat_completions,
                LocalModelE2ESmokeStatus.passed,
                "Local /v1 chat completion returned a redacted safe response envelope.",
            )
        else:
            add(
                LocalModelE2ESmokeStep.v1_chat_completions,
                LocalModelE2ESmokeStatus.failed,
                "Local /v1 chat completion returned an unsafe authority flag.",
            )

    _probe_openwebui_shell(add)
    _probe_auth_failure(add)
    _probe_safe_failure(add)

    if supervisor is None:
        add(
            LocalModelE2ESmokeStep.rollback,
            LocalModelE2ESmokeStatus.skipped,
            "Rollback check was skipped because no local lifecycle was started.",
            skipped_ref="skipped-ref:p0-005:rollback-no-started-lifecycle",
        )
    else:
        supervisor.stop()
        side_effect_refs.append("side-effect-ref:p0-005:llama-cpp-lifecycle-stopped")
        add(
            LocalModelE2ESmokeStep.rollback,
            LocalModelE2ESmokeStatus.passed,
            "Rollback check stopped the managed local lifecycle through the reviewed supervisor.",
        )

    _probe_tools_functions_streaming_denial(add)
    return _build_report(steps, prereq.rollback_plan_ref, side_effect_refs)


def _probe_openwebui_shell(add) -> None:
    models = build_openwebui_local_models_response()
    chat = build_openwebui_local_chat_completion_response(
        OpenWebUILocalChatCompletionRequest(
            model=UAA_OPENWEBUI_TEST_MODEL_ID,
            messages=[{"role": "user", "content": "shell smoke request sample"}],
        )
    )
    if (
        models["data"][0]["id"] == UAA_OPENWEBUI_TEST_MODEL_ID
        and chat["uaa_safety"]["openwebui_is_agent_brain"] is False
        and chat["uaa_safety"]["tool_executed"] is False
    ):
        add(
            LocalModelE2ESmokeStep.openwebui_shell_compatibility,
            LocalModelE2ESmokeStatus.passed,
            "OpenWebUI shell compatibility returned safe local OpenAI-compatible shapes.",
        )
    else:
        add(
            LocalModelE2ESmokeStep.openwebui_shell_compatibility,
            LocalModelE2ESmokeStatus.failed,
            "OpenWebUI shell compatibility returned unsafe shell authority state.",
        )


def _probe_auth_failure(add) -> None:
    openwebui_denied = not openwebui_test_gateway_authorized(
        "Bearer wrong",
        {"UAA_OPENWEBUI_TEST_GATEWAY_KEY": DEFAULT_UAA_OPENWEBUI_TEST_GATEWAY_KEY},
    )
    llama_denied = not llama_cpp_gateway_authorized(
        "Bearer wrong",
        {"UAA_LLAMA_CPP_GATEWAY_KEY": "local-smoke-key"},
    )
    add(
        LocalModelE2ESmokeStep.auth_failure,
        LocalModelE2ESmokeStatus.passed
        if openwebui_denied and llama_denied
        else LocalModelE2ESmokeStatus.failed,
        "Access check denied incorrect local values with redacted detail.",
    )


def _probe_safe_failure(add) -> None:
    try:
        M164ChatCompletionRequest(
            model=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
            stream=True,
            messages=[{"role": "user", "content": "failure smoke request sample"}],
        )
    except ValueError:
        status = LocalModelE2ESmokeStatus.passed
    else:
        status = LocalModelE2ESmokeStatus.failed
    add(
        LocalModelE2ESmokeStep.safe_failure,
        status,
        "Unsafe chat request shape failed safely with details redacted.",
    )


def _probe_tools_functions_streaming_denial(add) -> None:
    denied = 0
    probes: list[dict[str, Any]] = [
        {"stream": True},
        {"tools": [{"type": "function", "function": {"name": "unsafe"}}]},
        {"functions": [{"name": "unsafe"}]},
    ]
    for update in probes:
        payload: dict[str, Any] = {
            "model": DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
            "messages": [{"role": "user", "content": "denial smoke request sample"}],
        }
        payload.update(update)
        try:
            M164ChatCompletionRequest(**payload)
        except ValueError:
            denied += 1
    add(
        LocalModelE2ESmokeStep.tools_functions_streaming_denial,
        LocalModelE2ESmokeStatus.passed
        if denied == len(probes)
        else LocalModelE2ESmokeStatus.failed,
        "Tools, functions, and streaming were denied unless separately scoped later.",
    )


def _build_report(
    steps: list[LocalModelE2ESmokeStepResult],
    rollback_plan_ref: str,
    side_effect_refs: list[str],
) -> LocalModelE2ESmokeReport:
    statuses = {step.status for step in steps}
    if LocalModelE2ESmokeStatus.failed in statuses:
        status = LocalModelE2ESmokeStatus.failed
    elif LocalModelE2ESmokeStatus.blocked in statuses:
        status = LocalModelE2ESmokeStatus.blocked
    elif LocalModelE2ESmokeStatus.skipped in statuses:
        status = LocalModelE2ESmokeStatus.skipped
    else:
        status = LocalModelE2ESmokeStatus.passed
    return LocalModelE2ESmokeReport(
        status=status,
        step_results=steps,
        evidence_refs=[step.evidence_ref for step in steps],
        blocker_refs=[step.blocker_ref for step in steps if step.blocker_ref],
        skipped_refs=[step.skipped_ref for step in steps if step.skipped_ref],
        rollback_plan_ref=rollback_plan_ref,
        side_effect_refs=side_effect_refs,
        safe_summary=(
            "Local model E2E smoke harness produced redacted safe-ref evidence "
            f"with overall status {status.value}."
        ),
    )
