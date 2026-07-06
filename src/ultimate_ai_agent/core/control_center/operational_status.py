from __future__ import annotations

import os
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import build_authority_state_read_model
from ultimate_ai_agent.core.local_model_management.inventory import (
    inspect_local_model_inventory,
)
from ultimate_ai_agent.core.local_model_management.readiness import (
    OptionalLocalModelAdapterReadiness,
    build_optional_local_model_adapter_readiness,
    inspect_local_model_gateway,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.platform_capabilities import build_platform_capability_snapshot
from ultimate_ai_agent.core.runtime_readiness import build_matrix


SETTINGS_STATUS_ROUTE_REF = "GET /control-center/settings/status"
LOCAL_MODELS_STATUS_ROUTE_REF = "GET /control-center/local-models/status"
SETTINGS_KILL_SWITCH_CLARITY_CONTRACT_REF = (
    "contract-ref:product-loop-011-settings-kill-switch-clarity:v1"
)
OPERATIONAL_MATURITY_MANIFEST_REF = (
    "docs/control_center/operational_maturity_manifest.json"
)
OPERATIONALIZATION_LADDER_REF = "docs/control_center/OPERATIONALIZATION_LADDER.md"
OPERATIONAL_MATURITY_VERIFIER_REF = "scripts/verify_operational_maturity.py"
SETTINGS_KILL_SWITCH_CLARITY_VERIFIER_REF = (
    "scripts/verify_product_loop_011_settings_kill_switch_clarity.py"
)


SETTINGS_BLOCKED_AUTHORITIES = [
    "feature_flag_mutation",
    "kill_switch_mutation",
    "permission_mode_mutation",
    "model_identity_mutation",
    "runtime_lifecycle_mutation",
    "production_authority",
]
LOCAL_MODEL_BLOCKED_AUTHORITIES = [
    "model_download",
    "model_pull",
    "model_switch",
    "model_start_stop",
    "provider_model_authority",
    "runtime_adapter_execution",
    "model_lifecycle_mutation",
    "ollama_runtime_call",
    "mlx_lm_runtime_call",
    "openwebui_handoff_authority",
    "control_center_subprocess_execution",
    "production_authority",
]
SETTINGS_AUTHORITY_CAPABILITY_KEYS = [
    "web",
    "providers",
    "connectors",
    "memory_context_use",
    "model_runtime",
    "local_model_lifecycle",
    "platform_capabilities",
]
SETTINGS_AUTHORITY_DENIED_FLAGS = [
    "callable_runtime_authority",
    "setting_toggle_grants_authority",
    "provider_configuration_enabled",
    "connector_write_enabled",
    "context_injection_enabled",
    "model_call_enabled",
    "local_lifecycle_enabled",
    "installer_behavior_enabled",
    "production_authority_enabled",
    "authority_from_visibility",
]
SETTINGS_ALLOWED_REDACTION_MARKERS = frozenset({"raw_paths_omitted"})
SETTINGS_UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\braw[\s_-]?prompt\b"),
    re.compile(r"(?i)\braw[\s_-]?response\b"),
    re.compile(r"(?i)\braw[\s_-]?provider[\s_-]?(?:payload|exchange|content)?\b"),
    re.compile(r"(?i)\braw[\s_-]?log\b"),
    re.compile(r"(?i)\braw[\s_-]?path\b"),
    re.compile(r"(?i)\busername\b"),
    re.compile(r"(?i)\bhostname\b"),
    re.compile(r"(?i)\benv(?:ironment)?[\s_-]?dump\b"),
    re.compile(r"(?i)\bserial\b"),
    re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\|\\\\Users\\\\)"),
)


def _settings_contains_private_or_raw_content(value: Any) -> bool:
    if isinstance(value, str):
        if value in SETTINGS_ALLOWED_REDACTION_MARKERS:
            return False
        return any(pattern.search(value) for pattern in SETTINGS_UNSAFE_TEXT_PATTERNS)
    if isinstance(value, dict):
        return any(_settings_contains_private_or_raw_content(item) for item in value.values())
    if isinstance(value, list | tuple | set):
        return any(_settings_contains_private_or_raw_content(item) for item in value)
    return False


def _assert_settings_safe_payload(value: Any, error_code: str) -> None:
    if contains_secret_like(value) or _settings_contains_private_or_raw_content(value):
        raise ValueError(error_code)


