from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.agent_runtime.contracts import _validate_safe_ref, _validate_safe_text


class HandoffEnvelope(BaseModel):
    handoff_ref: str
    source_turn_ref: str | None = None
    source_run_ref: str | None = None
    source_capability_ref: str
    target_capability_ref: str
    objective_ref: str
    safe_objective_summary: str = Field(..., min_length=1)
    allowed_authority_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    expected_output_schema_ref: str
    timeout_policy_ref: str
    idempotency_ref: str
    rollback_or_safe_disable_ref: str
    human_review_required: bool = True
    execution_authorized: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    connector_write_authorized: bool = False

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator(
        "handoff_ref",
        "source_turn_ref",
        "source_run_ref",
        "source_capability_ref",
        "target_capability_ref",
        "objective_ref",
        "expected_output_schema_ref",
        "timeout_policy_ref",
        "idempotency_ref",
        "rollback_or_safe_disable_ref",
    )
    @classmethod
    def validate_ref_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value
        _validate_safe_ref(value, "handoff_ref")
        return value

    @field_validator("allowed_authority_refs", "blocked_authority_refs", "evidence_refs", "receipt_refs")
    @classmethod
    def validate_ref_lists(cls, values: list[str]) -> list[str]:
        for value in values:
            _validate_safe_ref(value, "handoff_ref")
        return values

    @field_validator("safe_objective_summary")
    @classmethod
    def validate_safe_objective_summary(cls, value: str) -> str:
        _validate_safe_text(value, "safe_objective_summary")
        return value

    @model_validator(mode="after")
    def validate_handoff_boundary(self) -> "HandoffEnvelope":
        if not self.source_turn_ref and not self.source_run_ref:
            raise ValueError("HANDOFF_SOURCE_REF_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("HANDOFF_BLOCKED_AUTHORITY_REFS_REQUIRED")
        enabled = [
            name
            for name, value in {
                "execution_authorized": self.execution_authorized,
                "memory_write_authorized": self.memory_write_authorized,
                "context_injection_authorized": self.context_injection_authorized,
                "connector_write_authorized": self.connector_write_authorized,
            }.items()
            if value
        ]
        if enabled:
            raise ValueError(f"HANDOFF_EXECUTION_AUTHORITY_DENIED: {', '.join(enabled)}")
        return self
