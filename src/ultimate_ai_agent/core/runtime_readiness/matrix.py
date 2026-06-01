from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.runtime_readiness.enums import (
    RuntimeCapabilityStatus,
    RuntimeRiskClass,
    RuntimeSurface,
)
from ultimate_ai_agent.core.time import utc_now


class RuntimeCapabilityEntry(BaseModel):
    surface: RuntimeSurface
    status: RuntimeCapabilityStatus
    risk_class: RuntimeRiskClass = RuntimeRiskClass.medium
    description: str = Field(..., min_length=1)
    allowed_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    requires_manual_operator: bool = False
    real_network_allowed: bool = False
    real_model_call_allowed: bool = False
    cloud_allowed: bool = False
    user_content_allowed: bool = False
    secrets_allowed: bool = False
    foundation_gate_covered: bool = True
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def no_runtime_expansion(self):
        if self.real_model_call_allowed:
            raise ValueError("REAL_MODEL_CALL_NOT_ALLOWED")
        if self.cloud_allowed:
            raise ValueError("CLOUD_RUNTIME_NOT_ALLOWED")
        if self.secrets_allowed:
            raise ValueError("SECRETS_NOT_ALLOWED_IN_READINESS_MATRIX")
        return self


class RuntimeCapabilityMatrix(BaseModel):
    matrix_id: str = "runtime_capability_matrix_m11"
    baseline_version: str = Field(default_factory=lambda: __version__)
    generated_at: str = "static-m11-readiness-contract"
    entries: list[RuntimeCapabilityEntry]
    summary: dict[str, bool] = Field(default_factory=dict)
    next_allowed_milestones: list[str] = Field(default_factory=list)
    blocked_milestones: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    def assert_no_runtime_expansion(self) -> bool:
        return all(
            not entry.real_model_call_allowed
            and not entry.cloud_allowed
            and not entry.secrets_allowed
            and entry.status
            in {
                RuntimeCapabilityStatus.supported.value,
                RuntimeCapabilityStatus.simulated_only.value,
                RuntimeCapabilityStatus.manual_only.value,
                RuntimeCapabilityStatus.dry_run_only.value,
                RuntimeCapabilityStatus.planned_disabled.value,
                RuntimeCapabilityStatus.blocked.value,
            }
            for entry in self.entries
        )

    def assert_foundation_gate_coverage(self) -> bool:
        return all(entry.foundation_gate_covered for entry in self.entries)


