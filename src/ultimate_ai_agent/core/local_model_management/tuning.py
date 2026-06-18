from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _SECRET_LIKE_RE,
    _validate_m61_ref,
    _validate_safe_payload,
)


class _M165Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class M165RuntimeObservation(_M165Model):
    observation_ref: str
    signal_kind: str
    safe_summary: str
    count: int = Field(default=1, ge=1)
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_log_included: bool = False
    raw_path_included: bool = False
    secret_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.observation_ref, "observation_ref")
        if self.signal_kind not in {"lag", "crash", "memory_pressure", "reload_loop", "error"}:
            raise ValueError("M165_SIGNAL_KIND_INVALID")
        _validate_safe_text(self.safe_summary, "safe_summary", max_length=240)
        return self


class M165TuningRecommendation(_M165Model):
    recommendation_ref: str
    action_kind: str
    setting_name: str
    suggested_value: str
    safe_reason: str
    advisory_only: bool = True
    one_change_only: bool = True
    settings_applied: bool = False
    restart_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.recommendation_ref, "recommendation_ref")
        for value, field_name in [
            (self.action_kind, "action_kind"),
            (self.setting_name, "setting_name"),
            (self.suggested_value, "suggested_value"),
            (self.safe_reason, "safe_reason"),
        ]:
            _validate_safe_text(value, field_name, max_length=240)
        return self


