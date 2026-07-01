from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.chat import CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


CHAT_TO_LOOP_HANDOFF_CONTRACT_REF = (
    "contract-ref:product-loop-009-chat-to-loop-handoff:v1"
)
CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE = (
    "python_core_chat_to_loop_handoff_read_model"
)
CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS: tuple[str, ...] = (
    "remember_this",
    "create_action",
    "add_to_plan",
    "defer",
    "ask_human",
    "blocked",
)
CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:chat-to-loop-no-model-output-authority",
    "blocked-state:chat-to-loop-no-direct-memory-write",
    "blocked-state:chat-to-loop-no-context-injection",
    "blocked-state:chat-to-loop-no-tool-execution",
    "blocked-state:chat-to-loop-no-connector-write",
    "blocked-state:chat-to-loop-no-action-execution",
    "blocked-state:chat-to-loop-no-plan-execution",
    "blocked-state:chat-to-loop-no-provider-model-call",
    "blocked-state:chat-to-loop-no-browser-execution",
    "blocked-state:chat-to-loop-no-production-authority",
)
_DENIED_FLAGS: tuple[str, ...] = (
    "model_output_authority",
    "direct_memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "tool_execution_enabled",
    "connector_write_enabled",
    "action_execution_enabled",
    "plan_execution_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "live_web_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "production_authority_enabled",
)
_UNSAFE_TEXT_FRAGMENTS: tuple[str, ...] = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "provider exchange",
    "full transcript",
    "unredacted transcript",
    "credential",
    "authorization",
    "api key",
    "secret",
    "password",
)
_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_#=-]{0,239}$")


