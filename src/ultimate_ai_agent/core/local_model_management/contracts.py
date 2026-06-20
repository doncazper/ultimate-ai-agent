from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.local_model_management.constants import (
    FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LOCAL_MODEL_MANAGEMENT_DOCS,
    LOCAL_MODEL_MANAGEMENT_M153_M165_DOCS,
    LOCAL_MODEL_SELECTION_WEIGHTS,
    REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS,
    SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    _FREEZE_RECORD_DENIALS,
    _FREEZE_REQUEST_DENIALS,
    _FREEZE_REQUIRED_TRUE,
    _FUTURE_LIVE_CONTRACT_DENIALS,
    _FUTURE_LIVE_CONTRACT_REQUIRED_TRUE,
    _GGUF_DENIALS,
    _GGUF_REQUIRED_TRUE,
    _HARDWARE_DENIALS,
    _HARDWARE_REQUIRED_TRUE,
    _HF_PREVIEW_DENIALS,
    _HF_PREVIEW_REQUIRED_TRUE,
    _M153_M165_DENIALS,
    _M153_M165_MILESTONE_EXTRA_DENIALS,
    _M153_M165_MILESTONE_REQUIRED_TRUE,
    _M153_M165_PLAN_REQUIRED_TRUE,
    _OBSERVABILITY_PREVIEW_DENIALS,
    _OBSERVABILITY_PREVIEW_REQUIRED_TRUE,
    _OBSERVABILITY_SIGNAL_DENIALS,
    _OBSERVABILITY_SIGNAL_REQUIRED_TRUE,
    _POLICY_DENIALS,
    _POLICY_REQUIRED_TRUE,
    _RAW_LOCAL_PATH_RE,
    _SECRET_LIKE_RE,
    _SELECTION_DENIALS,
    _SELECTION_REQUIRED_TRUE,
    _SETTINGS_DENIALS,
    _SETTINGS_REQUIRED_TRUE,
    _URL_RE,
)
from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeKind


class LocalModelManagementStatus(str, Enum):
    chartered = "chartered"
    search_preview_recorded = "search_preview_recorded"
    settings_plan_recorded = "settings_plan_recorded"
    selection_preview_recorded = "selection_preview_recorded"
    observability_preview_recorded = "observability_preview_recorded"
    foundation_frozen = "foundation_frozen"


class LocalModelObservabilitySignalKind(str, Enum):
    settings_summary = "settings_summary"
    error_summary = "error_summary"
    lag_summary = "lag_summary"
    crash_summary = "crash_summary"
    adjustment_suggestion = "adjustment_suggestion"


class LocalModelManagementLane(str, Enum):
    safe_contract = "safe_contract"
    live_bounded_read_only = "live_bounded_read_only"
    live_exact_approved_acquisition = "live_exact_approved_acquisition"
    live_llama_cpp_supervisor = "live_llama_cpp_supervisor"
    live_openai_gateway = "live_openai_gateway"
    live_settings_tuning = "live_settings_tuning"
    future_live_contract_only = "future_live_contract_only"


class LocalModelManagementMilestoneKind(str, Enum):
    m153_hardware_gguf_refs = "m153_hardware_gguf_refs"
    m154_llama_cpp_settings_plan = "m154_llama_cpp_settings_plan"
    m155_hf_search_preview = "m155_hf_search_preview"
    m156_review_only_settings_surface = "m156_review_only_settings_surface"
    m157_selection_preview = "m157_selection_preview"
    m158_observability_audit = "m158_observability_audit"
    m159_foundation_freeze = "m159_foundation_freeze"
    m160_hf_search_contract = "m160_hf_search_contract"
    m161_system_probe_contract = "m161_system_probe_contract"
    m162_model_acquisition_contract = "m162_model_acquisition_contract"
    m163_llama_cpp_supervisor_contract = "m163_llama_cpp_supervisor_contract"
    m164_openai_gateway_contract = "m164_openai_gateway_contract"
    m165_tuning_advisor_contract = "m165_tuning_advisor_contract"


class FutureLiveLocalModelCapabilityKind(str, Enum):
    hf_search = "hf_search"
    hardware_probe = "hardware_probe"
    gguf_download = "gguf_download"
    llama_cpp_supervisor = "llama_cpp_supervisor"
    openai_gateway = "openai_gateway"
    settings_tuning = "settings_tuning"


class FutureLiveContractStatus(str, Enum):
    recorded_for_review = "recorded_for_review"
    disabled_until_runtime_milestone = "disabled_until_runtime_milestone"
    denied = "denied"


class _LocalModelManagementModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class LocalModelManagementPolicy(_LocalModelManagementModel):
    policy_ref: str = "local-model-management-policy:m152"
    status: LocalModelManagementStatus = LocalModelManagementStatus.chartered
    contract_only: bool = True
    review_only: bool = True
    post_m151_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default: bool = True
    no_effect_receipt_required: bool = True
    model_router_metadata_only: bool = True
    model_runtime_contracts_only: bool = True
    openwebui_shell_only: bool = True
    control_center_review_surface_only: bool = True
    live_hf_search_enabled: bool = False
    local_system_probe_enabled: bool = False
    model_download_enabled: bool = False
    model_file_read_enabled: bool = False
    llama_cpp_import_enabled: bool = False
    llama_cpp_server_enabled: bool = False
    llama_cpp_settings_apply_enabled: bool = False
    runtime_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    network_access_enabled: bool = False
    prompt_processing_enabled: bool = False
    model_call_enabled: bool = False
    raw_prompt_logging_enabled: bool = False
    raw_response_logging_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(LOCAL_MODEL_MANAGEMENT_DOCS))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        _validate_safe_payload(self.metadata)
        return self


class HardwareCapabilitySummary(_LocalModelManagementModel):
    summary_ref: str
    source_ref: str
    observed_at_ref: str
    os_arch_bucket: str
    cpu_core_bucket: str
    ram_bucket: str
    vram_bucket: str
    backend_device_family_bucket: str
    disk_budget_bucket: str
    power_thermal_hint: str = "power-thermal:unknown"
    injected_summary_only: bool = True
    local_probe_performed: bool = False
    raw_hostname_included: bool = False
    raw_serial_included: bool = False
    raw_username_included: bool = False
    raw_path_included: bool = False
    env_dump_included: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.summary_ref, "summary_ref"),
            (self.source_ref, "source_ref"),
            (self.observed_at_ref, "observed_at_ref"),
            (self.power_thermal_hint, "power_thermal_hint"),
        ]:
            _validate_m61_ref(value, field_name)
        for value, field_name in [
            (self.os_arch_bucket, "os_arch_bucket"),
            (self.cpu_core_bucket, "cpu_core_bucket"),
            (self.ram_bucket, "ram_bucket"),
            (self.vram_bucket, "vram_bucket"),
            (self.backend_device_family_bucket, "backend_device_family_bucket"),
            (self.disk_budget_bucket, "disk_budget_bucket"),
        ]:
            _validate_safe_free_text(value, field_name)
        _validate_safe_payload(self.metadata)
        return self


