from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF = (
    "contract-ref:chat-local-operator-surface:v1"
)
CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS = [
    "turn_ref",
    "route_ref",
    "model_ref",
    "runtime_truth",
    "auth_truth",
    "tool_denial_truth",
    "safe_evidence_refs",
    "plans_handoff_ref",
    "actions_handoff_ref",
    "blocked_state_refs",
]
CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-model-output-authority",
    "blocked-state:no-tool-execution",
    "blocked-state:no-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-web-fetch",
    "blocked-state:no-connector-write",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-action-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-production-authority",
]
SAFE_CHAT_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")
UNSAFE_CHAT_OPERATOR_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "full transcript",
    "unredacted transcript",
    "api key",
    "authorization",
    "credential",
    "password",
)


class ChatLocalOperatorTurnEnvelope(BaseModel):
    contract_ref: str = CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
    turn_ref: str = Field(..., min_length=1)
    route_ref: str = Field(default="/v1/chat/completions", min_length=1)
    model_ref: str = Field(..., min_length=1)
    runtime_truth: str = Field(..., min_length=1, max_length=80)
    auth_truth: str = Field(..., min_length=1, max_length=80)
    tool_denial_truth: str = Field(..., min_length=1, max_length=80)
    tool_denial_ref: str = Field(..., min_length=1)
    safe_evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    plans_handoff_ref: str = Field(..., min_length=1)
    actions_handoff_ref: str = Field(..., min_length=1)
    blocked_state_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    response_visible: bool = False
    prompt_body_visible: bool = False
    completion_body_visible: bool = False
    model_output_authority: bool = False
    tool_execution_enabled: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    provider_sdk_call_enabled: bool = False
    web_fetch_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    action_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_turn_envelope(self) -> "ChatLocalOperatorTurnEnvelope":
        if self.contract_ref != CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF:
            raise ValueError("unexpected Chat local operator contract ref")
        for field_name in [
            "contract_ref",
            "turn_ref",
            "model_ref",
            "tool_denial_ref",
            "plans_handoff_ref",
            "actions_handoff_ref",
        ]:
            validate_task_ref(getattr(self, field_name), field_name)
        validate_safe_task_text(self.route_ref, "route_ref")
        validate_safe_task_text(self.runtime_truth, "runtime_truth")
        validate_safe_task_text(self.auth_truth, "auth_truth")
        validate_safe_task_text(self.tool_denial_truth, "tool_denial_truth")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for field_name in ["safe_evidence_refs", "blocked_state_refs"]:
            for ref_value in getattr(self, field_name):
                validate_task_ref(ref_value, field_name)
        missing_blockers = set(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blockers:
            raise ValueError("Chat local operator envelope missing blocked refs")
        denied_flags = {
            "response_visible": self.response_visible,
            "prompt_body_visible": self.prompt_body_visible,
            "completion_body_visible": self.completion_body_visible,
            "model_output_authority": self.model_output_authority,
            "tool_execution_enabled": self.tool_execution_enabled,
            "memory_write_authorized": self.memory_write_authorized,
            "context_injection_authorized": self.context_injection_authorized,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "web_fetch_enabled": self.web_fetch_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "action_execution_enabled": self.action_execution_enabled,
            "approval_grant_capture_enabled": self.approval_grant_capture_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"Chat local operator enabled denied authority: {enabled[0]}")
        payload = self.model_dump(mode="json")
        _validate_no_denied_fragments(payload)
        validate_safe_task_payload(payload, "chat_local_operator_turn")
        return self


def build_chat_local_operator_turn_envelope(
    *,
    model_ref: str,
    runtime_truth: str = "runtime-not-contacted",
    auth_truth: str = "auth-not-evaluated",
    tool_denial_truth: str = "tools-functions-streaming-denied",
    safe_evidence_refs: list[str] | None = None,
) -> ChatLocalOperatorTurnEnvelope:
    suffix = _safe_suffix(model_ref)
    return ChatLocalOperatorTurnEnvelope(
        turn_ref=f"chat-turn:local-operator:{suffix}",
        model_ref=model_ref,
        runtime_truth=runtime_truth,
        auth_truth=auth_truth,
        tool_denial_truth=tool_denial_truth,
        tool_denial_ref=f"tool-denial-ref:chat-local-operator:{suffix}",
        safe_evidence_refs=safe_evidence_refs
        or ["evidence-ref:chat-local-operator:turn"],
        plans_handoff_ref=f"handoff-ref:chat-to-plans:{suffix}",
        actions_handoff_ref=f"handoff-ref:chat-to-actions:{suffix}",
        blocked_state_refs=list(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS),
        safe_summary=(
            "Local Chat operator turn records route, runtime, auth, and "
            "tool-denial truth as safe refs; model output is not authority."
        ),
    )


def chat_local_operator_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "response_visible": False,
        "prompt_body_visible": False,
        "completion_body_visible": False,
        "model_output_authority": False,
        "tool_execution_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "provider_sdk_call_enabled": False,
        "web_fetch_enabled": False,
        "connector_write_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "action_execution_enabled": False,
        "approval_grant_capture_enabled": False,
        "production_authority_enabled": False,
    }


def chat_local_operator_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": "Today",
            "feed_status": "implemented_local_operator_turn_truth_refs",
            "feed_ref": CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
            "authority_boundary": "Chat state is safe operator-turn metadata only.",
        },
        {
            "surface": "Chat",
            "feed_status": "implemented_local_turn_send_and_truth_surface",
            "feed_ref": "/v1/chat/completions",
            "authority_boundary": "Chat output is not truth, memory, approval, or execution authority.",
        },
        {
            "surface": "Plans",
            "feed_status": "proposal_handoff_refs_only",
            "feed_ref": "handoff-ref:chat-to-plans",
            "authority_boundary": "Handoffs are proposal refs only.",
        },
        {
            "surface": "Actions",
            "feed_status": "proposal_handoff_refs_only",
            "feed_ref": "handoff-ref:chat-to-actions",
            "authority_boundary": "Handoffs are proposal refs only.",
        },
        {
            "surface": "Evidence",
            "feed_status": "safe_turn_evidence_refs",
            "feed_ref": "evidence-ref:chat-local-operator",
            "authority_boundary": "Evidence is route/auth/runtime/tool-denial metadata only.",
        },
        {
            "surface": "Memory",
            "feed_status": "blocked_until_cross_surface_memory_intake",
            "feed_ref": "blocked-state:no-chat-memory-write",
            "authority_boundary": "Chat does not write memory or inject context.",
        },
    ]


def _safe_suffix(value: str) -> str:
    lowered = value.strip().lower().replace(":", "-")
    suffix = SAFE_CHAT_SUFFIX_CHARS.sub("-", lowered).strip("-")
    return suffix or "missing"


def _validate_no_denied_fragments(payload: Any) -> None:
    if isinstance(payload, str):
        lowered = payload.lower()
        for fragment in UNSAFE_CHAT_OPERATOR_TEXT_FRAGMENTS:
            if fragment in lowered:
                raise ValueError("Chat local operator envelope contains denied raw content")
        return
    if isinstance(payload, dict):
        for value in payload.values():
            _validate_no_denied_fragments(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _validate_no_denied_fragments(value)
