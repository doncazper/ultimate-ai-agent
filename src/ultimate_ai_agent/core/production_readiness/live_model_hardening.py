from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


LIVE_MODEL_PRODUCTION_HARDENING_DOCS = [
    "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING.md",
    "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_BOUNDARY.md",
    "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_RUNBOOK.md",
    "docs/production/M167_LIVE_MODEL_PRODUCTION_HARDENING_NON_GOALS.md",
]

REQUIRED_M167_HARDWARE_PROFILES = (
    "apple_silicon",
    "cpu_only",
    "low_ram",
    "discrete_gpu",
    "limited_disk",
)

REQUIRED_M167_EVIDENCE_KINDS = (
    "model_matrix",
    "installer_runtime_packaging",
    "selection_quality_validation",
    "tuning_advisor_hardening",
    "openwebui_real_e2e",
    "load_soak",
    "operational_controls",
)


class LiveModelHardeningHardwareProfile(str, Enum):
    apple_silicon = "apple_silicon"
    cpu_only = "cpu_only"
    low_ram = "low_ram"
    discrete_gpu = "discrete_gpu"
    limited_disk = "limited_disk"


class LiveModelHardeningEvidenceKind(str, Enum):
    model_matrix = "model_matrix"
    installer_runtime_packaging = "installer_runtime_packaging"
    selection_quality_validation = "selection_quality_validation"
    tuning_advisor_hardening = "tuning_advisor_hardening"
    openwebui_real_e2e = "openwebui_real_e2e"
    load_soak = "load_soak"
    operational_controls = "operational_controls"


class LiveModelHardeningEvidenceStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    blocked = "blocked"


class LiveModelProductionHardeningStatus(str, Enum):
    live_production_hardening_passed = "live_production_hardening_passed"
    live_production_hardening_denied = "live_production_hardening_denied"


M167_REQUIRED_COVERAGE_FLAGS: dict[LiveModelHardeningEvidenceKind, tuple[str, ...]] = {
    LiveModelHardeningEvidenceKind.model_matrix: (
        "hf_search_verified",
        "download_verified",
        "selection_verified",
        "llama_cpp_launch_verified",
        "openwebui_chat_verified",
        "tuning_verified",
        "profile_resource_fit_verified",
    ),
    LiveModelHardeningEvidenceKind.installer_runtime_packaging: (
        "llama_server_discovery_verified",
        "supported_version_verified",
        "binary_provenance_verified",
        "update_handling_verified",
        "rollback_verified",
        "install_failure_messages_verified",
    ),
    LiveModelHardeningEvidenceKind.selection_quality_validation: (
        "ranking_weights_calibrated",
        "fit_accuracy_validated",
        "license_provenance_validated",
        "gated_model_handling_validated",
        "quant_choice_validated",
        "context_limits_validated",
        "disk_ram_vram_estimates_validated",
    ),
    LiveModelHardeningEvidenceKind.tuning_advisor_hardening: (
        "lag_detection_verified",
        "crash_detection_verified",
        "oom_detection_verified",
        "one_change_at_a_time_verified",
        "approval_apply_verified",
        "safe_restart_verified",
        "known_good_rollback_verified",
    ),
    LiveModelHardeningEvidenceKind.openwebui_real_e2e: (
        "auth_check_verified",
        "model_list_verified",
        "chat_completion_verified",
        "failure_messages_verified",
        "reconnect_verified",
        "no_raw_prompt_log_leak_verified",
        "shell_only_verified",
    ),
    LiveModelHardeningEvidenceKind.load_soak: (
        "concurrent_requests_verified",
        "repeated_reload_verified",
        "context_pressure_verified",
        "bad_model_file_verified",
        "crash_loop_verified",
        "port_conflict_verified",
        "memory_pressure_verified",
        "slow_tokens_verified",
    ),
    LiveModelHardeningEvidenceKind.operational_controls: (
        "cache_cleanup_runbook_verified",
        "model_removal_runbook_verified",
        "stuck_download_runbook_verified",
        "corrupted_gguf_runbook_verified",
        "rollback_runbook_verified",
        "credential_rotation_runbook_verified",
        "metrics_log_review_runbook_verified",
        "offline_mode_runbook_verified",
    ),
}


