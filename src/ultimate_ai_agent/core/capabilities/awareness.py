from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any, Literal

from jsonschema import SchemaError
from jsonschema.validators import validator_for
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityHealthStatus,
    PolicyDecisionStatus,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import CapabilityManifest
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry
from ultimate_ai_agent.core.execution.validation import (
    contains_absolute_local_path,
    validate_execution_ref,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


TAW01_CONTRACT_REF = "contract-ref:taw01:capability-awareness-envelope:v1"
TAW01_GENERATOR_REF = "generator-ref:taw01:registered-capability-envelope:v1"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SAFE_FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_EFFECT_RANK = {
    SideEffectLevel.none: 0,
    SideEffectLevel.read: 1,
    SideEffectLevel.write: 2,
    SideEffectLevel.external: 3,
    SideEffectLevel.destructive: 4,
}
_RISK_RANK = {
    RiskLevel.safe: 0,
    RiskLevel.low: 1,
    RiskLevel.medium: 2,
    RiskLevel.high: 3,
    RiskLevel.critical: 4,
    RiskLevel.forbidden: 5,
}


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("awareness payload must be canonical JSON") from exc


def _fingerprint(payload: object, *, prefix: str) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


def _validate_operator_text(value: str, field_name: str) -> None:
    if not value or value != value.strip() or "\n" in value or "\r" in value:
        raise ValueError(f"{field_name} must be one bounded line")
    if contains_absolute_local_path(value) or contains_obvious_secret(value):
        raise ValueError(f"{field_name} contains unsafe content")


def _validate_schema(schema: Mapping[str, Any], field_name: str) -> None:
    if schema.get("type") != "object":
        raise ValueError(f"{field_name} must be an object schema")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise ValueError(f"{field_name} properties and required fields are malformed")
    if any(
        not isinstance(item, str) or not _SAFE_FIELD_RE.fullmatch(item)
        for item in required
    ):
        raise ValueError(f"{field_name} required fields must be bounded safe labels")
    if len(required) != len(set(required)) or not set(required).issubset(properties):
        raise ValueError(f"{field_name} required fields are duplicate or undefined")
    for key, value in properties.items():
        if not isinstance(key, str) or not _SAFE_FIELD_RE.fullmatch(key):
            raise ValueError(f"{field_name} property names must be bounded safe labels")
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} property definitions must be mappings")
    try:
        validator_for(schema).check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"{field_name} is not a valid JSON Schema") from exc
    _canonical_json(schema)


def _validate_fingerprint_ref(value: str, field_name: str, *, prefix: str) -> None:
    expected_prefix = f"{prefix}:sha256:"
    if not value.startswith(expected_prefix) or not _DIGEST_RE.fullmatch(
        "sha256:" + value.removeprefix(expected_prefix)
    ):
        raise ValueError(f"{field_name} must be an exact {prefix} sha256 ref")


def _schema_fingerprint(schema: Mapping[str, Any], *, kind: str) -> str:
    return _fingerprint(schema, prefix=f"schema-fingerprint-ref:taw01:{kind}")


def _input_partition_schema(
    schema: Mapping[str, Any], *, required_partition: bool
) -> dict[str, Any]:
    properties = dict(schema.get("properties", {}))
    required = set(schema.get("required", []))
    selected = {
        key: properties[key]
        for key in sorted(properties)
        if (key in required) is required_partition
    }
    return {
        "type": "object",
        "properties": selected,
        "required": sorted(required) if required_partition else [],
        "additionalProperties": schema.get("additionalProperties", True),
    }


