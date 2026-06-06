from enum import Enum


class PluginManifestPermissionKind(str, Enum):
    read_only_local_docs = "read_only_local_docs"
    artifact_generation = "artifact_generation"
    local_web_ui_review = "local_web_ui_review"
    external_code_review = "external_code_review"
    cloud_compute = "cloud_compute"
    native_build_tooling = "native_build_tooling"
    browser_profile_control = "browser_profile_control"
    plugin_installation = "plugin_installation"
    runtime_execution = "runtime_execution"


class PluginManifestRiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class PluginManifestSecurityDecisionStatus(str, Enum):
    review_ready_disabled = "review_ready_disabled"
    denied = "denied"
    blocked = "blocked"


class PluginManifestReviewStage(str, Enum):
    security_model_only = "security_model_only"
    static_review_required = "static_review_required"
    sandbox_test_plan_required = "sandbox_test_plan_required"
    future_install_review_required = "future_install_review_required"
