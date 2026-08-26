"""Q30 social publishing proposal and deterministic dry-run kernel.

The module operates on synthetic, content-free fixture refs only. It does not
connect accounts, persist drafts, call providers, schedule work, or publish.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    contains_absolute_local_path,
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


CONTRACT_REF = "contract-ref:social-publishing:q30-dry-run:v1"
FIXTURE_REF = "fixture-ref:social-publishing:q30-founder-update"


class Platform(str, Enum):
    instagram = "instagram"
    x = "x"
    tiktok = "tiktok"


class CompatibilitySeverity(str, Enum):
    info = "info"
    warning = "warning"
    blocking = "blocking"
    unknown = "unknown"


class RightsPosture(str, Enum):
    verified_fixture = "verified_fixture"
    missing = "missing"
    unknown = "unknown"


class ApprovalDecision(str, Enum):
    approved_for_dry_run = "approved_for_dry_run"
    rejected = "rejected"


class SettlementStatus(str, Enum):
    succeeded = "succeeded"
    policy_rejected = "policy_rejected"
    platform_rejected = "platform_rejected"
    rate_limited = "rate_limited"
    auth_expired = "auth_expired"
    failed_safely = "failed_safely"
    unknown = "unknown"
    cancelled_before_dispatch = "cancelled_before_dispatch"


class ReconciliationObservation(str, Enum):
    matched = "matched"
    unmatched = "unmatched"
    still_unknown = "still_unknown"


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _walk(value: Any, key: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            found.extend(_walk(child, str(child_key)))
    elif isinstance(value, (list, tuple)):
        for child in value:
            found.extend(_walk(child, key))
    elif isinstance(value, str):
        found.append((key, value))
    return found


class _Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True, use_enum_values=False
    )

    @model_validator(mode="after")
    def validate_safe_values(self) -> "_Contract":
        payload = self.model_dump(mode="json")
        if contains_obvious_secret(payload):
            raise ValueError("Q30_SECRET_LIKE_VALUE_DENIED")
        for key, value in _walk(payload):
            if key.endswith("_ref") or key.endswith("_refs"):
                validate_execution_ref(value, key)
                if contains_absolute_local_path(value):
                    raise ValueError("Q30_LOCAL_PATH_DENIED")
            elif key in {"safe_summary", "next_safe_action", "label"}:
                validate_safe_execution_text(value, key)
        return self


class PlatformCapability(_Contract):
    capability_ref: str
    platform: Platform
    version_ref: str
    source_ref: str
    last_reviewed_ref: str
    supported_format_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    maximum_text_characters: int = Field(ge=1, le=100_000)
    maximum_media_items: int = Field(ge=1, le=64)
    alt_text_supported: bool
    native_scheduling_posture_ref: str
    correction_posture_ref: str
    reconciliation_posture_ref: str
    unknown_constraint_refs: tuple[str, ...] = Field(default=(), max_length=16)
    live_account_configured: Literal[False] = False
    provider_sdk_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    publishing_enabled: Literal[False] = False


class SocialPostDraft(_Contract):
    draft_ref: str
    draft_version_ref: str
    owner_ref: str
    workspace_ref: str
    campaign_ref: str
    objective_ref: str
    content_fingerprint_ref: str
    content_preview_ref: str
    media_version_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    link_refs: tuple[str, ...] = Field(default=(), max_length=12)
    rights_posture: RightsPosture
    fixture_only: Literal[True] = True
    raw_content_included: Literal[False] = False


class SocialPlatformVariant(_Contract):
    variant_ref: str
    variant_version_ref: str
    draft_ref: str
    platform: Platform
    account_ref: str
    content_format_ref: str
    rendered_payload_fingerprint_ref: str
    preview_ref: str
    diff_ref: str
    adaptation_reason_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    media_version_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    alt_text_ref: str | None = None
    rights_posture: RightsPosture
    fixture_only: Literal[True] = True
    raw_content_included: Literal[False] = False


class SocialCompatibilityFinding(_Contract):
    finding_ref: str
    variant_ref: str
    platform: Platform
    severity: CompatibilitySeverity
    constraint_ref: str
    safe_summary: str
    remedy_ref: str | None = None
    override_allowed: Literal[False] = False


class SocialDistributionTarget(_Contract):
    target_ref: str
    variant_ref: str
    platform: Platform
    account_ref: str
    operation_ref: str
    payload_fingerprint_ref: str
    requested_time_ref: str
    timezone_ref: str
    child_idempotency_ref: str
    adapter_posture_ref: str
    live_adapter_available: Literal[False] = False


class SocialPublishPlan(_Contract):
    plan_ref: str
    plan_fingerprint_ref: str
    contract_ref: Literal[CONTRACT_REF] = CONTRACT_REF
    draft_ref: str
    draft_version_ref: str
    parent_idempotency_ref: str
    target_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    targets: tuple[SocialDistributionTarget, ...] = Field(min_length=1, max_length=12)
    finding_refs: tuple[str, ...]
    findings: tuple[SocialCompatibilityFinding, ...]
    expires_at_ref: str
    safe_disable_ref: str
    correction_posture_ref: str
    reconciliation_posture_ref: str
    approval_required: Literal[True] = True
    dry_run_only: Literal[True] = True
    publishing_enabled: Literal[False] = False
    external_write_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan_bindings(self) -> "SocialPublishPlan":
        if self.target_refs != tuple(target.target_ref for target in self.targets):
            raise ValueError("Q30_TARGET_INVENTORY_DRIFT")
        if len(self.target_refs) != len(set(self.target_refs)):
            raise ValueError("Q30_DUPLICATE_TARGET")
        if self.finding_refs != tuple(item.finding_ref for item in self.findings):
            raise ValueError("Q30_FINDING_INVENTORY_DRIFT")
        if any(
            finding.severity
            in {CompatibilitySeverity.blocking, CompatibilitySeverity.unknown}
            for finding in self.findings
        ):
            raise ValueError("Q30_BLOCKING_OR_UNKNOWN_FINDING")
        if self.plan_fingerprint_ref != _plan_fingerprint(self):
            raise ValueError("Q30_PLAN_FINGERPRINT_DRIFT")
        return self


class SocialPublishApprovalEnvelope(_Contract):
    envelope_ref: str
    plan_ref: str
    plan_fingerprint_ref: str
    decision: ApprovalDecision
    decision_ref: str
    reviewed_target_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    reviewed_payload_fingerprint_refs: tuple[str, ...] = Field(
        min_length=1, max_length=12
    )
    expires_at_ref: str
    dry_run_only: Literal[True] = True
    live_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_envelope_identity(self) -> "SocialPublishApprovalEnvelope":
        expected_decision_ref = f"approval-decision-ref:q30:{self.decision.value}"
        expected_envelope_ref = _stable_ref(
            "social-publish-approval-envelope-ref",
            {"plan": self.plan_fingerprint_ref, "decision": self.decision.value},
        )
        if self.decision_ref != expected_decision_ref:
            raise ValueError("Q30_APPROVAL_DECISION_REF_DRIFT")
        if self.envelope_ref != expected_envelope_ref:
            raise ValueError("Q30_APPROVAL_ENVELOPE_REF_DRIFT")
        return self


class DryRunScenario(_Contract):
    scenario_ref: str
    plan_ref: str
    outcome_by_target_ref: dict[str, SettlementStatus] = Field(
        min_length=1, max_length=12
    )
    fixture_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_target_refs(self) -> "DryRunScenario":
        for target_ref in self.outcome_by_target_ref:
            validate_execution_ref(target_ref, "outcome_target_ref")
            if contains_absolute_local_path(target_ref):
                raise ValueError("Q30_LOCAL_PATH_DENIED")
        return self


class SocialPublishSettlement(_Contract):
    settlement_ref: str
    target_ref: str
    attempt_ref: str
    status: SettlementStatus
    evidence_ref: str
    retry_eligible: bool
    reconciliation_required: bool
    simulated: Literal[True] = True
    external_side_effect_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_settlement_posture(self) -> "SocialPublishSettlement":
        expected_retry = self.status in {
            SettlementStatus.rate_limited,
            SettlementStatus.failed_safely,
        }
        if self.retry_eligible is not expected_retry:
            raise ValueError("Q30_SETTLEMENT_RETRY_POSTURE_DRIFT")
        if self.reconciliation_required is not (
            self.status is SettlementStatus.unknown
        ):
            raise ValueError("Q30_SETTLEMENT_RECONCILIATION_POSTURE_DRIFT")
        return self


class SocialPublishReceipt(_Contract):
    receipt_ref: str
    plan_ref: str
    target_ref: str
    payload_fingerprint_ref: str
    settlement_ref: str
    settlement_status: SettlementStatus
    idempotency_ref: str
    reconciliation_posture_ref: str
    simulated: Literal[True] = True
    raw_content_included: Literal[False] = False
    external_side_effect_performed: Literal[False] = False


class SocialDryRunResult(_Contract):
    result_ref: str
    plan_ref: str
    envelope_ref: str
    request_fingerprint_ref: str
    status_ref: str
    settlements: tuple[SocialPublishSettlement, ...]
    receipts: tuple[SocialPublishReceipt, ...]
    succeeded_target_refs: tuple[str, ...]
    retry_eligible_target_refs: tuple[str, ...]
    reconciliation_required_target_refs: tuple[str, ...]
    next_safe_action: str
    replayed: bool = False
    simulated: Literal[True] = True
    publishing_enabled: Literal[False] = False
    external_side_effect_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_result_settlement_inventory(self) -> "SocialDryRunResult":
        settlement_targets = tuple(item.target_ref for item in self.settlements)
        receipt_targets = tuple(item.target_ref for item in self.receipts)
        if not settlement_targets or len(settlement_targets) != len(
            set(settlement_targets)
        ):
            raise ValueError("Q30_RESULT_SETTLEMENT_TARGET_INVENTORY_INVALID")
        if receipt_targets != settlement_targets:
            raise ValueError("Q30_RESULT_RECEIPT_TARGET_INVENTORY_DRIFT")
        for settlement, receipt in zip(self.settlements, self.receipts, strict=True):
            if (
                receipt.plan_ref != self.plan_ref
                or receipt.settlement_ref != settlement.settlement_ref
                or receipt.settlement_status is not settlement.status
            ):
                raise ValueError("Q30_RESULT_RECEIPT_BINDING_DRIFT")
        expected_succeeded = tuple(
            item.target_ref
            for item in self.settlements
            if item.status is SettlementStatus.succeeded
        )
        expected_retry = tuple(
            item.target_ref for item in self.settlements if item.retry_eligible
        )
        expected_reconcile = tuple(
            item.target_ref for item in self.settlements if item.reconciliation_required
        )
        if self.succeeded_target_refs != expected_succeeded:
            raise ValueError("Q30_RESULT_SUCCESS_INVENTORY_DRIFT")
        if self.retry_eligible_target_refs != expected_retry:
            raise ValueError("Q30_RESULT_RETRY_INVENTORY_DRIFT")
        if self.reconciliation_required_target_refs != expected_reconcile:
            raise ValueError("Q30_RESULT_RECONCILIATION_INVENTORY_DRIFT")
        return self


class SocialReconciliationResult(_Contract):
    reconciliation_ref: str
    prior_result_ref: str
    target_ref: str
    observation: ReconciliationObservation
    matched_existing_publication: bool
    retry_eligible: bool
    new_approval_required: bool
    evidence_ref: str
    next_safe_action: str
    simulated: Literal[True] = True
    network_access_enabled: Literal[False] = False
    external_side_effect_performed: Literal[False] = False


class SocialRetryPlan(_Contract):
    retry_plan_ref: str
    prior_result_ref: str
    target_refs: tuple[str, ...] = Field(min_length=1, max_length=12)
    new_approval_required: Literal[True] = True
    dry_run_only: Literal[True] = True
    publishing_enabled: Literal[False] = False
    external_side_effect_performed: Literal[False] = False


class SocialPublishingFixture(_Contract):
    fixture_ref: Literal[FIXTURE_REF] = FIXTURE_REF
    contract_ref: Literal[CONTRACT_REF] = CONTRACT_REF
    draft: SocialPostDraft
    capabilities: tuple[PlatformCapability, ...] = Field(min_length=3, max_length=3)
    variants: tuple[SocialPlatformVariant, ...] = Field(min_length=3, max_length=3)
    findings: tuple[SocialCompatibilityFinding, ...]
    plan: SocialPublishPlan
    safe_summary: str
    next_safe_action: str
    live_account_access_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    background_scheduler_enabled: Literal[False] = False
    publishing_enabled: Literal[False] = False


def _plan_fingerprint(plan: SocialPublishPlan) -> str:
    return _stable_ref(
        "social-publish-plan-fingerprint-ref",
        {
            "plan_ref": plan.plan_ref,
            "contract_ref": plan.contract_ref,
            "draft_ref": plan.draft_ref,
            "draft_version_ref": plan.draft_version_ref,
            "parent_idempotency_ref": plan.parent_idempotency_ref,
            "target_refs": plan.target_refs,
            "targets": [target.model_dump(mode="json") for target in plan.targets],
            "finding_refs": plan.finding_refs,
            "findings": [finding.model_dump(mode="json") for finding in plan.findings],
            "expires_at_ref": plan.expires_at_ref,
            "safe_disable_ref": plan.safe_disable_ref,
            "correction_posture_ref": plan.correction_posture_ref,
            "reconciliation_posture_ref": plan.reconciliation_posture_ref,
            "approval_required": plan.approval_required,
            "dry_run_only": plan.dry_run_only,
            "publishing_enabled": plan.publishing_enabled,
            "external_write_enabled": plan.external_write_enabled,
        },
    )


def _finding(
    *, variant: SocialPlatformVariant, severity: CompatibilitySeverity, suffix: str
) -> SocialCompatibilityFinding:
    summaries = {
        CompatibilitySeverity.info: "Fixture variant satisfies the reviewed capability contract.",
        CompatibilitySeverity.warning: "Fixture variant is compatible but keeps an operator-visible adaptation warning.",
        CompatibilitySeverity.blocking: "Fixture variant is blocked by a known capability constraint.",
        CompatibilitySeverity.unknown: "Fixture variant is blocked because a required capability remains unknown.",
    }
    return SocialCompatibilityFinding(
        finding_ref=f"social-compatibility-finding-ref:{variant.platform.value}:{suffix}",
        variant_ref=variant.variant_ref,
        platform=variant.platform,
        severity=severity,
        constraint_ref=f"platform-constraint-ref:{variant.platform.value}:{suffix}",
        safe_summary=summaries[severity],
        remedy_ref=(
            None
            if severity is CompatibilitySeverity.info
            else f"remedy-ref:social-publishing:{variant.platform.value}:{suffix}"
        ),
    )


def evaluate_variant_compatibility(
    variant: SocialPlatformVariant,
    capability: PlatformCapability,
) -> tuple[SocialCompatibilityFinding, ...]:
    variant = SocialPlatformVariant.model_validate(variant.model_dump(mode="python"))
    capability = PlatformCapability.model_validate(capability.model_dump(mode="python"))
    if variant.platform is not capability.platform:
        raise ValueError("Q30_VARIANT_CAPABILITY_PLATFORM_MISMATCH")
    if variant.content_format_ref not in capability.supported_format_refs:
        severity = CompatibilitySeverity.blocking
        suffix = "unsupported-format"
    elif variant.rights_posture is not RightsPosture.verified_fixture:
        severity = CompatibilitySeverity.blocking
        suffix = "media-rights-not-verified"
    elif capability.unknown_constraint_refs:
        severity = CompatibilitySeverity.unknown
        suffix = "capability-unknown"
    elif capability.alt_text_supported and variant.alt_text_ref is None:
        severity = CompatibilitySeverity.warning
        suffix = "alt-text-missing"
    else:
        severity = CompatibilitySeverity.info
        suffix = "compatible"
    return (_finding(variant=variant, severity=severity, suffix=suffix),)


def build_q30_fixture() -> SocialPublishingFixture:
    draft = SocialPostDraft(
        draft_ref="social-draft-ref:q30-founder-update",
        draft_version_ref="social-draft-version-ref:q30-founder-update:v1",
        owner_ref="owner-ref:studio",
        workspace_ref="workspace-ref:founder-private",
        campaign_ref="campaign-ref:q30-private-dogfood",
        objective_ref="objective-ref:q30-product-update",
        content_fingerprint_ref="content-fingerprint-ref:sha256:85d384173f2620040d8f1bb9d31b06ceebd51a58bcbe7d475ef083abc0606d2d",
        content_preview_ref="content-preview-ref:q30-founder-update-redacted",
        media_version_refs=("media-version-ref:q30-product-still:v1",),
        link_refs=("link-ref:q30-product-update",),
        rights_posture=RightsPosture.verified_fixture,
    )
    capabilities = tuple(
        PlatformCapability(
            capability_ref=f"platform-capability-ref:q30:{platform.value}:v1",
            platform=platform,
            version_ref=f"platform-capability-version-ref:{platform.value}:fixture-v1",
            source_ref=f"source-ref:q30-reviewed-fixture:{platform.value}",
            last_reviewed_ref="time-ref:q30-fixture-review-20260826",
            supported_format_refs=(
                f"content-format-ref:{platform.value}:single-image",
            ),
            maximum_text_characters=(2200 if platform is Platform.instagram else 280),
            maximum_media_items=(10 if platform is Platform.instagram else 4),
            alt_text_supported=True,
            native_scheduling_posture_ref=f"capability-posture-ref:{platform.value}:unknown-live",
            correction_posture_ref=f"correction-posture-ref:{platform.value}:future-gated",
            reconciliation_posture_ref=f"reconciliation-posture-ref:{platform.value}:fixture-only",
        )
        for platform in Platform
    )
    variants = tuple(
        SocialPlatformVariant(
            variant_ref=f"social-variant-ref:q30:{platform.value}",
            variant_version_ref=f"social-variant-version-ref:q30:{platform.value}:v1",
            draft_ref=draft.draft_ref,
            platform=platform,
            account_ref=f"social-account-ref:fixture:{platform.value}",
            content_format_ref=f"content-format-ref:{platform.value}:single-image",
            rendered_payload_fingerprint_ref=_stable_ref(
                "social-payload-fingerprint-ref",
                {"draft": draft.draft_version_ref, "platform": platform.value},
            ),
            preview_ref=f"social-preview-ref:q30:{platform.value}:redacted",
            diff_ref=f"social-diff-ref:q30:{platform.value}:v1",
            adaptation_reason_refs=(
                f"adaptation-reason-ref:{platform.value}:format-and-cadence",
            ),
            media_version_refs=draft.media_version_refs,
            alt_text_ref=f"alt-text-ref:q30:{platform.value}:reviewed-fixture",
            rights_posture=RightsPosture.verified_fixture,
        )
        for platform in Platform
    )
    findings = tuple(
        finding
        for variant, capability in zip(variants, capabilities, strict=True)
        for finding in evaluate_variant_compatibility(variant, capability)
    ) + (
        _finding(
            variant=variants[1],
            severity=CompatibilitySeverity.warning,
            suffix="concise-adaptation",
        ),
    )
    targets = tuple(
        SocialDistributionTarget(
            target_ref=f"social-target-ref:q30:{variant.platform.value}",
            variant_ref=variant.variant_ref,
            platform=variant.platform,
            account_ref=variant.account_ref,
            operation_ref=f"operation-ref:social-publishing:{variant.platform.value}:create-post-dry-run",
            payload_fingerprint_ref=variant.rendered_payload_fingerprint_ref,
            requested_time_ref=f"requested-time-ref:q30:{variant.platform.value}:fixture-window",
            timezone_ref="timezone-ref:america-los-angeles",
            child_idempotency_ref=f"idempotency-ref:q30:{variant.platform.value}:fixture-v1",
            adapter_posture_ref=f"adapter-posture-ref:{variant.platform.value}:not-installed",
        )
        for variant in variants
    )
    plan_payload: dict[str, Any] = {
        "plan_ref": "social-publish-plan-ref:q30-founder-update:v1",
        "plan_fingerprint_ref": "social-publish-plan-fingerprint-ref:sha256:placeholder",
        "draft_ref": draft.draft_ref,
        "draft_version_ref": draft.draft_version_ref,
        "parent_idempotency_ref": "idempotency-ref:q30:founder-update:v1",
        "target_refs": tuple(target.target_ref for target in targets),
        "targets": targets,
        "finding_refs": tuple(item.finding_ref for item in findings),
        "findings": findings,
        "expires_at_ref": "expiry-ref:q30:fixture-review-window",
        "safe_disable_ref": "safe-disable-ref:social-publishing:q30-default-deny",
        "correction_posture_ref": "correction-posture-ref:q30:new-plan-required",
        "reconciliation_posture_ref": "reconciliation-posture-ref:q30:unknown-blocks-retry",
    }
    unchecked = SocialPublishPlan.model_construct(**plan_payload)
    plan_payload["plan_fingerprint_ref"] = _plan_fingerprint(unchecked)
    plan = SocialPublishPlan.model_validate(plan_payload)
    return SocialPublishingFixture(
        draft=draft,
        capabilities=capabilities,
        variants=variants,
        findings=findings,
        plan=plan,
        safe_summary="A synthetic three-platform publish bundle is ready for exact dry-run review only.",
        next_safe_action="Review the exact fixture bundle, then simulate independent target settlements without connecting accounts.",
    )


def build_review_envelope(
    plan: SocialPublishPlan, decision: ApprovalDecision
) -> SocialPublishApprovalEnvelope:
    return SocialPublishApprovalEnvelope(
        envelope_ref=_stable_ref(
            "social-publish-approval-envelope-ref",
            {"plan": plan.plan_fingerprint_ref, "decision": decision.value},
        ),
        plan_ref=plan.plan_ref,
        plan_fingerprint_ref=plan.plan_fingerprint_ref,
        decision=decision,
        decision_ref=f"approval-decision-ref:q30:{decision.value}",
        reviewed_target_refs=plan.target_refs,
        reviewed_payload_fingerprint_refs=tuple(
            target.payload_fingerprint_ref for target in plan.targets
        ),
        expires_at_ref=plan.expires_at_ref,
    )


def build_scenario(
    plan: SocialPublishPlan, name: Literal["success", "mixed", "unknown"]
) -> DryRunScenario:
    if name == "success":
        statuses = (SettlementStatus.succeeded,) * len(plan.targets)
    elif name == "mixed":
        statuses = (
            SettlementStatus.succeeded,
            SettlementStatus.rate_limited,
            SettlementStatus.failed_safely,
        )
    else:
        statuses = (
            SettlementStatus.succeeded,
            SettlementStatus.unknown,
            SettlementStatus.cancelled_before_dispatch,
        )
    return DryRunScenario(
        scenario_ref=f"dry-run-scenario-ref:q30:{name}",
        plan_ref=plan.plan_ref,
        outcome_by_target_ref=dict(zip(plan.target_refs, statuses, strict=True)),
    )


class SocialPublishingDryRunKernel:
    """Process-local deterministic replay owner for Q30 fixture simulations."""

    def __init__(self) -> None:
        self._results: dict[str, tuple[str, SocialDryRunResult]] = {}

    def execute(
        self,
        *,
        plan: SocialPublishPlan,
        envelope: SocialPublishApprovalEnvelope,
        scenario: DryRunScenario,
    ) -> SocialDryRunResult:
        # Pydantic's model_copy deliberately skips validation. Re-enter through
        # the strict contracts at this authority boundary so a forged copy
        # cannot alter a Literal posture, safe ref, or exact plan binding.
        plan = SocialPublishPlan.model_validate(plan.model_dump(mode="python"))
        envelope = SocialPublishApprovalEnvelope.model_validate(
            envelope.model_dump(mode="python")
        )
        scenario = DryRunScenario.model_validate(scenario.model_dump(mode="python"))
        if envelope.decision is not ApprovalDecision.approved_for_dry_run:
            raise ValueError("Q30_DRY_RUN_NOT_APPROVED")
        if (
            envelope.plan_ref != plan.plan_ref
            or envelope.plan_fingerprint_ref != plan.plan_fingerprint_ref
            or envelope.reviewed_target_refs != plan.target_refs
            or envelope.reviewed_payload_fingerprint_refs
            != tuple(target.payload_fingerprint_ref for target in plan.targets)
            or envelope.expires_at_ref != plan.expires_at_ref
        ):
            raise ValueError("Q30_APPROVAL_ENVELOPE_BINDING_DRIFT")
        if scenario.plan_ref != plan.plan_ref or set(
            scenario.outcome_by_target_ref
        ) != set(plan.target_refs):
            raise ValueError("Q30_SCENARIO_TARGET_BINDING_DRIFT")
        request_ref = _stable_ref(
            "social-dry-run-request-fingerprint-ref",
            {
                "plan": plan.plan_fingerprint_ref,
                "envelope": envelope.model_dump(mode="json"),
                "scenario": scenario.model_dump(mode="json"),
            },
        )
        replay_key = plan.parent_idempotency_ref
        existing = self._results.get(replay_key)
        if existing:
            if existing[0] != request_ref:
                raise ValueError("Q30_IDEMPOTENCY_CONFLICT")
            return existing[1].model_copy(update={"replayed": True})

        settlements: list[SocialPublishSettlement] = []
        receipts: list[SocialPublishReceipt] = []
        retry: list[str] = []
        reconcile: list[str] = []
        succeeded: list[str] = []
        retry_statuses = {
            SettlementStatus.rate_limited,
            SettlementStatus.failed_safely,
        }
        for target in plan.targets:
            status = scenario.outcome_by_target_ref[target.target_ref]
            retry_eligible = status in retry_statuses
            reconciliation_required = status is SettlementStatus.unknown
            settlement = SocialPublishSettlement(
                settlement_ref=_stable_ref(
                    "social-publish-settlement-ref",
                    {"target": target.target_ref, "status": status.value},
                ),
                target_ref=target.target_ref,
                attempt_ref=f"social-publish-attempt-ref:q30:{target.platform.value}:1",
                status=status,
                evidence_ref=f"evidence-ref:q30:simulated:{target.platform.value}:{status.value}",
                retry_eligible=retry_eligible,
                reconciliation_required=reconciliation_required,
            )
            settlements.append(settlement)
            receipts.append(
                SocialPublishReceipt(
                    receipt_ref=_stable_ref(
                        "social-publish-receipt-ref",
                        {
                            "plan": plan.plan_ref,
                            "target": target.target_ref,
                            "settlement": settlement.settlement_ref,
                        },
                    ),
                    plan_ref=plan.plan_ref,
                    target_ref=target.target_ref,
                    payload_fingerprint_ref=target.payload_fingerprint_ref,
                    settlement_ref=settlement.settlement_ref,
                    settlement_status=status,
                    idempotency_ref=target.child_idempotency_ref,
                    reconciliation_posture_ref=(
                        "reconciliation-posture-ref:q30:required-before-retry"
                        if reconciliation_required
                        else "reconciliation-posture-ref:q30:not-required"
                    ),
                )
            )
            if status is SettlementStatus.succeeded:
                succeeded.append(target.target_ref)
            if retry_eligible:
                retry.append(target.target_ref)
            if reconciliation_required:
                reconcile.append(target.target_ref)

        if reconcile:
            status_ref = "dry-run-status-ref:q30:unknown-reconciliation-required"
            next_action = (
                "Reconcile every unknown simulated target before considering a retry."
            )
        elif len(succeeded) == len(plan.targets):
            status_ref = "dry-run-status-ref:q30:all-simulated-succeeded"
            next_action = (
                "Retain the content-free receipts; no target is eligible for retry."
            )
        else:
            status_ref = "dry-run-status-ref:q30:partially-simulated"
            next_action = "Preserve simulated successes and retry only explicitly eligible failed targets under a new exact review."
        result = SocialDryRunResult(
            result_ref=_stable_ref(
                "social-dry-run-result-ref",
                {
                    "request": request_ref,
                    "settlements": [item.settlement_ref for item in settlements],
                },
            ),
            plan_ref=plan.plan_ref,
            envelope_ref=envelope.envelope_ref,
            request_fingerprint_ref=request_ref,
            status_ref=status_ref,
            settlements=tuple(settlements),
            receipts=tuple(receipts),
            succeeded_target_refs=tuple(succeeded),
            retry_eligible_target_refs=tuple(retry),
            reconciliation_required_target_refs=tuple(reconcile),
            next_safe_action=next_action,
        )
        self._results[replay_key] = (request_ref, result)
        return result


def reconcile_unknown_settlement(
    result: SocialDryRunResult,
    *,
    target_ref: str,
    observation: ReconciliationObservation,
) -> SocialReconciliationResult:
    result = SocialDryRunResult.model_validate(result.model_dump(mode="python"))
    validate_execution_ref(target_ref, "target_ref")
    if target_ref not in result.reconciliation_required_target_refs:
        raise ValueError("Q30_RECONCILIATION_NOT_REQUIRED")
    matched = observation is ReconciliationObservation.matched
    retry_eligible = observation is ReconciliationObservation.unmatched
    summaries = {
        ReconciliationObservation.matched: "The fixture reconciliation matched a simulated publication; retry remains blocked.",
        ReconciliationObservation.unmatched: "The fixture reconciliation found no publication; a new exact approval is required before retry.",
        ReconciliationObservation.still_unknown: "The fixture outcome remains unknown; retry remains blocked.",
    }
    return SocialReconciliationResult(
        reconciliation_ref=_stable_ref(
            "social-publish-reconciliation-ref",
            {
                "result": result.result_ref,
                "target": target_ref,
                "observation": observation.value,
            },
        ),
        prior_result_ref=result.result_ref,
        target_ref=target_ref,
        observation=observation,
        matched_existing_publication=matched,
        retry_eligible=retry_eligible,
        new_approval_required=retry_eligible,
        evidence_ref=f"evidence-ref:q30:simulated-reconciliation:{observation.value}",
        next_safe_action=summaries[observation],
    )


def build_retry_plan(
    result: SocialDryRunResult, *, target_refs: tuple[str, ...]
) -> SocialRetryPlan:
    result = SocialDryRunResult.model_validate(result.model_dump(mode="python"))
    if len(target_refs) != len(set(target_refs)):
        raise ValueError("Q30_RETRY_TARGET_DUPLICATE")
    if not target_refs or not set(target_refs).issubset(
        set(result.retry_eligible_target_refs)
    ):
        raise ValueError("Q30_RETRY_TARGET_NOT_ELIGIBLE")
    if set(target_refs) & (
        set(result.succeeded_target_refs)
        | set(result.reconciliation_required_target_refs)
    ):
        raise ValueError("Q30_RETRY_TARGET_NOT_ELIGIBLE")
    return SocialRetryPlan(
        retry_plan_ref=_stable_ref(
            "social-retry-plan-ref",
            {"prior_result": result.result_ref, "targets": target_refs},
        ),
        prior_result_ref=result.result_ref,
        target_refs=target_refs,
    )