class ChatToLoopHandoffOutcome(BaseModel):
    outcome_ref: str
    outcome_kind: Literal[
        "remember_this",
        "create_action",
        "add_to_plan",
        "defer",
        "ask_human",
        "blocked",
    ]
    state: str
    target_surface: Literal["Memory", "Actions", "Plans", "Chat", "Authority"]
    safe_label: str
    source_ref: str
    proposal_ref: str
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_outcome(self) -> "ChatToLoopHandoffOutcome":
        for field_name in (
            "outcome_ref",
            "source_ref",
            "proposal_ref",
        ):
            _validate_safe_ref(getattr(self, field_name), field_name)
        for field_name in ("receipt_refs", "evidence_refs", "blocked_state_refs"):
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        for field_name in (
            "state",
            "safe_label",
            "target_surface",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        return self


class ChatToLoopHandoffReadModel(BaseModel):
    schema_version: str = "product-loop-009-chat-to-loop-handoff.v1"
    contract_ref: str = CHAT_TO_LOOP_HANDOFF_CONTRACT_REF
    source: str = CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE
    status: str = "backend_owned_chat_to_loop_handoff_polish"
    backend_owned: bool = True
    local_read_model_only: bool = True
    proposal_only: bool = True
    safe_refs_only: bool = True
    safe_summary_only: bool = True
    raw_content_included: bool = False
    idempotency_bound: bool = True
    outcome_kinds: list[str] = Field(
        default_factory=lambda: list(CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS)
    )
    safe_summary: str = (
        "Chat to loop handoff polish classifies safe Chat receipt refs into "
        "reviewable remember-this, create-action, add-to-plan, defer, ask-human, "
        "and blocked outcomes without granting memory, action, tool, connector, "
        "model, context, web, shell, browser, or production authority."
    )
    outcome_count: int = Field(default=0, ge=0)
    turn_receipt_count: int = Field(default=0, ge=0)
    handoff_receipt_count: int = Field(default=0, ge=0)
    remember_this_count: int = Field(default=0, ge=0)
    create_action_count: int = Field(default=0, ge=0)
    add_to_plan_count: int = Field(default=0, ge=0)
    defer_count: int = Field(default=0, ge=0)
    ask_human_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    outcomes: list[ChatToLoopHandoffOutcome] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    turn_receipt_refs: list[str] = Field(default_factory=list)
    handoff_receipt_refs: list[str] = Field(default_factory=list)
    action_created_refs: list[str] = Field(default_factory=list)
    plan_created_refs: list[str] = Field(default_factory=list)
    memory_proposal_refs: list[str] = Field(default_factory=list)
    defer_refs: list[str] = Field(default_factory=list)
    ask_human_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    idempotency_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Review Chat handoff outcomes as proposals only; create scoped Action, "
        "Plan, Memory, or human-review receipts through their own governed lanes."
    )
    model_output_authority: bool = False
    direct_memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    tool_execution_enabled: bool = False
    connector_write_enabled: bool = False
    action_execution_enabled: bool = False
    plan_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "ChatToLoopHandoffReadModel":
        if self.schema_version != "product-loop-009-chat-to-loop-handoff.v1":
            raise ValueError("unexpected Chat to loop handoff schema version")
        if self.contract_ref != CHAT_TO_LOOP_HANDOFF_CONTRACT_REF:
            raise ValueError("unexpected Chat to loop handoff contract ref")
        if self.source != CHAT_TO_LOOP_HANDOFF_READ_MODEL_SOURCE:
            raise ValueError("unexpected Chat to loop handoff read-model source")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "proposal_only",
            "safe_refs_only",
            "safe_summary_only",
            "idempotency_bound",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("Chat to loop handoff must not include raw content")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        if tuple(self.outcome_kinds) != CHAT_TO_LOOP_HANDOFF_OUTCOME_KINDS:
            raise ValueError("Chat to loop outcome kinds drifted")
        for field_name in (
            "status",
            "safe_summary",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "outcome_refs",
            "turn_receipt_refs",
            "handoff_receipt_refs",
            "action_created_refs",
            "plan_created_refs",
            "memory_proposal_refs",
            "defer_refs",
            "ask_human_refs",
            "evidence_refs",
            "idempotency_refs",
            "blocked_state_refs",
        ):
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        missing_blockers = set(CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blockers:
            raise ValueError("Chat to loop handoff missing blocked refs")
        if self.outcome_count != len(self.outcomes):
            raise ValueError("outcome_count must match outcomes")
        if self.outcome_refs != [outcome.outcome_ref for outcome in self.outcomes]:
            raise ValueError("outcome refs must match outcomes")
        count_pairs = (
            ("turn_receipt_count", "turn_receipt_refs"),
            ("handoff_receipt_count", "handoff_receipt_refs"),
            ("remember_this_count", "memory_proposal_refs"),
            ("create_action_count", "action_created_refs"),
            ("add_to_plan_count", "plan_created_refs"),
            ("defer_count", "defer_refs"),
            ("ask_human_count", "ask_human_refs"),
            ("blocked_count", "blocked_state_refs"),
        )
        for count_field, refs_field in count_pairs:
            if getattr(self, count_field) != len(getattr(self, refs_field)):
                raise ValueError(f"{count_field} must match {refs_field}")
        validate_safe_task_payload(self.model_dump(mode="json"), "chat_to_loop_handoff")
        return self


def build_chat_to_loop_handoff_read_model(
    *,
    chat_turn_receipts: list[dict[str, Any]],
    chat_handoff_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    turn_receipt_refs = _unique_refs(
        [
            str(receipt["receipt_ref"])
            for receipt in chat_turn_receipts
            if receipt.get("receipt_ref")
        ]
    )
    handoff_receipt_refs = _unique_refs(
        [
            str(receipt["receipt_ref"])
            for receipt in chat_handoff_receipts
            if receipt.get("receipt_ref")
        ]
    )
    action_handoffs = _safe_handoffs_for_target(chat_handoff_receipts, "actions")
    plan_handoffs = _safe_handoffs_for_target(chat_handoff_receipts, "plans")
    action_created_refs = _unique_refs(
        [str(receipt["created_ref"]) for receipt in action_handoffs]
    )
    plan_created_refs = _unique_refs(
        [str(receipt["created_ref"]) for receipt in plan_handoffs]
    )
    action_receipt_refs = _unique_refs(
        [str(receipt["receipt_ref"]) for receipt in action_handoffs]
    )
    plan_receipt_refs = _unique_refs(
        [str(receipt["receipt_ref"]) for receipt in plan_handoffs]
    )
    idempotency_refs = _unique_refs(
        [
            str(receipt["idempotency_key_ref"])
            for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
            if receipt.get("idempotency_key_ref")
        ]
    )
    evidence_refs = _unique_refs(
        [
            "evidence-ref:chat-to-loop-handoff:read-model",
            *[
                str(receipt["evidence_ref"])
                for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
                if receipt.get("evidence_ref")
            ],
            *[
                str(ref)
                for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
                for ref in list(receipt.get("evidence_refs") or [])
            ],
        ]
    )
    blocked_state_refs = _unique_refs(
        [
            *CHAT_TO_LOOP_HANDOFF_REQUIRED_BLOCKED_REFS,
            *CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS,
            *[
                str(ref)
                for receipt in [*chat_turn_receipts, *chat_handoff_receipts]
                for ref in list(receipt.get("blocked_state_refs") or [])
            ],
        ]
    )
    latest_turn_ref = (
        str(chat_turn_receipts[0]["turn_ref"])
        if chat_turn_receipts and chat_turn_receipts[0].get("turn_ref")
        else "chat-turn:local-operator:pending"
    )
    memory_proposal_refs = [f"memory-intake-proposal:chat:{_safe_suffix(latest_turn_ref)}"]
    defer_refs = [f"defer-ref:chat-to-loop:{_safe_suffix(latest_turn_ref)}"]
    ask_human_refs = [f"ask-human-ref:chat-to-loop:{_safe_suffix(latest_turn_ref)}"]
    action_source_ref = (
        str(action_handoffs[0]["turn_ref"]) if action_handoffs else latest_turn_ref
    )
    plan_source_ref = (
        str(plan_handoffs[0]["turn_ref"]) if plan_handoffs else latest_turn_ref
    )
    outcomes = [
        _outcome(
            "remember_this",
            "Memory",
            memory_proposal_refs[0],
            latest_turn_ref,
            evidence_refs,
            blocked_state_refs,
            bool(turn_receipt_refs),
        ),
        _outcome(
            "create_action",
            "Actions",
            action_created_refs[0]
            if action_created_refs
            else f"founder-action:chat-handoff:{_safe_suffix(action_source_ref)}",
            action_source_ref,
            evidence_refs,
            blocked_state_refs,
            bool(action_created_refs),
            action_receipt_refs,
        ),
        _outcome(
            "add_to_plan",
            "Plans",
            plan_created_refs[0]
            if plan_created_refs
            else f"plan-summary:chat-handoff:{_safe_suffix(plan_source_ref)}",
            plan_source_ref,
            evidence_refs,
            blocked_state_refs,
            bool(plan_created_refs),
            plan_receipt_refs,
        ),
        _outcome(
            "defer",
            "Chat",
            defer_refs[0],
            latest_turn_ref,
            evidence_refs,
            blocked_state_refs,
            bool(turn_receipt_refs),
        ),
        _outcome(
            "ask_human",
            "Chat",
            ask_human_refs[0],
            latest_turn_ref,
            evidence_refs,
            blocked_state_refs,
            bool(turn_receipt_refs),
        ),
        _outcome(
            "blocked",
            "Authority",
            "blocked-state:chat-to-loop-no-action-execution",
            latest_turn_ref,
            evidence_refs,
            blocked_state_refs,
            False,
        ),
    ]
    model = ChatToLoopHandoffReadModel(
        outcome_count=len(outcomes),
        turn_receipt_count=len(turn_receipt_refs),
        handoff_receipt_count=len(handoff_receipt_refs),
        remember_this_count=len(memory_proposal_refs),
        create_action_count=len(action_created_refs),
        add_to_plan_count=len(plan_created_refs),
        defer_count=len(defer_refs),
        ask_human_count=len(ask_human_refs),
        blocked_count=len(blocked_state_refs),
        outcomes=outcomes,
        outcome_refs=[outcome.outcome_ref for outcome in outcomes],
        turn_receipt_refs=turn_receipt_refs,
        handoff_receipt_refs=handoff_receipt_refs,
        action_created_refs=action_created_refs,
        plan_created_refs=plan_created_refs,
        memory_proposal_refs=memory_proposal_refs,
        defer_refs=defer_refs,
        ask_human_refs=ask_human_refs,
        evidence_refs=evidence_refs,
        idempotency_refs=idempotency_refs,
        blocked_state_refs=blocked_state_refs,
    )
    return model.model_dump(mode="json")


def _outcome(
    outcome_kind: str,
    target_surface: str,
    proposal_ref: str,
    source_ref: str,
    evidence_refs: list[str],
    blocked_state_refs: list[str],
    is_recorded: bool,
    receipt_refs: list[str] | None = None,
) -> ChatToLoopHandoffOutcome:
    state = "recorded_reviewable_proposal" if is_recorded else "blocked_review_required"
    if outcome_kind == "blocked":
        state = "blocked_authority"
    outcome_ref = f"chat-to-loop-outcome:{outcome_kind}:{_safe_suffix(source_ref)}"
    return ChatToLoopHandoffOutcome(
        outcome_ref=outcome_ref,
        outcome_kind=outcome_kind,  # type: ignore[arg-type]
        state=state,
        target_surface=target_surface,  # type: ignore[arg-type]
        safe_label=outcome_kind.replace("_", " "),
        source_ref=source_ref,
        proposal_ref=proposal_ref,
        receipt_refs=receipt_refs or [],
        evidence_refs=evidence_refs[:8],
        blocked_state_refs=blocked_state_refs[:12],
        next_safe_action=(
            "Review this Chat handoff outcome through its target surface; "
            "presence here does not authorize execution or memory writes."
        ),
    )


def _unique_refs(refs: list[str]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        try:
            _validate_safe_ref(ref, "chat_to_loop_ref")
        except ValueError:
            continue
        safe_refs.append(ref)
    return list(dict.fromkeys(safe_refs))


def _safe_handoffs_for_target(
    receipts: list[dict[str, Any]],
    target: Literal["actions", "plans"],
) -> list[dict[str, str]]:
    safe_receipts: list[dict[str, str]] = []
    for receipt in receipts:
        if receipt.get("handoff_target") != target:
            continue
        required_refs = {
            "turn_ref": str(receipt.get("turn_ref") or ""),
            "created_ref": str(receipt.get("created_ref") or ""),
            "receipt_ref": str(receipt.get("receipt_ref") or ""),
        }
        try:
            for field_name, ref in required_refs.items():
                _validate_safe_ref(ref, field_name)
        except ValueError:
            continue
        safe_receipts.append(required_refs)
    return safe_receipts


def _safe_suffix(value: str) -> str:
    lowered = value.lower()
    return "".join(char if char.isalnum() or char in "-_:" else "-" for char in lowered)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_task_text(value, field_name)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe ref")
    validate_task_ref(value, field_name)
    _validate_safe_text(value, field_name)