class M165SettingsApplyRequest(_M165Model):
    request_ref: str
    approval_ref: str
    previous_preset_ref: str
    target_preset_ref: str
    settings: dict[str, str]
    approved: bool = True
    restart_requested: bool = True
    rollback_on_failure: bool = True
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    secret_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.approval_ref, "approval_ref"),
            (self.previous_preset_ref, "previous_preset_ref"),
            (self.target_preset_ref, "target_preset_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.settings:
            raise ValueError("M165_SETTINGS_REQUIRED")
        for key, value in self.settings.items():
            _validate_allowed_setting(key)
            _validate_safe_text(value, f"setting:{key}", max_length=80)
        return self


class M165SettingsApplyResult(_M165Model):
    result_ref: str
    request_ref: str
    settings_applied: bool
    restart_performed: bool
    rollback_performed: bool = False
    previous_preset_ref: str
    active_preset_ref: str
    raw_prompt_logged: bool = False
    raw_response_logged: bool = False
    secret_logged: bool = False
    production_authority_granted: bool = False
    safe_summary: str

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.result_ref, "result_ref"),
            (self.request_ref, "request_ref"),
            (self.previous_preset_ref, "previous_preset_ref"),
            (self.active_preset_ref, "active_preset_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "safe_summary", max_length=240)
        return self


class M165SettingsApplier(Protocol):
    def apply(self, settings: dict[str, str]) -> bool:
        ...

    def rollback(self) -> bool:
        ...


class FakeM165SettingsApplier:
    def __init__(self, *, apply_ok: bool = True, rollback_ok: bool = True):
        self.apply_ok = apply_ok
        self.rollback_ok = rollback_ok
        self.applied_settings: list[dict[str, str]] = []
        self.rollback_calls = 0

    def apply(self, settings: dict[str, str]) -> bool:
        self.applied_settings.append(dict(settings))
        return self.apply_ok

    def rollback(self) -> bool:
        self.rollback_calls += 1
        return self.rollback_ok


def recommend_m165_llama_cpp_adjustment(
    observations: list[M165RuntimeObservation],
    *,
    current_settings: dict[str, str] | None = None,
) -> M165TuningRecommendation:
    validated = [M165RuntimeObservation.model_validate(item.model_dump()) for item in observations]
    settings = current_settings or {}
    _validate_safe_payload(settings)
    if not validated:
        return _recommend("noop", "settings", "unchanged", "No redacted lag, crash, or pressure signal was present.")
    kinds = [item.signal_kind for item in validated]
    if "crash" in kinds:
        return _recommend("reduce", "ctx-size", _reduced_numeric(settings.get("ctx-size"), default="2048"), "Crash signal suggests reducing context first.")
    if "memory_pressure" in kinds:
        return _recommend("reduce", "n-gpu-layers", _reduced_numeric(settings.get("n-gpu-layers"), default="0"), "Memory pressure suggests reducing GPU offload.")
    if "lag" in kinds:
        return _recommend("reduce", "parallel", "1", "Lag signal suggests reducing parallel work before changing model files.")
    if "reload_loop" in kinds:
        return _recommend("enable", "prompt-cache", "on", "Reload loop signal suggests keeping prompt cache enabled.")
    return _recommend("reduce", "batch-size", "default", "Error signal suggests returning batch settings to default.")


def apply_m165_settings_with_rollback(
    apply_request: M165SettingsApplyRequest,
    *,
    applier: M165SettingsApplier,
) -> M165SettingsApplyResult:
    validated = validate_m165_settings_apply_request(apply_request)
    applied = applier.apply(validated.settings)
    rollback = False
    active_ref = validated.target_preset_ref
    if not applied and validated.rollback_on_failure:
        rollback = applier.rollback()
        active_ref = validated.previous_preset_ref
    return validate_m165_settings_apply_result(
        M165SettingsApplyResult(
            result_ref=f"settings-apply-result:m165-{validated.request_ref.split(':')[-1]}",
            request_ref=validated.request_ref,
            settings_applied=applied,
            restart_performed=applied and validated.restart_requested,
            rollback_performed=rollback,
            previous_preset_ref=validated.previous_preset_ref,
            active_preset_ref=active_ref,
            safe_summary=(
                "M165 approved settings applied and runtime restart requested."
                if applied
                else "M165 settings apply failed and rollback was attempted."
            ),
        )
    )


def validate_m165_settings_apply_request(
    apply_request: M165SettingsApplyRequest,
) -> M165SettingsApplyRequest:
    validated = M165SettingsApplyRequest.model_validate(apply_request.model_dump())
    if not validated.approved:
        raise ValueError("M165_EXACT_APPROVAL_REQUIRED")
    for field_name, reason in [
        ("raw_prompt_included", "M165_RAW_PROMPT_DENIED"),
        ("raw_response_included", "M165_RAW_RESPONSE_DENIED"),
        ("secret_included", "M165_SECRET_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_m165_settings_apply_result(
    result: M165SettingsApplyResult,
) -> M165SettingsApplyResult:
    validated = M165SettingsApplyResult.model_validate(result.model_dump())
    for field_name, reason in [
        ("raw_prompt_logged", "M165_RAW_PROMPT_DENIED"),
        ("raw_response_logged", "M165_RAW_RESPONSE_DENIED"),
        ("secret_logged", "M165_SECRET_DENIED"),
        ("production_authority_granted", "M165_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_m165_tuning_recommendation(
    recommendation: M165TuningRecommendation,
) -> M165TuningRecommendation:
    validated = M165TuningRecommendation.model_validate(recommendation.model_dump())
    if not validated.advisory_only or not validated.one_change_only:
        raise ValueError("M165_ONE_ADVISORY_CHANGE_REQUIRED")
    if validated.settings_applied or validated.restart_performed:
        raise ValueError("M165_RECOMMENDATION_MUST_NOT_APPLY")
    return validated


def _recommend(action_kind: str, setting_name: str, suggested_value: str, safe_reason: str) -> M165TuningRecommendation:
    return validate_m165_tuning_recommendation(
        M165TuningRecommendation(
            recommendation_ref=f"settings-recommendation:m165-{setting_name}",
            action_kind=action_kind,
            setting_name=setting_name,
            suggested_value=suggested_value,
            safe_reason=safe_reason,
        )
    )


def _reduced_numeric(value: str | None, *, default: str) -> str:
    if value is None:
        return default
    try:
        parsed = max(0, int(value))
    except ValueError:
        return default
    return str(max(0, parsed // 2))


def _validate_allowed_setting(name: str) -> None:
    if name not in {
        "ctx-size",
        "n-gpu-layers",
        "parallel",
        "batch-size",
        "ubatch-size",
        "kv-cache-type",
        "mmap",
        "mlock",
        "prompt-cache",
        "flash-attn",
    }:
        raise ValueError("M165_SETTING_DENIED")


def _validate_safe_text(value: str, field_name: str, *, max_length: int) -> None:
    if not value or not value.strip() or len(value) > max_length:
        raise ValueError(f"{field_name} invalid")
    if _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)
