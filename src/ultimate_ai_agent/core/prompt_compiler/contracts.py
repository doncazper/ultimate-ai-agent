"""Typed contracts for deterministic prompt-module compilation."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PromptModuleKind(str, Enum):
    """A module's role in the compiled prompt."""

    system = "system"
    developer = "developer"
    skill = "skill"
    context = "context"


class PromptStabilityTier(str, Enum):
    """How frequently a module is expected to change."""

    stable_control_plane = "stable_control_plane"
    reviewed_context = "reviewed_context"
    runtime_selected = "runtime_selected"


class PromptVariableType(str, Enum):
    """Supported non-executable template variable types."""

    string = "string"
    integer = "integer"
    boolean = "boolean"


class _PromptCompilerModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=False,
        populate_by_name=True,
        frozen=True,
        hide_input_in_errors=True,
        strict=True,
    )


class PromptVariableDefinition(_PromptCompilerModel):
    """Strict declaration for a prompt template variable."""

    type: PromptVariableType
    required: bool = True
    default: str | int | bool | None = None
    allowed_values: list[str | int | bool] = Field(default_factory=list, max_length=64)
    max_length: int = Field(default=4096, ge=1, le=65_536)
    description: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def validate_default_and_allowed_values(self) -> "PromptVariableDefinition":
        if self.default is not None and not variable_value_matches_type(
            self.default, self.type
        ):
            raise ValueError("variable default does not match its declared type")
        for value in self.allowed_values:
            if not variable_value_matches_type(value, self.type):
                raise ValueError(
                    "allowed variable value does not match its declared type"
                )
            if isinstance(value, str) and len(value) > self.max_length:
                raise ValueError("allowed string variable value exceeds max_length")
        if isinstance(self.default, str) and len(self.default) > self.max_length:
            raise ValueError("string variable default exceeds max_length")
        typed_values = [(type(value), value) for value in self.allowed_values]
        if len(typed_values) != len(set(typed_values)):
            raise ValueError("duplicate allowed variable values are not allowed")
        if (
            self.default is not None
            and self.allowed_values
            and self.default not in self.allowed_values
        ):
            raise ValueError("variable default is not in allowed_values")
        return self


class PromptModuleDefinition(_PromptCompilerModel):
    """One source module and its dependency edges."""

    module_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,79}$")
    source_ref: str = Field(
        min_length=1,
        max_length=400,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,399}$",
    )
    kind: PromptModuleKind
    stability_tier: PromptStabilityTier
    dependencies: list[str] = Field(default_factory=list, max_length=128)
    required_variables: list[str] = Field(default_factory=list, max_length=128)

    @field_validator("dependencies", "required_variables")
    @classmethod
    def reject_duplicate_values(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate values are not allowed")
        return values

    @model_validator(mode="after")
    def reject_self_dependency(self) -> "PromptModuleDefinition":
        module_pattern = re.compile(r"^[a-z][a-z0-9._-]{0,79}$")
        variable_pattern = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
        if any(module_pattern.fullmatch(value) is None for value in self.dependencies):
            raise ValueError("dependency ids must use valid prompt module ids")
        if any(
            variable_pattern.fullmatch(value) is None
            for value in self.required_variables
        ):
            raise ValueError("required variable ids must use lower snake case")
        if self.module_id in self.dependencies:
            raise ValueError("a prompt module cannot depend on itself")
        return self


class PromptModuleManifest(_PromptCompilerModel):
    """Repository-owned input contract for a prompt-module dependency graph."""

    schema_ref: Literal["../../schemas/prompt_module_manifest.schema.json"] = Field(
        alias="$schema"
    )
    schema_version: Literal["uaa.prompt_module_bundle.v1"]
    bundle_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,119}$")
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    entry_module_ids: list[str] = Field(min_length=1, max_length=128)
    variables: dict[str, PromptVariableDefinition] = Field(
        default_factory=dict,
        max_length=128,
    )
    modules: list[PromptModuleDefinition] = Field(min_length=1, max_length=128)
    max_module_bytes: int = Field(default=262_144, ge=1, le=2_097_152)
    max_compiled_bytes: int = Field(default=2_097_152, ge=1, le=8_388_608)
    stable_within_run: Literal[True]

    @field_validator("entry_module_ids")
    @classmethod
    def reject_duplicate_entries(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate entry modules are not allowed")
        pattern = re.compile(r"^[a-z][a-z0-9._-]{0,79}$")
        if any(pattern.fullmatch(value) is None for value in values):
            raise ValueError("entry module ids must use valid prompt module ids")
        return values

    @field_validator("variables")
    @classmethod
    def validate_variable_names(
        cls,
        values: dict[str, PromptVariableDefinition],
    ) -> dict[str, PromptVariableDefinition]:
        pattern = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
        if any(pattern.fullmatch(name) is None for name in values):
            raise ValueError("variable names must use lower snake case")
        return values

    @model_validator(mode="after")
    def validate_module_identity(self) -> "PromptModuleManifest":
        module_ids = [module.module_id for module in self.modules]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("prompt module ids must be unique")
        return self


class PromptModuleSourceReceipt(_PromptCompilerModel):
    """Safe source metadata; source content is deliberately absent."""

    module_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,79}$")
    source_ref: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,399}$")
    source_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_bytes: int = Field(ge=0, le=2_097_152)


class PromptCompilationReceipt(_PromptCompilerModel):
    """Deterministic, redacted proof for a prompt compilation."""

    receipt_version: Literal["uaa.prompt_compilation_receipt.v1"]
    bundle_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,119}$")
    bundle_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    entry_module_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    ordered_module_ids: tuple[str, ...] = Field(min_length=1, max_length=128)
    source_receipts: tuple[PromptModuleSourceReceipt, ...] = Field(
        min_length=1,
        max_length=128,
    )
    manifest_contract_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    dependency_graph_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    variable_contract_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    supplied_variable_names: tuple[str, ...] = Field(max_length=128)
    compiled_artifact_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    compiled_bytes: int = Field(ge=0, le=8_388_608)
    raw_prompt_included: Literal[False]
    variable_values_included: Literal[False]
    runtime_model_calls: Literal[False]
    automatic_skill_loading: Literal[False]
    automatic_pr_creation: Literal[False]
    execution_authority: Literal["none"]


class PromptCompilationArtifact(_PromptCompilerModel):
    """Transient compiled content plus its safe durable receipt."""

    content: str = Field(repr=False)
    receipt: PromptCompilationReceipt


class PromptGraphInspection(_PromptCompilerModel):
    """Safe dependency metadata for review and blast-radius analysis."""

    bundle_id: str
    entry_module_ids: list[str]
    resolved_module_ids: list[str]
    manifest_contract_hash: str
    dependency_graph_hash: str
    dependencies: dict[str, list[str]]
    reverse_dependencies: dict[str, list[str]]
    impacted_module_ids: list[str] = Field(default_factory=list)


def variable_value_matches_type(value: Any, expected: PromptVariableType) -> bool:
    """Use strict scalar typing; bool is intentionally not an integer."""

    if expected is PromptVariableType.string:
        return isinstance(value, str)
    if expected is PromptVariableType.boolean:
        return isinstance(value, bool)
    return isinstance(value, int) and not isinstance(value, bool)
