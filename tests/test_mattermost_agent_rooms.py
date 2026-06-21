from typing import Any
from pathlib import Path
import pytest

from ultimate_ai_agent.core.mattermost import (
    MattermostBridgeConfig,
    MattermostBridgeService,
    MattermostMessageEvent,
    MattermostRoleBindRequest,
    MattermostRoleCreationMode,
    MattermostRoleSuggestionRequest,
    MattermostRoleSuggestionStatus,
    MattermostTriggerMode,
    MattermostTriggerPolicy,
    list_predefined_roles,
)
from ultimate_ai_agent.core.mattermost.roles import build_custom_role_from_prompt
from ultimate_ai_agent.core.mattermost.storage import MattermostBridgeStore


def _service(tmp_path: Path, *, reply_enabled: bool = True, auto_create: bool = False) -> Any:
    return MattermostBridgeService(
        config=MattermostBridgeConfig(
            enabled=True,
            reply_enabled=reply_enabled,
            auto_create_roles_enabled=auto_create,
            storage_dir=str(tmp_path),
        ),
        store=MattermostBridgeStore(tmp_path),
    )


def _bind(service: Any, *, mode: str = MattermostTriggerMode.mention_command, roles: Any | None = None) -> Any:
    return service.bind_roles(
        MattermostRoleBindRequest(
            workspace_ref="mattermost-workspace:local",
            channel_ref="mattermost-channel:town-square",
            role_ids=roles or ["planner", "critic"],
            trigger_policy=MattermostTriggerPolicy(mode=mode, max_replies_per_thread=2),
            reply_enabled=True,
            created_by_ref="mattermost-user:admin",
        )
    )


def _event(**updates: Any) -> Any:
    payload = {
        "event_ref": "mattermost-event:post1",
        "workspace_ref": "mattermost-workspace:local",
        "channel_ref": "mattermost-channel:town-square",
        "message_ref": "mattermost-message:post1",
        "thread_ref": "mattermost-thread:root1",
        "actor_ref": "mattermost-actor:plugin",
        "user_ref": "mattermost-user:alice",
        "message_preview": "@uaa-planner help us plan this",
        "idempotency_key": "mattermost-idempotency:post1",
        "mentioned_role_ids": ["planner"],
        "is_direct_mention": True,
    }
    payload.update(updates)
    return MattermostMessageEvent(**payload)


def test_predefined_role_catalog_is_stable_and_speak_only() -> None:
    roles = list_predefined_roles()
    role_ids = [role.role_id for role in roles]

    assert role_ids == [
        "planner",
        "summarizer",
        "critic",
        "implementer",
        "safety-reviewer",
        "facilitator",
    ]
    assert all(role.speak_only_by_default is True for role in roles)
    assert all(role.tool_actions_require_approval is True for role in roles)
    assert all(role.model_output_authoritative is False for role in roles)


def test_mattermost_event_rejects_secret_like_preview() -> None:
    with pytest.raises(ValueError, match="MESSAGE_PREVIEW_SECRET_LIKE"):
        _event(message_preview="Authorization: Bearer abcdefghijklmnop")


def test_role_suggestion_modes_include_predefined_proposal_and_auto_create(tmp_path: Path) -> None:
    service = _service(tmp_path, auto_create=False)

    predefined = service.suggest_roles(
        MattermostRoleSuggestionRequest(
            prompt_preview="We need a plan and a safety review",
            role_creation_mode=MattermostRoleCreationMode.predefined,
            desired_count=2,
        )
    )
    proposed = service.suggest_roles(
        MattermostRoleSuggestionRequest(
            prompt_preview="We need a plan and a safety review",
            role_creation_mode=MattermostRoleCreationMode.proposal_then_approve,
            desired_count=2,
        )
    )
    blocked = service.suggest_roles(
        MattermostRoleSuggestionRequest(
            prompt_preview="Invent an incident commander",
            role_creation_mode=MattermostRoleCreationMode.auto_create,
            auto_create_allowed=True,
            desired_count=1,
        )
    )
    auto_service = _service(tmp_path / "auto", auto_create=True)
    auto_created = auto_service.suggest_roles(
        MattermostRoleSuggestionRequest(
            prompt_preview="Invent an incident commander",
            role_creation_mode=MattermostRoleCreationMode.auto_create,
            auto_create_allowed=True,
            desired_count=1,
        )
    )

    assert predefined[0].status == MattermostRoleSuggestionStatus.predefined
    assert predefined[0].requires_approval is False
    assert proposed[0].status == MattermostRoleSuggestionStatus.proposed
    assert proposed[0].requires_approval is True
    assert blocked[0].status == MattermostRoleSuggestionStatus.blocked
    assert "MATTERMOST_AUTO_CREATE_DISABLED" in blocked[0].reason_codes
    assert auto_created[0].status == MattermostRoleSuggestionStatus.auto_created
    assert auto_created[0].role.speak_only_by_default is True