class ControlCenterSettingsAuthorityPosture(BaseModel):
    capability_key: Literal[
        "web",
        "providers",
        "connectors",
        "memory_context_use",
        "model_runtime",
        "local_model_lifecycle",
        "platform_capabilities",
    ]
    label: str
    state_label: Literal["Blocked", "Degraded", "Partial", "Metadata only"]
    posture_ref: str
    source_refs: list[str]
    safe_summary: str
    blocked_authority_refs: list[str]
    next_safe_action: str
    callable_runtime_authority: bool = False
    setting_toggle_grants_authority: bool = False
    provider_configuration_enabled: bool = False
    connector_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_call_enabled: bool = False
    local_lifecycle_enabled: bool = False
    installer_behavior_enabled: bool = False
    production_authority_enabled: bool = False
    authority_from_visibility: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def no_authority_from_posture_row(self) -> "ControlCenterSettingsAuthorityPosture":
        if any(getattr(self, field_name) for field_name in SETTINGS_AUTHORITY_DENIED_FLAGS):
            raise ValueError("CONTROL_CENTER_SETTINGS_AUTHORITY_ROW_DENIED")
        _assert_settings_safe_payload(
            self.model_dump(mode="json"),
            "CONTROL_CENTER_SETTINGS_AUTHORITY_ROW_PRIVATE_OR_RAW_VALUE_REJECTED",
        )
        return self


