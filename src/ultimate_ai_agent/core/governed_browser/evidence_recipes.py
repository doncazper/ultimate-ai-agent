"""Registered Evidence Recipes for exact injected browser observation.

Queue 01 item 05 composes the existing WebAccessGateway, isolated broker, and
external-action transaction kernel. It does not add a browser engine, live
network transport, navigation, clicks, forms, authenticated profiles, or real
external-target authority.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationError,
    model_validator,
)

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.web_access import (
    WebAccessAdapterKind,
    WebAccessAuthorityMode,
    WebAccessGateway,
    WebAccessNetworkLane,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)

from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    governed_receipt_identity_payload,
    stable_governed_browser_ref,
)
from .transaction import GovernedExternalActionKernel


GOVERNED_BROWSER_EVIDENCE_RECIPE_CONTRACT_REF = (
    "contract-ref:governed-browser-evidence-recipe:v1"
)
MAX_EVIDENCE_RECIPE_PREVIEW_CHARS = 2048
MAX_EVIDENCE_RECIPE_VISIBLE_TEXT_BYTES = 65_536
_HIGH_ENTROPY_PREVIEW_RE = re.compile(r"\b[A-Za-z0-9_/-]{32,}\b")

_CAPTURE_FIELDS = (
    "safe_title",
    "redacted_text_preview",
    "visible_text_bytes",
    "redaction_summary_ref",
)
_BROKER_ADDED_FIELDS = {
    "allowed",
    "profile_ref",
    "profile_ephemeral",
    "ordinary_profile_used",
    "external_mutation_enabled",
    "content_untrusted",
    "web_content_instruction_use_allowed",
}
_TRANSPORT_FIELDS = {
    "recipe_ref",
    "binding_ref",
    "origin_ref",
    "page_snapshot_ref",
    "target_ref",
    "safe_url_ref",
    "safe_title",
    "redacted_text_preview",
    "visible_text_bytes",
    "redaction_summary_ref",
    "raw_dom_included",
    "screenshot_included",
    "navigation_performed",
    "click_performed",
    "form_fill_performed",
    "authenticated_profile_used",
    "cookies_or_credentials_used",
    "download_or_upload_performed",
    "network_call_performed",
    "external_mutation_performed",
    "side_effects_performed",
}


class ExactBrowserObservationStatus(str, Enum):
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    observation_ready = "observation_ready"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


class GovernedBrowserEvidenceRecipe(BaseModel):
    """One registered capture schema bound to one exact authority scope."""

    schema_version: Literal["uaa-governed-browser-evidence-recipe.v1"] = (
        "uaa-governed-browser-evidence-recipe.v1"
    )
    contract_ref: Literal["contract-ref:governed-browser-evidence-recipe:v1"] = (
        GOVERNED_BROWSER_EVIDENCE_RECIPE_CONTRACT_REF
    )
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    binding_ref: str = Field(..., min_length=1, max_length=240)
    exact_origin_ref: str = Field(..., min_length=1, max_length=240)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    field_schema_ref: str = Field(..., min_length=1, max_length=240)
    target_ref: str = Field(..., min_length=1, max_length=240)
    safe_url_ref: str = Field(..., min_length=1, max_length=240)
    capture_fields: tuple[
        Literal[
            "safe_title",
            "redacted_text_preview",
            "visible_text_bytes",
            "redaction_summary_ref",
        ],
        ...,
    ] = _CAPTURE_FIELDS
    max_preview_chars: StrictInt = Field(
        default=MAX_EVIDENCE_RECIPE_PREVIEW_CHARS,
        ge=1,
        le=MAX_EVIDENCE_RECIPE_PREVIEW_CHARS,
    )
    max_visible_text_bytes: StrictInt = Field(
        default=MAX_EVIDENCE_RECIPE_VISIBLE_TEXT_BYTES,
        ge=1,
        le=MAX_EVIDENCE_RECIPE_VISIBLE_TEXT_BYTES,
    )
    local_validation_only: Literal[True] = True
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    ephemeral_private_profile_required: Literal[True] = True
    content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    raw_dom_allowed: Literal[False] = False
    screenshot_allowed: Literal[False] = False
    navigation_allowed: Literal[False] = False
    browser_action_allowed: Literal[False] = False
    authenticated_profile_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedBrowserEvidenceRecipe":
        for value, label in (
            (self.contract_ref, "contract_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.exact_origin_ref, "exact_origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.field_schema_ref, "field_schema_ref"),
            (self.target_ref, "target_ref"),
            (self.safe_url_ref, "safe_url_ref"),
        ):
            validate_task_ref(value, label)
        if not self.safe_url_ref.startswith("browser-url:"):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_SAFE_URL_REF_REQUIRED")
        if self.capture_fields != _CAPTURE_FIELDS:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_CAPTURE_FIELDS_NOT_EXACT")
        expected = stable_governed_browser_ref(
            "evidence-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "governed_browser_evidence_recipe"
        )
        return self


class EvidenceRecipeObservationTransportResult(BaseModel):
    """Strict output accepted from the injected isolated-broker transport."""

    recipe_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    target_ref: str
    safe_url_ref: str
    safe_title: str = Field(..., min_length=1, max_length=240)
    redacted_text_preview: str = Field(
        default="", max_length=MAX_EVIDENCE_RECIPE_PREVIEW_CHARS
    )
    visible_text_bytes: StrictInt = Field(
        ..., ge=0, le=MAX_EVIDENCE_RECIPE_VISIBLE_TEXT_BYTES
    )
    redaction_summary_ref: str
    raw_dom_included: Literal[False] = False
    screenshot_included: Literal[False] = False
    navigation_performed: Literal[False] = False
    click_performed: Literal[False] = False
    form_fill_performed: Literal[False] = False
    authenticated_profile_used: Literal[False] = False
    cookies_or_credentials_used: Literal[False] = False
    download_or_upload_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    side_effects_performed: tuple[()] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_transport_result(
        self,
    ) -> "EvidenceRecipeObservationTransportResult":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.target_ref, "target_ref"),
            (self.safe_url_ref, "safe_url_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
        ):
            validate_task_ref(value, label)
        validate_safe_task_text(self.safe_title, "safe_title")
        _validate_redacted_preview(self.redacted_text_preview)
        validate_safe_task_payload(
            self.model_dump(
                mode="json",
                exclude={
                    "redacted_text_preview",
                    "cookies_or_credentials_used",
                },
            ),
            "governed_browser_evidence_transport_result",
        )
        return self


class ExactBrowserObservationEvidence(BaseModel):
    """Bounded, redacted evidence returned only after exact governed checks."""

    schema_version: Literal["uaa-governed-browser-observation-evidence.v1"] = (
        "uaa-governed-browser-observation-evidence.v1"
    )
    evidence_ref: str
    recipe_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    target_ref: str
    safe_url_ref: str
    profile_ref: str
    safe_title: str
    redacted_text_preview: str
    visible_text_bytes: StrictInt
    redaction_summary_ref: str
    profile_ephemeral: Literal[True] = True
    ordinary_profile_used: Literal[False] = False
    content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    injected_observation_performed: Literal[True] = True
    live_browser_observation_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    raw_dom_included: Literal[False] = False
    screenshot_included: Literal[False] = False
    navigation_performed: Literal[False] = False
    browser_action_performed: Literal[False] = False
    authenticated_profile_used: Literal[False] = False
    live_network_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target_used: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_evidence(self) -> "ExactBrowserObservationEvidence":
        for value, label in (
            (self.evidence_ref, "evidence_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.target_ref, "target_ref"),
            (self.safe_url_ref, "safe_url_ref"),
            (self.profile_ref, "profile_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
        ):
            validate_task_ref(value, label)
        validate_safe_task_text(self.safe_title, "safe_title")
        _validate_redacted_preview(self.redacted_text_preview)
        expected = stable_governed_browser_ref(
            "evidence-ref:governed-browser-observation",
            self.model_dump(mode="json", exclude={"evidence_ref"}),
        )
        if self.evidence_ref != expected:
            raise ValueError("GOVERNED_BROWSER_OBSERVATION_EVIDENCE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"redacted_text_preview"}),
            "governed_browser_observation_evidence",
        )
        return self


class ExactBrowserObservationReceipt(BaseModel):
    """Content-free receipt for preflight denial or governed observation."""

    schema_version: Literal["uaa-governed-browser-observation-receipt.v1"] = (
        "uaa-governed-browser-observation-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: ExactBrowserObservationStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=20)
    replayed: StrictBool = False
    approval_ref_is_identifier_only: Literal[True] = True
    content_free: Literal[True] = True
    raw_content_included: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_receipt(self) -> "ExactBrowserObservationReceipt":
        for value, label in (
            (self.receipt_ref, "receipt_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
        ):
            if value is not None:
                validate_task_ref(value, label)
        for field_name in ("evidence_refs", "reason_refs"):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(
                    f"GOVERNED_BROWSER_OBSERVATION_DUPLICATE_{field_name.upper()}"
                )
            for value in values:
                validate_task_ref(value, field_name)
        if self.status == ExactBrowserObservationStatus.observation_ready.value:
            if (
                self.external_action_state != ExternalActionState.succeeded.value
                or self.replayed
                or not self.evidence_refs
                or any(
                    value is None
                    for value in (
                        self.external_action_receipt_ref,
                        self.approval_validation_ref,
                        self.authority_decision_ref,
                        self.budget_reservation_ref,
                        self.budget_settlement_ref,
                    )
                )
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE"
                )
        if self.status == ExactBrowserObservationStatus.replayed_content_free.value:
            if not self.replayed:
                raise ValueError("GOVERNED_BROWSER_OBSERVATION_REPLAY_FLAG_REQUIRED")
        status = ExactBrowserObservationStatus(self.status)
        state = ExternalActionState(self.external_action_state)
        if status != ExactBrowserObservationStatus.replayed_content_free:
            expected_states = {
                ExactBrowserObservationStatus.preflight_blocked: {
                    ExternalActionState.blocked
                },
                ExactBrowserObservationStatus.transaction_blocked: {
                    ExternalActionState.blocked
                },
                ExactBrowserObservationStatus.observation_ready: {
                    ExternalActionState.succeeded
                },
                ExactBrowserObservationStatus.failed: {
                    ExternalActionState.failed
                },
                ExactBrowserObservationStatus.outcome_ambiguous: {
                    ExternalActionState.outcome_ambiguous,
                    ExternalActionState.started,
                    ExternalActionState.prepared,
                },
            }[status]
            if state not in expected_states:
                raise ValueError(
                    "GOVERNED_BROWSER_OBSERVATION_RECEIPT_STATE_MISMATCH"
                )
            if self.replayed:
                raise ValueError(
                    "GOVERNED_BROWSER_OBSERVATION_REPLAY_STATUS_MISMATCH"
                )
        if state == ExternalActionState.succeeded and (
            any(
                ref is None
                for ref in (
                    self.external_action_receipt_ref,
                    self.approval_validation_ref,
                    self.authority_decision_ref,
                    self.budget_reservation_ref,
                    self.budget_settlement_ref,
                )
            )
            or not self.evidence_refs
        ):
            raise ValueError(
                "GOVERNED_BROWSER_OBSERVATION_SUCCESS_GOVERNANCE_INCOMPLETE"
            )
        external_kernel_proof_refs = (
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_release_ref,
            self.budget_settlement_ref,
        )
        external_proof_context_present = (
            self.external_action_receipt_ref is not None
            or any(ref is not None for ref in external_kernel_proof_refs)
            or bool(self.evidence_refs)
        )
        if (
            self.status == ExactBrowserObservationStatus.preflight_blocked.value
            and (external_proof_context_present or self.replayed)
        ):
            raise ValueError(
                "GOVERNED_BROWSER_OBSERVATION_PREFLIGHT_EXTERNAL_PROOF_DENIED"
            )
        if self.external_action_receipt_ref is None and (
            any(ref is not None for ref in external_kernel_proof_refs)
            or self.evidence_refs
        ):
            raise ValueError(
                "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_INVALID"
            )
        if (
            status != ExactBrowserObservationStatus.preflight_blocked
            and self.external_action_receipt_ref is None
        ):
            raise ValueError(
                "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_PROOF_CONTEXT_REQUIRED"
            )
        expected = stable_governed_browser_ref(
            "receipt-ref:governed-browser-observation",
            governed_receipt_identity_payload(self),
        )
        if self.receipt_ref != expected:
            raise ValueError("GOVERNED_BROWSER_OBSERVATION_RECEIPT_REF_MISMATCH")
        if self.external_action_receipt_ref is not None:
            external_reason_refs = tuple(self.reason_refs)
            if (
                self.external_action_state == ExternalActionState.failed.value
                and external_reason_refs
                == (
                    "reason-ref:governed-browser-evidence:"
                    "observation-dispatch-failed",
                )
            ):
                external_reason_refs = ()
            try:
                ExternalActionReceipt(
                    receipt_ref=self.external_action_receipt_ref,
                    transaction_ref=self.transaction_ref,
                    intent_ref=self.intent_ref,
                    binding_ref=self.binding_ref,
                    state=self.external_action_state,
                    approval_validation_ref=self.approval_validation_ref,
                    authority_decision_ref=self.authority_decision_ref,
                    budget_reservation_ref=self.budget_reservation_ref,
                    budget_release_ref=self.budget_release_ref,
                    budget_settlement_ref=self.budget_settlement_ref,
                    evidence_refs=tuple(self.evidence_refs),
                    reason_refs=external_reason_refs,
                    replayed=self.replayed,
                )
            except ValueError as exc:
                raise ValueError(
                    "GOVERNED_BROWSER_OBSERVATION_EXTERNAL_RECEIPT_REF_MISMATCH"
                ) from exc
        validate_safe_task_payload(
            self.model_dump(mode="json"), "governed_browser_observation_receipt"
        )
        return self


class ExactBrowserObservationResult(BaseModel):
    receipt: ExactBrowserObservationReceipt
    evidence: ExactBrowserObservationEvidence | None = None
    raw_gateway_result_returned: Literal[False] = False
    raw_transport_result_returned: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactBrowserObservationResult":
        if self.receipt.status == ExactBrowserObservationStatus.observation_ready.value:
            if (
                self.evidence is None
                or self.evidence.evidence_ref not in self.receipt.evidence_refs
                or self.evidence.binding_ref != self.receipt.binding_ref
                or self.evidence.recipe_ref != self.receipt.recipe_ref
            ):
                raise ValueError("GOVERNED_BROWSER_OBSERVATION_EVIDENCE_REQUIRED")
        elif self.evidence is not None:
            raise ValueError("GOVERNED_BROWSER_OBSERVATION_EVIDENCE_NOT_ALLOWED")
        return self


class ExactBrowserObservationRequest(BaseModel):
    recipe_ref: str
    execution_request: ExternalActionExecutionRequest

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactBrowserObservationRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        ExternalActionExecutionRequest.model_validate(
            self.execution_request.model_dump(mode="json")
        )
        return self


class GovernedBrowserEvidenceRecipeRegistry:
    """Immutable in-memory registry; arbitrary caller recipes are not executable."""

    def __init__(self, recipes: Sequence[GovernedBrowserEvidenceRecipe]) -> None:
        validated = [
            GovernedBrowserEvidenceRecipe.model_validate(recipe.model_dump(mode="json"))
            for recipe in recipes
        ]
        if not validated:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_RECIPE_REQUIRED")
        if len(validated) > 64:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_RECIPE_LIMIT_EXCEEDED")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_RECIPE_DUPLICATE")
        self._recipes = by_ref

    def resolve(self, recipe_ref: str) -> GovernedBrowserEvidenceRecipe | None:
        return self._recipes.get(recipe_ref)


def build_governed_browser_evidence_recipe(
    execution_request: ExternalActionExecutionRequest,
    *,
    target_ref: str,
    safe_url_ref: str,
    max_preview_chars: int = MAX_EVIDENCE_RECIPE_PREVIEW_CHARS,
    max_visible_text_bytes: int = MAX_EVIDENCE_RECIPE_VISIBLE_TEXT_BYTES,
) -> GovernedBrowserEvidenceRecipe:
    """Build one recipe whose target and safe URL are lease-bound resources."""

    request = ExternalActionExecutionRequest.model_validate(
        execution_request.model_dump(mode="json")
    )
    validate_task_ref(target_ref, "target_ref")
    validate_task_ref(safe_url_ref, "safe_url_ref")
    if request.binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_BROWSER_EVIDENCE_REAL_TARGETS_INACTIVE")
    if target_ref not in request.binding.resource_refs:
        raise ValueError("GOVERNED_BROWSER_EVIDENCE_TARGET_NOT_AUTHORITY_BOUND")
    if safe_url_ref not in request.binding.resource_refs:
        raise ValueError("GOVERNED_BROWSER_EVIDENCE_SAFE_URL_NOT_AUTHORITY_BOUND")
    payload = {
        "binding_ref": request.binding.binding_ref,
        "exact_origin_ref": request.binding.origin_ref,
        "page_snapshot_ref": request.binding.page_snapshot_ref,
        "field_schema_ref": request.binding.field_schema_ref,
        "target_ref": target_ref,
        "safe_url_ref": safe_url_ref,
        "max_preview_chars": max_preview_chars,
        "max_visible_text_bytes": max_visible_text_bytes,
    }
    provisional = GovernedBrowserEvidenceRecipe.model_construct(
        recipe_ref="evidence-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "evidence-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedBrowserEvidenceRecipe(recipe_ref=recipe_ref, **payload)


class ExactBrowserObservationService:
    """Execute one registered recipe through every existing governed boundary."""

    def __init__(
        self,
        *,
        registry: GovernedBrowserEvidenceRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        gateway: WebAccessGateway,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._gateway = gateway

    def observe(
        self, observation_request: ExactBrowserObservationRequest
    ) -> ExactBrowserObservationResult:
        request = ExactBrowserObservationRequest.model_validate(
            observation_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-evidence:recipe-unregistered",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)

        captured: dict[str, ExactBrowserObservationEvidence] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            try:
                evidence = self._observe_via_gateway(
                    recipe=recipe,
                    execution_request=dispatched_request,
                )
            except (ValidationError, ValueError, TypeError, KeyError):
                return _failed_dispatch(dispatched_request)
            captured["evidence"] = evidence
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[evidence.evidence_ref],
                verified=True,
            )

        external_receipt = self._kernel.execute(execution, dispatch=dispatch)
        evidence = captured.get("evidence")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            evidence = None
        return _result_from_external_receipt(
            request=request,
            external_receipt=external_receipt,
            evidence=evidence,
        )

    def _observe_via_gateway(
        self,
        *,
        recipe: GovernedBrowserEvidenceRecipe,
        execution_request: ExternalActionExecutionRequest,
    ) -> ExactBrowserObservationEvidence:
        result = self._gateway.execute(
            WebAccessRequest(
                kind=WebAccessRequestKind.BROWSER_OBSERVE,
                method="GET",
                authority_mode=WebAccessAuthorityMode.BROWSER_OBSERVE_ONLY,
                network_lane=WebAccessNetworkLane.BROWSER_OBSERVE_ONLY,
                actor="governed_browser_evidence_recipe",
                session_id=execution_request.intent_ref,
                metadata={
                    "recipe_ref": recipe.recipe_ref,
                    "binding_ref": recipe.binding_ref,
                    "safe_url_ref": recipe.safe_url_ref,
                    "exact_origin_ref": recipe.exact_origin_ref,
                    "page_snapshot_ref": recipe.page_snapshot_ref,
                    "target_ref": recipe.target_ref,
                    "ordinary_profile_requested": False,
                    "mutation_requested": False,
                    "request_body": False,
                    "raw_dom": False,
                    "screenshot": False,
                    "navigation": False,
                    "click": False,
                    "form_fill": False,
                    "uses_auth": False,
                    "cookies": False,
                    "download": False,
                    "upload": False,
                    "network_call": False,
                    "model_call": False,
                    "tool_execution": False,
                    "memory_write": False,
                    "context_injection": False,
                    "backend_route": False,
                    "control_center_control": False,
                    "production_authority": False,
                },
            )
        )
        if (
            result.status != WebAccessPolicyStatus.ALLOWED
            or result.audit.adapter_kind != WebAccessAdapterKind.LOCAL_BROWSER_OBSERVE
            or result.evidence_bundle is None
            or not result.content_untrusted
        ):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_GATEWAY_DENIED")
        payload = result.evidence_bundle.payload
        if not isinstance(payload, Mapping):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_PAYLOAD_INVALID")
        if set(payload) - (_TRANSPORT_FIELDS | _BROKER_ADDED_FIELDS):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_UNREGISTERED_FIELD")
        transport = EvidenceRecipeObservationTransportResult.model_validate(
            {key: payload[key] for key in _TRANSPORT_FIELDS if key in payload}
        )
        _validate_transport_binding(transport, recipe)
        if (
            payload.get("allowed") is not True
            or payload.get("profile_ephemeral") is not True
            or payload.get("ordinary_profile_used") is not False
            or payload.get("external_mutation_enabled") is not False
            or payload.get("content_untrusted") is not True
            or payload.get("web_content_instruction_use_allowed") is not False
        ):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_BROKER_POSTURE_INVALID")
        if len(transport.redacted_text_preview) > recipe.max_preview_chars:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_PREVIEW_LIMIT_EXCEEDED")
        if transport.visible_text_bytes > recipe.max_visible_text_bytes:
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_TEXT_LIMIT_EXCEEDED")
        profile_ref = payload.get("profile_ref")
        if not isinstance(profile_ref, str):
            raise ValueError("GOVERNED_BROWSER_EVIDENCE_PROFILE_REF_REQUIRED")
        evidence_payload = {
            "recipe_ref": recipe.recipe_ref,
            "binding_ref": recipe.binding_ref,
            "origin_ref": recipe.exact_origin_ref,
            "page_snapshot_ref": recipe.page_snapshot_ref,
            "target_ref": recipe.target_ref,
            "safe_url_ref": recipe.safe_url_ref,
            "profile_ref": profile_ref,
            "safe_title": transport.safe_title,
            "redacted_text_preview": transport.redacted_text_preview,
            "visible_text_bytes": transport.visible_text_bytes,
            "redaction_summary_ref": transport.redaction_summary_ref,
        }
        provisional = ExactBrowserObservationEvidence.model_construct(
            evidence_ref="evidence-ref:governed-browser-observation:pending",
            **evidence_payload,
        )
        evidence_ref = stable_governed_browser_ref(
            "evidence-ref:governed-browser-observation",
            provisional.model_dump(mode="json", exclude={"evidence_ref"}),
        )
        return ExactBrowserObservationEvidence(
            evidence_ref=evidence_ref,
            **evidence_payload,
        )


def _recipe_scope_reason(
    recipe: GovernedBrowserEvidenceRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-browser-evidence:binding-mismatch",
        ),
        (
            recipe.exact_origin_ref == binding.origin_ref,
            "reason-ref:governed-browser-evidence:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-browser-evidence:snapshot-mismatch",
        ),
        (
            recipe.field_schema_ref == binding.field_schema_ref,
            "reason-ref:governed-browser-evidence:schema-mismatch",
        ),
        (
            recipe.target_ref in binding.resource_refs,
            "reason-ref:governed-browser-evidence:target-not-authority-bound",
        ),
        (
            recipe.safe_url_ref in binding.resource_refs,
            "reason-ref:governed-browser-evidence:safe-url-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-browser-evidence:real-targets-inactive",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _validate_transport_binding(
    transport: EvidenceRecipeObservationTransportResult,
    recipe: GovernedBrowserEvidenceRecipe,
) -> None:
    values = (
        (transport.recipe_ref, recipe.recipe_ref),
        (transport.binding_ref, recipe.binding_ref),
        (transport.origin_ref, recipe.exact_origin_ref),
        (transport.page_snapshot_ref, recipe.page_snapshot_ref),
        (transport.target_ref, recipe.target_ref),
        (transport.safe_url_ref, recipe.safe_url_ref),
    )
    if any(observed != expected for observed, expected in values):
        raise ValueError("GOVERNED_BROWSER_EVIDENCE_TRANSPORT_BINDING_MISMATCH")


def _validate_redacted_preview(value: str) -> None:
    sanitized = value
    for marker in (
        "[REDACTED:SECRET_ASSIGNMENT]",
        "[REDACTED:BEARER_TOKEN]",
        "[REDACTED:PRIVATE_KEY_MARKER]",
        "[REDACTED:HIGH_ENTROPY_TOKEN]",
    ):
        sanitized = sanitized.replace(marker, "")
    if _HIGH_ENTROPY_PREVIEW_RE.search(sanitized):
        raise ValueError("GOVERNED_BROWSER_EVIDENCE_HIGH_ENTROPY_PREVIEW_DENIED")
    if sanitized.strip():
        validate_safe_task_text(sanitized, "redacted_text_preview")


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                "evidence-ref:governed-browser-observation-failed",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactBrowserObservationRequest,
    reason_ref: str,
) -> ExactBrowserObservationResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": ExactBrowserObservationStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        governed_receipt_identity_payload(
            ExactBrowserObservationReceipt.model_construct(
                receipt_ref="receipt-ref:governed-browser-observation:pending",
                **payload,
            )
        ),
    )
    return ExactBrowserObservationResult(
        receipt=ExactBrowserObservationReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactBrowserObservationRequest,
    external_receipt: ExternalActionReceipt,
    evidence: ExactBrowserObservationEvidence | None,
) -> ExactBrowserObservationResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed:
        status = ExactBrowserObservationStatus.replayed_content_free
    else:
        status = {
            ExternalActionState.succeeded: ExactBrowserObservationStatus.observation_ready,
            ExternalActionState.blocked: ExactBrowserObservationStatus.transaction_blocked,
            ExternalActionState.failed: ExactBrowserObservationStatus.failed,
            ExternalActionState.outcome_ambiguous: ExactBrowserObservationStatus.outcome_ambiguous,
            ExternalActionState.started: ExactBrowserObservationStatus.outcome_ambiguous,
            ExternalActionState.prepared: ExactBrowserObservationStatus.outcome_ambiguous,
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = [
            "reason-ref:governed-browser-evidence:observation-dispatch-failed"
        ]
    payload = {
        "recipe_ref": request.recipe_ref,
        "transaction_ref": external_receipt.transaction_ref,
        "intent_ref": external_receipt.intent_ref,
        "binding_ref": external_receipt.binding_ref,
        "status": status,
        "external_action_state": state,
        "external_action_receipt_ref": external_receipt.receipt_ref,
        "approval_validation_ref": external_receipt.approval_validation_ref,
        "authority_decision_ref": external_receipt.authority_decision_ref,
        "budget_reservation_ref": external_receipt.budget_reservation_ref,
        "budget_release_ref": external_receipt.budget_release_ref,
        "budget_settlement_ref": external_receipt.budget_settlement_ref,
        "evidence_refs": list(external_receipt.evidence_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-browser-observation",
        governed_receipt_identity_payload(
            ExactBrowserObservationReceipt.model_construct(
                receipt_ref="receipt-ref:governed-browser-observation:pending",
                **payload,
            )
        ),
    )
    return ExactBrowserObservationResult(
        receipt=ExactBrowserObservationReceipt(
            receipt_ref=receipt_ref,
            **payload,
        ),
        evidence=evidence,
    )
