from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.safe_contract_text import validate_safe_contract_text_shape


IMMUTABLE_DECOMPOSITION_SCHEMA_VERSION = "uaa-immutable-decomposition.v1"
PLAN_REVISION_SCHEMA_VERSION = "uaa-plan-revision.v1"


class PlanRevisionConflictError(ValueError):
    """Raised when replay or revision lineage does not match exactly."""


class _FrozenContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(prefix: str, value: object) -> str:
    return f"{prefix}:sha256:{hash_text(_canonical(value))}"


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} contains duplicate refs")
    for value in values:
        _validate_ref(value, field_name)


def _validate_ref(value: str, field_name: str) -> None:
    validate_task_ref(value, field_name)
    if re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_-]*(?::[A-Za-z0-9][A-Za-z0-9:_-]*)+",
        value,
    ) is None:
        raise ValueError(f"{field_name} must contain opaque safe refs")


class ImmutableDecompositionStep(_FrozenContract):
    step_ref: str
    safe_summary: str = Field(..., min_length=1, max_length=320)
    dependency_step_refs: tuple[str, ...] = Field(default=(), max_length=15)
    target_refs: tuple[str, ...] = Field(..., min_length=1, max_length=8)
    source_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    definition_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_step(self) -> "ImmutableDecompositionStep":
        _validate_ref(self.step_ref, "decomposition_step_ref")
        validate_safe_task_text(self.safe_summary, "decomposition_step_summary")
        validate_safe_contract_text_shape(
            self.safe_summary,
            "decomposition_step_summary",
        )
        for field_name in ("dependency_step_refs", "target_refs", "source_refs"):
            _validate_refs(getattr(self, field_name), field_name)
        if self.step_ref in self.dependency_step_refs:
            raise ValueError("decomposition step cannot depend on itself")
        _validate_ref(
            self.definition_fingerprint_ref,
            "decomposition_step_definition_fingerprint_ref",
        )
        expected = _fingerprint(
            "decomposition-step-definition-ref",
            {
                "step_ref": self.step_ref,
                "safe_summary": self.safe_summary,
                "dependency_step_refs": self.dependency_step_refs,
                "target_refs": self.target_refs,
                "source_refs": self.source_refs,
            },
        )
        if self.definition_fingerprint_ref != expected:
            raise ValueError("decomposition step fingerprint mismatch")
        return self


