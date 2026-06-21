from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


LOCAL_MODEL_PRODUCTION_READINESS_GATE_DOCS = [
    "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_GATE.md",
    "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_BOUNDARY.md",
    "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_RECEIPT_PLAN.md",
    "docs/production/LOCAL_MODEL_PRODUCTION_READINESS_NON_GOALS.md",
    "docs/production/M166_PRODUCTION_AUTHORITY_GATE.md",
]

REQUIRED_M166_EVIDENCE_KINDS = (
    "live_install_run",
    "openwebui_e2e",
    "security_review",
    "packaging",
    "operational_rollback",
    "load_test",
)


class ProductionReadinessEvidenceKind(str, Enum):
    live_install_run = "live_install_run"
    openwebui_e2e = "openwebui_e2e"
    security_review = "security_review"
    packaging = "packaging"
    operational_rollback = "operational_rollback"
    load_test = "load_test"


class ProductionReadinessEvidenceStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    blocked = "blocked"


class ProductionReleaseGateStatus(str, Enum):
    production_authority_granted = "production_authority_granted"
    production_authority_denied = "production_authority_denied"


class _ProductionReleaseGateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ProductionReadinessEvidenceRecord(_ProductionReleaseGateModel):
    evidence_ref: str
    kind: ProductionReadinessEvidenceKind
    source_checkpoint_ref: str = "checkpoint:m165"
    status: ProductionReadinessEvidenceStatus = ProductionReadinessEvidenceStatus.passed
    produced_by_ref: str
    observed_at_ref: str
    safe_summary: str
    metric_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    warning_refs: list[str] = Field(default_factory=list)
    reviewed_live_evidence: bool = False
    reviewed_by_ref: str | None = None
    redacted: bool = True
    safe_refs_only: bool = True
    loopback_only: bool = True
    openwebui_shell_only: bool = True
    openwebui_is_agent_brain: bool = False
    tools_enabled: bool = False
    functions_enabled: bool = False
    streaming_enabled: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    raw_log_included: bool = False
    raw_path_included: bool = False
    username_included: bool = False
    environment_dump_included: bool = False
    secret_included: bool = False
    unsupported_network_used: bool = False
    credential_material_included: bool = False
    production_side_effect_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.evidence_ref, "evidence_ref"),
            (self.source_checkpoint_ref, "source_checkpoint_ref"),
            (self.produced_by_ref, "produced_by_ref"),
            (self.observed_at_ref, "observed_at_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in [*self.metric_refs, *self.blocker_refs, *self.warning_refs]:
            _validate_m61_ref(ref, "evidence_support_ref")
        if self.reviewed_by_ref is not None:
            _validate_m61_ref(self.reviewed_by_ref, "reviewed_by_ref")
        if self.reviewed_live_evidence and self.reviewed_by_ref is None:
            raise ValueError("M166_REVIEWED_BY_REF_REQUIRED")
        _validate_safe_payload(
            {
                "safe_summary": self.safe_summary,
                "metric_refs": self.metric_refs,
                "warning_refs": self.warning_refs,
            }
        )
        return self


class ProductionReleaseGatePolicy(_ProductionReleaseGateModel):
    policy_ref: str = "production-release-gate-policy:m166"
    source_checkpoint_ref: str = "checkpoint:m165"
    required_evidence_kinds: tuple[ProductionReadinessEvidenceKind, ...] = tuple(
        ProductionReadinessEvidenceKind(kind) for kind in REQUIRED_M166_EVIDENCE_KINDS
    )
    exact_scope_required: bool = True
    all_evidence_passed_required: bool = True
    no_blockers_required: bool = True
    redaction_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    rollback_required: bool = True
    production_authority_grant_allowed: bool = True
    production_runtime_authorization_allowed: bool = True
    go_live_authorization_allowed: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_m61_ref(self.source_checkpoint_ref, "source_checkpoint_ref")
        _validate_safe_payload(self.metadata)
        return self


class ProductionReleaseGateRecord(_ProductionReleaseGateModel):
    gate_ref: str
    source_checkpoint_ref: str
    evidence_records: list[ProductionReadinessEvidenceRecord]
    evidence_refs: list[str]
    required_evidence_kinds: list[ProductionReadinessEvidenceKind]
    audit_ref: str
    replay_ref: str
    rollback_plan_ref: str
    release_scope_ref: str
    release_tag_ref: str
    status: ProductionReleaseGateStatus = ProductionReleaseGateStatus.production_authority_granted
    exact_scope_bound: bool = True
    all_evidence_passed: bool = True
    redacted_evidence_only: bool = True
    blockers_cleared: bool = True
    rollback_ready: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_granted: bool = Field(default=True)
    production_runtime_authorized: bool = Field(default=True)
    go_live_authorized: bool = Field(default=True)
    production_deployment_authorized: bool = Field(default=True)
    traffic_routing_authorized: bool = Field(default=True)
    credential_material_exported: bool = False
    raw_prompt_exported: bool = False
    raw_response_exported: bool = False
    raw_provider_payload_exported: bool = False
    raw_local_path_exported: bool = False
    raw_log_exported: bool = False
    unreviewed_dependency_added: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.gate_ref, "gate_ref"),
            (self.source_checkpoint_ref, "source_checkpoint_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.release_scope_ref, "release_scope_ref"),
            (self.release_tag_ref, "release_tag_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.evidence_refs:
            _validate_m61_ref(ref, "evidence_ref")
        if not self.reason_codes:
            raise ValueError("M166_REASON_CODE_REQUIRED")
        _validate_safe_payload({"safe_summary": self.safe_summary, "metadata": self.metadata})
        return self


def build_m166_green_production_readiness_evidence() -> list[ProductionReadinessEvidenceRecord]:
    summaries = {
        ProductionReadinessEvidenceKind.live_install_run: "Live local install and runtime smoke passed with loopback-only local model services.",
        ProductionReadinessEvidenceKind.openwebui_e2e: "OpenWebUI end-to-end shell flow passed against the UAA local gateway with shell-only authority.",
        ProductionReadinessEvidenceKind.security_review: "Security review passed with redaction, loopback, credential, and authority boundaries checked.",
        ProductionReadinessEvidenceKind.packaging: "Packaging review passed for reproducible local release artifacts and dependency inventory.",
        ProductionReadinessEvidenceKind.operational_rollback: "Operational rollback rehearsal passed with previous-known-good preset restoration.",
        ProductionReadinessEvidenceKind.load_test: "Load test passed within latency, crash, memory, and error-rate budgets.",
    }
    records: list[ProductionReadinessEvidenceRecord] = []
    for kind in ProductionReadinessEvidenceKind:
        records.append(
            ProductionReadinessEvidenceRecord(
                evidence_ref=f"production-readiness-evidence:m166:{kind.value}",
                kind=kind,
                produced_by_ref=f"producer-ref:m166:{kind.value}",
                observed_at_ref=f"observed-at-ref:m166:{kind.value}",
                safe_summary=summaries[kind],
                metric_refs=[f"metric-ref:m166:{kind.value}:green"],
            )
        )
    return records


def build_m166_production_release_gate_record(
    *,
    evidence_records: list[ProductionReadinessEvidenceRecord],
    policy: ProductionReleaseGatePolicy | None = None,
) -> ProductionReleaseGateRecord:
    active_policy = validate_m166_production_release_gate_policy(
        policy or ProductionReleaseGatePolicy()
    )
    validated_evidence = [
        validate_m166_production_readiness_evidence_record(record)
        for record in evidence_records
    ]
    required_kinds = list(active_policy.required_evidence_kinds)
    record = ProductionReleaseGateRecord(
        gate_ref="production-release-gate:m166:local-model-layer",
        source_checkpoint_ref=active_policy.source_checkpoint_ref,
        evidence_records=validated_evidence,
        evidence_refs=[record.evidence_ref for record in validated_evidence],
        required_evidence_kinds=required_kinds,
        audit_ref="audit-ref:m166:production-release-gate",
        replay_ref="replay-ref:m166:production-release-gate",
        rollback_plan_ref="rollback-plan-ref:m166:previous-known-good",
        release_scope_ref="release-scope-ref:m166:local-llama-cpp-openwebui",
        release_tag_ref="release-tag-ref:checkpoint-m166",
        exact_scope_bound=active_policy.exact_scope_required,
        all_evidence_passed=active_policy.all_evidence_passed_required,
        redacted_evidence_only=active_policy.redaction_required,
        blockers_cleared=active_policy.no_blockers_required,
        rollback_ready=active_policy.rollback_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        production_authority_granted=active_policy.production_authority_grant_allowed,
        production_runtime_authorized=active_policy.production_runtime_authorization_allowed,
        go_live_authorized=active_policy.go_live_authorization_allowed,
        production_deployment_authorized=active_policy.go_live_authorization_allowed,
        traffic_routing_authorized=active_policy.go_live_authorization_allowed,
        reason_codes=[
            "M166_PRODUCTION_READINESS_GREEN",
            "M166_LIVE_INSTALL_RUN_EVIDENCE_BOUND",
            "M166_OPENWEBUI_E2E_EVIDENCE_BOUND",
            "M166_SECURITY_REVIEW_EVIDENCE_BOUND",
            "M166_PACKAGING_EVIDENCE_BOUND",
            "M166_ROLLBACK_EVIDENCE_BOUND",
            "M166_LOAD_TEST_EVIDENCE_BOUND",
            "M166_PRODUCTION_AUTHORITY_GRANTED",
        ],
        safe_summary=(
            "M166 grants production authority for the local llama.cpp and "
            "OpenWebUI gateway layer only after all required redacted evidence "
            "records pass, blockers are clear, rollback is ready, and audit and "
            "replay refs are bound."
        ),
    )
    return validate_m166_production_release_gate_record(record)


def validate_m166_production_readiness_evidence_record(
    record: ProductionReadinessEvidenceRecord,
) -> ProductionReadinessEvidenceRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ProductionReadinessEvidenceRecord):
        raise ValueError("M166_SECRET_LIKE_EVIDENCE_DENIED")
    validated = ProductionReadinessEvidenceRecord.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m165":
        raise ValueError("M166_SOURCE_CHECKPOINT_M165_REQUIRED")
    if validated.status != ProductionReadinessEvidenceStatus.passed:
        raise ValueError("M166_EVIDENCE_MUST_PASS")
    for field_name, reason in [
        ("redacted", "M166_REDACTED_EVIDENCE_REQUIRED"),
        ("safe_refs_only", "M166_SAFE_REFS_REQUIRED"),
        ("loopback_only", "M166_LOOPBACK_REQUIRED"),
        ("openwebui_shell_only", "M166_OPENWEBUI_SHELL_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("openwebui_is_agent_brain", "M166_OPENWEBUI_AUTHORITY_DENIED"),
        ("tools_enabled", "M166_TOOLS_DENIED"),
        ("functions_enabled", "M166_FUNCTIONS_DENIED"),
        ("streaming_enabled", "M166_STREAMING_DENIED"),
        ("raw_prompt_included", "M166_RAW_PROMPT_DENIED"),
        ("raw_response_included", "M166_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_included", "M166_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_log_included", "M166_RAW_LOG_DENIED"),
        ("raw_path_included", "M166_RAW_PATH_DENIED"),
        ("username_included", "M166_USERNAME_DENIED"),
        ("environment_dump_included", "M166_ENV_DUMP_DENIED"),
        ("secret_included", "M166_SECRET_DENIED"),
        ("unsupported_network_used", "M166_UNSUPPORTED_NETWORK_DENIED"),
        ("credential_material_included", "M166_CREDENTIAL_MATERIAL_DENIED"),
        ("production_side_effect_performed", "M166_SIDE_EFFECT_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    if validated.blocker_refs:
        raise ValueError("M166_BLOCKERS_MUST_BE_EMPTY")
    return validated


def validate_m166_production_release_gate_policy(
    policy: ProductionReleaseGatePolicy | dict[str, Any],
) -> ProductionReleaseGatePolicy:
    payload = dict(policy) if isinstance(policy, dict) else _model_payload(policy)
    validated = ProductionReleaseGatePolicy.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m165":
        raise ValueError("M166_SOURCE_CHECKPOINT_M165_REQUIRED")
    required = tuple(ProductionReadinessEvidenceKind(kind) for kind in REQUIRED_M166_EVIDENCE_KINDS)
    if tuple(validated.required_evidence_kinds) != required:
        raise ValueError("M166_REQUIRED_EVIDENCE_KINDS_EXACT")
    for field_name, reason in [
        ("exact_scope_required", "M166_EXACT_SCOPE_REQUIRED"),
        ("all_evidence_passed_required", "M166_ALL_EVIDENCE_PASS_REQUIRED"),
        ("no_blockers_required", "M166_NO_BLOCKERS_REQUIRED"),
        ("redaction_required", "M166_REDACTION_REQUIRED"),
        ("audit_required", "M166_AUDIT_REQUIRED"),
        ("replay_required", "M166_REPLAY_REQUIRED"),
        ("rollback_required", "M166_ROLLBACK_REQUIRED"),
        ("production_authority_grant_allowed", "M166_PRODUCTION_AUTHORITY_GRANT_REQUIRED"),
        ("production_runtime_authorization_allowed", "M166_PRODUCTION_RUNTIME_AUTH_REQUIRED"),
        ("go_live_authorization_allowed", "M166_GO_LIVE_AUTH_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    return validated


def validate_m166_production_release_gate_record(
    record: ProductionReleaseGateRecord,
) -> ProductionReleaseGateRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ProductionReleaseGateRecord):
        raise ValueError("M166_SECRET_LIKE_GATE_CONTENT_DENIED")
    validated = ProductionReleaseGateRecord.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m165":
        raise ValueError("M166_SOURCE_CHECKPOINT_M165_REQUIRED")
    if validated.status != ProductionReleaseGateStatus.production_authority_granted:
        raise ValueError("M166_PRODUCTION_AUTHORITY_STATUS_REQUIRED")
    required = [ProductionReadinessEvidenceKind(kind) for kind in REQUIRED_M166_EVIDENCE_KINDS]
    if validated.required_evidence_kinds != required:
        raise ValueError("M166_REQUIRED_EVIDENCE_KINDS_EXACT")
    validated_evidence = [
        validate_m166_production_readiness_evidence_record(record)
        for record in validated.evidence_records
    ]
    if [record.evidence_ref for record in validated_evidence] != validated.evidence_refs:
        raise ValueError("M166_EVIDENCE_REF_BINDING_MISMATCH")
    seen_kinds = {record.kind for record in validated_evidence}
    if seen_kinds != set(required):
        raise ValueError("M166_ALL_REQUIRED_EVIDENCE_REQUIRED")
    if len(validated_evidence) != len(required):
        raise ValueError("M166_DUPLICATE_OR_EXTRA_EVIDENCE_DENIED")
    if any(not record.reviewed_live_evidence or record.reviewed_by_ref is None for record in validated_evidence):
        raise ValueError("M166_REVIEWED_LIVE_EVIDENCE_REQUIRED")
    for field_name, reason in [
        ("exact_scope_bound", "M166_EXACT_SCOPE_REQUIRED"),
        ("all_evidence_passed", "M166_ALL_EVIDENCE_PASS_REQUIRED"),
        ("redacted_evidence_only", "M166_REDACTION_REQUIRED"),
        ("blockers_cleared", "M166_NO_BLOCKERS_REQUIRED"),
        ("rollback_ready", "M166_ROLLBACK_REQUIRED"),
        ("audit_required", "M166_AUDIT_REQUIRED"),
        ("replay_safe", "M166_REPLAY_REQUIRED"),
        ("production_authority_granted", "M166_PRODUCTION_AUTHORITY_GRANT_REQUIRED"),
        ("production_runtime_authorized", "M166_PRODUCTION_RUNTIME_AUTH_REQUIRED"),
        ("go_live_authorized", "M166_GO_LIVE_AUTH_REQUIRED"),
        ("production_deployment_authorized", "M166_PRODUCTION_DEPLOYMENT_AUTH_REQUIRED"),
        ("traffic_routing_authorized", "M166_TRAFFIC_ROUTING_AUTH_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("credential_material_exported", "M166_CREDENTIAL_MATERIAL_DENIED"),
        ("raw_prompt_exported", "M166_RAW_PROMPT_DENIED"),
        ("raw_response_exported", "M166_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_exported", "M166_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_local_path_exported", "M166_RAW_PATH_DENIED"),
        ("raw_log_exported", "M166_RAW_LOG_DENIED"),
        ("unreviewed_dependency_added", "M166_UNREVIEWED_DEPENDENCY_DENIED"),
        ("backend_route_added", "M166_BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "M166_CONTROL_CENTER_CONTROL_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M166_RELEASE_GATE_SIDE_EFFECTS_DENIED")
    for reason_code in [
        "M166_PRODUCTION_READINESS_GREEN",
        "M166_PRODUCTION_AUTHORITY_GRANTED",
    ]:
        if reason_code not in validated.reason_codes:
            raise ValueError("M166_REASON_CODE_REQUIRED")
    return validated
