"""Human-present MFA, passkey, and CAPTCHA handoff contracts.

This Queue 01 lane prepares one content-free handoff for a registered visible
challenge.  It never handles challenge material, invokes a passkey, solves or
bypasses a CAPTCHA, starts a browser session, or authenticates an external
target.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    stable_governed_browser_ref,
)
from .transaction import GovernedExternalActionKernel


MAX_HUMAN_CHALLENGE_HANDOFF_LIFETIME = timedelta(minutes=10)


class GovernedHumanChallengeKind(str, Enum):
    mfa = "mfa"
    passkey = "passkey"
    captcha = "captcha"


class GovernedHumanChallengeAction(str, Enum):
    complete_mfa_on_external_surface = "complete_mfa_on_external_surface"
    invoke_passkey_on_external_surface = "invoke_passkey_on_external_surface"
    complete_captcha_on_external_surface = "complete_captcha_on_external_surface"


class GovernedHumanChallengeHandoffStatus(str, Enum):
    handoff_ready = "handoff_ready"
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


def governed_human_challenge_ref(
    *,
    kind: GovernedHumanChallengeKind,
    origin_ref: str,
    page_snapshot_ref: str,
    source_observation_ref: str,
    visibility_proof_ref: str,
) -> str:
    exact_kind = GovernedHumanChallengeKind(kind)
    for value, label in (
        (origin_ref, "origin_ref"),
        (page_snapshot_ref, "page_snapshot_ref"),
        (source_observation_ref, "source_observation_ref"),
        (visibility_proof_ref, "visibility_proof_ref"),
    ):
        validate_task_ref(value, label)
    if not source_observation_ref.startswith("browser-observe-output:"):
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_OBSERVATION_REF_REQUIRED")
    if not visibility_proof_ref.startswith("visibility-proof-ref:"):
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_VISIBILITY_PROOF_REF_REQUIRED")
    return stable_governed_browser_ref(
        "human-challenge-ref:governed-browser",
        {
            "kind": exact_kind.value,
            "origin_ref": origin_ref,
            "page_snapshot_ref": page_snapshot_ref,
            "source_observation_ref": source_observation_ref,
            "visibility_proof_ref": visibility_proof_ref,
        },
    )


def governed_human_challenge_schema_ref(
    *,
    kind: GovernedHumanChallengeKind,
    challenge_ref: str,
) -> str:
    exact_kind = GovernedHumanChallengeKind(kind)
    validate_task_ref(challenge_ref, "challenge_ref")
    return stable_governed_browser_ref(
        "human-challenge-schema-ref:governed-browser",
        {"kind": exact_kind.value, "challenge_ref": challenge_ref},
    )


def governed_human_challenge_handoff_ref(
    *,
    challenge_ref: str,
    human_presence_ref: str,
    handoff_surface_ref: str,
    expires_at: datetime,
) -> str:
    for value, label in (
        (challenge_ref, "challenge_ref"),
        (human_presence_ref, "human_presence_ref"),
        (handoff_surface_ref, "handoff_surface_ref"),
    ):
        validate_task_ref(value, label)
    if not handoff_surface_ref.startswith("human-handoff-surface-ref:"):
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_HANDOFF_SURFACE_REF_REQUIRED")
    if expires_at.tzinfo is None:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_TIMEZONE_REQUIRED")
    return stable_governed_browser_ref(
        "human-challenge-handoff-ref:governed-browser",
        {
            "challenge_ref": challenge_ref,
            "human_presence_ref": human_presence_ref,
            "handoff_surface_ref": handoff_surface_ref,
            "expires_at": expires_at.isoformat(),
        },
    )


def _human_action_for_kind(
    kind: GovernedHumanChallengeKind,
) -> GovernedHumanChallengeAction:
    return {
        GovernedHumanChallengeKind.mfa: (
            GovernedHumanChallengeAction.complete_mfa_on_external_surface
        ),
        GovernedHumanChallengeKind.passkey: (
            GovernedHumanChallengeAction.invoke_passkey_on_external_surface
        ),
        GovernedHumanChallengeKind.captcha: (
            GovernedHumanChallengeAction.complete_captcha_on_external_surface
        ),
    }[GovernedHumanChallengeKind(kind)]


class GovernedHumanChallengeHandoffRecipe(BaseModel):
    """One immutable, registered, human-only challenge handoff."""

    schema_version: Literal["uaa-governed-human-challenge-handoff-recipe.v1"] = (
        "uaa-governed-human-challenge-handoff-recipe.v1"
    )
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    handoff_ref: str = Field(..., min_length=1, max_length=240)
    challenge_ref: str = Field(..., min_length=1, max_length=240)
    challenge_schema_ref: str = Field(..., min_length=1, max_length=240)
    binding_ref: str = Field(..., min_length=1, max_length=240)
    origin_ref: str = Field(..., min_length=1, max_length=240)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    source_observation_ref: str = Field(..., min_length=1, max_length=240)
    visibility_proof_ref: str = Field(..., min_length=1, max_length=240)
    human_presence_ref: str = Field(..., min_length=1, max_length=240)
    handoff_surface_ref: str = Field(..., min_length=1, max_length=240)
    challenge_kind: GovernedHumanChallengeKind
    required_human_action: GovernedHumanChallengeAction
    created_at: datetime
    expires_at: datetime
    exact_capability: Literal[AuthorityCapability.prepare] = AuthorityCapability.prepare
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    human_presence_required: Literal[True] = True
    challenge_material_allowed: Literal[False] = False
    challenge_response_allowed: Literal[False] = False
    credential_challenge_handling_allowed: Literal[False] = False
    passkey_operation_allowed: Literal[False] = False
    captcha_solving_allowed: Literal[False] = False
    captcha_bypass_allowed: Literal[False] = False
    browser_open_allowed: Literal[False] = False
    browser_session_start_allowed: Literal[False] = False
    authentication_allowed: Literal[False] = False
    navigation_allowed: Literal[False] = False
    cookies_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedHumanChallengeHandoffRecipe":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.handoff_ref, "handoff_ref"),
            (self.challenge_ref, "challenge_ref"),
            (self.challenge_schema_ref, "challenge_schema_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.human_presence_ref, "human_presence_ref"),
            (self.handoff_surface_ref, "handoff_surface_ref"),
        ):
            validate_task_ref(value, label)
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at > MAX_HUMAN_CHALLENGE_HANDOFF_LIFETIME
        ):
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_LIFETIME_INVALID")
        kind = GovernedHumanChallengeKind(self.challenge_kind)
        if self.required_human_action != _human_action_for_kind(kind).value:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_ACTION_MISMATCH")
        expected_challenge_ref = governed_human_challenge_ref(
            kind=kind,
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            source_observation_ref=self.source_observation_ref,
            visibility_proof_ref=self.visibility_proof_ref,
        )
        if self.challenge_ref != expected_challenge_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_REF_MISMATCH")
        expected_schema_ref = governed_human_challenge_schema_ref(
            kind=kind,
            challenge_ref=self.challenge_ref,
        )
        if self.challenge_schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_SCHEMA_REF_MISMATCH")
        expected_handoff_ref = governed_human_challenge_handoff_ref(
            challenge_ref=self.challenge_ref,
            human_presence_ref=self.human_presence_ref,
            handoff_surface_ref=self.handoff_surface_ref,
            expires_at=self.expires_at,
        )
        if self.handoff_ref != expected_handoff_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_HANDOFF_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "human-challenge-handoff-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_allowed"}),
            "governed_human_challenge_handoff_recipe",
        )
        return self


def build_governed_human_challenge_handoff_recipe(
    request: ExternalActionExecutionRequest,
    *,
    challenge_kind: GovernedHumanChallengeKind,
    source_observation_ref: str,
    visibility_proof_ref: str,
    handoff_surface_ref: str,
    created_at: datetime,
    expires_at: datetime,
) -> GovernedHumanChallengeHandoffRecipe:
    """Build a local-validation handoff whose exact refs are lease-bound."""

    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    kind = GovernedHumanChallengeKind(challenge_kind)
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != AuthorityCapability.prepare.value:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_EXACT_CAPABILITY_MISMATCH")
    if not binding.human_present:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_HUMAN_PRESENCE_REQUIRED")
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline or expires_at > binding.start_deadline:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_DEADLINE_EXCEEDED")
    challenge_ref = governed_human_challenge_ref(
        kind=kind,
        origin_ref=binding.origin_ref,
        page_snapshot_ref=binding.page_snapshot_ref,
        source_observation_ref=source_observation_ref,
        visibility_proof_ref=visibility_proof_ref,
    )
    challenge_schema_ref = governed_human_challenge_schema_ref(
        kind=kind,
        challenge_ref=challenge_ref,
    )
    handoff_ref = governed_human_challenge_handoff_ref(
        challenge_ref=challenge_ref,
        human_presence_ref=binding.human_presence_ref,
        handoff_surface_ref=handoff_surface_ref,
        expires_at=expires_at,
    )
    if binding.field_schema_ref != challenge_schema_ref:
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_SCHEMA_NOT_AUTHORITY_BOUND")
    required_resources = {
        challenge_ref,
        source_observation_ref,
        visibility_proof_ref,
        handoff_surface_ref,
        handoff_ref,
    }
    if not required_resources.issubset(set(binding.resource_refs)):
        raise ValueError("GOVERNED_HUMAN_CHALLENGE_RESOURCE_NOT_AUTHORITY_BOUND")
    payload = {
        "handoff_ref": handoff_ref,
        "challenge_ref": challenge_ref,
        "challenge_schema_ref": challenge_schema_ref,
        "binding_ref": binding.binding_ref,
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "source_observation_ref": source_observation_ref,
        "visibility_proof_ref": visibility_proof_ref,
        "human_presence_ref": binding.human_presence_ref,
        "handoff_surface_ref": handoff_surface_ref,
        "challenge_kind": kind,
        "required_human_action": _human_action_for_kind(kind),
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedHumanChallengeHandoffRecipe.model_construct(
        recipe_ref="human-challenge-handoff-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "human-challenge-handoff-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedHumanChallengeHandoffRecipe(recipe_ref=recipe_ref, **payload)


class GovernedHumanChallengeHandoffRecipeRegistry:
    """Immutable registry; callers can select but cannot define a handoff."""

    def __init__(
        self,
        recipes: Sequence[GovernedHumanChallengeHandoffRecipe],
    ) -> None:
        validated = tuple(
            GovernedHumanChallengeHandoffRecipe.model_validate(
                recipe.model_dump(mode="json")
            )
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_RECIPE_REGISTRY_TOO_LARGE")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_RECIPE_REF_DUPLICATE")
        self._recipes = by_ref

    def resolve(
        self,
        recipe_ref: str,
    ) -> GovernedHumanChallengeHandoffRecipe | None:
        return self._recipes.get(recipe_ref)


class ExactGovernedHumanChallengeHandoffRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedHumanChallengeHandoffRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        return self


class ExactGovernedHumanChallengeHandoff(BaseModel):
    """Content-free instruction for a present human, never an executor."""

    schema_version: Literal["uaa-governed-human-challenge-handoff.v1"] = (
        "uaa-governed-human-challenge-handoff.v1"
    )
    handoff_ref: str
    recipe_ref: str
    challenge_ref: str
    challenge_schema_ref: str
    binding_ref: str
    origin_ref: str
    page_snapshot_ref: str
    source_observation_ref: str
    visibility_proof_ref: str
    human_presence_ref: str
    handoff_surface_ref: str
    challenge_kind: GovernedHumanChallengeKind
    required_human_action: GovernedHumanChallengeAction
    expires_at: datetime
    human_present: Literal[True] = True
    human_completion_required: Literal[True] = True
    handoff_prepared: Literal[True] = True
    challenge_completed: Literal[False] = False
    challenge_material_returned: Literal[False] = False
    challenge_response_accepted: Literal[False] = False
    credential_challenge_handled: Literal[False] = False
    passkey_operation_performed: Literal[False] = False
    captcha_solve_performed: Literal[False] = False
    captcha_bypass_performed: Literal[False] = False
    browser_opened: Literal[False] = False
    browser_session_started: Literal[False] = False
    authentication_performed: Literal[False] = False
    navigation_performed: Literal[False] = False
    cookies_used: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_handoff(self) -> "ExactGovernedHumanChallengeHandoff":
        for value, label in (
            (self.handoff_ref, "handoff_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.challenge_ref, "challenge_ref"),
            (self.challenge_schema_ref, "challenge_schema_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.human_presence_ref, "human_presence_ref"),
            (self.handoff_surface_ref, "handoff_surface_ref"),
        ):
            validate_task_ref(value, label)
        if self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_TIMEZONE_REQUIRED")
        kind = GovernedHumanChallengeKind(self.challenge_kind)
        if self.required_human_action != _human_action_for_kind(kind).value:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_ACTION_MISMATCH")
        expected_challenge_ref = governed_human_challenge_ref(
            kind=kind,
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            source_observation_ref=self.source_observation_ref,
            visibility_proof_ref=self.visibility_proof_ref,
        )
        if self.challenge_ref != expected_challenge_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_REF_MISMATCH")
        expected_schema_ref = governed_human_challenge_schema_ref(
            kind=kind,
            challenge_ref=self.challenge_ref,
        )
        if self.challenge_schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_SCHEMA_REF_MISMATCH")
        expected_handoff_ref = governed_human_challenge_handoff_ref(
            challenge_ref=self.challenge_ref,
            human_presence_ref=self.human_presence_ref,
            handoff_surface_ref=self.handoff_surface_ref,
            expires_at=self.expires_at,
        )
        if self.handoff_ref != expected_handoff_ref:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_HANDOFF_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_used"}),
            "governed_human_challenge_handoff",
        )
        return self


class GovernedHumanChallengeHandoffReceipt(BaseModel):
    schema_version: Literal["uaa-governed-human-challenge-handoff-receipt.v1"] = (
        "uaa-governed-human-challenge-handoff-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: GovernedHumanChallengeHandoffStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    human_handoff_only: Literal[True] = True
    automatic_retry_allowed: Literal[False] = False
    challenge_completed: Literal[False] = False
    browser_action_performed: Literal[False] = False
    authentication_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_receipt(self) -> "GovernedHumanChallengeHandoffReceipt":
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
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        if (
            self.status == GovernedHumanChallengeHandoffStatus.handoff_ready.value
            and self.external_action_state != ExternalActionState.succeeded.value
        ):
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_READY_STATE_MISMATCH")
        if (
            self.status
            == GovernedHumanChallengeHandoffStatus.replayed_content_free.value
            and not self.replayed
        ):
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_REPLAY_FLAG_REQUIRED")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_human_challenge_handoff_receipt",
        )
        return self


class ExactGovernedHumanChallengeHandoffResult(BaseModel):
    receipt: GovernedHumanChallengeHandoffReceipt
    handoff: ExactGovernedHumanChallengeHandoff | None = None
    challenge_material_returned: Literal[False] = False
    challenge_response_returned: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactGovernedHumanChallengeHandoffResult":
        if (
            self.receipt.status
            == GovernedHumanChallengeHandoffStatus.handoff_ready.value
        ):
            if self.handoff is None:
                raise ValueError("GOVERNED_HUMAN_CHALLENGE_HANDOFF_REQUIRED")
            if self.handoff.recipe_ref != self.receipt.recipe_ref:
                raise ValueError("GOVERNED_HUMAN_CHALLENGE_RECEIPT_MISMATCH")
        elif self.handoff is not None:
            raise ValueError("GOVERNED_HUMAN_CHALLENGE_NON_SUCCESS_HANDOFF_DENIED")
        return self


class ExactGovernedHumanChallengeHandoffService:
    """Prepare one human-only challenge handoff through every shared gate."""

    def __init__(
        self,
        *,
        registry: GovernedHumanChallengeHandoffRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._clock = clock

    def prepare(
        self,
        handoff_request: ExactGovernedHumanChallengeHandoffRequest,
    ) -> ExactGovernedHumanChallengeHandoffResult:
        request = ExactGovernedHumanChallengeHandoffRequest.model_validate(
            handoff_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-human-challenge:recipe-unregistered",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)
        captured: dict[str, ExactGovernedHumanChallengeHandoff] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            current_time = self._clock()
            if (
                dispatched_request.binding.binding_ref != recipe.binding_ref
                or not recipe.created_at <= current_time < recipe.expires_at
            ):
                return _failed_dispatch(
                    dispatched_request,
                    "handoff-revalidation-failed",
                )
            handoff = ExactGovernedHumanChallengeHandoff(
                handoff_ref=recipe.handoff_ref,
                recipe_ref=recipe.recipe_ref,
                challenge_ref=recipe.challenge_ref,
                challenge_schema_ref=recipe.challenge_schema_ref,
                binding_ref=recipe.binding_ref,
                origin_ref=recipe.origin_ref,
                page_snapshot_ref=recipe.page_snapshot_ref,
                source_observation_ref=recipe.source_observation_ref,
                visibility_proof_ref=recipe.visibility_proof_ref,
                human_presence_ref=recipe.human_presence_ref,
                handoff_surface_ref=recipe.handoff_surface_ref,
                challenge_kind=recipe.challenge_kind,
                required_human_action=recipe.required_human_action,
                expires_at=recipe.expires_at,
            )
            captured["handoff"] = handoff
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[recipe.handoff_ref, recipe.challenge_ref],
                verified=True,
            )

        external_receipt = self._kernel.execute(execution, dispatch=dispatch)
        handoff = captured.get("handoff")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            handoff = None
        return _result_from_external_receipt(
            request=request,
            external_receipt=external_receipt,
            handoff=handoff,
        )


def _recipe_scope_reason(
    recipe: GovernedHumanChallengeHandoffRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    required_resources = {
        recipe.challenge_ref,
        recipe.source_observation_ref,
        recipe.visibility_proof_ref,
        recipe.handoff_surface_ref,
        recipe.handoff_ref,
    }
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-human-challenge:binding-mismatch",
        ),
        (
            recipe.origin_ref == binding.origin_ref,
            "reason-ref:governed-human-challenge:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-human-challenge:snapshot-mismatch",
        ),
        (
            recipe.challenge_schema_ref == binding.field_schema_ref,
            "reason-ref:governed-human-challenge:schema-mismatch",
        ),
        (
            recipe.human_presence_ref == binding.human_presence_ref
            and binding.human_present,
            "reason-ref:governed-human-challenge:human-presence-mismatch",
        ),
        (
            binding.authority_capability == AuthorityCapability.prepare.value,
            "reason-ref:governed-human-challenge:capability-mismatch",
        ),
        (
            required_resources.issubset(set(binding.resource_refs)),
            "reason-ref:governed-human-challenge:resource-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-human-challenge:real-targets-inactive",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
    suffix: str,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                f"evidence-ref:governed-human-challenge:{suffix}",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactGovernedHumanChallengeHandoffRequest,
    reason_ref: str,
) -> ExactGovernedHumanChallengeHandoffResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": GovernedHumanChallengeHandoffStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        GovernedHumanChallengeHandoffReceipt.model_construct(
            receipt_ref=("receipt-ref:governed-human-challenge-handoff:pending"),
            **payload,
        ).model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return ExactGovernedHumanChallengeHandoffResult(
        receipt=GovernedHumanChallengeHandoffReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactGovernedHumanChallengeHandoffRequest,
    external_receipt: ExternalActionReceipt,
    handoff: ExactGovernedHumanChallengeHandoff | None,
) -> ExactGovernedHumanChallengeHandoffResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed:
        status = GovernedHumanChallengeHandoffStatus.replayed_content_free
    else:
        status = {
            ExternalActionState.succeeded: (
                GovernedHumanChallengeHandoffStatus.handoff_ready
            ),
            ExternalActionState.blocked: (
                GovernedHumanChallengeHandoffStatus.transaction_blocked
            ),
            ExternalActionState.failed: GovernedHumanChallengeHandoffStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                GovernedHumanChallengeHandoffStatus.outcome_ambiguous
            ),
            ExternalActionState.started: (
                GovernedHumanChallengeHandoffStatus.outcome_ambiguous
            ),
            ExternalActionState.prepared: (
                GovernedHumanChallengeHandoffStatus.outcome_ambiguous
            ),
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = ["reason-ref:governed-human-challenge:handoff-preparation-failed"]
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
        "budget_settlement_ref": external_receipt.budget_settlement_ref,
        "evidence_refs": list(external_receipt.evidence_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-human-challenge-handoff",
        GovernedHumanChallengeHandoffReceipt.model_construct(
            receipt_ref=("receipt-ref:governed-human-challenge-handoff:pending"),
            **payload,
        ).model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return ExactGovernedHumanChallengeHandoffResult(
        receipt=GovernedHumanChallengeHandoffReceipt(
            receipt_ref=receipt_ref,
            **payload,
        ),
        handoff=handoff,
    )
