from pathlib import Path

import pytest

from ultimate_ai_agent.core.local_model_management import (
    FakeM165SettingsApplier,
    M165RuntimeObservation,
    M165SettingsApplyRequest,
    M165TuningRecommendation,
    apply_m165_settings_with_rollback,
    recommend_m165_llama_cpp_adjustment,
    validate_m165_settings_apply_request,
    validate_m165_tuning_recommendation,
)
from ultimate_ai_agent.core.production_readiness import REQUIRED_M167_HARDWARE_PROFILES


MATRIX_PATH = Path("docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md")


def _matrix_rows() -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] in {
            "Apple Silicon",
            "CPU-only",
            "Low RAM",
            "Discrete GPU",
            "Limited disk",
        }:
            rows[cells[0]] = cells
    return rows


def test_m167_live_model_matrix_has_required_safe_ref_rows() -> None:
    rows = _matrix_rows()

    assert list(rows) == [
        "Apple Silicon",
        "CPU-only",
        "Low RAM",
        "Discrete GPU",
        "Limited disk",
    ]
    assert [
        row[1].removeprefix("evidence-ref:m167:matrix:").replace("-", "_")
        for row in rows.values()
    ] == list(REQUIRED_M167_HARDWARE_PROFILES)

    for profile, row in rows.items():
        assert len(row) == 10
        assert row[1].startswith("evidence-ref:m167:matrix:")
        assert row[2].startswith("review-ref:m167:")
        assert row[4] == "model-ref:m167:approved-gguf:pending"
        assert "llama.cpp" not in row[5].lower() or "pending" in row[5].lower()
        assert "blocker-ref:m167:" in row[6]
        assert row[7].startswith("verification-ref:m167:")
        assert "rollback-ref:m167:known-good-local-model:pending" in row[8]
        assert any(status in row[9].lower() for status in {"pending", "blocked"})
        assert "proven" not in row[9].lower()
        assert "not production-ready" in row[9].lower() or row[9].lower().startswith("blocked;")
        assert profile


def test_m167_live_model_matrix_documents_status_semantics_and_scope_denials() -> None:
    text = MATRIX_PATH.read_text(encoding="utf-8").lower()

    for fragment in [
        "proven: reviewed live evidence exists",
        "pending: the row is scoped",
        "blocked: the row is scoped",
        "not-scoped: the behavior is outside this task",
        "no hardware row is proven in this patch",
        "m166 remains the authority gate",
        "does not start llama.cpp",
        "does not scope remote model servers",
        "tool/function calling",
        "m166 authority-gate binding",
    ]:
        assert fragment in text


def _observation(signal_kind: str, *, count: int = 2) -> M165RuntimeObservation:
    return M165RuntimeObservation(
        observation_ref=f"observation-ref:m167:tuning:{signal_kind}",
        signal_kind=signal_kind,
        safe_summary=f"Redacted {signal_kind} summary only.",
        count=count,
    )


def _assert_safe_recommendation(recommendation: M165TuningRecommendation) -> None:
    validated = validate_m165_tuning_recommendation(recommendation)

    assert validated.advisory_only is True
    assert validated.one_change_only is True
    assert validated.setting_change_count <= 1
    assert validated.operator_confirmation_required is True
    assert validated.redacted_evidence_only is True
    assert validated.rollback_required_before_apply is True
    assert validated.unsafe_authority_required is False
    assert validated.settings_applied is False
    assert validated.restart_performed is False
    assert validated.evidence_ref.startswith("evidence-ref:m165:tuning:")
    assert validated.rollback_plan_ref.startswith("rollback-ref:m165:tuning:")

    dumped = " ".join(str(value).lower() for value in validated.model_dump().values())
    for unsafe_fragment in [
        "/users/",
        "/var/",
        "api_key",
        "authorization",
        "bearer ",
        "password",
        "raw prompt material",
        "raw response material",
        "provider payload",
    ]:
        assert unsafe_fragment not in dumped


@pytest.mark.parametrize(
    ("signal_kind", "setting_name", "suggested_value", "action_kind"),
    [
        ("lag", "parallel", "1", "reduce"),
        ("out_of_memory", "n-gpu-layers", "4", "reduce"),
        ("crash_loop", "ctx-size", "2048", "reduce"),
        ("reload_loop", "prompt-cache", "on", "enable"),
        ("slow_tokens_per_second", "batch-size", "default", "reset"),
    ],
)
def test_m167_tuning_advisor_hardening_cases_are_safe_bounded_and_rollback_aware(
    signal_kind: str,
    setting_name: str,
    suggested_value: str,
    action_kind: str,
) -> None:
    recommendation = recommend_m165_llama_cpp_adjustment(
        [_observation(signal_kind)],
        current_settings={
            "ctx-size": "4096",
            "n-gpu-layers": "8",
            "parallel": "4",
            "batch-size": "512",
            "prompt-cache": "off",
        },
    )

    _assert_safe_recommendation(recommendation)
    assert recommendation.setting_name == setting_name
    assert recommendation.suggested_value == suggested_value
    assert recommendation.action_kind == action_kind
    assert recommendation.setting_change_count == 1


