import pytest

from ultimate_ai_agent.core.local_model_management import (
    FakeM165SettingsApplier,
    M165RuntimeObservation,
    M165SettingsApplyRequest,
    apply_m165_settings_with_rollback,
    recommend_m165_llama_cpp_adjustment,
    validate_m165_settings_apply_request,
    validate_m165_settings_apply_result,
    validate_m165_tuning_recommendation,
)


def _observation(kind: str):
    return M165RuntimeObservation(
        observation_ref=f"runtime-observation:m165-{kind}",
        signal_kind=kind,
        safe_summary=f"Redacted {kind} signal.",
    )


def _apply_request(**overrides):
    data = {
        "request_ref": "settings-apply-request:m165-test",
        "approval_ref": "approval:m165-settings-apply",
        "previous_preset_ref": "llama-preset:m165-previous",
        "target_preset_ref": "llama-preset:m165-target",
        "settings": {"ctx-size": "2048"},
    }
    data.update(overrides)
    return M165SettingsApplyRequest(**data)


@pytest.mark.parametrize(
    "kind,setting",
    [
        ("crash", "ctx-size"),
        ("memory_pressure", "n-gpu-layers"),
        ("lag", "parallel"),
        ("reload_loop", "prompt-cache"),
        ("error", "batch-size"),
    ],
)
def test_m165_recommends_one_advisory_change(kind, setting):
    recommendation = recommend_m165_llama_cpp_adjustment(
        [_observation(kind)],
        current_settings={"ctx-size": "4096", "n-gpu-layers": "20"},
    )

    assert recommendation.setting_name == setting
    assert recommendation.advisory_only is True
    assert recommendation.one_change_only is True
    assert recommendation.settings_applied is False
    assert recommendation.restart_performed is False
    validate_m165_tuning_recommendation(recommendation)


def test_m165_apply_requires_exact_approval_and_applies_settings():
    applier = FakeM165SettingsApplier(apply_ok=True)

    result = apply_m165_settings_with_rollback(_apply_request(), applier=applier)

    assert applier.applied_settings == [{"ctx-size": "2048"}]
    assert result.settings_applied is True
    assert result.restart_performed is True
    assert result.rollback_performed is False
    assert result.active_preset_ref == "llama-preset:m165-target"
    assert result.raw_prompt_logged is False
    assert result.raw_response_logged is False


def test_m165_failed_apply_rolls_back_to_previous_known_good_preset():
    applier = FakeM165SettingsApplier(apply_ok=False)

    result = apply_m165_settings_with_rollback(_apply_request(), applier=applier)

    assert result.settings_applied is False
    assert result.restart_performed is False
    assert result.rollback_performed is True
    assert result.active_preset_ref == "llama-preset:m165-previous"
    assert applier.rollback_calls == 1


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"approved": False}, "M165_EXACT_APPROVAL_REQUIRED"),
        ({"raw_prompt_included": True}, "M165_RAW_PROMPT_DENIED"),
        ({"settings": {"unknown": "1"}}, "M165_SETTING_DENIED"),
    ],
)
def test_m165_apply_request_rejects_unsafe_shape(update, reason):
    with pytest.raises(ValueError, match=reason):
        validate_m165_settings_apply_request(_apply_request(**update))


def test_m165_result_validation_rejects_unsafe_mutation():
    result = apply_m165_settings_with_rollback(
        _apply_request(),
        applier=FakeM165SettingsApplier(),
    )

    with pytest.raises(ValueError, match="M165_RAW_RESPONSE_DENIED"):
        validate_m165_settings_apply_result(result.model_copy(update={"raw_response_logged": True}))