class _LiveModelProductionHardeningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LiveModelHardeningEvidenceRecord(_LiveModelProductionHardeningModel):
    evidence_ref: str
    kind: LiveModelHardeningEvidenceKind
    source_checkpoint_ref: str = "checkpoint:m166"
    hardware_profile: LiveModelHardeningHardwareProfile | None = None
    status: LiveModelHardeningEvidenceStatus = LiveModelHardeningEvidenceStatus.passed
    produced_by_ref: str
    observed_at_ref: str
    safe_summary: str
    coverage_refs: list[str] = Field(default_factory=list)
    coverage_flags: dict[str, bool] = Field(default_factory=dict)
    blocker_refs: list[str] = Field(default_factory=list)
    warning_refs: list[str] = Field(default_factory=list)
    actual_live_evidence: bool = False
    reviewed_by_ref: str | None = None
    redacted: bool = True
    safe_refs_only: bool = True
    loopback_only: bool = True
    openwebui_shell_only: bool = True
    openwebui_is_agent_brain: bool = False
    tools_enabled: bool = False
    functions_enabled: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    raw_log_included: bool = False
    raw_path_included: bool = False
    username_included: bool = False
    environment_dump_included: bool = False
    credential_material_included: bool = False
    unsupported_network_used: bool = False
    unreviewed_dependency_added: bool = False
    production_side_effect_unreviewed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.evidence_ref, "evidence_ref"),
            (self.source_checkpoint_ref, "source_checkpoint_ref"),
            (self.produced_by_ref, "produced_by_ref"),
            (self.observed_at_ref, "observed_at_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in [*self.coverage_refs, *self.blocker_refs, *self.warning_refs]:
            _validate_m61_ref(ref, "m167_support_ref")
        if self.reviewed_by_ref is not None:
            _validate_m61_ref(self.reviewed_by_ref, "reviewed_by_ref")
        if self.actual_live_evidence and self.reviewed_by_ref is None:
            raise ValueError("M167_REVIEWED_BY_REF_REQUIRED")
        if self.kind == LiveModelHardeningEvidenceKind.model_matrix:
            if self.hardware_profile is None:
                raise ValueError("M167_MODEL_MATRIX_PROFILE_REQUIRED")
        elif self.hardware_profile is not None:
            raise ValueError("M167_PROFILE_ONLY_ALLOWED_FOR_MODEL_MATRIX")
        _validate_safe_payload(
            {
                "safe_summary": self.safe_summary,
                "coverage_refs": self.coverage_refs,
                "warning_refs": self.warning_refs,
            }
        )
        return self


class LiveModelProductionHardeningPolicy(_LiveModelProductionHardeningModel):
    policy_ref: str = "live-model-production-hardening-policy:m167"
    source_checkpoint_ref: str = "checkpoint:m166"
    required_evidence_kinds: tuple[LiveModelHardeningEvidenceKind, ...] = tuple(
        LiveModelHardeningEvidenceKind(kind) for kind in REQUIRED_M167_EVIDENCE_KINDS
    )
    required_hardware_profiles: tuple[LiveModelHardeningHardwareProfile, ...] = tuple(
        LiveModelHardeningHardwareProfile(profile)
        for profile in REQUIRED_M167_HARDWARE_PROFILES
    )
    actual_live_evidence_required: bool = True
    reviewed_evidence_required: bool = True
    redaction_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    rollback_required: bool = True
    m166_production_gate_required: bool = True
    no_new_authority_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_m61_ref(self.source_checkpoint_ref, "source_checkpoint_ref")
        _validate_safe_payload(self.metadata)
        return self


class LiveModelProductionHardeningReport(_LiveModelProductionHardeningModel):
    report_ref: str
    source_checkpoint_ref: str
    evidence_records: list[LiveModelHardeningEvidenceRecord]
    evidence_refs: list[str]
    required_evidence_kinds: list[LiveModelHardeningEvidenceKind]
    required_hardware_profiles: list[LiveModelHardeningHardwareProfile]
    audit_ref: str
    replay_ref: str
    rollback_plan_ref: str
    release_scope_ref: str
    release_tag_ref: str
    status: LiveModelProductionHardeningStatus = (
        LiveModelProductionHardeningStatus.live_production_hardening_passed
    )
    model_matrix_passed: bool = True
    installer_runtime_packaging_ready: bool = True
    selection_quality_validated: bool = True
    tuning_loop_hardened: bool = True
    openwebui_real_e2e_passed: bool = True
    load_soak_passed: bool = True
    operational_controls_ready: bool = True
    actual_live_evidence_reviewed: bool = True
    redacted_evidence_only: bool = True
    blockers_cleared: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    rollback_ready: bool = True
    m166_production_authority_gate_required: bool = True
    production_authority_inherited_from_m166: bool = True
    new_production_authority_granted: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    runtime_execution_started_by_report: bool = False
    model_download_started_by_report: bool = False
    raw_prompt_exported: bool = False
    raw_response_exported: bool = False
    raw_provider_payload_exported: bool = False
    raw_local_path_exported: bool = False
    raw_log_exported: bool = False
    credential_material_exported: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.report_ref, "report_ref"),
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
            raise ValueError("M167_REASON_CODE_REQUIRED")
        _validate_safe_payload({"safe_summary": self.safe_summary, "metadata": self.metadata})
        return self


