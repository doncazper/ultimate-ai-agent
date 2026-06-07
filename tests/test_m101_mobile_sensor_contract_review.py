import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileSensorCapabilityClass,
    MobileSensorCapabilityContract,
    MobileSensorContractReviewPolicy,
    MobileSensorContractReviewStatus,
    MobileSensorRiskClass,
    build_mobile_sensor_contract_review_report,
    validate_mobile_sensor_capability_contract,
    validate_mobile_sensor_contract_review_policy,
    validate_mobile_sensor_contract_review_report,
    validate_mobile_sensor_permission_state_contract,
)


def test_m101_mobile_sensor_contract_review_is_contract_only() -> None:
    report = build_mobile_sensor_contract_review_report()

    assert report.status == MobileSensorContractReviewStatus.contract_only
    assert report.contract_only is True
    assert report.sensor_taxonomy_defined is True
    assert report.permission_state_contract_defined is True
    assert report.sensor_risk_classification_defined is True
    assert report.consent_revocation_required is True
    assert report.audit_required is True
    assert report.sensors_default_off is True
    assert report.unknown_sensor_denied is True
    assert report.runtime_sensor_access_enabled is False
    assert report.native_permission_prompt_enabled is False
    assert report.background_collection_enabled is False
    assert report.location_sensor_enabled is False
    assert report.camera_sensor_enabled is False
    assert report.photos_sensor_enabled is False
    assert report.microphone_sensor_enabled is False
    assert report.raw_sensor_payload_enabled is False
    assert report.backend_route_added is False
    assert report.dependency_added is False
    assert report.memory_write_enabled is False
    assert report.context_injection_enabled is False
    assert report.execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M101_MOBILE_SENSOR_CONTRACT_REVIEW_ONLY",
        "M101_SENSOR_TAXONOMY_DEFINED",
        "M101_PERMISSION_STATE_CONTRACT_DEFINED",
        "M101_SENSOR_RISK_CLASSIFICATION_DEFINED",
        "M101_SENSORS_DEFAULT_OFF",
        "M101_UNKNOWN_SENSOR_DENIED",
        "M102_REMAINS_FUTURE",
    ]


def test_m101_sensor_taxonomy_covers_known_sensors_and_excludes_unknown() -> None:
    report = build_mobile_sensor_contract_review_report()
    classes = {contract.capability_class for contract in report.capability_contracts}

    assert MobileSensorCapabilityClass.location in classes
    assert MobileSensorCapabilityClass.camera in classes
    assert MobileSensorCapabilityClass.photos in classes
    assert MobileSensorCapabilityClass.microphone in classes
    assert MobileSensorCapabilityClass.unknown not in classes
    assert all(contract.default_off for contract in report.capability_contracts)
    assert all(contract.explicit_consent_required for contract in report.capability_contracts)
    assert all(contract.revocable for contract in report.capability_contracts)
    assert all(contract.audit_required for contract in report.capability_contracts)
    assert all(not contract.runtime_sensor_access_enabled for contract in report.capability_contracts)
    assert all(not contract.native_permission_prompt_enabled for contract in report.capability_contracts)
    assert all(not contract.background_collection_enabled for contract in report.capability_contracts)
    assert all(not contract.raw_sensor_payload_enabled for contract in report.capability_contracts)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_sensor_access_enabled", "RUNTIME_SENSOR_ACCESS_DENIED"),
        ("native_permission_prompt_enabled", "NATIVE_PERMISSION_PROMPT_DENIED"),
        ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
        ("location_sensor_enabled", "LOCATION_SENSOR_DENIED"),
        ("camera_sensor_enabled", "CAMERA_SENSOR_DENIED"),
        ("photos_sensor_enabled", "PHOTOS_SENSOR_DENIED"),
        ("microphone_sensor_enabled", "MICROPHONE_SENSOR_DENIED"),
        ("raw_sensor_payload_enabled", "RAW_SENSOR_PAYLOAD_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("execution_enabled", "EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m101_policy_denies_sensor_runtime_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_sensor_contract_review_policy(
            MobileSensorContractReviewPolicy(**{field: True})
        )


def test_m101_unknown_sensor_contract_is_denied() -> None:
    with pytest.raises(ValueError, match="UNKNOWN_SENSOR_DENIED"):
        validate_mobile_sensor_capability_contract(
            MobileSensorCapabilityContract(
                sensor_ref="mobile-sensor-contract:m101:unknown",
                capability_class=MobileSensorCapabilityClass.unknown,
                safe_label="Unknown",
                safe_purpose_summary="Unknown sensor class must not be accepted.",
                risk_class=MobileSensorRiskClass.prohibited_unknown,
            )
        )


def test_m101_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_mobile_sensor_contract_review_report()

    for update, reason in [
        ({"runtime_sensor_access_enabled": True}, "RUNTIME_SENSOR_ACCESS_DENIED"),
        ({"native_permission_prompt_enabled": True}, "NATIVE_PERMISSION_PROMPT_DENIED"),
        ({"background_collection_enabled": True}, "BACKGROUND_COLLECTION_DENIED"),
        ({"raw_sensor_payload_enabled": True}, "RAW_SENSOR_PAYLOAD_DENIED"),
        ({"production_authority_enabled": True}, "PRODUCTION_AUTHORITY_DENIED"),
        ({"side_effects_performed": ["requested location permission"]}, "SIDE_EFFECTS_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_mobile_sensor_contract_review_report(report.model_copy(update=update))


def test_m101_rejects_duplicate_sensor_refs_and_secret_metadata() -> None:
    report = build_mobile_sensor_contract_review_report()
    duplicate = report.model_copy(
        update={"capability_contracts": [report.capability_contracts[0], report.capability_contracts[0]]}
    )

    with pytest.raises(ValueError, match="M101_SENSOR_REF_DUPLICATE"):
        validate_mobile_sensor_contract_review_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M101_SENSOR_CONTENT_DENIED"):
        validate_mobile_sensor_contract_review_report(
            report.model_copy(update={"metadata": {"api_key": "abc123supersecret"}})
        )


def test_m101_rejects_unsafe_capability_and_permission_state_mutations() -> None:
    report = build_mobile_sensor_contract_review_report()
    unsafe_capability = report.capability_contracts[0].model_copy(
        update={"runtime_sensor_access_enabled": True}
    )
    unsafe_state = report.permission_state_contracts[0].model_copy(
        update={"runtime_permission_granted": True}
    )

    with pytest.raises(ValueError, match="RUNTIME_SENSOR_ACCESS_DENIED"):
        validate_mobile_sensor_contract_review_report(
            report.model_copy(
                update={"capability_contracts": [unsafe_capability] + report.capability_contracts[1:]}
            )
        )

    with pytest.raises(ValueError, match="RUNTIME_SENSOR_ACCESS_DENIED"):
        validate_mobile_sensor_permission_state_contract(unsafe_state)
