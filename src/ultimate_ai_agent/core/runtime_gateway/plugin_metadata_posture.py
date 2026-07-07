from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_PLUGIN_METADATA_POSTURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-plugin-metadata-posture:v1"
)
RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF = (
    "GET /api/runtime/plugin-metadata-posture"
)
RUNTIME_PLUGIN_METADATA_POSTURE_CLI_REF = "uaa runtime inspect-plugin-metadata-posture"
RUNTIME_PLUGIN_METADATA_POSTURE_DOC_REF = (
    "docs/runtime/UAA_HERMES_RUNTIME_PLUGIN_METADATA_POSTURE.md"
)
RUNTIME_PLUGIN_METADATA_POSTURE_SNAPSHOT_REF = (
    "plugin-metadata-posture-snapshot-ref:runtime:phase-44"
)
RUNTIME_PLUGIN_METADATA_POSTURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-44:plugin-metadata-posture"
)
RUNTIME_PLUGIN_METADATA_POSTURE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-44:plugin-metadata-posture"
)
RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-plugin-metadata-posture-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:plugin-metadata-no-runtime-import",
    "blocked-authority:plugin-metadata-no-hook-execution",
    "blocked-authority:plugin-metadata-no-package-install",
    "blocked-authority:plugin-metadata-no-marketplace-content-execution",
    "blocked-authority:plugin-metadata-no-plugin-code-execution",
    "blocked-authority:plugin-metadata-no-connector-write",
    "blocked-authority:plugin-metadata-no-provider-call",
    "blocked-authority:plugin-metadata-no-shell-execution",
    "blocked-authority:plugin-metadata-no-raw-manifest-persistence",
    "blocked-authority:plugin-metadata-no-control-center-authority-mint",
)


class RuntimePluginSurfaceKind(str, Enum):
    adapter = "adapter"
    hook = "hook"
    tool = "tool"
    memory_provider = "memory_provider"
    context_engine = "context_engine"
    ui_extension = "ui_extension"
    skill_bundle = "skill_bundle"


class RuntimePluginSurfaceStatus(str, Enum):
    metadata_contract_only = "metadata_contract_only"
    blocked_until_grant = "blocked_until_grant"


