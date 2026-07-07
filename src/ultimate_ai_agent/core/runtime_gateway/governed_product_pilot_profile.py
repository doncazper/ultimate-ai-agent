from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.durable_runs import DURABLE_RUN_SCHEMA_VERSION
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_CONTRACT_REF,
    GOVERNED_RUNTIME_IMPLEMENTED_AUTHORITY_REFS,
    GOVERNED_RUNTIME_REDACTIONS,
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
    RuntimeProfile,
    build_default_runtime_capabilities,
)
from ultimate_ai_agent.core.time import utc_now


GOVERNED_PRODUCT_PILOT_PROFILE_CONTRACT_REF = (
    "contract-ref:governed-product-pilot-authority-profile:v1"
)
GOVERNED_PRODUCT_PILOT_PROFILE_REF = "authority-profile-ref:governed-product-pilot:v1"
SEALED_DEFAULT_PROFILE_REF = "authority-profile-ref:sealed-default:v1"
GOVERNED_PRODUCT_PILOT_ROUTE_REF = "GET /api/runtime/governed-product-pilot-profile"
GOVERNED_PRODUCT_PILOT_CLI_REF = "repo-local-command:uaa-runtime-authority-profile"
GOVERNED_PRODUCT_PILOT_VERIFIER_REF = (
    "verifier-ref:governed-product-pilot-authority-profile"
)
GOVERNED_PRODUCT_PILOT_VERIFIER_VERSION_REF = (
    "verifier-version-ref:governed-product-pilot-authority-profile:v1"
)

GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:pilot-broad-autonomy",
    "blocked-authority:pilot-unrestricted-shell-subprocess",
    "blocked-authority:pilot-browser-automation",
    "blocked-authority:pilot-connector-writes",
    "blocked-authority:pilot-remote-execution",
    "blocked-authority:pilot-plugin-runtime-import",
    "blocked-authority:pilot-production-authority",
    "blocked-authority:pilot-public-beta-or-release-claim",
    "blocked-authority:pilot-raw-prompt-response-provider-payload-log-path-sensitive-material-persistence",
)

GOVERNED_PRODUCT_PILOT_PROMOTED_AUTHORITY_REFS = (
    *GOVERNED_RUNTIME_IMPLEMENTED_AUTHORITY_REFS,
    "authority-ref:runtime-action-inbox-focused-pytest-phase-05",
    "authority-ref:runtime-action-inbox-repo-doctor-phase-05",
    "authority-ref:governed-product-pilot-portable-evidence-local-hash-envelope",
    "authority-ref:governed-product-pilot-durable-run-records",
)


def _combined_blocked_authority_refs() -> list[str]:
    return sorted(
        {
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            *GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS,
        }
    )


def _hash_ref(prefix: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:sha256:{digest}"


PORTABLE_EVIDENCE_HASH_FIELDS = (
    "schema_version",
    "envelope_ref",
    "receipt_ref",
    "evidence_ref",
    "action_id",
    "action_ref",
    "side_effect_class",
    "policy_decision_ref",
    "approval_ref",
    "verifier_version_ref",
    "verifier_ref",
    "issued_at",
)

PORTABLE_EVIDENCE_REQUIRED_FIELDS = (
    *PORTABLE_EVIDENCE_HASH_FIELDS,
    "envelope_hash_ref",
    "signed_envelope_ref",
    "signature_scheme_ref",
    "public_notarization_enabled",
    "signing_key_material_persisted",
    "safe_refs_only",
    "raw_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "sensitive_material_persisted",
    "portable_offline_inspection_ready",
)

PORTABLE_EVIDENCE_REDACTION_FIELDS = (
    "public_notarization_enabled",
    "signing_key_material_persisted",
    "raw_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "sensitive_material_persisted",
)


def _normalized_hash_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return value


def _portable_evidence_hash_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field: _normalized_hash_value(payload[field])
        for field in PORTABLE_EVIDENCE_HASH_FIELDS
    }


def _portable_evidence_hash_ref(payload: Mapping[str, Any]) -> str:
    return _hash_ref("hash-ref", _portable_evidence_hash_payload(payload))


def _portable_evidence_signed_ref(
    envelope_hash_ref: str,
    verifier_version_ref: str,
    signature_scheme_ref: str,
) -> str:
    return _hash_ref(
        "signed-envelope-ref",
        {
            "envelope_hash_ref": envelope_hash_ref,
            "signature_scheme_ref": signature_scheme_ref,
            "verifier_version_ref": verifier_version_ref,
        },
    )


