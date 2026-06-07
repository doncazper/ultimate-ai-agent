import pytest

from ultimate_ai_agent.core.mobile_companion import (
    LocationSensorAccuracyClass,
    LocationSensorOffByDefaultPolicy,
    LocationSensorOffByDefaultStatus,
    LocationSensorUseClass,
    build_location_sensor_off_by_default_report,
    validate_location_sensor_off_by_default_policy,
    validate_location_sensor_off_by_default_report,
    validate_location_sensor_scope_contract,
)


def test_m102_location_sensor_contract_is_off_by_default() -> None:
    report = build_location_sensor_off_by_default_report()

    assert report.status == LocationSensorOffByDefaultStatus.contract_only
    assert report.contract_only is True
    assert report.location_sensor_default_off is True
    assert report.location_permission_scope_defined is True
    assert report.foreground_only_review_defined is True
    assert report.precise_location_separate_approval_required is True
    assert report.consent_required is True
    assert report.revocation_required is True
    assert report.audit_required is True
    assert report.runtime_location_access_enabled is False
    assert report.native_permission_prompt_enabled is False
    assert report.background_location_enabled is False
    assert report.raw_coordinates_enabled is False
    assert report.location_history_enabled is False
    assert report.geofence_enabled is False
    assert report.location_export_enabled is False
    assert report.backend_route_added is False
    assert report.control_center_control_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M102_LOCATION_SENSOR_OFF_BY_DEFAULT",
        "M102_LOCATION_PERMISSION_SCOPE_DEFINED",
        "M102_FOREGROUND_ONLY_REVIEW_DEFINED",
        "M102_PRECISE_LOCATION_SEPARATE_APPROVAL_REQUIRED",
        "M102_NO_RUNTIME_LOCATION_ACCESS",
        "M103_REMAINS_FUTURE",
    ]


def test_m102_scope_contract_requires_foreground_review_without_accuracy_request() -> None:
    report = build_location_sensor_off_by_default_report()
    scope = report.scope_contracts[0]

    assert scope.sensor_ref == "mobile-sensor-contract:m101:location"
    assert scope.use_class == LocationSensorUseClass.foreground_review_candidate
    assert scope.accuracy_class == LocationSensorAccuracyClass.not_requested
    assert scope.disabled_by_default is True
    assert scope.exact_scope_required is True
    assert scope.foreground_only is True
    assert scope.separate_precise_approval_required is True
    assert scope.consent_required is True
    assert scope.revocable is True
    assert scope.audit_required is True
    assert scope.runtime_location_access_enabled is False
    assert scope.native_permission_prompt_enabled is False
    assert scope.background_location_enabled is False
    assert scope.raw_coordinates_enabled is False
    assert scope.side_effects_performed == []


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_location_access_enabled", "RUNTIME_LOCATION_ACCESS_DENIED"),
        ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
        ("background_location_enabled", "BACKGROUND_LOCATION_DENIED"),
        ("raw_coordinates_enabled", "RAW_COORDINATES_DENIED"),
        ("location_history_enabled", "LOCATION_HISTORY_DENIED"),
        ("geofence_enabled", "GEOFENCE_DENIED"),
        ("location_export_enabled", "LOCATION_EXPORT_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m102_policy_denies_location_runtime_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_location_sensor_off_by_default_policy(
            LocationSensorOffByDefaultPolicy(**{field: True})
        )


def test_m102_scope_denies_background_unknown_and_accuracy_requests() -> None:
    report = build_location_sensor_off_by_default_report()
    scope = report.scope_contracts[0]

    with pytest.raises(ValueError, match="BACKGROUND_OR_UNKNOWN_LOCATION_USE_DENIED"):
        validate_location_sensor_scope_contract(
            scope.model_copy(update={"use_class": LocationSensorUseClass.background_prohibited})
        )
    with pytest.raises(ValueError, match="BACKGROUND_OR_UNKNOWN_LOCATION_USE_DENIED"):
        validate_location_sensor_scope_contract(
            scope.model_copy(update={"use_class": LocationSensorUseClass.unknown})
        )
    with pytest.raises(ValueError, match="LOCATION_ACCURACY_REQUEST_DENIED"):
        validate_location_sensor_scope_contract(
            scope.model_copy(update={"accuracy_class": LocationSensorAccuracyClass.approximate_candidate})
        )
    with pytest.raises(ValueError, match="LOCATION_ACCURACY_REQUEST_DENIED"):
        validate_location_sensor_scope_contract(
            scope.model_copy(update={"accuracy_class": LocationSensorAccuracyClass.precise_candidate})
        )


def test_m102_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_location_sensor_off_by_default_report()

    for update, reason in [
        ({"runtime_location_access_enabled": True}, "RUNTIME_LOCATION_ACCESS_DENIED"),
        ({"native_permission_prompt_enabled": True}, "NATIVE_PERMISSION_PROMPT_DENIED"),
        ({"background_location_enabled": True}, "BACKGROUND_LOCATION_DENIED"),
        ({"raw_coordinates_enabled": True}, "RAW_COORDINATES_DENIED"),
        ({"location_history_enabled": True}, "LOCATION_HISTORY_DENIED"),
        ({"geofence_enabled": True}, "GEOFENCE_DENIED"),
        ({"location_export_enabled": True}, "LOCATION_EXPORT_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["requested location permission"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_location_sensor_off_by_default_report(report.model_copy(update=update))


def test_m102_rejects_duplicate_scope_refs_and_secret_metadata() -> None:
    report = build_location_sensor_off_by_default_report()
    duplicate = report.model_copy(update={"scope_contracts": [report.scope_contracts[0], report.scope_contracts[0]]})

    with pytest.raises(ValueError, match="M102_LOCATION_SCOPE_REF_DUPLICATE"):
        validate_location_sensor_off_by_default_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M102_LOCATION_CONTENT_DENIED"):
        validate_location_sensor_off_by_default_report(
            report.model_copy(update={"metadata": {"api_key": "abc123supersecret"}})
        )
