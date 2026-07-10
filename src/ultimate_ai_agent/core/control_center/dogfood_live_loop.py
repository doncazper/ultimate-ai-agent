from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    action_id_to_item_ref,
)
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
    local_task_commit_receipt_ref,
)
from ultimate_ai_agent.core.control_center.proof import (
    build_control_center_proof_detail,
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.start_here import (
    build_control_center_start_here_summary,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


DOGFOOD_LIVE_LOOP_SCHEMA_VERSION = "dogfood-live-loop-acceptance.v1"
DOGFOOD_LIVE_LOOP_FIXTURE_REF = (
    "fixture-ref:dogfood-live-loop:founder-operator-day"
)
DOGFOOD_LIVE_LOOP_VERIFIER_REF = "script-ref:verify-dogfood-live-loop-acceptance"
DOGFOOD_LIVE_LOOP_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py inspect-dogfood-live-loop"
)
DOGFOOD_LIVE_LOOP_ACTION_ID = "local-task-create-scorecard"
DOGFOOD_LIVE_LOOP_ACTION_REF = action_id_to_item_ref(DOGFOOD_LIVE_LOOP_ACTION_ID)
DOGFOOD_LIVE_LOOP_LOCAL_TASK_PROOF_REF = (
    "proof-ref:local-task-commit:founder-action-local-task-create-scorecard"
)
DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF = local_task_commit_receipt_ref(
    DOGFOOD_LIVE_LOOP_ACTION_REF,
    "idempotency-ref:dogfood-live-loop:local-task-commit",
)
DOGFOOD_LIVE_LOOP_APPROVAL_IDEMPOTENCY_REF = (
    "idempotency-ref:dogfood-live-loop:local-task-approval"
)
DOGFOOD_LIVE_LOOP_COMMIT_IDEMPOTENCY_REF = (
    "idempotency-ref:dogfood-live-loop:local-task-commit"
)
DOGFOOD_LIVE_LOOP_DECISION_REASON_REF = (
    "decision-reason-ref:dogfood-live-loop:approve-local-task"
)
DOGFOOD_LIVE_LOOP_COMMIT_REASON_REF = (
    "decision-reason-ref:dogfood-live-loop:commit-local-task"
)
DOGFOOD_LIVE_LOOP_METADATA_REF = "metadata-ref:dogfood-live-loop:acceptance"
DOGFOOD_LIVE_LOOP_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-state:dogfood-live-loop:no-provider-model-call",
    "blocked-state:dogfood-live-loop:no-connector-write-or-send",
    "blocked-state:dogfood-live-loop:no-browser-or-web-runtime",
    "blocked-state:dogfood-live-loop:no-shell-subprocess-runtime",
    "blocked-state:dogfood-live-loop:no-background-autonomy",
    "blocked-state:dogfood-live-loop:no-hidden-context-injection",
    "blocked-state:dogfood-live-loop:no-broad-approval",
    "blocked-state:dogfood-live-loop:no-production-authority",
)

_DENIED_TRUE_FRAGMENTS = (
    '"provider_model_call_enabled": true',
    '"runtime_model_call_enabled": true',
    '"connector_write_enabled": true',
    '"connector_send_enabled": true',
    '"browser_execution_enabled": true',
    '"shell_subprocess_execution_enabled": true',
    '"background_autonomy_enabled": true',
    '"production_authority_enabled": true',
    '"external_side_effect_performed": true',
    '"raw_content_included": true',
    '"raw_content_stored": true',
    '"raw_paths_included": true',
    '"control_center_grants_authority": true',
    '"broad_approval_enabled": true',
    '"standing_authority_enabled": true',
    '"runtime_context_injection_enabled": true',
    '"memory_truth_authority": true',
    '"context_injection_authorized": true',
    '"automatic_memory_write_authorized": true',
)
_FORBIDDEN_RAW_FRAGMENTS = (
    "/users/",
    "\\users\\",
    "raw prompt",
    "raw response",
    "raw provider payload",
    "credential material",
    "secret",
    "cookie",
    "oauth",
    "bearer ",
    "password",
)


