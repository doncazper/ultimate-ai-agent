from __future__ import annotations

from ultimate_ai_agent.core.macos_setup_assistant.contracts import (
    MacOSSetupAssistantPlan,
    MacOSSetupBridgePreview,
    MacOSSetupHardwareProfile,
    MacOSSetupModelRecommendation,
    MacOSSetupStep,
    MacOSSetupStepKind,
    MacOSSetupStepStatus,
)


def recommend_local_model_options(
    hardware_profile: MacOSSetupHardwareProfile | None = None,
) -> list[MacOSSetupModelRecommendation]:
    profile = hardware_profile or MacOSSetupHardwareProfile()
    default_reason = (
        "MACOS_SETUP_DEFAULT_LOCAL_MODEL"
        if profile.memory_bucket == "ram:unknown"
        else "MACOS_SETUP_HARDWARE_BUCKET_MATCH"
    )
    return [
        MacOSSetupModelRecommendation(
            recommendation_ref="macos-setup-model-rec:fast-local",
            model_ref="local-model-option:small-chat-gguf",
            display_name="Fast local chat",
            fit_summary="Small local GGUF class for first-run readiness checks.",
            recommended_for="Fastest offline setup check and low-memory Macs.",
            memory_bucket="ram:low-to-medium",
            disk_bucket="disk:small",
            selected_by_default=True,
            reason_codes=[default_reason, "MACOS_SETUP_OFFLINE_FIRST"],
        ),
        MacOSSetupModelRecommendation(
            recommendation_ref="macos-setup-model-rec:balanced-local",
            model_ref="local-model-option:balanced-assistant-gguf",
            display_name="Balanced local assistant",
            fit_summary="Balanced local GGUF class for general chat and planning.",
            recommended_for="Day-to-day UAA local assistant use after readiness is proven.",
            memory_bucket="ram:medium",
            disk_bucket="disk:medium",
            reason_codes=["MACOS_SETUP_BALANCED_DEFAULT", "MACOS_SETUP_APPROVAL_BEFORE_DOWNLOAD"],
        ),
        MacOSSetupModelRecommendation(
            recommendation_ref="macos-setup-model-rec:coding-local",
            model_ref="local-model-option:coding-assistant-gguf",
            display_name="Coding local assistant",
            fit_summary="Coding-focused local GGUF class for developer workflows.",
            recommended_for="Code review, implementation planning, and local developer loops.",
            memory_bucket="ram:medium-to-high",
            disk_bucket="disk:medium",
            reason_codes=["MACOS_SETUP_CODING_WORKFLOW", "MACOS_SETUP_APPROVAL_BEFORE_DOWNLOAD"],
        ),
        MacOSSetupModelRecommendation(
            recommendation_ref="macos-setup-model-rec:bring-your-own",
            model_ref="local-model-option:bring-your-own-gguf",
            display_name="Bring your own GGUF",
            fit_summary="User-selected GGUF class with later safe-ref validation.",
            recommended_for="Users who already have a reviewed local model artifact.",
            memory_bucket="ram:user-reviewed",
            disk_bucket="disk:user-reviewed",
            reason_codes=["MACOS_SETUP_SAFE_REF_VALIDATION_REQUIRED"],
        ),
    ]


def build_default_macos_setup_assistant_plan(
    hardware_profile: MacOSSetupHardwareProfile | None = None,
) -> MacOSSetupAssistantPlan:
    return MacOSSetupAssistantPlan(
        steps=_default_steps(),
        model_recommendations=recommend_local_model_options(hardware_profile),
        bridge_previews=_bridge_previews(),
        blocked_capabilities=[
            "macos-setup-runtime-installation",
            "macos-setup-model-download",
            "macos-setup-launch-agent-change",
            "macos-setup-background-service-change",
            "macos-setup-provider-call",
            "macos-setup-credential-storage",
        ],
        next_steps=[
            "Review the Control Center setup preview against the first-launch flow.",
            "Choose whether the next slice should be native SwiftUI or a packaged web shell.",
            "Add a reviewed dry-run API route only after the contract shape settles.",
        ],
        morning_review_checklist=[
            "Verify the model choices are labels only and not live downloads.",
            "Confirm every approval-required step has receipt and rollback refs.",
            "Confirm terminal details are bounded previews and not raw logs.",
            "Decide the native macOS app scaffold location before adding signing work.",
        ],
        metadata={
            "dry_run_only": True,
            "side_effects_performed": False,
            "native_app_scaffolded": False,
        },
    )


