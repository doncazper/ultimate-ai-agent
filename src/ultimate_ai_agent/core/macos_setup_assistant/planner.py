from __future__ import annotations
from typing import Any

from ultimate_ai_agent.core.macos_setup_assistant.contracts import (
    MacOSSetupApprovalEnvelope,
    MacOSSetupApprovalEnvelopeStatus,
    MacOSSetupAssistantPlan,
    MacOSSetupBridgePreview,
    MacOSSetupHardwareProfile,
    MacOSSetupModelRecommendation,
    MacOSSetupStep,
    MacOSSetupStepKind,
    MacOSSetupStepStatus,
)
from ultimate_ai_agent.core.macos_setup_assistant.lifecycle import (
    build_macos_setup_lifecycle_contract,
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
    steps = _default_steps()
    return MacOSSetupAssistantPlan(
        lifecycle=build_macos_setup_lifecycle_contract(),
        steps=steps,
        model_recommendations=recommend_local_model_options(hardware_profile),
        bridge_previews=_bridge_previews(),
        approval_envelopes=_approval_envelopes(steps),
        blocked_capabilities=[
            "macos-setup-runtime-installation",
            "macos-setup-model-download",
            "macos-setup-launch-agent-change",
            "macos-setup-background-service-change",
            "macos-setup-bridge-enablement",
            "macos-setup-provider-call",
            "macos-setup-credential-storage",
            "macos-setup-rollback-execution",
            "macos-setup-signed-distribution",
            "macos-setup-production-authority",
        ],
        next_steps=[
            "Review the setup-to-daily-loop proof refs before calling setup complete.",
            "Inspect local unsigned package proof refs without launching the app bundle.",
            "Review the Control Center setup preview against the first-launch flow.",
            "Choose whether the next slice should be native SwiftUI or a packaged web shell.",
            "Review dry-run approval envelopes before any setup mutation route is scoped.",
        ],
        morning_review_checklist=[
            "Verify the model choices are labels only and not live downloads.",
            "Confirm every approval-required step has receipt and rollback refs.",
            "Confirm local package proofs remain unsigned, local-only, and non-distribution.",
            "Confirm terminal details are bounded previews and not raw logs.",
            "Decide the native macOS app scaffold location before adding signing work.",
        ],
        metadata={
            "dry_run_only": True,
            "side_effects_performed": False,
            "native_app_scaffolded": False,
            "first_run_loop_refs_bound": True,
            "local_package_proof_refs_bound": True,
        },
    )


def _default_steps() -> list[MacOSSetupStep]:
    return [
        _step(
            step_id="macos-setup-step:first-launch",
            kind=MacOSSetupStepKind.first_launch,
            label="First launch setup",
            status=MacOSSetupStepStatus.ready,
            safe_summary="Show the local-first setup timeline and next daily-loop proof refs before any installer authority exists.",
            detail_preview=[
                "Welcome state explains local-only posture.",
                "Details pane shows bounded setup previews.",
                "Next step points to Start Here, Today, Action Inbox, Proof, Memory, and Trust refs.",
            ],
            log_preview=["setup preview initialized; no command executed"],
            reason_codes=[
                "MACOS_SETUP_VISUAL_PREVIEW_READY",
                "MACOS_SETUP_FIRST_RUN_LOOP_REFS_VISIBLE",
            ],
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
            step_id="macos-setup-step:model-download-planning",
            kind=MacOSSetupStepKind.model_download_planning,
            label="Model download planning",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Model download approval is represented as dry-run scope metadata only.",
            detail_preview=[
                "Future downloads require exact model refs and operator approval.",
                "No model URL is fetched and no model file is written.",
            ],
            log_preview=["model download envelope created; no download attempted"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-model-download-planning",
            reason_codes=["MACOS_SETUP_MODEL_DOWNLOAD_ENVELOPE_READY"],
            next_safe_action="review-model-download-envelope",
        ),
        _step(
            step_id="macos-setup-step:launch-agent-setup-planning",
            kind=MacOSSetupStepKind.launch_agent_setup_planning,
            label="LaunchAgent setup planning",
            status=MacOSSetupStepStatus.blocked,
            safe_summary="LaunchAgent setup remains blocked until a reviewed native packaging milestone.",
            detail_preview=[
                "The dry-run envelope names future approval scope refs only.",
                "No launch agent file, load action, or start action is available.",
            ],
            log_preview=["launch agent envelope created; no launch action attempted"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-launch-agent-setup-planning",
            reason_codes=["MACOS_SETUP_LAUNCH_AGENT_ENVELOPE_BLOCKED"],
            next_safe_action="wait-for-native-packaging-milestone",
        ),
        _step(
            step_id="macos-setup-step:local-bridge-setup-planning",
            kind=MacOSSetupStepKind.local_bridge_setup_planning,
            label="Local bridge setup planning",
            status=MacOSSetupStepStatus.approval_required,
            safe_summary="Local bridge enablement is represented as disabled-by-default dry-run scope metadata.",
            route_refs=["/v1/models", "/v1/chat/completions"],
            detail_preview=[
                "Bridge setup requires exact local scope and credential-safe handling.",
                "No bridge is enabled and no connector write occurs.",
            ],
            log_preview=["local bridge envelope created; no bridge contacted"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-local-bridge-setup-planning",
            reason_codes=["MACOS_SETUP_LOCAL_BRIDGE_ENVELOPE_READY"],
            next_safe_action="review-local-bridge-envelope",
        ),
        _step(
            step_id="macos-setup-step:background-service-setup-planning",
            kind=MacOSSetupStepKind.background_service_setup_planning,
            label="Background-service setup planning",
            status=MacOSSetupStepStatus.blocked,
            safe_summary="Background-service setup remains not scoped and cannot start a daemon, scheduler, or worker.",
            detail_preview=[
                "The envelope documents denied authority for future review.",
                "No background service, daemon, scheduler, worker, or auto-start mechanism is created.",
            ],
            log_preview=["background service envelope created; no service action attempted"],
            approval_required=True,
            approval_ref="approval-ref:macos-setup-background-service-setup-planning",
            reason_codes=["MACOS_SETUP_BACKGROUND_SERVICE_NOT_SCOPED"],
            next_safe_action="keep-background-service-not-scoped",
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


def _approval_envelopes(steps: list[MacOSSetupStep]) -> list[MacOSSetupApprovalEnvelope]:
    steps_by_kind = {step.kind: step for step in steps}
    return [
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.model_selection],
            status=MacOSSetupApprovalEnvelopeStatus.approval_required,
            safe_summary="Dry-run envelope for future model choice review; no model is selected, read, downloaded, or called.",
            requested_scope_refs=["scope-ref:macos-setup-model-selection"],
            risk_class="medium",
            not_scoped_actions=[
                "model-selection-persistence",
                "model-file-read",
                "model-download-execution",
                "model-call",
            ],
            blocked_runtime_authority=[
                "control-center-setup-model-selection-write",
                "runtime-model-calls",
                "provider-api-calls",
            ],
            evidence_refs=[
                "docs-ref:uaa-setup-assistant-plan",
                "docs-ref:local-model-operational-runbook",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-api-routes",
                "verifier:control-center-frontend",
            ],
            stale_state_handling=(
                "Stale if local model readiness refs, hardware buckets, or model "
                "recommendation classes change before review."
            ),
            redaction_summary=(
                "Safe recommendation refs only; raw model URLs, local file paths, "
                "prompts, logs, and provider payloads are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.model_download_planning],
            status=MacOSSetupApprovalEnvelopeStatus.approval_required,
            safe_summary="Dry-run envelope for future model download approval scope; no model is downloaded.",
            requested_scope_refs=["scope-ref:macos-setup-model-download-planning"],
            risk_class="high",
            not_scoped_actions=[
                "model-download-execution",
                "model-file-read",
                "model-call",
                "raw-model-url-display",
            ],
            blocked_runtime_authority=[
                "control-center-setup-model-downloads",
                "runtime-model-calls",
                "provider-api-calls",
            ],
            evidence_refs=[
                "docs-ref:local-model-operational-runbook",
                "docs-ref:local-model-packaging-provenance-checklist",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-api-manifest",
                "verifier:openapi-contract",
            ],
            stale_state_handling=(
                "Stale if model refs, route manifest, or local runtime prerequisites change; "
                "rebuild the dry-run envelope before approval review."
            ),
            redaction_summary=(
                "Safe refs and bounded summaries only; raw URLs, raw local paths, prompts, "
                "logs, and provider payloads are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.launch_agent_setup_planning],
            status=MacOSSetupApprovalEnvelopeStatus.blocked_prerequisite_missing,
            safe_summary="Dry-run envelope for future LaunchAgent setup scope; prerequisite authority is missing.",
            requested_scope_refs=["scope-ref:macos-setup-launch-agent-setup-planning"],
            risk_class="high",
            not_scoped_actions=[
                "launch-agent-installation",
                "launch-agent-load",
                "launch-agent-start",
                "launchctl",
            ],
            blocked_runtime_authority=[
                "control-center-setup-launch-agent-changes",
                "shell-subprocess-execution",
                "macos-system-control-authority",
            ],
            evidence_refs=[
                "docs-ref:uaa-setup-assistant-plan",
                "docs-ref:local-runtime-packaging",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-api-routes",
                "verifier:documentation-integrity",
            ],
            stale_state_handling=(
                "Stale until a scoped native packaging milestone defines reviewed LaunchAgent "
                "approval and rollback evidence."
            ),
            redaction_summary=(
                "Safe refs only; plist paths, user paths, hostnames, raw logs, and command "
                "strings are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.local_bridge_setup_planning],
            status=MacOSSetupApprovalEnvelopeStatus.approval_required,
            safe_summary="Dry-run envelope for future local bridge setup scope; no bridge is enabled.",
            requested_scope_refs=["scope-ref:macos-setup-local-bridge-setup-planning"],
            risk_class="high",
            not_scoped_actions=[
                "bridge-enable-now",
                "credential-capture",
                "connector-write",
                "raw-transcript-storage",
            ],
            blocked_runtime_authority=[
                "control-center-setup-credential-handling",
                "openwebui-runtime-authority",
                "connector-writes",
            ],
            evidence_refs=[
                "docs-ref:local-model-operational-runbook",
                "docs-ref:operator-shell-gap-map",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-no-execution",
                "verifier:control-center-frontend",
            ],
            stale_state_handling=(
                "Stale if bridge auth posture, local gateway refs, or credential handling "
                "requirements change."
            ),
            redaction_summary=(
                "Safe refs and disabled-by-default status only; credentials, cookies, "
                "transcripts, prompts, and provider payloads are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.background_service_setup_planning],
            status=MacOSSetupApprovalEnvelopeStatus.not_scoped,
            safe_summary="Dry-run envelope records that background-service setup is not scoped.",
            requested_scope_refs=["scope-ref:macos-setup-background-service-setup-planning"],
            risk_class="high",
            not_scoped_actions=[
                "background-service-installation",
                "background-service-start",
                "daemon-scheduler-worker",
                "auto-start-mechanism",
            ],
            blocked_runtime_authority=[
                "control-center-setup-background-service-changes",
                "autonomous-background-execution",
                "macos-system-control-authority",
            ],
            evidence_refs=[
                "docs-ref:uaa-setup-assistant-plan",
                "docs-ref:local-runtime-packaging",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-api-routes",
                "verifier:documentation-integrity",
            ],
            stale_state_handling=(
                "Stale only when a later accepted milestone scopes background-service "
                "authority with approval, rollback, and safe-disable evidence."
            ),
            redaction_summary=(
                "Safe refs only; service labels, host details, raw logs, paths, and command "
                "strings are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.openwebui_bridge],
            status=MacOSSetupApprovalEnvelopeStatus.approval_required,
            safe_summary="Dry-run envelope for future OpenWebUI bridge review; no bridge, credential, or runtime handoff is enabled.",
            requested_scope_refs=["scope-ref:macos-setup-openwebui-bridge"],
            risk_class="high",
            not_scoped_actions=[
                "openwebui-bridge-enablement",
                "credential-capture",
                "runtime-handoff",
                "raw-transcript-storage",
            ],
            blocked_runtime_authority=[
                "openwebui-runtime-authority",
                "control-center-setup-credential-handling",
                "provider-api-calls",
            ],
            evidence_refs=[
                "docs-ref:uaa-setup-assistant-plan",
                "docs-ref:openwebui-future-integration-stages",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-api-routes",
                "verifier:control-center-frontend",
            ],
            stale_state_handling=(
                "Stale if OpenWebUI auth posture, local gateway refs, credential "
                "requirements, or bridge defaults change before review."
            ),
            redaction_summary=(
                "Safe refs and disabled-by-default status only; credentials, cookies, "
                "transcripts, prompts, and provider payloads are omitted."
            ),
        ),
        _envelope(
            step=steps_by_kind[MacOSSetupStepKind.mattermost_bridge],
            status=MacOSSetupApprovalEnvelopeStatus.approval_required,
            safe_summary="Dry-run envelope for future Mattermost room bridge review; no room join, post, connector write, or transcript capture occurs.",
            requested_scope_refs=["scope-ref:macos-setup-mattermost-bridge"],
            risk_class="high",
            not_scoped_actions=[
                "mattermost-room-join",
                "mattermost-post",
                "connector-write",
                "raw-transcript-storage",
            ],
            blocked_runtime_authority=[
                "mattermost-connector-write",
                "control-center-setup-credential-handling",
                "raw-transcript-persistence",
            ],
            evidence_refs=[
                "docs-ref:uaa-setup-assistant-plan",
                "docs-ref:operator-shell-gap-map",
            ],
            verifier_refs=[
                "pytest:test-macos-setup-assistant",
                "pytest:test-control-center-api-routes",
                "verifier:control-center-frontend",
            ],
            stale_state_handling=(
                "Stale if room approval posture, connector policy, credential handling, "
                "or speak-only defaults change before review."
            ),
            redaction_summary=(
                "Safe refs and disabled-by-default status only; room identifiers, "
                "credentials, raw transcripts, and provider payloads are omitted."
            ),
        ),
    ]


def _envelope(
    *,
    step: MacOSSetupStep,
    status: MacOSSetupApprovalEnvelopeStatus,
    safe_summary: str,
    requested_scope_refs: list[str],
    risk_class: str,
    not_scoped_actions: list[str],
    blocked_runtime_authority: list[str],
    evidence_refs: list[str],
    verifier_refs: list[str],
    stale_state_handling: str,
    redaction_summary: str,
) -> MacOSSetupApprovalEnvelope:
    suffix = step.step_id.split(":")[-1]
    return MacOSSetupApprovalEnvelope(
        envelope_ref=f"macos-setup-approval-envelope:{suffix}",
        status=status,
        setup_step_id=step.step_id,
        setup_step_kind=step.kind,
        safe_summary=safe_summary,
        requested_scope_refs=requested_scope_refs,
        approval_request_ref=step.approval_ref or f"approval-ref:macos-setup-{suffix}",
        expected_receipt_ref=step.receipt_ref,
        rollback_plan_ref=step.rollback_ref,
        idempotency_key_ref=f"idempotency-ref:macos-setup-{suffix}",
        risk_class=risk_class,
        side_effect_class="validation_only",
        not_scoped_actions=not_scoped_actions,
        blocked_runtime_authority=blocked_runtime_authority,
        evidence_refs=evidence_refs,
        verifier_refs=verifier_refs,
        operator_next_action=step.next_safe_action,
        stale_state_handling=stale_state_handling,
        redaction_summary=redaction_summary,
        reason_codes=[
            "MACOS_SETUP_APPROVAL_ENVELOPE_DRY_RUN_ONLY",
            "MACOS_SETUP_APPROVAL_REF_IDENTIFIER_ONLY",
        ],
    )


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
    **kwargs: Any,
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
