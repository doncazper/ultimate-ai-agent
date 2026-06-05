import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileApiBoundaryRefresh,
    MobileApiBoundaryStatus,
    MobileCompanionSurface,
    MobileProductRole,
    MobileProductSurfaceContract,
    assert_mobile_product_contract_refresh_only,
    build_default_mobile_product_contract_refresh,
    validate_mobile_api_boundary_refresh,
    validate_mobile_product_surface_contract,
)


def test_default_m42_mobile_product_contract_refresh_is_planning_only() -> None:
    refresh = build_default_mobile_product_contract_refresh()

    assert refresh.milestone == "M42"
    assert refresh.version == "0.46.0"
    assert refresh.contract_refresh_only is True
    assert refresh.m43_read_only_api_future is True
    assert refresh.m44_ios_skeleton_future is True
    assert refresh.native_app_implemented is False
    assert refresh.mobile_api_implemented is False
    assert refresh.mobile_sensor_access_enabled is False
    assert refresh.os_permission_integration_enabled is False
    assert refresh.background_service_enabled is False
    assert refresh.signing_or_store_workflow_enabled is False
    assert refresh.approval_capture_enabled is False
    assert refresh.approval_execution_enabled is False
    assert refresh.memory_write_enabled is False
    assert refresh.context_injection_enabled is False
    assert refresh.raw_payload_exposure_enabled is False
    assert refresh.production_authority_enabled is False
    assert {role.role for role in refresh.product_roles} >= {
        MobileProductRole.governance_surface,
        MobileProductRole.review_surface,
        MobileProductRole.capture_inbox_surface,
        MobileProductRole.status_surface,
    }

    assert_mobile_product_contract_refresh_only(refresh)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("native_app_implemented", "native app"),
        ("mobile_api_implemented", "mobile api"),
        ("mobile_sensor_access_enabled", "mobile sensor access"),
        ("os_permission_integration_enabled", "OS permission integration"),
        ("background_service_enabled", "background service"),
        ("signing_or_store_workflow_enabled", "signing or store workflow"),
        ("approval_capture_enabled", "approval capture"),
        ("approval_execution_enabled", "approval execution"),
        ("memory_write_enabled", "memory write"),
        ("context_injection_enabled", "context injection"),
        ("raw_payload_exposure_enabled", "raw payload exposure"),
        ("production_authority_enabled", "production authority"),
    ],
)
def test_m42_model_copy_mutated_authority_flags_are_denied(field_name: str, match: str) -> None:
    refresh = build_default_mobile_product_contract_refresh().model_copy(
        update={field_name: True}
    )

    with pytest.raises(ValueError, match=match):
        assert_mobile_product_contract_refresh_only(refresh)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("review_only", "review-only"),
        ("read_only", "read-only"),
        ("authority_claimed", "authority"),
        ("approval_execution_enabled", "approval execution"),
        ("sensor_access_enabled", "sensor access"),
        ("background_service_enabled", "background service"),
        ("native_implementation_started", "native implementation"),
        ("raw_payload_display_enabled", "raw payload display"),
    ],
)
def test_m42_surface_contract_rejects_enabled_runtime_flags(
    field_name: str, match: str
) -> None:
    base = MobileProductSurfaceContract(
        role=MobileProductRole.review_surface,
        surfaces=[MobileCompanionSurface.receipt_view_planned],
        safe_summary="review surface planning only",
    )
    value = False if field_name in {"review_only", "read_only"} else True
    surface = base.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        validate_mobile_product_surface_contract(surface)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("m43_boundary_only", "M43"),
        ("backend_route_added", "backend route"),
        ("mutation_enabled", "mutation"),
        ("raw_data_enabled", "raw data"),
        ("sensor_endpoint_enabled", "sensor endpoint"),
        ("approval_execution_enabled", "approval execution"),
        ("credential_handling_enabled", "credential handling"),
    ],
)
def test_m42_api_boundary_rejects_route_or_runtime_flags(
    field_name: str, match: str
) -> None:
    base = MobileApiBoundaryRefresh(
        status=MobileApiBoundaryStatus.blocked_until_m43,
        safe_summary="M43 read-only API boundary planning only",
    )
    value = False if field_name == "m43_boundary_only" else True
    boundary = base.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        validate_mobile_api_boundary_refresh(boundary)


def test_m42_safe_summary_rejects_secret_like_text() -> None:
    refresh = build_default_mobile_product_contract_refresh().model_copy(
        update={"safe_summary": "token=abc123 should never appear"}
    )

    with pytest.raises(ValueError, match="secret"):
        assert_mobile_product_contract_refresh_only(refresh)
