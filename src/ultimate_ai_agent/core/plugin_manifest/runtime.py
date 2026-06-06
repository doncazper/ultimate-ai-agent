from ultimate_ai_agent.core.plugin_manifest.contracts import (
    PluginManifestReceiptPlan,
    PluginManifestSecurityDecision,
    PluginManifestSecurityPolicy,
    PluginManifestSecurityReviewRequest,
)
from ultimate_ai_agent.core.plugin_manifest.enums import PluginManifestSecurityDecisionStatus
from ultimate_ai_agent.core.plugin_manifest.validation import (
    validate_plugin_manifest_security_decision,
    validate_plugin_manifest_security_policy,
    validate_plugin_manifest_security_request,
)


M78_PLUGIN_MANIFEST_DOCS = [
    "docs/tooling/PLUGIN_MANIFEST_SECURITY_MODEL.md",
    "docs/tooling/PLUGIN_MANIFEST_POLICY.md",
    "docs/tooling/PLUGIN_PERMISSION_MODEL.md",
    "docs/tooling/PLUGIN_PROVENANCE_REVIEW.md",
    "docs/tooling/PLUGIN_SANDBOX_TEST_PLAN.md",
    "docs/tooling/PLUGIN_MANIFEST_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_MANIFEST_RECEIPT_PLAN.md",
    "docs/tooling/M78_TO_M79_BOUNDARY.md",
]


def build_default_plugin_manifest_security_policy() -> PluginManifestSecurityPolicy:
    policy = PluginManifestSecurityPolicy(
        docs_refs=M78_PLUGIN_MANIFEST_DOCS,
        metadata_refs=["milestone:M78", "version:v0.82.0"],
        metadata={
            "scope": "plugin_manifest_security_model_only",
            "next_milestone": "M79 remains future",
        },
    )
    return validate_plugin_manifest_security_policy(policy)


def build_plugin_manifest_security_decision(
    request: PluginManifestSecurityReviewRequest,
    policy: PluginManifestSecurityPolicy | None = None,
) -> PluginManifestSecurityDecision:
    active_policy = policy or build_default_plugin_manifest_security_policy()
    validate_plugin_manifest_security_policy(active_policy)
    validate_plugin_manifest_security_request(request, active_policy)
    safe_suffix = request.review_request_ref.rsplit(":", 1)[-1].replace("/", "_")
    receipt_plan = PluginManifestReceiptPlan(
        receipt_plan_ref=f"plugin-manifest-receipt-plan:{safe_suffix}",
        review_request_ref=request.review_request_ref,
        manifest_ref=request.manifest_ref,
        plugin_ref=request.plugin_ref,
        plugin_version=request.plugin_version,
        safe_summary="M78 plugin manifest receipt stores only reviewed safe refs.",
        static_review_ref=request.static_review_ref or "plugin-static-review:missing",
        sandbox_test_plan_ref=request.sandbox_test_plan_ref or "plugin-sandbox-test-plan:missing",
        tool_broker_mapping_ref=request.tool_broker_mapping_ref or "tool-broker-map:missing",
        event_ledger_plan_ref=request.event_ledger_plan_ref or "event-ledger-plan:missing",
        version_pin_ref=request.version_pin_ref or "plugin-version-pin:missing",
        revocation_plan_ref=request.revocation_plan_ref or "plugin-revocation-plan:missing",
        metadata_refs=["milestone:M78", "version:v0.82.0"],
    )
    decision = PluginManifestSecurityDecision(
        decision_ref=f"plugin-manifest-security-decision:{safe_suffix}",
        review_request_ref=request.review_request_ref,
        manifest_ref=request.manifest_ref,
        plugin_ref=request.plugin_ref,
        plugin_version=request.plugin_version,
        actor_ref=request.actor_ref,
        status=PluginManifestSecurityDecisionStatus.review_ready_disabled,
        safe_message="Plugin manifest is review-ready and remains disabled.",
        reason_codes=[
            "M78_PLUGIN_MANIFEST_SECURITY_MODEL",
            "PLUGIN_REVIEW_READY_DISABLED",
            "M79_REMAINS_FUTURE",
        ],
        receipt_plan=receipt_plan,
        docs_refs=M78_PLUGIN_MANIFEST_DOCS,
        metadata_refs=["milestone:M78", "version:v0.82.0"],
    )
    return validate_plugin_manifest_security_decision(decision)
