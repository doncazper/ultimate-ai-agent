"""Registered same-origin visible-click and GET-form plans.

Queue 01 item 06 proves exact action contracts through deterministic injected
local validation. It does not start a browser, navigate, click, submit a form,
perform a network call, or activate a real external target.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    ValidationError,
    model_validator,
)

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
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


GOVERNED_BROWSER_ACTION_RECIPE_CONTRACT_REF = (
    "contract-ref:governed-browser-action-recipe:v1"
)
MAX_GET_FORM_FIELD_VALUE_REFS = 16

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
    "plan_ref",
    "binding_ref",
    "origin_ref",
    "page_snapshot_ref",
    "source_observation_ref",
    "source_safe_url_ref",
    "destination_origin_ref",
    "destination_safe_url_ref",
    "element_ref",
    "visibility_proof_ref",
    "field_schema_ref",
    "field_value_refs",
    "operation",
    "method",
    "target_visible",
    "same_origin_verified",
    "field_schema_verified",
    "plan_generated",
    "source_observation_content_untrusted",
    "web_content_instruction_use_allowed",
    "browser_session_started",
    "navigation_performed",
    "click_performed",
    "form_fill_performed",
    "form_submitted",
    "request_body_included",
    "authenticated_profile_used",
    "cookies_or_credentials_used",
    "download_or_upload_performed",
    "network_call_performed",
    "external_mutation_performed",
    "side_effects_performed",
}


class GovernedBrowserActionKind(str, Enum):
    visible_click = "visible_click"
    get_form = "get_form"


class ExactBrowserActionStatus(str, Enum):
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    plan_ready = "plan_ready"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


class GovernedBrowserActionRecipe(BaseModel):
    """One registered action plan bound to one exact authority scope."""

    schema_version: Literal["uaa-governed-browser-action-recipe.v1"] = (
        "uaa-governed-browser-action-recipe.v1"
    )
    contract_ref: Literal["contract-ref:governed-browser-action-recipe:v1"] = (
        GOVERNED_BROWSER_ACTION_RECIPE_CONTRACT_REF
    )
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    plan_ref: str = Field(..., min_length=1, max_length=240)
    binding_ref: str = Field(..., min_length=1, max_length=240)
    exact_origin_ref: str = Field(..., min_length=1, max_length=240)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    source_observation_ref: str = Field(..., min_length=1, max_length=240)
    source_safe_url_ref: str = Field(..., min_length=1, max_length=240)
    destination_origin_ref: str = Field(..., min_length=1, max_length=240)
    destination_safe_url_ref: str = Field(..., min_length=1, max_length=240)
    element_ref: str = Field(..., min_length=1, max_length=240)
    visibility_proof_ref: str = Field(..., min_length=1, max_length=240)
    field_schema_ref: str = Field(..., min_length=1, max_length=240)
    field_value_refs: tuple[str, ...] = Field(
        default=(), max_length=MAX_GET_FORM_FIELD_VALUE_REFS
    )
    operation: GovernedBrowserActionKind
    method: Literal["GET"] = "GET"
    exact_capability: AuthorityCapability
    local_validation_only: Literal[True] = True
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    source_observation_required: Literal[True] = True
    source_observation_content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    visible_target_required: Literal[True] = True
    same_origin_required: Literal[True] = True
    request_body_allowed: Literal[False] = False
    browser_session_allowed: Literal[False] = False
    navigation_allowed: Literal[False] = False
    action_execution_allowed: Literal[False] = False
    authenticated_profile_allowed: Literal[False] = False
    cookies_or_credentials_allowed: Literal[False] = False
    download_or_upload_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedBrowserActionRecipe":
        for value, label in (
            (self.contract_ref, "contract_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.binding_ref, "binding_ref"),
            (self.exact_origin_ref, "exact_origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_origin_ref, "destination_origin_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.field_schema_ref, "field_schema_ref"),
            *[(ref, "field_value_ref") for ref in self.field_value_refs],
        ):
            validate_task_ref(value, label)
        if not self.plan_ref.startswith("browser-action-plan:"):
            raise ValueError("GOVERNED_BROWSER_ACTION_PLAN_REF_REQUIRED")
        if not self.source_observation_ref.startswith("browser-observe-output:"):
            raise ValueError("GOVERNED_BROWSER_ACTION_OBSERVATION_REF_REQUIRED")
        if not self.source_safe_url_ref.startswith("browser-url:"):
            raise ValueError("GOVERNED_BROWSER_ACTION_SOURCE_URL_REF_REQUIRED")
        if not self.destination_safe_url_ref.startswith("browser-url:"):
            raise ValueError("GOVERNED_BROWSER_ACTION_DESTINATION_URL_REF_REQUIRED")
        if self.destination_origin_ref != self.exact_origin_ref:
            raise ValueError("GOVERNED_BROWSER_ACTION_CROSS_ORIGIN_DENIED")
        if len(set(self.field_value_refs)) != len(self.field_value_refs):
            raise ValueError("GOVERNED_BROWSER_ACTION_DUPLICATE_FIELD_VALUE_REF")
        if any(
            not ref.startswith("form-field-value-ref:") for ref in self.field_value_refs
        ):
            raise ValueError("GOVERNED_BROWSER_ACTION_OPAQUE_FIELD_VALUE_REF_REQUIRED")
        if self.operation == GovernedBrowserActionKind.visible_click.value:
            if self.exact_capability != AuthorityCapability.click.value:
                raise ValueError("GOVERNED_BROWSER_ACTION_CLICK_CAPABILITY_REQUIRED")
            if self.field_value_refs:
                raise ValueError("GOVERNED_BROWSER_ACTION_CLICK_FIELDS_DENIED")
        elif self.operation == GovernedBrowserActionKind.get_form.value:
            if self.exact_capability != AuthorityCapability.form_fill.value:
                raise ValueError("GOVERNED_BROWSER_ACTION_FORM_CAPABILITY_REQUIRED")
            if not self.field_value_refs:
                raise ValueError("GOVERNED_BROWSER_ACTION_GET_FORM_FIELDS_REQUIRED")
        expected_plan_ref = stable_governed_browser_ref(
            "browser-action-plan",
            self.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
        )
        if self.plan_ref != expected_plan_ref:
            raise ValueError("GOVERNED_BROWSER_ACTION_PLAN_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "browser-action-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_BROWSER_ACTION_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_or_credentials_allowed"}),
            "governed_browser_action_recipe",
        )
        return self


class BrowserActionDryRunTransportResult(BaseModel):
    """Strict safe-ref-only output accepted from the injected plan transport."""

    recipe_ref: str
    plan_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    source_observation_ref: str
    source_safe_url_ref: str
    destination_origin_ref: str
    destination_safe_url_ref: str
    element_ref: str
    visibility_proof_ref: str
    field_schema_ref: str
    field_value_refs: tuple[str, ...] = Field(
        default=(), max_length=MAX_GET_FORM_FIELD_VALUE_REFS
    )
    operation: GovernedBrowserActionKind
    method: Literal["GET"] = "GET"
    target_visible: Literal[True] = True
    same_origin_verified: Literal[True] = True
    field_schema_verified: Literal[True] = True
    plan_generated: Literal[True] = True
    source_observation_content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    browser_session_started: Literal[False] = False
    navigation_performed: Literal[False] = False
    click_performed: Literal[False] = False
    form_fill_performed: Literal[False] = False
    form_submitted: Literal[False] = False
    request_body_included: Literal[False] = False
    authenticated_profile_used: Literal[False] = False
    cookies_or_credentials_used: Literal[False] = False
    download_or_upload_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    side_effects_performed: tuple[()] = ()

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_transport_result(self) -> "BrowserActionDryRunTransportResult":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_origin_ref, "destination_origin_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.field_schema_ref, "field_schema_ref"),
            *[(ref, "field_value_ref") for ref in self.field_value_refs],
        ):
            validate_task_ref(value, label)
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_or_credentials_used"}),
            "governed_browser_action_transport_result",
        )
        return self


class ExactBrowserActionPlan(BaseModel):
    """Safe-ref-only plan returned after every governed check succeeds."""

    schema_version: Literal["uaa-governed-browser-action-plan.v1"] = (
        "uaa-governed-browser-action-plan.v1"
    )
    plan_ref: str
    recipe_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    source_observation_ref: str
    source_safe_url_ref: str
    destination_safe_url_ref: str
    element_ref: str
    visibility_proof_ref: str
    field_schema_ref: str
    field_value_refs: tuple[str, ...] = Field(
        default=(), max_length=MAX_GET_FORM_FIELD_VALUE_REFS
    )
    operation: GovernedBrowserActionKind
    method: Literal["GET"] = "GET"
    profile_ref: str
    target_visible: Literal[True] = True
    same_origin_verified: Literal[True] = True
    field_schema_verified: Literal[True] = True
    plan_generated: Literal[True] = True
    injected_local_validation: Literal[True] = True
    browser_session_started: Literal[False] = False
    action_execution_performed: Literal[False] = False
    live_network_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_plan(self) -> "ExactBrowserActionPlan":
        for value, label in (
            (self.plan_ref, "plan_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.field_schema_ref, "field_schema_ref"),
            (self.profile_ref, "profile_ref"),
            *[(ref, "field_value_ref") for ref in self.field_value_refs],
        ):
            validate_task_ref(value, label)
        validate_safe_task_payload(
            self.model_dump(mode="json"), "governed_browser_action_plan"
        )
        return self


class ExactBrowserActionReceipt(BaseModel):
    """Content-free receipt separate from the safe-ref-only action plan."""

    schema_version: Literal["uaa-governed-browser-action-receipt.v1"] = (
        "uaa-governed-browser-action-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: ExactBrowserActionStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    automatic_retry_allowed: Literal[False] = False
    real_external_target: Literal[False] = False
    browser_action_performed: Literal[False] = False
    network_call_performed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_receipt(self) -> "ExactBrowserActionReceipt":
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
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        if (
            self.status == ExactBrowserActionStatus.plan_ready.value
            and self.external_action_state != ExternalActionState.succeeded.value
        ):
            raise ValueError("GOVERNED_BROWSER_ACTION_READY_STATE_MISMATCH")
        if (
            self.status == ExactBrowserActionStatus.replayed_content_free.value
            and not self.replayed
        ):
            raise ValueError("GOVERNED_BROWSER_ACTION_REPLAY_FLAG_REQUIRED")
        identity_payload = governed_receipt_identity_payload(self)
        expected_receipt_refs = {
            stable_governed_browser_ref(
                prefix,
                identity_payload,
            )
            for prefix in (
                "receipt-ref:governed-browser-action",
                "receipt-ref:governed-post-form",
            )
        }
        if self.receipt_ref not in expected_receipt_refs:
            raise ValueError("GOVERNED_BROWSER_ACTION_RECEIPT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"), "governed_browser_action_receipt"
        )
        return self


class ExactBrowserActionResult(BaseModel):
    receipt: ExactBrowserActionReceipt
    plan: ExactBrowserActionPlan | None = None
    raw_gateway_result_returned: Literal[False] = False
    raw_transport_result_returned: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactBrowserActionResult":
        if not self.receipt.receipt_ref.startswith(
            "receipt-ref:governed-browser-action:"
        ):
            raise ValueError("GOVERNED_BROWSER_ACTION_RESULT_RECEIPT_KIND_MISMATCH")
        if self.receipt.status == ExactBrowserActionStatus.plan_ready.value:
            if self.plan is None:
                raise ValueError("GOVERNED_BROWSER_ACTION_PLAN_REQUIRED")
            if self.plan.recipe_ref != self.receipt.recipe_ref:
                raise ValueError("GOVERNED_BROWSER_ACTION_PLAN_RECEIPT_MISMATCH")
        elif self.plan is not None:
            raise ValueError("GOVERNED_BROWSER_ACTION_NON_SUCCESS_PLAN_DENIED")
        return self


class ExactBrowserActionRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactBrowserActionRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        return self


class GovernedBrowserActionRecipeRegistry:
    """Immutable in-memory registry; callers may select but not define recipes."""

    def __init__(self, recipes: Sequence[GovernedBrowserActionRecipe]) -> None:
        validated = tuple(
            GovernedBrowserActionRecipe.model_validate(recipe.model_dump(mode="json"))
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_BROWSER_ACTION_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_BROWSER_ACTION_RECIPE_REGISTRY_TOO_LARGE")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_BROWSER_ACTION_RECIPE_REF_DUPLICATE")
        self._recipes = by_ref

    def resolve(self, recipe_ref: str) -> GovernedBrowserActionRecipe | None:
        return self._recipes.get(recipe_ref)


def build_governed_browser_action_recipe(
    request: ExternalActionExecutionRequest,
    *,
    operation: GovernedBrowserActionKind,
    source_observation_ref: str,
    source_safe_url_ref: str,
    destination_safe_url_ref: str,
    element_ref: str,
    visibility_proof_ref: str,
    field_value_refs: Sequence[str] = (),
) -> GovernedBrowserActionRecipe:
    """Build one exact local-validation recipe from already authority-bound refs."""

    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_BROWSER_ACTION_REAL_TARGETS_INACTIVE")
    operation = GovernedBrowserActionKind(operation)
    exact_capability = {
        GovernedBrowserActionKind.visible_click: AuthorityCapability.click,
        GovernedBrowserActionKind.get_form: AuthorityCapability.form_fill,
    }[operation]
    if binding.authority_capability != exact_capability.value:
        raise ValueError("GOVERNED_BROWSER_ACTION_EXACT_CAPABILITY_MISMATCH")
    authority_bound_refs = set(binding.resource_refs)
    required_refs = {
        source_observation_ref,
        source_safe_url_ref,
        destination_safe_url_ref,
        element_ref,
        visibility_proof_ref,
        *field_value_refs,
    }
    if not required_refs.issubset(authority_bound_refs):
        raise ValueError("GOVERNED_BROWSER_ACTION_RESOURCE_NOT_AUTHORITY_BOUND")
    payload = {
        "binding_ref": binding.binding_ref,
        "exact_origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "source_observation_ref": source_observation_ref,
        "source_safe_url_ref": source_safe_url_ref,
        "destination_origin_ref": binding.origin_ref,
        "destination_safe_url_ref": destination_safe_url_ref,
        "element_ref": element_ref,
        "visibility_proof_ref": visibility_proof_ref,
        "field_schema_ref": binding.field_schema_ref,
        "field_value_refs": tuple(field_value_refs),
        "operation": operation,
        "exact_capability": exact_capability,
    }
    provisional_plan = GovernedBrowserActionRecipe.model_construct(
        recipe_ref="browser-action-recipe-ref:governed-browser:pending",
        plan_ref="browser-action-plan:pending",
        **payload,
    )
    plan_ref = stable_governed_browser_ref(
        "browser-action-plan",
        provisional_plan.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
    )
    provisional_recipe = GovernedBrowserActionRecipe.model_construct(
        recipe_ref="browser-action-recipe-ref:governed-browser:pending",
        plan_ref=plan_ref,
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "browser-action-recipe-ref:governed-browser",
        provisional_recipe.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedBrowserActionRecipe(
        recipe_ref=recipe_ref,
        plan_ref=plan_ref,
        **payload,
    )


class ExactBrowserActionService:
    """Create one governed action plan through all existing authority gates."""

    def __init__(
        self,
        *,
        registry: GovernedBrowserActionRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        gateway: WebAccessGateway,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._gateway = gateway

    def plan(
        self, action_request: ExactBrowserActionRequest
    ) -> ExactBrowserActionResult:
        request = ExactBrowserActionRequest.model_validate(
            action_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-action:recipe-unregistered",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)

        captured: dict[str, ExactBrowserActionPlan] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            try:
                plan = self._plan_via_gateway(
                    recipe=recipe,
                    execution_request=dispatched_request,
                )
            except (ValidationError, ValueError, TypeError, KeyError):
                return _failed_dispatch(dispatched_request)
            captured["plan"] = plan
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[plan.plan_ref],
                verified=True,
            )

        external_receipt = self._kernel.execute(execution, dispatch=dispatch)
        plan = captured.get("plan")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            plan = None
        return _result_from_external_receipt(
            request=request,
            external_receipt=external_receipt,
            plan=plan,
        )

    def _plan_via_gateway(
        self,
        *,
        recipe: GovernedBrowserActionRecipe,
        execution_request: ExternalActionExecutionRequest,
    ) -> ExactBrowserActionPlan:
        result = self._gateway.execute(
            WebAccessRequest(
                kind=WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
                method="GET",
                authority_mode=WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN,
                network_lane=WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN,
                actor="governed_browser_action_recipe",
                session_id=execution_request.intent_ref,
                metadata={
                    "recipe_ref": recipe.recipe_ref,
                    "plan_ref": recipe.plan_ref,
                    "binding_ref": recipe.binding_ref,
                    "safe_url_ref": recipe.source_safe_url_ref,
                    "exact_origin_ref": recipe.exact_origin_ref,
                    "page_snapshot_ref": recipe.page_snapshot_ref,
                    "source_observation_ref": recipe.source_observation_ref,
                    "source_observation_content_untrusted": True,
                    "source_safe_url_ref": recipe.source_safe_url_ref,
                    "destination_origin_ref": recipe.destination_origin_ref,
                    "destination_safe_url_ref": recipe.destination_safe_url_ref,
                    "element_ref": recipe.element_ref,
                    "visibility_proof_ref": recipe.visibility_proof_ref,
                    "field_schema_ref": recipe.field_schema_ref,
                    "field_value_refs": recipe.field_value_refs,
                    "operation": recipe.operation,
                    "ordinary_profile_requested": False,
                    "mutation_requested": False,
                    "web_content_instruction_use_allowed": False,
                    "browser_action_execution": False,
                    "browser_session_start": False,
                    "navigation_execution": False,
                    "click_execution": False,
                    "form_fill_execution": False,
                    "screenshot": False,
                    "raw_dom": False,
                    "uses_auth": False,
                    "cookies": False,
                    "download": False,
                    "upload": False,
                    "request_body": False,
                    "remote_browser": False,
                    "network_interception": False,
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
            or result.audit.adapter_kind
            != WebAccessAdapterKind.LOCAL_BROWSER_ACTION_DRY_RUN
            or result.evidence_bundle is None
            or not result.content_untrusted
        ):
            raise ValueError("GOVERNED_BROWSER_ACTION_GATEWAY_DENIED")
        payload = result.evidence_bundle.payload
        if not isinstance(payload, Mapping):
            raise ValueError("GOVERNED_BROWSER_ACTION_PAYLOAD_INVALID")
        if set(payload) - (_TRANSPORT_FIELDS | _BROKER_ADDED_FIELDS):
            raise ValueError("GOVERNED_BROWSER_ACTION_UNREGISTERED_FIELD")
        transport = BrowserActionDryRunTransportResult.model_validate(
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
            raise ValueError("GOVERNED_BROWSER_ACTION_BROKER_POSTURE_INVALID")
        profile_ref = payload.get("profile_ref")
        if not isinstance(profile_ref, str):
            raise ValueError("GOVERNED_BROWSER_ACTION_PROFILE_REF_REQUIRED")
        return ExactBrowserActionPlan(
            plan_ref=recipe.plan_ref,
            recipe_ref=recipe.recipe_ref,
            binding_ref=recipe.binding_ref,
            origin_ref=recipe.exact_origin_ref,
            page_snapshot_ref=recipe.page_snapshot_ref,
            source_observation_ref=recipe.source_observation_ref,
            source_safe_url_ref=recipe.source_safe_url_ref,
            destination_safe_url_ref=recipe.destination_safe_url_ref,
            element_ref=recipe.element_ref,
            visibility_proof_ref=recipe.visibility_proof_ref,
            field_schema_ref=recipe.field_schema_ref,
            field_value_refs=recipe.field_value_refs,
            operation=GovernedBrowserActionKind(recipe.operation),
            profile_ref=profile_ref,
        )


def _recipe_scope_reason(
    recipe: GovernedBrowserActionRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-browser-action:binding-mismatch",
        ),
        (
            recipe.exact_origin_ref == binding.origin_ref
            and recipe.destination_origin_ref == binding.origin_ref,
            "reason-ref:governed-browser-action:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-browser-action:snapshot-mismatch",
        ),
        (
            recipe.field_schema_ref == binding.field_schema_ref,
            "reason-ref:governed-browser-action:schema-mismatch",
        ),
        (
            recipe.exact_capability == binding.authority_capability,
            "reason-ref:governed-browser-action:capability-mismatch",
        ),
        (
            {
                recipe.source_observation_ref,
                recipe.source_safe_url_ref,
                recipe.destination_safe_url_ref,
                recipe.element_ref,
                recipe.visibility_proof_ref,
                *recipe.field_value_refs,
            }.issubset(set(binding.resource_refs)),
            "reason-ref:governed-browser-action:resource-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-browser-action:real-targets-inactive",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _validate_transport_binding(
    transport: BrowserActionDryRunTransportResult,
    recipe: GovernedBrowserActionRecipe,
) -> None:
    values = (
        (transport.recipe_ref, recipe.recipe_ref),
        (transport.plan_ref, recipe.plan_ref),
        (transport.binding_ref, recipe.binding_ref),
        (transport.origin_ref, recipe.exact_origin_ref),
        (transport.page_snapshot_ref, recipe.page_snapshot_ref),
        (transport.source_observation_ref, recipe.source_observation_ref),
        (transport.source_safe_url_ref, recipe.source_safe_url_ref),
        (transport.destination_origin_ref, recipe.destination_origin_ref),
        (transport.destination_safe_url_ref, recipe.destination_safe_url_ref),
        (transport.element_ref, recipe.element_ref),
        (transport.visibility_proof_ref, recipe.visibility_proof_ref),
        (transport.field_schema_ref, recipe.field_schema_ref),
        (transport.field_value_refs, recipe.field_value_refs),
        (transport.operation, recipe.operation),
    )
    if any(observed != expected for observed, expected in values):
        raise ValueError("GOVERNED_BROWSER_ACTION_TRANSPORT_BINDING_MISMATCH")


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                "evidence-ref:governed-browser-action-plan-failed",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactBrowserActionRequest,
    reason_ref: str,
) -> ExactBrowserActionResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": ExactBrowserActionStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-browser-action",
        governed_receipt_identity_payload(
            ExactBrowserActionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-browser-action:pending",
                **payload,
            )
        ),
    )
    return ExactBrowserActionResult(
        receipt=ExactBrowserActionReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactBrowserActionRequest,
    external_receipt: ExternalActionReceipt,
    plan: ExactBrowserActionPlan | None,
) -> ExactBrowserActionResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed:
        status = ExactBrowserActionStatus.replayed_content_free
    else:
        status = {
            ExternalActionState.succeeded: ExactBrowserActionStatus.plan_ready,
            ExternalActionState.blocked: ExactBrowserActionStatus.transaction_blocked,
            ExternalActionState.failed: ExactBrowserActionStatus.failed,
            ExternalActionState.outcome_ambiguous: ExactBrowserActionStatus.outcome_ambiguous,
            ExternalActionState.started: ExactBrowserActionStatus.outcome_ambiguous,
            ExternalActionState.prepared: ExactBrowserActionStatus.outcome_ambiguous,
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = ["reason-ref:governed-browser-action:plan-dispatch-failed"]
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
        "receipt-ref:governed-browser-action",
        governed_receipt_identity_payload(
            ExactBrowserActionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-browser-action:pending",
                **payload,
            )
        ),
    )
    return ExactBrowserActionResult(
        receipt=ExactBrowserActionReceipt(
            receipt_ref=receipt_ref,
            **payload,
        ),
        plan=plan,
    )
