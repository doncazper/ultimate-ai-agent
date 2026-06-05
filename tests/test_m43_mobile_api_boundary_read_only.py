import pytest

from ultimate_ai_agent.core.mobile_companion import (
    MobileApiEndpointKind,
    MobileApiHttpMethod,
    MobileReadOnlyApiEndpointContract,
    assert_mobile_api_boundary_read_only,
    build_default_mobile_read_only_api_boundary,
    validate_mobile_api_endpoint_contract,
)


def test_default_m43_mobile_api_boundary_is_read_only_and_contract_only() -> None:
    boundary = build_default_mobile_read_only_api_boundary()

    assert boundary.milestone == "M43"
    assert boundary.version == "0.47.0"
    assert boundary.boundary_contract_only is True
    assert boundary.read_only_boundary is True
    assert boundary.redacted_summary_only is True
    assert boundary.backend_routes_added is False
    assert boundary.mobile_mutation_enabled is False
    assert boundary.mobile_sensor_access_enabled is False
    assert boundary.approval_capture_enabled is False
    assert boundary.approval_execution_enabled is False
    assert boundary.raw_data_enabled is False
    assert boundary.raw_payload_exposure_enabled is False
    assert boundary.context_injection_enabled is False
    assert boundary.memory_write_enabled is False
    assert boundary.export_enabled is False
    assert boundary.execution_enabled is False
    assert boundary.credential_or_cookie_handling_enabled is False
    assert boundary.background_collection_enabled is False
    assert boundary.m44_ios_skeleton_future is True
    assert {endpoint.kind for endpoint in boundary.endpoints} >= {
        MobileApiEndpointKind.manifest_summary,
        MobileApiEndpointKind.approval_status_summary,
        MobileApiEndpointKind.receipt_summary,
        MobileApiEndpointKind.review_packet_summary,
    }

    assert_mobile_api_boundary_read_only(boundary)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("boundary_contract_only", "contract-only"),
        ("read_only_boundary", "read-only"),
        ("redacted_summary_only", "redacted summary"),
        ("backend_routes_added", "backend route"),
        ("mobile_mutation_enabled", "mobile mutation"),
        ("mobile_sensor_access_enabled", "mobile sensor access"),
        ("approval_capture_enabled", "approval capture"),
        ("approval_execution_enabled", "approval execution"),
        ("raw_data_enabled", "raw data"),
        ("raw_payload_exposure_enabled", "raw payload exposure"),
        ("context_injection_enabled", "context injection"),
        ("memory_write_enabled", "memory write"),
        ("export_enabled", "export"),
        ("execution_enabled", "execution"),
        ("credential_or_cookie_handling_enabled", "credential"),
        ("background_collection_enabled", "background collection"),
        ("m44_ios_skeleton_future", "M44"),
    ],
)
def test_m43_boundary_rejects_model_copy_mutated_authority_flags(
    field_name: str, match: str
) -> None:
    boundary = build_default_mobile_read_only_api_boundary()
    value = False if field_name in {
        "boundary_contract_only",
        "read_only_boundary",
        "redacted_summary_only",
        "m44_ios_skeleton_future",
    } else True
    mutated = boundary.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        assert_mobile_api_boundary_read_only(mutated)


@pytest.mark.parametrize(
    ("field_name", "match"),
    [
        ("planned_route_ref", "route ref"),
        ("read_only", "read-only"),
        ("redacted_summary_only", "redacted summary"),
        ("raw_data_returned", "raw data"),
        ("raw_payload_returned", "raw payload"),
        ("raw_absolute_path_returned", "raw absolute path"),
        ("mutation_enabled", "mutation"),
        ("approval_capture_enabled", "approval capture"),
        ("approval_execution_enabled", "approval execution"),
        ("sensor_access_enabled", "sensor access"),
        ("context_injection_enabled", "context injection"),
        ("memory_write_enabled", "memory write"),
        ("export_enabled", "export"),
        ("execution_enabled", "execution"),
        ("credential_or_cookie_handling_enabled", "credential"),
        ("background_collection_enabled", "background collection"),
    ],
)
def test_m43_endpoint_rejects_raw_or_mutating_fields(
    field_name: str, match: str
) -> None:
    endpoint = MobileReadOnlyApiEndpointContract(
        endpoint_ref="mobile_api_endpoint:receipt-summary",
        kind=MobileApiEndpointKind.receipt_summary,
        planned_route_ref="mobile_api_route:receipts-summary",
        safe_summary="Receipt summary endpoint contract only.",
    )
    value = False if field_name in {"read_only", "redacted_summary_only"} else True
    if field_name == "planned_route_ref":
        value = "/Users/sambehdjou/private/raw-file.txt"
    mutated = endpoint.model_copy(update={field_name: value})

    with pytest.raises(ValueError, match=match):
        validate_mobile_api_endpoint_contract(mutated)


def test_m43_endpoint_rejects_non_get_methods() -> None:
    endpoint = MobileReadOnlyApiEndpointContract(
        endpoint_ref="mobile_api_endpoint:approval-status",
        kind=MobileApiEndpointKind.approval_status_summary,
        planned_route_ref="mobile_api_route:approval-status",
        safe_summary="Approval status endpoint contract only.",
        method=MobileApiHttpMethod.post,
    )

    with pytest.raises(ValueError, match="GET"):
        validate_mobile_api_endpoint_contract(endpoint)


def test_m43_endpoint_rejects_secret_like_safe_summary() -> None:
    endpoint = MobileReadOnlyApiEndpointContract(
        endpoint_ref="mobile_api_endpoint:manifest-summary",
        kind=MobileApiEndpointKind.manifest_summary,
        planned_route_ref="mobile_api_route:manifest-summary",
        safe_summary="token=abc123 should never appear",
    )

    with pytest.raises(ValueError, match="secret"):
        validate_mobile_api_endpoint_contract(endpoint)
