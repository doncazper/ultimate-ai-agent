from ultimate_ai_agent.core.plugin_install_review.contracts import (
    PluginInstallReviewDecision,
    PluginInstallReviewPolicy,
    PluginInstallReviewReceiptPlan,
    PluginInstallReviewRequest,
)
from ultimate_ai_agent.core.plugin_install_review.enums import PluginInstallReviewDecisionStatus
from ultimate_ai_agent.core.plugin_install_review.validation import (
    validate_plugin_install_review_decision,
    validate_plugin_install_review_policy,
    validate_plugin_install_review_request,
)


M79_PLUGIN_INSTALL_REVIEW_DOCS = [
    "docs/tooling/PLUGIN_INSTALL_REVIEW.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_POLICY.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/tooling/PLUGIN_INSTALL_REVIEW_RECEIPT_PLAN.md",
    "docs/tooling/M79_TO_M80_BOUNDARY.md",
]


def build_default_plugin_install_review_policy() -> PluginInstallReviewPolicy:
    policy = PluginInstallReviewPolicy(
        docs_refs=M79_PLUGIN_INSTALL_REVIEW_DOCS,
        metadata_refs=["milestone:M79", "version:v0.83.0"],
        metadata={
            "scope": "plugin_install_review_disabled_by_default",
            "next_milestone": "M80 remains future",
        },
    )
    return validate_plugin_install_review_policy(policy)


def build_plugin_install_review_decision(
    request: PluginInstallReviewRequest,
    policy: PluginInstallReviewPolicy | None = None,
) -> PluginInstallReviewDecision:
    active_policy = policy or build_default_plugin_install_review_policy()
    validate_plugin_install_review_policy(active_policy)
    validate_plugin_install_review_request(request, active_policy)
    safe_suffix = request.install_review_request_ref.rsplit(":", 1)[-1].replace("/", "_")
    receipt_plan = PluginInstallReviewReceiptPlan(
        receipt_plan_ref=f"plugin-install-review-receipt-plan:{safe_suffix}",
        install_review_request_ref=request.install_review_request_ref,
        manifest_security_decision_ref=request.manifest_security_decision.decision_ref,
        manifest_ref=request.manifest_ref,
        plugin_ref=request.plugin_ref,
        plugin_version=request.plugin_version,
        source_package_ref=request.source_package_ref or "plugin-package:missing",
        static_review_ref=request.static_review_ref or "plugin-static-review:missing",
        sandbox_test_plan_ref=request.sandbox_test_plan_ref
        or "plugin-sandbox-test-plan:missing",
        tool_broker_mapping_ref=request.tool_broker_mapping_ref or "tool-broker-map:missing",
        event_ledger_plan_ref=request.event_ledger_plan_ref or "event-ledger-plan:missing",
        version_pin_ref=request.version_pin_ref or "plugin-version-pin:missing",
        revocation_plan_ref=request.revocation_plan_ref or "plugin-revocation-plan:missing",
        safe_summary="M79 plugin install review receipt stores only reviewed safe refs.",
        metadata_refs=["milestone:M79", "version:v0.83.0"],
    )
    decision = PluginInstallReviewDecision(
        decision_ref=f"plugin-install-review-decision:{safe_suffix}",
        install_review_request_ref=request.install_review_request_ref,
        manifest_security_decision_ref=request.manifest_security_decision.decision_ref,
        manifest_ref=request.manifest_ref,
        plugin_ref=request.plugin_ref,
        plugin_version=request.plugin_version,
        actor_ref=request.actor_ref,
        status=PluginInstallReviewDecisionStatus.install_review_ready_disabled,
        safe_message="Plugin install review is ready; plugin remains disabled by default.",
        reason_codes=[
            "M79_PLUGIN_INSTALL_REVIEW_DISABLED_BY_DEFAULT",
            "PLUGIN_INSTALL_REVIEW_READY_DISABLED",
            "M80_REMAINS_FUTURE",
        ],
        receipt_plan=receipt_plan,
        docs_refs=M79_PLUGIN_INSTALL_REVIEW_DOCS,
        metadata_refs=["milestone:M79", "version:v0.83.0"],
    )
    return validate_plugin_install_review_decision(decision)