class DogfoodLiveLoopSection(BaseModel):
    section_ref: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1, max_length=180)
    source_ref: str = Field(..., min_length=1, max_length=180)
    route_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_section(self) -> "DogfoodLiveLoopSection":
        validate_execution_ref(self.section_ref, "section_ref")
        for field_name in ("status", "source_ref", "next_safe_action"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        for field_name in (
            "action_refs",
            "run_refs",
            "proof_refs",
            "receipt_refs",
            "evidence_refs",
            "memory_candidate_refs",
            "approval_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Dogfood live loop section must stay safe-ref only")
        return self


class DogfoodLiveLoopAcceptanceReadModel(BaseModel):
    schema_version: str = DOGFOOD_LIVE_LOOP_SCHEMA_VERSION
    fixture_ref: str = DOGFOOD_LIVE_LOOP_FIXTURE_REF
    status: str = Field(..., min_length=1, max_length=180)
    backend_owned: bool = True
    local_only: bool = True
    deterministic_fixture: bool = True
    fixture_seeded: bool = False
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    raw_content_included: bool = False
    raw_paths_included: bool = False
    control_center_presentation_only: bool = True
    cli_ref: str = DOGFOOD_LIVE_LOOP_CLI_REF
    verifier_ref: str = DOGFOOD_LIVE_LOOP_VERIFIER_REF
    action_id: str = DOGFOOD_LIVE_LOOP_ACTION_ID
    action_ref: str = DOGFOOD_LIVE_LOOP_ACTION_REF
    run_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    primary_proof_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    local_task_ref: str | None = None
    local_task_commit_proof_ref: str | None = None
    local_task_commit_receipt_ref: str | None = None
    local_task_was_actionable_before_commit: bool = False
    local_task_receipt_recorded: bool = False
    start_here_next_safe_action: str = Field(..., min_length=1, max_length=500)
    sections: list[DogfoodLiveLoopSection] = Field(default_factory=list, min_length=1)
    action_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    trust_available_now_lane_refs: list[str] = Field(default_factory=list)
    trust_approval_required_lane_refs: list[str] = Field(default_factory=list)
    trust_blocked_lane_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
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
    def validate_read_model(self) -> "DogfoodLiveLoopAcceptanceReadModel":
        if self.schema_version != DOGFOOD_LIVE_LOOP_SCHEMA_VERSION:
            raise ValueError("Dogfood live loop schema drift")
        if self.fixture_ref != DOGFOOD_LIVE_LOOP_FIXTURE_REF:
            raise ValueError("Dogfood live loop fixture drift")
        if self.action_ref != DOGFOOD_LIVE_LOOP_ACTION_REF:
            raise ValueError("Dogfood live loop action ref drift")
        if self.run_ref != FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF:
            raise ValueError("Dogfood live loop run ref drift")
        for field_name in (
            "fixture_ref",
            "action_ref",
            "run_ref",
            "primary_proof_ref",
            "verifier_ref",
        ):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        validate_safe_execution_text(self.cli_ref, "cli_ref")
        for optional_ref in (
            self.local_task_ref,
            self.local_task_commit_proof_ref,
            self.local_task_commit_receipt_ref,
        ):
            if optional_ref:
                validate_execution_ref(optional_ref, "local_task_ref")
        for field_name in ("status", "start_here_next_safe_action", "next_safe_action"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "action_refs",
            "run_refs",
            "proof_refs",
            "receipt_refs",
            "evidence_refs",
            "memory_candidate_refs",
            "approval_refs",
            "trust_available_now_lane_refs",
            "trust_approval_required_lane_refs",
            "trust_blocked_lane_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        if not self.backend_owned or not self.local_only:
            raise ValueError("Dogfood live loop must stay backend-owned and local-only")
        if (
            not self.safe_refs_only
            or self.raw_content_included
            or self.raw_paths_included
        ):
            raise ValueError("Dogfood live loop must stay redacted")
        for flag in (
            "provider_model_call_enabled",
            "runtime_model_call_enabled",
            "connector_write_enabled",
            "connector_send_enabled",
            "browser_execution_enabled",
            "shell_subprocess_execution_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ):
            if getattr(self, flag):
                raise ValueError(f"Dogfood live loop must not enable {flag}")
        return self


def seed_dogfood_live_loop_fixture(repo: FounderLoopRepository) -> dict[str, Any]:
    """Seed the deterministic local daily loop through accepted capabilities."""

    action_at_start = _find_action(repo.list_action_inbox(limit=50))
    existing_commit_receipt = _existing_commit_receipt_projection(action_at_start)
    if existing_commit_receipt is not None:
        if not _is_dogfood_commit_receipt(existing_commit_receipt):
            raise FounderLoopStorageError(
                "DOGFOOD_LIVE_LOOP_PREEXISTING_NON_DOGFOOD_LOCAL_TASK_RECEIPT"
            )
        return {
            "fixture_ref": DOGFOOD_LIVE_LOOP_FIXTURE_REF,
            "status": "dogfood_fixture_replayed",
            "decision_receipt_ref": None,
            "decision_approval_ref": action_at_start.get(
                "local_task_commit_approval_ref"
            ),
            "local_task_commit_receipt_ref": existing_commit_receipt.get("receipt_ref"),
            "local_task_ref": existing_commit_receipt.get("local_task_ref"),
            "commit_attempted": False,
            "local_task_was_actionable_before_commit": True,
            "action_before_commit": _action_fixture_projection(action_at_start),
            "action_after_commit": _action_fixture_projection(action_at_start),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "raw_paths_omitted": True,
            "provider_model_call_enabled": False,
            "connector_write_enabled": False,
            "external_side_effect_performed": False,
            "production_authority_enabled": False,
        }

    decision_receipt = repo.record_action_decision(
        action_id=DOGFOOD_LIVE_LOOP_ACTION_ID,
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            decision_reason_ref=DOGFOOD_LIVE_LOOP_DECISION_REASON_REF,
            metadata_refs=[DOGFOOD_LIVE_LOOP_METADATA_REF],
        ),
        idempotency_key_ref=DOGFOOD_LIVE_LOOP_APPROVAL_IDEMPOTENCY_REF,
    )
    action_before_commit = _find_action(repo.list_action_inbox(limit=50))
    commit_receipt = _existing_commit_receipt_projection(action_before_commit)
    commit_attempted = False

    if commit_receipt is not None and not _is_dogfood_commit_receipt(commit_receipt):
        raise FounderLoopStorageError(
            "DOGFOOD_LIVE_LOOP_PREEXISTING_NON_DOGFOOD_LOCAL_TASK_RECEIPT"
        )

    if commit_receipt is None:
        approval_ref = str(
            action_before_commit.get("local_task_commit_approval_ref")
            or decision_receipt.get("approval_ref")
            or ""
        )
        if not approval_ref:
            raise FounderLoopStorageError("DOGFOOD_LIVE_LOOP_APPROVAL_REF_MISSING")
        commit_attempted = True
        try:
            commit_receipt = repo.commit_local_task(
                action_id=DOGFOOD_LIVE_LOOP_ACTION_ID,
                request=FounderLoopLocalTaskCommitRequest(
                    approval_ref=approval_ref,
                    decision_reason_ref=DOGFOOD_LIVE_LOOP_COMMIT_REASON_REF,
                    metadata_refs=[DOGFOOD_LIVE_LOOP_METADATA_REF],
                ),
                idempotency_key_ref=DOGFOOD_LIVE_LOOP_COMMIT_IDEMPOTENCY_REF,
            )
        except FounderLoopStorageDuplicateError:
            action_with_receipt = _find_action(repo.list_action_inbox(limit=50))
            commit_receipt = _existing_commit_receipt_projection(action_with_receipt)
            if commit_receipt is None:
                raise
            if not _is_dogfood_commit_receipt(commit_receipt):
                raise FounderLoopStorageError(
                    "DOGFOOD_LIVE_LOOP_PREEXISTING_NON_DOGFOOD_LOCAL_TASK_RECEIPT"
                ) from None

    action_after_commit = _find_action(repo.list_action_inbox(limit=50))
    return {
        "fixture_ref": DOGFOOD_LIVE_LOOP_FIXTURE_REF,
        "status": "dogfood_fixture_seeded",
        "decision_receipt_ref": decision_receipt.get("receipt_ref"),
        "decision_approval_ref": decision_receipt.get("approval_ref"),
        "local_task_commit_receipt_ref": commit_receipt.get("receipt_ref"),
        "local_task_ref": commit_receipt.get("local_task_ref"),
        "commit_attempted": commit_attempted,
        "local_task_was_actionable_before_commit": bool(
            action_before_commit.get("local_task_commit_eligible")
            or commit_receipt.get("receipt_ref")
        ),
        "action_before_commit": _action_fixture_projection(action_before_commit),
        "action_after_commit": _action_fixture_projection(action_after_commit),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "connector_write_enabled": False,
        "external_side_effect_performed": False,
        "production_authority_enabled": False,
    }


def build_dogfood_live_loop_acceptance_read_model(
    *,
    repo: FounderLoopRepository,
    seed_fixture: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    seed_result = seed_dogfood_live_loop_fixture(repo) if seed_fixture else None
    bounded_limit = min(max(int(limit), 12), 50)
    today = repo.today_summary(limit=bounded_limit)
    start_here = build_control_center_start_here_summary(today_summary=today)
    action_inbox = repo.actions_inbox(limit=bounded_limit)
    proof_index = build_control_center_proof_index(today_summary=today)
    trust = build_trust_authority_matrix_read_model(today_summary=today)
    trust_runtime_blocked_lane_refs = _trust_runtime_blocked_lane_refs(trust)
    action = _find_action(today.get("actions") or action_inbox.get("items") or [])
    local_task_record = _local_task_proof_record(proof_index)
    proof_detail = build_control_center_proof_detail(
        today_summary=today,
        proof_ref=str(local_task_record.get("proof_ref")),
    )
    evidence_memory = _dict(today.get("evidence_memory_loop_binding_read_model"))
    local_task_receipt_ref = _first_ref(
        action.get("local_task_commit_receipt_ref"),
        seed_result.get("local_task_commit_receipt_ref") if seed_result else None,
    )
    local_task_ref = _first_ref(
        action.get("local_task_ref"),
        seed_result.get("local_task_ref") if seed_result else None,
    )
    local_task_was_actionable = bool(
        seed_result
        and seed_result.get("local_task_was_actionable_before_commit") is True
    )
    local_task_receipt_recorded = bool(local_task_receipt_ref)
    action_refs = _merge_refs(
        [DOGFOOD_LIVE_LOOP_ACTION_REF],
        [start_here.get("action_proposal_ref")],
        evidence_memory.get("action_refs"),
    )
    run_refs = _merge_refs(
        [FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        evidence_memory.get("run_refs"),
        local_task_record.get("run_refs"),
    )
    proof_refs = _merge_refs(
        [FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF],
        [local_task_record.get("proof_ref")],
        evidence_memory.get("proof_refs"),
    )
    receipt_refs = _merge_refs(
        [local_task_receipt_ref],
        action.get("receipt_refs"),
        local_task_record.get("receipt_refs"),
        evidence_memory.get("receipt_refs"),
    )
    evidence_refs = _merge_refs(
        action.get("evidence_refs"),
        local_task_record.get("evidence_refs"),
        evidence_memory.get("evidence_refs"),
        today.get("evidence_refs"),
    )
    memory_candidate_refs = _merge_refs(
        evidence_memory.get("memory_candidate_refs"),
        local_task_record.get("memory_candidate_refs"),
        today.get("memory_candidate_refs"),
    )
    approval_refs = _merge_refs(
        action.get("approval_refs"),
        [action.get("local_task_commit_approval_ref")],
        local_task_record.get("approval_refs"),
    )
    status = (
        "complete_local_dogfood_loop_proven"
        if local_task_was_actionable and local_task_receipt_recorded
        else "partial_local_dogfood_loop_unseeded_or_incomplete"
    )
    sections = [
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:start-here",
            status=str(start_here.get("local_loop_status")),
            source_ref=str(start_here.get("source")),
            route_refs=["GET /control-center/start-here/summary"],
            action_refs=_refs([start_here.get("action_proposal_ref")]),
            run_refs=_refs([start_here.get("primary_run_ref")]),
            proof_refs=_refs([start_here.get("primary_proof_ref")]),
            evidence_refs=_refs(start_here.get("evidence_refs"))[:12],
            blocked_authority_refs=_refs(start_here.get("blocked_authority_refs")),
            next_safe_action=str(start_here.get("next_safe_action")),
        ),
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:today",
            status=str(today.get("status")),
            source_ref="python_core_founder_loop_today_summary",
            route_refs=["GET /control-center/today/summary"],
            action_refs=[DOGFOOD_LIVE_LOOP_ACTION_REF],
            run_refs=run_refs[:4],
            proof_refs=proof_refs[:6],
            receipt_refs=receipt_refs[:8],
            evidence_refs=evidence_refs[:12],
            memory_candidate_refs=memory_candidate_refs[:8],
            next_safe_action=str(today.get("next_safe_action") or start_here["next_safe_action"]),
        ),
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:action-inbox",
            status=str(action.get("status") or "missing_action_ref"),
            source_ref=str(
                action_inbox.get("source")
                or action_inbox.get("action_inbox_work_queue_read_model", {}).get("source")
                or "python_core_action_inbox_read_model"
            ),
            route_refs=["GET /control-center/actions/inbox"],
            action_refs=[DOGFOOD_LIVE_LOOP_ACTION_REF],
            proof_refs=_refs(action.get("proof_refs"))[:8],
            receipt_refs=receipt_refs[:8],
            evidence_refs=_refs(action.get("evidence_refs"))[:12],
            approval_refs=approval_refs[:8],
            blocked_authority_refs=_refs(action.get("action_blocked_state_refs")),
            next_safe_action=str(action.get("next_safe_action") or "Inspect local task refs."),
        ),
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:proof-detail",
            status=str(proof_detail.get("status")),
            source_ref=str(proof_detail.get("source")),
            route_refs=[
                "GET /control-center/proof/index",
                "GET /control-center/proof/{proof_ref}",
            ],
            action_refs=[DOGFOOD_LIVE_LOOP_ACTION_REF],
            run_refs=_refs(local_task_record.get("run_refs")),
            proof_refs=_refs([local_task_record.get("proof_ref")]),
            receipt_refs=_refs(local_task_record.get("receipt_refs")),
            evidence_refs=_refs(local_task_record.get("evidence_refs")),
            approval_refs=_refs(local_task_record.get("approval_refs")),
            blocked_authority_refs=_refs(local_task_record.get("blocked_authority_refs")),
            next_safe_action=str(local_task_record.get("next_safe_action")),
        ),
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:evidence-memory",
            status=str(evidence_memory.get("status")),
            source_ref=str(evidence_memory.get("source")),
            route_refs=_texts(evidence_memory.get("route_refs")),
            action_refs=_refs(evidence_memory.get("action_refs")),
            run_refs=_refs(evidence_memory.get("run_refs")),
            proof_refs=_refs(evidence_memory.get("proof_refs"))[:12],
            receipt_refs=_refs(evidence_memory.get("receipt_refs"))[:12],
            evidence_refs=_refs(evidence_memory.get("evidence_refs"))[:20],
            memory_candidate_refs=_refs(evidence_memory.get("memory_candidate_refs")),
            blocked_authority_refs=_refs(evidence_memory.get("blocked_authority_refs")),
            next_safe_action=str(evidence_memory.get("next_safe_action")),
        ),
        DogfoodLiveLoopSection(
            section_ref="dogfood-live-loop-section:trust",
            status=str(trust.get("status")),
            source_ref="python_core_trust_authority_matrix_read_model",
            route_refs=["GET /control-center/trust-authority/matrix"],
            proof_refs=_refs(trust.get("proof_refs"))[:12],
            blocked_authority_refs=_refs(trust.get("blocked_authority_refs"))[:20],
            next_safe_action=str(trust.get("next_safe_action")),
        ),
    ]
    model = DogfoodLiveLoopAcceptanceReadModel(
        status=status,
        fixture_seeded=seed_result is not None,
        local_task_ref=local_task_ref,
        local_task_commit_proof_ref=str(local_task_record.get("proof_ref")),
        local_task_commit_receipt_ref=local_task_receipt_ref,
        local_task_was_actionable_before_commit=local_task_was_actionable,
        local_task_receipt_recorded=local_task_receipt_recorded,
        start_here_next_safe_action=str(start_here.get("next_safe_action")),
        sections=sections,
        action_refs=action_refs,
        run_refs=run_refs,
        proof_refs=proof_refs,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        memory_candidate_refs=memory_candidate_refs,
        approval_refs=approval_refs,
        trust_available_now_lane_refs=_refs(trust.get("available_now_lane_refs")),
        trust_approval_required_lane_refs=_refs(
            trust.get("approval_required_lane_refs")
        ),
        trust_blocked_lane_refs=trust_runtime_blocked_lane_refs,
        blocked_authority_refs=_merge_refs(
            DOGFOOD_LIVE_LOOP_BLOCKED_AUTHORITY_REFS,
            trust.get("blocked_authority_refs"),
        ),
        next_safe_action=(
            "Inspect the local task receipt, Evidence/Memory binding, and Trust "
            "posture before promoting any broader authority."
        ),
    )
    return model.model_dump(mode="json")


