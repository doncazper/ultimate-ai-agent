"""Queue 02 evidence-gated activation decisions for Queue 01 lanes.

This module records hardening evidence and fail-closed activation posture.  It
does not activate an adapter, target, browser, network, or external mutation.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.planning.validation import validate_task_ref

from .contracts import stable_governed_browser_ref


class GovernedBrowserQueue02Lane(str, Enum):
    exact_authority_binding = "01_exact_authority_binding"
    isolated_browser_broker = "02_isolated_browser_broker"
    external_action_kernel = "03_external_action_kernel"
    action_inbox_envelope = "04_action_inbox_envelope"
    evidence_recipes = "05_evidence_recipes"
    visible_click_get_form = "06_visible_click_get_form"
    exact_post_form = "07_exact_post_form"
    keychain_origin_session = "08_keychain_origin_session"
    human_challenge_handoff = "09_human_challenge_handoff"
    artifact_transfer = "10_artifact_transfer"
    external_operation_contracts = "11_external_operation_contracts"
    financial_operation_contracts = "12_financial_operation_contracts"
    task_composer = "13_task_composer"


class GovernedBrowserActivationPosture(str, Enum):
    adapter_required = "adapter_required"
    configuration_required = "configuration_required"
    external_facility_required = "external_facility_required"
    blocked_pending_live_evidence = "blocked_pending_live_evidence"
    eligible_for_separate_activation_review = "eligible_for_separate_activation_review"


class GovernedBrowserLaneActivationEvidence(BaseModel):
    """Exact evidence required before a separate activation review is possible."""

    schema_version: Literal["uaa-governed-browser-lane-activation-evidence.v1"] = (
        "uaa-governed-browser-lane-activation-evidence.v1"
    )
    lane: GovernedBrowserQueue02Lane
    evidence_ref: str
    implementation_verified: StrictBool
    focused_tests_verified: StrictBool
    adversarial_tests_verified: StrictBool
    request_scoped_policy_verified: StrictBool
    exact_approval_verified: StrictBool
    authority_lease_verified: StrictBool
    target_readiness_verified: StrictBool
    adapter_readiness_verified: StrictBool
    budget_posture_verified: StrictBool
    kill_switch_verified: StrictBool
    safe_disable_verified: StrictBool
    deadline_verified: StrictBool
    idempotency_verified: StrictBool
    receipt_verified: StrictBool
    reconciliation_verified: StrictBool
    recovery_verified: StrictBool
    macos_packaged_golden_verified: StrictBool
    activation_configuration_complete: StrictBool
    external_facility_available: StrictBool
    live_external_evidence_verified: StrictBool
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=24)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_evidence(self) -> "GovernedBrowserLaneActivationEvidence":
        validate_task_ref(self.evidence_ref, "activation_evidence_ref")
        for ref in self.evidence_refs:
            validate_task_ref(ref, "activation_supporting_evidence_ref")
        expected_ref = stable_governed_browser_ref(
            "activation-evidence-ref:governed-browser-queue02",
            self.model_dump(mode="json", exclude={"schema_version", "evidence_ref"}),
        )
        if self.evidence_ref != expected_ref:
            raise ValueError("GOVERNED_BROWSER_ACTIVATION_EVIDENCE_REF_MISMATCH")
        return self


class GovernedBrowserLaneActivationDecision(BaseModel):
    """Fail-closed posture for one lane; no value represents active authority."""

    schema_version: Literal["uaa-governed-browser-lane-activation-decision.v1"] = (
        "uaa-governed-browser-lane-activation-decision.v1"
    )
    decision_ref: str
    lane: GovernedBrowserQueue02Lane
    evidence_ref: str
    posture: GovernedBrowserActivationPosture
    reason_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    activation_performed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False
    browser_action_enabled: Literal[False] = False
    live_network_enabled: Literal[False] = False
    external_mutation_enabled: Literal[False] = False
    standing_authority_granted: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_decision(self) -> "GovernedBrowserLaneActivationDecision":
        for ref in (self.decision_ref, self.evidence_ref, *self.reason_refs):
            validate_task_ref(ref, "activation_decision_ref")
        expected_ref = stable_governed_browser_ref(
            "activation-decision-ref:governed-browser-queue02",
            self.model_dump(mode="json", exclude={"schema_version", "decision_ref"}),
        )
        if self.decision_ref != expected_ref:
            raise ValueError("GOVERNED_BROWSER_ACTIVATION_DECISION_REF_MISMATCH")
        return self


_CORE_EVIDENCE_FIELDS = (
    "implementation_verified",
    "focused_tests_verified",
    "adversarial_tests_verified",
    "request_scoped_policy_verified",
    "exact_approval_verified",
    "authority_lease_verified",
    "budget_posture_verified",
    "kill_switch_verified",
    "safe_disable_verified",
    "deadline_verified",
    "idempotency_verified",
    "receipt_verified",
    "reconciliation_verified",
    "recovery_verified",
    "macos_packaged_golden_verified",
)


def decide_governed_browser_lane_activation(
    evidence: GovernedBrowserLaneActivationEvidence,
) -> GovernedBrowserLaneActivationDecision:
    """Return a separate-review posture without activating the lane."""

    if not evidence.adapter_readiness_verified:
        posture = GovernedBrowserActivationPosture.adapter_required
        reasons = ("reason-ref:governed-browser-queue02:adapter-required",)
    elif not evidence.activation_configuration_complete:
        posture = GovernedBrowserActivationPosture.configuration_required
        reasons = ("reason-ref:governed-browser-queue02:configuration-required",)
    elif not evidence.external_facility_available:
        posture = GovernedBrowserActivationPosture.external_facility_required
        reasons = ("reason-ref:governed-browser-queue02:external-facility-required",)
    elif not evidence.target_readiness_verified:
        posture = GovernedBrowserActivationPosture.blocked_pending_live_evidence
        reasons = ("reason-ref:governed-browser-queue02:target-readiness-unverified",)
    else:
        missing = tuple(
            field for field in _CORE_EVIDENCE_FIELDS if not getattr(evidence, field)
        )
        if missing or not evidence.live_external_evidence_verified:
            posture = GovernedBrowserActivationPosture.blocked_pending_live_evidence
            reasons = (
                stable_governed_browser_ref(
                    "reason-ref:governed-browser-queue02:evidence-missing",
                    {
                        "lane": evidence.lane,
                        "fields": (missing or ("live_external_evidence_verified",)),
                    },
                ),
            )
        else:
            posture = (
                GovernedBrowserActivationPosture.eligible_for_separate_activation_review
            )
            reasons = ("reason-ref:governed-browser-queue02:separate-review-required",)
    payload = {
        "lane": evidence.lane,
        "evidence_ref": evidence.evidence_ref,
        "posture": posture,
        "reason_refs": reasons,
        "activation_performed": False,
        "real_external_targets_enabled": False,
        "browser_action_enabled": False,
        "live_network_enabled": False,
        "external_mutation_enabled": False,
        "standing_authority_granted": False,
    }
    decision_ref = stable_governed_browser_ref(
        "activation-decision-ref:governed-browser-queue02",
        {
            key: value.value if isinstance(value, Enum) else value
            for key, value in payload.items()
        },
    )
    return GovernedBrowserLaneActivationDecision(
        decision_ref=decision_ref,
        **payload,
    )


_QUEUE02_POSTURES = {
    GovernedBrowserQueue02Lane.exact_authority_binding: (
        GovernedBrowserActivationPosture.configuration_required
    ),
    GovernedBrowserQueue02Lane.isolated_browser_broker: (
        GovernedBrowserActivationPosture.adapter_required
    ),
    GovernedBrowserQueue02Lane.external_action_kernel: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.action_inbox_envelope: (
        GovernedBrowserActivationPosture.configuration_required
    ),
    GovernedBrowserQueue02Lane.evidence_recipes: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.visible_click_get_form: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.exact_post_form: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.keychain_origin_session: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.human_challenge_handoff: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.artifact_transfer: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.external_operation_contracts: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.financial_operation_contracts: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
    GovernedBrowserQueue02Lane.task_composer: (
        GovernedBrowserActivationPosture.external_facility_required
    ),
}


def governed_browser_queue02_inactive_activation_matrix(
    *,
    macos_packaged_golden_verified: bool,
) -> tuple[GovernedBrowserLaneActivationDecision, ...]:
    """Build the honest all-inactive matrix for the thirteen Queue 01 lanes."""

    decisions: list[GovernedBrowserLaneActivationDecision] = []
    supporting_refs = (
        "evidence-ref:governed-browser-queue02:focused-tests",
        "evidence-ref:governed-browser-queue02:adversarial-campaign",
        "evidence-ref:governed-browser-queue02:full-regression",
    )
    for lane, required_posture in _QUEUE02_POSTURES.items():
        adapter_ready = (
            required_posture != GovernedBrowserActivationPosture.adapter_required
        )
        configuration_complete = (
            required_posture != GovernedBrowserActivationPosture.configuration_required
        )
        facility_available = required_posture not in {
            GovernedBrowserActivationPosture.external_facility_required,
            GovernedBrowserActivationPosture.adapter_required,
            GovernedBrowserActivationPosture.configuration_required,
        }
        payload = {
            "lane": lane,
            "implementation_verified": True,
            "focused_tests_verified": True,
            "adversarial_tests_verified": True,
            "request_scoped_policy_verified": True,
            "exact_approval_verified": True,
            "authority_lease_verified": True,
            "target_readiness_verified": False,
            "adapter_readiness_verified": adapter_ready,
            "budget_posture_verified": True,
            "kill_switch_verified": True,
            "safe_disable_verified": True,
            "deadline_verified": True,
            "idempotency_verified": True,
            "receipt_verified": True,
            "reconciliation_verified": True,
            "recovery_verified": True,
            "macos_packaged_golden_verified": macos_packaged_golden_verified,
            "activation_configuration_complete": configuration_complete,
            "external_facility_available": facility_available,
            "live_external_evidence_verified": False,
            "evidence_refs": supporting_refs,
        }
        evidence_ref = stable_governed_browser_ref(
            "activation-evidence-ref:governed-browser-queue02",
            {
                key: value.value if isinstance(value, Enum) else value
                for key, value in payload.items()
            },
        )
        evidence = GovernedBrowserLaneActivationEvidence(
            evidence_ref=evidence_ref,
            **payload,
        )
        decision = decide_governed_browser_lane_activation(evidence)
        if decision.posture != required_posture.value:
            raise ValueError("GOVERNED_BROWSER_QUEUE02_MATRIX_POSTURE_MISMATCH")
        decisions.append(decision)
    return tuple(decisions)
