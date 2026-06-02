from enum import Enum


class DevicePlatform(str, Enum):
    ios_planned = "ios_planned"
    android_planned = "android_planned"
    mobile_web_planned = "mobile_web_planned"
    macos_planned = "macos_planned"
    unknown_planned = "unknown_planned"


class DeviceCapabilityKind(str, Enum):
    camera = "camera"
    microphone = "microphone"
    location = "location"
    notifications = "notifications"
    contacts = "contacts"
    calendar = "calendar"
    photos = "photos"
    files = "files"
    clipboard = "clipboard"
    bluetooth = "bluetooth"
    nfc = "nfc"
    biometrics = "biometrics"
    background_service = "background_service"
    device_identity = "device_identity"
    device_pairing = "device_pairing"
    local_network = "local_network"
    motion = "motion"
    health = "health"
    screen_capture = "screen_capture"
    unknown = "unknown"


class DeviceCapabilityStatus(str, Enum):
    contract_only = "contract_only"
    planned_disabled = "planned_disabled"
    blocked = "blocked"
    future_requires_broker = "future_requires_broker"
    future_requires_pairing = "future_requires_pairing"
    future_requires_user_approval = "future_requires_user_approval"
    not_implemented = "not_implemented"


class DevicePermissionScope(str, Enum):
    none = "none"
    one_time_planned = "one_time_planned"
    session_planned = "session_planned"
    foreground_planned = "foreground_planned"
    background_blocked = "background_blocked"
    standing_blocked = "standing_blocked"


class DeviceCaptureMode(str, Enum):
    manual_selected_planned = "manual_selected_planned"
    passive_blocked = "passive_blocked"
    background_blocked = "background_blocked"
    continuous_blocked = "continuous_blocked"


class DeviceTrustState(str, Enum):
    unpaired_planned = "unpaired_planned"
    paired_planned = "paired_planned"
    revoked = "revoked"
    blocked = "blocked"
    unknown = "unknown"


class DeviceCapabilityDecisionStatus(str, Enum):
    denied = "denied"
    blocked = "blocked"
    contract_valid = "contract_valid"
    requires_future_broker = "requires_future_broker"
    requires_future_pairing = "requires_future_pairing"
    requires_user_approval = "requires_user_approval"
    not_implemented = "not_implemented"


class DeviceReceiptRequirement(str, Enum):
    receipt_required = "receipt_required"
    redacted_receipt_required = "redacted_receipt_required"
    no_storage_allowed = "no_storage_allowed"
    not_applicable = "not_applicable"


class DeviceDataClassification(str, Enum):
    public = "public"
    internal = "internal"
    personal = "personal"
    sensitive = "sensitive"
    regulated = "regulated"
    forbidden = "forbidden"


class DeviceRiskLevel(str, Enum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"
