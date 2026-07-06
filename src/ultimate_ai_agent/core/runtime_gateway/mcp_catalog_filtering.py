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


RUNTIME_MCP_CATALOG_FILTERING_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-mcp-catalog-filtering:v1"
)
RUNTIME_MCP_CATALOG_FILTERING_ROUTE_REF = "GET /api/runtime/mcp-catalog-filtering"
RUNTIME_MCP_CATALOG_FILTERING_CLI_REF = "uaa runtime inspect-mcp-catalog-filtering"
RUNTIME_MCP_CATALOG_FILTERING_SNAPSHOT_REF = (
    "mcp-catalog-snapshot-ref:runtime:filtered-metadata"
)
RUNTIME_MCP_CATALOG_FILTERING_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-30:mcp-catalog-filtering"
)
RUNTIME_MCP_CATALOG_FILTERING_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-30:mcp-catalog-filtering"
)

RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:mcp-catalog-no-server-install",
    "blocked-authority:mcp-catalog-no-subprocess-runtime",
    "blocked-authority:mcp-catalog-no-oauth-login",
    "blocked-authority:mcp-catalog-no-tool-invocation",
    "blocked-authority:mcp-catalog-no-connector-write",
    "blocked-authority:mcp-catalog-no-raw-manifest-persistence",
    "blocked-authority:mcp-catalog-no-control-center-authority-mint",
)


class RuntimeMcpServerCatalogState(str, Enum):
    reviewed_metadata = "reviewed_metadata"
    review_required = "review_required"
    activation_blocked = "activation_blocked"


class RuntimeMcpToolFilterState(str, Enum):
    metadata_visible = "metadata_visible"
    filtered_blocked = "filtered_blocked"
    grant_required = "grant_required"


