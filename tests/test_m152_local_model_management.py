import pytest

from ultimate_ai_agent.core.local_model_management import (
    REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    GgufArtifactRef,
    HardwareCapabilitySummary,
    HuggingFaceSearchPreviewRequest,
    LlamaCppSettingsPlan,
    LocalModelCandidateSummary,
    LocalModelManagementFreezeRequest,
    LocalModelManagementPolicy,
    LocalModelObservabilityPreview,
    LocalModelObservabilitySignal,
    LocalModelObservabilitySignalKind,
    build_local_model_management_freeze_record,
    build_model_selection_preview,
    validate_gguf_artifact_ref,
    validate_hardware_capability_summary,
    validate_hugging_face_search_preview_request,
    validate_llama_cpp_settings_plan,
    validate_local_model_management_freeze_request,
    validate_local_model_management_policy,
    validate_local_model_observability_preview,
    validate_local_model_observability_signal,
)


def _hardware_summary(**overrides):
    data = {
        "summary_ref": "hardware-summary:m152-test",
        "source_ref": "source:m152-injected",
        "observed_at_ref": "observed-at:m152-review",
        "os_arch_bucket": "darwin-arm64-bucket",
        "cpu_core_bucket": "core-bucket-8-to-16",
        "ram_bucket": "ram-bucket-32gb-to-64gb",
        "vram_bucket": "vram-bucket-shared",
        "backend_device_family_bucket": "backend-device-family-metal",
        "disk_budget_bucket": "disk-budget-under-256gb",
    }
    data.update(overrides)
    return HardwareCapabilitySummary(**data)


def _artifact(**overrides):
    data = {
        "artifact_ref": "gguf-artifact:m152-qwopus-q4",
        "repo_ref": "hf-repo:m152-qwopus",
        "revision_ref": "hf-revision:m152-pinned",
        "filename_ref": "gguf-file:qwopus-q4_k_m.gguf",
        "license_ref": "license:declared-safe",
        "provenance_ref": "provenance:reviewed",
        "size_bucket": "size-bucket-under-20gb",
        "quantization_ref": "quant:q4_k_m",
    }
    data.update(overrides)
    return GgufArtifactRef(**data)


def _search_request(**overrides):
    data = {
        "request_ref": "hf-search-preview:m152-qwopus",
        "query": "qwopus",
        "task_ref": "task:coding",
        "hardware_summary_ref": "hardware-summary:m152-test",
        "query_pool_ref": "candidate-pool:m152-query",
        "alternative_pool_ref": "candidate-pool:m152-alternatives",
        "no_effect_receipt_plan_ref": "receipt-plan:m152-search-no-effect",
    }
    data.update(overrides)
    return HuggingFaceSearchPreviewRequest(**data)


def _settings_plan(**overrides):
    data = {
        "plan_ref": "llama-cpp-settings-plan:m152-test",
        "settings_ref": "settings:m152-qwopus",
        "model_candidate_ref": "candidate:m152-qwopus",
        "artifact_ref": "gguf-artifact:m152-qwopus-q4",
        "preset_ref": "model-preset:m152-default",
        "no_effect_receipt_plan_ref": "receipt-plan:m152-settings-no-effect",
    }
    data.update(overrides)
    return LlamaCppSettingsPlan(**data)


def _freeze_request(**overrides):
    data = {
        "request_ref": "local-model-freeze-request:m152-test",
        "freeze_ref": "local-model-freeze:m159-planned",
        "baseline_ref": "baseline:m151-accepted",
        "actor_ref": "actor:local-reviewer",
        "accepted_checkpoint_refs": list(REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS),
        "checklist_refs": ["checklist:m152-safe-contract-lane"],
        "authority_boundary_ref": "authority-boundary:m152-local-model-management",
        "audit_ref": "audit:m152-local-model-management",
        "replay_ref": "replay:m152-local-model-management",
        "no_effect_receipt_plan_ref": "receipt-plan:m152-freeze-no-effect",
        "safe_summary": "Freeze accepted local model management contract refs only.",
    }
    data.update(overrides)
    return LocalModelManagementFreezeRequest(**data)


