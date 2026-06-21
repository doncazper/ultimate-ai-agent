from typing import Any
import pytest

from ultimate_ai_agent.core.production_readiness import (
    REQUIRED_M167_EVIDENCE_KINDS,
    REQUIRED_M167_HARDWARE_PROFILES,
    LiveModelHardeningEvidenceKind,
    LiveModelHardeningEvidenceStatus,
    LiveModelHardeningHardwareProfile,
    LiveModelProductionHardeningStatus,
    build_m167_fixture_live_model_hardening_evidence,
    build_m167_live_model_production_hardening_report,
    validate_m167_live_model_hardening_evidence_record,
    validate_m167_live_model_production_hardening_policy,
    validate_m167_live_model_production_hardening_report,
)


def _reviewed(evidence: Any) -> Any:
    return [
        item.model_copy(
            update={
                "actual_live_evidence": True,
                "reviewed_by_ref": f"review-ref:m167:{item.evidence_ref.split(':')[-1]}",
            }
        )
        for item in evidence
    ]


def test_m167_fixture_evidence_covers_required_live_hardening_lanes() -> None:
    evidence = build_m167_fixture_live_model_hardening_evidence()

    matrix_profiles = [
        item.hardware_profile.value
        for item in evidence
        if item.kind == LiveModelHardeningEvidenceKind.model_matrix
    ]
    non_matrix_kinds = [
        item.kind.value
        for item in evidence
        if item.kind != LiveModelHardeningEvidenceKind.model_matrix
    ]

    assert matrix_profiles == list(REQUIRED_M167_HARDWARE_PROFILES)
    assert non_matrix_kinds == [
        kind
        for kind in REQUIRED_M167_EVIDENCE_KINDS
        if kind != "model_matrix"
    ]
    for item in evidence:
        assert item.source_checkpoint_ref == "checkpoint:m166"
        assert item.status == LiveModelHardeningEvidenceStatus.passed
        assert item.redacted is True
        assert item.safe_refs_only is True
        assert item.loopback_only is True
        assert item.openwebui_shell_only is True
        assert item.openwebui_is_agent_brain is False
        assert item.raw_prompt_included is False
        assert item.raw_response_included is False
        assert item.raw_log_included is False
        assert item.credential_material_included is False
        assert item.blocker_refs == []
        assert item.actual_live_evidence is False
        assert item.reviewed_by_ref is None


def test_m167_fixture_evidence_cannot_pass_live_hardening_report() -> None:
    evidence = build_m167_fixture_live_model_hardening_evidence()

    with pytest.raises(ValueError, match="M167_REVIEWED_LIVE_EVIDENCE_REQUIRED"):
        build_m167_live_model_production_hardening_report(evidence_records=evidence)


def test_m167_report_passes_when_all_live_evidence_is_reviewed() -> None:
    evidence = _reviewed(build_m167_fixture_live_model_hardening_evidence())
    report = build_m167_live_model_production_hardening_report(evidence_records=evidence)

    assert report.status == LiveModelProductionHardeningStatus.live_production_hardening_passed
    assert report.source_checkpoint_ref == "checkpoint:m166"
    assert report.evidence_refs == [item.evidence_ref for item in evidence]
    assert report.required_evidence_kinds == [
        LiveModelHardeningEvidenceKind(kind) for kind in REQUIRED_M167_EVIDENCE_KINDS
    ]
    assert report.required_hardware_profiles == [
        LiveModelHardeningHardwareProfile(profile)
        for profile in REQUIRED_M167_HARDWARE_PROFILES
    ]
    assert report.model_matrix_passed is True
    assert report.installer_runtime_packaging_ready is True
    assert report.selection_quality_validated is True
    assert report.tuning_loop_hardened is True
    assert report.openwebui_real_e2e_passed is True
    assert report.load_soak_passed is True
    assert report.operational_controls_ready is True
    assert report.production_authority_inherited_from_m166 is True
    assert report.new_production_authority_granted is False
    assert report.side_effects_performed == []
    assert "M167_NO_NEW_AUTHORITY_GRANTED" in report.reason_codes
    assert validate_m167_live_model_production_hardening_report(report) == report


