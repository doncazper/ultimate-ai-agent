"""Registered exact POST-form schemas and inactive validation plans.

Queue 01 item 07 proves schema registration, exact field/value binding, and
the existing governed transaction sequence through deterministic injected
local validation. It does not materialize a request body, start a browser,
submit a form, perform a network call, or activate a real external target.
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
    StrictInt,
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

from .browser_actions import (
    ExactBrowserActionReceipt,
    ExactBrowserActionStatus,
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


GOVERNED_POST_FORM_SCHEMA_CONTRACT_REF = (
    "contract-ref:governed-browser-post-form-schema:v1"
)
GOVERNED_POST_FORM_RECIPE_CONTRACT_REF = (
    "contract-ref:governed-browser-post-form-recipe:v1"
)
MAX_REGISTERED_POST_FORM_FIELDS = 5
MAX_POST_FORM_FIELD_BYTES = 4096
MAX_POST_FORM_TOTAL_BYTES = 16384

_BROKER_ADDED_FIELDS = {
    "allowed",
    "profile_ref",
    "profile_ephemeral",
    "ordinary_profile_used",
    "external_mutation_enabled",
    "content_untrusted",
    "web_content_instruction_use_allowed",
}
_POST_FORM_TRANSPORT_FIELDS = {
    "recipe_ref",
    "plan_ref",
    "binding_ref",
    "schema_ref",
    "origin_ref",
    "page_snapshot_ref",
    "source_observation_ref",
    "source_safe_url_ref",
    "destination_origin_ref",
    "destination_safe_url_ref",
    "element_ref",
    "visibility_proof_ref",
    "field_value_bindings",
    "operation",
    "method",
    "encoding",
    "target_visible",
    "same_origin_verified",
    "registered_schema_verified",
    "field_bindings_verified",
    "plan_generated",
    "source_observation_content_untrusted",
    "web_content_instruction_use_allowed",
    "browser_session_started",
    "navigation_performed",
    "form_fill_performed",
    "form_submission_performed",
    "field_values_resolved",
    "request_body_materialized",
    "request_body_included",
    "authenticated_profile_used",
    "cookies_or_credentials_used",
    "download_or_upload_performed",
    "network_call_performed",
    "external_mutation_performed",
    "side_effects_performed",
}


class GovernedPostFormValueKind(str, Enum):
    opaque_text_ref = "opaque_text_ref"
    opaque_choice_ref = "opaque_choice_ref"
    opaque_boolean_ref = "opaque_boolean_ref"


class GovernedPostFormFieldSchema(BaseModel):
    """One safe-ref-only field definition in a registered POST schema."""

    field_ref: str = Field(..., min_length=1, max_length=240)
    value_kind: GovernedPostFormValueKind
    required: StrictBool = True
    max_encoded_bytes: StrictInt = Field(..., ge=1, le=MAX_POST_FORM_FIELD_BYTES)
    multiple_values_allowed: Literal[False] = False
    raw_field_name_stored: Literal[False] = False
    raw_default_value_stored: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_field(self) -> "GovernedPostFormFieldSchema":
        validate_task_ref(self.field_ref, "field_ref")
        if not self.field_ref.startswith("form-field-ref:"):
            raise ValueError("GOVERNED_POST_FORM_FIELD_REF_REQUIRED")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_post_form_field_schema",
        )
        return self


class GovernedPostFormFieldValueBinding(BaseModel):
    """One exact field-to-opaque-value mapping; no raw value is accepted."""

    field_ref: str = Field(..., min_length=1, max_length=240)
    field_value_ref: str = Field(..., min_length=1, max_length=240)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_binding(self) -> "GovernedPostFormFieldValueBinding":
        validate_task_ref(self.field_ref, "field_ref")
        validate_task_ref(self.field_value_ref, "field_value_ref")
        if not self.field_ref.startswith("form-field-ref:"):
            raise ValueError("GOVERNED_POST_FORM_FIELD_REF_REQUIRED")
        if not self.field_value_ref.startswith("form-field-value-ref:"):
            raise ValueError("GOVERNED_POST_FORM_OPAQUE_VALUE_REF_REQUIRED")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_post_form_field_value_binding",
        )
        return self


class GovernedPostFormSchema(BaseModel):
    """Immutable exact schema selected from a trusted local registry."""

    schema_version: Literal["uaa-governed-browser-post-form-schema.v1"] = (
        "uaa-governed-browser-post-form-schema.v1"
    )
    contract_ref: Literal["contract-ref:governed-browser-post-form-schema:v1"] = (
        GOVERNED_POST_FORM_SCHEMA_CONTRACT_REF
    )
    schema_ref: str = Field(..., min_length=1, max_length=240)
    exact_origin_ref: str = Field(..., min_length=1, max_length=240)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    source_observation_ref: str = Field(..., min_length=1, max_length=240)
    source_safe_url_ref: str = Field(..., min_length=1, max_length=240)
    destination_origin_ref: str = Field(..., min_length=1, max_length=240)
    destination_safe_url_ref: str = Field(..., min_length=1, max_length=240)
    element_ref: str = Field(..., min_length=1, max_length=240)
    visibility_proof_ref: str = Field(..., min_length=1, max_length=240)
    fields: tuple[GovernedPostFormFieldSchema, ...] = Field(
        ..., min_length=1, max_length=MAX_REGISTERED_POST_FORM_FIELDS
    )
    max_total_encoded_bytes: StrictInt = Field(..., ge=1, le=MAX_POST_FORM_TOTAL_BYTES)
    method: Literal["POST"] = "POST"
    encoding: Literal["application/x-www-form-urlencoded"] = (
        "application/x-www-form-urlencoded"
    )
    registered_schema_required: Literal[True] = True
    source_observation_required: Literal[True] = True
    source_observation_content_untrusted: Literal[True] = True
    visible_target_required: Literal[True] = True
    same_origin_required: Literal[True] = True
    exact_field_set_required: Literal[True] = True
    raw_field_names_allowed: Literal[False] = False
    raw_field_values_allowed: Literal[False] = False
    request_body_materialization_allowed: Literal[False] = False
    browser_session_allowed: Literal[False] = False
    form_submission_allowed: Literal[False] = False
    authenticated_session_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_schema(self) -> "GovernedPostFormSchema":
        for value, label in (
            (self.contract_ref, "contract_ref"),
            (self.schema_ref, "schema_ref"),
            (self.exact_origin_ref, "exact_origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_origin_ref, "destination_origin_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
        ):
            validate_task_ref(value, label)
        if not self.schema_ref.startswith(
            "field-schema-ref:governed-browser-post-form:"
        ):
            raise ValueError("GOVERNED_POST_FORM_SCHEMA_REF_REQUIRED")
        if not self.source_observation_ref.startswith("browser-observe-output:"):
            raise ValueError("GOVERNED_POST_FORM_OBSERVATION_REF_REQUIRED")
        if not self.source_safe_url_ref.startswith("browser-url:"):
            raise ValueError("GOVERNED_POST_FORM_SOURCE_URL_REF_REQUIRED")
        if not self.destination_safe_url_ref.startswith("browser-url:"):
            raise ValueError("GOVERNED_POST_FORM_DESTINATION_URL_REF_REQUIRED")
        if self.destination_origin_ref != self.exact_origin_ref:
            raise ValueError("GOVERNED_POST_FORM_CROSS_ORIGIN_DENIED")
        field_refs = [field.field_ref for field in self.fields]
        if len(set(field_refs)) != len(field_refs):
            raise ValueError("GOVERNED_POST_FORM_DUPLICATE_FIELD_REF")
        if self.max_total_encoded_bytes > sum(
            field.max_encoded_bytes for field in self.fields
        ):
            raise ValueError("GOVERNED_POST_FORM_TOTAL_LIMIT_EXCEEDS_FIELD_LIMITS")
        expected_schema_ref = stable_governed_browser_ref(
            "field-schema-ref:governed-browser-post-form",
            self.model_dump(mode="json", exclude={"schema_ref"}),
        )
        if self.schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_POST_FORM_SCHEMA_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_post_form_schema",
        )
        return self

    @property
    def field_refs(self) -> tuple[str, ...]:
        return tuple(field.field_ref for field in self.fields)


class GovernedPostFormRecipe(BaseModel):
    """One exact registered POST plan bound to one authority binding."""

    schema_version: Literal["uaa-governed-browser-post-form-recipe.v1"] = (
        "uaa-governed-browser-post-form-recipe.v1"
    )
    contract_ref: Literal["contract-ref:governed-browser-post-form-recipe:v1"] = (
        GOVERNED_POST_FORM_RECIPE_CONTRACT_REF
    )
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    plan_ref: str = Field(..., min_length=1, max_length=240)
    binding_ref: str = Field(..., min_length=1, max_length=240)
    schema_ref: str = Field(..., min_length=1, max_length=240)
    field_value_bindings: tuple[GovernedPostFormFieldValueBinding, ...] = Field(
        ..., min_length=1, max_length=MAX_REGISTERED_POST_FORM_FIELDS
    )
    operation: Literal["registered_post_form"] = "registered_post_form"
    method: Literal["POST"] = "POST"
    exact_capability: Literal[AuthorityCapability.form_fill] = (
        AuthorityCapability.form_fill
    )
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    request_body_materialization_allowed: Literal[False] = False
    browser_session_allowed: Literal[False] = False
    form_submission_allowed: Literal[False] = False
    authenticated_session_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedPostFormRecipe":
        for value, label in (
            (self.contract_ref, "contract_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.binding_ref, "binding_ref"),
            (self.schema_ref, "schema_ref"),
        ):
            validate_task_ref(value, label)
        if not self.plan_ref.startswith("browser-action-plan:"):
            raise ValueError("GOVERNED_POST_FORM_PLAN_REF_REQUIRED")
        field_refs = [binding.field_ref for binding in self.field_value_bindings]
        value_refs = [binding.field_value_ref for binding in self.field_value_bindings]
        if len(set(field_refs)) != len(field_refs):
            raise ValueError("GOVERNED_POST_FORM_DUPLICATE_FIELD_BINDING")
        if len(set(value_refs)) != len(value_refs):
            raise ValueError("GOVERNED_POST_FORM_DUPLICATE_VALUE_REF")
        expected_plan_ref = stable_governed_browser_ref(
            "browser-action-plan",
            self.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
        )
        if self.plan_ref != expected_plan_ref:
            raise ValueError("GOVERNED_POST_FORM_PLAN_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "browser-post-form-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_POST_FORM_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_post_form_recipe",
        )
        return self


class GovernedPostFormSchemaRegistry:
    """Immutable registry of exact POST schemas."""

    def __init__(self, schemas: Sequence[GovernedPostFormSchema]) -> None:
        validated = tuple(
            GovernedPostFormSchema.model_validate(schema.model_dump(mode="json"))
            for schema in schemas
        )
        if not validated:
            raise ValueError("GOVERNED_POST_FORM_SCHEMA_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_POST_FORM_SCHEMA_REGISTRY_TOO_LARGE")
        by_ref = {schema.schema_ref: schema for schema in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_POST_FORM_SCHEMA_REF_DUPLICATE")
        self._schemas = by_ref

    def resolve(self, schema_ref: str) -> GovernedPostFormSchema | None:
        return self._schemas.get(schema_ref)


class GovernedPostFormRecipeRegistry:
    """Immutable recipe registry coupled to the exact schema registry."""

    def __init__(
        self,
        *,
        recipes: Sequence[GovernedPostFormRecipe],
        schema_registry: GovernedPostFormSchemaRegistry,
    ) -> None:
        validated = tuple(
            GovernedPostFormRecipe.model_validate(recipe.model_dump(mode="json"))
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_POST_FORM_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 64:
            raise ValueError("GOVERNED_POST_FORM_RECIPE_REGISTRY_TOO_LARGE")
        for recipe in validated:
            schema = schema_registry.resolve(recipe.schema_ref)
            if schema is None:
                raise ValueError("GOVERNED_POST_FORM_SCHEMA_UNREGISTERED")
            _validate_recipe_field_set(recipe, schema)
        by_ref = {recipe.recipe_ref: recipe for recipe in validated}
        if len(by_ref) != len(validated):
            raise ValueError("GOVERNED_POST_FORM_RECIPE_REF_DUPLICATE")
        self._recipes = by_ref
        self._schemas = schema_registry

    def resolve(
        self, recipe_ref: str
    ) -> tuple[GovernedPostFormRecipe, GovernedPostFormSchema] | None:
        recipe = self._recipes.get(recipe_ref)
        if recipe is None:
            return None
        schema = self._schemas.resolve(recipe.schema_ref)
        if schema is None:
            return None
        return recipe, schema


def build_governed_post_form_schema(
    *,
    exact_origin_ref: str,
    page_snapshot_ref: str,
    source_observation_ref: str,
    source_safe_url_ref: str,
    destination_origin_ref: str,
    destination_safe_url_ref: str,
    element_ref: str,
    visibility_proof_ref: str,
    fields: Sequence[GovernedPostFormFieldSchema],
    max_total_encoded_bytes: int,
) -> GovernedPostFormSchema:
    """Build a content-derived exact schema without granting action authority."""

    payload = {
        "exact_origin_ref": exact_origin_ref,
        "page_snapshot_ref": page_snapshot_ref,
        "source_observation_ref": source_observation_ref,
        "source_safe_url_ref": source_safe_url_ref,
        "destination_origin_ref": destination_origin_ref,
        "destination_safe_url_ref": destination_safe_url_ref,
        "element_ref": element_ref,
        "visibility_proof_ref": visibility_proof_ref,
        "fields": tuple(fields),
        "max_total_encoded_bytes": max_total_encoded_bytes,
    }
    provisional = GovernedPostFormSchema.model_construct(
        schema_ref="field-schema-ref:governed-browser-post-form:pending",
        **payload,
    )
    schema_ref = stable_governed_browser_ref(
        "field-schema-ref:governed-browser-post-form",
        provisional.model_dump(mode="json", exclude={"schema_ref"}),
    )
    return GovernedPostFormSchema(schema_ref=schema_ref, **payload)


def build_governed_post_form_recipe(
    request: ExternalActionExecutionRequest,
    *,
    schema: GovernedPostFormSchema,
    field_value_bindings: Sequence[GovernedPostFormFieldValueBinding],
) -> GovernedPostFormRecipe:
    """Build one exact inactive recipe from already authority-bound safe refs."""

    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    schema = GovernedPostFormSchema.model_validate(schema.model_dump(mode="json"))
    binding = execution.binding
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_POST_FORM_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != AuthorityCapability.form_fill.value:
        raise ValueError("GOVERNED_POST_FORM_EXACT_CAPABILITY_MISMATCH")
    if binding.field_schema_ref != schema.schema_ref:
        raise ValueError("GOVERNED_POST_FORM_SCHEMA_BINDING_MISMATCH")
    if (
        binding.origin_ref != schema.exact_origin_ref
        or binding.origin_ref != schema.destination_origin_ref
    ):
        raise ValueError("GOVERNED_POST_FORM_ORIGIN_BINDING_MISMATCH")
    if binding.page_snapshot_ref != schema.page_snapshot_ref:
        raise ValueError("GOVERNED_POST_FORM_SNAPSHOT_BINDING_MISMATCH")
    values = tuple(
        GovernedPostFormFieldValueBinding.model_validate(value.model_dump(mode="json"))
        for value in field_value_bindings
    )
    payload = {
        "binding_ref": binding.binding_ref,
        "schema_ref": schema.schema_ref,
        "field_value_bindings": values,
    }
    provisional_plan = GovernedPostFormRecipe.model_construct(
        recipe_ref="browser-post-form-recipe-ref:governed-browser:pending",
        plan_ref="browser-action-plan:pending",
        **payload,
    )
    plan_ref = stable_governed_browser_ref(
        "browser-action-plan",
        provisional_plan.model_dump(mode="json", exclude={"recipe_ref", "plan_ref"}),
    )
    provisional_recipe = GovernedPostFormRecipe.model_construct(
        recipe_ref="browser-post-form-recipe-ref:governed-browser:pending",
        plan_ref=plan_ref,
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "browser-post-form-recipe-ref:governed-browser",
        provisional_recipe.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    recipe = GovernedPostFormRecipe(
        recipe_ref=recipe_ref,
        plan_ref=plan_ref,
        **payload,
    )
    _validate_recipe_field_set(recipe, schema)
    required_resources = {
        schema.source_observation_ref,
        schema.source_safe_url_ref,
        schema.destination_safe_url_ref,
        schema.element_ref,
        schema.visibility_proof_ref,
        *schema.field_refs,
        *(item.field_value_ref for item in recipe.field_value_bindings),
    }
    if not required_resources.issubset(set(binding.resource_refs)):
        raise ValueError("GOVERNED_POST_FORM_RESOURCE_NOT_AUTHORITY_BOUND")
    return recipe


class ExactPostFormDryRunTransportResult(BaseModel):
    """Strict safe-ref-only result from the injected POST planner."""

    recipe_ref: str
    plan_ref: str
    binding_ref: str
    schema_ref: str
    origin_ref: str
    page_snapshot_ref: str
    source_observation_ref: str
    source_safe_url_ref: str
    destination_origin_ref: str
    destination_safe_url_ref: str
    element_ref: str
    visibility_proof_ref: str
    field_value_bindings: tuple[GovernedPostFormFieldValueBinding, ...] = Field(
        ..., min_length=1, max_length=MAX_REGISTERED_POST_FORM_FIELDS
    )
    operation: Literal["registered_post_form"] = "registered_post_form"
    method: Literal["POST"] = "POST"
    encoding: Literal["application/x-www-form-urlencoded"] = (
        "application/x-www-form-urlencoded"
    )
    target_visible: Literal[True]
    same_origin_verified: Literal[True]
    registered_schema_verified: Literal[True]
    field_bindings_verified: Literal[True]
    plan_generated: Literal[True]
    source_observation_content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False
    browser_session_started: Literal[False] = False
    navigation_performed: Literal[False] = False
    form_fill_performed: Literal[False] = False
    form_submission_performed: Literal[False] = False
    field_values_resolved: Literal[False] = False
    request_body_materialized: Literal[False] = False
    request_body_included: Literal[False] = False
    authenticated_profile_used: Literal[False] = False
    cookies_or_credentials_used: Literal[False] = False
    download_or_upload_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    side_effects_performed: tuple[()] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_transport(self) -> "ExactPostFormDryRunTransportResult":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.plan_ref, "plan_ref"),
            (self.binding_ref, "binding_ref"),
            (self.schema_ref, "schema_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_origin_ref, "destination_origin_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
        ):
            validate_task_ref(value, label)
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_or_credentials_used"}),
            "governed_post_form_transport_result",
        )
        return self


class ExactPostFormPlan(BaseModel):
    """Safe-ref-only inactive POST plan returned after all checks pass."""

    schema_version: Literal["uaa-governed-browser-post-form-plan.v1"] = (
        "uaa-governed-browser-post-form-plan.v1"
    )
    projection_ref: str
    plan_ref: str
    recipe_ref: str
    binding_ref: str
    schema_ref: str
    origin_ref: str
    page_snapshot_ref: str
    source_observation_ref: str
    source_safe_url_ref: str
    destination_safe_url_ref: str
    element_ref: str
    visibility_proof_ref: str
    field_value_bindings: tuple[GovernedPostFormFieldValueBinding, ...] = Field(
        ..., min_length=1, max_length=MAX_REGISTERED_POST_FORM_FIELDS
    )
    operation: Literal["registered_post_form"] = "registered_post_form"
    method: Literal["POST"] = "POST"
    encoding: Literal["application/x-www-form-urlencoded"] = (
        "application/x-www-form-urlencoded"
    )
    profile_ref: str
    target_visible: Literal[True]
    same_origin_verified: Literal[True]
    registered_schema_verified: Literal[True]
    field_bindings_verified: Literal[True]
    plan_generated: Literal[True]
    injected_local_validation: Literal[True] = True
    browser_session_started: Literal[False] = False
    navigation_performed: Literal[False] = False
    form_fill_performed: Literal[False] = False
    form_submission_performed: Literal[False] = False
    field_values_resolved: Literal[False] = False
    request_body_materialized: Literal[False] = False
    authenticated_profile_used: Literal[False] = False
    download_or_upload_performed: Literal[False] = False
    action_execution_performed: Literal[False] = False
    live_network_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    content_untrusted: Literal[True] = True
    web_content_instruction_use_allowed: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_plan(self) -> "ExactPostFormPlan":
        for value, label in (
            (self.projection_ref, "projection_ref"),
            (self.plan_ref, "plan_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.schema_ref, "schema_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.source_observation_ref, "source_observation_ref"),
            (self.source_safe_url_ref, "source_safe_url_ref"),
            (self.destination_safe_url_ref, "destination_safe_url_ref"),
            (self.element_ref, "element_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.profile_ref, "profile_ref"),
        ):
            validate_task_ref(value, label)
        expected_projection_ref = stable_governed_browser_ref(
            "browser-post-form-plan-projection-ref:governed-browser",
            self.model_dump(mode="json", exclude={"projection_ref"}),
        )
        if self.projection_ref != expected_projection_ref:
            raise ValueError(
                "GOVERNED_POST_FORM_PLAN_PROJECTION_REF_MISMATCH"
            )
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_post_form_plan",
        )
        return self


class ExactPostFormRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactPostFormRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        return self


class ExactPostFormResult(BaseModel):
    receipt: ExactBrowserActionReceipt
    plan: ExactPostFormPlan | None = None
    raw_gateway_result_returned: Literal[False] = False
    raw_transport_result_returned: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactPostFormResult":
        if not self.receipt.receipt_ref.startswith(
            "receipt-ref:governed-post-form:"
        ):
            raise ValueError("GOVERNED_POST_FORM_RESULT_RECEIPT_KIND_MISMATCH")
        if self.receipt.status == ExactBrowserActionStatus.plan_ready.value:
            if self.plan is None:
                raise ValueError("GOVERNED_POST_FORM_PLAN_REQUIRED")
            if (
                self.plan.recipe_ref != self.receipt.recipe_ref
                or self.plan.binding_ref != self.receipt.binding_ref
                or tuple(self.receipt.evidence_refs)
                != (self.plan.plan_ref, self.plan.projection_ref)
            ):
                raise ValueError("GOVERNED_POST_FORM_PLAN_RECEIPT_MISMATCH")
        elif self.plan is not None:
            raise ValueError("GOVERNED_POST_FORM_NON_SUCCESS_PLAN_DENIED")
        return self


class ExactPostFormService:
    """Validate one exact registered POST schema through all governed gates."""

    def __init__(
        self,
        *,
        registry: GovernedPostFormRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        gateway: WebAccessGateway,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._gateway = gateway

    def plan(self, form_request: ExactPostFormRequest) -> ExactPostFormResult:
        request = ExactPostFormRequest.model_validate(
            form_request.model_dump(mode="json")
        )
        execution = request.execution_request
        resolved = self._registry.resolve(request.recipe_ref)
        if resolved is None:
            return _preflight_blocked(
                request,
                "reason-ref:governed-post-form:recipe-unregistered",
            )
        recipe, schema = resolved
        scope_reason = _recipe_scope_reason(recipe, schema, execution)
        if scope_reason is not None:
            return _preflight_blocked(request, scope_reason)

        captured: dict[str, ExactPostFormPlan] = {}

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            try:
                plan = self._plan_via_gateway(
                    recipe=recipe,
                    schema=schema,
                    execution_request=dispatched_request,
                )
            except (ValidationError, ValueError, TypeError, KeyError):
                return _failed_dispatch(dispatched_request)
            captured["plan"] = plan
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=[plan.plan_ref, plan.projection_ref],
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
        recipe: GovernedPostFormRecipe,
        schema: GovernedPostFormSchema,
        execution_request: ExternalActionExecutionRequest,
    ) -> ExactPostFormPlan:
        result = self._gateway.execute(
            WebAccessRequest(
                kind=WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
                method="GET",
                authority_mode=WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN,
                network_lane=WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN,
                actor="governed_post_form_schema",
                session_id=execution_request.intent_ref,
                metadata={
                    "recipe_ref": recipe.recipe_ref,
                    "plan_ref": recipe.plan_ref,
                    "binding_ref": recipe.binding_ref,
                    "schema_ref": schema.schema_ref,
                    "safe_url_ref": schema.source_safe_url_ref,
                    "exact_origin_ref": schema.exact_origin_ref,
                    "page_snapshot_ref": schema.page_snapshot_ref,
                    "source_observation_ref": schema.source_observation_ref,
                    "source_observation_content_untrusted": True,
                    "source_safe_url_ref": schema.source_safe_url_ref,
                    "destination_origin_ref": schema.destination_origin_ref,
                    "destination_safe_url_ref": schema.destination_safe_url_ref,
                    "element_ref": schema.element_ref,
                    "visibility_proof_ref": schema.visibility_proof_ref,
                    "field_value_bindings": tuple(
                        item.model_dump(mode="json")
                        for item in recipe.field_value_bindings
                    ),
                    "operation": recipe.operation,
                    "planned_method": "POST",
                    "encoding": schema.encoding,
                    "ordinary_profile_requested": False,
                    "mutation_requested": False,
                    "web_content_instruction_use_allowed": False,
                    "browser_action_execution": False,
                    "browser_session_start": False,
                    "navigation_execution": False,
                    "click_execution": False,
                    "form_fill_execution": False,
                    "form_submission_execution": False,
                    "field_value_resolution": False,
                    "request_body_materialization": False,
                    "form_submission_performed": False,
                    "field_values_resolved": False,
                    "request_body_materialized": False,
                    "request_body": False,
                    "screenshot": False,
                    "raw_dom": False,
                    "uses_auth": False,
                    "cookies": False,
                    "download": False,
                    "upload": False,
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
            raise ValueError("GOVERNED_POST_FORM_GATEWAY_DENIED")
        payload = result.evidence_bundle.payload
        if not isinstance(payload, Mapping):
            raise ValueError("GOVERNED_POST_FORM_PAYLOAD_INVALID")
        if set(payload) - (_POST_FORM_TRANSPORT_FIELDS | _BROKER_ADDED_FIELDS):
            raise ValueError("GOVERNED_POST_FORM_UNREGISTERED_FIELD")
        transport = ExactPostFormDryRunTransportResult.model_validate(
            {key: payload[key] for key in _POST_FORM_TRANSPORT_FIELDS if key in payload}
        )
        _validate_transport_binding(transport, recipe, schema)
        if (
            payload.get("allowed") is not True
            or payload.get("profile_ephemeral") is not True
            or payload.get("ordinary_profile_used") is not False
            or payload.get("external_mutation_enabled") is not False
            or payload.get("content_untrusted") is not True
            or payload.get("web_content_instruction_use_allowed") is not False
        ):
            raise ValueError("GOVERNED_POST_FORM_BROKER_POSTURE_INVALID")
        profile_ref = payload.get("profile_ref")
        if not isinstance(profile_ref, str):
            raise ValueError("GOVERNED_POST_FORM_PROFILE_REF_REQUIRED")
        plan_payload = {
            "plan_ref": recipe.plan_ref,
            "recipe_ref": recipe.recipe_ref,
            "binding_ref": recipe.binding_ref,
            "schema_ref": schema.schema_ref,
            "origin_ref": schema.exact_origin_ref,
            "page_snapshot_ref": schema.page_snapshot_ref,
            "source_observation_ref": schema.source_observation_ref,
            "source_safe_url_ref": schema.source_safe_url_ref,
            "destination_safe_url_ref": schema.destination_safe_url_ref,
            "element_ref": schema.element_ref,
            "visibility_proof_ref": schema.visibility_proof_ref,
            "field_value_bindings": recipe.field_value_bindings,
            "profile_ref": profile_ref,
            "target_visible": transport.target_visible,
            "same_origin_verified": transport.same_origin_verified,
            "registered_schema_verified": transport.registered_schema_verified,
            "field_bindings_verified": transport.field_bindings_verified,
            "plan_generated": transport.plan_generated,
        }
        provisional = ExactPostFormPlan.model_construct(
            projection_ref=(
                "browser-post-form-plan-projection-ref:"
                "governed-browser:pending"
            ),
            **plan_payload,
        )
        projection_ref = stable_governed_browser_ref(
            "browser-post-form-plan-projection-ref:governed-browser",
            provisional.model_dump(mode="json", exclude={"projection_ref"}),
        )
        return ExactPostFormPlan(
            projection_ref=projection_ref,
            **plan_payload,
        )


def _validate_recipe_field_set(
    recipe: GovernedPostFormRecipe,
    schema: GovernedPostFormSchema,
) -> None:
    registered = set(schema.field_refs)
    provided = {item.field_ref for item in recipe.field_value_bindings}
    required = {field.field_ref for field in schema.fields if field.required}
    if not provided.issubset(registered):
        raise ValueError("GOVERNED_POST_FORM_UNREGISTERED_FIELD_BINDING")
    if not required.issubset(provided):
        raise ValueError("GOVERNED_POST_FORM_REQUIRED_FIELD_MISSING")


def _recipe_scope_reason(
    recipe: GovernedPostFormRecipe,
    schema: GovernedPostFormSchema,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    resource_refs = {
        schema.source_observation_ref,
        schema.source_safe_url_ref,
        schema.destination_safe_url_ref,
        schema.element_ref,
        schema.visibility_proof_ref,
        *schema.field_refs,
        *(item.field_value_ref for item in recipe.field_value_bindings),
    }
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-post-form:binding-mismatch",
        ),
        (
            recipe.schema_ref == binding.field_schema_ref == schema.schema_ref,
            "reason-ref:governed-post-form:schema-mismatch",
        ),
        (
            schema.exact_origin_ref
            == schema.destination_origin_ref
            == binding.origin_ref,
            "reason-ref:governed-post-form:origin-mismatch",
        ),
        (
            schema.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-post-form:snapshot-mismatch",
        ),
        (
            binding.authority_capability == AuthorityCapability.form_fill.value,
            "reason-ref:governed-post-form:capability-mismatch",
        ),
        (
            resource_refs.issubset(set(binding.resource_refs)),
            "reason-ref:governed-post-form:resource-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-post-form:real-targets-inactive",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _validate_transport_binding(
    transport: ExactPostFormDryRunTransportResult,
    recipe: GovernedPostFormRecipe,
    schema: GovernedPostFormSchema,
) -> None:
    values = (
        (transport.recipe_ref, recipe.recipe_ref),
        (transport.plan_ref, recipe.plan_ref),
        (transport.binding_ref, recipe.binding_ref),
        (transport.schema_ref, schema.schema_ref),
        (transport.origin_ref, schema.exact_origin_ref),
        (transport.page_snapshot_ref, schema.page_snapshot_ref),
        (transport.source_observation_ref, schema.source_observation_ref),
        (transport.source_safe_url_ref, schema.source_safe_url_ref),
        (transport.destination_origin_ref, schema.destination_origin_ref),
        (transport.destination_safe_url_ref, schema.destination_safe_url_ref),
        (transport.element_ref, schema.element_ref),
        (transport.visibility_proof_ref, schema.visibility_proof_ref),
        (transport.field_value_bindings, recipe.field_value_bindings),
    )
    if any(observed != expected for observed, expected in values):
        raise ValueError("GOVERNED_POST_FORM_TRANSPORT_BINDING_MISMATCH")


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                "evidence-ref:governed-post-form-plan-failed",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _preflight_blocked(
    request: ExactPostFormRequest,
    reason_ref: str,
) -> ExactPostFormResult:
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
        "receipt-ref:governed-post-form",
        governed_receipt_identity_payload(
            ExactBrowserActionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-post-form:pending",
                **payload,
            )
        ),
    )
    return ExactPostFormResult(
        receipt=ExactBrowserActionReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactPostFormRequest,
    external_receipt: ExternalActionReceipt,
    plan: ExactPostFormPlan | None,
) -> ExactPostFormResult:
    state = ExternalActionState(external_receipt.state)
    if external_receipt.replayed:
        status = ExactBrowserActionStatus.replayed_content_free
    else:
        status = {
            ExternalActionState.succeeded: ExactBrowserActionStatus.plan_ready,
            ExternalActionState.blocked: ExactBrowserActionStatus.transaction_blocked,
            ExternalActionState.failed: ExactBrowserActionStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                ExactBrowserActionStatus.outcome_ambiguous
            ),
            ExternalActionState.started: ExactBrowserActionStatus.outcome_ambiguous,
            ExternalActionState.prepared: ExactBrowserActionStatus.outcome_ambiguous,
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = ["reason-ref:governed-post-form:plan-dispatch-failed"]
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
        "receipt-ref:governed-post-form",
        governed_receipt_identity_payload(
            ExactBrowserActionReceipt.model_construct(
                receipt_ref="receipt-ref:governed-post-form:pending",
                **payload,
            )
        ),
    )
    return ExactPostFormResult(
        receipt=ExactBrowserActionReceipt(receipt_ref=receipt_ref, **payload),
        plan=plan,
    )