@pytest.mark.parametrize(
    "field,reason",
    [
        ("live_hf_search_enabled", "M152_LIVE_HF_SEARCH_DENIED"),
        ("local_system_probe_enabled", "M152_LOCAL_SYSTEM_PROBE_DENIED"),
        ("model_download_enabled", "M152_MODEL_DOWNLOAD_DENIED"),
        ("model_file_read_enabled", "M152_MODEL_FILE_READ_DENIED"),
        ("llama_cpp_import_enabled", "M152_LLAMA_CPP_IMPORT_DENIED"),
        ("llama_cpp_server_enabled", "M152_LLAMA_CPP_SERVER_DENIED"),
        ("runtime_execution_enabled", "M152_RUNTIME_EXECUTION_DENIED"),
        ("subprocess_execution_enabled", "M152_SUBPROCESS_EXECUTION_DENIED"),
        ("network_access_enabled", "M152_NETWORK_ACCESS_DENIED"),
        ("model_call_enabled", "M152_MODEL_CALL_DENIED"),
        ("backend_route_enabled", "M152_BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "M152_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M152_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M152_PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m152_policy_denies_live_local_model_authority(field, reason):
    with pytest.raises(ValueError, match=reason):
        validate_local_model_management_policy(LocalModelManagementPolicy(**{field: True}))


def test_m152_hardware_summary_is_injected_and_redacted():
    summary = validate_hardware_capability_summary(_hardware_summary())

    assert summary.injected_summary_only is True
    assert summary.local_probe_performed is False
    assert summary.raw_path_included is False

    with pytest.raises(ValueError, match="M152_LOCAL_SYSTEM_PROBE_DENIED"):
        validate_hardware_capability_summary(_hardware_summary(local_probe_performed=True))
    with pytest.raises(ValueError, match="unsafe content"):
        _hardware_summary(os_arch_bucket="/Users/sam/private")


def test_m152_gguf_artifact_ref_never_reads_or_downloads_model_file():
    artifact = validate_gguf_artifact_ref(_artifact())

    assert artifact.gguf_declared is True
    assert artifact.download_requested is False
    assert artifact.model_file_read_requested is False

    with pytest.raises(ValueError, match="M152_MODEL_DOWNLOAD_DENIED"):
        validate_gguf_artifact_ref(_artifact(download_requested=True))
    with pytest.raises(ValueError, match="M152_GGUF_FILENAME_REF_REQUIRED"):
        _artifact(filename_ref="model-file:qwopus.bin")


def test_m152_hf_qwopus_search_preview_is_inert():
    request = validate_hugging_face_search_preview_request(_search_request())
    payload = request.model_dump_json()

    assert request.query == "qwopus"
    assert request.live_search_requested is False
    assert request.network_access_requested is False
    assert request.download_requested is False
    assert request.model_call_requested is False
    assert "Authorization" not in payload
    assert "/Users/" not in payload

    with pytest.raises(ValueError, match="M152_LIVE_HF_SEARCH_DENIED"):
        validate_hugging_face_search_preview_request(_search_request(live_search_requested=True))
    with pytest.raises(ValueError, match="M152_SEARCH_QUERY_MUST_BE_INERT_TEXT"):
        _search_request(query="https://example.invalid/qwopus")


def test_m152_llama_cpp_settings_plan_never_executes_or_applies():
    plan = validate_llama_cpp_settings_plan(_settings_plan())

    assert plan.fit_enabled is True
    assert plan.gpu_layers == "auto"
    assert plan.parallel_slots == 1
    assert plan.server_started is False
    assert plan.subprocess_spawned is False
    assert plan.settings_applied is False
    assert plan.model_loaded is False

    with pytest.raises(ValueError, match="M152_LLAMA_CPP_SERVER_DENIED"):
        validate_llama_cpp_settings_plan(_settings_plan(server_started=True))
    with pytest.raises(ValueError, match="M152_SETTINGS_APPLY_DENIED"):
        validate_llama_cpp_settings_plan(_settings_plan(settings_applied=True))


def test_m152_candidate_ranking_uses_injected_candidates_only():
    selection = build_model_selection_preview(
        _search_request(),
        [
            LocalModelCandidateSummary(
                candidate_ref="candidate:m152-alt",
                repo_ref="hf-repo:m152-alt",
                revision_ref="hf-revision:m152-pinned",
                artifact_ref="gguf-artifact:m152-alt",
                filename_ref="gguf-file:alt-q5.gguf",
                task_ref="task:coding",
                license_ref="license:declared-safe",
                provenance_ref="provenance:reviewed",
                hardware_fit_score=1.0,
                task_capability_score=0.9,
                query_name_score=0.0,
                popularity_score=0.9,
                recency_score=0.9,
                license_provenance_score=1.0,
            ),
            LocalModelCandidateSummary(
                candidate_ref="candidate:m152-qwopus",
                repo_ref="hf-repo:m152-qwopus",
                revision_ref="hf-revision:m152-pinned",
                artifact_ref="gguf-artifact:m152-qwopus",
                filename_ref="gguf-file:qwopus-q4.gguf",
                task_ref="task:coding",
                license_ref="license:declared-safe",
                provenance_ref="provenance:reviewed",
                hardware_fit_score=1.0,
                task_capability_score=0.8,
                query_name_score=1.0,
                popularity_score=0.4,
                recency_score=0.4,
                license_provenance_score=1.0,
            ),
            LocalModelCandidateSummary(
                candidate_ref="candidate:m152-too-large",
                repo_ref="hf-repo:m152-too-large",
                revision_ref="hf-revision:m152-pinned",
                artifact_ref="gguf-artifact:m152-too-large",
                filename_ref="gguf-file:too-large.gguf",
                task_ref="task:coding",
                license_ref="license:declared-safe",
                provenance_ref="provenance:reviewed",
                exceeds_memory_limit=True,
            ),
        ],
    )

    assert selection.injected_candidates_only is True
    assert selection.live_search_performed is False
    assert selection.download_performed is False
    assert selection.model_loaded is False
    assert selection.query_match_candidate_refs == ["candidate:m152-qwopus"]
    assert selection.alternative_candidate_refs == ["candidate:m152-alt"]
    assert selection.rejected_candidate_refs == ["candidate:m152-too-large"]


def test_m152_observability_is_redacted_and_advisory_only():
    signal = LocalModelObservabilitySignal(
        signal_ref="observability-signal:m152-lag",
        kind=LocalModelObservabilitySignalKind.lag_summary,
        settings_plan_ref="llama-cpp-settings-plan:m152-test",
        safe_summary="Lag bucket summary; reduce context first.",
        suggested_adjustment_ref="settings-adjustment:m152-reduce-context",
    )
    preview = validate_local_model_observability_preview(
        LocalModelObservabilityPreview(
            preview_ref="observability-preview:m152-redacted",
            settings_plan_ref="llama-cpp-settings-plan:m152-test",
            signal_refs=[signal.signal_ref],
            signals=[signal],
            no_effect_receipt_plan_ref="receipt-plan:m152-observability-no-effect",
        )
    )

    payload = preview.model_dump_json()
    assert preview.redacted_only is True
    assert preview.advisory_only is True
    assert preview.settings_applied is False
    assert preview.raw_prompt_exported is False
    assert "/Users/" not in payload
    assert "Traceback" not in payload

    with pytest.raises(ValueError, match="M152_RAW_PROMPT_DENIED"):
        validate_local_model_observability_signal(signal.model_copy(update={"raw_prompt_included": True}))


def test_m152_freeze_record_requires_exact_m152_to_m158_refs():
    record = build_local_model_management_freeze_record(_freeze_request())

    assert record.accepted_checkpoint_refs == list(REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert record.no_effect_receipt_plan_ref == "receipt-plan:m152-freeze-no-effect"
    assert record.live_search_performed is False
    assert record.llama_cpp_server_started is False
    assert record.side_effects_performed == []

    with pytest.raises(ValueError, match="M152_EXACT_M152_M158_CHECKPOINT_REFS_REQUIRED"):
        validate_local_model_management_freeze_request(
            _freeze_request(
                accepted_checkpoint_refs=[
                    *REQUIRED_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
                    "checkpoint:m159",
                ]
            )
        )
    with pytest.raises(ValueError, match="M152_MODEL_DOWNLOAD_DENIED"):
        validate_local_model_management_freeze_request(_freeze_request(download_requested=True))
