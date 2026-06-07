import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobilePermissionCategory,
    MobilePermissionModelV1Policy,
    MobilePermissionModelV1Status,
    MobilePermissionTaxonomyEntry,
    build_mobile_permission_model_v1_report,
    validate_mobile_permission_model_v1_policy,
    validate_mobile_permission_model_v1_report,
    validate_mobile_permission_taxonomy_entry,
)


def test_m100_mobile_permission_model_v1_is_contract_only() -> None:
    report = build_mobile_permission_model_v1_report()

    assert report.status == MobilePermissionModelV1Status.contract_only
    assert report.contract_only is True
    assert report.permission_taxonomy_defined is True
    assert report.consent_model_defined is True
    assert report.revocation_model_defined is True
    assert report.privacy_copy_defined is True
    assert report.permission_audit_defined is True
    assert report.sensors_remain_off is True
    assert report.no_background_collection is True
    assert report.runtime_permission_prompts_enabled is False
    assert report.native_permission_requests_enabled is False
    assert report.mobile_sensor_enabled is False
    assert report.location_access_enabled is False
    assert report.camera_access_enabled is False
    assert report.photos_access_enabled is False
    assert report.microphone_access_enabled is False
    assert report.background_collection_enabled is False
    assert report.push_execution_enabled is False
    assert report.production_authority_enabled is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M100_MOBILE_PERMISSION_MODEL_V1_CONTRACT_ONLY",
        "M100_PERMISSION_TAXONOMY_DEFINED",
        "M100_CONSENT_REVOCATION_REQUIRED",
        "M100_SENSORS_REMAIN_OFF",
        "M100_NO_BACKGROUND_COLLECTION",
        "POST_M100_REMAINS_FUTURE",
    ]


def test_m100_taxonomy_entries_require_privacy_copy_and_no_runtime_prompt() -> None:
    report = build_mobile_permission_model_v1_report()
    categories = {entry.category for entry in report.taxonomy}

    assert MobilePermissionCategory.camera in categories
    assert MobilePermissionCategory.location in categories
    assert MobilePermissionCategory.photos in categories
    assert all(entry.safe_privacy_copy for entry in report.taxonomy)
    assert all(entry.planned_disabled for entry in report.taxonomy)
    assert all(entry.requires_explicit_consent for entry in report.taxonomy)
    assert all(entry.revocable for entry in report.taxonomy)
    assert all(entry.runtime_prompt_enabled is False for entry in report.taxonomy)
    assert all(entry.native_permission_request_enabled is False for entry in report.taxonomy)
    assert all(entry.sensor_access_enabled is False for entry in report.taxonomy)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("runtime_permission_prompts_enabled", "RUNTIME_PERMISSION_PROMPT_DENIED"),
        ("native_permission_requests_enabled", "NATIVE_PERMISSION_REQUEST_DENIED"),
        ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
        ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
        ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
        ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
        ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
        ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
        ("push_execution_enabled", "PUSH_EXECUTION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
        ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ],
)
def test_m100_policy_denies_runtime_permission_authority(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_mobile_permission_model_v1_policy(
            MobilePermissionModelV1Policy(**{field: True})
        )


def test_m100_revalidates_model_copy_mutated_report_fields() -> None:
    report = build_mobile_permission_model_v1_report()

    with pytest.raises(ValueError, match="MOBILE_SENSOR_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(update={"mobile_sensor_enabled": True})
        )

    with pytest.raises(ValueError, match="BACKGROUND_COLLECTION_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(update={"background_collection_enabled": True})
        )

    with pytest.raises(ValueError, match="SIDE_EFFECTS_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(update={"side_effects_performed": ["requested os prompt"]})
        )


def test_m100_rejects_duplicate_permission_refs_and_secret_metadata() -> None:
    report = build_mobile_permission_model_v1_report()
    duplicate = report.model_copy(
        update={"taxonomy": [report.taxonomy[0], report.taxonomy[0]]}
    )

    with pytest.raises(ValueError, match="M100_PERMISSION_REF_DUPLICATE"):
        validate_mobile_permission_model_v1_report(duplicate)

    with pytest.raises(ValueError, match="SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(update={"metadata": {"api_key": "abc123supersecret"}})
        )


def test_m100_rejects_unsafe_taxonomy_model_copy_mutations() -> None:
    report = build_mobile_permission_model_v1_report()
    unsafe_entry = report.taxonomy[0].model_copy(
        update={"native_permission_request_enabled": True}
    )

    with pytest.raises(ValueError, match="NATIVE_PERMISSION_REQUEST_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(update={"taxonomy": [unsafe_entry] + report.taxonomy[1:]})
        )

    with pytest.raises(ValueError, match="SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED"):
        MobilePermissionTaxonomyEntry(
            permission_ref="mobile-permission-v1:camera-secret",
            category=MobilePermissionCategory.camera,
            safe_label="Camera",
            safe_privacy_copy="Explains future camera permission review without enabling access.",
            metadata={"token": "abc123supersecret"},
        )


def test_m100_exported_taxonomy_validator_revalidates_model_copy_fields() -> None:
    report = build_mobile_permission_model_v1_report()
    unsafe_entry = report.taxonomy[0].model_copy(
        update={"safe_privacy_copy": "Token abc123supersecret must not appear"}
    )

    with pytest.raises(ValueError, match="SECRET_LIKE_AUTONOMY_CONTENT_DENIED"):
        validate_mobile_permission_taxonomy_entry(unsafe_entry)


def test_m100_rejects_secret_like_consent_and_revocation_metadata() -> None:
    report = build_mobile_permission_model_v1_report()
    unsafe_consent = report.consent_contracts[0].model_copy(
        update={"metadata": {"password": "abc123supersecret"}}
    )
    unsafe_revocation = report.revocation_contracts[0].model_copy(
        update={"metadata": {"api_key": "abc123supersecret"}}
    )

    with pytest.raises(ValueError, match="SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(
                update={
                    "consent_contracts": [unsafe_consent] + report.consent_contracts[1:]
                }
            )
        )

    with pytest.raises(ValueError, match="SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED"):
        validate_mobile_permission_model_v1_report(
            report.model_copy(
                update={
                    "revocation_contracts": [unsafe_revocation]
                    + report.revocation_contracts[1:]
                }
            )
        )