def validate_dogfood_live_loop_acceptance(
    read_model: dict[str, Any],
    *,
    require_seeded: bool = True,
) -> list[str]:
    issues: list[str] = []
    try:
        parsed = DogfoodLiveLoopAcceptanceReadModel(**read_model)
    except Exception as exc:  # pragma: no cover - caller reports message.
        return [f"dogfood-live-loop-schema-invalid:{type(exc).__name__}"]

    if require_seeded and not parsed.fixture_seeded:
        issues.append("dogfood-live-loop-fixture-not-seeded")
    if parsed.status != "complete_local_dogfood_loop_proven":
        issues.append("dogfood-live-loop-status-not-complete")
    if require_seeded and not parsed.local_task_was_actionable_before_commit:
        issues.append("dogfood-live-loop-local-task-not-actionable-before-commit")
    if not parsed.local_task_receipt_recorded or not parsed.local_task_commit_receipt_ref:
        issues.append("dogfood-live-loop-local-task-receipt-missing")
    if (
        parsed.local_task_commit_receipt_ref
        and parsed.local_task_commit_receipt_ref
        != DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF
    ):
        issues.append("dogfood-live-loop-nondeterministic-commit-receipt")
    if DOGFOOD_LIVE_LOOP_ACTION_REF not in parsed.action_refs:
        issues.append("dogfood-live-loop-action-ref-missing")
    if parsed.run_ref not in parsed.run_refs:
        issues.append("dogfood-live-loop-run-ref-missing")
    if parsed.primary_proof_ref not in parsed.proof_refs:
        issues.append("dogfood-live-loop-primary-proof-ref-missing")
    if not parsed.local_task_commit_proof_ref or (
        parsed.local_task_commit_proof_ref not in parsed.proof_refs
    ):
        issues.append("dogfood-live-loop-local-task-proof-ref-missing")
    if not parsed.evidence_refs:
        issues.append("dogfood-live-loop-evidence-refs-missing")
    if not parsed.memory_candidate_refs:
        issues.append("dogfood-live-loop-memory-binding-missing")
    if "trust-lane:local-task-commit" not in parsed.trust_approval_required_lane_refs:
        issues.append("dogfood-live-loop-trust-local-task-posture-missing")
    for required_trust_lane in (
        "trust-lane:connector-write-low-risk",
        "trust-lane:production-authority-gate",
    ):
        if required_trust_lane not in parsed.trust_blocked_lane_refs:
            issues.append(
                "dogfood-live-loop-trust-blocked-lane-missing:"
                f"{required_trust_lane}"
            )

    required_section_refs = {
        "dogfood-live-loop-section:start-here",
        "dogfood-live-loop-section:today",
        "dogfood-live-loop-section:action-inbox",
        "dogfood-live-loop-section:proof-detail",
        "dogfood-live-loop-section:evidence-memory",
        "dogfood-live-loop-section:trust",
    }
    section_refs = {section.section_ref for section in parsed.sections}
    for required in (
        *required_section_refs,
    ):
        if required not in section_refs:
            issues.append(f"dogfood-live-loop-section-missing:{required}")
    for section in parsed.sections:
        if section.section_ref in required_section_refs:
            if (
                section.section_ref
                in {
                    "dogfood-live-loop-section:today",
                    "dogfood-live-loop-section:action-inbox",
                    "dogfood-live-loop-section:proof-detail",
                    "dogfood-live-loop-section:evidence-memory",
                }
                and DOGFOOD_LIVE_LOOP_ACTION_REF not in section.action_refs
            ):
                issues.append(
                    f"dogfood-live-loop-section-action-ref-missing:{section.section_ref}"
                )
            if (
                section.section_ref
                in {
                    "dogfood-live-loop-section:today",
                    "dogfood-live-loop-section:proof-detail",
                    "dogfood-live-loop-section:evidence-memory",
                    "dogfood-live-loop-section:trust",
                }
                and not section.proof_refs
            ):
                issues.append(
                    f"dogfood-live-loop-section-proof-ref-missing:{section.section_ref}"
                )
            if section.section_ref in {
                "dogfood-live-loop-section:today",
                "dogfood-live-loop-section:action-inbox",
                "dogfood-live-loop-section:proof-detail",
                "dogfood-live-loop-section:evidence-memory",
            } and (
                DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF
                not in section.receipt_refs
            ):
                issues.append(
                    f"dogfood-live-loop-section-receipt-ref-missing:{section.section_ref}"
                )
            if section.section_ref in {
                "dogfood-live-loop-section:today",
                "dogfood-live-loop-section:proof-detail",
                "dogfood-live-loop-section:evidence-memory",
            } and not section.evidence_refs:
                issues.append(
                    f"dogfood-live-loop-section-evidence-ref-missing:{section.section_ref}"
                )
            if section.section_ref in {
                "dogfood-live-loop-section:today",
                "dogfood-live-loop-section:evidence-memory",
            } and not section.memory_candidate_refs:
                issues.append(
                    f"dogfood-live-loop-section-memory-ref-missing:{section.section_ref}"
                )
            if (
                section.section_ref == "dogfood-live-loop-section:trust"
                and "trust-lane:connector-write-low-risk"
                not in parsed.trust_blocked_lane_refs
            ):
                issues.append(
                    "dogfood-live-loop-section-trust-blocked-ref-missing"
                )

    text = json.dumps(read_model, sort_keys=True).lower()
    for fragment in _DENIED_TRUE_FRAGMENTS:
        if fragment in text:
            issues.append(f"dogfood-live-loop-forbidden-enabled:{fragment}")
    for fragment in _FORBIDDEN_RAW_FRAGMENTS:
        if fragment in text:
            issues.append(f"dogfood-live-loop-forbidden-raw-fragment:{fragment}")
    return issues


