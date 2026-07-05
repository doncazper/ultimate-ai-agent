from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    RuntimeInvocationRecord,
    RuntimeInvocationStatus,
)
from ultimate_ai_agent.core.time import utc_now


RUNTIME_ACTION_EVIDENCE_CONTRACT_REF = (
    "contract-ref:governed-runtime-action-signed-evidence:v1"
)
RUNTIME_ACTION_EVIDENCE_VERIFIER_REF = (
    "verifier-ref:governed-runtime-action-signed-evidence"
)
RUNTIME_ACTION_EVIDENCE_VERIFIER_VERSION_REF = (
    "verifier-version-ref:governed-runtime-action-signed-evidence-v1"
)
RUNTIME_ACTION_EVIDENCE_SIGNATURE_SCHEME_REF = (
    "signature-scheme-ref:local-sha256-envelope-v1"
)
RUNTIME_ACTION_EVIDENCE_CANONICAL_JSON_REF = (
    "canonical-json-ref:runtime-action-signed-evidence-v1"
)

_REDACTION_FLAG_FIELDS = (
    "raw_prompt_persisted",
    "raw_response_persisted",
    "raw_provider_payload_persisted",
    "raw_command_output_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "environment_persisted",
    "credential_material_persisted",
    "sensitive_material_persisted",
)
_DENIED_AUTHORITY_FLAG_FIELDS = (
    "unrestricted_shell_execution_performed",
    "browser_automation_performed",
    "connector_write_performed",
    "plugin_runtime_import_performed",
    "remote_execution_performed",
    "provider_model_call_performed",
    "production_authority_performed",
)
_HASH_FIELDS = (
    "schema_version",
    "contract_ref",
    "envelope_ref",
    "invocation_ref",
    "receipt_ref",
    "action_envelope_ref",
    "exact_scope_ref",
    "approval_ref",
    "approval_validated",
    "approval_status",
    "policy_decision_ref",
    "payload_fingerprint_ref",
    "route_decision_binding_ref",
    "action_kind",
    "command_intent",
    "side_effect_class",
    "invocation_idempotency_ref",
    "approval_idempotency_ref",
    "replay_count",
    "receipt_status",
    "execution_performed",
    "command_execution_performed",
    "rollback_ref",
    "safe_disable_ref",
    "safe_disable_posture_ref",
    "safe_disable_active",
    "artifact_hash_refs",
    "evidence_refs",
    "blocked_reason_refs",
    "blocked_authority_refs",
    "redactions_applied",
    "canonical_json_ref",
    "verifier_ref",
    "verifier_version_ref",
    "signature_scheme_ref",
    "issued_at",
    "safe_refs_only",
    *_REDACTION_FLAG_FIELDS,
    *_DENIED_AUTHORITY_FLAG_FIELDS,
)
_REQUIRED_FIELDS = (
    *_HASH_FIELDS,
    "envelope_hash_ref",
    "signed_envelope_ref",
)


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, list):
        return [_normalize_for_hash(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_for_hash(item) for key, item in value.items()}
    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _normalize_for_hash(dict(payload)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _hash_ref(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


def _hash_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {field: _normalize_for_hash(payload[field]) for field in _HASH_FIELDS}


def _envelope_hash_ref(payload: Mapping[str, Any]) -> str:
    return _hash_ref("runtime-action-evidence-hash-ref", _hash_payload(payload))


def _signed_envelope_ref(
    *,
    envelope_hash_ref: str,
    verifier_version_ref: str,
    signature_scheme_ref: str,
) -> str:
    return _hash_ref(
        "runtime-action-signed-envelope-ref",
        {
            "envelope_hash_ref": envelope_hash_ref,
            "signature_scheme_ref": signature_scheme_ref,
            "verifier_version_ref": verifier_version_ref,
        },
    )


def _missing_field_ref(field_name: str) -> str:
    return f"missing-field-ref:runtime-action-evidence:{field_name.replace('_', '-')}"


def _route_decision_binding_ref(record: RuntimeInvocationRecord) -> str:
    return _hash_ref(
        "route-decision-binding-ref",
        {
            "invocation_ref": record.invocation_ref,
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
    )


def _error_category_ref(error_category: str | None) -> str | None:
    if not error_category:
        return None
    validate_safe_execution_text(error_category, "error_category")
    normalized = error_category.lower().replace("_", "-")
    if normalized.startswith("runtime-command-"):
        normalized = normalized.removeprefix("runtime-command-")
    return f"blocked-state:runtime-command-{normalized}"


class RuntimeActionSignedEvidenceEnvelope(BaseModel):
    schema_version: str = "governed_runtime_action_signed_evidence_envelope.v1"
    contract_ref: str = RUNTIME_ACTION_EVIDENCE_CONTRACT_REF
    envelope_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    exact_scope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_validated: bool = False
    approval_status: str = Field(..., min_length=1, max_length=120)
    policy_decision_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    route_decision_binding_ref: str = Field(..., min_length=1)
    action_kind: str = "runtime-allowlisted-command"
    command_intent: str | None = None
    side_effect_class: Literal[
        "none",
        "validation_only",
        "local_dev_workspace_only",
        "governed_network_read_only",
    ] = "local_dev_workspace_only"
    invocation_idempotency_ref: str = Field(..., min_length=1)
    approval_idempotency_ref: str = Field(..., min_length=1)
    replay_count: int = Field(default=0, ge=0)
    receipt_status: str = Field(..., min_length=1, max_length=120)
    execution_performed: bool = False
    command_execution_performed: bool = False
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    safe_disable_posture_ref: str = Field(..., min_length=1)
    safe_disable_active: bool = False
    artifact_hash_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS))
    canonical_json_ref: str = RUNTIME_ACTION_EVIDENCE_CANONICAL_JSON_REF
    verifier_ref: str = RUNTIME_ACTION_EVIDENCE_VERIFIER_REF
    verifier_version_ref: str = RUNTIME_ACTION_EVIDENCE_VERIFIER_VERSION_REF
    signature_scheme_ref: str = RUNTIME_ACTION_EVIDENCE_SIGNATURE_SCHEME_REF
    issued_at: datetime = Field(default_factory=utc_now)
    envelope_hash_ref: str = Field(..., min_length=1)
    signed_envelope_ref: str = Field(..., min_length=1)
    safe_refs_only: bool = True
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_command_output_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    environment_persisted: bool = False
    credential_material_persisted: bool = False
    sensitive_material_persisted: bool = False
    unrestricted_shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    connector_write_performed: bool = False
    plugin_runtime_import_performed: bool = False
    remote_execution_performed: bool = False
    provider_model_call_performed: bool = False
    production_authority_performed: bool = False
    public_notarization_enabled: bool = False
    signing_key_material_persisted: bool = False
    verifier_only_local_hash_signature: bool = True
    safe_summary: str = (
        "Runtime action signed evidence stores safe refs, stable hashes, "
        "approval posture, receipt refs, and redacted execution metadata only."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "RuntimeActionSignedEvidenceEnvelope":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.envelope_ref, "envelope_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.action_envelope_ref, "action_envelope_ref"),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.approval_ref, "approval_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.route_decision_binding_ref, "route_decision_binding_ref"),
            (self.invocation_idempotency_ref, "invocation_idempotency_ref"),
            (self.approval_idempotency_ref, "approval_idempotency_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
            (self.canonical_json_ref, "canonical_json_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.verifier_version_ref, "verifier_version_ref"),
            (self.signature_scheme_ref, "signature_scheme_ref"),
            (self.envelope_hash_ref, "envelope_hash_ref"),
            (self.signed_envelope_ref, "signed_envelope_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for ref in [
            *self.artifact_hash_refs,
            *self.evidence_refs,
            *self.blocked_reason_refs,
            *self.blocked_authority_refs,
        ]:
            validate_execution_ref(ref, "runtime_action_evidence_ref")
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.approval_status, "approval_status"),
            (self.action_kind, "action_kind"),
            (self.command_intent or "not_applicable", "command_intent"),
            (self.side_effect_class, "side_effect_class"),
            (self.receipt_status, "receipt_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for redaction_ref in self.redactions_applied:
            validate_safe_execution_text(redaction_ref, "redaction")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_SAFE_REFS_REQUIRED")
        if any(getattr(self, field) for field in _REDACTION_FLAG_FIELDS):
            raise ValueError("RUNTIME_ACTION_EVIDENCE_RAW_OR_SENSITIVE_PERSISTENCE_DENIED")
        if any(getattr(self, field) for field in _DENIED_AUTHORITY_FLAG_FIELDS):
            raise ValueError("RUNTIME_ACTION_EVIDENCE_DENIED_AUTHORITY_PERFORMED")
        if self.public_notarization_enabled:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_PUBLIC_NOTARIZATION_DENIED")
        if self.signing_key_material_persisted:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_SIGNING_KEY_PERSISTENCE_DENIED")
        if self.execution_performed and not self.approval_validated:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_APPROVAL_VALIDATION_REQUIRED")
        if self.command_execution_performed and not self.execution_performed:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_COMMAND_EXECUTION_FLAG_DRIFT")
        if self.execution_performed and self.receipt_status != RuntimeInvocationStatus.receipt_recorded.value:
            raise ValueError("RUNTIME_ACTION_EVIDENCE_RECEIPT_RECORDED_STATUS_REQUIRED")
        if not self.envelope_hash_ref.startswith("runtime-action-evidence-hash-ref:sha256:"):
            raise ValueError("RUNTIME_ACTION_EVIDENCE_HASH_REF_REQUIRED")
        if not self.signed_envelope_ref.startswith(
            "runtime-action-signed-envelope-ref:sha256:"
        ):
            raise ValueError("RUNTIME_ACTION_EVIDENCE_SIGNED_REF_REQUIRED")
        return self


class RuntimeActionSignedEvidenceVerificationResult(BaseModel):
    schema_version: str = "governed_runtime_action_signed_evidence_verification.v1"
    verifier_ref: str = RUNTIME_ACTION_EVIDENCE_VERIFIER_REF
    verifier_version_ref: str = RUNTIME_ACTION_EVIDENCE_VERIFIER_VERSION_REF
    envelope_ref: str = "runtime-action-evidence-envelope-ref:missing"
    verification_status: Literal["passed", "failed"]
    offline_verification_performed: bool = True
    required_fields_present: bool
    envelope_hash_valid: bool
    signed_envelope_ref_valid: bool
    redaction_status_valid: bool
    denied_authority_status_valid: bool
    tamper_detected: bool
    safe_refs_only: bool
    input_path_echoed: bool = False
    missing_field_refs: list[str] = Field(default_factory=list)
    failure_reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = "Runtime action signed evidence was verified offline using safe refs only."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RuntimeActionSignedEvidenceVerificationResult":
        for value, field_name in [
            (self.verifier_ref, "verifier_ref"),
            (self.verifier_version_ref, "verifier_version_ref"),
            (self.envelope_ref, "envelope_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for ref in [
            *self.missing_field_refs,
            *self.failure_reason_refs,
            *self.evidence_refs,
        ]:
            validate_execution_ref(ref, "verification_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        return self


def build_runtime_action_signed_evidence(
    record: RuntimeInvocationRecord,
) -> RuntimeActionSignedEvidenceEnvelope:
    if record.receipt is None:
        raise ValueError("RUNTIME_ACTION_EVIDENCE_RECEIPT_REQUIRED")
    if record.action_inbox_envelope is None:
        raise ValueError("RUNTIME_ACTION_EVIDENCE_ACTION_ENVELOPE_REQUIRED")
    receipt = record.receipt
    envelope = record.action_inbox_envelope
    metadata = receipt.command_receipt_metadata
    issued_at = receipt.created_at
    error_ref = _error_category_ref(metadata.error_category if metadata else None)
    evidence_refs = list(
        dict.fromkeys(
            [
                *envelope.evidence_refs,
                *receipt.evidence_refs,
                "evidence-ref:governed-runtime-action-signed-evidence",
            ]
        )
    )
    blocked_authority_refs = list(
        dict.fromkeys([*receipt.blocked_authority_refs])
    )
    blocked_reason_refs = list(
        dict.fromkeys(
            [
                *envelope.blocked_reason_refs,
                *([error_ref] if error_ref is not None else []),
            ]
        )
    )
    base: dict[str, Any] = {
        "schema_version": "governed_runtime_action_signed_evidence_envelope.v1",
        "contract_ref": RUNTIME_ACTION_EVIDENCE_CONTRACT_REF,
        "envelope_ref": _hash_ref(
            "runtime-action-evidence-envelope-ref",
            {
                "invocation_ref": record.invocation_ref,
                "receipt_ref": receipt.receipt_ref,
                "action_envelope_ref": envelope.action_envelope_ref,
            },
        ),
        "invocation_ref": record.invocation_ref,
        "receipt_ref": receipt.receipt_ref,
        "action_envelope_ref": envelope.action_envelope_ref,
        "exact_scope_ref": envelope.exact_scope_ref,
        "approval_ref": envelope.approval_ref,
        "approval_validated": envelope.approval_validated,
        "approval_status": str(envelope.status),
        "policy_decision_ref": record.policy_decision.policy_decision_ref,
        "payload_fingerprint_ref": record.payload_fingerprint_ref,
        "route_decision_binding_ref": _route_decision_binding_ref(record),
        "action_kind": "runtime-allowlisted-command",
        "command_intent": str(envelope.command_intent) if envelope.command_intent else None,
        "side_effect_class": "local_dev_workspace_only",
        "invocation_idempotency_ref": record.idempotency_ref,
        "approval_idempotency_ref": envelope.idempotency_ref,
        "replay_count": record.replay_count,
        "receipt_status": str(receipt.invocation_status),
        "execution_performed": receipt.execution_performed,
        "command_execution_performed": receipt.command_execution_performed,
        "rollback_ref": envelope.rollback_ref,
        "safe_disable_ref": envelope.safe_disable_ref,
        "safe_disable_posture_ref": envelope.safe_disable_posture_ref,
        "safe_disable_active": bool(receipt.safe_disable.active or record.safe_disable.active),
        "artifact_hash_refs": [
            artifact.artifact_ref for artifact in receipt.artifact_refs
        ],
        "evidence_refs": evidence_refs,
        "blocked_reason_refs": blocked_reason_refs,
        "blocked_authority_refs": blocked_authority_refs,
        "redactions_applied": list(receipt.redactions_applied),
        "canonical_json_ref": RUNTIME_ACTION_EVIDENCE_CANONICAL_JSON_REF,
        "verifier_ref": RUNTIME_ACTION_EVIDENCE_VERIFIER_REF,
        "verifier_version_ref": RUNTIME_ACTION_EVIDENCE_VERIFIER_VERSION_REF,
        "signature_scheme_ref": RUNTIME_ACTION_EVIDENCE_SIGNATURE_SCHEME_REF,
        "issued_at": issued_at,
        "safe_refs_only": True,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "raw_provider_payload_persisted": False,
        "raw_command_output_persisted": bool(
            metadata.command_output_persisted if metadata else False
        ),
        "raw_log_persisted": False,
        "raw_local_path_persisted": bool(metadata.cwd_persisted if metadata else False),
        "environment_persisted": bool(metadata.environment_persisted if metadata else False),
        "credential_material_persisted": False,
        "sensitive_material_persisted": False,
        "unrestricted_shell_execution_performed": bool(metadata.shell_used if metadata else False),
        "browser_automation_performed": receipt.browser_automation_performed,
        "connector_write_performed": receipt.connector_write_performed,
        "plugin_runtime_import_performed": False,
        "remote_execution_performed": False,
        "provider_model_call_performed": receipt.model_call_performed,
        "production_authority_performed": False,
    }
    envelope_hash_ref = _envelope_hash_ref(base)
    return RuntimeActionSignedEvidenceEnvelope(
        **base,
        envelope_hash_ref=envelope_hash_ref,
        signed_envelope_ref=_signed_envelope_ref(
            envelope_hash_ref=envelope_hash_ref,
            verifier_version_ref=RUNTIME_ACTION_EVIDENCE_VERIFIER_VERSION_REF,
            signature_scheme_ref=RUNTIME_ACTION_EVIDENCE_SIGNATURE_SCHEME_REF,
        ),
    )


def verify_runtime_action_signed_evidence(
    envelope: Mapping[str, Any] | RuntimeActionSignedEvidenceEnvelope,
) -> RuntimeActionSignedEvidenceVerificationResult:
    payload = (
        envelope.model_dump(mode="json")
        if isinstance(envelope, RuntimeActionSignedEvidenceEnvelope)
        else dict(envelope)
    )
    missing_fields = [field for field in _REQUIRED_FIELDS if field not in payload]
    required_fields_present = not missing_fields
    envelope_ref = str(
        payload.get("envelope_ref", "runtime-action-evidence-envelope-ref:missing")
    )
    redaction_status_valid = bool(payload.get("safe_refs_only") is True) and not any(
        bool(payload.get(field)) for field in _REDACTION_FLAG_FIELDS
    )
    denied_authority_status_valid = not any(
        bool(payload.get(field)) for field in _DENIED_AUTHORITY_FLAG_FIELDS
    )

    envelope_hash_valid = False
    signed_envelope_ref_valid = False
    failure_reason_refs: list[str] = []
    if required_fields_present:
        expected_hash_ref = _envelope_hash_ref(payload)
        envelope_hash_valid = payload.get("envelope_hash_ref") == expected_hash_ref
        expected_signed_ref = _signed_envelope_ref(
            envelope_hash_ref=str(payload.get("envelope_hash_ref")),
            verifier_version_ref=str(payload.get("verifier_version_ref")),
            signature_scheme_ref=str(payload.get("signature_scheme_ref")),
        )
        signed_envelope_ref_valid = payload.get("signed_envelope_ref") == expected_signed_ref
    else:
        failure_reason_refs.append(
            "failure-reason-ref:runtime-action-evidence:required-fields-missing"
        )
    if not envelope_hash_valid:
        failure_reason_refs.append(
            "failure-reason-ref:runtime-action-evidence:envelope-hash-invalid"
        )
    if not signed_envelope_ref_valid:
        failure_reason_refs.append(
            "failure-reason-ref:runtime-action-evidence:signed-envelope-invalid"
        )
    if not redaction_status_valid:
        failure_reason_refs.append(
            "failure-reason-ref:runtime-action-evidence:redaction-status-invalid"
        )
    if not denied_authority_status_valid:
        failure_reason_refs.append(
            "failure-reason-ref:runtime-action-evidence:denied-authority-invalid"
        )
    safe_refs_only = bool(payload.get("safe_refs_only") is True)
    verification_status: Literal["passed", "failed"] = (
        "passed"
        if all(
            [
                required_fields_present,
                envelope_hash_valid,
                signed_envelope_ref_valid,
                redaction_status_valid,
                denied_authority_status_valid,
                safe_refs_only,
            ]
        )
        else "failed"
    )
    return RuntimeActionSignedEvidenceVerificationResult(
        envelope_ref=envelope_ref,
        verification_status=verification_status,
        required_fields_present=required_fields_present,
        envelope_hash_valid=envelope_hash_valid,
        signed_envelope_ref_valid=signed_envelope_ref_valid,
        redaction_status_valid=redaction_status_valid,
        denied_authority_status_valid=denied_authority_status_valid,
        tamper_detected=not envelope_hash_valid or not signed_envelope_ref_valid,
        safe_refs_only=safe_refs_only,
        missing_field_refs=[_missing_field_ref(field) for field in missing_fields],
        failure_reason_refs=list(dict.fromkeys(failure_reason_refs)),
        evidence_refs=list(payload.get("evidence_refs", []))
        if isinstance(payload.get("evidence_refs"), list)
        else [],
    )