def build_m167_fixture_live_model_hardening_evidence() -> list[LiveModelHardeningEvidenceRecord]:
    records: list[LiveModelHardeningEvidenceRecord] = []
    for profile in LiveModelHardeningHardwareProfile:
        records.append(
            _build_m167_evidence_record(
                kind=LiveModelHardeningEvidenceKind.model_matrix,
                suffix=profile.value,
                safe_summary=(
                    "Live model matrix profile evidence covers search, acquisition, "
                    "selection, launch, chat, tuning, and resource fit."
                ),
                hardware_profile=profile,
            )
        )
    summaries = {
        LiveModelHardeningEvidenceKind.installer_runtime_packaging: (
            "Installer and runtime packaging evidence covers discovery, version, "
            "provenance, update, rollback, and failure message behavior."
        ),
        LiveModelHardeningEvidenceKind.selection_quality_validation: (
            "Selection quality evidence covers real GGUF candidate calibration, fit, "
            "provenance, gated handling, quant choice, context, disk, RAM, and VRAM."
        ),
        LiveModelHardeningEvidenceKind.tuning_advisor_hardening: (
            "Tuning advisor evidence covers lag, crash, OOM, approval, restart, and rollback."
        ),
        LiveModelHardeningEvidenceKind.openwebui_real_e2e: (
            "OpenWebUI real E2E evidence covers gateway auth, model list, chat, "
            "failure messaging, reconnect, and leak checks."
        ),
        LiveModelHardeningEvidenceKind.load_soak: (
            "Load and soak evidence covers concurrency, reload, context pressure, "
            "bad model files, crash loops, port conflicts, memory pressure, and slow tokens."
        ),
        LiveModelHardeningEvidenceKind.operational_controls: (
            "Operational controls evidence covers cleanup, removal, stuck downloads, "
            "corrupted GGUFs, rollback, credential rotation, metrics review, and offline mode."
        ),
    }
    for kind, safe_summary in summaries.items():
        records.append(
            _build_m167_evidence_record(
                kind=kind,
                suffix=kind.value,
                safe_summary=safe_summary,
            )
        )
    return records