def _input_field_refs(
    operation_id: str, schema: Mapping[str, Any]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    suffix = operation_id.split(":", 1)[1].replace(":", "/")
    required = set(schema.get("required", []))
    required_refs = tuple(
        sorted(
            f"input-field-ref:{suffix}/{name}"
            for name in schema.get("properties", {})
            if name in required
        )
    )
    optional_refs = tuple(
        sorted(
            f"input-field-ref:{suffix}/{name}"
            for name in schema.get("properties", {})
            if name not in required
        )
    )
    return required_refs, optional_refs


class CapabilityOperationSchema(_FrozenModel):
    schema_version: Literal["uaa-taw01-operation-schema.v1"] = (
        "uaa-taw01-operation-schema.v1"
    )
    operation_id: str
    operation_version: str
    capability_id: str
    capability_version: str
    operator_summary: str = Field(..., min_length=1, max_length=240)
    aliases: tuple[str, ...] = Field(..., min_length=1, max_length=32)
    effect_class: SideEffectLevel
    risk_class: RiskLevel
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    precondition_refs: tuple[str, ...] = ()
    incompatibility_refs: tuple[str, ...] = ()
    dependency_operation_refs: tuple[str, ...] = ()
    positive_eval_refs: tuple[str, ...] = Field(..., min_length=1)
    negative_eval_refs: tuple[str, ...] = Field(..., min_length=1)
    ambiguity_eval_refs: tuple[str, ...] = Field(..., min_length=1)
    adversarial_eval_refs: tuple[str, ...] = Field(..., min_length=1)
    provenance_ref: str
    review_ref: str
    reviewed: Literal[True] = True

    @model_validator(mode="after")
    def validate_operation(self) -> "CapabilityOperationSchema":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.capability_id, "capability_id"),
            (self.provenance_ref, "provenance_ref"),
            (self.review_ref, "review_ref"),
        ):
            _validate_ref(value, field_name)
        for value, field_name in (
            (self.operation_version, "operation_version"),
            (self.capability_version, "capability_version"),
        ):
            if not _SAFE_LABEL_RE.fullmatch(value):
                raise ValueError(f"{field_name} must be a bounded safe label")
        _validate_operator_text(self.operator_summary, "operator_summary")
        if self.aliases != tuple(sorted(self.aliases, key=str.casefold)) or len(
            self.aliases
        ) != len({item.casefold() for item in self.aliases}):
            raise ValueError("aliases must be case-insensitively unique and sorted")
        for alias in self.aliases:
            _validate_operator_text(alias, "alias")
        _validate_schema(self.input_schema, "input_schema")
        _validate_schema(self.output_schema, "output_schema")
        for values, field_name in (
            (self.precondition_refs, "precondition_refs"),
            (self.incompatibility_refs, "incompatibility_refs"),
            (self.dependency_operation_refs, "dependency_operation_refs"),
            (self.positive_eval_refs, "positive_eval_refs"),
            (self.negative_eval_refs, "negative_eval_refs"),
            (self.ambiguity_eval_refs, "ambiguity_eval_refs"),
            (self.adversarial_eval_refs, "adversarial_eval_refs"),
        ):
            _validate_refs(values, field_name)
        if self.operation_id in self.dependency_operation_refs:
            raise ValueError("an operation cannot depend on itself")
        return self