def build_matrix(baseline_version: str | None = None) -> RuntimeCapabilityMatrix:
    entries = [
        _entry(
            RuntimeSurface.simulated_model_runtime,
            RuntimeCapabilityStatus.simulated_only,
            RuntimeRiskClass.low,
            "Simulated model runtime adapter returns deterministic non-authoritative responses only.",
            ["validate simulated runtime requests", "return simulated fallback responses"],
            ["real model calls", "provider calls", "network calls"],
            ["src/ultimate_ai_agent/core/model_runtime"],
        ),
        _entry(
            RuntimeSurface.local_loopback_policy,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.medium,
            "Supported validation-only contract for local loopback endpoint policy; real smoke execution remains "
            "manual-only, approval-gated, fixed-prompt-only, and non-authoritative.",
            ["validate loopback endpoint policy"],
            [
                "non-loopback endpoints",
                "URL credentials",
                "secret query strings",
                "automated smoke execution",
                "production runtime readiness claims",
            ],
            ["src/ultimate_ai_agent/core/model_runtime/loopback.py"],
            metadata={
                "validation_only_contract": True,
                "real_smoke_execution": "manual_only",
                "approval_gated": True,
                "production_runtime_ready": False,
            },
        ),
        _entry(
            RuntimeSurface.manual_loopback_smoke,
            RuntimeCapabilityStatus.manual_only,
            RuntimeRiskClass.high,
            "Manual local loopback smoke remains CLI-only, fixed-prompt-only, approval-gated, and non-authoritative.",
            ["manual operator smoke validation", "fake transport tests"],
            ["automated smoke execution", "user prompt content", "provider calls"],
            ["src/ultimate_ai_agent/core/model_runtime/smoke.py", "scripts/local_loopback_smoke.py"],
            requires_approval=True,
            requires_manual_operator=True,
            real_network_allowed=False,
        ),
        _entry(
            RuntimeSurface.remote_worker_foundation,
            RuntimeCapabilityStatus.dry_run_only,
            RuntimeRiskClass.high,
            "Remote worker foundation supports validation/status/dry-run metadata only.",
            ["validate remote worker metadata", "build dry-run envelopes"],
            ["dispatch", "remote execution", "remote approvals", "subagent launch"],
            ["src/ultimate_ai_agent/core/remote_workers"],
        ),
        _planned_mesh(RuntimeSurface.private_mesh_planned, "Private mesh transport taxonomy is planned and disabled."),
        _planned_mesh(RuntimeSurface.tailnet_planned, "Tailnet transport metadata is planned and disabled."),
        _planned_mesh(RuntimeSurface.headscale_planned, "Headscale transport metadata is planned and disabled."),
        _planned_mesh(RuntimeSurface.generic_wireguard_planned, "Generic WireGuard transport metadata is planned and disabled."),
        _planned_mesh(RuntimeSurface.tailscale_planned, "Tailscale transport metadata is planned and disabled."),
        _entry(
            RuntimeSurface.model_router,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.medium,
            "Model router selects policy decisions only; it does not call models.",
            ["validate route decisions"],
            ["model invocation", "credential resolution"],
            ["src/ultimate_ai_agent/core/model_router"],
        ),
        _entry(
            RuntimeSurface.cost_governor,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.low,
            "Cost/resource governor evaluates budgets without billing API integration.",
            ["estimate and evaluate local budget contracts"],
            ["billing API calls"],
            ["src/ultimate_ai_agent/core/costs"],
        ),
        _entry(
            RuntimeSurface.approval_authority,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.medium,
            "Local/dev approval authority validates grants and decisions without production auth.",
            ["validate local/dev approval grants"],
            ["OAuth", "production auth", "secret resolution"],
            ["src/ultimate_ai_agent/core/approvals"],
        ),
        _entry(
            RuntimeSurface.api_boundary,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.medium,
            "Public API exposes validation, preview, status, and dry-run contracts only.",
            ["OpenAPI status and validation routes"],
            ["execute routes", "connect routes", "provider invoke routes"],
            ["src/ultimate_ai_agent/api"],
        ),
        _entry(
            RuntimeSurface.foundation_gate,
            RuntimeCapabilityStatus.supported,
            RuntimeRiskClass.low,
            "Foundation Gate verifies blocked runtime expansion and documentation integrity.",
            ["run deterministic gate criteria"],
            ["live runtime checks", "network probes"],
            ["src/ultimate_ai_agent/core/gate"],
        ),
        _entry(
            RuntimeSurface.mobile_companion_planned,
            RuntimeCapabilityStatus.planned_disabled,
            RuntimeRiskClass.high,
            "Mobile Companion remains future planning only with no sensor, OS permission, or native app code.",
            ["documentation planning"],
            ["camera", "microphone", "location", "native build"],
            ["docs/canonical/64_mobile_companion_and_device_capability_broker.md"],
        ),
        _entry(
            RuntimeSurface.device_capability_broker_planned,
            RuntimeCapabilityStatus.planned_disabled,
            RuntimeRiskClass.high,
            "Device Capability Broker remains future planning only.",
            ["documentation planning"],
            ["sensor access", "background services", "automatic memory writes"],
            ["docs/canonical/65_mobile_device_registry_and_sensor_permission_manifest.md"],
        ),
        _entry(
            RuntimeSurface.codex_plugin_governance,
            RuntimeCapabilityStatus.planned_disabled,
            RuntimeRiskClass.high,
            "Codex plugin governance is documentation and policy only; no plugin is enabled by runtime code.",
            ["document future approval boundaries"],
            ["plugin enablement", "native build tools", "computer-use automation"],
            ["docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md"],
            metadata={"documentation_only": True, "plugin_enablement_allowed": False},
        ),
        _entry(
            RuntimeSurface.cloud_provider_runtime,
            RuntimeCapabilityStatus.blocked,
            RuntimeRiskClass.forbidden,
            "Cloud/provider runtime execution is blocked for M11.",
            [],
            ["OpenAI-compatible calls", "provider SDK calls", "cloud model calls", "billing API calls"],
            ["scripts/verify_all.py", "src/ultimate_ai_agent/core/gate/evaluators.py"],
        ),
    ]
    return RuntimeCapabilityMatrix(
        baseline_version=baseline_version or __version__,
        generated_at=utc_now().replace(microsecond=0).isoformat(),
        entries=entries,
        summary={
            "production_runtime_ready": False,
            "real_model_runtime_ready": False,
            "remote_execution_ready": False,
            "mobile_sensor_ready": False,
            "plugin_or_native_build_ready": False,
            "manual_smoke_report_validation_ready": True,
        },
        next_allowed_milestones=[
            "web_control_center_contract_foundation",
            "runtime_readiness_follow_up_validation",
        ],
        blocked_milestones=[
            "cloud_provider_runtime",
            "remote_worker_execution",
            "mobile_sensor_runtime",
            "plugin_enablement",
        ],
        metadata={"source": "static_m11_contract", "truth_authority": False},
    )


def _entry(
    surface: RuntimeSurface,
    status: RuntimeCapabilityStatus,
    risk_class: RuntimeRiskClass,
    description: str,
    allowed_actions: list[str],
    blocked_actions: list[str],
    evidence_refs: list[str],
    **overrides: Any,
) -> RuntimeCapabilityEntry:
    return RuntimeCapabilityEntry(
        surface=surface,
        status=status,
        risk_class=risk_class,
        description=description,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        evidence_refs=evidence_refs,
        **overrides,
    )


def _planned_mesh(surface: RuntimeSurface, description: str) -> RuntimeCapabilityEntry:
    return _entry(
        surface,
        RuntimeCapabilityStatus.planned_disabled,
        RuntimeRiskClass.high,
        description,
        ["metadata documentation"],
        ["live mesh connection", "credential loading", "network configuration", "remote dispatch"],
        ["docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md", "docs/remote/TAILNET_TRANSPORT_POLICY.md"],
    )