def _find_action(actions: Any) -> dict[str, Any]:
    for action in _list_of_dicts(actions):
        if action.get("item_ref") == DOGFOOD_LIVE_LOOP_ACTION_REF:
            return action
    raise FounderLoopStorageError("DOGFOOD_LIVE_LOOP_ACTION_NOT_FOUND")


def _local_task_proof_record(proof_index: dict[str, Any]) -> dict[str, Any]:
    for record in _list_of_dicts(proof_index.get("records")):
        if (
            record.get("proof_kind") == "local_task_commit"
            and record.get("proof_ref") == DOGFOOD_LIVE_LOOP_LOCAL_TASK_PROOF_REF
            and DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF
            in _refs(record.get("receipt_refs"))
        ):
            return record
    raise FounderLoopStorageError("DOGFOOD_LIVE_LOOP_LOCAL_TASK_PROOF_NOT_FOUND")


def _existing_commit_receipt_projection(action: dict[str, Any]) -> dict[str, Any] | None:
    receipt_ref = action.get("local_task_commit_receipt_ref")
    local_task_ref = action.get("local_task_ref")
    if not isinstance(receipt_ref, str) or not receipt_ref:
        return None
    return {
        "status": "local_task_created",
        "receipt_ref": receipt_ref,
        "local_task_ref": local_task_ref,
        "replayed": True,
        "safe_refs_only": True,
        "raw_content_stored": False,
        "external_side_effect_performed": False,
        "connector_write_performed": False,
        "provider_model_call_enabled": False,
        "production_authority_enabled": False,
    }


