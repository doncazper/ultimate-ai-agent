from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.runtime_readiness.enums import RuntimeReadinessStatus
from ultimate_ai_agent.core.runtime_readiness.matrix import RuntimeCapabilityMatrix, build_matrix
from ultimate_ai_agent.core.time import utc_now


class RuntimeReadinessReport(BaseModel):
    report_id: str = "runtime_readiness_report_m11"
    baseline_version: str = Field(default_factory=lambda: __version__)
    generated_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    status: RuntimeReadinessStatus = RuntimeReadinessStatus.ready_for_manual_smoke
    production_ready: bool = False
    real_model_runtime_ready: bool = False
    remote_execution_ready: bool = False
    mobile_sensor_ready: bool = False
    plugin_or_native_build_ready: bool = False
    model_output_authoritative: bool = False
    manual_smoke_report_validation_ready: bool = True
    plugin_governance_status: str = "documentation_policy_only"
    capability_matrix: RuntimeCapabilityMatrix
    guardrail_summary: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def build_readiness_report(baseline_version: str | None = None) -> RuntimeReadinessReport:
    matrix = build_matrix(baseline_version=baseline_version)
    return RuntimeReadinessReport(
        baseline_version=baseline_version or __version__,
        capability_matrix=matrix,
        guardrail_summary=[
            "M11 adds readiness reports and manual smoke report validation only; no runtime execution is added.",
            "Model output remains non-authoritative and cannot be treated as evidence by this report.",
            "Remote execution, cloud/provider runtimes, mobile sensors, and plugin/native-build enablement remain blocked or planned-disabled.",
        ],
        evidence_refs=[
            "src/ultimate_ai_agent/core/runtime_readiness",
            "src/ultimate_ai_agent/core/gate/criteria.py",
            "docs/runtime/RUNTIME_READINESS.md",
        ],
    )