def _missing_field_ref(field_name: str) -> str:
    return (
        "missing-field-ref:governed-product-pilot-evidence:"
        f"{field_name.replace('_', '-')}"
    )


class GovernedProductPilotPortableEvidenceEnvelope(BaseModel):
    schema_version: str = "governed_product_pilot_portable_evidence_envelope.v1"
    envelope_ref: str = "evidence-envelope-ref:governed-product-pilot-profile"
    receipt_ref: str = "receipt-ref:governed-product-pilot-profile"
    evidence_ref: str = "evidence-ref:governed-product-pilot-profile"
    action_id: str = "governed-product-pilot-authority-profile"
    action_ref: str = "action-ref:governed-product-pilot-authority-profile"
    side_effect_class: Literal[
        "none",
        "validation_only",
        "local_dev_workspace_only",
        "governed_network_read_only",
    ] = "local_dev_workspace_only"
    policy_decision_ref: str = "policy-decision-ref:governed-product-pilot-profile"
    approval_ref: str = "approval-ref:governed-product-pilot-profile-exact-lanes"
    verifier_version_ref: str = GOVERNED_PRODUCT_PILOT_VERIFIER_VERSION_REF
    verifier_ref: str = GOVERNED_PRODUCT_PILOT_VERIFIER_REF
    issued_at: datetime = Field(default_factory=utc_now)
    envelope_hash_ref: str
    signed_envelope_ref: str
    signature_scheme_ref: str = "signature-scheme-ref:local-sha256-envelope-v1"
    public_notarization_enabled: bool = False
    signing_key_material_persisted: bool = False
    safe_refs_only: bool = True
    raw_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    sensitive_material_persisted: bool = False
    portable_offline_inspection_ready: bool = True
    safe_summary: str = (
        "Portable evidence envelope stores safe refs, hashes, timestamps, policy, "
        "approval, action, side-effect class, and verifier version only."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "GovernedProductPilotPortableEvidenceEnvelope":
        for value, field_name in [
            (self.envelope_ref, "envelope_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.evidence_ref, "evidence_ref"),
            (self.action_ref, "action_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.approval_ref, "approval_ref"),
            (self.verifier_version_ref, "verifier_version_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.envelope_hash_ref, "envelope_hash_ref"),
            (self.signed_envelope_ref, "signed_envelope_ref"),
            (self.signature_scheme_ref, "signature_scheme_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.action_id, "action_id"),
            (self.side_effect_class, "side_effect_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        if not self.envelope_hash_ref.startswith("hash-ref:sha256:"):
            raise ValueError("PILOT_EVIDENCE_HASH_REF_REQUIRED")
        if not self.signed_envelope_ref.startswith("signed-envelope-ref:sha256:"):
            raise ValueError("PILOT_EVIDENCE_SIGNED_REF_REQUIRED")
        if self.public_notarization_enabled:
            raise ValueError("PILOT_EVIDENCE_PUBLIC_NOTARIZATION_DENIED")
        if self.signing_key_material_persisted:
            raise ValueError("PILOT_EVIDENCE_SIGNING_KEY_MATERIAL_PERSISTENCE_DENIED")
        if not self.safe_refs_only:
            raise ValueError("PILOT_EVIDENCE_SAFE_REFS_REQUIRED")
        if any(
            [
                self.raw_payload_persisted,
                self.raw_log_persisted,
                self.raw_local_path_persisted,
                self.sensitive_material_persisted,
            ]
        ):
            raise ValueError("PILOT_EVIDENCE_RAW_OR_SENSITIVE_PERSISTENCE_DENIED")
        return self


class GovernedProductPilotEvidenceVerificationResult(BaseModel):
    schema_version: str = "governed_product_pilot_evidence_verification.v1"
    verifier_ref: str = GOVERNED_PRODUCT_PILOT_VERIFIER_REF
    verifier_version_ref: str = GOVERNED_PRODUCT_PILOT_VERIFIER_VERSION_REF
    envelope_ref: str = "evidence-envelope-ref:governed-product-pilot-profile"
    verification_status: Literal["passed", "failed"]
    offline_verification_performed: bool = True
    required_fields_present: bool
    envelope_hash_valid: bool
    signed_envelope_ref_valid: bool
    redaction_status_valid: bool
    tamper_detected: bool
    safe_refs_only: bool
    input_path_echoed: bool = False
    raw_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    sensitive_material_persisted: bool = False
    missing_field_refs: list[str] = Field(default_factory=list)
    failure_reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_verification_result(
        self,
    ) -> "GovernedProductPilotEvidenceVerificationResult":
        for value, field_name in [
            (self.verifier_ref, "verifier_ref"),
            (self.verifier_version_ref, "verifier_version_ref"),
            (self.envelope_ref, "envelope_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in [
            "missing_field_refs",
            "failure_reason_refs",
            "evidence_refs",
        ]:
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.schema_version, "schema_version")
        validate_safe_execution_text(self.verification_status, "verification_status")
        if not self.offline_verification_performed:
            raise ValueError("PILOT_EVIDENCE_OFFLINE_VERIFICATION_REQUIRED")
        if self.input_path_echoed:
            raise ValueError("PILOT_EVIDENCE_INPUT_PATH_ECHO_DENIED")
        if any(
            [
                self.raw_payload_persisted,
                self.raw_log_persisted,
                self.raw_local_path_persisted,
                self.sensitive_material_persisted,
            ]
        ):
            raise ValueError("PILOT_EVIDENCE_VERIFICATION_RAW_PERSISTENCE_DENIED")
        if self.verification_status == "passed" and not all(
            [
                self.required_fields_present,
                self.envelope_hash_valid,
                self.signed_envelope_ref_valid,
                self.redaction_status_valid,
                self.safe_refs_only,
            ]
        ):
            raise ValueError("PILOT_EVIDENCE_VERIFICATION_PASS_REQUIRES_ALL_CHECKS")
        if self.verification_status == "passed" and (
            self.tamper_detected or self.failure_reason_refs or self.missing_field_refs
        ):
            raise ValueError("PILOT_EVIDENCE_VERIFICATION_PASS_REQUIRES_NO_FAILURES")
        return self


class GovernedProductPilotLane(BaseModel):
    lane_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    status: Literal["implemented", "profile_ready", "blocked"]
    full_strength_goal: str = Field(..., min_length=1, max_length=300)
    repo_safe_status: str = Field(..., min_length=1, max_length=300)
    promotion_path_ref: str = Field(..., min_length=1)
    exact_micro_lane_only: bool = True
    enabled_in_sealed_profile: bool = False
    enabled_in_pilot_profile: bool = True
    execution_capable: bool = False
    read_only_no_op: bool = False
    approval_binding_required: bool = True
    idempotency_required: bool = True
    audit_receipt_required: bool = True
    rollback_or_safe_disable_required: bool = True
    redaction_required: bool = True
    python_core_owned: bool = True
    cli_parity: bool = True
    api_parity: bool = True
    control_center_presentation_only: bool = True
    raw_persistence_allowed: bool = False
    generic_tool_execution_enabled: bool = False
    broad_authority_enabled: bool = False
    route_refs: list[str] = Field(default_factory=list)
    cli_refs: list[str] = Field(default_factory=list)
    core_contract_refs: list[str] = Field(default_factory=list)
    authority_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    test_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=_combined_blocked_authority_refs)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "GovernedProductPilotLane":
        for value, field_name in [
            (self.lane_ref, "lane_ref"),
            (self.promotion_path_ref, "promotion_path_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.title, "title"),
            (self.full_strength_goal, "full_strength_goal"),
            (self.repo_safe_status, "repo_safe_status"),
            (self.status, "status"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for field_name in [
            "cli_refs",
            "core_contract_refs",
            "authority_refs",
            "receipt_refs",
            "evidence_refs",
            "rollback_refs",
            "safe_disable_refs",
            "verifier_refs",
            "test_refs",
            "blocked_authority_refs",
        ]:
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for ref in self.route_refs:
            validate_safe_execution_text(ref, "route_refs")
        if self.enabled_in_sealed_profile:
            raise ValueError("PILOT_LANE_SEALED_PROFILE_MUST_REMAIN_DISABLED")
        if self.enabled_in_pilot_profile and not self.exact_micro_lane_only:
            raise ValueError("PILOT_LANE_EXACT_SCOPE_REQUIRED")
        if (
            self.execution_capable
            and not self.read_only_no_op
            and not self.approval_binding_required
        ):
            raise ValueError("PILOT_EXECUTION_LANE_APPROVAL_BINDING_REQUIRED")
        required = set(GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS)
        if not required.issubset(set(self.blocked_authority_refs)):
            raise ValueError("PILOT_LANE_BLOCKED_AUTHORITY_REFS_REQUIRED")
        if not all(
            [
                self.idempotency_required,
                self.audit_receipt_required,
                self.rollback_or_safe_disable_required,
                self.redaction_required,
                self.python_core_owned,
                self.cli_parity,
                self.api_parity,
                self.control_center_presentation_only,
            ]
        ):
            raise ValueError("PILOT_LANE_GOVERNANCE_PROOF_REQUIRED")
        if self.raw_persistence_allowed:
            raise ValueError("PILOT_LANE_RAW_PERSISTENCE_DENIED")
        if self.generic_tool_execution_enabled or self.broad_authority_enabled:
            raise ValueError("PILOT_LANE_BROAD_AUTHORITY_DENIED")
        return self


class GovernedProductPilotAuthorityProfileReadModel(BaseModel):
    schema_version: str = "governed_product_pilot_authority_profile.v1"
    contract_ref: str = GOVERNED_PRODUCT_PILOT_PROFILE_CONTRACT_REF
    profile_ref: str = GOVERNED_PRODUCT_PILOT_PROFILE_REF
    sealed_default_profile_ref: str = SEALED_DEFAULT_PROFILE_REF
    source: str = "python_core_runtime_gateway_authority_profile"
    status: str = "local_governed_product_pilot_ready"
    active_profile_name: str = "governed-product-pilot"
    default_runtime_profile: RuntimeProfile = RuntimeProfile.sealed
    pilot_runtime_profiles: list[RuntimeProfile] = Field(
        default_factory=lambda: [RuntimeProfile.local_runtime, RuntimeProfile.operator_approved]
    )
    backend_owned: bool = True
    sealed_default_hard_rules_preserved: bool = True
    sealed_profile_deny_by_default: bool = True
    pilot_profile_exact_lane_only: bool = True
    runtime_gateway_required: bool = True
    local_model_output_non_authoritative: bool = True
    control_center_mints_authority: bool = False
    control_center_presentation_only: bool = True
    broad_autonomy_enabled: bool = False
    unrestricted_shell_subprocess_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_writes_enabled: bool = False
    remote_execution_enabled: bool = False
    plugin_runtime_import_enabled: bool = False
    production_authority_enabled: bool = False
    public_beta_or_release_claim_enabled: bool = False
    raw_prompt_response_provider_payload_log_path_persistence_enabled: bool = False
    promoted_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_PRODUCT_PILOT_PROMOTED_AUTHORITY_REFS)
    )
    blocked_authority_refs: list[str] = Field(default_factory=_combined_blocked_authority_refs)
    lanes: list[GovernedProductPilotLane]
    portable_evidence_envelope: GovernedProductPilotPortableEvidenceEnvelope
    durable_orchestration_contract: dict[str, Any]
    route_refs: list[str] = Field(
        default_factory=lambda: [
            GOVERNED_PRODUCT_PILOT_ROUTE_REF,
            "GET /api/runtime/capabilities",
            "GET /api/runtime/invocations",
            "POST /api/runtime/local-model/call",
            "POST /api/runtime/command/run",
            "POST /api/runtime/invocations/{id}/approve",
            "POST /api/runtime/invocations/{id}/execute",
            "POST /api/runtime/safe-disable",
        ]
    )
    cli_refs: list[str] = Field(
        default_factory=lambda: [
            GOVERNED_PRODUCT_PILOT_CLI_REF,
            "repo-local-command:uaa-runtime-status",
            "repo-local-command:uaa-runtime-capabilities",
            "repo-local-command:uaa-runtime-invocations",
            "repo-local-command:uaa-runtime-receipts",
            "repo-local-command:uaa-runtime-safe-disable",
            "repo-local-command:uaa-runtime-actions",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [GOVERNED_PRODUCT_PILOT_VERIFIER_REF]
    )
    test_refs: list[str] = Field(
        default_factory=lambda: [
            "test-ref:tests-test-governed-product-pilot-authority-profile",
            "test-ref:tests-test-governed-runtime-contracts",
            "test-ref:tests-test-governed-runtime-api-routes",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "doc-ref:docs-control-center-governed-product-pilot-authority-profile",
            "doc-ref:docs-control-center-authority-graduation-board",
            "doc-ref:docs-roadmap-product-release-truth-packet",
        ]
    )
    generated_at: datetime = Field(default_factory=utc_now)
    safe_summary: str = (
        "Governed Product Pilot profile keeps sealed default denial and exposes "
        "only lease-scoped local RuntimeGateway capabilities, receipts, evidence, "
        "and durable run posture."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_profile(self) -> "GovernedProductPilotAuthorityProfileReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.profile_ref, "profile_ref"),
            (self.sealed_default_profile_ref, "sealed_default_profile_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.status, "status"),
            (self.active_profile_name, "active_profile_name"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for field_name in [
            "promoted_authority_refs",
            "blocked_authority_refs",
            "cli_refs",
            "verifier_refs",
            "test_refs",
            "docs_refs",
        ]:
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for ref in self.route_refs:
            validate_safe_execution_text(ref, "route_refs")
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redactions_applied")
        if self.default_runtime_profile != RuntimeProfile.sealed.value:
            raise ValueError("PILOT_DEFAULT_PROFILE_MUST_BE_SEALED")
        if not all(
            [
                self.backend_owned,
                self.sealed_default_hard_rules_preserved,
                self.sealed_profile_deny_by_default,
                self.pilot_profile_exact_lane_only,
                self.runtime_gateway_required,
                self.local_model_output_non_authoritative,
                self.control_center_presentation_only,
            ]
        ):
            raise ValueError("PILOT_PROFILE_GOVERNANCE_POSTURE_REQUIRED")
        if any(
            [
                self.control_center_mints_authority,
                self.broad_autonomy_enabled,
                self.unrestricted_shell_subprocess_enabled,
                self.browser_automation_enabled,
                self.connector_writes_enabled,
                self.remote_execution_enabled,
                self.plugin_runtime_import_enabled,
                self.production_authority_enabled,
                self.public_beta_or_release_claim_enabled,
                self.raw_prompt_response_provider_payload_log_path_persistence_enabled,
            ]
        ):
            raise ValueError("PILOT_PROFILE_BROAD_AUTHORITY_DENIED")
        required = set(GOVERNED_PRODUCT_PILOT_REQUIRED_BLOCKED_AUTHORITY_REFS)
        if not required.issubset(set(self.blocked_authority_refs)):
            raise ValueError("PILOT_PROFILE_BLOCKED_AUTHORITY_REFS_REQUIRED")
        if len(self.lanes) < 4:
            raise ValueError("PILOT_PROFILE_CORE_LANES_REQUIRED")
        if not self.portable_evidence_envelope.portable_offline_inspection_ready:
            raise ValueError("PILOT_EVIDENCE_PORTABILITY_REQUIRED")
        validate_safe_execution_text(
            json.dumps(self.durable_orchestration_contract, sort_keys=True),
            "durable_orchestration_contract",
        )
        return self


def build_portable_evidence_envelope() -> GovernedProductPilotPortableEvidenceEnvelope:
    issued_at = utc_now()
    base = {
        "schema_version": "governed_product_pilot_portable_evidence_envelope.v1",
        "envelope_ref": "evidence-envelope-ref:governed-product-pilot-profile",
        "receipt_ref": "receipt-ref:governed-product-pilot-profile",
        "evidence_ref": "evidence-ref:governed-product-pilot-profile",
        "action_id": "governed-product-pilot-authority-profile",
        "action_ref": "action-ref:governed-product-pilot-authority-profile",
        "side_effect_class": "local_dev_workspace_only",
        "policy_decision_ref": "policy-decision-ref:governed-product-pilot-profile",
        "approval_ref": "approval-ref:governed-product-pilot-profile-exact-lanes",
        "verifier_version_ref": GOVERNED_PRODUCT_PILOT_VERIFIER_VERSION_REF,
        "verifier_ref": GOVERNED_PRODUCT_PILOT_VERIFIER_REF,
        "issued_at": issued_at,
    }
    signature_scheme_ref = "signature-scheme-ref:local-sha256-envelope-v1"
    envelope_hash_ref = _portable_evidence_hash_ref(base)
    signed_envelope_ref = _portable_evidence_signed_ref(
        envelope_hash_ref,
        GOVERNED_PRODUCT_PILOT_VERIFIER_VERSION_REF,
        signature_scheme_ref,
    )
    return GovernedProductPilotPortableEvidenceEnvelope(
        **base,
        envelope_hash_ref=envelope_hash_ref,
        signed_envelope_ref=signed_envelope_ref,
        signature_scheme_ref=signature_scheme_ref,
    )


def verify_portable_evidence_envelope(
    envelope: Mapping[str, Any] | GovernedProductPilotPortableEvidenceEnvelope,
) -> GovernedProductPilotEvidenceVerificationResult:
    payload = (
        envelope.model_dump(mode="json")
        if isinstance(envelope, GovernedProductPilotPortableEvidenceEnvelope)
        else dict(envelope)
    )
    missing_fields = [
        field for field in PORTABLE_EVIDENCE_REQUIRED_FIELDS if field not in payload
    ]
    required_fields_present = not missing_fields
    envelope_ref = str(
        payload.get(
            "envelope_ref",
            "evidence-envelope-ref:governed-product-pilot-profile",
        )
    )
    redaction_status_valid = bool(payload.get("safe_refs_only") is True) and not any(
        bool(payload.get(field)) for field in PORTABLE_EVIDENCE_REDACTION_FIELDS
    )

    envelope_hash_valid = False
    signed_envelope_ref_valid = False
    failure_reason_refs: list[str] = []
    if required_fields_present:
        expected_hash_ref = _portable_evidence_hash_ref(payload)
        envelope_hash_valid = payload.get("envelope_hash_ref") == expected_hash_ref
        expected_signed_ref = _portable_evidence_signed_ref(
            str(payload.get("envelope_hash_ref")),
            str(payload.get("verifier_version_ref")),
            str(payload.get("signature_scheme_ref")),
        )
        signed_envelope_ref_valid = (
            payload.get("signed_envelope_ref") == expected_signed_ref
        )
    else:
        failure_reason_refs.append(
            "failure-reason-ref:portable-evidence-required-fields-missing"
        )

    if not envelope_hash_valid:
        failure_reason_refs.append(
            "failure-reason-ref:portable-evidence-envelope-hash-invalid"
        )
    if not signed_envelope_ref_valid:
        failure_reason_refs.append(
            "failure-reason-ref:portable-evidence-signed-envelope-invalid"
        )
    if not redaction_status_valid:
        failure_reason_refs.append(
            "failure-reason-ref:portable-evidence-redaction-status-invalid"
        )

    safe_refs_only = bool(payload.get("safe_refs_only") is True)
    tamper_detected = not envelope_hash_valid or not signed_envelope_ref_valid
    verification_status: Literal["passed", "failed"] = (
        "passed"
        if all(
            [
                required_fields_present,
                envelope_hash_valid,
                signed_envelope_ref_valid,
                redaction_status_valid,
                safe_refs_only,
            ]
        )
        else "failed"
    )
    return GovernedProductPilotEvidenceVerificationResult(
        envelope_ref=envelope_ref,
        verification_status=verification_status,
        required_fields_present=required_fields_present,
        envelope_hash_valid=envelope_hash_valid,
        signed_envelope_ref_valid=signed_envelope_ref_valid,
        redaction_status_valid=redaction_status_valid,
        tamper_detected=tamper_detected,
        safe_refs_only=safe_refs_only,
        missing_field_refs=[_missing_field_ref(field) for field in missing_fields],
        failure_reason_refs=list(dict.fromkeys(failure_reason_refs)),
        evidence_refs=[
            str(payload.get("evidence_ref", "evidence-ref:governed-product-pilot-profile"))
        ],
    )


def _pilot_lanes() -> list[GovernedProductPilotLane]:
    blocked = _combined_blocked_authority_refs()
    return [
        GovernedProductPilotLane(
            lane_ref="lane-ref:governed-product-pilot-live-local-agent-runtime",
            title="Live local agent runtime",
            status="implemented",
            full_strength_goal=(
                "Live local runtime can produce proposal signals for the operator cockpit."
            ),
            repo_safe_status=(
                "RuntimeGateway supports configured loopback local model calls with "
                "non-authoritative output and redacted receipts."
            ),
            promotion_path_ref="promotion-path-ref:runtime-gateway-local-model-loopback",
            execution_capable=True,
            approval_binding_required=True,
            route_refs=[
                "GET /api/runtime/capabilities",
                "POST /api/runtime/local-model/call",
            ],
            cli_refs=[
                "repo-local-command:uaa-runtime-capabilities",
                "repo-local-command:uaa-runtime-status",
            ],
            core_contract_refs=[
                GOVERNED_RUNTIME_CONTRACT_REF,
                "contract-ref:runtime-gateway-local-model-loopback",
            ],
            authority_refs=["authority-ref:runtime-local-model-loopback-phase-03"],
            receipt_refs=["receipt-ref:runtime-local-model-loopback"],
            evidence_refs=["evidence-ref:runtime-local-model-loopback"],
            rollback_refs=["rollback-ref:governed-runtime-pilot:disable-profile"],
            safe_disable_refs=["safe-disable-ref:governed-runtime-pilot"],
            verifier_refs=[GOVERNED_PRODUCT_PILOT_VERIFIER_REF],
            test_refs=["test-ref:tests-test-governed-runtime-contracts"],
            blocked_authority_refs=blocked,
        ),
        GovernedProductPilotLane(
            lane_ref="lane-ref:governed-product-pilot-mature-action-execution",
            title="Mature action execution",
            status="implemented",
            full_strength_goal=(
                "Local action execution runs only implemented authority capabilities "
                "with active lease scope and receipts."
            ),
            repo_safe_status=(
                "Only allowlisted RuntimeGateway command capabilities exist: read-only "
                "git status plus Action Inbox approved focused pytest, repo-verifier, "
                "frontend-check, and repo-doctor under active workspace/execute scope."
            ),
            promotion_path_ref="promotion-path-ref:runtime-command-authority-capabilities",
            execution_capable=True,
            approval_binding_required=True,
            route_refs=[
                "POST /api/runtime/command/run",
                "POST /api/runtime/invocations/{id}/approve",
                "POST /api/runtime/invocations/{id}/execute",
            ],
            cli_refs=[
                "repo-local-command:uaa-runtime-actions",
                "repo-local-command:uaa-runtime-receipts",
            ],
            core_contract_refs=[
                GOVERNED_RUNTIME_CONTRACT_REF,
                "contract-ref:runtime-command-allowlist",
                "contract-ref:runtime-action-inbox-approval-envelope",
            ],
            authority_refs=[
                "authority-ref:runtime-allowlisted-readonly-command-phase-04",
                "authority-ref:runtime-action-inbox-focused-pytest-phase-05",
                "authority-ref:runtime-action-inbox-repo-verifier-phase-05",
                "authority-ref:runtime-action-inbox-frontend-check-phase-05",
                "authority-ref:runtime-action-inbox-repo-doctor-phase-05",
            ],
            receipt_refs=[
                "receipt-ref:runtime-focused-pytest-command",
                "receipt-ref:runtime-repo-verifier-command",
                "receipt-ref:runtime-frontend-check-command",
                "receipt-ref:runtime-repo-doctor-command",
            ],
            evidence_refs=[
                "evidence-ref:runtime-focused-pytest-command",
                "evidence-ref:runtime-repo-verifier-command",
                "evidence-ref:runtime-frontend-check-command",
                "evidence-ref:runtime-repo-doctor-command",
            ],
            rollback_refs=["rollback-ref:governed-runtime-pilot:disable-profile"],
            safe_disable_refs=["safe-disable-ref:governed-runtime-pilot"],
            verifier_refs=[GOVERNED_PRODUCT_PILOT_VERIFIER_REF],
            test_refs=[
                "test-ref:tests-test-governed-runtime-contracts",
                "test-ref:tests-test-governed-runtime-api-routes",
            ],
            blocked_authority_refs=blocked,
        ),
        GovernedProductPilotLane(
            lane_ref="lane-ref:governed-product-pilot-portable-evidence",
            title="Portable evidence envelopes",
            status="profile_ready",
            full_strength_goal=(
                "Receipts can be inspected offline as portable signed evidence envelopes."
            ),
            repo_safe_status=(
                "Local hash envelope contract covers safe refs, policy, approval, "
                "action id, side-effect class, timestamp, and verifier version."
            ),
            promotion_path_ref="promotion-path-ref:portable-evidence-local-hash-envelope",
            execution_capable=False,
            approval_binding_required=True,
            route_refs=[GOVERNED_PRODUCT_PILOT_ROUTE_REF],
            cli_refs=[GOVERNED_PRODUCT_PILOT_CLI_REF],
            core_contract_refs=[
                GOVERNED_PRODUCT_PILOT_PROFILE_CONTRACT_REF,
                "contract-ref:portable-evidence-local-hash-envelope",
            ],
            authority_refs=[
                "authority-ref:governed-product-pilot-portable-evidence-local-hash-envelope"
            ],
            receipt_refs=["receipt-ref:governed-product-pilot-profile"],
            evidence_refs=["evidence-ref:governed-product-pilot-profile"],
            rollback_refs=["rollback-ref:governed-runtime-pilot:disable-profile"],
            safe_disable_refs=["safe-disable-ref:governed-runtime-pilot"],
            verifier_refs=[GOVERNED_PRODUCT_PILOT_VERIFIER_REF],
            test_refs=["test-ref:tests-test-governed-product-pilot-authority-profile"],
            blocked_authority_refs=blocked,
        ),
        GovernedProductPilotLane(
            lane_ref="lane-ref:governed-product-pilot-durable-orchestration",
            title="Durable orchestration",
            status="implemented",
            full_strength_goal=(
                "Runs persist progress, checkpoints, waits, retry posture, and receipts."
            ),
            repo_safe_status=(
                "Durable run records provide local state, checkpoints, blocked and "
                "cancelled states, retry posture, redacted errors, receipts, and evidence refs."
            ),
            promotion_path_ref="promotion-path-ref:durable-run-lifecycle-local-records",
            execution_capable=False,
            approval_binding_required=True,
            route_refs=[
                "GET /control-center/runs/observability",
                "GET /task-decomposition/runs/{run_id}/lifecycle",
            ],
            cli_refs=["repo-local-command:uaa-runtime-status"],
            core_contract_refs=[
                f"contract-ref:{DURABLE_RUN_SCHEMA_VERSION}",
                "contract-ref:run-observability-read-model",
            ],
            authority_refs=["authority-ref:governed-product-pilot-durable-run-records"],
            receipt_refs=["receipt-ref:durable-run-lifecycle"],
            evidence_refs=["evidence-ref:durable-run-lifecycle"],
            rollback_refs=["rollback-ref:durable-run-safe-disable-or-cancel"],
            safe_disable_refs=["safe-disable-ref:governed-runtime-pilot"],
            verifier_refs=[GOVERNED_PRODUCT_PILOT_VERIFIER_REF],
            test_refs=[
                "test-ref:tests-test-durable-run-lifecycle-read-model",
                "test-ref:tests-test-run-observability-surface",
            ],
            blocked_authority_refs=blocked,
        ),
    ]


def build_governed_product_pilot_authority_profile() -> GovernedProductPilotAuthorityProfileReadModel:
    capabilities = build_default_runtime_capabilities()
    durable_orchestration_contract = {
        "schema_version": DURABLE_RUN_SCHEMA_VERSION,
        "source": "python_core_durable_run_lifecycle",
        "local_run_records": True,
        "checkpoints_supported": True,
        "progress_refs_supported": True,
        "approval_wait_states_supported": True,
        "retry_recovery_posture_supported": True,
        "cancellation_and_blocked_states_supported": True,
        "dead_letter_state_supported": True,
        "read_model_status_refs": [
            "run-status-ref:active",
            "run-status-ref:completed",
            "run-status-ref:blocked",
            "run-status-ref:failed",
            "run-status-ref:recovered",
        ],
        "durable_event_log_is_source_of_truth": True,
        "progress_refs_are_source_of_truth": False,
        "resume_requires_exact_lane": True,
        "cancel_requires_exact_lane": True,
        "retry_requires_exact_lane": True,
        "redacted_errors_only": True,
        "raw_payload_storage_allowed": False,
        "production_runtime_authority": False,
    }
    return GovernedProductPilotAuthorityProfileReadModel(
        default_runtime_profile=capabilities.default_profile,
        pilot_runtime_profiles=[RuntimeProfile.local_runtime, RuntimeProfile.operator_approved],
        lanes=_pilot_lanes(),
        portable_evidence_envelope=build_portable_evidence_envelope(),
        durable_orchestration_contract=durable_orchestration_contract,
    )
