import re
from typing import Iterable

from ultimate_ai_agent.core.mobile_companion.contracts import (
    CccIosSkeletonManifest,
    CccIosSkeletonSurface,
    MobileApiBoundaryRefresh,
    MobileCapabilityPlan,
    MobileCaptureIntentPlan,
    MobileClientPlan,
    MobileCompanionManifest,
    MobileProductContractRefresh,
    MobileProductSurfaceContract,
    MobileReadOnlyApiBoundary,
    MobileReadOnlyApiEndpointContract,
)
from ultimate_ai_agent.core.mobile_companion.enums import (
    CccIosSkeletonSurfaceKind,
    MobileApiBoundaryStatus,
    MobileApiEndpointKind,
    MobileApiHttpMethod,
    MobileCapabilityKind,
    MobileCapabilityStatus,
    MobileClientPlatform,
    MobileCompanionSurface,
    MobileDataClassification,
    MobileProductRole,
)


SENSOR_CAPABILITIES = {
    MobileCapabilityKind.camera_planned,
    MobileCapabilityKind.microphone_planned,
    MobileCapabilityKind.location_planned,
    MobileCapabilityKind.photos_planned,
    MobileCapabilityKind.contacts_planned,
    MobileCapabilityKind.calendar_planned,
    MobileCapabilityKind.bluetooth_planned,
    MobileCapabilityKind.nfc_planned,
    MobileCapabilityKind.biometrics_planned,
}

SECRET_LIKE = re.compile(
    r"(?i)(api[_-]?key|auth[_-]?token|authorization|cookie|credential|password|secret|token)\s*[:=]"
)
RAW_CONTENT_KEYS = {
    "raw_location",
    "raw_camera",
    "raw_microphone",
    "raw_contact",
    "raw_calendar",
    "raw_photo",
    "raw_file",
    "raw_memory",
}
RAW_PATH_OR_ROUTE_REF = re.compile(
    r"(?i)(^/|[a-z]:\\|/users/|/home/|\.\.|raw[_ -]?(path|file|payload|content)|absolute[_ -]?path)"
)


def build_default_mobile_companion_manifest(
    version: str = "0.23.1",
) -> MobileCompanionManifest:
    clients = [
        MobileClientPlan(
            platform=MobileClientPlatform.ios_planned,
            surfaces=[
                MobileCompanionSurface.approval_status_planned,
                MobileCompanionSurface.receipt_view_planned,
                MobileCompanionSurface.capture_inbox_planned,
                MobileCompanionSurface.status_dashboard_planned,
            ],
            safe_summary="Future iOS control client planning only; no iOS app exists.",
        ),
        MobileClientPlan(
            platform=MobileClientPlatform.android_planned,
            surfaces=[
                MobileCompanionSurface.approval_status_planned,
                MobileCompanionSurface.receipt_view_planned,
                MobileCompanionSurface.capture_inbox_planned,
                MobileCompanionSurface.status_dashboard_planned,
            ],
            safe_summary="Future Android control client planning only; no Android app exists.",
        ),
        MobileClientPlan(
            platform=MobileClientPlatform.mobile_web_planned,
            surfaces=[MobileCompanionSurface.status_dashboard_planned],
            safe_summary="Future mobile web companion planning only.",
        ),
    ]
    capabilities = [
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.approvals_planned,
            status=MobileCapabilityStatus.contract_only,
            safe_summary="Approval status planning only; mobile cannot execute approvals.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.receipts_planned,
            status=MobileCapabilityStatus.contract_only,
            safe_summary="Receipt viewing planning only.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.status_planned,
            status=MobileCapabilityStatus.contract_only,
            safe_summary="Status dashboard planning only.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.camera_planned,
            status=MobileCapabilityStatus.future_requires_device_capability_broker,
            safe_summary="Camera planning only; no sensor access is enabled.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.microphone_planned,
            status=MobileCapabilityStatus.future_requires_device_capability_broker,
            safe_summary="microphone planning only; no sensor access is enabled.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.location_planned,
            status=MobileCapabilityStatus.future_requires_device_capability_broker,
            safe_summary="Location planning only; no sensor access is enabled.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.contacts_planned,
            status=MobileCapabilityStatus.future_requires_device_capability_broker,
            safe_summary="Contacts planning only; no contact access is enabled.",
        ),
        MobileCapabilityPlan(
            capability=MobileCapabilityKind.calendar_planned,
            status=MobileCapabilityStatus.future_requires_device_capability_broker,
            safe_summary="Calendar planning only; no calendar access is enabled.",
        ),
    ]
    manifest = MobileCompanionManifest(
        version=version,
        clients=clients,
        capabilities=capabilities,
        safe_summary=(
            "M19 mobile companion contract/API planning only; phone/mobile "
            "clients are control surfaces, not the agent brain."
        ),
    )
    assert_mobile_contract_only(manifest)
    for capability in manifest.capabilities:
        validate_mobile_capability_plan(capability)
    return manifest