def test_m167_report_requires_all_hardware_profiles() -> None:
    evidence = [
        item
        for item in _reviewed(build_m167_fixture_live_model_hardening_evidence())
        if item.hardware_profile != LiveModelHardeningHardwareProfile.limited_disk
    ]

    with pytest.raises(ValueError, match="M167_ALL_REQUIRED_HARDWARE_PROFILES_REQUIRED"):
        build_m167_live_model_production_hardening_report(evidence_records=evidence)


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"status": LiveModelHardeningEvidenceStatus.failed}, "M167_EVIDENCE_MUST_PASS"),
        ({"blocker_refs": ["blocker-ref:m167:critical"]}, "M167_BLOCKERS_MUST_BE_EMPTY"),
        ({"redacted": False}, "M167_REDACTED_EVIDENCE_REQUIRED"),
        ({"raw_prompt_included": True}, "M167_RAW_PROMPT_DENIED"),
        ({"raw_response_included": True}, "M167_RAW_RESPONSE_DENIED"),
        ({"raw_log_included": True}, "M167_RAW_LOG_DENIED"),
        ({"raw_path_included": True}, "M167_RAW_PATH_DENIED"),
        ({"credential_material_included": True}, "M167_CREDENTIAL_MATERIAL_DENIED"),
        ({"openwebui_is_agent_brain": True}, "M167_OPENWEBUI_AUTHORITY_DENIED"),
        ({"unsupported_network_used": True}, "M167_UNSUPPORTED_NETWORK_DENIED"),
        ({"actual_live_evidence": False}, "M167_REVIEWED_LIVE_EVIDENCE_REQUIRED"),
        (
            {"source_checkpoint_ref": "checkpoint:m165"},
            "M167_SOURCE_CHECKPOINT_M166_REQUIRED",
        ),
    ],
)
def test_m167_evidence_rejects_unsafe_mutations(update: Any, reason: str) -> None:
    evidence = _reviewed(build_m167_fixture_live_model_hardening_evidence())[0]

    with pytest.raises(ValueError, match=reason):
        validate_m167_live_model_hardening_evidence_record(evidence.model_copy(update=update))


def test_m167_evidence_requires_each_lane_coverage_flag() -> None:
    evidence = _reviewed(build_m167_fixture_live_model_hardening_evidence())[0]
    flags = dict(evidence.coverage_flags)
    flags["hf_search_verified"] = False

    with pytest.raises(ValueError, match="M167_COVERAGE_FLAG_REQUIRED:hf_search_verified"):
        validate_m167_live_model_hardening_evidence_record(
            evidence.model_copy(update={"coverage_flags": flags})
        )


@pytest.mark.parametrize(
    ("update", "reason"),
    [
        ({"model_matrix_passed": False}, "M167_MODEL_MATRIX_REQUIRED"),
        ({"installer_runtime_packaging_ready": False}, "M167_INSTALLER_RUNTIME_PACKAGING_REQUIRED"),
        ({"selection_quality_validated": False}, "M167_SELECTION_QUALITY_REQUIRED"),
        ({"tuning_loop_hardened": False}, "M167_TUNING_LOOP_REQUIRED"),
        ({"openwebui_real_e2e_passed": False}, "M167_OPENWEBUI_E2E_REQUIRED"),
        ({"load_soak_passed": False}, "M167_LOAD_SOAK_REQUIRED"),
        ({"operational_controls_ready": False}, "M167_OPERATIONAL_CONTROLS_REQUIRED"),
        ({"new_production_authority_granted": True}, "M167_NEW_AUTHORITY_DENIED"),
        ({"backend_route_added": True}, "M167_BACKEND_ROUTE_DENIED"),
        ({"control_center_control_added": True}, "M167_CONTROL_CENTER_CONTROL_DENIED"),
        ({"dependency_added": True}, "M167_DEPENDENCY_DENIED"),
        ({"runtime_execution_started_by_report": True}, "M167_REPORT_RUNTIME_EXECUTION_DENIED"),
        ({"model_download_started_by_report": True}, "M167_REPORT_DOWNLOAD_DENIED"),
        ({"raw_prompt_exported": True}, "M167_RAW_PROMPT_DENIED"),
        ({"credential_material_exported": True}, "M167_CREDENTIAL_MATERIAL_DENIED"),
        ({"side_effects_performed": ["deploy"]}, "M167_REPORT_SIDE_EFFECTS_DENIED"),
    ],
)
def test_m167_report_rejects_unsafe_mutations(update: Any, reason: str) -> None:
    report = build_m167_live_model_production_hardening_report(
        evidence_records=_reviewed(build_m167_fixture_live_model_hardening_evidence())
    )

    with pytest.raises(ValueError, match=reason):
        validate_m167_live_model_production_hardening_report(report.model_copy(update=update))


def test_m167_policy_requires_exact_evidence_profiles_and_no_new_authority() -> None:
    policy = validate_m167_live_model_production_hardening_policy(
        {
            "actual_live_evidence_required": True,
            "reviewed_evidence_required": True,
            "no_new_authority_required": True,
        }
    )

    assert policy.source_checkpoint_ref == "checkpoint:m166"
    assert [kind.value for kind in policy.required_evidence_kinds] == list(
        REQUIRED_M167_EVIDENCE_KINDS
    )
    assert [profile.value for profile in policy.required_hardware_profiles] == list(
        REQUIRED_M167_HARDWARE_PROFILES
    )