class ControlCenterSettingsKillSwitchPosture(BaseModel):
    posture_ref: str
    label: str
    state_label: Literal["Not configured", "Blocked", "Metadata only"]
    safe_summary: str
    revocation_ref: str
    safe_disable_ref: str
    evidence_refs: list[str]
    next_safe_action: str
    execution_enabled: bool = False
    revocation_execution_enabled: bool = False
    approval_revocation_enabled: bool = False
    authority_granted: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def no_kill_switch_execution(self) -> "ControlCenterSettingsKillSwitchPosture":
        if (
            self.execution_enabled
            or self.revocation_execution_enabled
            or self.approval_revocation_enabled
            or self.authority_granted
            or self.production_authority_enabled
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_KILL_SWITCH_EXECUTION_DENIED")
        _assert_settings_safe_payload(
            self.model_dump(mode="json"),
            "CONTROL_CENTER_SETTINGS_KILL_SWITCH_PRIVATE_OR_RAW_VALUE_REJECTED",
        )
        return self


class ControlCenterSettingsFeatureFlagPosture(BaseModel):
    posture_ref: str
    label: str
    state_label: Literal["Metadata only", "Blocked", "Partial"]
    safe_summary: str
    owner_ref: str
    evidence_refs: list[str]
    next_safe_action: str
    writable: bool = False
    toggle_enabled: bool = False
    runtime_activation_enabled: bool = False
    authority_granted: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def no_feature_flag_write(self) -> "ControlCenterSettingsFeatureFlagPosture":
        if (
            self.writable
            or self.toggle_enabled
            or self.runtime_activation_enabled
            or self.authority_granted
            or self.production_authority_enabled
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_FEATURE_FLAG_WRITE_DENIED")
        _assert_settings_safe_payload(
            self.model_dump(mode="json"),
            "CONTROL_CENTER_SETTINGS_FEATURE_FLAG_PRIVATE_OR_RAW_VALUE_REJECTED",
        )
        return self


class ControlCenterSettingsStatus(BaseModel):
    schema_version: Literal["uaa-control-center-settings-status.v1"] = (
        "uaa-control-center-settings-status.v1"
    )
    module_id: Literal["settings"] = "settings"
    status: Literal["read_only_status"] = "read_only_status"
    route_ref: Literal[SETTINGS_STATUS_ROUTE_REF] = SETTINGS_STATUS_ROUTE_REF
    safe_summary: str = (
        "Settings status is backend-owned read-only posture over maturity gate, "
        "feature-flag, kill-switch, route safety, and blocked authority refs."
    )
    maturity_gate_status: Literal["active_promotion_gate"] = "active_promotion_gate"
    maturity_manifest_ref: Literal[OPERATIONAL_MATURITY_MANIFEST_REF] = (
        OPERATIONAL_MATURITY_MANIFEST_REF
    )
    ladder_doc_ref: Literal[OPERATIONALIZATION_LADDER_REF] = OPERATIONALIZATION_LADDER_REF
    verifier_ref: Literal[OPERATIONAL_MATURITY_VERIFIER_REF] = (
        OPERATIONAL_MATURITY_VERIFIER_REF
    )
    settings_authority_contract_ref: Literal[SETTINGS_KILL_SWITCH_CLARITY_CONTRACT_REF]
    settings_authority_verifier_ref: Literal[SETTINGS_KILL_SWITCH_CLARITY_VERIFIER_REF]
    route_status_manifest_ref: Literal["docs/control_center/route_status_manifest.json"] = (
        "docs/control_center/route_status_manifest.json"
    )
    api_manifest_route_ref: Literal["GET /api/manifest"] = "GET /api/manifest"
    runtime_readiness_route_ref: Literal["GET /control-center/runtime-readiness/summary"] = (
        "GET /control-center/runtime-readiness/summary"
    )
    runtime_capability_matrix_ref: str
    platform_capability_snapshot_ref: str
    platform_capability_inspection_ref: Literal["scripts/inspect_platform_capabilities.py"] = (
        "scripts/inspect_platform_capabilities.py"
    )
    review_proposals: list[str] = Field(
        default_factory=lambda: [
            "settings-proposal:feature-flag-status-route",
            "settings-proposal:kill-switch-status-route",
            "settings-proposal:reviewed-local-runtime-settings-status",
        ]
    )
    proposal_review_only: bool = True
    feature_flag_posture: Literal["read_only_metadata_only"] = (
        "read_only_metadata_only"
    )
    kill_switch_posture: Literal["not_configured_status_only"] = (
        "not_configured_status_only"
    )
    disabled_by_default: bool = True
    feature_flag_mutation_enabled: bool = False
    kill_switch_mutation_enabled: bool = False
    settings_mutation_enabled: bool = False
    callable_runtime_authority_enabled: bool = False
    provider_configuration_enabled: bool = False
    installer_behavior_enabled: bool = False
    settings_toggle_grants_authority: bool = False
    catalog_visibility_grants_authority: bool = False
    production_authority_enabled: bool = False
    authority_postures: list[ControlCenterSettingsAuthorityPosture]
    kill_switch_postures: list[ControlCenterSettingsKillSwitchPosture]
    feature_flag_postures: list[ControlCenterSettingsFeatureFlagPosture]
    authority_lease_state: dict[str, Any]
    blocked_authorities: list[str] = Field(
        default_factory=lambda: list(SETTINGS_BLOCKED_AUTHORITIES)
    )
    missing_contracts: list[str] = Field(
        default_factory=lambda: [
            "feature_flag_mutation_contract",
            "kill_switch_execution_contract",
            "reviewed_local_runtime_settings_mutation_contract",
        ]
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "safe_refs_only",
            "raw_paths_omitted",
            "credentials_omitted",
            "no_runtime_values",
        ]
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def read_only_only(self) -> "ControlCenterSettingsStatus":
        if (
            self.feature_flag_mutation_enabled
            or self.kill_switch_mutation_enabled
            or self.settings_mutation_enabled
            or self.callable_runtime_authority_enabled
            or self.provider_configuration_enabled
            or self.installer_behavior_enabled
            or self.settings_toggle_grants_authority
            or self.catalog_visibility_grants_authority
            or self.production_authority_enabled
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_MUTATION_DENIED")
        posture_keys = [posture.capability_key for posture in self.authority_postures]
        if posture_keys != SETTINGS_AUTHORITY_CAPABILITY_KEYS:
            raise ValueError("CONTROL_CENTER_SETTINGS_AUTHORITY_POSTURE_KEYS_REQUIRED")
        if any(
            posture.callable_runtime_authority
            or posture.setting_toggle_grants_authority
            or posture.authority_from_visibility
            for posture in self.authority_postures
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_AUTHORITY_POSTURE_DENIED")
        if any(
            posture.execution_enabled
            or posture.revocation_execution_enabled
            or posture.authority_granted
            for posture in self.kill_switch_postures
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_KILL_SWITCH_AUTHORITY_DENIED")
        if any(
            posture.writable
            or posture.toggle_enabled
            or posture.runtime_activation_enabled
            or posture.authority_granted
            for posture in self.feature_flag_postures
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_FEATURE_FLAG_AUTHORITY_DENIED")
        _assert_settings_safe_payload(
            self.model_dump(mode="json"),
            "CONTROL_CENTER_SETTINGS_STATUS_PRIVATE_OR_RAW_VALUE_REJECTED",
        )
        return self


class ControlCenterLocalModelsStatus(BaseModel):
    schema_version: Literal["uaa-control-center-local-models-status.v1"] = (
        "uaa-control-center-local-models-status.v1"
    )
    module_id: Literal["local_models"] = "local_models"
    status: Literal["read_only_status"] = "read_only_status"
    route_ref: Literal[LOCAL_MODELS_STATUS_ROUTE_REF] = LOCAL_MODELS_STATUS_ROUTE_REF
    safe_summary: str = (
        "Local Models status is backend-owned read-only metadata over inventory "
        "and gateway posture; lifecycle and provider/model authority remain blocked."
    )
    review_proposals: list[str] = Field(
        default_factory=lambda: [
            "local-models-proposal:read-only-inventory-table",
            "local-models-proposal:lifecycle-status-route",
            "local-models-proposal:dry-run-switch-planner-contract",
        ]
    )
    proposal_review_only: bool = True
    inventory: dict[str, Any]
    gateway_posture: dict[str, Any]
    adapter_readiness: list[OptionalLocalModelAdapterReadiness] = Field(
        default_factory=lambda: list(build_optional_local_model_adapter_readiness())
    )
    lifecycle_actions: dict[str, bool] = Field(
        default_factory=lambda: {
            "download_enabled": False,
            "model_pull_enabled": False,
            "switch_enabled": False,
            "start_enabled": False,
            "stop_enabled": False,
            "runtime_adapter_execution_enabled": False,
            "provider_model_authority_enabled": False,
            "openwebui_handoff_enabled": False,
            "control_center_subprocess_execution_enabled": False,
        }
    )
    blocked_authorities: list[str] = Field(
        default_factory=lambda: list(LOCAL_MODEL_BLOCKED_AUTHORITIES)
    )
    evidence_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md",
            "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md",
        ]
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "safe_refs_only",
            "raw_paths_omitted",
            "credentials_omitted",
            "no_model_calls",
        ]
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def lifecycle_remains_blocked(self) -> "ControlCenterLocalModelsStatus":
        if any(self.lifecycle_actions.values()):
            raise ValueError("CONTROL_CENTER_LOCAL_MODELS_LIFECYCLE_DENIED")
        adapter_ids = [item.adapter_id for item in self.adapter_readiness]
        if set(adapter_ids) != {"ollama", "mlx_lm"} or len(adapter_ids) != 2:
            raise ValueError("CONTROL_CENTER_LOCAL_MODELS_OPTIONAL_ADAPTERS_MISSING")
        for item in self.adapter_readiness:
            if (
                item.runtime_calls_enabled
                or item.model_pulls_enabled
                or item.model_downloads_enabled
                or item.lifecycle_start_stop_switch_enabled
                or item.provider_model_authority_enabled
                or item.control_center_subprocess_execution_enabled
            ):
                raise ValueError("CONTROL_CENTER_LOCAL_MODELS_ADAPTER_AUTHORITY_DENIED")
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_LOCAL_MODELS_SECRET_LIKE_VALUE_REJECTED")
        return self


def build_control_center_settings_status() -> ControlCenterSettingsStatus:
    runtime_matrix = build_matrix()
    platform_snapshot = build_platform_capability_snapshot()
    return ControlCenterSettingsStatus(
        settings_authority_contract_ref=SETTINGS_KILL_SWITCH_CLARITY_CONTRACT_REF,
        settings_authority_verifier_ref=SETTINGS_KILL_SWITCH_CLARITY_VERIFIER_REF,
        runtime_capability_matrix_ref=runtime_matrix.matrix_id,
        platform_capability_snapshot_ref=platform_snapshot.snapshot_ref,
        authority_postures=_settings_authority_postures(platform_snapshot.snapshot_ref),
        kill_switch_postures=_settings_kill_switch_postures(),
        feature_flag_postures=_settings_feature_flag_postures(),
        authority_lease_state=build_authority_state_read_model().model_dump(mode="json"),
    )


def _settings_authority_postures(
    platform_snapshot_ref: str,
) -> list[ControlCenterSettingsAuthorityPosture]:
    return [
        ControlCenterSettingsAuthorityPosture(
            capability_key="web",
            label="Web",
            state_label="Blocked",
            posture_ref="settings-authority:web",
            source_refs=[
                "GET /api/manifest",
                "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
            ],
            safe_summary=(
                "Public web visibility is metadata only; unrestricted fetching and browser execution remain blocked."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-live-web",
                "blocked-state:settings-no-browser-execution",
            ],
            next_safe_action="Inspect WebAccessGateway posture before scoping any web runtime.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="providers",
            label="Providers",
            state_label="Blocked",
            posture_ref="settings-authority:providers",
            source_refs=[
                "GET /api/manifest",
                "provider-readiness:reference-only",
            ],
            safe_summary=(
                "Provider diagnostics and provider safe refs are visible only as readiness metadata."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-provider-sdk-call",
                "blocked-state:settings-no-provider-configuration",
            ],
            next_safe_action="Review provider refs without collecting credentials or invoking providers.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="connectors",
            label="Connectors",
            state_label="Blocked",
            posture_ref="settings-authority:connectors",
            source_refs=[
                "GET /control-center/sources/readiness",
                "docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md",
            ],
            safe_summary="Connector runtime and connector writes are not enabled from Settings.",
            blocked_authority_refs=[
                "blocked-state:settings-no-connector-runtime",
                "blocked-state:settings-no-connector-write",
            ],
            next_safe_action="Use source readiness refs before any connector milestone is scoped.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="memory_context_use",
            label="Memory context use",
            state_label="Partial",
            posture_ref="settings-authority:memory-context-use",
            source_refs=[
                "GET /control-center/memory/context-packs",
                "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
            ],
            safe_summary=(
                "Memory context packs are reviewable proposals only; hidden injection and truth authority remain blocked."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-hidden-context-injection",
                "blocked-state:settings-memory-recall-not-truth",
            ],
            next_safe_action="Review memory proposals as recall only before any context-use milestone.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="model_runtime",
            label="Model runtime",
            state_label="Degraded",
            posture_ref="settings-authority:model-runtime",
            source_refs=[
                "GET /control-center/runtime-readiness/summary",
                "runtime-capability-matrix:m11",
            ],
            safe_summary=(
                "Model runtime posture is readiness-only; runtime model calls and provider calls are blocked here."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-runtime-model-call",
                "blocked-state:settings-no-provider-model-call",
            ],
            next_safe_action="Inspect runtime readiness and local model status before lifecycle work.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="local_model_lifecycle",
            label="Local model lifecycle",
            state_label="Blocked",
            posture_ref="settings-authority:local-model-lifecycle",
            source_refs=[
                "GET /control-center/local-models/status",
                "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md",
            ],
            safe_summary=(
                "Local model inventory is readable, but download switch start stop and calls remain blocked."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-model-download",
                "blocked-state:settings-no-model-start-stop",
            ],
            next_safe_action="Inspect local model status without starting or switching models.",
        ),
        ControlCenterSettingsAuthorityPosture(
            capability_key="platform_capabilities",
            label="Platform capabilities",
            state_label="Metadata only",
            posture_ref="settings-authority:platform-capabilities",
            source_refs=[
                platform_snapshot_ref,
                "scripts/inspect_platform_capabilities.py",
            ],
            safe_summary=(
                "Platform capabilities are safe bucketed metadata and do not grant install service credential or OS data authority."
            ),
            blocked_authority_refs=[
                "blocked-state:settings-no-installer-behavior",
                "blocked-state:settings-no-platform-permission-grant",
            ],
            next_safe_action="Inspect platform capability metadata before any OS adapter milestone.",
        ),
    ]


def _settings_kill_switch_postures() -> list[ControlCenterSettingsKillSwitchPosture]:
    return [
        ControlCenterSettingsKillSwitchPosture(
            posture_ref="settings-kill-switch:global-runtime-authority",
            label="Global runtime authority",
            state_label="Not configured",
            safe_summary=(
                "Settings can show kill-switch posture only; no kill switch or revocation execution is available."
            ),
            revocation_ref="revocation-ref:settings:global-runtime-authority-review-only",
            safe_disable_ref="safe-disable-ref:settings:global-runtime-authority-review-only",
            evidence_refs=[
                "docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md",
                "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
            ],
            next_safe_action="Define an exact scoped kill-switch milestone before execution exists.",
        )
    ]


def _settings_feature_flag_postures() -> list[ControlCenterSettingsFeatureFlagPosture]:
    return [
        ControlCenterSettingsFeatureFlagPosture(
            posture_ref="settings-feature-flag:authority-visibility",
            label="Authority visibility",
            state_label="Metadata only",
            safe_summary=(
                "Settings feature-flag labels are readable posture only and cannot enable runtime behavior."
            ),
            owner_ref="owner-ref:python-agent-core-settings-status",
            evidence_refs=[
                "GET /control-center/settings/status",
                "docs/control_center/SETTINGS_KILL_SWITCH_FEATURE_FLAGS_SPEC.md",
            ],
            next_safe_action="Keep flags read-only until a scoped mutation contract exists.",
        )
    ]


def build_control_center_local_models_status(
    env: dict[str, str] | None = None,
) -> ControlCenterLocalModelsStatus:
    values = os.environ if env is None else env
    inventory = inspect_local_model_inventory(roots=()).to_dict()
    gateway = inspect_local_model_gateway(values).model_dump(mode="json")
    return ControlCenterLocalModelsStatus(
        inventory=inventory,
        gateway_posture=gateway,
        adapter_readiness=list(build_optional_local_model_adapter_readiness()),
    )
