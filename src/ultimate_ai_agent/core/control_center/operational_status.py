from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.inventory import (
    inspect_local_model_inventory,
)
from ultimate_ai_agent.core.local_model_management.readiness import (
    inspect_local_model_gateway,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like


SETTINGS_STATUS_ROUTE_REF = "GET /control-center/settings/status"
LOCAL_MODELS_STATUS_ROUTE_REF = "GET /control-center/local-models/status"
OPERATIONAL_MATURITY_MANIFEST_REF = (
    "docs/control_center/operational_maturity_manifest.json"
)
OPERATIONALIZATION_LADDER_REF = "docs/control_center/OPERATIONALIZATION_LADDER.md"
OPERATIONAL_MATURITY_VERIFIER_REF = "scripts/verify_operational_maturity.py"


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
    "model_switch",
    "model_start_stop",
    "provider_model_authority",
    "runtime_adapter_execution",
    "model_lifecycle_mutation",
    "production_authority",
]


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
    route_status_manifest_ref: Literal["docs/control_center/route_status_manifest.json"] = (
        "docs/control_center/route_status_manifest.json"
    )
    api_manifest_route_ref: Literal["GET /api/manifest"] = "GET /api/manifest"
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
    production_authority_enabled: bool = False
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
            or self.production_authority_enabled
        ):
            raise ValueError("CONTROL_CENTER_SETTINGS_MUTATION_DENIED")
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_SETTINGS_STATUS_SECRET_LIKE_VALUE_REJECTED")
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
    lifecycle_actions: dict[str, bool] = Field(
        default_factory=lambda: {
            "download_enabled": False,
            "switch_enabled": False,
            "start_enabled": False,
            "stop_enabled": False,
            "runtime_adapter_execution_enabled": False,
            "provider_model_authority_enabled": False,
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
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_LOCAL_MODELS_SECRET_LIKE_VALUE_REJECTED")
        return self


def build_control_center_settings_status() -> ControlCenterSettingsStatus:
    return ControlCenterSettingsStatus()


def build_control_center_local_models_status(
    env: dict[str, str] | None = None,
) -> ControlCenterLocalModelsStatus:
    values = os.environ if env is None else env
    inventory = inspect_local_model_inventory(roots=()).to_dict()
    gateway = inspect_local_model_gateway(values).model_dump(mode="json")
    return ControlCenterLocalModelsStatus(
        inventory=inventory,
        gateway_posture=gateway,
    )
