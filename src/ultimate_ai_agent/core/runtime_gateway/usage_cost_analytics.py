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


RUNTIME_USAGE_COST_ANALYTICS_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-usage-cost-analytics:v1"
)
RUNTIME_USAGE_COST_ANALYTICS_ROUTE_REF = "GET /api/runtime/usage-cost-analytics"
RUNTIME_USAGE_COST_ANALYTICS_CLI_REF = "uaa runtime inspect-usage-cost-analytics"
RUNTIME_USAGE_COST_ANALYTICS_SNAPSHOT_REF = (
    "usage-cost-analytics-snapshot-ref:runtime:redacted-accounting"
)
RUNTIME_USAGE_COST_ANALYTICS_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-22:usage-cost-analytics"
)
RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-usage-cost-analytics-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:usage-cost-analytics-no-billing-action",
    "blocked-authority:usage-cost-analytics-no-provider-call",
    "blocked-authority:usage-cost-analytics-no-provider-sdk-call",
    "blocked-authority:usage-cost-analytics-no-live-price-fetch",
    "blocked-authority:usage-cost-analytics-no-raw-prompt-persistence",
    "blocked-authority:usage-cost-analytics-no-raw-response-persistence",
    "blocked-authority:usage-cost-analytics-no-provider-payload-persistence",
    "blocked-authority:usage-cost-analytics-no-operator-export",
    "blocked-authority:usage-cost-analytics-no-production-authority",
]


class RuntimeUsageAccountingSource(str, Enum):
    manual_diagnostic_receipt = "manual_diagnostic_receipt"
    runtime_receipt_metadata = "runtime_receipt_metadata"
    provider_catalog_reference = "provider_catalog_reference"
    delegated_runtime_future = "delegated_runtime_future"


class RuntimeUsageAccountingStatus(str, Enum):
    recorded_diagnostic = "recorded_diagnostic"
    read_only_estimate = "read_only_estimate"
    blocked_missing_authority = "blocked_missing_authority"