def build_default_mobile_product_contract_refresh(
    version: str = "0.46.0",
) -> MobileProductContractRefresh:
    refresh = MobileProductContractRefresh(
        version=version,
        safe_summary=(
            "M42 mobile companion product contract refresh only; mobile remains "
            "governance/control, not the agent brain."
        ),
        product_roles=[
            MobileProductSurfaceContract(
                role=MobileProductRole.governance_surface,
                surfaces=[
                    MobileCompanionSurface.approval_status_planned,
                    MobileCompanionSurface.emergency_stop_planned,
                ],
                safe_summary="Governance status planning only; no approval execution.",
            ),
            MobileProductSurfaceContract(
                role=MobileProductRole.review_surface,
                surfaces=[MobileCompanionSurface.receipt_view_planned],
                safe_summary="Review and receipt display planning only.",
            ),
            MobileProductSurfaceContract(
                role=MobileProductRole.capture_inbox_surface,
                surfaces=[MobileCompanionSurface.capture_inbox_planned],
                safe_summary="Capture inbox product planning only; no sensor capture.",
            ),
            MobileProductSurfaceContract(
                role=MobileProductRole.status_surface,
                surfaces=[MobileCompanionSurface.status_dashboard_planned],
                safe_summary="Status dashboard planning only.",
            ),
        ],
        api_boundary=MobileApiBoundaryRefresh(
            status=MobileApiBoundaryStatus.blocked_until_m43,
            safe_summary="M43 may define a read-only mobile API boundary; M42 adds no route.",
        ),
    )
    assert_mobile_product_contract_refresh_only(refresh)
    return refresh


def build_default_mobile_read_only_api_boundary(
    version: str = "0.47.0",
) -> MobileReadOnlyApiBoundary:
    boundary = MobileReadOnlyApiBoundary(
        version=version,
        safe_summary=(
            "M43 mobile API boundary contract only; planned endpoints are "
            "read-only redacted summaries and add no backend routes."
        ),
        endpoints=[
            MobileReadOnlyApiEndpointContract(
                endpoint_ref="mobile_api_endpoint:manifest-summary",
                kind=MobileApiEndpointKind.manifest_summary,
                planned_route_ref="mobile_api_route:manifest-summary",
                safe_summary="Manifest summary endpoint contract only.",
            ),
            MobileReadOnlyApiEndpointContract(
                endpoint_ref="mobile_api_endpoint:approval-status-summary",
                kind=MobileApiEndpointKind.approval_status_summary,
                planned_route_ref="mobile_api_route:approval-status-summary",
                safe_summary="Approval status summary endpoint contract only.",
            ),
            MobileReadOnlyApiEndpointContract(
                endpoint_ref="mobile_api_endpoint:receipt-summary",
                kind=MobileApiEndpointKind.receipt_summary,
                planned_route_ref="mobile_api_route:receipt-summary",
                safe_summary="Receipt summary endpoint contract only.",
            ),
            MobileReadOnlyApiEndpointContract(
                endpoint_ref="mobile_api_endpoint:review-packet-summary",
                kind=MobileApiEndpointKind.review_packet_summary,
                planned_route_ref="mobile_api_route:review-packet-summary",
                safe_summary="Review packet summary endpoint contract only.",
            ),
            MobileReadOnlyApiEndpointContract(
                endpoint_ref="mobile_api_endpoint:device-status-summary",
                kind=MobileApiEndpointKind.device_status_summary,
                planned_route_ref="mobile_api_route:device-status-summary",
                safe_summary="Device status summary endpoint contract only; no sensors.",
            ),
        ],
    )
    assert_mobile_api_boundary_read_only(boundary)
    return boundary


