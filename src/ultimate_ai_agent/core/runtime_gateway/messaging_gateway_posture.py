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


RUNTIME_MESSAGING_GATEWAY_POSTURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-messaging-gateway-posture:v1"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_ROUTE_REF = (
    "GET /api/runtime/messaging-gateway-posture"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_CLI_REF = (
    "uaa runtime inspect-messaging-gateway-posture"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_DOC_REF = (
    "docs/runtime/UAA_HERMES_RUNTIME_MESSAGING_GATEWAY_POSTURE.md"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_SNAPSHOT_REF = (
    "messaging-gateway-posture-snapshot-ref:runtime:phase-42"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-42:messaging-gateway-posture"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-42:messaging-gateway-posture"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-messaging-gateway-posture-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:messaging-gateway-no-connector-runtime",
    "blocked-authority:messaging-gateway-no-sends",
    "blocked-authority:messaging-gateway-no-oauth",
    "blocked-authority:messaging-gateway-no-webhook-exposure",
    "blocked-authority:messaging-gateway-no-account-sync",
    "blocked-authority:messaging-gateway-no-external-writes",
    "blocked-authority:messaging-gateway-no-raw-message-persistence",
    "blocked-authority:messaging-gateway-no-control-center-authority-mint",
)


class RuntimeMessagingPlatformKind(str, Enum):
    email = "email"
    slack = "slack"
    telegram = "telegram"
    sms = "sms"
    discord = "discord"
    generic_webhook = "generic_webhook"


class RuntimeMessagingGatewayStatus(str, Enum):
    readiness_label_only = "readiness_label_only"
    blocked_until_authority = "blocked_until_authority"


class RuntimeMessagingGatewayPlatform(BaseModel):
    platform_ref: str
    platform_kind: RuntimeMessagingPlatformKind
    display_label: str
    status: RuntimeMessagingGatewayStatus
    safe_summary: str
    connector_label_ref: str
    inbound_readiness_ref: str
    outbound_write_label_ref: str
    oauth_label_ref: str
    webhook_label_ref: str
    account_sync_label_ref: str
    redaction_policy_ref: str
    proof_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    connector_runtime_enabled: bool = False
    connector_read_enabled: bool = False
    send_enabled: bool = False
    oauth_enabled: bool = False
    webhook_exposure_enabled: bool = False
    account_sync_enabled: bool = False
    external_write_enabled: bool = False
    raw_message_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_platform(self) -> "RuntimeMessagingGatewayPlatform":
        for value, field_name in [
            (self.platform_ref, "platform_ref"),
            (self.connector_label_ref, "connector_label_ref"),
            (self.inbound_readiness_ref, "inbound_readiness_ref"),
            (self.outbound_write_label_ref, "outbound_write_label_ref"),
            (self.oauth_label_ref, "oauth_label_ref"),
            (self.webhook_label_ref, "webhook_label_ref"),
            (self.account_sync_label_ref, "account_sync_label_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
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
            (str(self.platform_kind), "platform_kind"),
            (self.display_label, "display_label"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "connector_runtime_enabled": self.connector_runtime_enabled,
            "connector_read_enabled": self.connector_read_enabled,
            "send_enabled": self.send_enabled,
            "oauth_enabled": self.oauth_enabled,
            "webhook_exposure_enabled": self.webhook_exposure_enabled,
            "account_sync_enabled": self.account_sync_enabled,
            "external_write_enabled": self.external_write_enabled,
            "raw_message_persisted": self.raw_message_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_MESSAGING_GATEWAY_PLATFORM_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_PLATFORM_BLOCKERS_REQUIRED")
        return self


class RuntimeMessagingGatewayPostureReadModel(BaseModel):
    schema_version: str = "runtime_messaging_gateway_posture.v1"
    contract_ref: str = RUNTIME_MESSAGING_GATEWAY_POSTURE_CONTRACT_REF
    status: str = "metadata_readiness_map_only"
    snapshot_ref: str = RUNTIME_MESSAGING_GATEWAY_POSTURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:messaging-gateway-posture:pending"
    route_ref: str = RUNTIME_MESSAGING_GATEWAY_POSTURE_ROUTE_REF
    cli_ref: str = RUNTIME_MESSAGING_GATEWAY_POSTURE_CLI_REF
    doc_ref: str = RUNTIME_MESSAGING_GATEWAY_POSTURE_DOC_REF
    authority_state_route_ref: str = (
        RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_STATE_ROUTE_REF
    )
    authority_state_cli_ref: str = (
        RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_STATE_CLI_REF
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
        "Messaging platforms are represented as readiness labels only; connector "
        "runtime, sends, OAuth, webhook exposure, account sync, and writes remain "
        "blocked."
    )
    platforms: list[RuntimeMessagingGatewayPlatform] = Field(default_factory=list)
    platform_count: int = 0
    blocked_platform_count: int = 0
    connector_runtime_enabled: bool = False
    connector_read_enabled: bool = False
    send_enabled: bool = False
    oauth_enabled: bool = False
    webhook_exposure_enabled: bool = False
    account_sync_enabled: bool = False
    external_write_enabled: bool = False
    raw_message_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_messages_omitted",
            "account_material_omitted",
            "connector_payloads_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeMessagingGatewayPostureReadModel":
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
            != RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "connector_runtime_enabled": self.connector_runtime_enabled,
            "connector_read_enabled": self.connector_read_enabled,
            "send_enabled": self.send_enabled,
            "oauth_enabled": self.oauth_enabled,
            "webhook_exposure_enabled": self.webhook_exposure_enabled,
            "account_sync_enabled": self.account_sync_enabled,
            "external_write_enabled": self.external_write_enabled,
            "raw_message_persisted": self.raw_message_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_MESSAGING_GATEWAY_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if set(RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_BLOCKERS_REQUIRED")
        if self.platform_count != len(self.platforms):
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_COUNT_MISMATCH")
        if self.blocked_platform_count != len(
            [
                platform
                for platform in self.platforms
                if platform.status
                == RuntimeMessagingGatewayStatus.blocked_until_authority
            ]
        ):
            raise ValueError("RUNTIME_MESSAGING_GATEWAY_BLOCKED_COUNT_MISMATCH")
        return self


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _platform(
    platform_kind: RuntimeMessagingPlatformKind,
    display_label: str,
    summary: str,
) -> RuntimeMessagingGatewayPlatform:
    token = platform_kind.value.replace("_", "-")
    return RuntimeMessagingGatewayPlatform(
        platform_ref=f"messaging-platform-ref:runtime:{token}",
        platform_kind=platform_kind,
        display_label=display_label,
        status=RuntimeMessagingGatewayStatus.blocked_until_authority,
        safe_summary=summary,
        connector_label_ref=f"connector-label-ref:messaging:{token}",
        inbound_readiness_ref=f"inbound-readiness-ref:messaging:{token}",
        outbound_write_label_ref=f"outbound-write-label-ref:messaging:{token}",
        oauth_label_ref=f"oauth-label-ref:messaging:{token}",
        webhook_label_ref=f"webhook-label-ref:messaging:{token}",
        account_sync_label_ref=f"account-sync-label-ref:messaging:{token}",
        redaction_policy_ref=f"redaction-policy-ref:messaging:{token}",
        proof_ref=f"proof-ref:messaging-gateway:{token}",
        blocked_authority_refs=list(RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:messaging:{token}:account-ref",
            f"promotion-path-ref:messaging:{token}:delivery-receipt",
            f"promotion-path-ref:messaging:{token}:revoke-safe-disable",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:messaging:{token}:connector-contract"
        ],
    )


def build_runtime_messaging_gateway_posture_read_model(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> (
    RuntimeMessagingGatewayPostureReadModel
):
    authority_entry = _authority_entry(authority_decision_catalog)
    platforms = [
        _platform(
            RuntimeMessagingPlatformKind.email,
            "Email",
            "Email remains a readiness label only; sends, sync, OAuth, and raw "
            "message persistence are blocked.",
        ),
        _platform(
            RuntimeMessagingPlatformKind.slack,
            "Slack",
            "Slack remains a readiness label only; OAuth, workspace sync, webhooks, "
            "and sends are blocked.",
        ),
        _platform(
            RuntimeMessagingPlatformKind.telegram,
            "Telegram",
            "Telegram remains a readiness label only; bot runtime, webhook exposure, "
            "and sends are blocked.",
        ),
        _platform(
            RuntimeMessagingPlatformKind.sms,
            "SMS",
            "SMS remains a readiness label only; account sync, sends, and external "
            "delivery are blocked.",
        ),
        _platform(
            RuntimeMessagingPlatformKind.discord,
            "Discord",
            "Discord remains a readiness label only; OAuth, bot runtime, webhooks, "
            "and sends are blocked.",
        ),
        _platform(
            RuntimeMessagingPlatformKind.generic_webhook,
            "Generic webhook",
            "Generic webhook remains a readiness label only; inbound exposure and "
            "external writes are blocked.",
        ),
    ]
    payload = {
        "route_ref": RUNTIME_MESSAGING_GATEWAY_POSTURE_ROUTE_REF,
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
        "platforms": platforms,
        "platform_count": len(platforms),
        "blocked_platform_count": len(platforms),
        "blocked_authority_refs": list(RUNTIME_MESSAGING_GATEWAY_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:messaging-gateway:connector-read-write-authority",
            "promotion-path-ref:messaging-gateway:account-refs",
            "promotion-path-ref:messaging-gateway:delivery-receipt",
            "promotion-path-ref:messaging-gateway:revoke-safe-disable",
            "promotion-path-ref:messaging-gateway:redaction-proof",
        ],
        "proof_refs": [RUNTIME_MESSAGING_GATEWAY_POSTURE_PROOF_REF],
        "verifier_refs": [RUNTIME_MESSAGING_GATEWAY_POSTURE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:messaging-gateway:connector-read-contract",
            "next-safe-action-ref:messaging-gateway:send-write-approval-contract",
        ],
    }
    snapshot_material = {
        "contract_ref": RUNTIME_MESSAGING_GATEWAY_POSTURE_CONTRACT_REF,
        "route_ref": payload["route_ref"],
        "cli_ref": RUNTIME_MESSAGING_GATEWAY_POSTURE_CLI_REF,
        "platform_refs": [platform.platform_ref for platform in platforms],
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:messaging-gateway-posture:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeMessagingGatewayPostureReadModel(**payload)


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_MESSAGING_GATEWAY_POSTURE_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_MESSAGING_GATEWAY_AUTHORITY_MAPPING_MISSING")