def _is_dogfood_commit_receipt(receipt: dict[str, Any]) -> bool:
    return receipt.get("receipt_ref") == DOGFOOD_LIVE_LOOP_EXPECTED_COMMIT_RECEIPT_REF


def _action_fixture_projection(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_ref": action.get("item_ref"),
        "status": action.get("status"),
        "action_kind": action.get("action_kind"),
        "local_task_ref": action.get("local_task_ref"),
        "local_task_commit_approval_ref": action.get(
            "local_task_commit_approval_ref"
        ),
        "local_task_commit_approval_status": action.get(
            "local_task_commit_approval_status"
        ),
        "local_task_commit_eligible": action.get("local_task_commit_eligible"),
        "local_task_commit_receipt_ref": action.get(
            "local_task_commit_receipt_ref"
        ),
        "receipt_refs": _refs(action.get("receipt_refs")),
        "evidence_refs": _refs(action.get("evidence_refs")),
        "safe_refs_only": True,
        "raw_content_omitted": True,
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _first_ref(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def _refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        refs: list[str] = []
        for item in value:
            if isinstance(item, str) and item:
                refs.append(item)
        return list(dict.fromkeys(refs))
    return []


def _texts(value: Any) -> list[str]:
    return _refs(value)


def _merge_refs(*values: Any) -> list[str]:
    refs: list[str] = []
    for value in values:
        refs.extend(_refs(value))
    return list(dict.fromkeys(refs))


def _trust_runtime_blocked_lane_refs(trust: dict[str, Any]) -> list[str]:
    """Project lanes that are denied now, including planned unsupported lanes."""

    denied_lane_refs = [
        entry.get("source_lane_ref")
        for entry in _list_of_dicts(trust.get("authority_capability_catalog"))
        if entry.get("authority_state_decision_outcome") == "deny"
    ]
    return _merge_refs(trust.get("blocked_lane_refs"), denied_lane_refs)


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_execution_ref(value, field_name)


def _validate_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_safe_execution_text(value, field_name)
