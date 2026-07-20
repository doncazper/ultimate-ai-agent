"""Inactive exact contracts for high-consequence external operations.

Queue 01 item 11 prepares one content-free contract for an exact
communication, publishing, account-creation, legal-consent, or deletion
operation.  Preparation passes through the governed external-action kernel,
but never opens a browser, calls a network, materializes payload content, or
performs the described external effect.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Literal

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
from .transaction import (
    ExternalActionTransactionConflict,
    GovernedExternalActionKernel,
)


MAX_GOVERNED_EXTERNAL_OPERATION_RECIPE_LIFETIME = timedelta(minutes=10)
_HASH_PINNED_SUFFIX_RE = re.compile(r"sha256:[0-9a-f]{64}")
_OPERATION_AUTHORITY_PREFIX = "external-operation-authority-ref:governed-browser:"


class GovernedExternalOperation(str, Enum):
    send_communication = "send_communication"
    publish_artifact = "publish_artifact"
    create_account = "create_account"
    record_legal_consent = "record_legal_consent"
    delete_resource = "delete_resource"


class GovernedLegalConsentDecision(str, Enum):
    accept = "accept"
    decline = "decline"


class GovernedExternalOperationReversibility(str, Enum):
    reversible = "reversible"
    manual_recovery = "manual_recovery"
    irreversible = "irreversible"


class GovernedExternalOperationContractStatus(str, Enum):
    contract_ready = "contract_ready"
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


def _required_capability(
    operation: GovernedExternalOperation,
) -> AuthorityCapability:
    return {
        GovernedExternalOperation.send_communication: AuthorityCapability.send,
        GovernedExternalOperation.publish_artifact: AuthorityCapability.send,
        GovernedExternalOperation.create_account: AuthorityCapability.write,
        GovernedExternalOperation.record_legal_consent: AuthorityCapability.mutate,
        GovernedExternalOperation.delete_resource: AuthorityCapability.destructive,
    }[GovernedExternalOperation(operation)]


def _validate_hash_pinned_ref(
    value: str,
    *,
    label: str,
    prefix: str,
) -> None:
    validate_task_ref(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"GOVERNED_EXTERNAL_OPERATION_{label.upper()}_REQUIRED")
    if _HASH_PINNED_SUFFIX_RE.fullmatch(value.removeprefix(prefix)) is None:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_HASH_PIN_REQUIRED")


def governed_external_operation_target_ref(
    *,
    operation: GovernedExternalOperation,
    target_descriptor_ref: str,
) -> str:
    validate_task_ref(target_descriptor_ref, "target_descriptor_ref")
    return stable_governed_browser_ref(
        "external-operation-target-ref:governed-browser",
        {
            "operation": GovernedExternalOperation(operation).value,
            "target_descriptor_ref": target_descriptor_ref,
        },
    )


def governed_external_operation_input_ref(
    *,
    operation: GovernedExternalOperation,
    target_ref: str,
    artifact_refs: Sequence[str],
) -> str:
    exact_operation = GovernedExternalOperation(operation)
    _validate_hash_pinned_ref(
        target_ref,
        label="target_ref",
        prefix="external-operation-target-ref:governed-browser:",
    )
    exact_artifacts = list(artifact_refs)
    if not exact_artifacts or len(exact_artifacts) > 8:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_ARTIFACT_SCOPE_INVALID")
    for artifact_ref in exact_artifacts:
        _validate_hash_pinned_ref(
            artifact_ref,
            label="artifact_ref",
            prefix="external-operation-artifact-ref:governed-browser:",
        )
    if len(set(exact_artifacts)) != len(exact_artifacts):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_ARTIFACT_DUPLICATE")
    return stable_governed_browser_ref(
        "external-operation-input-ref:governed-browser",
        {
            "operation": exact_operation.value,
            "target_ref": target_ref,
            "artifact_refs": exact_artifacts,
        },
    )


def governed_external_operation_schema_ref(
    *,
    operation: GovernedExternalOperation,
    target_ref: str,
    operation_input_ref: str,
    artifact_refs: Sequence[str],
    legal_instrument_ref: str | None,
    legal_decision: GovernedLegalConsentDecision | None,
    delete_resource_ref: str | None,
    reversibility: GovernedExternalOperationReversibility,
    rollback_ref: str,
    reconciliation_ref: str,
) -> str:
    exact_operation = GovernedExternalOperation(operation)
    exact_reversibility = GovernedExternalOperationReversibility(reversibility)
    exact_artifacts = list(artifact_refs)
    _validate_hash_pinned_ref(
        target_ref,
        label="target_ref",
        prefix="external-operation-target-ref:governed-browser:",
    )
    _validate_hash_pinned_ref(
        operation_input_ref,
        label="operation_input_ref",
        prefix="external-operation-input-ref:governed-browser:",
    )
    for artifact_ref in exact_artifacts:
        _validate_hash_pinned_ref(
            artifact_ref,
            label="artifact_ref",
            prefix="external-operation-artifact-ref:governed-browser:",
        )
    expected_input_ref = governed_external_operation_input_ref(
        operation=exact_operation,
        target_ref=target_ref,
        artifact_refs=exact_artifacts,
    )
    if operation_input_ref != expected_input_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_INPUT_REF_MISMATCH")
    for value, label, prefix in (
        (
            rollback_ref,
            "rollback_ref",
            "external-operation-rollback-ref:governed-browser:",
        ),
        (
            reconciliation_ref,
            "reconciliation_ref",
            "external-operation-reconciliation-ref:governed-browser:",
        ),
    ):
        _validate_hash_pinned_ref(value, label=label, prefix=prefix)
    if legal_instrument_ref is not None:
        _validate_hash_pinned_ref(
            legal_instrument_ref,
            label="legal_instrument_ref",
            prefix="legal-instrument-ref:governed-browser:",
        )
    if delete_resource_ref is not None:
        _validate_hash_pinned_ref(
            delete_resource_ref,
            label="delete_resource_ref",
            prefix="external-operation-target-ref:governed-browser:",
        )
    _validate_operation_specific_scope(
        operation=exact_operation,
        target_ref=target_ref,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=legal_decision,
        delete_resource_ref=delete_resource_ref,
    )
    _validate_reversibility(
        operation=exact_operation,
        reversibility=exact_reversibility,
    )
    return stable_governed_browser_ref(
        "external-operation-schema-ref:governed-browser",
        {
            "operation": exact_operation.value,
            "target_ref": target_ref,
            "operation_input_ref": operation_input_ref,
            "artifact_refs": exact_artifacts,
            "legal_instrument_ref": legal_instrument_ref,
            "legal_decision": (
                GovernedLegalConsentDecision(legal_decision).value
                if legal_decision is not None
                else None
            ),
            "delete_resource_ref": delete_resource_ref,
            "reversibility": exact_reversibility.value,
            "rollback_ref": rollback_ref,
            "reconciliation_ref": reconciliation_ref,
        },
    )


def governed_external_operation_authority_ref(
    *,
    operation: GovernedExternalOperation,
    origin_ref: str,
    target_ref: str,
    schema_ref: str,
) -> str:
    validate_task_ref(origin_ref, "origin_ref")
    _validate_hash_pinned_ref(
        target_ref,
        label="target_ref",
        prefix="external-operation-target-ref:governed-browser:",
    )
    _validate_hash_pinned_ref(
        schema_ref,
        label="schema_ref",
        prefix="external-operation-schema-ref:governed-browser:",
    )
    return stable_governed_browser_ref(
        "external-operation-authority-ref:governed-browser",
        {
            "operation": GovernedExternalOperation(operation).value,
            "origin_ref": origin_ref,
            "target_ref": target_ref,
            "schema_ref": schema_ref,
        },
    )


def governed_external_operation_contract_ref(
    *,
    operation: GovernedExternalOperation,
    origin_ref: str,
    page_snapshot_ref: str,
    target_ref: str,
    operation_input_ref: str,
    schema_ref: str,
    operation_authority_ref: str,
    artifact_refs: Sequence[str],
    legal_instrument_ref: str | None,
    legal_decision: GovernedLegalConsentDecision | None,
    delete_resource_ref: str | None,
    reversibility: GovernedExternalOperationReversibility,
    rollback_ref: str,
    reconciliation_ref: str,
    expires_at: datetime,
) -> str:
    for value, label in (
        (origin_ref, "origin_ref"),
        (page_snapshot_ref, "page_snapshot_ref"),
    ):
        validate_task_ref(value, label)
    if expires_at.tzinfo is None:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_TIMEZONE_REQUIRED")
    expected_schema_ref = governed_external_operation_schema_ref(
        operation=operation,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        artifact_refs=artifact_refs,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=legal_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
    )
    if schema_ref != expected_schema_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_SCHEMA_REF_MISMATCH")
    expected_authority_ref = governed_external_operation_authority_ref(
        operation=operation,
        origin_ref=origin_ref,
        target_ref=target_ref,
        schema_ref=schema_ref,
    )
    if operation_authority_ref != expected_authority_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_AUTHORITY_REF_MISMATCH")
    return stable_governed_browser_ref(
        "external-operation-contract-ref:governed-browser",
        {
            "operation": GovernedExternalOperation(operation).value,
            "origin_ref": origin_ref,
            "page_snapshot_ref": page_snapshot_ref,
            "target_ref": target_ref,
            "operation_input_ref": operation_input_ref,
            "schema_ref": schema_ref,
            "operation_authority_ref": operation_authority_ref,
            "artifact_refs": list(artifact_refs),
            "legal_instrument_ref": legal_instrument_ref,
            "legal_decision": (
                GovernedLegalConsentDecision(legal_decision).value
                if legal_decision is not None
                else None
            ),
            "delete_resource_ref": delete_resource_ref,
            "reversibility": GovernedExternalOperationReversibility(
                reversibility
            ).value,
            "rollback_ref": rollback_ref,
            "reconciliation_ref": reconciliation_ref,
            "expires_at": expires_at.isoformat(),
        },
    )


def _validate_operation_specific_scope(
    *,
    operation: GovernedExternalOperation,
    target_ref: str,
    legal_instrument_ref: str | None,
    legal_decision: GovernedLegalConsentDecision | None,
    delete_resource_ref: str | None,
) -> None:
    exact_operation = GovernedExternalOperation(operation)
    legal_operation = exact_operation == GovernedExternalOperation.record_legal_consent
    delete_operation = exact_operation == GovernedExternalOperation.delete_resource
    if legal_operation != (
        legal_instrument_ref is not None and legal_decision is not None
    ):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_LEGAL_SCOPE_MISMATCH")
    if not legal_operation and (
        legal_instrument_ref is not None or legal_decision is not None
    ):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_LEGAL_SCOPE_MISMATCH")
    if delete_operation != (delete_resource_ref is not None):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_DELETE_SCOPE_MISMATCH")
    if delete_operation and delete_resource_ref != target_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_DELETE_TARGET_MISMATCH")


def _validate_reversibility(
    *,
    operation: GovernedExternalOperation,
    reversibility: GovernedExternalOperationReversibility,
) -> None:
    exact_operation = GovernedExternalOperation(operation)
    exact_reversibility = GovernedExternalOperationReversibility(reversibility)
    if (
        exact_operation == GovernedExternalOperation.send_communication
        and exact_reversibility != GovernedExternalOperationReversibility.irreversible
    ):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_REVERSIBILITY_UNPROVEN")
    if (
        exact_operation
        in {
            GovernedExternalOperation.publish_artifact,
            GovernedExternalOperation.create_account,
            GovernedExternalOperation.record_legal_consent,
        }
        and exact_reversibility
        != GovernedExternalOperationReversibility.manual_recovery
    ):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_REVERSIBILITY_UNPROVEN")
    if (
        exact_operation == GovernedExternalOperation.delete_resource
        and exact_reversibility
        not in {
            GovernedExternalOperationReversibility.manual_recovery,
            GovernedExternalOperationReversibility.irreversible,
        }
    ):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_REVERSIBILITY_UNPROVEN")


class GovernedExternalOperationRecipe(BaseModel):
    """One immutable registered plan-only external operation."""

    schema_version: Literal["uaa-governed-external-operation-recipe.v1"] = (
        "uaa-governed-external-operation-recipe.v1"
    )
    recipe_ref: str
    contract_ref: str
    operation_authority_ref: str
    binding_ref: str
    operation: GovernedExternalOperation
    required_capability: AuthorityCapability
    origin_ref: str
    page_snapshot_ref: str
    target_ref: str
    operation_input_ref: str
    schema_ref: str
    artifact_refs: list[str] = Field(..., min_length=1, max_length=8)
    legal_instrument_ref: str | None = None
    legal_decision: GovernedLegalConsentDecision | None = None
    delete_resource_ref: str | None = None
    reversibility: GovernedExternalOperationReversibility
    rollback_ref: str
    reconciliation_ref: str
    created_at: datetime
    expires_at: datetime
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    human_presence_required: Literal[True] = True
    contract_plan_only: Literal[True] = True
    payload_materialization_allowed: Literal[False] = False
    browser_open_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    communication_send_allowed: Literal[False] = False
    publishing_allowed: Literal[False] = False
    account_creation_allowed: Literal[False] = False
    legal_consent_recording_allowed: Literal[False] = False
    delete_allowed: Literal[False] = False
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
    def validate_recipe(self) -> "GovernedExternalOperationRecipe":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.operation_authority_ref, "operation_authority_ref"),
            (self.binding_ref, "binding_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.target_ref, "target_ref"),
            (self.operation_input_ref, "operation_input_ref"),
            (self.schema_ref, "schema_ref"),
            (self.legal_instrument_ref, "legal_instrument_ref"),
            (self.delete_resource_ref, "delete_resource_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.reconciliation_ref, "reconciliation_ref"),
            *[(ref, "artifact_ref") for ref in self.artifact_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at
            > MAX_GOVERNED_EXTERNAL_OPERATION_RECIPE_LIFETIME
        ):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_LIFETIME_INVALID")
        operation = GovernedExternalOperation(self.operation)
        if self.required_capability != _required_capability(operation).value:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_CAPABILITY_MISMATCH")
        _validate_operation_specific_scope(
            operation=operation,
            target_ref=self.target_ref,
            legal_instrument_ref=self.legal_instrument_ref,
            legal_decision=(
                GovernedLegalConsentDecision(self.legal_decision)
                if self.legal_decision is not None
                else None
            ),
            delete_resource_ref=self.delete_resource_ref,
        )
        expected_input_ref = governed_external_operation_input_ref(
            operation=operation,
            target_ref=self.target_ref,
            artifact_refs=self.artifact_refs,
        )
        if self.operation_input_ref != expected_input_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_INPUT_REF_MISMATCH")
        expected_schema_ref = governed_external_operation_schema_ref(
            operation=operation,
            target_ref=self.target_ref,
            operation_input_ref=self.operation_input_ref,
            artifact_refs=self.artifact_refs,
            legal_instrument_ref=self.legal_instrument_ref,
            legal_decision=(
                GovernedLegalConsentDecision(self.legal_decision)
                if self.legal_decision is not None
                else None
            ),
            delete_resource_ref=self.delete_resource_ref,
            reversibility=GovernedExternalOperationReversibility(self.reversibility),
            rollback_ref=self.rollback_ref,
            reconciliation_ref=self.reconciliation_ref,
        )
        if self.schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_SCHEMA_REF_MISMATCH")
        expected_authority_ref = governed_external_operation_authority_ref(
            operation=operation,
            origin_ref=self.origin_ref,
            target_ref=self.target_ref,
            schema_ref=self.schema_ref,
        )
        if self.operation_authority_ref != expected_authority_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_AUTHORITY_REF_MISMATCH")
        expected_contract_ref = governed_external_operation_contract_ref(
            operation=operation,
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            target_ref=self.target_ref,
            operation_input_ref=self.operation_input_ref,
            schema_ref=self.schema_ref,
            operation_authority_ref=self.operation_authority_ref,
            artifact_refs=self.artifact_refs,
            legal_instrument_ref=self.legal_instrument_ref,
            legal_decision=(
                GovernedLegalConsentDecision(self.legal_decision)
                if self.legal_decision is not None
                else None
            ),
            delete_resource_ref=self.delete_resource_ref,
            reversibility=GovernedExternalOperationReversibility(self.reversibility),
            rollback_ref=self.rollback_ref,
            reconciliation_ref=self.reconciliation_ref,
            expires_at=self.expires_at,
        )
        if self.contract_ref != expected_contract_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_CONTRACT_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "external-operation-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_external_operation_recipe",
        )
        return self


def build_governed_external_operation_recipe(
    request: ExternalActionExecutionRequest,
    *,
    operation: GovernedExternalOperation,
    target_ref: str,
    operation_input_ref: str,
    legal_instrument_ref: str | None,
    legal_decision: GovernedLegalConsentDecision | None,
    delete_resource_ref: str | None,
    reversibility: GovernedExternalOperationReversibility,
    rollback_ref: str,
    reconciliation_ref: str,
    created_at: datetime,
    expires_at: datetime,
) -> GovernedExternalOperationRecipe:
    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    exact_operation = GovernedExternalOperation(operation)
    exact_reversibility = GovernedExternalOperationReversibility(reversibility)
    exact_decision = (
        GovernedLegalConsentDecision(legal_decision)
        if legal_decision is not None
        else None
    )
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != _required_capability(exact_operation).value:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_EXACT_CAPABILITY_MISMATCH")
    if not binding.human_present:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_HUMAN_PRESENCE_REQUIRED")
    if target_ref != binding.recipient_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_TARGET_NOT_AUTHORITY_BOUND")
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline or expires_at > binding.start_deadline:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_DEADLINE_EXCEEDED")
    expected_input_ref = governed_external_operation_input_ref(
        operation=exact_operation,
        target_ref=target_ref,
        artifact_refs=binding.artifact_refs,
    )
    if operation_input_ref != expected_input_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_INPUT_REF_MISMATCH")
    schema_ref = governed_external_operation_schema_ref(
        operation=exact_operation,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        artifact_refs=binding.artifact_refs,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=exact_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=exact_reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
    )
    if binding.field_schema_ref != schema_ref:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_SCHEMA_NOT_AUTHORITY_BOUND")
    operation_authority_ref = governed_external_operation_authority_ref(
        operation=exact_operation,
        origin_ref=binding.origin_ref,
        target_ref=target_ref,
        schema_ref=schema_ref,
    )
    contract_ref = governed_external_operation_contract_ref(
        operation=exact_operation,
        origin_ref=binding.origin_ref,
        page_snapshot_ref=binding.page_snapshot_ref,
        target_ref=target_ref,
        operation_input_ref=operation_input_ref,
        schema_ref=schema_ref,
        operation_authority_ref=operation_authority_ref,
        artifact_refs=binding.artifact_refs,
        legal_instrument_ref=legal_instrument_ref,
        legal_decision=exact_decision,
        delete_resource_ref=delete_resource_ref,
        reversibility=exact_reversibility,
        rollback_ref=rollback_ref,
        reconciliation_ref=reconciliation_ref,
        expires_at=expires_at,
    )
    required_resources = {
        operation_authority_ref,
        operation_input_ref,
        rollback_ref,
        reconciliation_ref,
        contract_ref,
    }
    if legal_instrument_ref is not None:
        required_resources.add(legal_instrument_ref)
    if delete_resource_ref is not None:
        required_resources.add(delete_resource_ref)
    if set(binding.resource_refs) != required_resources:
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_RESOURCE_NOT_EXACTLY_BOUND")
    bound_authority_refs = tuple(
        ref
        for ref in binding.resource_refs
        if ref.startswith(_OPERATION_AUTHORITY_PREFIX)
    )
    if bound_authority_refs != (operation_authority_ref,):
        raise ValueError("GOVERNED_EXTERNAL_OPERATION_AUTHORITY_NOT_EXACTLY_BOUND")
    payload = {
        "contract_ref": contract_ref,
        "operation_authority_ref": operation_authority_ref,
        "binding_ref": binding.binding_ref,
        "operation": exact_operation,
        "required_capability": _required_capability(exact_operation),
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "target_ref": target_ref,
        "operation_input_ref": operation_input_ref,
        "schema_ref": schema_ref,
        "artifact_refs": list(binding.artifact_refs),
        "legal_instrument_ref": legal_instrument_ref,
        "legal_decision": exact_decision,
        "delete_resource_ref": delete_resource_ref,
        "reversibility": exact_reversibility,
        "rollback_ref": rollback_ref,
        "reconciliation_ref": reconciliation_ref,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedExternalOperationRecipe.model_construct(
        recipe_ref="external-operation-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "external-operation-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedExternalOperationRecipe(recipe_ref=recipe_ref, **payload)


class GovernedExternalOperationRecipeRegistry:
    """Immutable exact-operation registry."""

    def __init__(self, recipes: Sequence[GovernedExternalOperationRecipe]) -> None:
        validated = tuple(
            GovernedExternalOperationRecipe.model_validate(
                recipe.model_dump(mode="json")
            )
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECIPE_REGISTRY_TOO_LARGE")
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECIPE_REF_DUPLICATE")
        by_authority = {recipe.operation_authority_ref: recipe for recipe in validated}
        if len(by_authority) != len(validated):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_AUTHORITY_DUPLICATE")
        self._recipes = by_ref

    def resolve(self, recipe_ref: str) -> GovernedExternalOperationRecipe | None:
        return self._recipes.get(recipe_ref)


class ExactGovernedExternalOperationRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str
    contract_ref: str
    operation: GovernedExternalOperation
    target_ref: str

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedExternalOperationRequest":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.target_ref, "target_ref"),
        ):
            validate_task_ref(value, label)
        return self


class ExactGovernedExternalOperationContract(BaseModel):
    """Content-free exact contract; never an execution result."""

    schema_version: Literal["uaa-governed-external-operation-contract.v1"] = (
        "uaa-governed-external-operation-contract.v1"
    )
    contract_ref: str
    operation_authority_ref: str
    binding_ref: str
    operation: GovernedExternalOperation
    required_capability: AuthorityCapability
    origin_ref: str
    page_snapshot_ref: str
    target_ref: str
    operation_input_ref: str
    schema_ref: str
    artifact_refs: list[str] = Field(..., min_length=1, max_length=8)
    legal_instrument_ref: str | None = None
    legal_decision: GovernedLegalConsentDecision | None = None
    delete_resource_ref: str | None = None
    reversibility: GovernedExternalOperationReversibility
    rollback_ref: str
    reconciliation_ref: str
    expires_at: datetime
    contract_prepared: Literal[True] = True
    separate_exact_execution_required: Literal[True] = True
    payload_materialized: Literal[False] = False
    browser_opened: Literal[False] = False
    network_call_performed: Literal[False] = False
    communication_sent: Literal[False] = False
    artifact_published: Literal[False] = False
    account_created: Literal[False] = False
    legal_consent_recorded: Literal[False] = False
    resource_deleted: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_contract(self) -> "ExactGovernedExternalOperationContract":
        operation = GovernedExternalOperation(self.operation)
        if self.required_capability != _required_capability(operation).value:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_CAPABILITY_MISMATCH")
        _validate_operation_specific_scope(
            operation=operation,
            target_ref=self.target_ref,
            legal_instrument_ref=self.legal_instrument_ref,
            legal_decision=(
                GovernedLegalConsentDecision(self.legal_decision)
                if self.legal_decision is not None
                else None
            ),
            delete_resource_ref=self.delete_resource_ref,
        )
        expected_contract_ref = governed_external_operation_contract_ref(
            operation=operation,
            origin_ref=self.origin_ref,
            page_snapshot_ref=self.page_snapshot_ref,
            target_ref=self.target_ref,
            operation_input_ref=self.operation_input_ref,
            schema_ref=self.schema_ref,
            operation_authority_ref=self.operation_authority_ref,
            artifact_refs=self.artifact_refs,
            legal_instrument_ref=self.legal_instrument_ref,
            legal_decision=(
                GovernedLegalConsentDecision(self.legal_decision)
                if self.legal_decision is not None
                else None
            ),
            delete_resource_ref=self.delete_resource_ref,
            reversibility=GovernedExternalOperationReversibility(self.reversibility),
            rollback_ref=self.rollback_ref,
            reconciliation_ref=self.reconciliation_ref,
            expires_at=self.expires_at,
        )
        if self.contract_ref != expected_contract_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_CONTRACT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "exact_governed_external_operation_contract",
        )
        return self


def _external_operation_receipt_identity_payload(receipt: BaseModel) -> dict[str, Any]:
    payload = receipt.model_dump(mode="json", exclude={"receipt_ref"})
    if payload.get("budget_release_ref") is None:
        payload.pop("budget_release_ref", None)
    if payload.get("external_action_reason_refs") is None:
        payload.pop("external_action_reason_refs", None)
    return payload


class GovernedExternalOperationReceipt(BaseModel):
    schema_version: Literal["uaa-governed-external-operation-receipt.v1"] = (
        "uaa-governed-external-operation-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    contract_ref: str
    operation: GovernedExternalOperation
    target_ref: str
    operation_authority_ref: str | None = None
    operation_input_ref: str | None = None
    rollback_ref: str | None = None
    reconciliation_ref: str | None = None
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: GovernedExternalOperationContractStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
    budget_settlement_ref: str | None = None
    external_action_reason_refs: tuple[str, ...] | None = Field(
        default=None,
        max_length=16,
    )
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    contract_plan_only: Literal[True] = True
    payload_recorded: Literal[False] = False
    browser_action_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_receipt(self) -> "GovernedExternalOperationReceipt":
        for value, label in (
            (self.receipt_ref, "receipt_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.contract_ref, "contract_ref"),
            (self.target_ref, "target_ref"),
            (self.operation_authority_ref, "operation_authority_ref"),
            (self.operation_input_ref, "operation_input_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.reconciliation_ref, "reconciliation_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_release_ref, "budget_release_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            *[
                (ref, "external_action_reason_ref")
                for ref in (self.external_action_reason_refs or ())
            ],
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        status = GovernedExternalOperationContractStatus(self.status)
        state = ExternalActionState(self.external_action_state)
        successful_statuses = {
            GovernedExternalOperationContractStatus.contract_ready,
            GovernedExternalOperationContractStatus.replayed_content_free,
        }
        if (
            status == GovernedExternalOperationContractStatus.contract_ready
            and state != ExternalActionState.succeeded
        ):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_READY_STATE_MISMATCH")
        if (
            status == GovernedExternalOperationContractStatus.contract_ready
            and self.replayed
        ):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_READY_PROOF_REQUIRED")
        success_kernel_proof_refs = (
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_settlement_ref,
        )
        external_kernel_proof_refs = (
            *success_kernel_proof_refs,
            self.budget_release_ref,
        )
        external_proof_context_present = (
            self.external_action_receipt_ref is not None
            or any(ref is not None for ref in external_kernel_proof_refs)
            or bool(self.evidence_refs)
            or bool(self.external_action_reason_refs)
        )
        if (
            status == GovernedExternalOperationContractStatus.preflight_blocked
            and (external_proof_context_present or self.replayed)
        ):
            raise ValueError(
                "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_INVALID"
            )
        if self.external_action_receipt_ref is None and (
            any(ref is not None for ref in external_kernel_proof_refs)
            or self.evidence_refs
            or self.external_action_reason_refs
        ):
            raise ValueError(
                "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_PROOF_CONTEXT_INVALID"
            )
        scope_proof_refs = (
            self.operation_authority_ref,
            self.operation_input_ref,
            self.rollback_ref,
            self.reconciliation_ref,
        )
        if status in successful_statuses:
            if self.external_action_receipt_ref is None or any(
                ref is None for ref in success_kernel_proof_refs
            ):
                raise ValueError(
                    "GOVERNED_EXTERNAL_OPERATION_SUCCESS_KERNEL_PROOF_REQUIRED"
                )
            if any(ref is None for ref in scope_proof_refs):
                raise ValueError(
                    "GOVERNED_EXTERNAL_OPERATION_SUCCESS_SCOPE_PROOF_REQUIRED"
                )
            for value, label, prefix in (
                (
                    self.recipe_ref,
                    "recipe_ref",
                    "external-operation-recipe-ref:governed-browser:",
                ),
                (
                    self.contract_ref,
                    "contract_ref",
                    "external-operation-contract-ref:governed-browser:",
                ),
                (
                    self.target_ref,
                    "target_ref",
                    "external-operation-target-ref:governed-browser:",
                ),
            ):
                _validate_hash_pinned_ref(value, label=label, prefix=prefix)
            assert self.operation_authority_ref is not None
            assert self.operation_input_ref is not None
            assert self.rollback_ref is not None
            assert self.reconciliation_ref is not None
            for value, label, prefix in (
                (
                    self.operation_authority_ref,
                    "operation_authority_ref",
                    _OPERATION_AUTHORITY_PREFIX,
                ),
                (
                    self.operation_input_ref,
                    "operation_input_ref",
                    "external-operation-input-ref:governed-browser:",
                ),
                (
                    self.rollback_ref,
                    "rollback_ref",
                    "external-operation-rollback-ref:governed-browser:",
                ),
                (
                    self.reconciliation_ref,
                    "reconciliation_ref",
                    "external-operation-reconciliation-ref:governed-browser:",
                ),
            ):
                _validate_hash_pinned_ref(value, label=label, prefix=prefix)
            if self.evidence_refs != [
                self.contract_ref,
                self.operation_authority_ref,
                self.operation_input_ref,
                self.rollback_ref,
                self.reconciliation_ref,
            ]:
                raise ValueError(
                    "GOVERNED_EXTERNAL_OPERATION_SUCCESS_EVIDENCE_MISMATCH"
                )
        if status == GovernedExternalOperationContractStatus.replayed_content_free and (
            not self.replayed or state != ExternalActionState.succeeded
        ):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_REPLAY_STATE_MISMATCH")
        if self.external_action_receipt_ref is not None:
            legacy_external_action_reason_refs = tuple(self.reason_refs)
            if (
                status == GovernedExternalOperationContractStatus.failed
                and legacy_external_action_reason_refs
                == (
                    "reason-ref:governed-external-operation:contract-preparation-failed",
                )
            ):
                legacy_external_action_reason_refs = ()
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
                    reason_refs=(
                        self.external_action_reason_refs
                        if self.external_action_reason_refs is not None
                        else legacy_external_action_reason_refs
                    ),
                    replayed=self.replayed,
                )
            except ValueError as exc:
                raise ValueError(
                    "GOVERNED_EXTERNAL_OPERATION_EXTERNAL_RECEIPT_REF_MISMATCH"
                ) from exc
        expected_receipt_ref = stable_governed_browser_ref(
            "receipt-ref:governed-external-operation",
            _external_operation_receipt_identity_payload(self),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECEIPT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_external_operation_receipt",
        )
        return self


class ExactGovernedExternalOperationResult(BaseModel):
    receipt: GovernedExternalOperationReceipt
    contract: ExactGovernedExternalOperationContract | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactGovernedExternalOperationResult":
        ready = (
            self.receipt.status
            == GovernedExternalOperationContractStatus.contract_ready.value
        )
        if ready != (self.contract is not None):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_CONTRACT_PROJECTION_MISMATCH")
        if self.contract is not None and (
            self.contract.contract_ref != self.receipt.contract_ref
            or self.contract.operation != self.receipt.operation
            or self.contract.target_ref != self.receipt.target_ref
            or self.contract.operation_authority_ref
            != self.receipt.operation_authority_ref
            or self.contract.operation_input_ref != self.receipt.operation_input_ref
            or self.contract.rollback_ref != self.receipt.rollback_ref
            or self.contract.reconciliation_ref != self.receipt.reconciliation_ref
        ):
            raise ValueError("GOVERNED_EXTERNAL_OPERATION_RECEIPT_SCOPE_MISMATCH")
        return self


class ExactGovernedExternalOperationService:
    """Prepare an exact plan-only contract through every shared gate."""

    def __init__(
        self,
        *,
        registry: GovernedExternalOperationRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._clock = clock

    def prepare(
        self,
        contract_request: ExactGovernedExternalOperationRequest,
    ) -> ExactGovernedExternalOperationResult:
        request = ExactGovernedExternalOperationRequest.model_validate(
            contract_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        if recipe is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-external-operation:recipe-unregistered",
            )
        if (
            request.operation,
            request.contract_ref,
            request.target_ref,
        ) != (
            recipe.operation,
            recipe.contract_ref,
            recipe.target_ref,
        ):
            return _preflight_blocked(
                request,
                "reason-ref:governed-external-operation:request-scope-mismatch",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)
        kernel_execution = _operation_kernel_execution(
            execution,
            recipe_ref=recipe.recipe_ref,
        )
        try:
            replay = self._kernel.replay_if_terminal(kernel_execution)
            prior_start = self._kernel.recover_if_prior_start(kernel_execution)
        except ExternalActionTransactionConflict:
            return _preflight_blocked(
                request,
                "reason-ref:governed-external-operation:idempotency-conflict",
            )
        if replay is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=replay,
                contract=None,
            )
        if prior_start is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=prior_start,
                contract=None,
            )
        current_time, clock_reason = _read_clock(self._clock)
        if clock_reason is not None:
            return _preflight_blocked(request, clock_reason)
        assert current_time is not None
        if current_time < recipe.created_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-external-operation:recipe-not-yet-valid",
            )
        if current_time >= recipe.expires_at:
            return _preflight_blocked(
                request,
                "reason-ref:governed-external-operation:recipe-expired",
            )
        captured: dict[str, ExactGovernedExternalOperationContract] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            dispatch_time, dispatch_clock_reason = _read_clock(self._clock)
            if dispatch_clock_reason is not None:
                return _failed_dispatch(
                    dispatched_request,
                    "trusted-clock-invalid",
                )
            assert dispatch_time is not None
            if (
                dispatched_request.binding.binding_ref != recipe.binding_ref
                or not recipe.created_at <= dispatch_time < recipe.expires_at
            ):
                return _failed_dispatch(
                    dispatched_request,
                    "contract-revalidation-failed",
                )
            contract = _build_exact_contract(recipe)
            captured["contract"] = contract
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[
                    recipe.contract_ref,
                    recipe.operation_authority_ref,
                    recipe.operation_input_ref,
                    recipe.rollback_ref,
                    recipe.reconciliation_ref,
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
                "reason-ref:governed-external-operation:idempotency-conflict",
            )
        contract = captured.get("contract")
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            contract = None
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            contract=contract,
        )


def _operation_kernel_execution(
    request: ExternalActionExecutionRequest,
    *,
    recipe_ref: str,
) -> ExternalActionExecutionRequest:
    return ExternalActionExecutionRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-external-operation",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe_ref,
                },
            ),
        }
    )


def _recipe_scope_reason(
    recipe: GovernedExternalOperationRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    required_resources = {
        recipe.operation_authority_ref,
        recipe.operation_input_ref,
        recipe.rollback_ref,
        recipe.reconciliation_ref,
        recipe.contract_ref,
    }
    if recipe.legal_instrument_ref is not None:
        required_resources.add(recipe.legal_instrument_ref)
    if recipe.delete_resource_ref is not None:
        required_resources.add(recipe.delete_resource_ref)
    bound_authority_refs = tuple(
        ref
        for ref in binding.resource_refs
        if ref.startswith(_OPERATION_AUTHORITY_PREFIX)
    )
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-external-operation:binding-mismatch",
        ),
        (
            recipe.origin_ref == binding.origin_ref,
            "reason-ref:governed-external-operation:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-external-operation:snapshot-mismatch",
        ),
        (
            recipe.target_ref == binding.recipient_ref,
            "reason-ref:governed-external-operation:target-mismatch",
        ),
        (
            recipe.schema_ref == binding.field_schema_ref,
            "reason-ref:governed-external-operation:schema-mismatch",
        ),
        (
            tuple(recipe.artifact_refs) == binding.artifact_refs,
            "reason-ref:governed-external-operation:artifact-mismatch",
        ),
        (
            binding.authority_capability
            == _required_capability(GovernedExternalOperation(recipe.operation)).value,
            "reason-ref:governed-external-operation:capability-mismatch",
        ),
        (
            bound_authority_refs == (recipe.operation_authority_ref,),
            "reason-ref:governed-external-operation:operation-authority-mismatch",
        ),
        (
            set(binding.resource_refs) == required_resources,
            "reason-ref:governed-external-operation:resource-scope-mismatch",
        ),
        (
            binding.human_present,
            "reason-ref:governed-external-operation:human-presence-required",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-external-operation:real-targets-inactive",
        ),
        (
            recipe.expires_at <= binding.start_deadline,
            "reason-ref:governed-external-operation:recipe-outlives-deadline",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _build_exact_contract(
    recipe: GovernedExternalOperationRecipe,
) -> ExactGovernedExternalOperationContract:
    return ExactGovernedExternalOperationContract(
        contract_ref=recipe.contract_ref,
        operation_authority_ref=recipe.operation_authority_ref,
        binding_ref=recipe.binding_ref,
        operation=recipe.operation,
        required_capability=recipe.required_capability,
        origin_ref=recipe.origin_ref,
        page_snapshot_ref=recipe.page_snapshot_ref,
        target_ref=recipe.target_ref,
        operation_input_ref=recipe.operation_input_ref,
        schema_ref=recipe.schema_ref,
        artifact_refs=recipe.artifact_refs,
        legal_instrument_ref=recipe.legal_instrument_ref,
        legal_decision=recipe.legal_decision,
        delete_resource_ref=recipe.delete_resource_ref,
        reversibility=recipe.reversibility,
        rollback_ref=recipe.rollback_ref,
        reconciliation_ref=recipe.reconciliation_ref,
        expires_at=recipe.expires_at,
    )


def _read_clock(
    clock: Callable[[], datetime],
) -> tuple[datetime | None, str | None]:
    try:
        current_time = clock()
    except Exception:
        return None, "reason-ref:governed-external-operation:trusted-clock-failed"
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        return None, "reason-ref:governed-external-operation:trusted-clock-invalid"
    try:
        return current_time.astimezone(timezone.utc), None
    except Exception:
        return None, "reason-ref:governed-external-operation:trusted-clock-invalid"


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
    suffix: str,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                f"evidence-ref:governed-external-operation:{suffix}",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactGovernedExternalOperationRequest,
    reason_ref: str,
) -> ExactGovernedExternalOperationResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "contract_ref": request.contract_ref,
        "operation": request.operation,
        "target_ref": request.target_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": GovernedExternalOperationContractStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        _external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(
                receipt_ref="receipt-ref:governed-external-operation:pending",
                **payload,
            )
        ),
    )
    return ExactGovernedExternalOperationResult(
        receipt=GovernedExternalOperationReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactGovernedExternalOperationRequest,
    recipe: GovernedExternalOperationRecipe,
    external_receipt: ExternalActionReceipt,
    contract: ExactGovernedExternalOperationContract | None,
) -> ExactGovernedExternalOperationResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed and state == ExternalActionState.succeeded:
        status = GovernedExternalOperationContractStatus.replayed_content_free
    elif state == ExternalActionState.succeeded:
        status = GovernedExternalOperationContractStatus.contract_ready
    else:
        status = {
            ExternalActionState.blocked: (
                GovernedExternalOperationContractStatus.transaction_blocked
            ),
            ExternalActionState.failed: GovernedExternalOperationContractStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                GovernedExternalOperationContractStatus.outcome_ambiguous
            ),
            ExternalActionState.started: (
                GovernedExternalOperationContractStatus.outcome_ambiguous
            ),
            ExternalActionState.prepared: (
                GovernedExternalOperationContractStatus.outcome_ambiguous
            ),
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = [
            "reason-ref:governed-external-operation:contract-preparation-failed"
        ]
    payload = {
        "recipe_ref": recipe.recipe_ref,
        "contract_ref": recipe.contract_ref,
        "operation": recipe.operation,
        "target_ref": recipe.target_ref,
        "operation_authority_ref": recipe.operation_authority_ref,
        "operation_input_ref": recipe.operation_input_ref,
        "rollback_ref": recipe.rollback_ref,
        "reconciliation_ref": recipe.reconciliation_ref,
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
        "external_action_reason_refs": tuple(external_receipt.reason_refs),
        "evidence_refs": list(external_receipt.evidence_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-external-operation",
        _external_operation_receipt_identity_payload(
            GovernedExternalOperationReceipt.model_construct(
                receipt_ref="receipt-ref:governed-external-operation:pending",
                **payload,
            )
        ),
    )
    return ExactGovernedExternalOperationResult(
        receipt=GovernedExternalOperationReceipt(
            receipt_ref=receipt_ref,
            **payload,
        ),
        contract=contract,
    )