def build_m167_live_model_production_hardening_report(
    *,
    evidence_records: list[LiveModelHardeningEvidenceRecord],
    policy: LiveModelProductionHardeningPolicy | None = None,
) -> LiveModelProductionHardeningReport:
    active_policy = validate_m167_live_model_production_hardening_policy(
        policy or LiveModelProductionHardeningPolicy()
    )
    validated_evidence = [
        validate_m167_live_model_hardening_evidence_record(record)
        for record in evidence_records
    ]
    report = LiveModelProductionHardeningReport(
        report_ref="live-model-production-hardening-report:m167",
        source_checkpoint_ref=active_policy.source_checkpoint_ref,
        evidence_records=validated_evidence,
        evidence_refs=[record.evidence_ref for record in validated_evidence],
        required_evidence_kinds=list(active_policy.required_evidence_kinds),
        required_hardware_profiles=list(active_policy.required_hardware_profiles),
        audit_ref="audit-ref:m167:live-model-hardening",
        replay_ref="replay-ref:m167:live-model-hardening",
        rollback_plan_ref="rollback-plan-ref:m167:known-good-local-model",
        release_scope_ref="release-scope-ref:m167:local-model-production-hardening",
        release_tag_ref="release-tag-ref:checkpoint-m167",
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        rollback_ready=active_policy.rollback_required,
        m166_production_authority_gate_required=active_policy.m166_production_gate_required,
        reason_codes=[
            "M167_LIVE_MODEL_PRODUCTION_HARDENING_GREEN",
            "M167_REAL_MODEL_MATRIX_EVIDENCE_BOUND",
            "M167_INSTALLER_RUNTIME_PACKAGING_BOUND",
            "M167_SELECTION_QUALITY_VALIDATION_BOUND",
            "M167_TUNING_ADVISOR_HARDENING_BOUND",
            "M167_OPENWEBUI_REAL_E2E_BOUND",
            "M167_LOAD_SOAK_BOUND",
            "M167_OPERATIONAL_CONTROLS_BOUND",
            "M167_NO_NEW_AUTHORITY_GRANTED",
        ],
        safe_summary=(
            "M167 confirms live local model production hardening only after reviewed "
            "real evidence covers the required hardware profiles, packaging, selection "
            "quality, tuning loop, OpenWebUI E2E, load and soak, and operations controls."
        ),
    )
    return validate_m167_live_model_production_hardening_report(report)