class RuntimeMcpToolSlice(BaseModel):
    tool_ref: str
    display_label: str
    filter_state: RuntimeMcpToolFilterState
    risk_label: str
    safe_summary: str
    filter_reason_refs: list[str] = Field(default_factory=list)
    grant_requirement_refs: list[str] = Field(default_factory=list)
    receipt_requirement_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    metadata_visible: bool = True
    invocation_enabled: bool = False
    connector_write_enabled: bool = False
    raw_schema_persisted: bool = False
    runtime_dispatch_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_tool_slice(self) -> "RuntimeMcpToolSlice":
        validate_execution_ref(self.tool_ref, "tool_ref")
        for field_name in (
            "filter_reason_refs",
            "grant_requirement_refs",
            "receipt_requirement_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.filter_state), "filter_state"),
            (self.risk_label, "risk_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "invocation_enabled": self.invocation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_schema_persisted": self.raw_schema_persisted,
            "runtime_dispatch_enabled": self.runtime_dispatch_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError("RUNTIME_MCP_TOOL_AUTHORITY_DENIED: " + ", ".join(enabled))
        if not self.metadata_visible:
            raise ValueError("RUNTIME_MCP_TOOL_METADATA_VISIBILITY_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_MCP_TOOL_BLOCKERS_REQUIRED")
        return self


class RuntimeMcpServerCatalogEntry(BaseModel):
    server_ref: str
    display_label: str
    catalog_state: RuntimeMcpServerCatalogState
    manifest_ref: str
    filter_contract_ref: str
    safe_summary: str
    tool_slices: list[RuntimeMcpToolSlice] = Field(default_factory=list)
    tool_count: int = 0
    metadata_visible_tool_count: int = 0
    filtered_blocked_tool_count: int = 0
    grant_required_tool_count: int = 0
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    install_enabled: bool = False
    subprocess_runtime_enabled: bool = False
    oauth_login_enabled: bool = False
    tool_invocation_enabled: bool = False
    connector_write_enabled: bool = False
    raw_manifest_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_server(self) -> "RuntimeMcpServerCatalogEntry":
        for value, field_name in [
            (self.server_ref, "server_ref"),
            (self.manifest_ref, "manifest_ref"),
            (self.filter_contract_ref, "filter_contract_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.catalog_state), "catalog_state"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.tool_count != len(self.tool_slices):
            raise ValueError("RUNTIME_MCP_TOOL_COUNT_DRIFT")
        state_counts = {
            RuntimeMcpToolFilterState.metadata_visible.value: (
                self.metadata_visible_tool_count
            ),
            RuntimeMcpToolFilterState.filtered_blocked.value: (
                self.filtered_blocked_tool_count
            ),
            RuntimeMcpToolFilterState.grant_required.value: (
                self.grant_required_tool_count
            ),
        }
        for state, expected in state_counts.items():
            actual = sum(1 for tool in self.tool_slices if tool.filter_state == state)
            if actual != expected:
                raise ValueError("RUNTIME_MCP_TOOL_FILTER_COUNT_DRIFT")
        denied_flags = {
            "install_enabled": self.install_enabled,
            "subprocess_runtime_enabled": self.subprocess_runtime_enabled,
            "oauth_login_enabled": self.oauth_login_enabled,
            "tool_invocation_enabled": self.tool_invocation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_manifest_persisted": self.raw_manifest_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError("RUNTIME_MCP_SERVER_AUTHORITY_DENIED: " + ", ".join(enabled))
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_MCP_SERVER_BLOCKERS_REQUIRED")
        if not self.proof_refs:
            raise ValueError("RUNTIME_MCP_SERVER_PROOF_REQUIRED")
        return self


class RuntimeMcpCatalogFilteringReadModel(BaseModel):
    schema_version: str = "runtime_mcp_catalog_filtering.v1"
    contract_ref: str = RUNTIME_MCP_CATALOG_FILTERING_CONTRACT_REF
    status: str = "metadata_catalog_filtering_posture"
    snapshot_ref: str = RUNTIME_MCP_CATALOG_FILTERING_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-mcp-catalog:pending"
    route_ref: str = RUNTIME_MCP_CATALOG_FILTERING_ROUTE_REF
    cli_ref: str = RUNTIME_MCP_CATALOG_FILTERING_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "MCP catalog filtering exposes reviewed server metadata and blocked "
        "tool-slice activation posture only."
    )
    servers: list[RuntimeMcpServerCatalogEntry] = Field(default_factory=list)
    server_count: int = 0
    reviewed_metadata_count: int = 0
    review_required_count: int = 0
    activation_blocked_count: int = 0
    tool_slice_count: int = 0
    metadata_visible_tool_count: int = 0
    filtered_blocked_tool_count: int = 0
    grant_required_tool_count: int = 0
    metadata_catalog_visible: bool = True
    tool_filter_contracts_visible: bool = True
    blocked_activation_states_visible: bool = True
    install_enabled: bool = False
    subprocess_runtime_enabled: bool = False
    oauth_login_enabled: bool = False
    tool_invocation_enabled: bool = False
    connector_write_enabled: bool = False
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
            "raw_mcp_manifests_omitted",
            "raw_tool_schemas_omitted",
            "oauth_material_omitted",
            "connector_payloads_omitted",
        ]
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeMcpCatalogFilteringReadModel":
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
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if self.server_count != len(self.servers):
            raise ValueError("RUNTIME_MCP_SERVER_COUNT_DRIFT")
        server_states = {
            RuntimeMcpServerCatalogState.reviewed_metadata.value: (
                self.reviewed_metadata_count
            ),
            RuntimeMcpServerCatalogState.review_required.value: self.review_required_count,
            RuntimeMcpServerCatalogState.activation_blocked.value: (
                self.activation_blocked_count
            ),
        }
        for state, expected in server_states.items():
            actual = sum(1 for server in self.servers if server.catalog_state == state)
            if actual != expected:
                raise ValueError("RUNTIME_MCP_SERVER_STATE_COUNT_DRIFT")
        if self.tool_slice_count != sum(server.tool_count for server in self.servers):
            raise ValueError("RUNTIME_MCP_TOTAL_TOOL_COUNT_DRIFT")
        expected_tool_counts = {
            "metadata_visible_tool_count": sum(
                server.metadata_visible_tool_count for server in self.servers
            ),
            "filtered_blocked_tool_count": sum(
                server.filtered_blocked_tool_count for server in self.servers
            ),
            "grant_required_tool_count": sum(
                server.grant_required_tool_count for server in self.servers
            ),
        }
        for field_name, expected in expected_tool_counts.items():
            if getattr(self, field_name) != expected:
                raise ValueError("RUNTIME_MCP_TOTAL_FILTER_COUNT_DRIFT")
        visibility_flags = {
            "metadata_catalog_visible": self.metadata_catalog_visible,
            "tool_filter_contracts_visible": self.tool_filter_contracts_visible,
            "blocked_activation_states_visible": self.blocked_activation_states_visible,
        }
        missing = [name for name, value in visibility_flags.items() if not value]
        if missing:
            raise ValueError("RUNTIME_MCP_VISIBILITY_REQUIRED: " + ", ".join(missing))
        denied_flags = {
            "install_enabled": self.install_enabled,
            "subprocess_runtime_enabled": self.subprocess_runtime_enabled,
            "oauth_login_enabled": self.oauth_login_enabled,
            "tool_invocation_enabled": self.tool_invocation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "raw_manifest_persisted": self.raw_manifest_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError("RUNTIME_MCP_CATALOG_AUTHORITY_DENIED: " + ", ".join(enabled))
        for ref in RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_MCP_CATALOG_BLOCKER_MISSING")
        if RUNTIME_MCP_CATALOG_FILTERING_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_MCP_CATALOG_PROOF_REF_REQUIRED")
        if RUNTIME_MCP_CATALOG_FILTERING_VERIFIER_REF not in self.verifier_refs:
            raise ValueError("RUNTIME_MCP_CATALOG_VERIFIER_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-mcp-catalog:{digest}"


def _tool_slice(
    slug: str,
    *,
    display_label: str,
    filter_state: RuntimeMcpToolFilterState,
    risk_label: str,
    safe_summary: str,
) -> RuntimeMcpToolSlice:
    return RuntimeMcpToolSlice(
        tool_ref=f"mcp-tool-slice-ref:{slug}",
        display_label=display_label,
        filter_state=filter_state,
        risk_label=risk_label,
        safe_summary=safe_summary,
        filter_reason_refs=[f"mcp-filter-reason-ref:{slug}"],
        grant_requirement_refs=[f"mcp-grant-requirement-ref:{slug}"],
        receipt_requirement_refs=[f"mcp-receipt-requirement-ref:{slug}"],
        blocked_authority_refs=list(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS),
    )


def _server(
    slug: str,
    *,
    display_label: str,
    catalog_state: RuntimeMcpServerCatalogState,
    safe_summary: str,
    tool_slices: list[RuntimeMcpToolSlice],
) -> RuntimeMcpServerCatalogEntry:
    return RuntimeMcpServerCatalogEntry(
        server_ref=f"mcp-server-ref:{slug}",
        display_label=display_label,
        catalog_state=catalog_state,
        manifest_ref=f"mcp-manifest-ref:{slug}:redacted",
        filter_contract_ref=f"mcp-filter-contract-ref:{slug}:reviewed-slices",
        safe_summary=safe_summary,
        tool_slices=tool_slices,
        tool_count=len(tool_slices),
        metadata_visible_tool_count=sum(
            1
            for tool in tool_slices
            if tool.filter_state == RuntimeMcpToolFilterState.metadata_visible.value
        ),
        filtered_blocked_tool_count=sum(
            1
            for tool in tool_slices
            if tool.filter_state == RuntimeMcpToolFilterState.filtered_blocked.value
        ),
        grant_required_tool_count=sum(
            1
            for tool in tool_slices
            if tool.filter_state == RuntimeMcpToolFilterState.grant_required.value
        ),
        proof_refs=[RUNTIME_MCP_CATALOG_FILTERING_PROOF_REF],
        blocked_authority_refs=list(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS),
        next_safe_action_refs=[f"next-safe-action-ref:mcp-catalog:{slug}:review-filter"],
    )


def build_runtime_mcp_catalog_filtering_read_model() -> RuntimeMcpCatalogFilteringReadModel:
    servers = [
        _server(
            "filesystem-metadata",
            display_label="Filesystem metadata server",
            catalog_state=RuntimeMcpServerCatalogState.reviewed_metadata,
            safe_summary=(
                "Metadata-only server record for future file metadata tools; "
                "subprocess runtime remains blocked."
            ),
            tool_slices=[
                _tool_slice(
                    "filesystem-list-metadata",
                    display_label="List file metadata",
                    filter_state=RuntimeMcpToolFilterState.metadata_visible,
                    risk_label="read_metadata_only",
                    safe_summary="Tool metadata is visible; invocation is blocked.",
                ),
                _tool_slice(
                    "filesystem-write-file",
                    display_label="Write file",
                    filter_state=RuntimeMcpToolFilterState.filtered_blocked,
                    risk_label="file_mutation_blocked",
                    safe_summary="File mutation tool slice is filtered out.",
                ),
            ],
        ),
        _server(
            "browser-research",
            display_label="Browser research server",
            catalog_state=RuntimeMcpServerCatalogState.activation_blocked,
            safe_summary=(
                "Browser research server is catalog metadata only; browser "
                "runtime and web fetching remain blocked."
            ),
            tool_slices=[
                _tool_slice(
                    "browser-fetch-page",
                    display_label="Fetch page",
                    filter_state=RuntimeMcpToolFilterState.filtered_blocked,
                    risk_label="web_fetch_blocked",
                    safe_summary="Web fetch tool slice is blocked.",
                ),
                _tool_slice(
                    "browser-click",
                    display_label="Browser click",
                    filter_state=RuntimeMcpToolFilterState.filtered_blocked,
                    risk_label="browser_action_blocked",
                    safe_summary="Browser action tool slice is blocked.",
                ),
            ],
        ),
        _server(
            "crm-draft",
            display_label="CRM draft server",
            catalog_state=RuntimeMcpServerCatalogState.review_required,
            safe_summary=(
                "CRM draft server needs reviewed grants before any draft helper "
                "can become more than metadata."
            ),
            tool_slices=[
                _tool_slice(
                    "crm-draft-summary",
                    display_label="Draft CRM summary",
                    filter_state=RuntimeMcpToolFilterState.grant_required,
                    risk_label="draft_review_required",
                    safe_summary="Draft helper metadata needs exact grants and receipts.",
                ),
                _tool_slice(
                    "crm-send-message",
                    display_label="Send CRM message",
                    filter_state=RuntimeMcpToolFilterState.filtered_blocked,
                    risk_label="connector_write_blocked",
                    safe_summary="Connector write tool slice is filtered out.",
                ),
            ],
        ),
    ]
    payload_for_hash: dict[str, object] = {
        "servers": [server.model_dump(mode="json") for server in servers],
        "blocked": list(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS),
    }
    tool_slice_count = sum(server.tool_count for server in servers)
    return RuntimeMcpCatalogFilteringReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        servers=servers,
        server_count=len(servers),
        reviewed_metadata_count=sum(
            1
            for server in servers
            if server.catalog_state
            == RuntimeMcpServerCatalogState.reviewed_metadata.value
        ),
        review_required_count=sum(
            1
            for server in servers
            if server.catalog_state == RuntimeMcpServerCatalogState.review_required.value
        ),
        activation_blocked_count=sum(
            1
            for server in servers
            if server.catalog_state
            == RuntimeMcpServerCatalogState.activation_blocked.value
        ),
        tool_slice_count=tool_slice_count,
        metadata_visible_tool_count=sum(
            server.metadata_visible_tool_count for server in servers
        ),
        filtered_blocked_tool_count=sum(
            server.filtered_blocked_tool_count for server in servers
        ),
        grant_required_tool_count=sum(
            server.grant_required_tool_count for server in servers
        ),
        blocked_authority_refs=list(RUNTIME_MCP_CATALOG_FILTERING_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            "promotion-path-ref:mcp-catalog:reviewed-server-manifest",
            "promotion-path-ref:mcp-catalog:command-allowlist",
            "promotion-path-ref:mcp-catalog:credential-refs",
            "promotion-path-ref:mcp-catalog:tool-grants",
            "promotion-path-ref:mcp-catalog:receipts",
            "promotion-path-ref:mcp-catalog:safe-disable",
        ],
        proof_refs=[
            RUNTIME_MCP_CATALOG_FILTERING_PROOF_REF,
            "proof-ref:mcp-catalog:metadata-only",
            "proof-ref:mcp-catalog:filtered-tool-slices",
        ],
        verifier_refs=[RUNTIME_MCP_CATALOG_FILTERING_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:mcp-catalog:review-server-manifests",
            "next-safe-action-ref:mcp-catalog:define-tool-grants",
            "next-safe-action-ref:mcp-catalog:bind-receipts",
        ],
    )