class RuntimePluginMetadataSurface(BaseModel):
    surface_ref: str
    surface_kind: RuntimePluginSurfaceKind
    display_label: str
    status: RuntimePluginSurfaceStatus
    safe_summary: str
    reviewed_manifest_ref: str
    static_scan_ref: str
    sandbox_ref: str
    activation_grant_ref: str
    rollback_ref: str
    safe_disable_ref: str
    receipt_plan_ref: str
    proof_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    runtime_import_enabled: bool = False
    hook_execution_enabled: bool = False
    package_install_enabled: bool = False
    marketplace_content_execution_enabled: bool = False
    plugin_code_execution_enabled: bool = False
    connector_write_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    raw_manifest_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_surface(self) -> "RuntimePluginMetadataSurface":
        for value, field_name in [
            (self.surface_ref, "surface_ref"),
            (self.reviewed_manifest_ref, "reviewed_manifest_ref"),
            (self.static_scan_ref, "static_scan_ref"),
            (self.sandbox_ref, "sandbox_ref"),
            (self.activation_grant_ref, "activation_grant_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
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
            (str(self.surface_kind), "surface_kind"),
            (self.display_label, "display_label"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "runtime_import_enabled": self.runtime_import_enabled,
            "hook_execution_enabled": self.hook_execution_enabled,
            "package_install_enabled": self.package_install_enabled,
            "marketplace_content_execution_enabled": (
                self.marketplace_content_execution_enabled
            ),
            "plugin_code_execution_enabled": self.plugin_code_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "raw_manifest_persisted": self.raw_manifest_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PLUGIN_METADATA_SURFACE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_PLUGIN_METADATA_SURFACE_BLOCKERS_REQUIRED")
        return self


class RuntimePluginMetadataPostureReadModel(BaseModel):
    schema_version: str = "runtime_plugin_metadata_posture.v1"
    contract_ref: str = RUNTIME_PLUGIN_METADATA_POSTURE_CONTRACT_REF
    status: str = "metadata_contract_only"
    snapshot_ref: str = RUNTIME_PLUGIN_METADATA_POSTURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:plugin-metadata-posture:pending"
    route_ref: str = RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF
    cli_ref: str = RUNTIME_PLUGIN_METADATA_POSTURE_CLI_REF
    doc_ref: str = RUNTIME_PLUGIN_METADATA_POSTURE_DOC_REF
    authority_state_route_ref: str = (
        RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = (
        RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_STATE_CLI_REF
    )
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Plugin architecture surfaces are represented as metadata contracts only; "
        "runtime import, hooks, package install, marketplace execution, and plugin "
        "code execution remain blocked."
    )
    surfaces: list[RuntimePluginMetadataSurface] = Field(default_factory=list)
    surface_count: int = 0
    blocked_surface_count: int = 0
    runtime_import_enabled: bool = False
    hook_execution_enabled: bool = False
    package_install_enabled: bool = False
    marketplace_content_execution_enabled: bool = False
    plugin_code_execution_enabled: bool = False
    connector_write_enabled: bool = False
    provider_call_enabled: bool = False
    shell_execution_enabled: bool = False
    raw_manifest_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_manifests_omitted",
            "package_payloads_omitted",
            "external_code_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimePluginMetadataPostureReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.doc_ref, "doc_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
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
        if (
            self.authority_state_mapping_ref
            != RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_PLUGIN_METADATA_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_PLUGIN_METADATA_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "runtime_import_enabled": self.runtime_import_enabled,
            "hook_execution_enabled": self.hook_execution_enabled,
            "package_install_enabled": self.package_install_enabled,
            "marketplace_content_execution_enabled": (
                self.marketplace_content_execution_enabled
            ),
            "plugin_code_execution_enabled": self.plugin_code_execution_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "raw_manifest_persisted": self.raw_manifest_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PLUGIN_METADATA_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_PLUGIN_METADATA_BLOCKERS_REQUIRED")
        if self.surface_count != len(self.surfaces):
            raise ValueError("RUNTIME_PLUGIN_METADATA_COUNT_MISMATCH")
        if self.blocked_surface_count != len(
            [
                surface
                for surface in self.surfaces
                if surface.status == RuntimePluginSurfaceStatus.blocked_until_grant
            ]
        ):
            raise ValueError("RUNTIME_PLUGIN_METADATA_BLOCKED_COUNT_MISMATCH")
        return self


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _surface(
    surface_kind: RuntimePluginSurfaceKind,
    display_label: str,
    summary: str,
) -> RuntimePluginMetadataSurface:
    token = surface_kind.value.replace("_", "-")
    return RuntimePluginMetadataSurface(
        surface_ref=f"plugin-surface-ref:runtime:{token}",
        surface_kind=surface_kind,
        display_label=display_label,
        status=RuntimePluginSurfaceStatus.blocked_until_grant,
        safe_summary=summary,
        reviewed_manifest_ref=f"reviewed-manifest-ref:plugin:{token}",
        static_scan_ref=f"static-scan-ref:plugin:{token}",
        sandbox_ref=f"sandbox-ref:plugin:{token}",
        activation_grant_ref=f"activation-grant-ref:plugin:{token}",
        rollback_ref=f"rollback-ref:plugin:{token}",
        safe_disable_ref=f"safe-disable-ref:plugin:{token}",
        receipt_plan_ref=f"receipt-plan-ref:plugin:{token}",
        proof_ref=f"proof-ref:plugin-metadata:{token}",
        blocked_authority_refs=list(RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:plugin:{token}:reviewed-manifest",
            f"promotion-path-ref:plugin:{token}:static-scan",
            f"promotion-path-ref:plugin:{token}:sandbox-grant",
            f"promotion-path-ref:plugin:{token}:rollback-receipt",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:plugin:{token}:metadata-contract"
        ],
    )


def build_runtime_plugin_metadata_posture_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> (
    RuntimePluginMetadataPostureReadModel
):
    authority_entry = _authority_entry(authority_decision_catalog)
    surfaces = [
        _surface(
            RuntimePluginSurfaceKind.adapter,
            "Adapters",
            "Adapter metadata is inspectable, but adapter import and execution remain blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.hook,
            "Hooks",
            "Hook metadata is inspectable, but lifecycle hook execution remains blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.tool,
            "Tools",
            "Tool metadata is inspectable, but tool execution and connector writes remain blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.memory_provider,
            "Memory providers",
            "Memory provider metadata is inspectable, but external memory provider runtime remains blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.context_engine,
            "Context engines",
            "Context engine metadata is inspectable, but hidden context injection remains blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.ui_extension,
            "UI extensions",
            "UI extension metadata is inspectable, but executable extension runtime remains blocked.",
        ),
        _surface(
            RuntimePluginSurfaceKind.skill_bundle,
            "Skill bundles",
            "Skill bundle metadata is inspectable, but skill runtime import and marketplace execution remain blocked.",
        ),
    ]
    payload = {
        "route_ref": RUNTIME_PLUGIN_METADATA_POSTURE_ROUTE_REF,
        "authority_state_mapping_ref": authority_entry.lane_ref,
        "authority_state_catalog_ref": authority_entry.catalog_ref,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "authority_state_status": authority_entry.status,
        "authority_state_operator_message": authority_entry.decision.operator_message,
        "authority_state_reason_refs": list(authority_entry.decision.reason_refs),
        "unsupported_adapter_refs": list(authority_entry.unsupported_adapter_refs),
        "surfaces": surfaces,
        "surface_count": len(surfaces),
        "blocked_surface_count": len(surfaces),
        "blocked_authority_refs": list(RUNTIME_PLUGIN_METADATA_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:plugin-metadata:reviewed-manifest",
            "promotion-path-ref:plugin-metadata:static-scan",
            "promotion-path-ref:plugin-metadata:sandbox-grant",
            "promotion-path-ref:plugin-metadata:rollback-safe-disable",
            "promotion-path-ref:plugin-metadata:receipts-proof",
        ],
        "proof_refs": [RUNTIME_PLUGIN_METADATA_POSTURE_PROOF_REF],
        "verifier_refs": [RUNTIME_PLUGIN_METADATA_POSTURE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:plugin-metadata:manifest-schema",
            "next-safe-action-ref:plugin-metadata:activation-grant-contract",
        ],
    }
    snapshot_material = {
        "contract_ref": RUNTIME_PLUGIN_METADATA_POSTURE_CONTRACT_REF,
        "route_ref": payload["route_ref"],
        "cli_ref": RUNTIME_PLUGIN_METADATA_POSTURE_CLI_REF,
        "surface_refs": [surface.surface_ref for surface in surfaces],
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:plugin-metadata-posture:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimePluginMetadataPostureReadModel(**payload)


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_PLUGIN_METADATA_POSTURE_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_PLUGIN_METADATA_AUTHORITY_MAPPING_MISSING")
