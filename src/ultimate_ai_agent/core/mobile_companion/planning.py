import re
from typing import Iterable

from ultimate_ai_agent.core.mobile_companion.contracts import (
    MobileApiBoundaryRefresh,
    MobileCapabilityPlan,
    MobileCaptureIntentPlan,
    MobileClientPlan,
    MobileCompanionManifest,
    MobileProductContractRefresh,
    MobileProductSurfaceContract,
)
from ultimate_ai_agent.core.mobile_companion.enums import (
    MobileApiBoundaryStatus,
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
        if "\n" in ref or len(ref) > 160:
            raise ValueError("metadata refs must be short string/ref-only values")