def test_mention_trigger_proposes_role_reply_and_records_receipt(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _bind(service)

    decision = service.handle_message_event(_event())

    assert decision.status.value == "reply_proposed"
    assert decision.reply_commands[0].role_id == "planner"
    assert decision.receipt.stored_raw_transcript is False
    assert decision.receipt.connector_write_performed_by_uaa is False
    assert decision.receipt.latency_ms is not None
    assert service.audit_events()
    assert service.receipts()
    stored = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.glob("*.jsonl"))
    assert "@uaa-planner help us plan this" not in stored


def test_enabled_room_allows_unmentioned_message(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _bind(service, mode=MattermostTriggerMode.enabled_room, roles=["summarizer"])

    decision = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post2",
            message_ref="mattermost-message:post2",
            idempotency_key="mattermost-idempotency:post2",
            message_preview="Please recap the thread",
            mentioned_role_ids=[],
            is_direct_mention=False,
        )
    )

    assert decision.status.value == "reply_proposed"
    assert decision.reply_commands[0].role_id == "summarizer"


def test_cooldown_suppresses_second_reply_in_same_thread(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _bind(service)

    first = service.handle_message_event(_event())
    second = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post-cooldown",
            message_ref="mattermost-message:post-cooldown",
            idempotency_key="mattermost-idempotency:post-cooldown",
        )
    )

    assert first.status.value == "reply_proposed"
    assert second.status.value == "ignored"
    assert "MATTERMOST_COOLDOWN_ACTIVE" in second.reason_codes


def test_bot_message_and_duplicate_events_are_suppressed(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _bind(service)

    bot_decision = service.handle_message_event(_event(is_bot_message=True))
    first = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post3",
            message_ref="mattermost-message:post3",
            idempotency_key="mattermost-idempotency:post3",
        )
    )
    duplicate = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post3",
            message_ref="mattermost-message:post3",
            idempotency_key="mattermost-idempotency:post3",
        )
    )

    assert bot_decision.status.value == "ignored"
    assert "MATTERMOST_BOT_MESSAGE_IGNORED" in bot_decision.reason_codes
    assert first.status.value == "reply_proposed"
    assert duplicate.status.value == "duplicate"


def test_tool_like_action_requires_approval_instead_of_reply(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _bind(service, mode=MattermostTriggerMode.enabled_room)

    decision = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post4",
            message_ref="mattermost-message:post4",
            idempotency_key="mattermost-idempotency:post4",
            message_preview="@uaa-implementer execute this external tool",
            mentioned_role_ids=["implementer"],
        )
    )

    assert decision.status.value == "approval_required"
    assert decision.approval_required is True
    assert decision.reply_commands == []
    assert decision.approval_ref == "approval:mattermost:post4"


def test_auto_created_custom_role_can_be_bound_and_reply_safely(tmp_path: Path) -> None:
    service = _service(tmp_path, auto_create=True)
    custom = build_custom_role_from_prompt("incident commander", 1)
    assert "incident" not in custom.role_id
    assert "commander" not in custom.role_id
    service.bind_roles(
        MattermostRoleBindRequest(
            workspace_ref="mattermost-workspace:local",
            channel_ref="mattermost-channel:town-square",
            role_ids=[custom.role_id],
            custom_roles=[custom],
            role_creation_mode=MattermostRoleCreationMode.auto_create,
            trigger_policy=MattermostTriggerPolicy(mode=MattermostTriggerMode.enabled_room),
            reply_enabled=True,
        )
    )

    decision = service.handle_message_event(
        _event(
            event_ref="mattermost-event:post5",
            message_ref="mattermost-message:post5",
            idempotency_key="mattermost-idempotency:post5",
            message_preview="Who should coordinate?",
            mentioned_role_ids=[],
        )
    )

    assert decision.status.value == "reply_proposed"
    assert decision.reply_commands[0].role_id == custom.role_id
    assert "approval" in decision.reply_commands[0].reply_preview.lower()