def test_m167_tuning_advisor_prioritizes_one_change_for_multiple_signals() -> None:
    recommendation = recommend_m165_llama_cpp_adjustment(
        [
            _observation("lag"),
            _observation("out_of_memory"),
            _observation("slow_tokens_per_second"),
        ],
        current_settings={"n-gpu-layers": "6", "parallel": "4", "batch-size": "512"},
    )

    _assert_safe_recommendation(recommendation)
    assert recommendation.setting_name == "n-gpu-layers"
    assert recommendation.suggested_value == "3"
    assert recommendation.setting_change_count == 1


def test_m167_tuning_advisor_unknown_state_is_conservative_and_operator_actionable() -> None:
    recommendation = recommend_m165_llama_cpp_adjustment([_observation("unknown")])

    _assert_safe_recommendation(recommendation)
    assert recommendation.action_kind == "noop"
    assert recommendation.setting_name == "settings"
    assert recommendation.suggested_value == "unchanged"
    assert recommendation.setting_change_count == 0
    assert "operator review" in recommendation.safe_reason.lower()


@pytest.mark.parametrize(
    ("flag_name", "reason"),
    [
        ("raw_prompt_included", "M165_RAW_PROMPT_DENIED"),
        ("raw_response_included", "M165_RAW_RESPONSE_DENIED"),
        ("raw_provider_payload_included", "M165_RAW_PROVIDER_PAYLOAD_DENIED"),
        ("raw_log_included", "M165_RAW_LOG_DENIED"),
        ("raw_path_included", "M165_RAW_PATH_DENIED"),
        ("username_included", "M165_USERNAME_DENIED"),
        ("hostname_included", "M165_HOSTNAME_DENIED"),
        ("serial_included", "M165_SERIAL_DENIED"),
        ("environment_dump_included", "M165_ENVIRONMENT_DUMP_DENIED"),
        ("secret_included", "M165_SECRET_DENIED"),
    ],
)
def test_m167_tuning_observations_reject_raw_or_sensitive_evidence(
    flag_name: str,
    reason: str,
) -> None:
    with pytest.raises(ValueError, match=reason):
        M165RuntimeObservation(
            observation_ref="observation-ref:m167:tuning:redaction-denial",
            signal_kind="lag",
            safe_summary="Redacted lag summary only.",
            **{flag_name: True},
        )


def test_m167_tuning_apply_is_one_change_and_rolls_back_on_failure() -> None:
    request = M165SettingsApplyRequest(
        request_ref="settings-apply-request:m167:one-change-rollback",
        approval_ref="approval-ref:m167:tuning:operator-confirmed",
        previous_preset_ref="preset-ref:m167:known-good",
        target_preset_ref="preset-ref:m167:parallel-one",
        settings={"parallel": "1"},
        approved=True,
        restart_requested=True,
        rollback_on_failure=True,
    )
    applier = FakeM165SettingsApplier(apply_ok=False, rollback_ok=True)

    result = apply_m165_settings_with_rollback(request, applier=applier)

    assert applier.applied_settings == [{"parallel": "1"}]
    assert applier.rollback_calls == 1
    assert result.settings_applied is False
    assert result.restart_performed is False
    assert result.rollback_performed is True
    assert result.active_preset_ref == "preset-ref:m167:known-good"
    assert result.previous_preset_ref == "preset-ref:m167:known-good"
    assert "rollback was attempted" in result.safe_summary.lower()


def test_m167_tuning_apply_rejects_multi_setting_changes() -> None:
    request = M165SettingsApplyRequest(
        request_ref="settings-apply-request:m167:multi-change-denied",
        approval_ref="approval-ref:m167:tuning:operator-confirmed",
        previous_preset_ref="preset-ref:m167:known-good",
        target_preset_ref="preset-ref:m167:multi-change",
        settings={"parallel": "1", "batch-size": "default"},
        approved=True,
        restart_requested=True,
        rollback_on_failure=True,
    )

    with pytest.raises(ValueError, match="M165_ONE_SETTING_CHANGE_REQUIRED"):
        validate_m165_settings_apply_request(request)
