from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_runtime.activation import LocalModelRuntimeActivationPolicy
from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeStatus
from ultimate_ai_agent.core.model_runtime.health_plan import LocalRuntimeHealthProbePlan
from ultimate_ai_agent.core.model_runtime.provider_profiles import (
    LocalRuntimeProviderProfile,
    build_default_local_runtime_provider_profiles,
)


class _LocalRuntimeActivationManifestModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


M22_LOCAL_RUNTIME_DOCS = [
    "docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md",
    "docs/runtime/LOCAL_RUNTIME_PROVIDER_PROFILES.md",
    "docs/runtime/LOCAL_RUNTIME_ENDPOINT_POLICY.md",
    "docs/runtime/LOCAL_RUNTIME_HEALTH_PROBE_PLAN.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_SECURITY_MODEL.md",
    "docs/runtime/LOCAL_RUNTIME_ACTIVATION_NON_GOALS.md",
    "docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md",
]


class LocalModelRuntimeActivationManifest(_LocalRuntimeActivationManifestModel):
    manifest_ref: str = "local_model_runtime_activation_manifest_m22"
    baseline_version: str = "0.26.0"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: LocalModelRuntimeStatus = LocalModelRuntimeStatus.contract_only
    provider_profiles: list[LocalRuntimeProviderProfile] = Field(default_factory=list)
    activation_policy: LocalModelRuntimeActivationPolicy = Field(default_factory=LocalModelRuntimeActivationPolicy)
    health_probe_plan: LocalRuntimeHealthProbePlan = Field(
        default_factory=lambda: LocalRuntimeHealthProbePlan(
            plan_ref="local_runtime_health_probe_plan_m22",
            safe_summary="M22 health probe plan is metadata-only and performs no endpoint contact.",
        )
    )
    docs_refs: list[str] = Field(default_factory=lambda: list(M22_LOCAL_RUNTIME_DOCS))
    warnings: list[str] = Field(default_factory=list)
    safe_summary: str = "M22 local model runtime activation contract-only manifest."
    activation_allowed_now: bool = False
    real_model_call_allowed: bool = False
    runtime_execution_allowed: bool = False
    provider_call_allowed: bool = False
    endpoint_probe_allowed: bool = False
    user_content_allowed: bool = False
    tool_call_allowed: bool = False
    memory_write_allowed: bool = False
    secret_material_allowed: bool = False
    no_model_called: bool = True
    no_runtime_activated: bool = True
    no_endpoint_contacted: bool = True
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def build_default_local_runtime_activation_manifest(
    baseline_version: str = "0.26.0",
) -> LocalModelRuntimeActivationManifest:
    from ultimate_ai_agent.core.model_runtime.validation import validate_local_runtime_activation_manifest

    manifest = LocalModelRuntimeActivationManifest(
        baseline_version=baseline_version,
        provider_profiles=build_default_local_runtime_provider_profiles(),
        warnings=[
            "M22 is contract-only.",
            "No model was called.",
            "No runtime was activated.",
            "No endpoint was contacted.",
            "M23 remains future for any first bounded local model call.",
        ],
    )
    validate_local_runtime_activation_manifest(manifest)
    return manifest