class RuntimeUsageCostRecord(BaseModel):
    record_ref: str
    display_label: str
    source_kind: RuntimeUsageAccountingSource
    status: RuntimeUsageAccountingStatus
    runtime_ref: str
    provider_ref: str
    model_ref: str
    task_value_ref: str
    receipt_ref: str
    cost_estimate_ref: str
    safe_summary: str
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_total_tokens: int = 0
    latency_ms: int = 0
    estimated_cost_minor_units: int = 0
    currency_ref: str = "currency-ref:usd"
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    provider_call_performed: bool = False
    provider_sdk_call_performed: bool = False
    billing_action_performed: bool = False
    live_price_fetch_performed: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    provider_payload_persisted: bool = False
    output_authoritative: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeUsageCostRecord":
        for value, field_name in [
            (self.record_ref, "record_ref"),
            (self.runtime_ref, "runtime_ref"),
            (self.provider_ref, "provider_ref"),
            (self.model_ref, "model_ref"),
            (self.task_value_ref, "task_value_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.cost_estimate_ref, "cost_estimate_ref"),
            (self.currency_ref, "currency_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("proof_refs", "evidence_refs", "blocked_authority_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (str(self.source_kind), "source_kind"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if (
            self.estimated_input_tokens
            + self.estimated_output_tokens
            != self.estimated_total_tokens
        ):
            raise ValueError("RUNTIME_USAGE_COST_TOTAL_MISMATCH")
        for field_name in (
            "estimated_input_tokens",
            "estimated_output_tokens",
            "estimated_total_tokens",
            "latency_ms",
            "estimated_cost_minor_units",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError("RUNTIME_USAGE_COST_NEGATIVE_ACCOUNTING_DENIED")
        denied_flags = {
            "provider_call_performed": self.provider_call_performed,
            "provider_sdk_call_performed": self.provider_sdk_call_performed,
            "billing_action_performed": self.billing_action_performed,
            "live_price_fetch_performed": self.live_price_fetch_performed,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "provider_payload_persisted": self.provider_payload_persisted,
            "output_authoritative": self.output_authoritative,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_USAGE_COST_RECORD_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_USAGE_COST_RECORD_BLOCKERS_REQUIRED")
        return self


class RuntimeUsageCostAnalyticsReadModel(BaseModel):
    schema_version: str = "runtime_usage_cost_analytics.v1"
    contract_ref: str = RUNTIME_USAGE_COST_ANALYTICS_CONTRACT_REF
    status: str = "read_only_redacted_accounting_posture"
    snapshot_ref: str = RUNTIME_USAGE_COST_ANALYTICS_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-usage-cost-analytics:pending"
    route_ref: str = RUNTIME_USAGE_COST_ANALYTICS_ROUTE_REF
    cli_ref: str = RUNTIME_USAGE_COST_ANALYTICS_CLI_REF
    authority_state_route_ref: str
    authority_state_cli_ref: str
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
        "Runtime usage and cost posture uses redacted receipt metadata and "
        "manual estimates only; provider calls, billing actions, live price "
        "fetches, and operator export remain blocked."
    )
    records: list[RuntimeUsageCostRecord]
    record_count: int = 0
    manual_diagnostic_receipt_count: int = 0
    runtime_receipt_record_count: int = 0
    provider_catalog_reference_count: int = 0
    blocked_record_count: int = 0
    total_estimated_input_tokens: int = 0
    total_estimated_output_tokens: int = 0
    total_estimated_tokens: int = 0
    total_latency_ms: int = 0
    total_estimated_cost_minor_units: int = 0
    currency_ref: str = "currency-ref:usd"
    operator_export_available: bool = False
    billing_action_enabled: bool = False
    provider_call_enabled: bool = False
    provider_sdk_enabled: bool = False
    live_price_fetch_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    provider_payload_persistence_enabled: bool = False
    output_authority_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_prompts_omitted",
                "raw_responses_omitted",
                "provider_payloads_omitted",
                "billing_payloads_omitted",
                "operator_export_payloads_omitted",
                "usage_samples_bounded",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeUsageCostAnalyticsReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.currency_ref, "currency_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
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
        if (
            self.authority_state_mapping_ref
            != RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_USAGE_COST_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_USAGE_COST_AUTHORITY_DECISION_INVALID")
        if self.record_count != len(self.records):
            raise ValueError("RUNTIME_USAGE_COST_RECORD_COUNT_MISMATCH")
        if self.manual_diagnostic_receipt_count != len(
            [
                record
                for record in self.records
                if record.source_kind
                == RuntimeUsageAccountingSource.manual_diagnostic_receipt.value
            ]
        ):
            raise ValueError("RUNTIME_USAGE_COST_MANUAL_COUNT_MISMATCH")
        if self.runtime_receipt_record_count != len(
            [
                record
                for record in self.records
                if record.source_kind
                == RuntimeUsageAccountingSource.runtime_receipt_metadata.value
            ]
        ):
            raise ValueError("RUNTIME_USAGE_COST_RECEIPT_COUNT_MISMATCH")
        if self.provider_catalog_reference_count != len(
            [
                record
                for record in self.records
                if record.source_kind
                == RuntimeUsageAccountingSource.provider_catalog_reference.value
            ]
        ):
            raise ValueError("RUNTIME_USAGE_COST_CATALOG_COUNT_MISMATCH")
        if self.blocked_record_count != len(
            [
                record
                for record in self.records
                if record.status
                == RuntimeUsageAccountingStatus.blocked_missing_authority.value
            ]
        ):
            raise ValueError("RUNTIME_USAGE_COST_BLOCKED_COUNT_MISMATCH")
        totals = {
            "total_estimated_input_tokens": sum(
                record.estimated_input_tokens for record in self.records
            ),
            "total_estimated_output_tokens": sum(
                record.estimated_output_tokens for record in self.records
            ),
            "total_estimated_tokens": sum(
                record.estimated_total_tokens for record in self.records
            ),
            "total_latency_ms": sum(record.latency_ms for record in self.records),
            "total_estimated_cost_minor_units": sum(
                record.estimated_cost_minor_units for record in self.records
            ),
        }
        mismatches = [
            field_name
            for field_name, expected in totals.items()
            if getattr(self, field_name) != expected
        ]
        if mismatches:
            raise ValueError(
                "RUNTIME_USAGE_COST_TOTALS_MISMATCH: " + ", ".join(mismatches)
            )
        denied_flags = {
            "operator_export_available": self.operator_export_available,
            "billing_action_enabled": self.billing_action_enabled,
            "provider_call_enabled": self.provider_call_enabled,
            "provider_sdk_enabled": self.provider_sdk_enabled,
            "live_price_fetch_enabled": self.live_price_fetch_enabled,
            "raw_prompt_persistence_enabled": self.raw_prompt_persistence_enabled,
            "raw_response_persistence_enabled": self.raw_response_persistence_enabled,
            "provider_payload_persistence_enabled": (
                self.provider_payload_persistence_enabled
            ),
            "output_authority_enabled": self.output_authority_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if RUNTIME_USAGE_COST_ANALYTICS_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_USAGE_COST_ANALYTICS_PROOF_REQUIRED")
        if set(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_USAGE_COST_ANALYTICS_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-usage-cost-analytics:{digest}"


def _record(
    *,
    slug: str,
    display_label: str,
    source_kind: RuntimeUsageAccountingSource,
    status: RuntimeUsageAccountingStatus,
    runtime_ref: str,
    provider_ref: str,
    model_ref: str,
    task_value_ref: str,
    safe_summary: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    latency_ms: int,
    estimated_cost_minor_units: int,
) -> RuntimeUsageCostRecord:
    return RuntimeUsageCostRecord(
        record_ref=f"usage-cost-record-ref:{slug}",
        display_label=display_label,
        source_kind=source_kind,
        status=status,
        runtime_ref=runtime_ref,
        provider_ref=provider_ref,
        model_ref=model_ref,
        task_value_ref=task_value_ref,
        receipt_ref=f"runtime-receipt-ref:usage-cost:{slug}",
        cost_estimate_ref=f"cost-estimate-ref:runtime-usage:{slug}",
        safe_summary=safe_summary,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        estimated_total_tokens=estimated_input_tokens + estimated_output_tokens,
        latency_ms=latency_ms,
        estimated_cost_minor_units=estimated_cost_minor_units,
        proof_refs=[RUNTIME_USAGE_COST_ANALYTICS_PROOF_REF],
        evidence_refs=[f"evidence-ref:runtime-usage-cost:{slug}"],
        blocked_authority_refs=list(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS),
    )


def _default_records() -> list[RuntimeUsageCostRecord]:
    return [
        _record(
            slug="local-loopback-diagnostic",
            display_label="Local diagnostic accounting",
            source_kind=RuntimeUsageAccountingSource.manual_diagnostic_receipt,
            status=RuntimeUsageAccountingStatus.recorded_diagnostic,
            runtime_ref="runtime-ref:uaa:runtime-gateway",
            provider_ref="provider-ref:uaa:local-loopback",
            model_ref="model-ref:uaa:loopback-diagnostic",
            task_value_ref="task-value-ref:runtime-usage:local-diagnostic",
            safe_summary=(
                "Manual diagnostic row records bounded local loopback accounting "
                "metadata without remote provider activity."
            ),
            estimated_input_tokens=128,
            estimated_output_tokens=64,
            latency_ms=42,
            estimated_cost_minor_units=0,
        ),
        _record(
            slug="runtime-receipt-metadata",
            display_label="Runtime receipt metadata estimate",
            source_kind=RuntimeUsageAccountingSource.runtime_receipt_metadata,
            status=RuntimeUsageAccountingStatus.read_only_estimate,
            runtime_ref="runtime-ref:uaa:runtime-gateway",
            provider_ref="provider-ref:uaa:governed-local-adapter",
            model_ref="model-ref:uaa:receipt-metadata-estimate",
            task_value_ref="task-value-ref:runtime-usage:receipt-metadata",
            safe_summary=(
                "Read-only estimate row binds accounting posture to a receipt ref "
                "and stores no raw prompt, response, or provider payload."
            ),
            estimated_input_tokens=320,
            estimated_output_tokens=120,
            latency_ms=155,
            estimated_cost_minor_units=0,
        ),
        _record(
            slug="provider-catalog-reference",
            display_label="Provider catalog cost reference",
            source_kind=RuntimeUsageAccountingSource.provider_catalog_reference,
            status=RuntimeUsageAccountingStatus.read_only_estimate,
            runtime_ref="runtime-ref:provider-catalog:read-only",
            provider_ref="provider-ref:frontier-provider:blocked-reference",
            model_ref="model-ref:frontier-model:cost-reference",
            task_value_ref="task-value-ref:runtime-usage:provider-catalog-reference",
            safe_summary=(
                "Catalog reference row is an offline estimate only; it performs "
                "no provider call, SDK call, billing action, or price fetch."
            ),
            estimated_input_tokens=900,
            estimated_output_tokens=250,
            latency_ms=0,
            estimated_cost_minor_units=14,
        ),
        _record(
            slug="delegated-runtime-future",
            display_label="Delegated runtime future accounting",
            source_kind=RuntimeUsageAccountingSource.delegated_runtime_future,
            status=RuntimeUsageAccountingStatus.blocked_missing_authority,
            runtime_ref="runtime-ref:hermes-agent:optional-target",
            provider_ref="provider-ref:delegated-runtime:future",
            model_ref="model-ref:delegated-runtime:future",
            task_value_ref="task-value-ref:runtime-usage:delegated-future",
            safe_summary=(
                "Delegated runtime accounting stays blocked until result envelopes, "
                "cost attribution, and redacted receipts are implemented."
            ),
            estimated_input_tokens=0,
            estimated_output_tokens=0,
            latency_ms=0,
            estimated_cost_minor_units=0,
        ),
    ]


def build_runtime_usage_cost_analytics_read_model() -> (
    RuntimeUsageCostAnalyticsReadModel
):
    return build_runtime_usage_cost_analytics_read_model_from_authority_catalog(
        authority_decision_catalog=build_authority_decision_catalog()
    )


def build_runtime_usage_cost_analytics_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeUsageCostAnalyticsReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    records = _default_records()
    model = RuntimeUsageCostAnalyticsReadModel(
        authority_state_route_ref=RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_STATE_CLI_REF,
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        records=records,
        record_count=len(records),
        manual_diagnostic_receipt_count=len(
            [
                record
                for record in records
                if record.source_kind
                == RuntimeUsageAccountingSource.manual_diagnostic_receipt.value
            ]
        ),
        runtime_receipt_record_count=len(
            [
                record
                for record in records
                if record.source_kind
                == RuntimeUsageAccountingSource.runtime_receipt_metadata.value
            ]
        ),
        provider_catalog_reference_count=len(
            [
                record
                for record in records
                if record.source_kind
                == RuntimeUsageAccountingSource.provider_catalog_reference.value
            ]
        ),
        blocked_record_count=len(
            [
                record
                for record in records
                if record.status
                == RuntimeUsageAccountingStatus.blocked_missing_authority.value
            ]
        ),
        total_estimated_input_tokens=sum(
            record.estimated_input_tokens for record in records
        ),
        total_estimated_output_tokens=sum(
            record.estimated_output_tokens for record in records
        ),
        total_estimated_tokens=sum(record.estimated_total_tokens for record in records),
        total_latency_ms=sum(record.latency_ms for record in records),
        total_estimated_cost_minor_units=sum(
            record.estimated_cost_minor_units for record in records
        ),
        blocked_authority_refs=list(RUNTIME_USAGE_COST_ANALYTICS_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_USAGE_COST_ANALYTICS_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-22"],
        next_safe_action_refs=[
            "next-safe-action-ref:usage-cost-analytics:bind-provider-result-envelope",
            "next-safe-action-ref:usage-cost-analytics:add-cost-attribution",
            "next-safe-action-ref:usage-cost-analytics:keep-billing-blocked",
        ],
    )
    model.snapshot_hash_ref = _hash_payload(
        [
            {
                "record_ref": record.record_ref,
                "source_kind": record.source_kind,
                "status": record.status,
                "runtime_ref": record.runtime_ref,
                "provider_ref": record.provider_ref,
                "model_ref": record.model_ref,
                "receipt_ref": record.receipt_ref,
                "estimated_total_tokens": record.estimated_total_tokens,
                "estimated_cost_minor_units": record.estimated_cost_minor_units,
                "authority_state_decision_ref": (
                    authority_entry.decision.decision_ref
                ),
                "authority_state_decision_outcome": _authority_value(
                    authority_entry.decision.outcome
                ),
            }
            for record in records
        ]
    )
    return RuntimeUsageCostAnalyticsReadModel(**model.model_dump(mode="json"))


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> AuthorityDecisionCatalogEntry:
    for entry in authority_decision_catalog:
        if entry.lane_ref == RUNTIME_USAGE_COST_ANALYTICS_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_USAGE_COST_AUTHORITY_MAPPING_NOT_FOUND")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
