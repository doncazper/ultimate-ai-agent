from enum import Enum


class MobileClientPlatform(str, Enum):
    ios_planned = "ios_planned"
    android_planned = "android_planned"
    mobile_web_planned = "mobile_web_planned"
    unknown_planned = "unknown_planned"


class MobileCompanionSurface(str, Enum):
    approval_status_planned = "approval_status_planned"
    receipt_view_planned = "receipt_view_planned"
    capture_inbox_planned = "capture_inbox_planned"
    emergency_stop_planned = "emergency_stop_planned"
    status_dashboard_planned = "status_dashboard_planned"
    notification_planned = "notification_planned"
    sensor_capture_planned = "sensor_capture_planned"


class MobileCapabilityKind(str, Enum):
    approvals_planned = "approvals_planned"
    receipts_planned = "receipts_planned"
    status_planned = "status_planned"
    capture_inbox_planned = "capture_inbox_planned"
    camera_planned = "camera_planned"
    microphone_planned = "microphone_planned"
    location_planned = "location_planned"
    notifications_planned = "notifications_planned"
    files_planned = "files_planned"
    photos_planned = "photos_planned"
    contacts_planned = "contacts_planned"
    calendar_planned = "calendar_planned"
    bluetooth_planned = "bluetooth_planned"
    nfc_planned = "nfc_planned"
    biometrics_planned = "biometrics_planned"


class MobileCapabilityStatus(str, Enum):
    planned_disabled = "planned_disabled"
    contract_only = "contract_only"
    blocked = "blocked"
    future_requires_device_capability_broker = "future_requires_device_capability_broker"


class MobileDataClassification(str, Enum):
    public = "public"
    internal = "internal"
    personal = "personal"
    sensitive = "sensitive"
    regulated = "regulated"
    forbidden = "forbidden"


class MobilePermissionDecision(str, Enum):
    allowed_contract_only = "allowed_contract_only"
    denied = "denied"
    blocked = "blocked"
    requires_future_broker = "requires_future_broker"
    requires_user_approval = "requires_user_approval"
    not_implemented = "not_implemented"


class MobileReceiptRequirement(str, Enum):
    receipt_required = "receipt_required"
    redacted_receipt_required = "redacted_receipt_required"
    no_storage_allowed = "no_storage_allowed"
    not_applicable = "not_applicable"


class MobileProductRole(str, Enum):
    governance_surface = "governance_surface"
    review_surface = "review_surface"
    status_surface = "status_surface"
    capture_inbox_surface = "capture_inbox_surface"
    notification_surface = "notification_surface"


class MobileApiBoundaryStatus(str, Enum):
    future_read_only = "future_read_only"
    not_implemented = "not_implemented"
    blocked_until_m43 = "blocked_until_m43"
    read_only_contract = "read_only_contract"


class MobileApiEndpointKind(str, Enum):
    manifest_summary = "manifest_summary"
    approval_status_summary = "approval_status_summary"
    receipt_summary = "receipt_summary"
    review_packet_summary = "review_packet_summary"
    context_proposal_summary = "context_proposal_summary"
    device_status_summary = "device_status_summary"


class MobileApiHttpMethod(str, Enum):
    get = "GET"
    post = "POST"
    put = "PUT"
    patch = "PATCH"
    delete = "DELETE"


class CccIosSkeletonSurfaceKind(str, Enum):
    status_overview = "status_overview"
    review_packet_preview = "review_packet_preview"
    receipt_preview = "receipt_preview"
    authority_boundary = "authority_boundary"


class CccIosLocalConnectionEndpointKind(str, Enum):
    manifest_summary = "manifest_summary"
    review_packet_summary = "review_packet_summary"
    receipt_summary = "receipt_summary"
    authority_boundary = "authority_boundary"


class CccIosReviewReceiptSurfaceKind(str, Enum):
    review_packet_summary = "review_packet_summary"
    review_packet_detail = "review_packet_detail"
    receipt_summary = "receipt_summary"
    receipt_detail = "receipt_detail"
    authority_boundary = "authority_boundary"


class InternalTestFlightPipelineStageKind(str, Enum):
    source_snapshot = "source_snapshot"
    build_archive_plan = "build_archive_plan"
    signing_asset_presence_check = "signing_asset_presence_check"
    internal_distribution_review = "internal_distribution_review"
    rollback_plan = "rollback_plan"
    audit_receipt_plan = "audit_receipt_plan"


class FirstInternalTestFlightBuildStatus(str, Enum):
    reviewed_candidate = "reviewed_candidate"
    blocked_pending_external_signing = "blocked_pending_external_signing"


class MobileReviewApprovalDecisionKind(str, Enum):
    approve_review_only = "approve_review_only"
    deny_review_only = "deny_review_only"


class MobileReviewApprovalCaptureDecisionStatus(str, Enum):
    approved_for_mobile_review_only = "approved_for_mobile_review_only"
    denied_for_mobile_review = "denied_for_mobile_review"
    rejected = "rejected"


class MobileApprovalAuditStatus(str, Enum):
    passed = "passed"
    failed = "failed"