def build_default_ccc_ios_skeleton_manifest(
    version: str = "0.48.0",
) -> CccIosSkeletonManifest:
    manifest = CccIosSkeletonManifest(
        version=version,
        safe_summary=(
            "M44 CCC iOS source-only skeleton; mock read-only views, no native "
            "authority, and no production workflow."
        ),
        surfaces=[
            CccIosSkeletonSurface(
                surface_ref="ccc_ios_surface:status-overview",
                kind=CccIosSkeletonSurfaceKind.status_overview,
                safe_summary="Mock status overview surface; read-only and non-authoritative.",
            ),
            CccIosSkeletonSurface(
                surface_ref="ccc_ios_surface:review-packet-preview",
                kind=CccIosSkeletonSurfaceKind.review_packet_preview,
                safe_summary="Mock review packet preview surface; no approval capture.",
            ),
            CccIosSkeletonSurface(
                surface_ref="ccc_ios_surface:receipt-preview",
                kind=CccIosSkeletonSurfaceKind.receipt_preview,
                safe_summary="Mock receipt preview surface; safe refs only.",
            ),
            CccIosSkeletonSurface(
                surface_ref="ccc_ios_surface:authority-boundary",
                kind=CccIosSkeletonSurfaceKind.authority_boundary,
                safe_summary="Authority boundary copy; iOS is not the agent brain.",
            ),
        ],
    )
    assert_ccc_ios_skeleton_no_authority(manifest)
    return manifest