class GgufArtifactRef(_LocalModelManagementModel):
    artifact_ref: str
    repo_ref: str
    revision_ref: str
    filename_ref: str
    license_ref: str
    provenance_ref: str
    size_bucket: str
    quantization_ref: str
    checksum_ref: str | None = None
    gguf_declared: bool = True
    download_requested: bool = False
    model_file_read_requested: bool = False
    raw_url_included: bool = False
    raw_local_path_included: bool = False
    raw_model_card_included: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.artifact_ref, "artifact_ref"),
            (self.repo_ref, "repo_ref"),
            (self.revision_ref, "revision_ref"),
            (self.filename_ref, "filename_ref"),
            (self.license_ref, "license_ref"),
            (self.provenance_ref, "provenance_ref"),
            (self.quantization_ref, "quantization_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.checksum_ref is not None:
            _validate_m61_ref(self.checksum_ref, "checksum_ref")
        if ".gguf" not in self.filename_ref.lower():
            raise ValueError("M152_GGUF_FILENAME_REF_REQUIRED")
        _validate_safe_free_text(self.size_bucket, "size_bucket")
        _validate_safe_payload(self.metadata)
        return self


class HuggingFaceSearchPreviewRequest(_LocalModelManagementModel):
    request_ref: str
    query: str
    task_ref: str
    hardware_summary_ref: str
    query_pool_ref: str
    alternative_pool_ref: str
    no_effect_receipt_plan_ref: str
    inert_preview_only: bool = True
    injected_candidates_only: bool = True
    live_search_requested: bool = False
    network_access_requested: bool = False
    authenticated_request_requested: bool = False
    token_use_requested: bool = False
    raw_model_card_requested: bool = False
    download_requested: bool = False
    model_call_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.task_ref, "task_ref"),
            (self.hardware_summary_ref, "hardware_summary_ref"),
            (self.query_pool_ref, "query_pool_ref"),
            (self.alternative_pool_ref, "alternative_pool_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_search_query(self.query)
        _validate_safe_payload(self.metadata)
        return self


class LlamaCppSettingsPlan(_LocalModelManagementModel):
    plan_ref: str
    settings_ref: str
    model_candidate_ref: str
    artifact_ref: str
    preset_ref: str
    no_effect_receipt_plan_ref: str
    runtime_kind: LocalModelRuntimeKind = LocalModelRuntimeKind.llama_cpp_planned
    ctx_size_tokens: int = Field(default=4096, ge=512, le=262144)
    ctx_size_capped_by_fit: bool = True
    gpu_layers: str = "auto"
    device_ref: str = "device:auto"
    fit_enabled: bool = True
    parallel_slots: int = Field(default=1, ge=1, le=1)
    batch_size: int = Field(default=2048, ge=1, le=8192)
    ubatch_size: int = Field(default=512, ge=1, le=4096)
    threads_ref: str = "threads:auto"
    kv_cache_type_ref: str = "kv-cache:auto"
    mmap_ref: str = "mmap:auto"
    mlock_ref: str = "mlock:auto"
    flash_attention: str = "auto"
    prompt_cache_enabled: bool = True
    metrics_loopback_only: bool = True
    generated_argv_preview_ref: str | None = None
    llama_cpp_imported: bool = False
    server_started: bool = False
    subprocess_spawned: bool = False
    argv_executed: bool = False
    endpoint_contacted: bool = False
    settings_applied: bool = False
    model_loaded: bool = False
    prompt_processed: bool = False
    model_call_performed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.plan_ref, "plan_ref"),
            (self.settings_ref, "settings_ref"),
            (self.model_candidate_ref, "model_candidate_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.preset_ref, "preset_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
            (self.device_ref, "device_ref"),
            (self.threads_ref, "threads_ref"),
            (self.kv_cache_type_ref, "kv_cache_type_ref"),
            (self.mmap_ref, "mmap_ref"),
            (self.mlock_ref, "mlock_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if self.generated_argv_preview_ref is not None:
            _validate_m61_ref(self.generated_argv_preview_ref, "generated_argv_preview_ref")
        _validate_safe_free_text(self.gpu_layers, "gpu_layers")
        _validate_safe_free_text(self.flash_attention, "flash_attention")
        _validate_safe_payload(self.metadata)
        return self


class LocalModelCandidateSummary(_LocalModelManagementModel):
    candidate_ref: str
    repo_ref: str
    revision_ref: str
    artifact_ref: str
    filename_ref: str
    task_ref: str
    license_ref: str
    provenance_ref: str
    hardware_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)
    task_capability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    query_name_score: float = Field(default=0.0, ge=0.0, le=1.0)
    popularity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    recency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    license_provenance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    has_gguf: bool = True
    fits_hardware: bool = True
    gated_without_approval: bool = False
    unsupported_modality_required: bool = False
    unsafe_or_unknown_provenance: bool = False
    exceeds_disk_limit: bool = False
    exceeds_memory_limit: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.candidate_ref, "candidate_ref"),
            (self.repo_ref, "repo_ref"),
            (self.revision_ref, "revision_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.filename_ref, "filename_ref"),
            (self.task_ref, "task_ref"),
            (self.license_ref, "license_ref"),
            (self.provenance_ref, "provenance_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.metadata)
        return self


class ModelSelectionPreview(_LocalModelManagementModel):
    preview_ref: str
    request_ref: str
    hardware_summary_ref: str
    query: str
    query_match_candidate_refs: list[str]
    alternative_candidate_refs: list[str]
    rejected_candidate_refs: list[str]
    ranked_candidate_refs: list[str]
    score_by_candidate_ref: dict[str, float]
    no_effect_receipt_plan_ref: str
    status: LocalModelManagementStatus = LocalModelManagementStatus.selection_preview_recorded
    injected_candidates_only: bool = True
    live_search_performed: bool = False
    selection_authority_granted: bool = False
    routing_authority_granted: bool = False
    download_performed: bool = False
    model_loaded: bool = False
    model_call_performed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.preview_ref, "preview_ref"),
            (self.request_ref, "request_ref"),
            (self.hardware_summary_ref, "hardware_summary_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(
            self.query_match_candidate_refs,
            "query_match_candidate_refs",
            allow_empty=True,
        )
        _validate_ref_list(
            self.alternative_candidate_refs,
            "alternative_candidate_refs",
            allow_empty=True,
        )
        _validate_ref_list(
            self.rejected_candidate_refs,
            "rejected_candidate_refs",
            allow_empty=True,
        )
        _validate_ref_list(self.ranked_candidate_refs, "ranked_candidate_refs", allow_empty=True)
        for ref in self.score_by_candidate_ref:
            _validate_m61_ref(ref, "score_by_candidate_ref")
        _validate_search_query(self.query)
        _validate_safe_payload(self.metadata)
        return self


class LocalModelObservabilitySignal(_LocalModelManagementModel):
    signal_ref: str
    kind: LocalModelObservabilitySignalKind
    settings_plan_ref: str
    safe_summary: str
    suggested_adjustment_ref: str | None = None
    redacted: bool = True
    local_only: bool = True
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    raw_log_included: bool = False
    env_vars_included: bool = False
    raw_path_included: bool = False
    secret_included: bool = False
    settings_applied: bool = False
    restart_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.signal_ref, "signal_ref")
        _validate_m61_ref(self.settings_plan_ref, "settings_plan_ref")
        if self.suggested_adjustment_ref is not None:
            _validate_m61_ref(self.suggested_adjustment_ref, "suggested_adjustment_ref")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=500)
        _validate_safe_payload(self.metadata)
        return self