def _default_steps() -> list[MacOSSetupStep]:
    return [
        _step(
            step_id="macos-setup-step:first-launch",
            kind=MacOSSetupStepKind.first_launch,
            label="First launch setup",
            status=MacOSSetupStepStatus.ready,
            safe_summary="Show the local-first setup timeline before any installer authority exists.",
            detail_preview=[
                "Welcome state explains local-only posture.",
                "Details pane shows bounded setup previews.",
            ],
            log_preview=["setup preview initialized; no command executed"],
            reason_codes=["MACOS_SETUP_VISUAL_PREVIEW_READY"],
        ),
        _step(
            step_id="macos-setup-step:runtime-health",
            kind=MacOSSetupStepKind.runtime_health,
            label="Runtime health",
            status=MacOSSetupStepStatus.ready,
            safe_summary="Use existing health and readiness refs as inspectable setup inputs.",
            route_refs=["/health", "/version", "/runtime/readiness", "/runtime/capability-matrix"],
            detail_preview=["Runtime status is read-only.", "No lifecycle action is exposed."],
            log_preview=["health route planned for read-only inspection"],
            reason_codes=["MACOS_SETUP_RUNTIME_READINESS_REF"],
        ),
        _step(
            step_id="macos-setup-step:local-model-readiness",
            kind=MacOSSetupStepKind.local_model_readiness,
            label="Local model readiness",
            status=MacOSSetupStepStatus.blocked,
            safe_summary="Model readiness remains gated by reviewed local gateway configuration.",
            route_refs=["/v1/models", "/v1/chat/completions"],
            detail_preview=[
                "Model list inspection is allowed only through configured local UAA routes.",
                "Chat probes remain redacted and disabled by default.",
            ],
            log_preview=["local model route preview is gated; no prompt sent"],
            reason_codes=["MACOS_SETUP_LOCAL_GATEWAY_DISABLED_BY_DEFAULT"],
            next_safe_action="enable-reviewed-local-gateway",
        ),
        _step(
            step_id="macos-setup-step:model-selection",
            kind=MacOSSetupStepKind.model_selection,
            label="Model selection",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Model choices are recommendation records only until the user approves a download or safe-ref import.",
            detail_preview=[
                "Choices show size and fit buckets.",
                "No model file is read or downloaded by this slice.",
            ],
            log_preview=["model recommendation list built from safe labels"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-model-selection",
            reason_codes=["MACOS_SETUP_MODEL_APPROVAL_REQUIRED"],
            next_safe_action="review-model-choice",
        ),
        _step(
            step_id="macos-setup-step:ask-setup-question",
            kind=MacOSSetupStepKind.setup_question,
            label="Setup questions",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="The future setup assistant may answer questions from setup state, but model output is never authority.",
            detail_preview=[
                "Question answering remains a planned local assistant surface.",
                "Advice cannot approve downloads, services, or bridge enablement.",
            ],
            log_preview=["question assistant placeholder; no model called"],
            reason_codes=["MACOS_SETUP_QUERY_ASSISTANT_DRY_RUN_ONLY"],
        ),
        _step(
            step_id="macos-setup-step:openwebui-bridge",
            kind=MacOSSetupStepKind.openwebui_bridge,
            label="Optional OpenWebUI bridge",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="OpenWebUI bridge setup is optional and remains explicit local approval work.",
            route_refs=["/v1/models", "/v1/chat/completions"],
            detail_preview=["Bridge enablement is disabled by default.", "No OpenWebUI runtime handoff is performed."],
            log_preview=["openwebui bridge preview only; no external runtime contacted"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-openwebui-bridge",
            reason_codes=["MACOS_SETUP_OPENWEBUI_APPROVAL_REQUIRED"],
            next_safe_action="review-openwebui-bridge",
        ),
        _step(
            step_id="macos-setup-step:mattermost-bridge",
            kind=MacOSSetupStepKind.mattermost_bridge,
            label="Optional Mattermost Agent Rooms",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Mattermost Agent Rooms remain a local, disabled-by-default bridge with explicit room approval.",
            route_refs=["/integrations/mattermost/status", "/integrations/mattermost/roles/catalog"],
            detail_preview=["Room participation is speak-only by default.", "No raw transcript is persisted."],
            log_preview=["mattermost bridge preview only; no post observed"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-mattermost-bridge",
            reason_codes=["MACOS_SETUP_MATTERMOST_APPROVAL_REQUIRED"],
            next_safe_action="review-mattermost-bridge",
        ),
        _step(
            step_id="macos-setup-step:approvals",
            kind=MacOSSetupStepKind.approval,
            label="Approvals",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="Every future setup mutation needs exact local approval before execution.",
            route_refs=["/approvals/validate", "/control-center/actions/preview"],
            detail_preview=["Approval refs are identifiers only.", "The visual shell cannot grant authority."],
            log_preview=["approval boundary preview ready"],
            reason_codes=["MACOS_SETUP_APPROVAL_BOUNDARY_VISIBLE"],
        ),
        _step(
            step_id="macos-setup-step:receipts-audit-latency",
            kind=MacOSSetupStepKind.receipt_audit_latency,
            label="Receipts, audit, and latency",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="Receipt, audit, and latency refs are planned before any setup action is allowed.",
            route_refs=["/receipts", "/events"],
            detail_preview=["Raw terminal logs are not persisted.", "Latency is tracked as safe summary metadata."],
            log_preview=["receipt plan created as preview metadata"],
            reason_codes=["MACOS_SETUP_RECEIPT_PLAN_VISIBLE"],
        ),
        _step(
            step_id="macos-setup-step:rollback-uninstall",
            kind=MacOSSetupStepKind.rollback_uninstall,
            label="Rollback and uninstall",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="Rollback and uninstall refs are visible before any reviewed setup mutation exists.",
            detail_preview=[
                "Future model files, LaunchAgents, and local config need explicit rollback refs.",
                "No rollback action is executed by this slice.",
            ],
            log_preview=["rollback plan preview ready; no files changed"],
            reason_codes=["MACOS_SETUP_ROLLBACK_PLAN_VISIBLE"],
        ),
    ]


def _bridge_previews() -> list[MacOSSetupBridgePreview]:
    return [
        MacOSSetupBridgePreview(
            bridge_ref="macos-setup-bridge:openwebui",
            label="OpenWebUI bridge",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Optional local OpenWebUI bridge remains disabled until explicit setup approval.",
            reason_codes=["MACOS_SETUP_BRIDGE_DISABLED_BY_DEFAULT"],
        ),
        MacOSSetupBridgePreview(
            bridge_ref="macos-setup-bridge:mattermost",
            label="Mattermost Agent Rooms",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Optional Mattermost room bridge remains disabled until explicit setup approval.",
            reason_codes=["MACOS_SETUP_BRIDGE_DISABLED_BY_DEFAULT"],
        ),
    ]


def _step(
    *,
    step_id: str,
    kind: MacOSSetupStepKind,
    label: str,
    status: MacOSSetupStepStatus,
    safe_summary: str,
    receipt_ref: str | None = None,
    rollback_ref: str | None = None,
    latency_ref: str | None = None,
    **kwargs,
) -> MacOSSetupStep:
    suffix = step_id.split(":")[-1]
    return MacOSSetupStep(
        step_id=step_id,
        kind=kind,
        label=label,
        status=status,
        safe_summary=safe_summary,
        receipt_ref=receipt_ref or f"receipt-plan:macos-setup-{suffix}",
        rollback_ref=rollback_ref or f"rollback-plan:macos-setup-{suffix}",
        latency_ref=latency_ref or f"latency-ref:macos-setup-{suffix}",
        **kwargs,
    )