def validate_m167_live_model_hardening_evidence_record(
    record: LiveModelHardeningEvidenceRecord | dict[str, Any],
) -> LiveModelHardeningEvidenceRecord:
    payload = dict(record) if isinstance(record, dict) else _model_payload(record)
    if _has_secret_like_extra(payload, LiveModelHardeningEvidenceRecord):
        raise ValueError("M167_SECRET_LIKE_EVIDENCE_DENIED")
    validated = LiveModelHardeningEvidenceRecord.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m166":
        raise ValueError("M167_SOURCE_CHECKPOINT_M166_REQUIRED")
    if validated.status != LiveModelHardeningEvidenceStatus.passed:
        raise ValueError("M167_EVIDENCE_MUST_PASS")
    if not validated.actual_live_evidence or validated.reviewed_by_ref is None:
        raise ValueError("M167_REVIEWED_LIVE_EVIDENCE_REQUIRED")
    for flag_name in M167_REQUIRED_COVERAGE_FLAGS[validated.kind]:
        if validated.coverage_flags.get(flag_name) is not True:
            raise ValueError(f"M167_COVERAGE_FLAG_REQUIRED:{flag_name}")
    for field_name, reason in [
        ("redacted", "M167_REDACTED_EVIDENCE_REQUIRED"),
        ("safe_refs_only", "M167_SAFE_REFS_REQUIRED"),
        ("loopback_only", "M167_LOOPBACK_REQUIRED"),
        ("openwebui_shell_only", "M167_OPENWEBUI_SHELL_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("openwebui_is_agent_brain", "M167_OPENWEBUI_AUTHORITY_DENIED"),
        ("tools_enabled", "M167_TOOLS_DENIED"),
        ("functions_enabled", "M167_FUNCTIONS_DENIED"),
        ("raw_prompt_included", "M167_RAW_PROMPT_DENIED"),
        ("raw_response_included", "M167_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_included", "M167_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_log_included", "M167_RAW_LOG_DENIED"),
        ("raw_path_included", "M167_RAW_PATH_DENIED"),
        ("username_included", "M167_USERNAME_DENIED"),
        ("environment_dump_included", "M167_ENV_DUMP_DENIED"),
        ("credential_material_included", "M167_CREDENTIAL_MATERIAL_DENIED"),
        ("unsupported_network_used", "M167_UNSUPPORTED_NETWORK_DENIED"),
        ("unreviewed_dependency_added", "M167_UNREVIEWED_DEPENDENCY_DENIED"),
        ("production_side_effect_unreviewed", "M167_UNREVIEWED_SIDE_EFFECT_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    if validated.blocker_refs:
        raise ValueError("M167_BLOCKERS_MUST_BE_EMPTY")
    return validated


def validate_m167_live_model_production_hardening_policy(
    policy: LiveModelProductionHardeningPolicy | dict[str, Any],
) -> LiveModelProductionHardeningPolicy:
    payload = dict(policy) if isinstance(policy, dict) else _model_payload(policy)
    validated = LiveModelProductionHardeningPolicy.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m166":
        raise ValueError("M167_SOURCE_CHECKPOINT_M166_REQUIRED")
    required_kinds = tuple(
        LiveModelHardeningEvidenceKind(kind) for kind in REQUIRED_M167_EVIDENCE_KINDS
    )
    if tuple(validated.required_evidence_kinds) != required_kinds:
        raise ValueError("M167_REQUIRED_EVIDENCE_KINDS_EXACT")
    required_profiles = tuple(
        LiveModelHardeningHardwareProfile(profile)
        for profile in REQUIRED_M167_HARDWARE_PROFILES
    )
    if tuple(validated.required_hardware_profiles) != required_profiles:
        raise ValueError("M167_REQUIRED_HARDWARE_PROFILES_EXACT")
    for field_name, reason in [
        ("actual_live_evidence_required", "M167_ACTUAL_LIVE_EVIDENCE_REQUIRED"),
        ("reviewed_evidence_required", "M167_REVIEWED_EVIDENCE_REQUIRED"),
        ("redaction_required", "M167_REDACTION_REQUIRED"),
        ("audit_required", "M167_AUDIT_REQUIRED"),
        ("replay_required", "M167_REPLAY_REQUIRED"),
        ("rollback_required", "M167_ROLLBACK_REQUIRED"),
        ("m166_production_gate_required", "M167_M166_GATE_REQUIRED"),
        ("no_new_authority_required", "M167_NO_NEW_AUTHORITY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    return validated


def validate_m167_live_model_production_hardening_report(
    report: LiveModelProductionHardeningReport | dict[str, Any],
) -> LiveModelProductionHardeningReport:
    payload = dict(report) if isinstance(report, dict) else _model_payload(report)
    if _has_secret_like_extra(payload, LiveModelProductionHardeningReport):
        raise ValueError("M167_SECRET_LIKE_REPORT_CONTENT_DENIED")
    validated = LiveModelProductionHardeningReport.model_validate(payload)
    if validated.source_checkpoint_ref != "checkpoint:m166":
        raise ValueError("M167_SOURCE_CHECKPOINT_M166_REQUIRED")
    if validated.status != LiveModelProductionHardeningStatus.live_production_hardening_passed:
        raise ValueError("M167_LIVE_HARDENING_STATUS_REQUIRED")
    required_kinds = [
        LiveModelHardeningEvidenceKind(kind) for kind in REQUIRED_M167_EVIDENCE_KINDS
    ]
    required_profiles = [
        LiveModelHardeningHardwareProfile(profile)
        for profile in REQUIRED_M167_HARDWARE_PROFILES
    ]
    if validated.required_evidence_kinds != required_kinds:
        raise ValueError("M167_REQUIRED_EVIDENCE_KINDS_EXACT")
    if validated.required_hardware_profiles != required_profiles:
        raise ValueError("M167_REQUIRED_HARDWARE_PROFILES_EXACT")
    validated_evidence = [
        validate_m167_live_model_hardening_evidence_record(record)
        for record in validated.evidence_records
    ]
    if [record.evidence_ref for record in validated_evidence] != validated.evidence_refs:
        raise ValueError("M167_EVIDENCE_REF_BINDING_MISMATCH")
    non_matrix_kinds = {
        kind for kind in required_kinds if kind != LiveModelHardeningEvidenceKind.model_matrix
    }
    seen_non_matrix_kinds = {
        record.kind
        for record in validated_evidence
        if record.kind != LiveModelHardeningEvidenceKind.model_matrix
    }
    if seen_non_matrix_kinds != non_matrix_kinds:
        raise ValueError("M167_ALL_REQUIRED_EVIDENCE_REQUIRED")
    seen_profiles = {
        record.hardware_profile
        for record in validated_evidence
        if record.kind == LiveModelHardeningEvidenceKind.model_matrix
    }
    if seen_profiles != set(required_profiles):
        raise ValueError("M167_ALL_REQUIRED_HARDWARE_PROFILES_REQUIRED")
    if len(seen_profiles) != len(required_profiles):
        raise ValueError("M167_DUPLICATE_MODEL_MATRIX_PROFILE_DENIED")
    if len(validated_evidence) != len(required_profiles) + len(non_matrix_kinds):
        raise ValueError("M167_DUPLICATE_OR_EXTRA_EVIDENCE_DENIED")
    for field_name, reason in [
        ("model_matrix_passed", "M167_MODEL_MATRIX_REQUIRED"),
        ("installer_runtime_packaging_ready", "M167_INSTALLER_RUNTIME_PACKAGING_REQUIRED"),
        ("selection_quality_validated", "M167_SELECTION_QUALITY_REQUIRED"),
        ("tuning_loop_hardened", "M167_TUNING_LOOP_REQUIRED"),
        ("openwebui_real_e2e_passed", "M167_OPENWEBUI_E2E_REQUIRED"),
        ("load_soak_passed", "M167_LOAD_SOAK_REQUIRED"),
        ("operational_controls_ready", "M167_OPERATIONAL_CONTROLS_REQUIRED"),
        ("actual_live_evidence_reviewed", "M167_ACTUAL_LIVE_EVIDENCE_REQUIRED"),
        ("redacted_evidence_only", "M167_REDACTION_REQUIRED"),
        ("blockers_cleared", "M167_BLOCKERS_REQUIRED"),
        ("audit_required", "M167_AUDIT_REQUIRED"),
        ("replay_safe", "M167_REPLAY_REQUIRED"),
        ("rollback_ready", "M167_ROLLBACK_REQUIRED"),
        ("m166_production_authority_gate_required", "M167_M166_GATE_REQUIRED"),
        ("production_authority_inherited_from_m166", "M167_M166_AUTHORITY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("new_production_authority_granted", "M167_NEW_AUTHORITY_DENIED"),
        ("backend_route_added", "M167_BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "M167_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M167_DEPENDENCY_DENIED"),
        ("runtime_execution_started_by_report", "M167_REPORT_RUNTIME_EXECUTION_DENIED"),
        ("model_download_started_by_report", "M167_REPORT_DOWNLOAD_DENIED"),
        ("raw_prompt_exported", "M167_RAW_PROMPT_DENIED"),
        ("raw_response_exported", "M167_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_exported", "M167_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_local_path_exported", "M167_RAW_PATH_DENIED"),
        ("raw_log_exported", "M167_RAW_LOG_DENIED"),
        ("credential_material_exported", "M167_CREDENTIAL_MATERIAL_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("M167_REPORT_SIDE_EFFECTS_DENIED")
    for reason_code in [
        "M167_LIVE_MODEL_PRODUCTION_HARDENING_GREEN",
        "M167_NO_NEW_AUTHORITY_GRANTED",
    ]:
        if reason_code not in validated.reason_codes:
            raise ValueError("M167_REASON_CODE_REQUIRED")
    return validated


def _build_m167_evidence_record(
    *,
    kind: LiveModelHardeningEvidenceKind,
    suffix: str,
    safe_summary: str,
    hardware_profile: LiveModelHardeningHardwareProfile | None = None,
) -> LiveModelHardeningEvidenceRecord:
    return LiveModelHardeningEvidenceRecord(
        evidence_ref=f"live-model-hardening-evidence:m167:{suffix}",
        kind=kind,
        hardware_profile=hardware_profile,
        produced_by_ref=f"producer-ref:m167:{suffix}",
        observed_at_ref=f"observed-at-ref:m167:{suffix}",
        safe_summary=safe_summary,
        coverage_refs=[
            f"coverage-ref:m167:{suffix}:{flag_name}"
            for flag_name in M167_REQUIRED_COVERAGE_FLAGS[kind]
        ],
        coverage_flags={
            flag_name: True
            for flag_name in M167_REQUIRED_COVERAGE_FLAGS[kind]
        },
    )