class LocalModelObservabilityPreview(_LocalModelManagementModel):
    preview_ref: str
    settings_plan_ref: str
    signal_refs: list[str]
    signals: list[LocalModelObservabilitySignal]
    no_effect_receipt_plan_ref: str
    status: LocalModelManagementStatus = LocalModelManagementStatus.observability_preview_recorded
    redacted_only: bool = True
    local_only: bool = True
    advisory_only: bool = True
    settings_applied: bool = False
    restart_requested: bool = False
    model_call_performed: bool = False
    raw_prompt_exported: bool = False
    raw_response_exported: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.preview_ref, "preview_ref"),
            (self.settings_plan_ref, "settings_plan_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.signal_refs, "signal_refs")
        if [signal.signal_ref for signal in self.signals] != self.signal_refs:
            raise ValueError("M152_OBSERVABILITY_SIGNAL_REFS_MISMATCH")
        _validate_safe_payload(self.metadata)
        return self


class LocalModelManagementFreezeRequest(_LocalModelManagementModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    checklist_refs: list[str]
    authority_boundary_ref: str
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    live_search_requested: bool = False
    local_probe_requested: bool = False
    download_requested: bool = False
    llama_cpp_server_requested: bool = False
    subprocess_execution_requested: bool = False
    network_access_requested: bool = False
    model_call_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_freeze_ref_shape(
            self.request_ref,
            self.freeze_ref,
            self.baseline_ref,
            self.actor_ref,
            self.authority_boundary_ref,
            self.audit_ref,
            self.replay_ref,
            self.no_effect_receipt_plan_ref,
        )
        _validate_ref_list(self.accepted_checkpoint_refs, "accepted_checkpoint_refs")
        _validate_ref_list(self.checklist_refs, "checklist_refs")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=500)
        _validate_safe_payload(self.metadata)
        return self


class LocalModelManagementFreezeRecord(_LocalModelManagementModel):
    record_ref: str
    freeze_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    checklist_refs: list[str]
    authority_boundary_ref: str
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    status: LocalModelManagementStatus = LocalModelManagementStatus.foundation_frozen
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    live_search_performed: bool = False
    local_probe_performed: bool = False
    download_performed: bool = False
    llama_cpp_server_started: bool = False
    subprocess_execution_performed: bool = False
    network_access_performed: bool = False
    model_call_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_freeze_ref_shape(
            self.record_ref,
            self.freeze_ref,
            self.baseline_ref,
            self.actor_ref,
            self.authority_boundary_ref,
            self.audit_ref,
            self.replay_ref,
            self.no_effect_receipt_plan_ref,
            request_ref=self.request_ref,
        )
        _validate_ref_list(self.accepted_checkpoint_refs, "accepted_checkpoint_refs")
        _validate_ref_list(self.checklist_refs, "checklist_refs")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=500)
        _validate_safe_payload(self.metadata)
        return self


class LocalModelManagementMilestoneContract(_LocalModelManagementModel):
    milestone_ref: str
    milestone_kind: LocalModelManagementMilestoneKind
    lane: LocalModelManagementLane
    title_ref: str
    prerequisite_refs: list[str]
    input_contract_refs: list[str]
    output_contract_refs: list[str]
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default: bool = True
    no_effect_only: bool = True
    future_live_authority_contract_only: bool = True
    live_capability_authorized: bool = False
    live_hf_search_performed: bool = False
    local_system_probe_performed: bool = False
    model_download_performed: bool = False
    model_file_read_performed: bool = False
    model_cache_write_performed: bool = False
    llama_cpp_import_performed: bool = False
    llama_cpp_server_started: bool = False
    subprocess_execution_performed: bool = False
    network_access_performed: bool = False
    prompt_processed: bool = False
    model_call_performed: bool = False
    settings_applied: bool = False
    runtime_restart_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    openwebui_plugin_added: bool = False
    dependency_added: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    tool_execution_performed: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.milestone_ref, "milestone_ref"),
            (self.title_ref, "title_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.prerequisite_refs, "prerequisite_refs", allow_empty=True)
        _validate_ref_list(self.input_contract_refs, "input_contract_refs", allow_empty=True)
        _validate_ref_list(self.output_contract_refs, "output_contract_refs")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=700)
        _validate_safe_payload(self.metadata)
        return self


class LocalModelManagementProgressionPlan(_LocalModelManagementModel):
    plan_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    milestone_contracts: list[LocalModelManagementMilestoneContract]
    safe_lane_refs: list[str]
    live_read_only_lane_refs: list[str]
    live_acquisition_lane_refs: list[str]
    live_supervisor_lane_refs: list[str]
    live_gateway_lane_refs: list[str]
    live_tuning_lane_refs: list[str]
    future_live_lane_refs: list[str]
    authority_boundary_ref: str
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default: bool = True
    no_effect_only: bool = True
    m153_m159_safe_lane_complete: bool = True
    m160_live_read_only_lane_enabled: bool = True
    m162_live_acquisition_lane_enabled: bool = True
    m163_live_supervisor_lane_enabled: bool = True
    m164_live_gateway_lane_enabled: bool = True
    m165_live_tuning_lane_enabled: bool = True
    live_capability_authorized: bool = False
    live_hf_search_performed: bool = False
    local_system_probe_performed: bool = False
    model_download_performed: bool = False
    llama_cpp_server_started: bool = False
    subprocess_execution_performed: bool = False
    network_access_performed: bool = False
    model_call_performed: bool = False
    settings_applied: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    docs_refs: list[str] = Field(default_factory=lambda: list(LOCAL_MODEL_MANAGEMENT_M153_M165_DOCS))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.plan_ref, "plan_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.authority_boundary_ref, "authority_boundary_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.accepted_checkpoint_refs, "accepted_checkpoint_refs")
        _validate_ref_list(self.safe_lane_refs, "safe_lane_refs")
        _validate_ref_list(self.live_read_only_lane_refs, "live_read_only_lane_refs")
        _validate_ref_list(self.live_acquisition_lane_refs, "live_acquisition_lane_refs")
        _validate_ref_list(self.live_supervisor_lane_refs, "live_supervisor_lane_refs")
        _validate_ref_list(self.live_gateway_lane_refs, "live_gateway_lane_refs")
        _validate_ref_list(self.live_tuning_lane_refs, "live_tuning_lane_refs")
        _validate_ref_list(self.future_live_lane_refs, "future_live_lane_refs", allow_empty=True)
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=700)
        _validate_safe_payload(self.metadata)
        return self