def validate_mobile_capability_plan(plan: MobileCapabilityPlan) -> MobileCapabilityPlan:
    _assert_safe_text(plan.safe_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    if plan.allowed_now:
        raise ValueError("mobile capability allowed_now must remain false in M19")
    if plan.os_permission_integrated:
        raise ValueError("OS permission integration is not implemented in M19")
    if plan.background_service_enabled:
        raise ValueError("background service is not implemented in M19")
    if plan.capability in SENSOR_CAPABILITIES:
        allowed_statuses = {
            MobileCapabilityStatus.planned_disabled,
            MobileCapabilityStatus.future_requires_device_capability_broker,
        }
        if plan.status not in allowed_statuses:
            raise ValueError("sensor capabilities require a future Device Capability Broker")
        if not plan.requires_device_capability_broker:
            raise ValueError("sensor capabilities must require the Device Capability Broker")
    return plan


def validate_mobile_capture_intent_plan(
    plan: MobileCaptureIntentPlan,
) -> MobileCaptureIntentPlan:
    _assert_safe_text(plan.safe_summary)
    _assert_metadata_refs_only(plan.metadata_refs)
    if plan.silent_capture:
        raise ValueError("silent_capture is not allowed in M19")
    if plan.automatic_memory_write:
        raise ValueError("automatic_memory_write is not allowed in M19")
    if plan.external_send_allowed:
        raise ValueError("external_send_allowed is not allowed in M19")
    if plan.storage_allowed and plan.data_classification in {
        MobileDataClassification.sensitive,
        MobileDataClassification.forbidden,
    }:
        raise ValueError("storage_allowed is denied for sensitive or forbidden captures")
    return plan


def assert_mobile_contract_only(manifest: MobileCompanionManifest) -> MobileCompanionManifest:
    _assert_safe_text(manifest.safe_summary)
    if not manifest.contract_only:
        raise ValueError("mobile companion manifest must remain contract_only")
    if manifest.mobile_client_is_authority:
        raise ValueError("mobile client authority is not implemented")
    if manifest.mobile_approval_execution_implemented:
        raise ValueError("mobile approval execution is not implemented")
    if manifest.sensor_access_enabled:
        raise ValueError("mobile sensor access is not enabled")
    if manifest.os_permission_integration_implemented:
        raise ValueError("OS permission integration is not implemented")
    if manifest.background_service_implemented:
        raise ValueError("background service is not implemented")
    if manifest.arbitrary_strings_are_authority:
        raise ValueError("arbitrary strings are not authority")
    if manifest.secrets_allowed:
        raise ValueError("secrets are not allowed in mobile companion contracts")
    if not manifest.device_capability_broker_required:
        raise ValueError("Device Capability Broker is required before sensor access")
    for client in manifest.clients:
        _validate_client(client)
    for capability in manifest.capabilities:
        validate_mobile_capability_plan(capability)
    for capture in manifest.capture_intents:
        validate_mobile_capture_intent_plan(capture)
    for receipt in manifest.receipt_plans:
        _assert_safe_text(receipt.safe_summary)
        _assert_metadata_refs_only(receipt.metadata_refs)
        if receipt.raw_payload_stored or receipt.secret_storage_allowed:
            raise ValueError("mobile receipt plans cannot store raw payloads or secrets")
    return manifest


def assert_mobile_product_contract_refresh_only(
    refresh: MobileProductContractRefresh,
) -> MobileProductContractRefresh:
    _assert_safe_text(refresh.safe_summary)
    if refresh.milestone != "M42":
        raise ValueError("mobile product refresh must remain scoped to M42")
    if not refresh.contract_refresh_only:
        raise ValueError("M42 mobile product refresh must remain contract_refresh_only")
    if not refresh.m43_read_only_api_future:
        raise ValueError("M43 read-only API boundary must remain future")
    if not refresh.m44_ios_skeleton_future:
        raise ValueError("M44 iOS skeleton must remain future")
    forbidden_flags = {
        "native app": refresh.native_app_implemented,
        "mobile api": refresh.mobile_api_implemented,
        "mobile sensor access": refresh.mobile_sensor_access_enabled,
        "OS permission integration": refresh.os_permission_integration_enabled,
        "background service": refresh.background_service_enabled,
        "signing or store workflow": refresh.signing_or_store_workflow_enabled,
        "approval capture": refresh.approval_capture_enabled,
        "approval execution": refresh.approval_execution_enabled,
        "memory write": refresh.memory_write_enabled,
        "context injection": refresh.context_injection_enabled,
        "raw payload exposure": refresh.raw_payload_exposure_enabled,
        "production authority": refresh.production_authority_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M42 cannot enable {label}")
    validate_mobile_api_boundary_refresh(refresh.api_boundary)
    for role in refresh.product_roles:
        validate_mobile_product_surface_contract(role)
    return refresh


def validate_mobile_product_surface_contract(
    contract: MobileProductSurfaceContract,
) -> MobileProductSurfaceContract:
    _assert_safe_text(contract.safe_summary)
    if not contract.review_only:
        raise ValueError("M42 mobile product surfaces must remain review-only")
    if not contract.read_only:
        raise ValueError("M42 mobile product surfaces must remain read-only")
    forbidden_flags = {
        "authority": contract.authority_claimed,
        "approval execution": contract.approval_execution_enabled,
        "sensor access": contract.sensor_access_enabled,
        "background service": contract.background_service_enabled,
        "native implementation": contract.native_implementation_started,
        "raw payload display": contract.raw_payload_display_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M42 mobile product surface cannot enable {label}")
    return contract


def validate_mobile_api_boundary_refresh(
    boundary: MobileApiBoundaryRefresh,
) -> MobileApiBoundaryRefresh:
    _assert_safe_text(boundary.safe_summary)
    if boundary.status not in {
        MobileApiBoundaryStatus.future_read_only,
        MobileApiBoundaryStatus.blocked_until_m43,
    }:
        raise ValueError("M42 API boundary must remain future/read-only planning")
    if not boundary.m43_boundary_only:
        raise ValueError("M42 must keep the mobile API boundary reserved for M43")
    forbidden_flags = {
        "backend route": boundary.backend_route_added,
        "mutation": boundary.mutation_enabled,
        "raw data": boundary.raw_data_enabled,
        "sensor endpoint": boundary.sensor_endpoint_enabled,
        "approval execution": boundary.approval_execution_enabled,
        "credential handling": boundary.credential_handling_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M42 API boundary cannot enable {label}")
    return boundary


def assert_mobile_api_boundary_read_only(
    boundary: MobileReadOnlyApiBoundary,
) -> MobileReadOnlyApiBoundary:
    _assert_safe_text(boundary.safe_summary)
    if boundary.milestone != "M43":
        raise ValueError("mobile API boundary must remain scoped to M43")
    if not boundary.version.startswith("0.47."):
        raise ValueError("M43 mobile API boundary version must be 0.47.x")
    if not boundary.boundary_contract_only:
        raise ValueError("M43 mobile API boundary must remain contract-only")
    if not boundary.read_only_boundary:
        raise ValueError("M43 mobile API boundary must remain read-only")
    if not boundary.redacted_summary_only:
        raise ValueError("M43 mobile API boundary must remain redacted summary only")
    if not boundary.m44_ios_skeleton_future:
        raise ValueError("M44 iOS skeleton must remain future after M43")
    forbidden_flags = {
        "backend route": boundary.backend_routes_added,
        "mobile mutation": boundary.mobile_mutation_enabled,
        "mobile sensor access": boundary.mobile_sensor_access_enabled,
        "approval capture": boundary.approval_capture_enabled,
        "approval execution": boundary.approval_execution_enabled,
        "raw data": boundary.raw_data_enabled,
        "raw payload exposure": boundary.raw_payload_exposure_enabled,
        "raw absolute path exposure": boundary.raw_absolute_path_exposure_enabled,
        "context injection": boundary.context_injection_enabled,
        "memory write": boundary.memory_write_enabled,
        "export": boundary.export_enabled,
        "execution": boundary.execution_enabled,
        "credential or cookie handling": boundary.credential_or_cookie_handling_enabled,
        "background collection": boundary.background_collection_enabled,
        "production authority": boundary.production_authority_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M43 mobile API boundary cannot enable {label}")
    if not boundary.endpoints:
        raise ValueError("M43 mobile API boundary requires planned endpoint contracts")
    seen_refs: set[str] = set()
    for endpoint in boundary.endpoints:
        validate_mobile_api_endpoint_contract(endpoint)
        if endpoint.endpoint_ref in seen_refs:
            raise ValueError(f"duplicate M43 endpoint ref: {endpoint.endpoint_ref}")
        seen_refs.add(endpoint.endpoint_ref)
    return boundary


def validate_mobile_api_endpoint_contract(
    endpoint: MobileReadOnlyApiEndpointContract,
) -> MobileReadOnlyApiEndpointContract:
    _assert_safe_ref(endpoint.endpoint_ref, label="endpoint ref")
    _assert_safe_ref(endpoint.planned_route_ref, label="route ref")
    _assert_safe_text(endpoint.safe_summary)
    _assert_metadata_refs_only(endpoint.metadata_refs)
    if endpoint.method != MobileApiHttpMethod.get:
        raise ValueError("M43 mobile API endpoint contracts must use GET only")
    if not endpoint.read_only:
        raise ValueError("M43 mobile API endpoints must remain read-only")
    if not endpoint.redacted_summary_only:
        raise ValueError("M43 mobile API endpoints must remain redacted summary only")
    forbidden_flags = {
        "raw data": endpoint.raw_data_returned,
        "raw payload": endpoint.raw_payload_returned,
        "raw absolute path": endpoint.raw_absolute_path_returned,
        "mutation": endpoint.mutation_enabled,
        "approval capture": endpoint.approval_capture_enabled,
        "approval execution": endpoint.approval_execution_enabled,
        "sensor access": endpoint.sensor_access_enabled,
        "context injection": endpoint.context_injection_enabled,
        "memory write": endpoint.memory_write_enabled,
        "export": endpoint.export_enabled,
        "execution": endpoint.execution_enabled,
        "credential or cookie handling": endpoint.credential_or_cookie_handling_enabled,
        "background collection": endpoint.background_collection_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M43 mobile API endpoint cannot enable {label}")
    return endpoint


def assert_ccc_ios_skeleton_no_authority(
    manifest: CccIosSkeletonManifest,
) -> CccIosSkeletonManifest:
    _assert_safe_text(manifest.safe_summary)
    _assert_safe_ref(manifest.source_root_ref, label="source root ref")
    if manifest.milestone != "M44":
        raise ValueError("CCC iOS skeleton must remain scoped to M44")
    if not manifest.version.startswith("0.48."):
        raise ValueError("M44 CCC iOS skeleton version must be 0.48.x")
    if not manifest.source_only_skeleton:
        raise ValueError("M44 CCC iOS skeleton must remain source-only")
    if not manifest.no_authority:
        raise ValueError("M44 CCC iOS skeleton must remain no-authority")
    if not manifest.m45_local_read_only_connection_future:
        raise ValueError("M45 local read-only connection must remain future")
    forbidden_flags = {
        "production workflow": manifest.production_workflow_enabled,
        "signing or store workflow": manifest.signing_or_store_workflow_enabled,
        "native build workflow": manifest.native_build_workflow_enabled,
        "network access": manifest.network_access_enabled,
        "sensor access": manifest.sensor_access_enabled,
        "OS permission integration": manifest.os_permission_integration_enabled,
        "approval capture": manifest.approval_capture_enabled,
        "approval execution": manifest.approval_execution_enabled,
        "context injection": manifest.context_injection_enabled,
        "memory write": manifest.memory_write_enabled,
        "file mutation": manifest.file_mutation_enabled,
        "execution": manifest.execution_enabled,
        "credential storage": manifest.credential_storage_enabled,
        "background task": manifest.background_task_enabled,
        "production authority": manifest.production_authority_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M44 CCC iOS skeleton cannot enable {label}")
    if not manifest.surfaces:
        raise ValueError("M44 CCC iOS skeleton requires read-only surfaces")
    seen_refs: set[str] = set()
    for surface in manifest.surfaces:
        validate_ccc_ios_skeleton_surface(surface)
        if surface.surface_ref in seen_refs:
            raise ValueError(f"duplicate M44 iOS surface ref: {surface.surface_ref}")
        seen_refs.add(surface.surface_ref)
    return manifest


def validate_ccc_ios_skeleton_surface(
    surface: CccIosSkeletonSurface,
) -> CccIosSkeletonSurface:
    _assert_safe_ref(surface.surface_ref, label="surface ref")
    _assert_safe_text(surface.safe_summary)
    _assert_metadata_refs_only(surface.metadata_refs)
    if not surface.read_only:
        raise ValueError("M44 CCC iOS surfaces must remain read-only")
    if not surface.mock_only:
        raise ValueError("M44 CCC iOS surfaces must remain mock-only")
    if not surface.non_authoritative:
        raise ValueError("M44 CCC iOS surfaces must remain non-authoritative")
    forbidden_flags = {
        "mutation": surface.mutation_enabled,
        "approval capture": surface.approval_capture_enabled,
        "approval execution": surface.approval_execution_enabled,
        "sensor access": surface.sensor_access_enabled,
        "network access": surface.network_access_enabled,
        "context injection": surface.context_injection_enabled,
        "memory write": surface.memory_write_enabled,
        "file mutation": surface.file_mutation_enabled,
        "execution": surface.execution_enabled,
        "credential storage": surface.credential_storage_enabled,
    }
    for label, enabled in forbidden_flags.items():
        if enabled:
            raise ValueError(f"M44 CCC iOS surface cannot enable {label}")
    return surface


def assert_no_sensor_access_enabled(plan: MobileCapabilityPlan) -> MobileCapabilityPlan:
    return validate_mobile_capability_plan(plan)


def assert_no_silent_memory_write(plan: MobileCaptureIntentPlan) -> MobileCaptureIntentPlan:
    return validate_mobile_capture_intent_plan(plan)


def _validate_client(client: MobileClientPlan) -> None:
    _assert_safe_text(client.safe_summary)
    if client.implemented_now:
        raise ValueError("mobile client implementation is not part of M19")
    if client.authority_claimed:
        raise ValueError("mobile client authority is not implemented")
    if client.native_package_created:
        raise ValueError("native mobile package is not part of M19")
    if client.os_permission_integration_claimed:
        raise ValueError("OS permission integration is not implemented")
    if client.signing_or_store_workflow_claimed:
        raise ValueError("signing or store workflow is not part of M19")


def _assert_safe_text(text: str) -> None:
    if SECRET_LIKE.search(text):
        raise ValueError("secret-like text is not allowed in safe summaries")
    lowered = text.lower()
    for key in RAW_CONTENT_KEYS:
        if key.replace("_", " ") in lowered or key in lowered:
            raise ValueError("raw mobile content fields are not allowed")


def _assert_metadata_refs_only(refs: Iterable[str]) -> None:
    for ref in refs:
        _assert_safe_text(ref)
        _assert_safe_ref(ref, label="metadata ref")
        if "\n" in ref or len(ref) > 160:
            raise ValueError("metadata refs must be short string/ref-only values")


def _assert_safe_ref(ref: str, *, label: str) -> None:
    _assert_safe_text(ref)
    if "\n" in ref or len(ref) > 160:
        raise ValueError(f"{label} must be a short ref-only value")
    if RAW_PATH_OR_ROUTE_REF.search(ref):
        raise ValueError(f"{label} cannot contain raw paths, raw route paths, or raw data markers")
