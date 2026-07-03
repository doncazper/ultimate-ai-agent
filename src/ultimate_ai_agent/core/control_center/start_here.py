from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


CONTROL_CENTER_START_HERE_CONTRACT_REF = "contract-ref:control-center-start-here:v1"
CONTROL_CENTER_START_HERE_READ_MODEL_SOURCE = (
    "python_core_control_center_start_here_read_model"
)
CONTROL_CENTER_START_HERE_ROUTE_REF = "GET /control-center/start-here/summary"

_DENIED_FLAGS = (
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "browser_execution_enabled",
    "shell_subprocess_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)


class ControlCenterStartHereStep(BaseModel):
    step_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=80)
    route_ref: str = Field(..., min_length=1, max_length=120)
    backend_route_ref: str = Field(..., min_length=1, max_length=160)
    status: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    run_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    proof_ref: str = Field(..., min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self) -> "ControlCenterStartHereStep":
        validate_execution_ref(self.run_ref, "run_ref")
        validate_execution_ref(self.proof_ref, "proof_ref")
        for field_name in (
            "step_id",
            "label",
            "route_ref",
            "backend_route_ref",
            "status",
            "safe_summary",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "receipt_refs",
            "evidence_refs",
            "approval_refs",
            "memory_candidate_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class ControlCenterStartHereSummary(BaseModel):
    schema_version: str = "control-center-start-here-summary.v1"
    contract_ref: str = CONTROL_CENTER_START_HERE_CONTRACT_REF
    status: str = "implemented_backend_owned_start_here_loop_contract"
    readiness_state: str = "ready_for_one_local_governed_loop"
    local_loop_status: str = "one_governed_local_loop_available"
    source: str = CONTROL_CENTER_START_HERE_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    raw_content_included: bool = False
    ui_truth_source: str = "python_core_read_model"
    primary_run_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    primary_proof_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    action_proposal_ref: str = Field(..., min_length=1)
    route_refs: list[str] = Field(default_factory=list)
    backend_route_refs: list[str] = Field(default_factory=list)
    steps: list[ControlCenterStartHereStep] = Field(default_factory=list)
    complete_daily_loop_available: bool = True
    operator_goal: str = (
        "Complete one governed local daily loop across Today, Action Inbox, "
        "Evidence, Memory, and Trust posture."
    )
    next_safe_action: str = (
        "Open the Action Inbox proposal, inspect its run/proof/evidence refs, "
        "then review Evidence and Memory before claiming the loop outcome."
    )
    missing_prerequisite_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_summary(self) -> "ControlCenterStartHereSummary":
        _validate_common_read_model(self)
        if not self.steps:
            raise ValueError("Start Here must expose at least one loop step")
        for field_name in (
            "primary_run_ref",
            "primary_proof_ref",
            "action_proposal_ref",
        ):
            validate_execution_ref(getattr(self, field_name), field_name)
        for field_name in (
            "readiness_state",
            "local_loop_status",
            "operator_goal",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "route_refs",
            "blocked_authority_refs",
            "missing_prerequisite_refs",
            "evidence_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        _validate_text_list(self.backend_route_refs, "backend_route_refs")
        return self


def build_control_center_start_here_summary(
    *,
    today_summary: dict[str, Any],
) -> dict[str, Any]:
    runs = _runs_model(today_summary)
    bindings = [
        binding
        for binding in runs.get("surface_bindings", [])
        if isinstance(binding, dict)
    ]
    step_by_surface = {str(binding.get("surface_id")): binding for binding in bindings}
    action_proposal_ref = _action_proposal_ref(today_summary, runs)
    evidence_refs = _refs(runs.get("evidence_refs"))[:16]
    blocked_authority_refs = _refs(runs.get("blocked_authority_refs"))[:16]
    missing_prerequisite_refs = _missing_prerequisites(today_summary)
    complete_daily_loop_available = bool(bindings) and not missing_prerequisite_refs
    steps = [
        ControlCenterStartHereStep(
            step_id="start",
            label="Start Here",
            route_ref="route-ref:control-center:start",
            backend_route_ref=CONTROL_CENTER_START_HERE_ROUTE_REF,
            status="implemented_backend_owned_entrypoint",
            safe_summary=(
                "Start Here binds the local daily loop to backend-owned run, proof, "
                "evidence, action, and memory refs."
            ),
            next_safe_action="Open Action Inbox and review the proposed local loop action.",
            proof_ref=FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
            evidence_refs=evidence_refs[:8],
            receipt_refs=_refs(runs.get("receipt_refs"))[:8],
            approval_refs=_refs(runs.get("approval_refs"))[:8],
            memory_candidate_refs=_refs(runs.get("memory_candidate_refs"))[:8],
            blocked_authority_refs=blocked_authority_refs[:12],
        ),
        *[
            _start_step_from_binding(step_id, step_by_surface)
            for step_id in (
                "today",
                "action_inbox",
                "decision_receipt",
                "evidence_timeline",
                "memory_review",
                "weekly_review",
            )
        ],
    ]
    model = ControlCenterStartHereSummary(
        action_proposal_ref=action_proposal_ref,
        route_refs=_unique_refs(step.route_ref for step in steps),
        backend_route_refs=_safe_texts(step.backend_route_ref for step in steps),
        steps=steps,
        complete_daily_loop_available=complete_daily_loop_available,
        local_loop_status=(
            "one_governed_local_loop_available"
            if complete_daily_loop_available
            else "local_loop_partial_missing_prerequisites"
        ),
        readiness_state=(
            "ready_for_one_local_governed_loop"
            if complete_daily_loop_available
            else "partial_missing_prerequisites"
        ),
        missing_prerequisite_refs=missing_prerequisite_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_authority_refs,
    )
    return model.model_dump(mode="json")


def _runs_model(today_summary: dict[str, Any]) -> dict[str, Any]:
    value = today_summary.get("founder_loop_runs_integration_read_model")
    return value if isinstance(value, dict) else {}


def _action_proposal_ref(
    today_summary: dict[str, Any],
    runs: dict[str, Any],
) -> str:
    actions = today_summary.get("actions")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("action_kind") == "local_task_create":
                ref = action.get("action_envelope_ref") or action.get("item_ref")
                if isinstance(ref, str) and ref:
                    return ref
        for action in actions:
            if not isinstance(action, dict):
                continue
            ref = action.get("action_envelope_ref") or action.get("item_ref")
            if isinstance(ref, str) and ref:
                return ref
    action_refs = _refs(runs.get("action_source_refs"))
    return action_refs[0] if action_refs else "action-proposal-ref:missing"


def _missing_prerequisites(today_summary: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not isinstance(today_summary.get("founder_loop_runs_integration_read_model"), dict):
        missing.append("missing-prerequisite-ref:founder-loop-runs-integration")
    actions = today_summary.get("actions")
    if not isinstance(actions, list) or not actions:
        missing.append("missing-prerequisite-ref:action-inbox-proposal")
    if not _refs(today_summary.get("evidence_refs")):
        missing.append("missing-prerequisite-ref:evidence-refs")
    return missing


def _start_step_from_binding(
    step_id: str,
    step_by_surface: dict[str, dict[str, Any]],
) -> ControlCenterStartHereStep:
    binding = step_by_surface.get(step_id)
    if not binding:
        return ControlCenterStartHereStep(
            step_id=step_id,
            label=step_id.replace("_", " ").title(),
            route_ref=f"route-ref:control-center:{step_id}",
            backend_route_ref="missing-backend-route:start-here",
            status="missing_backend_binding",
            safe_summary="The Start Here loop is missing this backend-owned binding.",
            next_safe_action="Inspect missing prerequisite refs before relying on this step.",
            proof_ref=FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
            blocked_authority_refs=[
                "blocked-state:start-here:missing-backend-binding"
            ],
        )
    return ControlCenterStartHereStep(
        step_id=step_id,
        label=str(binding.get("surface") or step_id.replace("_", " ").title()),
        route_ref=_route_ref(binding.get("frontend_route_ref"), step_id),
        backend_route_ref=str(binding.get("backend_route_ref") or "backend-route:missing"),
        status=str(binding.get("status") or "backend_owned_read_model"),
        safe_summary=str(
            binding.get("safe_summary")
            or "Backend-owned Start Here loop step is available as safe refs."
        ),
        next_safe_action=str(
            binding.get("next_safe_action")
            or "Inspect this step's safe refs before relying on it."
        ),
        proof_ref=str(
            binding.get("proof_ref") or FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
        ),
        receipt_refs=_refs(binding.get("receipt_refs"))[:8],
        evidence_refs=_refs(binding.get("evidence_refs"))[:8],
        approval_refs=_refs(binding.get("approval_refs"))[:8],
        memory_candidate_refs=_refs(binding.get("memory_candidate_refs"))[:8],
        blocked_authority_refs=_refs(binding.get("blocked_state_refs"))[:12],
    )


def _validate_common_read_model(model: ControlCenterStartHereSummary) -> None:
    if model.schema_version != "control-center-start-here-summary.v1":
        raise ValueError("Start Here schema drift")
    if model.contract_ref != CONTROL_CENTER_START_HERE_CONTRACT_REF:
        raise ValueError("Start Here contract drift")
    if model.source != CONTROL_CENTER_START_HERE_READ_MODEL_SOURCE:
        raise ValueError("Start Here source drift")
    if not model.backend_owned or not model.local_read_model_only:
        raise ValueError("Start Here must remain backend-owned local read model")
    if not model.safe_refs_only or model.raw_content_included:
        raise ValueError("Start Here must stay safe-ref only")
    for flag in _DENIED_FLAGS:
        if getattr(model, flag):
            raise ValueError(f"Start Here must not enable {flag}")


def _route_ref(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.startswith("route-ref:"):
        validate_execution_ref(value, "route_ref")
        return value
    if isinstance(value, str) and value.startswith("/"):
        slug = value.strip("/").replace("/", "-") or "overview"
        validate_safe_execution_text(slug, "route_ref")
        route_ref = f"route-ref:control-center:{slug}"
        validate_execution_ref(route_ref, "route_ref")
        return route_ref
    slug = fallback.replace("_", "-")
    route_ref = f"route-ref:control-center:{slug}"
    validate_execution_ref(route_ref, "route_ref")
    return route_ref


def _refs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            validate_execution_ref(item, "ref")
            refs.append(item)
    return _unique_refs(refs)


def _unique_refs(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or value in seen:
            continue
        validate_execution_ref(value, "ref")
        seen.add(value)
        result.append(value)
    return result


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)


def _safe_texts(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        validate_safe_execution_text(value, "text")
        if value not in result:
            result.append(value)
    return result


def _validate_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_safe_execution_text(value, field_name)