class FutureLiveLocalModelApprovalBoundContract(_LocalModelManagementModel):
    contract_ref: str
    capability_kind: FutureLiveLocalModelCapabilityKind
    source_m159_freeze_ref: str
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    approval_ref: str
    approval_bundle_ref: str
    revocation_ref: str
    kill_switch_ref: str
    audit_ref: str
    replay_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    status: FutureLiveContractStatus = FutureLiveContractStatus.disabled_until_runtime_milestone
    approval_bound: bool = True
    approval_refs_are_identifiers_only: bool = True
    exact_scope_bound: bool = True
    non_transferable: bool = True
    revocable: bool = True
    replay_safe: bool = True
    disabled_by_default: bool = True
    review_only: bool = True
    no_effect_only: bool = True
    live_capability_authorized: bool = False
    network_access_performed: bool = False
    local_system_probe_performed: bool = False
    download_performed: bool = False
    model_file_read_performed: bool = False
    model_cache_write_performed: bool = False
    llama_cpp_import_performed: bool = False
    subprocess_execution_performed: bool = False
    server_started: bool = False
    shell_string_included: bool = False
    argv_executed: bool = False
    prompt_processed: bool = False
    raw_prompt_logged: bool = False
    raw_response_logged: bool = False
    model_call_performed: bool = False
    settings_applied: bool = False
    runtime_restart_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    openwebui_settings_mutation_requested: bool = False
    openwebui_privileged_management_used: bool = False
    openwebui_plugin_added: bool = False
    openwebui_is_agent_brain: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    tool_execution_performed: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.source_m159_freeze_ref, "source_m159_freeze_ref"),
            (self.actor_ref, "actor_ref"),
            (self.approval_bundle_ref, "approval_bundle_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.kill_switch_ref, "kill_switch_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_ref_list(self.resource_refs, "resource_refs")
        _validate_ref_list(self.capability_refs, "capability_refs")
        _validate_ref_list(self.allowlist_refs, "allowlist_refs")
        _validate_safe_free_text(self.safe_summary, "safe_summary", max_length=700)
        _validate_safe_payload(self.metadata)
        return self


def validate_local_model_management_policy(
    policy: LocalModelManagementPolicy,
) -> LocalModelManagementPolicy:
    validated = LocalModelManagementPolicy.model_validate(policy.model_dump())
    _require_true_flags(validated, _POLICY_REQUIRED_TRUE)
    _require_false_flags(validated, _POLICY_DENIALS)
    return validated


def validate_hardware_capability_summary(
    summary: HardwareCapabilitySummary,
) -> HardwareCapabilitySummary:
    validated = HardwareCapabilitySummary.model_validate(summary.model_dump())
    _require_true_flags(validated, _HARDWARE_REQUIRED_TRUE)
    _require_false_flags(validated, _HARDWARE_DENIALS)
    return validated


def validate_gguf_artifact_ref(artifact: GgufArtifactRef) -> GgufArtifactRef:
    validated = GgufArtifactRef.model_validate(artifact.model_dump())
    _require_true_flags(validated, _GGUF_REQUIRED_TRUE)
    _require_false_flags(validated, _GGUF_DENIALS)
    return validated


def validate_hugging_face_search_preview_request(
    request: HuggingFaceSearchPreviewRequest,
) -> HuggingFaceSearchPreviewRequest:
    validated = HuggingFaceSearchPreviewRequest.model_validate(request.model_dump())
    _require_true_flags(validated, _HF_PREVIEW_REQUIRED_TRUE)
    _require_false_flags(validated, _HF_PREVIEW_DENIALS)
    return validated


def validate_llama_cpp_settings_plan(plan: LlamaCppSettingsPlan) -> LlamaCppSettingsPlan:
    validated = LlamaCppSettingsPlan.model_validate(plan.model_dump())
    if validated.runtime_kind != LocalModelRuntimeKind.llama_cpp_planned:
        raise ValueError("M152_LLAMA_CPP_PLANNED_RUNTIME_REQUIRED")
    _require_true_flags(validated, _SETTINGS_REQUIRED_TRUE)
    _require_false_flags(validated, _SETTINGS_DENIALS)
    return validated


def validate_model_candidate_summary(
    candidate: LocalModelCandidateSummary,
) -> LocalModelCandidateSummary:
    return LocalModelCandidateSummary.model_validate(candidate.model_dump())


def build_model_selection_preview(
    request: HuggingFaceSearchPreviewRequest,
    candidates: list[LocalModelCandidateSummary],
    *,
    top_k: int = 5,
) -> ModelSelectionPreview:
    request = validate_hugging_face_search_preview_request(request)
    validated_candidates = [validate_model_candidate_summary(candidate) for candidate in candidates]
    ranked_valid = sorted(
        (candidate for candidate in validated_candidates if not _candidate_rejection_reasons(candidate)),
        key=lambda candidate: (
            -_candidate_weighted_score(candidate),
            candidate.repo_ref,
            candidate.revision_ref,
            candidate.filename_ref,
            candidate.candidate_ref,
        ),
    )
    rejected_refs = [
        candidate.candidate_ref
        for candidate in validated_candidates
        if _candidate_rejection_reasons(candidate)
    ]
    deduped: list[LocalModelCandidateSummary] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for candidate in ranked_valid:
        key = (candidate.repo_ref, candidate.revision_ref, candidate.filename_ref)
        if key in seen_keys:
            rejected_refs.append(candidate.candidate_ref)
            continue
        seen_keys.add(key)
        deduped.append(candidate)

    query_matches = [
        candidate.candidate_ref
        for candidate in deduped
        if _candidate_matches_query(candidate, request.query)
    ][:top_k]
    alternatives = [
        candidate.candidate_ref
        for candidate in deduped
        if not _candidate_matches_query(candidate, request.query)
    ][:top_k]
    ranked_refs = [candidate.candidate_ref for candidate in deduped][:top_k]
    scores = {
        candidate.candidate_ref: round(_candidate_weighted_score(candidate), 4)
        for candidate in deduped[:top_k]
    }
    return validate_model_selection_preview(
        ModelSelectionPreview(
            preview_ref=f"local-model-selection-preview:{_safe_preview_suffix(request.request_ref)}",
            request_ref=request.request_ref,
            hardware_summary_ref=request.hardware_summary_ref,
            query=request.query,
            query_match_candidate_refs=query_matches,
            alternative_candidate_refs=alternatives,
            rejected_candidate_refs=list(dict.fromkeys(rejected_refs)),
            ranked_candidate_refs=ranked_refs,
            score_by_candidate_ref=scores,
            no_effect_receipt_plan_ref=request.no_effect_receipt_plan_ref,
        )
    )


def validate_model_selection_preview(preview: ModelSelectionPreview) -> ModelSelectionPreview:
    validated = ModelSelectionPreview.model_validate(preview.model_dump())
    _require_true_flags(validated, _SELECTION_REQUIRED_TRUE)
    _require_false_flags(validated, _SELECTION_DENIALS)
    for ref in validated.score_by_candidate_ref:
        if ref not in validated.ranked_candidate_refs:
            raise ValueError("M152_SELECTION_SCORE_REF_NOT_RANKED")
    return validated


def validate_local_model_observability_signal(
    signal: LocalModelObservabilitySignal,
) -> LocalModelObservabilitySignal:
    validated = LocalModelObservabilitySignal.model_validate(signal.model_dump())
    _require_true_flags(validated, _OBSERVABILITY_SIGNAL_REQUIRED_TRUE)
    _require_false_flags(validated, _OBSERVABILITY_SIGNAL_DENIALS)
    return validated


def validate_local_model_observability_preview(
    preview: LocalModelObservabilityPreview,
) -> LocalModelObservabilityPreview:
    validated = LocalModelObservabilityPreview.model_validate(preview.model_dump())
    _require_true_flags(validated, _OBSERVABILITY_PREVIEW_REQUIRED_TRUE)
    _require_false_flags(validated, _OBSERVABILITY_PREVIEW_DENIALS)
    for signal in validated.signals:
        validate_local_model_observability_signal(signal)
    return validated


def validate_local_model_management_freeze_request(
    request: LocalModelManagementFreezeRequest,
) -> LocalModelManagementFreezeRequest:
    validated = LocalModelManagementFreezeRequest.model_validate(request.model_dump())
    _require_true_flags(validated, _FREEZE_REQUIRED_TRUE)
    _require_false_flags(validated, _FREEZE_REQUEST_DENIALS)
    _validate_exact_checkpoint_refs(validated.accepted_checkpoint_refs)
    if validated.side_effects_performed:
        raise ValueError("M152_SIDE_EFFECTS_DENIED")
    return validated


def build_local_model_management_freeze_record(
    request: LocalModelManagementFreezeRequest,
) -> LocalModelManagementFreezeRecord:
    request = validate_local_model_management_freeze_request(request)
    return validate_local_model_management_freeze_record(
        LocalModelManagementFreezeRecord(
            record_ref=f"local-model-management-freeze-record:{_safe_preview_suffix(request.freeze_ref)}",
            freeze_ref=request.freeze_ref,
            request_ref=request.request_ref,
            baseline_ref=request.baseline_ref,
            actor_ref=request.actor_ref,
            accepted_checkpoint_refs=list(request.accepted_checkpoint_refs),
            checklist_refs=list(request.checklist_refs),
            authority_boundary_ref=request.authority_boundary_ref,
            audit_ref=request.audit_ref,
            replay_ref=request.replay_ref,
            no_effect_receipt_plan_ref=request.no_effect_receipt_plan_ref,
            safe_summary=request.safe_summary,
        )
    )


def validate_local_model_management_freeze_record(
    record: LocalModelManagementFreezeRecord,
) -> LocalModelManagementFreezeRecord:
    validated = LocalModelManagementFreezeRecord.model_validate(record.model_dump())
    _require_true_flags(validated, _FREEZE_REQUIRED_TRUE)
    _require_false_flags(validated, _FREEZE_RECORD_DENIALS)
    _validate_exact_checkpoint_refs(validated.accepted_checkpoint_refs)
    if validated.side_effects_performed:
        raise ValueError("M152_SIDE_EFFECTS_DENIED")
    return validated


def build_default_local_model_management_m153_m165_contracts() -> list[LocalModelManagementMilestoneContract]:
    specs = [
        (
            "checkpoint:m153",
            LocalModelManagementMilestoneKind.m153_hardware_gguf_refs,
            LocalModelManagementLane.safe_contract,
            "title:m153-hardware-gguf-refs",
            ["local-model-policy:m152"],
            [
                "hardware-summary-contract:m153",
                "gguf-artifact-ref-contract:m153",
                "hf-repo-ref-contract:m153",
                "license-provenance-ref-contract:m153",
                "model-fit-constraint-contract:m153",
            ],
            "Review injected hardware summaries, GGUF artifact refs, repo refs, license refs, provenance refs, fit constraints, and no-effect receipt plans.",
        ),
        (
            "checkpoint:m154",
            LocalModelManagementMilestoneKind.m154_llama_cpp_settings_plan,
            LocalModelManagementLane.safe_contract,
            "title:m154-llama-cpp-settings-plan",
            ["checkpoint:m153"],
            [
                "llama-cpp-settings-plan-contract:m154",
                "ctx-size-setting-ref:m154",
                "gpu-layer-setting-ref:m154",
                "kv-cache-setting-ref:m154",
                "prompt-cache-setting-ref:m154",
            ],
            "Review llama.cpp settings-plan refs for context, fit, GPU layer plan, batch, ubatch, threads, cache, mmap, mlock, and metrics.",
        ),
        (
            "checkpoint:m155",
            LocalModelManagementMilestoneKind.m155_hf_search_preview,
            LocalModelManagementLane.safe_contract,
            "title:m155-hf-search-preview",
            ["checkpoint:m154"],
            [
                "hf-search-preview-contract:m155",
                "search-term-ref:m155",
                "query-pool-ref:m155",
                "alternative-pool-ref:m155",
            ],
            "Review inert Hugging Face search preview terms and candidate-pool refs without live search or network access.",
        ),
        (
            "checkpoint:m156",
            LocalModelManagementMilestoneKind.m156_review_only_settings_surface,
            LocalModelManagementLane.safe_contract,
            "title:m156-review-only-settings-surface",
            ["checkpoint:m155"],
            [
                "control-center-local-models-review-surface-ref:m156",
                "openwebui-settings-guidance-ref:m156",
                "no-execute-control-ref:m156",
            ],
            "Review the future Local Models settings surface and OpenWebUI guidance while keeping controls non-executing.",
        ),
        (
            "checkpoint:m157",
            LocalModelManagementMilestoneKind.m157_selection_preview,
            LocalModelManagementLane.safe_contract,
            "title:m157-selection-preview",
            ["checkpoint:m156"],
            [
                "deterministic-selection-preview-contract:m157",
                "query-match-ranking-ref:m157",
                "alternative-ranking-ref:m157",
                "hard-rejection-ref:m157",
            ],
            "Review deterministic model selection previews from injected candidate refs only.",
        ),
        (
            "checkpoint:m158",
            LocalModelManagementMilestoneKind.m158_observability_audit,
            LocalModelManagementLane.safe_contract,
            "title:m158-observability-audit",
            ["checkpoint:m157"],
            [
                "redacted-observability-contract:m158",
                "lag-summary-ref:m158",
                "crash-summary-ref:m158",
                "settings-adjustment-suggestion-ref:m158",
            ],
            "Review redacted settings, lag, crash, error, and advisory adjustment refs without raw prompts, responses, logs, or paths.",
        ),
        (
            "checkpoint:m159",
            LocalModelManagementMilestoneKind.m159_foundation_freeze,
            LocalModelManagementLane.safe_contract,
            "title:m159-foundation-freeze",
            ["checkpoint:m158"],
            [
                "local-model-management-foundation-freeze-ref:m159",
                "accepted-m152-m158-ref:m159",
                "no-effect-freeze-receipt-ref:m159",
            ],
            "Freeze the accepted M152-M158 local model management foundation as reviewed contracts only.",
        ),
        (
            "checkpoint:m160",
            LocalModelManagementMilestoneKind.m160_hf_search_contract,
            LocalModelManagementLane.live_bounded_read_only,
            "title:m160-hf-search-contract",
            ["checkpoint:m159"],
            [
                "bounded-hf-search-transport-contract:m160",
                "bounded-gguf-search-result-ref:m160",
                "stdlib-hf-search-transport-ref:m160",
            ],
            "Enable bounded read-only Hugging Face GGUF metadata search with unauthenticated HTTPS GET and no downloads.",
        ),
        (
            "checkpoint:m161",
            LocalModelManagementMilestoneKind.m161_system_probe_contract,
            LocalModelManagementLane.live_bounded_read_only,
            "title:m161-system-probe-contract",
            ["checkpoint:m160"],
            [
                "redacted-system-capability-probe-contract:m161",
                "redacted-hardware-bucket-ref:m161",
                "stdlib-system-probe-ref:m161",
            ],
            "Enable redacted local system capability probing with stdlib-only bucket outputs and no broad scans.",
        ),
        (
            "checkpoint:m162",
            LocalModelManagementMilestoneKind.m162_model_acquisition_contract,
            LocalModelManagementLane.live_exact_approved_acquisition,
            "title:m162-model-acquisition-contract",
            ["checkpoint:m161"],
            [
                "exact-approved-model-acquisition-contract:m162",
                "uaa-cache-artifact-ref:m162",
                "approval-bound-gguf-acquisition-ref:m162",
                "stdlib-hf-resolve-transport-ref:m162",
            ],
            "Enable exact user-approved GGUF acquisition into a UAA-owned cache with pinned revision, exact filename, and no model calls.",
        ),
        (
            "checkpoint:m163",
            LocalModelManagementMilestoneKind.m163_llama_cpp_supervisor_contract,
            LocalModelManagementLane.live_llama_cpp_supervisor,
            "title:m163-llama-cpp-supervisor-contract",
            ["checkpoint:m162"],
            [
                "llama-cpp-supervisor-contract:m163",
                "structured-argv-supervisor-ref:m163",
                "loopback-only-server-ref:m163",
                "redacted-supervisor-log-ref:m163",
            ],
            "Enable a structured argv llama.cpp supervisor on loopback with redacted logs and no shell strings.",
        ),
        (
            "checkpoint:m164",
            LocalModelManagementMilestoneKind.m164_openai_gateway_contract,
            LocalModelManagementLane.live_openai_gateway,
            "title:m164-openai-gateway-contract",
            ["checkpoint:m163"],
            [
                "openai-compatible-gateway-contract:m164",
                "openwebui-local-gateway-ref:m164",
                "tools-disabled-gateway-ref:m164",
            ],
            "Expose approved llama.cpp models through UAA's local OpenAI-compatible gateway while keeping tools, functions, and streaming disabled.",
        ),
        (
            "checkpoint:m165",
            LocalModelManagementMilestoneKind.m165_tuning_advisor_contract,
            LocalModelManagementLane.live_settings_tuning,
            "title:m165-tuning-advisor-contract",
            ["checkpoint:m164"],
            [
                "tuning-advisor-contract:m165",
                "approved-settings-apply-plan-ref:m165",
                "rollback-plan-ref:m165",
            ],
            "Enable advisory tuning plus exact-approved settings apply, restart, and rollback to previous known-good presets.",
        ),
    ]
    return [
        LocalModelManagementMilestoneContract(
            milestone_ref=milestone_ref,
            milestone_kind=milestone_kind,
            lane=lane,
            title_ref=title_ref,
            prerequisite_refs=prerequisite_refs,
            input_contract_refs=prerequisite_refs,
            output_contract_refs=output_contract_refs,
            audit_ref=f"audit:{milestone_ref.split(':', 1)[1]}-local-model-management",
            replay_ref=f"replay:{milestone_ref.split(':', 1)[1]}-local-model-management",
            no_effect_receipt_plan_ref=f"receipt-plan:{milestone_ref.split(':', 1)[1]}-no-effect",
            safe_summary=safe_summary,
        )
        for (
            milestone_ref,
            milestone_kind,
            lane,
            title_ref,
            prerequisite_refs,
            output_contract_refs,
            safe_summary,
        ) in specs
    ]


def validate_local_model_management_milestone_contract(
    contract: LocalModelManagementMilestoneContract,
) -> LocalModelManagementMilestoneContract:
    validated = LocalModelManagementMilestoneContract.model_validate(contract.model_dump())
    _require_true_flags(validated, _M153_M165_MILESTONE_REQUIRED_TRUE)
    _require_false_flags(validated, _M153_M165_DENIALS)
    _require_false_flags(validated, _M153_M165_MILESTONE_EXTRA_DENIALS)
    if validated.side_effects_performed:
        raise ValueError("M153_M165_SIDE_EFFECTS_DENIED")
    _validate_milestone_lane(validated.milestone_ref, validated.lane)
    _validate_milestone_kind(validated.milestone_ref, validated.milestone_kind)
    return validated


def build_local_model_management_m153_m165_progression_plan(
    *,
    plan_ref: str = "local-model-management-progression:m153-m165",
    baseline_ref: str = "baseline:m152-accepted",
    actor_ref: str = "actor:local-model-management-reviewer",
) -> LocalModelManagementProgressionPlan:
    contracts = [
        validate_local_model_management_milestone_contract(contract)
        for contract in build_default_local_model_management_m153_m165_contracts()
    ]
    return validate_local_model_management_m153_m165_progression_plan(
        LocalModelManagementProgressionPlan(
            plan_ref=plan_ref,
            baseline_ref=baseline_ref,
            actor_ref=actor_ref,
            accepted_checkpoint_refs=list(REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS),
            milestone_contracts=contracts,
            safe_lane_refs=list(SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            live_read_only_lane_refs=list(LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            live_acquisition_lane_refs=list(LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            live_supervisor_lane_refs=list(LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            live_gateway_lane_refs=list(LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            live_tuning_lane_refs=list(LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            future_live_lane_refs=list(FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
            authority_boundary_ref="authority-boundary:m153-m165-local-model-management",
            audit_ref="audit:m153-m165-local-model-management",
            replay_ref="replay:m153-m165-local-model-management",
            no_effect_receipt_plan_ref="receipt-plan:m153-m165-no-effect",
            safe_summary="Review M153-M165 local model management progression contracts without live authority.",
        )
    )


def validate_local_model_management_m153_m165_progression_plan(
    plan: LocalModelManagementProgressionPlan,
) -> LocalModelManagementProgressionPlan:
    validated = LocalModelManagementProgressionPlan.model_validate(plan.model_dump())
    _require_true_flags(validated, _M153_M165_PLAN_REQUIRED_TRUE)
    _require_false_flags(validated, _M153_M165_DENIALS)
    if validated.side_effects_performed:
        raise ValueError("M153_M165_SIDE_EFFECTS_DENIED")
    if tuple(validated.accepted_checkpoint_refs) != REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS:
        raise ValueError("M153_M165_EXACT_CHECKPOINT_REFS_REQUIRED")
    if tuple(validated.safe_lane_refs) != SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M153_M159_EXACT_SAFE_LANE_REFS_REQUIRED")
    if tuple(validated.live_read_only_lane_refs) != LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M160_M161_EXACT_LIVE_READ_ONLY_REFS_REQUIRED")
    if tuple(validated.live_acquisition_lane_refs) != LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M162_EXACT_LIVE_ACQUISITION_REFS_REQUIRED")
    if tuple(validated.live_supervisor_lane_refs) != LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M163_EXACT_LIVE_SUPERVISOR_REFS_REQUIRED")
    if tuple(validated.live_gateway_lane_refs) != LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M164_EXACT_LIVE_GATEWAY_REFS_REQUIRED")
    if tuple(validated.live_tuning_lane_refs) != LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M165_EXACT_LIVE_TUNING_REFS_REQUIRED")
    if tuple(validated.future_live_lane_refs) != FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M153_M165_FUTURE_LIVE_LANE_EMPTY_REQUIRED")
    contract_refs = [contract.milestone_ref for contract in validated.milestone_contracts]
    if tuple(contract_refs) != REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS:
        raise ValueError("M153_M165_MILESTONE_CONTRACTS_INCOMPLETE")
    for contract in validated.milestone_contracts:
        validate_local_model_management_milestone_contract(contract)
    return validated


def build_future_live_local_model_contract(
    *,
    contract_ref: str,
    capability_kind: FutureLiveLocalModelCapabilityKind,
    source_m159_freeze_ref: str = "local-model-freeze:m159-planned",
    actor_ref: str = "actor:local-model-management-reviewer",
    approval_ref: str,
    safe_summary: str,
) -> FutureLiveLocalModelApprovalBoundContract:
    milestone = _future_live_capability_milestone(capability_kind)
    reason_prefix = milestone.upper()
    return validate_future_live_local_model_contract(
        FutureLiveLocalModelApprovalBoundContract(
            contract_ref=contract_ref,
            capability_kind=capability_kind,
            source_m159_freeze_ref=source_m159_freeze_ref,
            actor_ref=actor_ref,
            resource_refs=[f"resource:{milestone}-local-model-management"],
            capability_refs=[f"capability:{milestone}-{capability_kind.value}"],
            allowlist_refs=[f"allowlist:{milestone}-exact-scope-only"],
            approval_ref=approval_ref,
            approval_bundle_ref=f"approval-bundle:{milestone}-local-model-management",
            revocation_ref=f"revocation:{milestone}-local-model-management",
            kill_switch_ref=f"kill-switch:{milestone}-local-model-management",
            audit_ref=f"audit:{milestone}-local-model-management",
            replay_ref=f"replay:{milestone}-local-model-management",
            no_effect_receipt_plan_ref=f"receipt-plan:{milestone}-no-effect",
            safe_summary=safe_summary,
            reason_codes=[
                f"{reason_prefix}_APPROVAL_REF_NOT_AUTHORITY",
                f"{reason_prefix}_DISABLED_UNTIL_RUNTIME_MILESTONE",
            ],
        )
    )


def build_m160_disabled_hf_search_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m160-hf-search",
        capability_kind=FutureLiveLocalModelCapabilityKind.hf_search,
        approval_ref="approval:m160-hf-search-reviewed-only",
        safe_summary="Record future bounded Hugging Face search contract with fake transport refs only.",
    )


def build_m161_disabled_hardware_probe_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m161-hardware-probe",
        capability_kind=FutureLiveLocalModelCapabilityKind.hardware_probe,
        approval_ref="approval:m161-hardware-probe-reviewed-only",
        safe_summary="Record future redacted hardware probe contract with injected bucket refs only.",
    )


def build_m162_disabled_gguf_download_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m162-gguf-download",
        capability_kind=FutureLiveLocalModelCapabilityKind.gguf_download,
        approval_ref="approval:m162-gguf-download-reviewed-only",
        safe_summary="Record future exact-approved GGUF acquisition contract without downloads or cache writes.",
    )


def build_m163_disabled_llama_cpp_supervisor_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m163-llama-cpp-supervisor",
        capability_kind=FutureLiveLocalModelCapabilityKind.llama_cpp_supervisor,
        approval_ref="approval:m163-llama-cpp-supervisor-reviewed-only",
        safe_summary="Record future llama.cpp supervisor contract with fake supervisor refs only.",
    )


def build_m164_disabled_openai_gateway_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m164-openai-gateway",
        capability_kind=FutureLiveLocalModelCapabilityKind.openai_gateway,
        approval_ref="approval:m164-openai-gateway-reviewed-only",
        safe_summary="Record future UAA local gateway guidance while OpenWebUI remains a shell only.",
    )


def build_m165_disabled_settings_tuning_contract() -> FutureLiveLocalModelApprovalBoundContract:
    return build_future_live_local_model_contract(
        contract_ref="future-live-contract:m165-settings-tuning",
        capability_kind=FutureLiveLocalModelCapabilityKind.settings_tuning,
        approval_ref="approval:m165-settings-tuning-reviewed-only",
        safe_summary="Record future tuning advisor contract without settings apply, restart, or rollback execution.",
    )


def build_m163_m165_disabled_future_live_contracts() -> list[FutureLiveLocalModelApprovalBoundContract]:
    return []


def build_m162_m165_disabled_future_live_contracts() -> list[FutureLiveLocalModelApprovalBoundContract]:
    return build_m163_m165_disabled_future_live_contracts()


def build_m161_m165_disabled_future_live_contracts() -> list[FutureLiveLocalModelApprovalBoundContract]:
    return build_m163_m165_disabled_future_live_contracts()


def build_m160_m165_disabled_future_live_contracts() -> list[FutureLiveLocalModelApprovalBoundContract]:
    return build_m163_m165_disabled_future_live_contracts()


def validate_future_live_local_model_contract(
    contract: FutureLiveLocalModelApprovalBoundContract,
) -> FutureLiveLocalModelApprovalBoundContract:
    validated = FutureLiveLocalModelApprovalBoundContract.model_validate(contract.model_dump())
    _require_true_flags(validated, _FUTURE_LIVE_CONTRACT_REQUIRED_TRUE)
    _require_false_flags(validated, _FUTURE_LIVE_CONTRACT_DENIALS)
    if validated.status != FutureLiveContractStatus.disabled_until_runtime_milestone:
        raise ValueError("M160_M165_DISABLED_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M160_M165_SIDE_EFFECTS_DENIED")
    _validate_local_model_approval_ref(validated.approval_ref, validated.capability_kind)
    return validated


def _candidate_weighted_score(candidate: LocalModelCandidateSummary) -> float:
    return (
        candidate.hardware_fit_score * LOCAL_MODEL_SELECTION_WEIGHTS["hardware_fit"]
        + candidate.task_capability_score * LOCAL_MODEL_SELECTION_WEIGHTS["task_capability"]
        + candidate.query_name_score * LOCAL_MODEL_SELECTION_WEIGHTS["query_name"]
        + candidate.popularity_score * LOCAL_MODEL_SELECTION_WEIGHTS["popularity"]
        + candidate.recency_score * LOCAL_MODEL_SELECTION_WEIGHTS["recency"]
        + candidate.license_provenance_score
        * LOCAL_MODEL_SELECTION_WEIGHTS["license_provenance"]
    )


def _candidate_rejection_reasons(candidate: LocalModelCandidateSummary) -> list[str]:
    reasons: list[str] = []
    if not candidate.has_gguf:
        reasons.append("M152_REJECT_NO_GGUF")
    if not candidate.fits_hardware:
        reasons.append("M152_REJECT_HARDWARE_FIT")
    if candidate.gated_without_approval:
        reasons.append("M152_REJECT_GATED_WITHOUT_APPROVAL")
    if candidate.unsupported_modality_required:
        reasons.append("M152_REJECT_UNSUPPORTED_MODALITY")
    if candidate.unsafe_or_unknown_provenance:
        reasons.append("M152_REJECT_UNSAFE_PROVENANCE")
    if candidate.exceeds_disk_limit:
        reasons.append("M152_REJECT_DISK_LIMIT")
    if candidate.exceeds_memory_limit:
        reasons.append("M152_REJECT_MEMORY_LIMIT")
    return reasons


def _candidate_matches_query(candidate: LocalModelCandidateSummary, query: str) -> bool:
    query_value = query.strip().lower()
    if not query_value:
        return False
    haystack = " ".join(
        [
            candidate.candidate_ref,
            candidate.repo_ref,
            candidate.filename_ref,
            candidate.artifact_ref,
        ]
    ).lower()
    return candidate.query_name_score > 0.0 or query_value in haystack


def _validate_milestone_lane(milestone_ref: str, lane: LocalModelManagementLane) -> None:
    if milestone_ref in SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.safe_contract:
            raise ValueError("M153_M159_SAFE_CONTRACT_LANE_REQUIRED")
        return
    if milestone_ref in LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.live_bounded_read_only:
            raise ValueError("M160_M161_LIVE_BOUNDED_READ_ONLY_LANE_REQUIRED")
        return
    if milestone_ref in LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.live_exact_approved_acquisition:
            raise ValueError("M162_LIVE_EXACT_APPROVED_ACQUISITION_LANE_REQUIRED")
        return
    if milestone_ref in LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.live_llama_cpp_supervisor:
            raise ValueError("M163_LIVE_LLAMA_CPP_SUPERVISOR_LANE_REQUIRED")
        return
    if milestone_ref in LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.live_openai_gateway:
            raise ValueError("M164_LIVE_OPENAI_GATEWAY_LANE_REQUIRED")
        return
    if milestone_ref in LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.live_settings_tuning:
            raise ValueError("M165_LIVE_SETTINGS_TUNING_LANE_REQUIRED")
        return
    if milestone_ref in FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        if lane != LocalModelManagementLane.future_live_contract_only:
            raise ValueError("M153_M165_FUTURE_LIVE_CONTRACT_ONLY_REQUIRED")
        return
    raise ValueError("M153_M165_UNKNOWN_MILESTONE_REF")


def _validate_milestone_kind(
    milestone_ref: str,
    milestone_kind: LocalModelManagementMilestoneKind,
) -> None:
    expected = {
        "checkpoint:m153": LocalModelManagementMilestoneKind.m153_hardware_gguf_refs,
        "checkpoint:m154": LocalModelManagementMilestoneKind.m154_llama_cpp_settings_plan,
        "checkpoint:m155": LocalModelManagementMilestoneKind.m155_hf_search_preview,
        "checkpoint:m156": LocalModelManagementMilestoneKind.m156_review_only_settings_surface,
        "checkpoint:m157": LocalModelManagementMilestoneKind.m157_selection_preview,
        "checkpoint:m158": LocalModelManagementMilestoneKind.m158_observability_audit,
        "checkpoint:m159": LocalModelManagementMilestoneKind.m159_foundation_freeze,
        "checkpoint:m160": LocalModelManagementMilestoneKind.m160_hf_search_contract,
        "checkpoint:m161": LocalModelManagementMilestoneKind.m161_system_probe_contract,
        "checkpoint:m162": LocalModelManagementMilestoneKind.m162_model_acquisition_contract,
        "checkpoint:m163": LocalModelManagementMilestoneKind.m163_llama_cpp_supervisor_contract,
        "checkpoint:m164": LocalModelManagementMilestoneKind.m164_openai_gateway_contract,
        "checkpoint:m165": LocalModelManagementMilestoneKind.m165_tuning_advisor_contract,
    }
    if expected.get(milestone_ref) != milestone_kind:
        raise ValueError("M153_M165_MILESTONE_KIND_MISMATCH")


def _future_live_capability_milestone(capability_kind: FutureLiveLocalModelCapabilityKind) -> str:
    mapping = {
        FutureLiveLocalModelCapabilityKind.hf_search: "m160",
        FutureLiveLocalModelCapabilityKind.hardware_probe: "m161",
        FutureLiveLocalModelCapabilityKind.gguf_download: "m162",
        FutureLiveLocalModelCapabilityKind.llama_cpp_supervisor: "m163",
        FutureLiveLocalModelCapabilityKind.openai_gateway: "m164",
        FutureLiveLocalModelCapabilityKind.settings_tuning: "m165",
    }
    return mapping[capability_kind]


def _validate_local_model_approval_ref(
    approval_ref: str,
    capability_kind: FutureLiveLocalModelCapabilityKind,
) -> None:
    lowered = approval_ref.lower()
    milestone = _future_live_capability_milestone(capability_kind)
    if "approval_test_" in lowered or ":all" in lowered or ":*" in lowered or "*" in lowered:
        raise ValueError("M160_M165_APPROVAL_REF_NOT_AUTHORITY")
    _validate_m61_ref(approval_ref, "approval_ref")
    for fragment in ["expired", "revoked", "replay-used"]:
        if fragment in lowered:
            raise ValueError("M160_M165_APPROVAL_REF_NOT_ACTIVE")
    if milestone not in lowered or capability_kind.value.replace("_", "-") not in lowered:
        raise ValueError("M160_M165_APPROVAL_REF_SCOPE_MISMATCH")


def _validate_exact_checkpoint_refs(refs: list[str]) -> None:
    if tuple(refs) != REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS:
        raise ValueError("M152_EXACT_M152_M158_CHECKPOINT_REFS_REQUIRED")


def _validate_freeze_ref_shape(*refs: str, request_ref: str | None = None) -> None:
    for index, ref in enumerate(refs):
        _validate_m61_ref(ref, f"freeze_ref_{index}")
    if request_ref is not None:
        _validate_m61_ref(request_ref, "request_ref")


def _validate_ref_list(refs: list[str], field_name: str, *, allow_empty: bool = False) -> None:
    if not allow_empty and not refs:
        raise ValueError(f"{field_name} is required")
    for ref in refs:
        _validate_m61_ref(ref, field_name)


def _validate_search_query(query: str) -> None:
    _require_nonempty(query, "query")
    if len(query) > 120:
        raise ValueError("query is too long")
    if _URL_RE.search(query):
        raise ValueError("M152_SEARCH_QUERY_MUST_BE_INERT_TEXT")
    if _RAW_LOCAL_PATH_RE.search(query) or _SECRET_LIKE_RE.search(query):
        raise ValueError("query contains unsafe content")
    _validate_safe_payload(query)


def _validate_safe_free_text(value: str, field_name: str, *, max_length: int = 160) -> None:
    _require_nonempty(value, field_name)
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long")
    if _RAW_LOCAL_PATH_RE.search(value) or _URL_RE.search(value) or _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)


def _require_true_flags(model: BaseModel, checks: list[tuple[str, str]]) -> None:
    for field_name, reason in checks:
        if getattr(model, field_name) is not True:
            raise ValueError(reason)


def _require_false_flags(model: BaseModel, checks: list[tuple[str, str]]) -> None:
    for field_name, reason in checks:
        if getattr(model, field_name) is not False:
            raise ValueError(reason)


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _safe_preview_suffix(ref: str) -> str:
    return ref.split(":", 1)[1].replace("/", "-")
