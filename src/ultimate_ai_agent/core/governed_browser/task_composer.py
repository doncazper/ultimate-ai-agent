"""Plan-only composition of broad intent into exact registered operations.

Queue 01 item 13 adds a deterministic local-validation boundary.  A caller
may provide only a hash-pinned broad-intent reference.  The composer can
project that reference into an ordered plan of immutable registry records, but
it cannot create a new capability, inherit authority into a step, execute a
step, call a model, open a browser, call a network, or perform an external
effect.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    ValidationInfo,
    model_validator,
)

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
from .replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    ExternalActionReplayValidationContext,
    build_external_action_replay_validation_context,
    replay_validation_context,
    require_external_action_replay_provenance,
)
from .transaction import (
    ExternalActionTransactionConflict,
    GovernedExternalActionKernel,
)


MAX_GOVERNED_TASK_COMPOSITION_LIFETIME = timedelta(minutes=10)
MAX_GOVERNED_TASK_COMPOSITION_STEPS = 8
_TASK_COMPOSER_REPLAY_LANE_REF = "lane-ref:governed-task-composer"
_HASH_PINNED_SUFFIX_RE = re.compile(r"sha256:[0-9a-f]{64}")
_HASH_PINNED_REF_RE = re.compile(r".+:sha256:[0-9a-f]{64}")


def _separator_tolerant_token_pattern(value: str) -> str:
    return r"[^a-z0-9]*".join(re.escape(character) for character in value)


_BROAD_SCOPE_TOKEN_PATTERN = "(?:" + "|".join(
    _separator_tolerant_token_pattern(value)
    for value in ("capability", "capabilities", "authority", "authorities")
) + ")"
_BROAD_QUANTITY_TOKEN_PATTERN = "(?:" + "|".join(
    _separator_tolerant_token_pattern(value) for value in ("all", "any")
) + ")"
_BROAD_SCOPE_GRANT_RE = re.compile(
    rf"(?:^|[^a-z0-9])(?:{_BROAD_SCOPE_TOKEN_PATTERN}[^a-z0-9]*"
    rf"{_BROAD_QUANTITY_TOKEN_PATTERN}|{_BROAD_QUANTITY_TOKEN_PATTERN}"
    rf"[^a-z0-9]*{_BROAD_SCOPE_TOKEN_PATTERN})(?:[^a-z0-9]|$)"
)
_BROAD_NAMED_GRANT_RE = re.compile(
    rf"(?:^|[^a-z0-9])(?:{_separator_tolerant_token_pattern('wildcard')}|"
    rf"{_separator_tolerant_token_pattern('complete')}[^a-z0-9]*"
    rf"{_separator_tolerant_token_pattern('any')}[^a-z0-9]*"
    rf"{_separator_tolerant_token_pattern('task')})(?:[^a-z0-9]|$)"
)
_REGISTERED_SOURCE_PREFIXES = {
    "source_recipe_ref": "source-recipe-ref:governed-task-composer:",
    "source_contract_ref": "source-contract-ref:governed-task-composer:",
    "source_binding_ref": "source-binding-ref:governed-task-composer:",
    "operation_authority_ref": "source-authority-ref:governed-task-composer:",
    "target_ref": "source-target-ref:governed-task-composer:",
    "schema_ref": "source-schema-ref:governed-task-composer:",
}


class GovernedTaskOperationKind(str, Enum):
    evidence_observation = "evidence_observation"
    visible_click = "visible_click"
    get_form_plan = "get_form_plan"
    post_form_plan = "post_form_plan"
    credential_lifecycle = "credential_lifecycle"
    challenge_handoff = "challenge_handoff"
    download_quarantine = "download_quarantine"
    upload_plan = "upload_plan"
    external_operation = "external_operation"
    financial_operation = "financial_operation"


_ALLOWED_CAPABILITIES = {
    GovernedTaskOperationKind.evidence_observation: {AuthorityCapability.observe},
    GovernedTaskOperationKind.visible_click: {AuthorityCapability.click},
    GovernedTaskOperationKind.get_form_plan: {AuthorityCapability.form_fill},
    GovernedTaskOperationKind.post_form_plan: {AuthorityCapability.form_fill},
    GovernedTaskOperationKind.credential_lifecycle: {AuthorityCapability.execute},
    GovernedTaskOperationKind.challenge_handoff: {AuthorityCapability.prepare},
    GovernedTaskOperationKind.download_quarantine: {AuthorityCapability.download},
    GovernedTaskOperationKind.upload_plan: {AuthorityCapability.upload},
    GovernedTaskOperationKind.external_operation: {
        AuthorityCapability.send,
        AuthorityCapability.write,
        AuthorityCapability.mutate,
        AuthorityCapability.destructive,
    },
    GovernedTaskOperationKind.financial_operation: {
        AuthorityCapability.purchase,
        AuthorityCapability.purchase_under_budget,
    },
}


class GovernedTaskCompositionStatus(str, Enum):
    plan_ready = "plan_ready"
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    proof_incomplete = "proof_incomplete"
    replayed_content_free = "replayed_content_free"


def _validate_hash_pinned_ref(
    value: str,
    *,
    label: str,
    prefix: str,
) -> None:
    validate_task_ref(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"GOVERNED_TASK_COMPOSER_{label.upper()}_REQUIRED")
    if _HASH_PINNED_SUFFIX_RE.fullmatch(value.removeprefix(prefix)) is None:
        raise ValueError("GOVERNED_TASK_COMPOSER_HASH_PIN_REQUIRED")


def _deny_broad_grant_language(value: str, *, label: str) -> None:
    lowered = value.lower()
    broad_scope_grant = _BROAD_SCOPE_GRANT_RE.search(lowered) is not None
    if (
        "*" in value
        or _BROAD_NAMED_GRANT_RE.search(lowered) is not None
        or broad_scope_grant
    ):
        raise ValueError(f"GOVERNED_TASK_COMPOSER_BROAD_{label.upper()}_DENIED")


def governed_task_broad_intent_ref(*, intent_fingerprint: str) -> str:
    """Create a content-free broad-intent ref from an already safe fingerprint."""

    _deny_broad_grant_language(intent_fingerprint, label="intent")
    _validate_hash_pinned_ref(
        intent_fingerprint,
        label="intent_fingerprint",
        prefix="intent-fingerprint-ref:governed-task-composer:",
    )
    return stable_governed_browser_ref(
        "broad-intent-ref:governed-task-composer",
        {"intent_fingerprint": intent_fingerprint},
    )


def _opaque_registered_source_ref(*, label: str, source_ref: str) -> str:
    validate_task_ref(source_ref, label)
    _deny_broad_grant_language(source_ref, label=label)
    if _HASH_PINNED_REF_RE.fullmatch(source_ref) is None:
        raise ValueError(
            f"GOVERNED_TASK_COMPOSER_{label.upper()}_HASH_PIN_REQUIRED"
        )
    return stable_governed_browser_ref(
        _REGISTERED_SOURCE_PREFIXES[label].removesuffix(":"),
        {"source_ref": source_ref},
    )


class RegisteredGovernedTaskOperation(BaseModel):
    """One immutable pointer to an already exact operation contract."""

    schema_version: Literal["uaa-governed-task-operation.v1"] = (
        "uaa-governed-task-operation.v1"
    )
    operation_ref: str
    kind: GovernedTaskOperationKind
    source_recipe_ref: str
    source_contract_ref: str
    source_binding_ref: str
    operation_authority_ref: str
    required_capability: AuthorityCapability
    target_ref: str
    schema_ref: str
    registered_exact_operation: Literal[True] = True
    later_exact_authority_required: Literal[True] = True
    composer_authority_inherited: Literal[False] = False
    operation_authorized: Literal[False] = False
    operation_executed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_operation(self) -> "RegisteredGovernedTaskOperation":
        for value, label in (
            (self.operation_ref, "operation_ref"),
            (self.source_recipe_ref, "source_recipe_ref"),
            (self.source_contract_ref, "source_contract_ref"),
            (self.source_binding_ref, "source_binding_ref"),
            (self.operation_authority_ref, "operation_authority_ref"),
            (self.target_ref, "target_ref"),
            (self.schema_ref, "schema_ref"),
        ):
            _deny_broad_grant_language(value, label=label)
            prefix = (
                "registered-operation-ref:governed-task-composer:"
                if label == "operation_ref"
                else _REGISTERED_SOURCE_PREFIXES[label]
            )
            _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        kind = GovernedTaskOperationKind(self.kind)
        capability = AuthorityCapability(self.required_capability)
        if capability not in _ALLOWED_CAPABILITIES[kind]:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_CAPABILITY_MISMATCH")
        expected = stable_governed_browser_ref(
            "registered-operation-ref:governed-task-composer",
            self.model_dump(mode="json", exclude={"operation_ref"}),
        )
        if self.operation_ref != expected:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "registered_governed_task_operation",
        )
        return self


def build_registered_governed_task_operation(
    *,
    kind: GovernedTaskOperationKind,
    source_recipe_ref: str,
    source_contract_ref: str,
    source_binding_ref: str,
    operation_authority_ref: str,
    required_capability: AuthorityCapability,
    target_ref: str,
    schema_ref: str,
) -> RegisteredGovernedTaskOperation:
    payload = {
        "kind": GovernedTaskOperationKind(kind),
        "source_recipe_ref": _opaque_registered_source_ref(
            label="source_recipe_ref",
            source_ref=source_recipe_ref,
        ),
        "source_contract_ref": _opaque_registered_source_ref(
            label="source_contract_ref",
            source_ref=source_contract_ref,
        ),
        "source_binding_ref": _opaque_registered_source_ref(
            label="source_binding_ref",
            source_ref=source_binding_ref,
        ),
        "operation_authority_ref": _opaque_registered_source_ref(
            label="operation_authority_ref",
            source_ref=operation_authority_ref,
        ),
        "required_capability": AuthorityCapability(required_capability),
        "target_ref": _opaque_registered_source_ref(
            label="target_ref",
            source_ref=target_ref,
        ),
        "schema_ref": _opaque_registered_source_ref(
            label="schema_ref",
            source_ref=schema_ref,
        ),
    }
    provisional = RegisteredGovernedTaskOperation.model_construct(
        operation_ref="registered-operation-ref:governed-task-composer:pending",
        **payload,
    )
    operation_ref = stable_governed_browser_ref(
        "registered-operation-ref:governed-task-composer",
        provisional.model_dump(mode="json", exclude={"operation_ref"}),
    )
    return RegisteredGovernedTaskOperation(operation_ref=operation_ref, **payload)


class GovernedTaskOperationRegistry:
    """Immutable registry; membership is not operation authority."""

    def __init__(self, operations: Sequence[RegisteredGovernedTaskOperation]) -> None:
        validated = tuple(
            RegisteredGovernedTaskOperation.model_validate(
                operation.model_dump(mode="json")
            )
            for operation in operations
        )
        if not validated:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REGISTRY_TOO_LARGE")
        by_ref = {operation.operation_ref: operation for operation in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REF_DUPLICATE")
        by_authority = {
            operation.operation_authority_ref: operation for operation in validated
        }
        if len(by_authority) != len(validated):
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_AUTHORITY_DUPLICATE")
        self._operations = by_ref
        self._registry_ref = stable_governed_browser_ref(
            "operation-registry-ref:governed-task-composer",
            {"operation_refs": sorted(by_ref)},
        )

    @property
    def registry_ref(self) -> str:
        return self._registry_ref

    def resolve(self, operation_ref: str) -> RegisteredGovernedTaskOperation | None:
        operation = self._operations.get(operation_ref)
        if operation is None:
            return None
        return RegisteredGovernedTaskOperation.model_validate(
            operation.model_dump(mode="json")
        )


class GovernedTaskCompositionStep(BaseModel):
    step_ref: str
    ordinal: StrictInt = Field(..., ge=1, le=MAX_GOVERNED_TASK_COMPOSITION_STEPS)
    operation_ref: str
    depends_on_step_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=4)

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_step(self) -> "GovernedTaskCompositionStep":
        for value, label in (
            (self.step_ref, "step_ref"),
            (self.operation_ref, "operation_ref"),
            *[(ref, "dependency_step_ref") for ref in self.depends_on_step_refs],
        ):
            validate_task_ref(value, label)
            _deny_broad_grant_language(value, label=label)
        if len(set(self.depends_on_step_refs)) != len(self.depends_on_step_refs):
            raise ValueError("GOVERNED_TASK_COMPOSER_DEPENDENCY_DUPLICATE")
        expected = stable_governed_browser_ref(
            "composition-step-ref:governed-task-composer",
            self.model_dump(mode="json", exclude={"step_ref"}),
        )
        if self.step_ref != expected:
            raise ValueError("GOVERNED_TASK_COMPOSER_STEP_REF_MISMATCH")
        return self


def build_governed_task_composition_step(
    *,
    ordinal: int,
    operation_ref: str,
    depends_on_step_refs: Sequence[str] = (),
) -> GovernedTaskCompositionStep:
    payload = {
        "ordinal": ordinal,
        "operation_ref": operation_ref,
        "depends_on_step_refs": tuple(depends_on_step_refs),
    }
    provisional = GovernedTaskCompositionStep.model_construct(
        step_ref="composition-step-ref:governed-task-composer:pending",
        **payload,
    )
    step_ref = stable_governed_browser_ref(
        "composition-step-ref:governed-task-composer",
        provisional.model_dump(mode="json", exclude={"step_ref"}),
    )
    return GovernedTaskCompositionStep(step_ref=step_ref, **payload)


def governed_task_composition_schema_ref(
    *,
    registry_ref: str,
    steps: Sequence[GovernedTaskCompositionStep],
) -> str:
    _validate_hash_pinned_ref(
        registry_ref,
        label="registry_ref",
        prefix="operation-registry-ref:governed-task-composer:",
    )
    return stable_governed_browser_ref(
        "composition-schema-ref:governed-task-composer",
        {
            "registry_ref": registry_ref,
            "steps": [step.model_dump(mode="json") for step in steps],
        },
    )


def governed_task_composition_plan_payload_ref(
    *,
    broad_intent_ref: str,
    registry_ref: str,
    steps: Sequence[GovernedTaskCompositionStep],
    created_at: datetime,
    expires_at: datetime,
) -> str:
    _validate_hash_pinned_ref(
        broad_intent_ref,
        label="broad_intent_ref",
        prefix="broad-intent-ref:governed-task-composer:",
    )
    _validate_hash_pinned_ref(
        registry_ref,
        label="registry_ref",
        prefix="operation-registry-ref:governed-task-composer:",
    )
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_TASK_COMPOSER_TIMEZONE_REQUIRED")
    if (
        expires_at <= created_at
        or expires_at - created_at > MAX_GOVERNED_TASK_COMPOSITION_LIFETIME
    ):
        raise ValueError("GOVERNED_TASK_COMPOSER_LIFETIME_INVALID")
    return stable_governed_browser_ref(
        "composition-plan-payload-ref:governed-task-composer",
        {
            "broad_intent_ref": broad_intent_ref,
            "registry_ref": registry_ref,
            "steps": [step.model_dump(mode="json") for step in steps],
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        },
    )


def governed_task_composer_authority_ref(
    *,
    origin_ref: str,
    page_snapshot_ref: str,
    plan_payload_ref: str,
    registry_ref: str,
) -> str:
    for value, label in (
        (origin_ref, "origin_ref"),
        (page_snapshot_ref, "page_snapshot_ref"),
    ):
        validate_task_ref(value, label)
    _validate_hash_pinned_ref(
        plan_payload_ref,
        label="plan_payload_ref",
        prefix="composition-plan-payload-ref:governed-task-composer:",
    )
    _validate_hash_pinned_ref(
        registry_ref,
        label="registry_ref",
        prefix="operation-registry-ref:governed-task-composer:",
    )
    return stable_governed_browser_ref(
        "composer-authority-ref:governed-task-composer",
        {
            "capability": AuthorityCapability.prepare.value,
            "origin_ref": origin_ref,
            "page_snapshot_ref": page_snapshot_ref,
            "plan_payload_ref": plan_payload_ref,
            "registry_ref": registry_ref,
        },
    )


def governed_task_composition_plan_ref(
    *,
    plan_payload_ref: str,
    recipe_ref: str,
    composer_authority_ref: str,
    binding_ref: str,
) -> str:
    """Bind immutable plan content to its exact registered authority envelope."""

    for value, label, prefix in (
        (
            plan_payload_ref,
            "plan_payload_ref",
            "composition-plan-payload-ref:governed-task-composer:",
        ),
        (
            recipe_ref,
            "recipe_ref",
            "composition-recipe-ref:governed-task-composer:",
        ),
        (
            composer_authority_ref,
            "composer_authority_ref",
            "composer-authority-ref:governed-task-composer:",
        ),
        (
            binding_ref,
            "binding_ref",
            "authority-binding-ref:governed-external-action:",
        ),
    ):
        _validate_hash_pinned_ref(value, label=label, prefix=prefix)
    return stable_governed_browser_ref(
        "composition-plan-ref:governed-task-composer",
        {
            "plan_payload_ref": plan_payload_ref,
            "recipe_ref": recipe_ref,
            "composer_authority_ref": composer_authority_ref,
            "binding_ref": binding_ref,
        },
    )


def governed_task_composition_envelope_ref(
    *,
    plan_ref: str,
    recipe_ref: str,
    composer_authority_ref: str,
    binding_ref: str,
) -> str:
    for value, label, prefix in (
        (
            plan_ref,
            "plan_ref",
            "composition-plan-ref:governed-task-composer:",
        ),
        (
            recipe_ref,
            "recipe_ref",
            "composition-recipe-ref:governed-task-composer:",
        ),
        (
            composer_authority_ref,
            "composer_authority_ref",
            "composer-authority-ref:governed-task-composer:",
        ),
        (
            binding_ref,
            "binding_ref",
            "authority-binding-ref:governed-external-action:",
        ),
    ):
        _validate_hash_pinned_ref(value, label=label, prefix=prefix)
    return stable_governed_browser_ref(
        "composition-envelope-ref:governed-task-composer",
        {
            "plan_ref": plan_ref,
            "recipe_ref": recipe_ref,
            "composer_authority_ref": composer_authority_ref,
            "binding_ref": binding_ref,
        },
    )


class GovernedTaskCompositionRecipe(BaseModel):
    """One registered, bounded, acyclic, plan-only composition."""

    schema_version: Literal["uaa-governed-task-composition-recipe.v1"] = (
        "uaa-governed-task-composition-recipe.v1"
    )
    recipe_ref: str
    plan_ref: str
    plan_payload_ref: str
    composer_authority_ref: str
    binding_ref: str
    transaction_ref: str
    intent_ref: str
    broad_intent_ref: str
    registry_ref: str
    schema_ref: str
    origin_ref: str
    page_snapshot_ref: str
    steps: tuple[GovernedTaskCompositionStep, ...] = Field(
        ..., min_length=1, max_length=MAX_GOVERNED_TASK_COMPOSITION_STEPS
    )
    created_at: datetime
    expires_at: datetime
    required_capability: Literal[AuthorityCapability.prepare] = (
        AuthorityCapability.prepare
    )
    registered_operations_only: Literal[True] = True
    exact_step_authority_required: Literal[True] = True
    composer_authority_applies_to_steps: Literal[False] = False
    complete_any_task_granted: Literal[False] = False
    model_call_allowed: Literal[False] = False
    automatic_execution_allowed: Literal[False] = False
    browser_action_allowed: Literal[False] = False
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
    def validate_recipe(self) -> "GovernedTaskCompositionRecipe":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.plan_payload_ref, "plan_payload_ref"),
            (self.composer_authority_ref, "composer_authority_ref"),
            (self.binding_ref, "binding_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.broad_intent_ref, "broad_intent_ref"),
            (self.registry_ref, "registry_ref"),
            (self.schema_ref, "schema_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
        ):
            validate_task_ref(value, label)
            _deny_broad_grant_language(value, label=label)
        _validate_hash_pinned_ref(
            self.broad_intent_ref,
            label="broad_intent_ref",
            prefix="broad-intent-ref:governed-task-composer:",
        )
        _validate_hash_pinned_ref(
            self.registry_ref,
            label="registry_ref",
            prefix="operation-registry-ref:governed-task-composer:",
        )
        _validate_hash_pinned_ref(
            self.transaction_ref,
            label="transaction_ref",
            prefix="transaction-ref:governed-task-composer:",
        )
        _validate_hash_pinned_ref(
            self.intent_ref,
            label="intent_ref",
            prefix="intent-ref:governed-external-action:",
        )
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_TASK_COMPOSER_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at
            > MAX_GOVERNED_TASK_COMPOSITION_LIFETIME
        ):
            raise ValueError("GOVERNED_TASK_COMPOSER_LIFETIME_INVALID")
        expected_ordinals = list(range(1, len(self.steps) + 1))
        if [step.ordinal for step in self.steps] != expected_ordinals:
            raise ValueError("GOVERNED_TASK_COMPOSER_STEP_ORDER_INVALID")
        operation_refs = [step.operation_ref for step in self.steps]
        if len(set(operation_refs)) != len(operation_refs):
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REUSE_DENIED")
        prior_step_refs: set[str] = set()
        for step in self.steps:
            if any(ref not in prior_step_refs for ref in step.depends_on_step_refs):
                raise ValueError("GOVERNED_TASK_COMPOSER_DEPENDENCY_NOT_PRIOR")
            prior_step_refs.add(step.step_ref)
        expected_schema_ref = governed_task_composition_schema_ref(
            registry_ref=self.registry_ref,
            steps=self.steps,
        )
        if self.schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_SCHEMA_REF_MISMATCH")
        expected_plan_payload_ref = governed_task_composition_plan_payload_ref(
            broad_intent_ref=self.broad_intent_ref,
            registry_ref=self.registry_ref,
            steps=self.steps,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )
        if self.plan_payload_ref != expected_plan_payload_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_PAYLOAD_REF_MISMATCH")
        expected_authority_ref = governed_task_composer_authority_ref(
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            plan_payload_ref=self.plan_payload_ref,
            registry_ref=self.registry_ref,
        )
        if self.composer_authority_ref != expected_authority_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_AUTHORITY_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "composition-recipe-ref:governed-task-composer",
            self.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECIPE_REF_MISMATCH")
        expected_plan_ref = governed_task_composition_plan_ref(
            plan_payload_ref=self.plan_payload_ref,
            recipe_ref=self.recipe_ref,
            composer_authority_ref=self.composer_authority_ref,
            binding_ref=self.binding_ref,
        )
        if self.plan_ref != expected_plan_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_task_composition_recipe",
        )
        return self


def build_governed_task_composition_recipe(
    request: ExternalActionExecutionRequest,
    *,
    broad_intent_ref: str,
    registry: GovernedTaskOperationRegistry,
    steps: Sequence[GovernedTaskCompositionStep],
    created_at: datetime,
    expires_at: datetime,
) -> GovernedTaskCompositionRecipe:
    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    exact_steps = [
        GovernedTaskCompositionStep.model_validate(step.model_dump(mode="json"))
        for step in steps
    ]
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_TASK_COMPOSER_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != AuthorityCapability.prepare.value:
        raise ValueError("GOVERNED_TASK_COMPOSER_PREPARE_CAPABILITY_REQUIRED")
    if not binding.human_present:
        raise ValueError("GOVERNED_TASK_COMPOSER_HUMAN_PRESENCE_REQUIRED")
    _validate_hash_pinned_ref(
        binding.transaction_ref,
        label="transaction_ref",
        prefix="transaction-ref:governed-task-composer:",
    )
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_TASK_COMPOSER_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline or expires_at > binding.start_deadline:
        raise ValueError("GOVERNED_TASK_COMPOSER_DEADLINE_EXCEEDED")
    for step in exact_steps:
        if registry.resolve(step.operation_ref) is None:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_UNREGISTERED")
    registry_ref = registry.registry_ref
    schema_ref = governed_task_composition_schema_ref(
        registry_ref=registry_ref,
        steps=exact_steps,
    )
    plan_payload_ref = governed_task_composition_plan_payload_ref(
        broad_intent_ref=broad_intent_ref,
        registry_ref=registry_ref,
        steps=exact_steps,
        created_at=created_at,
        expires_at=expires_at,
    )
    composer_authority_ref = governed_task_composer_authority_ref(
        origin_ref=binding.origin_ref,
        page_snapshot_ref=binding.page_snapshot_ref,
        plan_payload_ref=plan_payload_ref,
        registry_ref=registry_ref,
    )
    operation_refs = [step.operation_ref for step in exact_steps]
    required_resources = {
        broad_intent_ref,
        registry_ref,
        plan_payload_ref,
        composer_authority_ref,
    }
    if binding.recipient_ref != plan_payload_ref:
        raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_NOT_AUTHORITY_BOUND")
    if binding.field_schema_ref != schema_ref:
        raise ValueError("GOVERNED_TASK_COMPOSER_SCHEMA_NOT_AUTHORITY_BOUND")
    if binding.artifact_refs != tuple(operation_refs):
        raise ValueError("GOVERNED_TASK_COMPOSER_OPERATIONS_NOT_EXACTLY_BOUND")
    if set(binding.resource_refs) != required_resources:
        raise ValueError("GOVERNED_TASK_COMPOSER_RESOURCE_NOT_EXACTLY_BOUND")
    payload = {
        "plan_payload_ref": plan_payload_ref,
        "composer_authority_ref": composer_authority_ref,
        "binding_ref": binding.binding_ref,
        "transaction_ref": binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "broad_intent_ref": broad_intent_ref,
        "registry_ref": registry_ref,
        "schema_ref": schema_ref,
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "steps": tuple(exact_steps),
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedTaskCompositionRecipe.model_construct(
        recipe_ref="composition-recipe-ref:governed-task-composer:pending",
        plan_ref="composition-plan-ref:governed-task-composer:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "composition-recipe-ref:governed-task-composer",
        provisional.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
    )
    plan_ref = governed_task_composition_plan_ref(
        plan_payload_ref=plan_payload_ref,
        recipe_ref=recipe_ref,
        composer_authority_ref=composer_authority_ref,
        binding_ref=binding.binding_ref,
    )
    return GovernedTaskCompositionRecipe(
        recipe_ref=recipe_ref,
        plan_ref=plan_ref,
        **payload,
    )


class GovernedTaskCompositionRecipeRegistry:
    """Immutable recipe registry with no dynamic decomposition behavior."""

    def __init__(self, recipes: Sequence[GovernedTaskCompositionRecipe]) -> None:
        validated = tuple(
            GovernedTaskCompositionRecipe.model_validate(recipe.model_dump(mode="json"))
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECIPE_REGISTRY_TOO_LARGE")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_TASK_COMPOSER_RECIPE_REF_DUPLICATE")
        by_plan = {recipe.plan_ref: recipe for recipe in validated}
        if len(by_plan) != len(validated):
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_REF_DUPLICATE")
        self._recipes = by_ref

    def resolve(self, recipe_ref: str) -> GovernedTaskCompositionRecipe | None:
        recipe = self._recipes.get(recipe_ref)
        if recipe is None:
            return None
        return GovernedTaskCompositionRecipe.model_validate(
            recipe.model_dump(mode="json")
        )


class ExactGovernedTaskCompositionRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str
    plan_ref: str
    broad_intent_ref: str
    registry_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedTaskCompositionRequest":
        for value, label, prefix in (
            (
                self.recipe_ref,
                "recipe_ref",
                "composition-recipe-ref:governed-task-composer:",
            ),
            (
                self.plan_ref,
                "plan_ref",
                "composition-plan-ref:governed-task-composer:",
            ),
            (
                self.broad_intent_ref,
                "broad_intent_ref",
                "broad-intent-ref:governed-task-composer:",
            ),
            (
                self.registry_ref,
                "registry_ref",
                "operation-registry-ref:governed-task-composer:",
            ),
        ):
            _deny_broad_grant_language(value, label=label)
            _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        _validate_hash_pinned_ref(
            self.execution_request.binding.transaction_ref,
            label="transaction_ref",
            prefix="transaction-ref:governed-task-composer:",
        )
        return self


class GovernedTaskCompositionPlanStep(BaseModel):
    step_ref: str
    ordinal: StrictInt = Field(..., ge=1, le=MAX_GOVERNED_TASK_COMPOSITION_STEPS)
    operation_ref: str
    kind: GovernedTaskOperationKind
    source_recipe_ref: str
    source_contract_ref: str
    source_binding_ref: str
    operation_authority_ref: str
    required_capability: AuthorityCapability
    target_ref: str
    schema_ref: str
    depends_on_step_refs: tuple[str, ...] = Field(..., max_length=4)
    exact_operation_authority_required: Literal[True] = True
    composer_authority_inherited: Literal[False] = False
    operation_authorized: Literal[False] = False
    operation_executed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_plan_step(self) -> "GovernedTaskCompositionPlanStep":
        for value, label in (
            (self.step_ref, "step_ref"),
            (self.operation_ref, "operation_ref"),
            (self.source_recipe_ref, "source_recipe_ref"),
            (self.source_contract_ref, "source_contract_ref"),
            (self.source_binding_ref, "source_binding_ref"),
            (self.operation_authority_ref, "operation_authority_ref"),
            (self.target_ref, "target_ref"),
            (self.schema_ref, "schema_ref"),
            *[(ref, "dependency_step_ref") for ref in self.depends_on_step_refs],
        ):
            validate_task_ref(value, label)
            _deny_broad_grant_language(value, label=label)
        registered = RegisteredGovernedTaskOperation(
            operation_ref=self.operation_ref,
            kind=self.kind,
            source_recipe_ref=self.source_recipe_ref,
            source_contract_ref=self.source_contract_ref,
            source_binding_ref=self.source_binding_ref,
            operation_authority_ref=self.operation_authority_ref,
            required_capability=self.required_capability,
            target_ref=self.target_ref,
            schema_ref=self.schema_ref,
        )
        expected_step_ref = build_governed_task_composition_step(
            ordinal=self.ordinal,
            operation_ref=registered.operation_ref,
            depends_on_step_refs=self.depends_on_step_refs,
        ).step_ref
        if self.step_ref != expected_step_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_STEP_REF_MISMATCH")
        return self


class GovernedTaskCompositionPlan(BaseModel):
    schema_version: Literal["uaa-governed-task-composition-plan.v1"] = (
        "uaa-governed-task-composition-plan.v1"
    )
    plan_ref: str
    plan_payload_ref: str
    recipe_ref: str
    recipe_snapshot: GovernedTaskCompositionRecipe
    broad_intent_ref: str
    registry_ref: str
    composer_authority_ref: str
    binding_ref: str
    envelope_ref: str
    steps: tuple[GovernedTaskCompositionPlanStep, ...] = Field(
        ..., min_length=1, max_length=MAX_GOVERNED_TASK_COMPOSITION_STEPS
    )
    created_at: datetime
    expires_at: datetime
    plan_prepared: Literal[True] = True
    registered_operations_only: Literal[True] = True
    exact_step_authority_required: Literal[True] = True
    composer_authority_applies_to_steps: Literal[False] = False
    complete_any_task_granted: Literal[False] = False
    raw_intent_recorded: Literal[False] = False
    model_call_performed: Literal[False] = False
    browser_action_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    automatic_execution_performed: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_plan(self) -> "GovernedTaskCompositionPlan":
        for value, label in (
            (self.plan_ref, "plan_ref"),
            (self.plan_payload_ref, "plan_payload_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.broad_intent_ref, "broad_intent_ref"),
            (self.registry_ref, "registry_ref"),
            (self.composer_authority_ref, "composer_authority_ref"),
            (self.binding_ref, "binding_ref"),
            (self.envelope_ref, "envelope_ref"),
        ):
            validate_task_ref(value, label)
            _deny_broad_grant_language(value, label=label)
        _validate_hash_pinned_ref(
            self.broad_intent_ref,
            label="broad_intent_ref",
            prefix="broad-intent-ref:governed-task-composer:",
        )
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_TASK_COMPOSER_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at
            > MAX_GOVERNED_TASK_COMPOSITION_LIFETIME
        ):
            raise ValueError("GOVERNED_TASK_COMPOSER_LIFETIME_INVALID")
        expected_ordinals = list(range(1, len(self.steps) + 1))
        if [step.ordinal for step in self.steps] != expected_ordinals:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_ORDER_INVALID")
        operation_refs = [step.operation_ref for step in self.steps]
        if len(set(operation_refs)) != len(operation_refs):
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_REUSE_DENIED")
        operation_authority_refs = [
            step.operation_authority_ref for step in self.steps
        ]
        if len(set(operation_authority_refs)) != len(operation_authority_refs):
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_AUTHORITY_DUPLICATE")
        composition_steps = [
            GovernedTaskCompositionStep(
                step_ref=step.step_ref,
                ordinal=step.ordinal,
                operation_ref=step.operation_ref,
                depends_on_step_refs=step.depends_on_step_refs,
            )
            for step in self.steps
        ]
        prior_step_refs: set[str] = set()
        for step in composition_steps:
            if any(ref not in prior_step_refs for ref in step.depends_on_step_refs):
                raise ValueError("GOVERNED_TASK_COMPOSER_DEPENDENCY_NOT_PRIOR")
            prior_step_refs.add(step.step_ref)
        expected_plan_payload_ref = governed_task_composition_plan_payload_ref(
            broad_intent_ref=self.broad_intent_ref,
            registry_ref=self.registry_ref,
            steps=composition_steps,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )
        if self.plan_payload_ref != expected_plan_payload_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_PAYLOAD_REF_MISMATCH")
        expected_plan_ref = governed_task_composition_plan_ref(
            plan_payload_ref=self.plan_payload_ref,
            recipe_ref=self.recipe_ref,
            composer_authority_ref=self.composer_authority_ref,
            binding_ref=self.binding_ref,
        )
        if self.plan_ref != expected_plan_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_REF_MISMATCH")
        expected_envelope_ref = governed_task_composition_envelope_ref(
            plan_ref=self.plan_ref,
            recipe_ref=self.recipe_ref,
            composer_authority_ref=self.composer_authority_ref,
            binding_ref=self.binding_ref,
        )
        if self.envelope_ref != expected_envelope_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_ENVELOPE_REF_MISMATCH")
        if (
            self.recipe_snapshot.recipe_ref != self.recipe_ref
            or self.recipe_snapshot.plan_ref != self.plan_ref
            or self.recipe_snapshot.plan_payload_ref != self.plan_payload_ref
            or self.recipe_snapshot.broad_intent_ref != self.broad_intent_ref
            or self.recipe_snapshot.registry_ref != self.registry_ref
            or self.recipe_snapshot.composer_authority_ref
            != self.composer_authority_ref
            or self.recipe_snapshot.binding_ref != self.binding_ref
            or self.recipe_snapshot.created_at != self.created_at
            or self.recipe_snapshot.expires_at != self.expires_at
            or self.recipe_snapshot.steps != tuple(composition_steps)
        ):
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_RECIPE_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_task_composition_plan",
        )
        return self


def _external_receipt_snapshot_identity_payload(snapshot: BaseModel) -> dict[str, Any]:
    payload = snapshot.model_dump(mode="json", exclude={"snapshot_ref"})
    if payload.get("budget_release_ref") is None:
        payload.pop("budget_release_ref", None)
    return payload


def _task_composition_receipt_identity_payload(
    receipt: BaseModel,
) -> dict[str, Any]:
    payload = receipt.model_dump(mode="json", exclude={"receipt_ref"})
    if payload.get("budget_release_ref") is None:
        payload.pop("budget_release_ref", None)
    external_snapshot = payload.get("external_receipt_snapshot")
    if (
        isinstance(external_snapshot, dict)
        and external_snapshot.get("budget_release_ref") is None
    ):
        external_snapshot.pop("budget_release_ref", None)
    return payload


class GovernedTaskCompositionExternalReceiptSnapshot(BaseModel):
    """Immutable content-free copy of one exact kernel receipt and proof chain."""

    schema_version: Literal[
        "uaa-governed-task-composition-external-receipt-snapshot.v1"
    ] = "uaa-governed-task-composition-external-receipt-snapshot.v1"
    snapshot_ref: str
    external_action_receipt_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    state: ExternalActionState
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_snapshot(
        self,
        info: ValidationInfo,
    ) -> "GovernedTaskCompositionExternalReceiptSnapshot":
        for value, label in (
            (self.snapshot_ref, "external_receipt_snapshot_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "external_action_reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
                _deny_broad_grant_language(value, label=label)
        for value, label, prefix in (
            (
                self.snapshot_ref,
                "external_receipt_snapshot_ref",
                "external-receipt-snapshot-ref:governed-task-composer:",
            ),
            (
                self.external_action_receipt_ref,
                "external_action_receipt_ref",
                "receipt-ref:governed-external-action:",
            ),
            (
                self.transaction_ref,
                "transaction_ref",
                "transaction-ref:governed-task-composer:",
            ),
            (
                self.intent_ref,
                "intent_ref",
                "intent-ref:governed-external-action:",
            ),
            (
                self.binding_ref,
                "binding_ref",
                "authority-binding-ref:governed-external-action:",
            ),
        ):
            _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        for value, label, prefix in (
            (
                self.approval_validation_ref,
                "approval_validation_ref",
                "approval-validation-ref:governed-external-action:",
            ),
            (
                self.budget_reservation_ref,
                "budget_reservation_ref",
                "authority-budget-reservation-ref:",
            ),
            (
                self.budget_release_ref,
                "budget_release_ref",
                "receipt-ref:authority-budget:",
            ),
            (
                self.budget_settlement_ref,
                "budget_settlement_ref",
                "receipt-ref:authority-budget:",
            ),
        ):
            if value is not None:
                _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        if self.authority_decision_ref is not None and (
            re.fullmatch(
                r"authority-policy-decision-ref:sha256:[0-9a-f]{24}",
                self.authority_decision_ref,
            )
            is None
        ):
            raise ValueError(
                "GOVERNED_TASK_COMPOSER_AUTHORITY_DECISION_REF_REQUIRED"
            )
        try:
            external_candidate = ExternalActionReceipt(
                receipt_ref=self.external_action_receipt_ref,
                transaction_ref=self.transaction_ref,
                intent_ref=self.intent_ref,
                binding_ref=self.binding_ref,
                state=self.state,
                approval_validation_ref=self.approval_validation_ref,
                authority_decision_ref=self.authority_decision_ref,
                budget_reservation_ref=self.budget_reservation_ref,
                budget_release_ref=self.budget_release_ref,
                budget_settlement_ref=self.budget_settlement_ref,
                evidence_refs=self.evidence_refs,
                reason_refs=self.reason_refs,
                replayed=self.replayed,
            )
        except ValueError as exc:
            raise ValueError(
                "GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_REF_MISMATCH"
            ) from exc
        if self.replayed:
            require_external_action_replay_provenance(
                info,
                lane_ref=_TASK_COMPOSER_REPLAY_LANE_REF,
                operation_ref=self.binding_ref,
                candidate=external_candidate,
            )
        expected_snapshot_ref = stable_governed_browser_ref(
            "external-receipt-snapshot-ref:governed-task-composer",
            _external_receipt_snapshot_identity_payload(self),
        )
        if self.snapshot_ref != expected_snapshot_ref:
            raise ValueError(
                "GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_SNAPSHOT_REF_MISMATCH"
            )
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_task_composition_external_receipt_snapshot",
        )
        return self


def _build_external_receipt_snapshot(
    receipt: ExternalActionReceipt,
    *,
    validation_context: ExternalActionReplayValidationContext | None = None,
) -> GovernedTaskCompositionExternalReceiptSnapshot:
    payload = {
        "external_action_receipt_ref": receipt.receipt_ref,
        "transaction_ref": receipt.transaction_ref,
        "intent_ref": receipt.intent_ref,
        "binding_ref": receipt.binding_ref,
        "state": receipt.state,
        "approval_validation_ref": receipt.approval_validation_ref,
        "authority_decision_ref": receipt.authority_decision_ref,
        "budget_reservation_ref": receipt.budget_reservation_ref,
        "budget_release_ref": receipt.budget_release_ref,
        "budget_settlement_ref": receipt.budget_settlement_ref,
        "evidence_refs": tuple(receipt.evidence_refs),
        "reason_refs": tuple(receipt.reason_refs),
        "replayed": receipt.replayed,
    }
    snapshot_ref = stable_governed_browser_ref(
        "external-receipt-snapshot-ref:governed-task-composer",
        _external_receipt_snapshot_identity_payload(
            GovernedTaskCompositionExternalReceiptSnapshot.model_construct(
                snapshot_ref=(
                    "external-receipt-snapshot-ref:governed-task-composer:pending"
                ),
                **payload,
            )
        ),
    )
    snapshot_payload = {
        "snapshot_ref": snapshot_ref,
        **payload,
    }
    return (
        GovernedTaskCompositionExternalReceiptSnapshot.model_validate(
            snapshot_payload,
            context=replay_validation_context(validation_context),
        )
        if validation_context is not None
        else GovernedTaskCompositionExternalReceiptSnapshot(**snapshot_payload)
    )


class GovernedTaskCompositionReceipt(BaseModel):
    schema_version: Literal["uaa-governed-task-composition-receipt.v1"] = (
        "uaa-governed-task-composition-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    plan_ref: str
    broad_intent_ref: str
    registry_ref: str
    recipe_snapshot: GovernedTaskCompositionRecipe | None = None
    external_receipt_snapshot: (
        GovernedTaskCompositionExternalReceiptSnapshot | None
    ) = None
    composer_authority_ref: str | None = None
    envelope_ref: str | None = None
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: GovernedTaskCompositionStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    operation_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=8)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    external_action_reason_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=16,
    )
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    plan_only: Literal[True] = True
    raw_intent_recorded: Literal[False] = False
    composer_authority_applies_to_steps: Literal[False] = False
    complete_any_task_granted: Literal[False] = False
    model_call_performed: Literal[False] = False
    browser_action_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    automatic_execution_performed: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_receipt(
        self,
        info: ValidationInfo,
    ) -> "GovernedTaskCompositionReceipt":
        for value, label in (
            (self.receipt_ref, "receipt_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.broad_intent_ref, "broad_intent_ref"),
            (self.registry_ref, "registry_ref"),
            (self.composer_authority_ref, "composer_authority_ref"),
            (self.envelope_ref, "envelope_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[(ref, "operation_ref") for ref in self.operation_refs],
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[
                (ref, "external_action_reason_ref")
                for ref in self.external_action_reason_refs
            ],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
                _deny_broad_grant_language(value, label=label)
        _validate_hash_pinned_ref(
            self.broad_intent_ref,
            label="broad_intent_ref",
            prefix="broad-intent-ref:governed-task-composer:",
        )
        _validate_hash_pinned_ref(
            self.registry_ref,
            label="registry_ref",
            prefix="operation-registry-ref:governed-task-composer:",
        )
        _validate_hash_pinned_ref(
            self.intent_ref,
            label="intent_ref",
            prefix="intent-ref:governed-external-action:",
        )
        for value, label, prefix in (
            (
                self.recipe_ref,
                "recipe_ref",
                "composition-recipe-ref:governed-task-composer:",
            ),
            (
                self.plan_ref,
                "plan_ref",
                "composition-plan-ref:governed-task-composer:",
            ),
            (
                self.transaction_ref,
                "transaction_ref",
                "transaction-ref:governed-task-composer:",
            ),
            (
                self.binding_ref,
                "binding_ref",
                "authority-binding-ref:governed-external-action:",
            ),
        ):
            _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        for value, label, prefix in (
            (
                self.composer_authority_ref,
                "composer_authority_ref",
                "composer-authority-ref:governed-task-composer:",
            ),
            (
                self.envelope_ref,
                "envelope_ref",
                "composition-envelope-ref:governed-task-composer:",
            ),
        ):
            if value is not None:
                _validate_hash_pinned_ref(value, label=label, prefix=prefix)
        for operation_ref in self.operation_refs:
            _validate_hash_pinned_ref(
                operation_ref,
                label="operation_ref",
                prefix="registered-operation-ref:governed-task-composer:",
            )
        status = GovernedTaskCompositionStatus(self.status)
        state = ExternalActionState(self.external_action_state)
        expected_states = {
            GovernedTaskCompositionStatus.plan_ready: {
                ExternalActionState.succeeded
            },
            GovernedTaskCompositionStatus.preflight_blocked: {
                ExternalActionState.blocked
            },
            GovernedTaskCompositionStatus.transaction_blocked: {
                ExternalActionState.blocked
            },
            GovernedTaskCompositionStatus.failed: {ExternalActionState.failed},
            GovernedTaskCompositionStatus.outcome_ambiguous: {
                ExternalActionState.outcome_ambiguous,
                ExternalActionState.started,
                ExternalActionState.prepared,
            },
            GovernedTaskCompositionStatus.proof_incomplete: {
                ExternalActionState.succeeded
            },
            GovernedTaskCompositionStatus.replayed_content_free: {
                ExternalActionState.succeeded
            },
        }[status]
        if state not in expected_states:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECEIPT_STATE_MISMATCH")
        successful_statuses = {
            GovernedTaskCompositionStatus.plan_ready,
            GovernedTaskCompositionStatus.replayed_content_free,
        }
        success_kernel_proof_refs = (
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_settlement_ref,
        )
        expected_success_evidence = (
            self.recipe_ref,
            self.plan_ref,
            self.registry_ref,
            self.composer_authority_ref,
            *self.operation_refs,
        )
        external_kernel_proof_refs = (
            *success_kernel_proof_refs,
            self.budget_release_ref,
        )
        if status == GovernedTaskCompositionStatus.plan_ready and self.replayed:
            raise ValueError("GOVERNED_TASK_COMPOSER_READY_STATE_MISMATCH")
        external_projection_required = (
            status != GovernedTaskCompositionStatus.preflight_blocked
        )
        if self.external_action_receipt_ref is None:
            if external_projection_required:
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_PROOF_CONTEXT_REQUIRED"
                )
            if (
                self.recipe_snapshot is not None
                or self.external_receipt_snapshot is not None
                or self.composer_authority_ref is not None
                or self.envelope_ref is not None
                or any(ref is not None for ref in external_kernel_proof_refs)
                or self.operation_refs
                or self.evidence_refs
                or self.external_action_reason_refs
                or self.replayed
            ):
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_PROOF_CONTEXT_INVALID"
                )
        else:
            if not external_projection_required:
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_PROOF_CONTEXT_INVALID"
                )
            if (
                self.recipe_snapshot is None
                or self.external_receipt_snapshot is None
                or self.composer_authority_ref is None
                or self.envelope_ref is None
                or not self.operation_refs
            ):
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_PROOF_CONTEXT_REQUIRED"
                )
            assert self.recipe_snapshot is not None
            assert self.external_receipt_snapshot is not None
            assert self.composer_authority_ref is not None
            assert self.envelope_ref is not None
            snapshot = self.recipe_snapshot
            if (
                snapshot.recipe_ref != self.recipe_ref
                or snapshot.plan_ref != self.plan_ref
                or snapshot.broad_intent_ref != self.broad_intent_ref
                or snapshot.registry_ref != self.registry_ref
                or snapshot.composer_authority_ref != self.composer_authority_ref
                or snapshot.binding_ref != self.binding_ref
                or snapshot.transaction_ref != self.transaction_ref
                or snapshot.intent_ref != self.intent_ref
            ):
                raise ValueError("GOVERNED_TASK_COMPOSER_RECIPE_SNAPSHOT_MISMATCH")
            expected_operation_refs = tuple(
                step.operation_ref for step in snapshot.steps
            )
            if self.operation_refs != expected_operation_refs:
                raise ValueError("GOVERNED_TASK_COMPOSER_RECEIPT_SCOPE_MISMATCH")
            for value, label, prefix in (
                (
                    self.external_action_receipt_ref,
                    "external_action_receipt_ref",
                    "receipt-ref:governed-external-action:",
                ),
                (
                    self.approval_validation_ref,
                    "approval_validation_ref",
                    "approval-validation-ref:governed-external-action:",
                ),
                (
                    self.budget_reservation_ref,
                    "budget_reservation_ref",
                    "authority-budget-reservation-ref:",
                ),
                (
                    self.budget_release_ref,
                    "budget_release_ref",
                    "receipt-ref:authority-budget:",
                ),
                (
                    self.budget_settlement_ref,
                    "budget_settlement_ref",
                    "receipt-ref:authority-budget:",
                ),
            ):
                if value is not None:
                    _validate_hash_pinned_ref(value, label=label, prefix=prefix)
            if self.authority_decision_ref is not None and (
                re.fullmatch(
                    r"authority-policy-decision-ref:sha256:[0-9a-f]{24}",
                    self.authority_decision_ref,
                )
                is None
            ):
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_AUTHORITY_DECISION_REF_REQUIRED"
                )
            try:
                external_candidate = ExternalActionReceipt(
                    receipt_ref=self.external_action_receipt_ref,
                    transaction_ref=self.transaction_ref,
                    intent_ref=self.intent_ref,
                    binding_ref=self.binding_ref,
                    state=state,
                    approval_validation_ref=self.approval_validation_ref,
                    authority_decision_ref=self.authority_decision_ref,
                    budget_reservation_ref=self.budget_reservation_ref,
                    budget_release_ref=self.budget_release_ref,
                    budget_settlement_ref=self.budget_settlement_ref,
                    evidence_refs=self.evidence_refs,
                    reason_refs=self.external_action_reason_refs,
                    replayed=self.replayed,
                )
            except ValueError as exc:
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_REF_MISMATCH"
                ) from exc
            if self.replayed:
                require_external_action_replay_provenance(
                    info,
                    lane_ref=_TASK_COMPOSER_REPLAY_LANE_REF,
                    operation_ref=self.binding_ref,
                    candidate=external_candidate,
                )
            external_snapshot = self.external_receipt_snapshot
            if (
                external_snapshot.external_action_receipt_ref
                != self.external_action_receipt_ref
                or external_snapshot.transaction_ref != self.transaction_ref
                or external_snapshot.intent_ref != self.intent_ref
                or external_snapshot.binding_ref != self.binding_ref
                or external_snapshot.state != state.value
                or external_snapshot.approval_validation_ref
                != self.approval_validation_ref
                or external_snapshot.authority_decision_ref
                != self.authority_decision_ref
                or external_snapshot.budget_reservation_ref
                != self.budget_reservation_ref
                or external_snapshot.budget_release_ref != self.budget_release_ref
                or external_snapshot.budget_settlement_ref
                != self.budget_settlement_ref
                or external_snapshot.evidence_refs != self.evidence_refs
                or external_snapshot.reason_refs
                != self.external_action_reason_refs
                or external_snapshot.replayed != self.replayed
            ):
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_EXTERNAL_RECEIPT_SNAPSHOT_MISMATCH"
                )
            expected_envelope_ref = governed_task_composition_envelope_ref(
                plan_ref=self.plan_ref,
                recipe_ref=self.recipe_ref,
                composer_authority_ref=self.composer_authority_ref,
                binding_ref=self.binding_ref,
            )
            if self.envelope_ref != expected_envelope_ref:
                raise ValueError("GOVERNED_TASK_COMPOSER_ENVELOPE_REF_MISMATCH")
        if status in successful_statuses:
            if (
                self.external_action_receipt_ref is None
                or any(ref is None for ref in success_kernel_proof_refs)
            ):
                raise ValueError("GOVERNED_TASK_COMPOSER_SUCCESS_PROOF_REQUIRED")
            if self.external_action_reason_refs or self.reason_refs:
                raise ValueError("GOVERNED_TASK_COMPOSER_SUCCESS_REASON_INVALID")
            if len(set(self.operation_refs)) != len(self.operation_refs):
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_SUCCESS_OPERATION_SCOPE_INVALID"
                )
            if self.evidence_refs != expected_success_evidence:
                raise ValueError("GOVERNED_TASK_COMPOSER_SUCCESS_EVIDENCE_MISMATCH")
        elif (
            status == GovernedTaskCompositionStatus.proof_incomplete
            and all(ref is not None for ref in success_kernel_proof_refs)
            and self.evidence_refs == expected_success_evidence
        ):
            raise ValueError(
                "GOVERNED_TASK_COMPOSER_PROOF_INCOMPLETE_STATE_MISMATCH"
            )
        elif not self.reason_refs:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECEIPT_REASON_REQUIRED")
        elif self.external_action_receipt_ref is not None:
            expected_reason_refs = self.external_action_reason_refs or (
                f"reason-ref:governed-task-composer:kernel-{status.value}",
            )
            if self.reason_refs != expected_reason_refs:
                raise ValueError(
                    "GOVERNED_TASK_COMPOSER_DENIAL_REASON_MISMATCH"
                )
        if status == GovernedTaskCompositionStatus.replayed_content_free and (
            not self.replayed
        ):
            raise ValueError("GOVERNED_TASK_COMPOSER_REPLAY_STATE_MISMATCH")
        expected_receipt_ref = stable_governed_browser_ref(
            "receipt-ref:governed-task-composition",
            _task_composition_receipt_identity_payload(self),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("GOVERNED_TASK_COMPOSER_RECEIPT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_task_composition_receipt",
        )
        return self


class ExactGovernedTaskCompositionResult(BaseModel):
    receipt: GovernedTaskCompositionReceipt
    plan: GovernedTaskCompositionPlan | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactGovernedTaskCompositionResult":
        ready = self.receipt.status == GovernedTaskCompositionStatus.plan_ready.value
        if ready != (self.plan is not None):
            raise ValueError("GOVERNED_TASK_COMPOSER_PLAN_PROJECTION_MISMATCH")
        if self.plan is not None and (
            self.plan.plan_ref != self.receipt.plan_ref
            or self.plan.recipe_ref != self.receipt.recipe_ref
            or self.plan.broad_intent_ref != self.receipt.broad_intent_ref
            or self.plan.registry_ref != self.receipt.registry_ref
            or self.plan.composer_authority_ref != self.receipt.composer_authority_ref
            or self.plan.binding_ref != self.receipt.binding_ref
            or self.plan.envelope_ref != self.receipt.envelope_ref
            or tuple(step.operation_ref for step in self.plan.steps)
            != self.receipt.operation_refs
        ):
            raise ValueError("GOVERNED_TASK_COMPOSER_RECEIPT_SCOPE_MISMATCH")
        return self


class ExactGovernedTaskComposer:
    """Prepare one registered plan through every shared authority gate."""

    def __init__(
        self,
        *,
        operation_registry: GovernedTaskOperationRegistry,
        recipe_registry: GovernedTaskCompositionRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._operation_registry = operation_registry
        self._recipe_registry = recipe_registry
        self._kernel = kernel
        self._clock = clock

    def compose(
        self,
        composition_request: ExactGovernedTaskCompositionRequest,
    ) -> ExactGovernedTaskCompositionResult:
        request = ExactGovernedTaskCompositionRequest.model_validate(
            composition_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._recipe_registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:recipe-unregistered",
            )
        if (
            request.plan_ref,
            request.broad_intent_ref,
            request.registry_ref,
        ) != (
            recipe.plan_ref,
            recipe.broad_intent_ref,
            recipe.registry_ref,
        ):
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:request-scope-mismatch",
            )
        if self._operation_registry.registry_ref != recipe.registry_ref:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:registry-mismatch",
            )
        if any(
            self._operation_registry.resolve(step.operation_ref) is None
            for step in recipe.steps
        ):
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:operation-unregistered",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)
        kernel_execution = _composer_kernel_execution(
            execution,
            recipe_ref=recipe.recipe_ref,
        )
        try:
            replay = self._kernel.replay_if_terminal(kernel_execution)
            prior_start = self._kernel.recover_if_prior_start(kernel_execution)
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:idempotency-conflict",
            )
        if replay is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=replay,
                plan=None,
                validation_context=_task_composer_replay_context(
                    self._kernel,
                    expected_execution=kernel_execution,
                    recipe=recipe,
                    replay_receipt=replay,
                ),
            )
        if prior_start is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=prior_start,
                plan=None,
            )
        current_time, clock_reason = _read_clock(self._clock)
        if clock_reason is not None:
            return _preflight_blocked(request, clock_reason)
        assert current_time is not None
        if current_time < recipe.created_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:recipe-not-yet-valid",
            )
        if current_time >= recipe.expires_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:recipe-expired",
            )
        captured: dict[str, GovernedTaskCompositionPlan] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            dispatch_time, dispatch_clock_reason = _read_clock(self._clock)
            if dispatch_clock_reason is not None:
                return _failed_dispatch(dispatched_request, "trusted-clock-invalid")
            assert dispatch_time is not None
            if (
                dispatched_request.binding.binding_ref != recipe.binding_ref
                or not recipe.created_at <= dispatch_time < recipe.expires_at
                or self._operation_registry.registry_ref != recipe.registry_ref
            ):
                return _failed_dispatch(
                    dispatched_request,
                    "plan-revalidation-failed",
                )
            plan = _build_plan(recipe, self._operation_registry)
            captured["plan"] = plan
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[
                    recipe.recipe_ref,
                    recipe.plan_ref,
                    recipe.registry_ref,
                    recipe.composer_authority_ref,
                    *[step.operation_ref for step in recipe.steps],
                ],
                verified=True,
            )

        try:
            external_receipt = self._kernel.execute(
                kernel_execution,
                dispatch=dispatch,
            )
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-task-composer:idempotency-conflict",
            )
        plan = captured.get("plan")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            plan = None
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            plan=plan,
            validation_context=(
                _task_composer_replay_context(
                    self._kernel,
                    expected_execution=kernel_execution,
                    recipe=recipe,
                    replay_receipt=external_receipt,
                )
                if external_receipt.replayed
                else None
            ),
        )


def _composer_kernel_execution(
    request: ExternalActionExecutionRequest,
    *,
    recipe_ref: str,
) -> ExternalActionExecutionRequest:
    return ExternalActionExecutionRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-task-composer",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe_ref,
                },
            ),
        }
    )


def _task_composer_replay_context(
    kernel: GovernedExternalActionKernel,
    *,
    expected_execution: ExternalActionExecutionRequest,
    recipe: GovernedTaskCompositionRecipe,
    replay_receipt: ExternalActionReceipt,
) -> ExternalActionReplayValidationContext:
    expected_evidence = (
        (
            recipe.recipe_ref,
            recipe.plan_ref,
            recipe.registry_ref,
            recipe.composer_authority_ref,
            *(step.operation_ref for step in recipe.steps),
        )
        if replay_receipt.state == ExternalActionState.succeeded.value
        else tuple(replay_receipt.evidence_refs)
    )
    return build_external_action_replay_validation_context(
        kernel,
        expected_execution=expected_execution,
        replay_receipt=replay_receipt,
        expectation=ExternalActionReplayEvidenceExpectation(
            lane_ref=_TASK_COMPOSER_REPLAY_LANE_REF,
            operation_ref=recipe.binding_ref,
            evidence_refs=expected_evidence,
        ),
    )


def _recipe_scope_reason(
    recipe: GovernedTaskCompositionRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    operation_refs = [step.operation_ref for step in recipe.steps]
    required_resources = {
        recipe.broad_intent_ref,
        recipe.registry_ref,
        recipe.plan_payload_ref,
        recipe.composer_authority_ref,
    }
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-task-composer:binding-mismatch",
        ),
        (
            recipe.transaction_ref == binding.transaction_ref,
            "reason-ref:governed-task-composer:transaction-mismatch",
        ),
        (
            recipe.intent_ref == request.intent_ref,
            "reason-ref:governed-task-composer:intent-mismatch",
        ),
        (
            recipe.origin_ref == binding.origin_ref,
            "reason-ref:governed-task-composer:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-task-composer:snapshot-mismatch",
        ),
        (
            recipe.plan_payload_ref == binding.recipient_ref,
            "reason-ref:governed-task-composer:plan-mismatch",
        ),
        (
            recipe.schema_ref == binding.field_schema_ref,
            "reason-ref:governed-task-composer:schema-mismatch",
        ),
        (
            tuple(operation_refs) == binding.artifact_refs,
            "reason-ref:governed-task-composer:operation-scope-mismatch",
        ),
        (
            set(binding.resource_refs) == required_resources,
            "reason-ref:governed-task-composer:resource-scope-mismatch",
        ),
        (
            binding.authority_capability == AuthorityCapability.prepare.value,
            "reason-ref:governed-task-composer:capability-mismatch",
        ),
        (
            binding.human_present,
            "reason-ref:governed-task-composer:human-presence-required",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-task-composer:real-targets-inactive",
        ),
        (
            recipe.expires_at <= binding.start_deadline,
            "reason-ref:governed-task-composer:recipe-outlives-deadline",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _build_plan(
    recipe: GovernedTaskCompositionRecipe,
    registry: GovernedTaskOperationRegistry,
) -> GovernedTaskCompositionPlan:
    plan_steps: list[GovernedTaskCompositionPlanStep] = []
    for step in recipe.steps:
        operation = registry.resolve(step.operation_ref)
        if operation is None:
            raise ValueError("GOVERNED_TASK_COMPOSER_OPERATION_UNREGISTERED")
        plan_steps.append(
            GovernedTaskCompositionPlanStep(
                step_ref=step.step_ref,
                ordinal=step.ordinal,
                operation_ref=operation.operation_ref,
                kind=operation.kind,
                source_recipe_ref=operation.source_recipe_ref,
                source_contract_ref=operation.source_contract_ref,
                source_binding_ref=operation.source_binding_ref,
                operation_authority_ref=operation.operation_authority_ref,
                required_capability=operation.required_capability,
                target_ref=operation.target_ref,
                schema_ref=operation.schema_ref,
                depends_on_step_refs=step.depends_on_step_refs,
            )
        )
    return GovernedTaskCompositionPlan(
        plan_ref=recipe.plan_ref,
        plan_payload_ref=recipe.plan_payload_ref,
        recipe_ref=recipe.recipe_ref,
        recipe_snapshot=recipe,
        broad_intent_ref=recipe.broad_intent_ref,
        registry_ref=recipe.registry_ref,
        composer_authority_ref=recipe.composer_authority_ref,
        binding_ref=recipe.binding_ref,
        envelope_ref=governed_task_composition_envelope_ref(
            plan_ref=recipe.plan_ref,
            recipe_ref=recipe.recipe_ref,
            composer_authority_ref=recipe.composer_authority_ref,
            binding_ref=recipe.binding_ref,
        ),
        steps=tuple(plan_steps),
        created_at=recipe.created_at,
        expires_at=recipe.expires_at,
    )


def _read_clock(
    clock: Callable[[], datetime],
) -> tuple[datetime | None, str | None]:
    try:
        current_time = clock()
    except Exception:
        return None, "reason-ref:governed-task-composer:trusted-clock-failed"
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        return None, "reason-ref:governed-task-composer:trusted-clock-invalid"
    try:
        return current_time.astimezone(timezone.utc), None
    except Exception:
        return None, "reason-ref:governed-task-composer:trusted-clock-invalid"


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
    suffix: str,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                f"evidence-ref:governed-task-composer:{suffix}",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactGovernedTaskCompositionRequest,
    reason_ref: str,
) -> ExactGovernedTaskCompositionResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "plan_ref": request.plan_ref,
        "broad_intent_ref": request.broad_intent_ref,
        "registry_ref": request.registry_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": GovernedTaskCompositionStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": (reason_ref,),
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        _task_composition_receipt_identity_payload(
            GovernedTaskCompositionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-task-composition:pending",
                **payload,
            )
        ),
    )
    return ExactGovernedTaskCompositionResult(
        receipt=GovernedTaskCompositionReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactGovernedTaskCompositionRequest,
    recipe: GovernedTaskCompositionRecipe,
    external_receipt: ExternalActionReceipt,
    plan: GovernedTaskCompositionPlan | None,
    validation_context: ExternalActionReplayValidationContext | None = None,
) -> ExactGovernedTaskCompositionResult:
    execution = request.execution_request
    if (
        external_receipt.transaction_ref,
        external_receipt.intent_ref,
        external_receipt.binding_ref,
    ) != (
        execution.binding.transaction_ref,
        execution.intent_ref,
        recipe.binding_ref,
    ) or recipe.binding_ref != execution.binding.binding_ref:
        return _preflight_blocked(
            request,
            "reason-ref:governed-task-composer:external-receipt-scope-mismatch",
        )
    state = ExternalActionState(external_receipt.state)
    expected_success_evidence = (
        recipe.recipe_ref,
        recipe.plan_ref,
        recipe.registry_ref,
        recipe.composer_authority_ref,
        *(step.operation_ref for step in recipe.steps),
    )
    success_proofs_complete = (
        all(
            ref is not None
            for ref in (
                external_receipt.approval_validation_ref,
                external_receipt.authority_decision_ref,
                external_receipt.budget_reservation_ref,
                external_receipt.budget_settlement_ref,
            )
        )
        and tuple(external_receipt.evidence_refs) == expected_success_evidence
    )
    if state == ExternalActionState.succeeded and not success_proofs_complete:
        status = GovernedTaskCompositionStatus.proof_incomplete
    elif external_receipt.replayed and state == ExternalActionState.succeeded:
        status = GovernedTaskCompositionStatus.replayed_content_free
    elif state == ExternalActionState.succeeded:
        status = GovernedTaskCompositionStatus.plan_ready
    else:
        status = {
            ExternalActionState.blocked: GovernedTaskCompositionStatus.transaction_blocked,
            ExternalActionState.failed: GovernedTaskCompositionStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                GovernedTaskCompositionStatus.outcome_ambiguous
            ),
            ExternalActionState.started: GovernedTaskCompositionStatus.outcome_ambiguous,
            ExternalActionState.prepared: GovernedTaskCompositionStatus.outcome_ambiguous,
        }[state]
    reason_refs = tuple(external_receipt.reason_refs)
    if not reason_refs and status not in {
        GovernedTaskCompositionStatus.plan_ready,
        GovernedTaskCompositionStatus.replayed_content_free,
    }:
        reason_refs = (
            f"reason-ref:governed-task-composer:kernel-{status.value}",
        )
    operation_refs = tuple(step.operation_ref for step in recipe.steps)
    external_receipt_snapshot = _build_external_receipt_snapshot(
        external_receipt,
        validation_context=validation_context,
    )
    payload = {
        "recipe_ref": recipe.recipe_ref,
        "plan_ref": recipe.plan_ref,
        "broad_intent_ref": recipe.broad_intent_ref,
        "registry_ref": recipe.registry_ref,
        "recipe_snapshot": recipe,
        "external_receipt_snapshot": external_receipt_snapshot,
        "composer_authority_ref": recipe.composer_authority_ref,
        "envelope_ref": governed_task_composition_envelope_ref(
            plan_ref=recipe.plan_ref,
            recipe_ref=recipe.recipe_ref,
            composer_authority_ref=recipe.composer_authority_ref,
            binding_ref=recipe.binding_ref,
        ),
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
        "operation_refs": operation_refs,
        "evidence_refs": tuple(external_receipt.evidence_refs),
        "external_action_reason_refs": tuple(external_receipt.reason_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-task-composition",
        _task_composition_receipt_identity_payload(
            GovernedTaskCompositionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-task-composition:pending",
                **payload,
            )
        ),
    )
    receipt_payload = {
        "receipt_ref": receipt_ref,
        **payload,
    }
    result_plan = (
        plan if status == GovernedTaskCompositionStatus.plan_ready else None
    )
    if validation_context is not None:
        return ExactGovernedTaskCompositionResult.model_validate(
            {
                "receipt": receipt_payload,
                "plan": result_plan,
            },
            context=replay_validation_context(validation_context),
        )
    return ExactGovernedTaskCompositionResult(
        receipt=GovernedTaskCompositionReceipt(**receipt_payload),
        plan=result_plan,
    )