class CapabilityAwarenessBinding(_FrozenModel):
    schema_version: Literal["uaa-taw01-awareness-binding.v1"] = (
        "uaa-taw01-awareness-binding.v1"
    )
    operation_id: str
    health_status: CapabilityHealthStatus
    availability_ref: str
    policy_decision_status: PolicyDecisionStatus
    policy_snapshot_ref: str
    authority_lane_status: Literal["not_applicable", "blocked", "graduated"]
    authority_lane_ref: str
    safe_disable_ref: str
    rollback_posture: Literal["supported", "not_applicable", "required_but_unavailable"]
    rollback_ref: str
    terminal_proof_contract_ref: str
    expected_terminal_status_refs: tuple[str, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_binding(self) -> "CapabilityAwarenessBinding":
        for value, field_name in (
            (self.operation_id, "operation_id"),
            (self.availability_ref, "availability_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.authority_lane_ref, "authority_lane_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.terminal_proof_contract_ref, "terminal_proof_contract_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_refs(
            self.expected_terminal_status_refs, "expected_terminal_status_refs"
        )
        return self


class CapabilityAwarenessEnvelope(_FrozenModel):
    schema_version: Literal["uaa-taw01-capability-awareness-envelope.v1"] = (
        "uaa-taw01-capability-awareness-envelope.v1"
    )
    contract_ref: Literal["contract-ref:taw01:capability-awareness-envelope:v1"] = (
        TAW01_CONTRACT_REF
    )
    generator_ref: Literal["generator-ref:taw01:registered-capability-envelope:v1"] = (
        TAW01_GENERATOR_REF
    )
    capability_id: str
    capability_version: str
    operation_id: str
    operation_version: str
    operator_summary: str
    aliases: tuple[str, ...]
    effect_class: SideEffectLevel
    risk_class: RiskLevel
    authority_class: CapabilityAuthorityLevel
    approval_class: Literal["not_required", "exact_approval_required"]
    required_input_field_refs: tuple[str, ...]
    optional_input_field_refs: tuple[str, ...]
    required_input_schema_fingerprint_ref: str
    optional_input_schema_fingerprint_ref: str
    output_schema_fingerprint_ref: str
    operation_schema_fingerprint_ref: str
    precondition_refs: tuple[str, ...]
    incompatibility_refs: tuple[str, ...]
    dependency_operation_refs: tuple[str, ...]
    health_status: CapabilityHealthStatus
    availability_ref: str
    policy_decision_status: PolicyDecisionStatus
    policy_snapshot_ref: str
    authority_lane_status: Literal["not_applicable", "blocked", "graduated"]
    authority_lane_ref: str
    safe_disable_ref: str
    rollback_posture: Literal["supported", "not_applicable", "required_but_unavailable"]
    rollback_ref: str
    receipt_required: bool
    terminal_proof_contract_ref: str
    expected_terminal_status_refs: tuple[str, ...]
    positive_eval_refs: tuple[str, ...]
    negative_eval_refs: tuple[str, ...]
    ambiguity_eval_refs: tuple[str, ...]
    adversarial_eval_refs: tuple[str, ...]
    provenance_ref: str
    review_ref: str
    catalog_epoch_ref: str
    availability_epoch_ref: str
    generated_at_epoch_seconds: int = Field(..., ge=0)
    expires_at_epoch_seconds: int = Field(..., ge=0)
    envelope_fingerprint_ref: str
    raw_operator_content_persisted: Literal[False] = False
    raw_model_content_persisted: Literal[False] = False
    model_call_performed: Literal[False] = False
    provider_call_performed: Literal[False] = False
    execution_enabled: Literal[False] = False
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_envelope(self) -> "CapabilityAwarenessEnvelope":
        if self.generated_at_epoch_seconds >= self.expires_at_epoch_seconds:
            raise ValueError("awareness envelope expiry must follow generation")
        for value, field_name in (
            (self.capability_id, "capability_id"),
            (self.operation_id, "operation_id"),
            (self.availability_ref, "availability_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
            (self.authority_lane_ref, "authority_lane_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.terminal_proof_contract_ref, "terminal_proof_contract_ref"),
            (self.provenance_ref, "provenance_ref"),
            (self.review_ref, "review_ref"),
            (self.catalog_epoch_ref, "catalog_epoch_ref"),
            (self.availability_epoch_ref, "availability_epoch_ref"),
        ):
            _validate_ref(value, field_name)
        for value, field_name in (
            (self.capability_version, "capability_version"),
            (self.operation_version, "operation_version"),
        ):
            if not _SAFE_LABEL_RE.fullmatch(value):
                raise ValueError(f"{field_name} must be a bounded safe label")
        _validate_operator_text(self.operator_summary, "operator_summary")
        if self.aliases != tuple(sorted(self.aliases, key=str.casefold)) or len(
            self.aliases
        ) != len({item.casefold() for item in self.aliases}):
            raise ValueError("aliases must be case-insensitively unique and sorted")
        for alias in self.aliases:
            _validate_operator_text(alias, "alias")
        for values, field_name in (
            (self.required_input_field_refs, "required_input_field_refs"),
            (self.optional_input_field_refs, "optional_input_field_refs"),
            (self.precondition_refs, "precondition_refs"),
            (self.incompatibility_refs, "incompatibility_refs"),
            (self.dependency_operation_refs, "dependency_operation_refs"),
            (self.expected_terminal_status_refs, "expected_terminal_status_refs"),
            (self.positive_eval_refs, "positive_eval_refs"),
            (self.negative_eval_refs, "negative_eval_refs"),
            (self.ambiguity_eval_refs, "ambiguity_eval_refs"),
            (self.adversarial_eval_refs, "adversarial_eval_refs"),
        ):
            _validate_refs(values, field_name)
        if set(self.required_input_field_refs).intersection(
            self.optional_input_field_refs
        ):
            raise ValueError("required and optional input field refs must be disjoint")
        if self.operation_id in self.dependency_operation_refs:
            raise ValueError("an operation cannot depend on itself")
        if self.effect_class in {SideEffectLevel.none, SideEffectLevel.read}:
            if self.authority_class not in {
                CapabilityAuthorityLevel.metadata_only,
                CapabilityAuthorityLevel.read_only,
            }:
                raise ValueError("read/no-effect envelope authority is inconsistent")
            if (
                self.approval_class == "not_required"
                and self.authority_lane_status != "not_applicable"
            ):
                raise ValueError(
                    "read/no-effect envelope without approval cannot claim an authority lane"
                )
            if self.rollback_posture not in {"supported", "not_applicable"}:
                raise ValueError(
                    "read/no-effect envelope rollback posture is inconsistent"
                )
        else:
            if self.authority_lane_status == "not_applicable":
                raise ValueError("mutating envelope requires an authority-lane posture")
            if (
                self.effect_class == SideEffectLevel.write
                and self.authority_class
                not in {
                    CapabilityAuthorityLevel.mutating,
                    CapabilityAuthorityLevel.external,
                    CapabilityAuthorityLevel.destructive,
                }
            ):
                raise ValueError("write envelope authority is inconsistent")
            if (
                self.effect_class == SideEffectLevel.external
                and self.authority_class
                not in {
                    CapabilityAuthorityLevel.external,
                    CapabilityAuthorityLevel.destructive,
                }
            ):
                raise ValueError("external envelope authority is inconsistent")
            if (
                self.effect_class == SideEffectLevel.destructive
                and self.authority_class != CapabilityAuthorityLevel.destructive
            ):
                raise ValueError("destructive envelope authority is inconsistent")
        if (
            self.approval_class == "exact_approval_required"
            and self.authority_lane_status == "not_applicable"
        ):
            raise ValueError(
                "approval-required envelope needs an authority-lane posture"
            )
        for value, field_name, prefix in (
            (
                self.required_input_schema_fingerprint_ref,
                "required_input_schema_fingerprint_ref",
                "schema-fingerprint-ref:taw01:required-input",
            ),
            (
                self.optional_input_schema_fingerprint_ref,
                "optional_input_schema_fingerprint_ref",
                "schema-fingerprint-ref:taw01:optional-input",
            ),
            (
                self.output_schema_fingerprint_ref,
                "output_schema_fingerprint_ref",
                "schema-fingerprint-ref:taw01:output",
            ),
            (
                self.operation_schema_fingerprint_ref,
                "operation_schema_fingerprint_ref",
                "operation-schema-ref:taw01",
            ),
            (
                self.envelope_fingerprint_ref,
                "envelope_fingerprint_ref",
                "awareness-envelope-ref:taw01",
            ),
        ):
            _validate_fingerprint_ref(value, field_name, prefix=prefix)
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"envelope_fingerprint_ref"}),
            prefix="awareness-envelope-ref:taw01",
        )
        if self.envelope_fingerprint_ref != expected:
            raise ValueError("awareness envelope fingerprint binding drift")
        return self


class CapabilityAwarenessCatalog(_FrozenModel):
    schema_version: Literal["uaa-taw01-capability-awareness-catalog.v1"] = (
        "uaa-taw01-capability-awareness-catalog.v1"
    )
    contract_ref: Literal["contract-ref:taw01:capability-awareness-envelope:v1"] = (
        TAW01_CONTRACT_REF
    )
    catalog_epoch_ref: str
    availability_epoch_ref: str
    policy_snapshot_ref: str
    generated_at_epoch_seconds: int = Field(..., ge=0)
    expires_at_epoch_seconds: int = Field(..., ge=0)
    envelopes: tuple[CapabilityAwarenessEnvelope, ...] = Field(..., min_length=1)
    catalog_fingerprint_ref: str
    raw_operator_content_persisted: Literal[False] = False
    raw_model_content_persisted: Literal[False] = False
    model_call_performed: Literal[False] = False
    provider_call_performed: Literal[False] = False
    execution_enabled: Literal[False] = False
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_catalog(self) -> "CapabilityAwarenessCatalog":
        for value, field_name in (
            (self.catalog_epoch_ref, "catalog_epoch_ref"),
            (self.availability_epoch_ref, "availability_epoch_ref"),
            (self.policy_snapshot_ref, "policy_snapshot_ref"),
        ):
            _validate_ref(value, field_name)
        keys = [(item.capability_id, item.operation_id) for item in self.envelopes]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("awareness catalog envelopes must be unique and sorted")
        if self.generated_at_epoch_seconds >= self.expires_at_epoch_seconds:
            raise ValueError("awareness catalog expiry must follow generation")
        for envelope in self.envelopes:
            if (
                envelope.catalog_epoch_ref != self.catalog_epoch_ref
                or envelope.availability_epoch_ref != self.availability_epoch_ref
                or envelope.policy_snapshot_ref != self.policy_snapshot_ref
                or envelope.generated_at_epoch_seconds
                != self.generated_at_epoch_seconds
                or envelope.expires_at_epoch_seconds != self.expires_at_epoch_seconds
            ):
                raise ValueError("awareness envelope/catalog binding is inconsistent")
        _validate_fingerprint_ref(
            self.catalog_fingerprint_ref,
            "catalog_fingerprint_ref",
            prefix="awareness-catalog-ref:taw01",
        )
        expected = _fingerprint(
            self.model_dump(mode="json", exclude={"catalog_fingerprint_ref"}),
            prefix="awareness-catalog-ref:taw01",
        )
        if self.catalog_fingerprint_ref != expected:
            raise ValueError("awareness catalog fingerprint binding drift")
        return self


def operation_schema_from_manifest(
    manifest: CapabilityManifest,
    *,
    operation_id: str,
    operation_version: str,
    operator_summary: str,
    aliases: tuple[str, ...],
    precondition_refs: tuple[str, ...] = (),
    incompatibility_refs: tuple[str, ...] = (),
    dependency_operation_refs: tuple[str, ...] = (),
    positive_eval_refs: tuple[str, ...],
    negative_eval_refs: tuple[str, ...],
    ambiguity_eval_refs: tuple[str, ...],
    adversarial_eval_refs: tuple[str, ...],
    provenance_ref: str,
    review_ref: str,
) -> CapabilityOperationSchema:
    return CapabilityOperationSchema(
        operation_id=operation_id,
        operation_version=operation_version,
        capability_id=manifest.id,
        capability_version=manifest.version,
        operator_summary=operator_summary,
        aliases=aliases,
        effect_class=manifest.side_effects,
        risk_class=manifest.risk_level,
        input_schema=manifest.input_schema,
        output_schema=manifest.output_schema,
        precondition_refs=precondition_refs,
        incompatibility_refs=incompatibility_refs,
        dependency_operation_refs=dependency_operation_refs,
        positive_eval_refs=positive_eval_refs,
        negative_eval_refs=negative_eval_refs,
        ambiguity_eval_refs=ambiguity_eval_refs,
        adversarial_eval_refs=adversarial_eval_refs,
        provenance_ref=provenance_ref,
        review_ref=review_ref,
    )


def _expected_rollback_posture(manifest: CapabilityManifest) -> str:
    if manifest.rollback_supported:
        return "supported"
    if manifest.side_effects in {SideEffectLevel.none, SideEffectLevel.read}:
        return "not_applicable"
    return "required_but_unavailable"


def _operation_schema_fingerprint(operation: CapabilityOperationSchema) -> str:
    return _fingerprint(
        operation.model_dump(mode="json"),
        prefix="operation-schema-ref:taw01",
    )


def build_capability_awareness_catalog(
    registry: CapabilityRegistry,
    *,
    operation_schemas: Iterable[CapabilityOperationSchema],
    bindings: Iterable[CapabilityAwarenessBinding],
    catalog_epoch_ref: str,
    availability_epoch_ref: str,
    generated_at_epoch_seconds: int,
    expires_at_epoch_seconds: int,
) -> CapabilityAwarenessCatalog:
    operations = tuple(operation_schemas)
    evidence_bindings = tuple(bindings)
    if not operations:
        raise ValueError("at least one operation schema is required")
    operation_ids = [item.operation_id for item in operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("operation schemas must not contain duplicate operation IDs")
    binding_ids = [item.operation_id for item in evidence_bindings]
    if len(binding_ids) != len(set(binding_ids)):
        raise ValueError("awareness bindings must not contain duplicate operation IDs")
    if set(operation_ids) != set(binding_ids):
        raise ValueError("every operation requires exactly one awareness binding")
    binding_by_id = {item.operation_id: item for item in evidence_bindings}
    envelopes: list[CapabilityAwarenessEnvelope] = []
    for operation in sorted(
        operations, key=lambda item: (item.capability_id, item.operation_id)
    ):
        try:
            manifest = registry.load_manifest(operation.capability_id)
        except KeyError as exc:
            raise ValueError("operation references an unregistered capability") from exc
        binding = binding_by_id[operation.operation_id]
        if operation.capability_version != manifest.version:
            raise ValueError("operation capability version does not match the registry")
        if _EFFECT_RANK[operation.effect_class] > _EFFECT_RANK[manifest.side_effects]:
            raise ValueError("operation effect exceeds its registered capability")
        if _RISK_RANK[operation.risk_class] > _RISK_RANK[manifest.risk_level]:
            raise ValueError("operation risk exceeds its registered capability")
        if (
            operation.input_schema != manifest.input_schema
            or operation.output_schema != manifest.output_schema
        ):
            raise ValueError("operation schemas do not match the registered capability")
        if binding.rollback_posture != _expected_rollback_posture(manifest):
            raise ValueError("rollback posture contradicts the registered capability")
        if bool(manifest.approval_required) != manifest.safety.approval_required:
            raise ValueError(
                "approval posture contradicts the registered capability safety policy"
            )
        if operation.effect_class in {SideEffectLevel.none, SideEffectLevel.read}:
            if (
                not manifest.approval_required
                and binding.authority_lane_status != "not_applicable"
            ):
                raise ValueError(
                    "read/no-effect operations without approval cannot claim an authority lane"
                )
            if (
                manifest.approval_required
                and binding.authority_lane_status == "not_applicable"
            ):
                raise ValueError(
                    "approval-required operations need an authority-lane posture"
                )
        elif binding.authority_lane_status == "not_applicable":
            raise ValueError(
                "mutating operations require an explicit authority-lane posture"
            )
        approval_class = (
            "exact_approval_required"
            if bool(manifest.approval_required)
            else "not_required"
        )
        required_refs, optional_refs = _input_field_refs(
            operation.operation_id, operation.input_schema
        )
        payload: dict[str, Any] = {
            "schema_version": "uaa-taw01-capability-awareness-envelope.v1",
            "contract_ref": TAW01_CONTRACT_REF,
            "generator_ref": TAW01_GENERATOR_REF,
            "capability_id": manifest.id,
            "capability_version": manifest.version,
            "operation_id": operation.operation_id,
            "operation_version": operation.operation_version,
            "operator_summary": operation.operator_summary,
            "aliases": operation.aliases,
            "effect_class": operation.effect_class,
            "risk_class": operation.risk_class,
            "authority_class": manifest.authority_level,
            "approval_class": approval_class,
            "required_input_field_refs": required_refs,
            "optional_input_field_refs": optional_refs,
            "required_input_schema_fingerprint_ref": _schema_fingerprint(
                _input_partition_schema(
                    operation.input_schema, required_partition=True
                ),
                kind="required-input",
            ),
            "optional_input_schema_fingerprint_ref": _schema_fingerprint(
                _input_partition_schema(
                    operation.input_schema, required_partition=False
                ),
                kind="optional-input",
            ),
            "output_schema_fingerprint_ref": _schema_fingerprint(
                operation.output_schema, kind="output"
            ),
            "operation_schema_fingerprint_ref": _operation_schema_fingerprint(
                operation
            ),
            "precondition_refs": operation.precondition_refs,
            "incompatibility_refs": operation.incompatibility_refs,
            "dependency_operation_refs": operation.dependency_operation_refs,
            "health_status": binding.health_status,
            "availability_ref": binding.availability_ref,
            "policy_decision_status": binding.policy_decision_status,
            "policy_snapshot_ref": binding.policy_snapshot_ref,
            "authority_lane_status": binding.authority_lane_status,
            "authority_lane_ref": binding.authority_lane_ref,
            "safe_disable_ref": binding.safe_disable_ref,
            "rollback_posture": binding.rollback_posture,
            "rollback_ref": binding.rollback_ref,
            "receipt_required": manifest.receipt_required,
            "terminal_proof_contract_ref": binding.terminal_proof_contract_ref,
            "expected_terminal_status_refs": binding.expected_terminal_status_refs,
            "positive_eval_refs": operation.positive_eval_refs,
            "negative_eval_refs": operation.negative_eval_refs,
            "ambiguity_eval_refs": operation.ambiguity_eval_refs,
            "adversarial_eval_refs": operation.adversarial_eval_refs,
            "provenance_ref": operation.provenance_ref,
            "review_ref": operation.review_ref,
            "catalog_epoch_ref": catalog_epoch_ref,
            "availability_epoch_ref": availability_epoch_ref,
            "generated_at_epoch_seconds": generated_at_epoch_seconds,
            "expires_at_epoch_seconds": expires_at_epoch_seconds,
            "raw_operator_content_persisted": False,
            "raw_model_content_persisted": False,
            "model_call_performed": False,
            "provider_call_performed": False,
            "execution_enabled": False,
            "authority_granted": False,
        }
        payload["envelope_fingerprint_ref"] = _fingerprint(
            payload, prefix="awareness-envelope-ref:taw01"
        )
        envelopes.append(CapabilityAwarenessEnvelope.model_validate(payload))
    catalog_payload: dict[str, Any] = {
        "schema_version": "uaa-taw01-capability-awareness-catalog.v1",
        "contract_ref": TAW01_CONTRACT_REF,
        "catalog_epoch_ref": catalog_epoch_ref,
        "availability_epoch_ref": availability_epoch_ref,
        "policy_snapshot_ref": evidence_bindings[0].policy_snapshot_ref,
        "generated_at_epoch_seconds": generated_at_epoch_seconds,
        "expires_at_epoch_seconds": expires_at_epoch_seconds,
        "envelopes": tuple(envelopes),
        "raw_operator_content_persisted": False,
        "raw_model_content_persisted": False,
        "model_call_performed": False,
        "provider_call_performed": False,
        "execution_enabled": False,
        "authority_granted": False,
    }
    if any(
        binding.policy_snapshot_ref != catalog_payload["policy_snapshot_ref"]
        for binding in evidence_bindings
    ):
        raise ValueError("awareness bindings must use one exact policy snapshot")
    catalog_payload["catalog_fingerprint_ref"] = _fingerprint(
        {
            key: (
                [item.model_dump(mode="json") for item in value]
                if key == "envelopes"
                else value
            )
            for key, value in catalog_payload.items()
        },
        prefix="awareness-catalog-ref:taw01",
    )
    return CapabilityAwarenessCatalog.model_validate(catalog_payload)


def validate_capability_awareness_catalog(
    catalog: CapabilityAwarenessCatalog | Mapping[str, Any],
    *,
    expected_catalog_epoch_ref: str,
    expected_availability_epoch_ref: str,
    expected_policy_snapshot_ref: str,
    observed_at_epoch_seconds: int,
) -> CapabilityAwarenessCatalog:
    if not isinstance(observed_at_epoch_seconds, int) or isinstance(
        observed_at_epoch_seconds, bool
    ):
        raise ValueError("observed time must be an integer epoch second")
    if observed_at_epoch_seconds < 0 or not math.isfinite(observed_at_epoch_seconds):
        raise ValueError("observed time must be non-negative and finite")
    validated = (
        catalog
        if isinstance(catalog, CapabilityAwarenessCatalog)
        else CapabilityAwarenessCatalog.model_validate(dict(catalog))
    )
    if validated.catalog_epoch_ref != expected_catalog_epoch_ref:
        raise ValueError("awareness catalog epoch is stale or substituted")
    if validated.availability_epoch_ref != expected_availability_epoch_ref:
        raise ValueError("awareness availability epoch is stale or substituted")
    if validated.policy_snapshot_ref != expected_policy_snapshot_ref:
        raise ValueError("awareness policy snapshot is stale or substituted")
    if observed_at_epoch_seconds > validated.expires_at_epoch_seconds:
        raise ValueError("awareness catalog is stale")
    return validated


__all__ = [
    "CapabilityAwarenessBinding",
    "CapabilityAwarenessCatalog",
    "CapabilityAwarenessEnvelope",
    "CapabilityOperationSchema",
    "TAW01_CONTRACT_REF",
    "TAW01_GENERATOR_REF",
    "build_capability_awareness_catalog",
    "operation_schema_from_manifest",
    "validate_capability_awareness_catalog",
]