def build_immutable_decomposition_step(
    *,
    step_ref: str,
    safe_summary: str,
    dependency_step_refs: tuple[str, ...] = (),
    target_refs: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> ImmutableDecompositionStep:
    payload = {
        "step_ref": step_ref,
        "safe_summary": safe_summary,
        "dependency_step_refs": dependency_step_refs,
        "target_refs": target_refs,
        "source_refs": source_refs,
    }
    return ImmutableDecompositionStep(
        **payload,
        definition_fingerprint_ref=_fingerprint(
            "decomposition-step-definition-ref",
            payload,
        ),
    )


class ImmutableDecompositionBinding(_FrozenContract):
    schema_version: Literal["uaa-immutable-decomposition.v1"] = (
        IMMUTABLE_DECOMPOSITION_SCHEMA_VERSION
    )
    decomposition_ref: str
    intent_fingerprint_ref: str
    ordered_steps: tuple[ImmutableDecompositionStep, ...] = Field(
        ...,
        min_length=1,
        max_length=16,
    )
    decomposition_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_decomposition(self) -> "ImmutableDecompositionBinding":
        _validate_ref(self.decomposition_ref, "decomposition_ref")
        _validate_ref(self.intent_fingerprint_ref, "intent_fingerprint_ref")
        _validate_ref(
            self.decomposition_fingerprint_ref,
            "decomposition_fingerprint_ref",
        )
        step_refs = tuple(step.step_ref for step in self.ordered_steps)
        if len(step_refs) != len(set(step_refs)):
            raise ValueError("decomposition contains duplicate step refs")
        known_steps = set(step_refs)
        for step in self.ordered_steps:
            if any(ref not in known_steps for ref in step.dependency_step_refs):
                raise ValueError("decomposition dependency is missing")
        self._validate_acyclic(step_refs)
        expected = _fingerprint(
            "decomposition-fingerprint-ref",
            _decomposition_payload(self),
        )
        if self.decomposition_fingerprint_ref != expected:
            raise ValueError("decomposition fingerprint mismatch")
        return self

    def _validate_acyclic(self, step_refs: tuple[str, ...]) -> None:
        unresolved = {
            step.step_ref: set(step.dependency_step_refs)
            for step in self.ordered_steps
        }
        order = {step_ref: index for index, step_ref in enumerate(step_refs)}
        ready = sorted(
            [step_ref for step_ref, refs in unresolved.items() if not refs],
            key=order.__getitem__,
        )
        visited: list[str] = []
        while ready:
            current = ready.pop(0)
            visited.append(current)
            for step_ref, refs in unresolved.items():
                if current in refs:
                    refs.remove(current)
                    if not refs and step_ref not in visited + ready:
                        ready.append(step_ref)
                        ready.sort(key=order.__getitem__)
        if len(visited) != len(step_refs):
            raise ValueError("decomposition dependency cycle denied")


def _decomposition_payload(binding: ImmutableDecompositionBinding) -> dict[str, object]:
    return {
        "schema_version": binding.schema_version,
        "decomposition_ref": binding.decomposition_ref,
        "intent_fingerprint_ref": binding.intent_fingerprint_ref,
        "ordered_steps": [
            step.model_dump(mode="json") for step in binding.ordered_steps
        ],
    }


def build_immutable_decomposition(
    *,
    decomposition_ref: str,
    intent_fingerprint_ref: str,
    ordered_steps: tuple[ImmutableDecompositionStep, ...],
) -> ImmutableDecompositionBinding:
    payload = {
        "schema_version": IMMUTABLE_DECOMPOSITION_SCHEMA_VERSION,
        "decomposition_ref": decomposition_ref,
        "intent_fingerprint_ref": intent_fingerprint_ref,
        "ordered_steps": [step.model_dump(mode="json") for step in ordered_steps],
    }
    return ImmutableDecompositionBinding(
        decomposition_ref=decomposition_ref,
        intent_fingerprint_ref=intent_fingerprint_ref,
        ordered_steps=ordered_steps,
        decomposition_fingerprint_ref=_fingerprint(
            "decomposition-fingerprint-ref",
            payload,
        ),
    )


class PlanRevisionBinding(_FrozenContract):
    schema_version: Literal["uaa-plan-revision.v1"] = PLAN_REVISION_SCHEMA_VERSION
    lineage_ref: str
    revision_ref: str
    revision_index: int = Field(..., ge=1, le=100)
    predecessor_revision_ref: str | None = None
    predecessor_revision_fingerprint_ref: str | None = None
    reason_ref: str
    safe_reason: str = Field(..., min_length=1, max_length=320)
    decomposition: ImmutableDecompositionBinding
    revision_fingerprint_ref: str
    authority_posture: Literal["non_authoritative_plan_truth"] = (
        "non_authoritative_plan_truth"
    )
    downstream_authority_bindings_invalidated: Literal[True] = True

    @model_validator(mode="after")
    def validate_revision(self) -> "PlanRevisionBinding":
        for value, field_name in (
            (self.lineage_ref, "plan_revision_lineage_ref"),
            (self.revision_ref, "plan_revision_ref"),
            (self.reason_ref, "plan_revision_reason_ref"),
            (self.revision_fingerprint_ref, "plan_revision_fingerprint_ref"),
        ):
            _validate_ref(value, field_name)
        validate_safe_task_text(self.safe_reason, "plan_revision_safe_reason")
        validate_safe_contract_text_shape(
            self.safe_reason,
            "plan_revision_safe_reason",
        )
        if (self.predecessor_revision_ref is None) != (
            self.predecessor_revision_fingerprint_ref is None
        ):
            raise ValueError("plan revision predecessor binding is incomplete")
        if self.revision_index == 1 and self.predecessor_revision_ref is not None:
            raise ValueError("initial plan revision cannot have a predecessor")
        if self.revision_index > 1 and self.predecessor_revision_ref is None:
            raise ValueError("later plan revision requires a predecessor")
        if self.predecessor_revision_ref is not None:
            _validate_ref(
                self.predecessor_revision_ref,
                "plan_revision_predecessor_ref",
            )
            _validate_ref(
                self.predecessor_revision_fingerprint_ref or "",
                "plan_revision_predecessor_fingerprint_ref",
            )
            if self.predecessor_revision_ref == self.revision_ref:
                raise ValueError("plan revision cannot reference itself")
        expected = _fingerprint("plan-revision-fingerprint-ref", _revision_payload(self))
        if self.revision_fingerprint_ref != expected:
            raise ValueError("plan revision fingerprint mismatch")
        return self


def _revision_payload(binding: PlanRevisionBinding) -> dict[str, object]:
    return {
        "schema_version": binding.schema_version,
        "lineage_ref": binding.lineage_ref,
        "revision_ref": binding.revision_ref,
        "revision_index": binding.revision_index,
        "predecessor_revision_ref": binding.predecessor_revision_ref,
        "predecessor_revision_fingerprint_ref": (
            binding.predecessor_revision_fingerprint_ref
        ),
        "reason_ref": binding.reason_ref,
        "safe_reason": binding.safe_reason,
        "decomposition": binding.decomposition.model_dump(mode="json"),
        "authority_posture": binding.authority_posture,
        "downstream_authority_bindings_invalidated": (
            binding.downstream_authority_bindings_invalidated
        ),
    }


def build_initial_plan_revision(
    *,
    lineage_ref: str,
    revision_ref: str,
    reason_ref: str,
    safe_reason: str,
    decomposition: ImmutableDecompositionBinding,
) -> PlanRevisionBinding:
    payload = {
        "schema_version": PLAN_REVISION_SCHEMA_VERSION,
        "lineage_ref": lineage_ref,
        "revision_ref": revision_ref,
        "revision_index": 1,
        "predecessor_revision_ref": None,
        "predecessor_revision_fingerprint_ref": None,
        "reason_ref": reason_ref,
        "safe_reason": safe_reason,
        "decomposition": decomposition.model_dump(mode="json"),
        "authority_posture": "non_authoritative_plan_truth",
        "downstream_authority_bindings_invalidated": True,
    }
    return PlanRevisionBinding(
        lineage_ref=lineage_ref,
        revision_ref=revision_ref,
        revision_index=1,
        reason_ref=reason_ref,
        safe_reason=safe_reason,
        decomposition=decomposition,
        revision_fingerprint_ref=_fingerprint(
            "plan-revision-fingerprint-ref",
            payload,
        ),
    )


def build_plan_revision(
    *,
    previous: PlanRevisionBinding,
    revision_ref: str,
    reason_ref: str,
    safe_reason: str,
    decomposition: ImmutableDecompositionBinding,
) -> PlanRevisionBinding:
    if revision_ref == previous.revision_ref:
        raise PlanRevisionConflictError("new plan revision requires a new revision ref")
    if (
        decomposition.decomposition_fingerprint_ref
        == previous.decomposition.decomposition_fingerprint_ref
    ):
        raise PlanRevisionConflictError("unchanged decomposition is replay, not revision")
    payload = {
        "schema_version": PLAN_REVISION_SCHEMA_VERSION,
        "lineage_ref": previous.lineage_ref,
        "revision_ref": revision_ref,
        "revision_index": previous.revision_index + 1,
        "predecessor_revision_ref": previous.revision_ref,
        "predecessor_revision_fingerprint_ref": previous.revision_fingerprint_ref,
        "reason_ref": reason_ref,
        "safe_reason": safe_reason,
        "decomposition": decomposition.model_dump(mode="json"),
        "authority_posture": "non_authoritative_plan_truth",
        "downstream_authority_bindings_invalidated": True,
    }
    candidate = PlanRevisionBinding(
        lineage_ref=previous.lineage_ref,
        revision_ref=revision_ref,
        revision_index=previous.revision_index + 1,
        predecessor_revision_ref=previous.revision_ref,
        predecessor_revision_fingerprint_ref=previous.revision_fingerprint_ref,
        reason_ref=reason_ref,
        safe_reason=safe_reason,
        decomposition=decomposition,
        revision_fingerprint_ref=_fingerprint(
            "plan-revision-fingerprint-ref",
            payload,
        ),
    )
    validate_revision_successor(previous, candidate)
    return candidate


def validate_plan_replay(
    expected: PlanRevisionBinding,
    candidate: PlanRevisionBinding,
) -> None:
    if expected.revision_ref != candidate.revision_ref:
        raise PlanRevisionConflictError("plan replay revision ref changed")
    if expected.revision_fingerprint_ref != candidate.revision_fingerprint_ref:
        raise PlanRevisionConflictError("plan replay content changed")


def validate_revision_successor(
    previous: PlanRevisionBinding,
    candidate: PlanRevisionBinding,
) -> None:
    if candidate.lineage_ref != previous.lineage_ref:
        raise PlanRevisionConflictError("plan revision lineage changed")
    if (
        candidate.decomposition.intent_fingerprint_ref
        != previous.decomposition.intent_fingerprint_ref
    ):
        raise PlanRevisionConflictError("plan revision intent fingerprint changed")
    if candidate.revision_index != previous.revision_index + 1:
        raise PlanRevisionConflictError("plan revision index is not contiguous")
    if candidate.predecessor_revision_ref != previous.revision_ref:
        raise PlanRevisionConflictError("plan revision predecessor ref mismatch")
    if (
        candidate.predecessor_revision_fingerprint_ref
        != previous.revision_fingerprint_ref
    ):
        raise PlanRevisionConflictError("plan revision predecessor fingerprint mismatch")
    if (
        candidate.decomposition.decomposition_fingerprint_ref
        == previous.decomposition.decomposition_fingerprint_ref
    ):
        raise PlanRevisionConflictError("plan revision did not change decomposition")
