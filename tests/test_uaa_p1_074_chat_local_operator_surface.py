import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.chat import (
    CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS,
    CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS,
    CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF,
    ChatLocalOperatorTurnEnvelope,
    build_chat_local_operator_turn_envelope,
    chat_local_operator_authority_posture,
    chat_local_operator_surface_bindings,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


def test_chat_local_operator_turn_envelope_denies_authority_flags() -> None:
    envelope = build_chat_local_operator_turn_envelope(
        model_ref="model-ref:local-chat-gateway",
        runtime_truth="runtime-readiness-gated",
        auth_truth="local-bearer-required",
        tool_denial_truth="tools-functions-streaming-denied",
    )
    payload = envelope.model_dump(mode="json")

    assert payload["contract_ref"] == CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
    assert payload["turn_ref"] == "chat-turn:local-operator:model-ref-local-chat-gateway"
    assert payload["route_ref"] == "/v1/chat/completions"
    assert payload["plans_handoff_ref"].startswith("handoff-ref:chat-to-plans:")
    assert payload["actions_handoff_ref"].startswith("handoff-ref:chat-to-actions:")
    assert payload["response_visible"] is False
    assert payload["prompt_body_visible"] is False
    assert payload["completion_body_visible"] is False
    assert payload["model_output_authority"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["memory_write_authorized"] is False
    assert payload["context_injection_authorized"] is False
    assert payload["provider_sdk_call_enabled"] is False
    assert payload["web_fetch_enabled"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["shell_subprocess_execution_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["approval_grant_capture_enabled"] is False
    assert payload["production_authority_enabled"] is False
    assert set(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS) <= set(
        payload["blocked_state_refs"]
    )

    for denied_flag in [
        "response_visible",
        "prompt_body_visible",
        "completion_body_visible",
        "model_output_authority",
        "tool_execution_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "provider_sdk_call_enabled",
        "web_fetch_enabled",
        "connector_write_enabled",
        "shell_subprocess_execution_enabled",
        "action_execution_enabled",
        "approval_grant_capture_enabled",
        "production_authority_enabled",
    ]:
        unsafe = dict(payload)
        unsafe[denied_flag] = True
        with pytest.raises(ValidationError):
            ChatLocalOperatorTurnEnvelope(**unsafe)


def test_chat_local_operator_envelope_rejects_raw_content() -> None:
    payload = build_chat_local_operator_turn_envelope(
        model_ref="model-ref:local-chat-gateway",
    ).model_dump(mode="json")
    payload["safe_summary"] = "raw prompt material"
    with pytest.raises(ValidationError):
        ChatLocalOperatorTurnEnvelope(**payload)


def test_chat_local_operator_posture_and_surface_bindings() -> None:
    posture = chat_local_operator_authority_posture()
    bindings = chat_local_operator_surface_bindings()

    assert posture["safe_refs_only"] is True
    assert posture["model_output_authority"] is False
    assert posture["tool_execution_enabled"] is False
    assert posture["memory_write_authorized"] is False
    assert {binding["surface"] for binding in bindings} == {
        "Today",
        "Chat",
        "Plans",
        "Actions",
        "Evidence",
        "Memory",
    }


def test_founder_loop_today_binds_chat_local_operator_surface(tmp_path) -> None:
    repo = FounderLoopRepository(tmp_path, seed_defaults=True)
    today = repo.today_summary()

    assert today["chat_local_operator_contract_ref"] == (
        CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF
    )
    assert today["chat_local_operator_status"] == "implemented_local_turn_truth_surface"
    assert today["chat_local_operator_route_ref"] == "/v1/chat/completions"
    assert today["chat_local_operator_runtime_truth"] == "runtime-readiness-gated"
    assert today["chat_local_operator_auth_truth"] == "local-bearer-required"
    assert (
        today["chat_local_operator_tool_denial_truth"]
        == "tools-functions-streaming-denied"
    )
    assert today["chat_local_operator_required_truth_fields"] == (
        CHAT_LOCAL_OPERATOR_REQUIRED_TRUTH_FIELDS
    )
    assert set(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS) <= set(
        today["chat_local_operator_blocked_state_refs"]
    )
    assert (
        today["chat_local_operator_authority_posture"]["model_output_authority"]
        is False
    )
    assert (
        today["chat_local_operator_authority_posture"]["memory_write_authorized"]
        is False
    )

    module_feeds = {item["module"]: item for item in today["module_feed_contract"]}
    assert module_feeds["Chat"]["status"] == "implemented_local_operator_surface_contract"
    assert CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF in module_feeds["Chat"][
        "current_feed_refs"
    ]

    timeline = today["evidence_timeline"]
    chat_item = next(
        item for item in timeline if item["item_kind"] == "chat_local_operator_turn_ref"
    )
    assert CHAT_LOCAL_OPERATOR_SURFACE_CONTRACT_REF in chat_item["status_refs"]
    assert chat_item["history_answers"]["approved"]["status"] == "blocked"
    assert chat_item["memory_truth_authority"] is False
    assert chat_item["raw_evidence_included"] is False
    assert set(CHAT_LOCAL_OPERATOR_REQUIRED_BLOCKED_REFS) <= set(
        chat_item["blocked_states"]
    )
