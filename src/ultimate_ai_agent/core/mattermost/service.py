from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Mapping

from ultimate_ai_agent.core.mattermost.api_safety import (
    mattermost_auto_create_roles_enabled,
    mattermost_bridge_enabled,
    mattermost_bridge_storage_dir,
    mattermost_reply_enabled,
)
from ultimate_ai_agent.core.mattermost.contracts import (
    MattermostAgentDecision,
    MattermostAuditEvent,
    MattermostBridgeReceipt,
    MattermostBridgeStatus,
    MattermostMessageEvent,
    MattermostReplyCommand,
    MattermostRoleBindRequest,
    MattermostRoleBinding,
    MattermostRoleSuggestion,
    MattermostRoleSuggestionRequest,
    MattermostRoleUnbindRequest,
)
from ultimate_ai_agent.core.mattermost.enums import (
    MattermostDecisionStatus,
    MattermostRoleCreationMode,
    MattermostRoleSuggestionStatus,
    MattermostTriggerMode,
)
from ultimate_ai_agent.core.mattermost.roles import (
    build_custom_role_from_prompt,
    get_predefined_role,
    list_predefined_roles,
    suggest_predefined_role_ids,
)
from ultimate_ai_agent.core.mattermost.storage import MattermostBridgeStore
from ultimate_ai_agent.core.time import utc_now


@dataclass(frozen=True)
class MattermostBridgeConfig:
    enabled: bool
    reply_enabled: bool
    auto_create_roles_enabled: bool
    storage_dir: str

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "MattermostBridgeConfig":
        return cls(
            enabled=mattermost_bridge_enabled(values),
            reply_enabled=mattermost_reply_enabled(values),
            auto_create_roles_enabled=mattermost_auto_create_roles_enabled(values),
            storage_dir=mattermost_bridge_storage_dir(values),
        )


class MattermostBridgeService:
    def __init__(self, config: MattermostBridgeConfig, store: MattermostBridgeStore | None = None):
        self.config = config
        self.store = store or MattermostBridgeStore(config.storage_dir)

    @classmethod
    def from_env(cls, values: Mapping[str, str] | None = None) -> "MattermostBridgeService":
        config = MattermostBridgeConfig.from_env(values)
        return cls(config=config)

    def status(self) -> MattermostBridgeStatus:
        return MattermostBridgeStatus(
            enabled=self.config.enabled,
            reply_enabled=self.config.reply_enabled,
            auto_create_roles_enabled=self.config.auto_create_roles_enabled,
            storage_ref=self.store.storage_ref,
            role_count=len(list_predefined_roles()),
            trigger_modes=list(MattermostTriggerMode),
            role_creation_modes=list(MattermostRoleCreationMode),
            capabilities_declared=[
                "mattermost_agent_rooms_disabled_by_default",
                "mattermost_role_catalog",
                "mattermost_redacted_message_ingress",
                "mattermost_role_bound_speak_only_replies",
                "mattermost_approval_required_tool_actions",
            ],
            capabilities_blocked=[
                "mattermost_raw_transcript_storage",
                "mattermost_unapproved_connector_writes",
                "mattermost_model_output_authority",
                "mattermost_unbounded_background_autonomy",
            ],
        )

    def role_catalog(self) -> list[dict]:
        return [role.model_dump(mode="json") for role in list_predefined_roles()]

    def suggest_roles(self, request: MattermostRoleSuggestionRequest) -> list[MattermostRoleSuggestion]:
        role_ids = suggest_predefined_role_ids(request.prompt_preview, request.desired_count)
        if request.role_creation_mode == MattermostRoleCreationMode.predefined:
            return [
                MattermostRoleSuggestion(
                    suggestion_id=f"mattermost-role-suggestion:{role_id}",
                    role=get_predefined_role(role_id),
                    status=MattermostRoleSuggestionStatus.predefined,
                    requires_approval=False,
                    reason_codes=["MATTERMOST_PREDEFINED_ROLE_SELECTED"],
                )
                for role_id in role_ids
                if get_predefined_role(role_id) is not None
            ]

        if request.role_creation_mode == MattermostRoleCreationMode.auto_create:
            if not (self.config.auto_create_roles_enabled and request.auto_create_allowed):
                blocked_role = build_custom_role_from_prompt(request.prompt_preview, 1)
                return [
                    MattermostRoleSuggestion(
                        suggestion_id=f"mattermost-role-suggestion:{blocked_role.role_id}",
                        role=blocked_role,
                        status=MattermostRoleSuggestionStatus.blocked,
                        requires_approval=True,
                        reason_codes=["MATTERMOST_AUTO_CREATE_DISABLED"],
                    )
                ]
            return [
                MattermostRoleSuggestion(
                    suggestion_id=f"mattermost-role-suggestion:auto:{index}",
                    role=build_custom_role_from_prompt(request.prompt_preview, index),
                    status=MattermostRoleSuggestionStatus.auto_created,
                    requires_approval=False,
                    reason_codes=["MATTERMOST_AUTO_CREATED_SPEAK_ONLY_ROLE"],
                )
                for index in range(1, request.desired_count + 1)
            ]

        return [
            MattermostRoleSuggestion(
                suggestion_id=f"mattermost-role-suggestion:{role_id}",
                role=get_predefined_role(role_id),
                status=MattermostRoleSuggestionStatus.proposed,
                requires_approval=True,
                reason_codes=["MATTERMOST_ROLE_APPROVAL_REQUIRED"],
            )
            for role_id in role_ids
            if get_predefined_role(role_id) is not None
        ]

    def bind_roles(self, request: MattermostRoleBindRequest) -> MattermostRoleBinding:
        if request.role_creation_mode == MattermostRoleCreationMode.auto_create and not self.config.auto_create_roles_enabled:
            raise ValueError("MATTERMOST_AUTO_CREATE_DISABLED")
        custom_role_ids = {role.role_id for role in request.custom_roles}
        unknown = [
            role_id
            for role_id in request.role_ids
            if get_predefined_role(role_id) is None and role_id not in custom_role_ids
        ]
        if unknown and request.role_creation_mode != MattermostRoleCreationMode.auto_create:
            raise ValueError("MATTERMOST_UNKNOWN_ROLE")
        if unknown:
            raise ValueError("MATTERMOST_CUSTOM_ROLE_CARD_REQUIRED")
        binding = MattermostRoleBinding(
            binding_id=f"mattermost-binding:{_suffix(request.workspace_ref)}:{_suffix(request.channel_ref)}",
            workspace_ref=request.workspace_ref,
            channel_ref=request.channel_ref,
            role_ids=request.role_ids,
            custom_roles=request.custom_roles,
            trigger_policy=request.trigger_policy,
            role_creation_mode=request.role_creation_mode,
            reply_enabled=request.reply_enabled and self.config.reply_enabled,
            enabled=True,
            created_by_ref=request.created_by_ref,
        )
        saved = self.store.save_binding(binding)
        self._record_audit(
            event_type="role_binding_saved",
            workspace_ref=saved.workspace_ref,
            channel_ref=saved.channel_ref,
            safe_summary="Mattermost role binding saved with safe refs only.",
            reason_codes=["MATTERMOST_ROLE_BINDING_SAVED"],
        )
        return saved

    def unbind_roles(self, request: MattermostRoleUnbindRequest) -> MattermostRoleBinding | None:
        updated = self.store.unbind_roles(request.workspace_ref, request.channel_ref, request.role_ids)
        self._record_audit(
            event_type="role_binding_removed",
            workspace_ref=request.workspace_ref,
            channel_ref=request.channel_ref,
            safe_summary="Mattermost role binding removed or disabled with safe refs only.",
            reason_codes=["MATTERMOST_ROLE_BINDING_REMOVED"],
        )
        return updated

    def handle_message_event(self, event: MattermostMessageEvent) -> MattermostAgentDecision:
        started = time.perf_counter()
        if self.store.idempotency_seen(event.idempotency_key):
            return self._decision(
                event=event,
                status=MattermostDecisionStatus.duplicate,
                reason_codes=["MATTERMOST_DUPLICATE_EVENT_IGNORED"],
                started=started,
            )

        binding = self.store.find_binding(event.workspace_ref, event.channel_ref)
        if binding is None or not binding.enabled or not binding.role_ids:
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.ignored,
                reason_codes=["MATTERMOST_CHANNEL_NOT_BOUND"],
                started=started,
            )
        if event.is_bot_message and not binding.trigger_policy.respond_to_bot_messages:
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.ignored,
                reason_codes=["MATTERMOST_BOT_MESSAGE_IGNORED"],
                started=started,
            )
        if not self._trigger_matches(event, binding):
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.ignored,
                reason_codes=["MATTERMOST_TRIGGER_NOT_MATCHED"],
                started=started,
            )
        if self._requires_tool_approval(event.message_preview):
            approval_ref = f"approval:mattermost:{_suffix(event.message_ref)}"
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.approval_required,
                reason_codes=["MATTERMOST_TOOL_ACTION_APPROVAL_REQUIRED"],
                started=started,
                approval_ref=approval_ref,
                approval_required=True,
            )
        if self._cooldown_active(event, binding):
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.ignored,
                reason_codes=["MATTERMOST_COOLDOWN_ACTIVE"],
                started=started,
            )

        selected_roles = self._select_roles(event, binding)
        commands = [
            self._reply_command(event, binding, role_id, index)
            for index, role_id in enumerate(selected_roles, start=1)
            if self._role_for_binding(binding, role_id) is not None
        ]
        if not commands or not binding.reply_enabled:
            return self._finish_event(
                event=event,
                status=MattermostDecisionStatus.ignored,
                reason_codes=["MATTERMOST_REPLY_DISABLED"],
                started=started,
            )
        return self._finish_event(
            event=event,
            status=MattermostDecisionStatus.reply_proposed,
            reason_codes=["MATTERMOST_REPLY_COMMANDS_PROPOSED"],
            started=started,
            reply_commands=commands,
        )

    def audit_events(self, limit: int = 100) -> list[dict]:
        return [event.model_dump(mode="json") for event in self.store.audit_events(limit)]

    def receipts(self, limit: int = 100) -> list[dict]:
        return [receipt.model_dump(mode="json") for receipt in self.store.receipts(limit)]

    def _finish_event(
        self,
        *,
        event: MattermostMessageEvent,
        status: MattermostDecisionStatus,
        reason_codes: list[str],
        started: float,
        reply_commands: list[MattermostReplyCommand] | None = None,
        approval_required: bool = False,
        approval_ref: str | None = None,
    ) -> MattermostAgentDecision:
        decision = self._decision(
            event=event,
            status=status,
            reason_codes=reason_codes,
            started=started,
            reply_commands=reply_commands,
            approval_required=approval_required,
            approval_ref=approval_ref,
        )
        self.store.record_idempotency(event.idempotency_key, decision.decision_ref)
        self.store.append_receipt(decision.receipt)
        if decision.status == MattermostDecisionStatus.reply_proposed and decision.reply_commands:
            self.store.record_cooldown(self._cooldown_scope(event), decision.decision_ref)
        self._record_audit(
            event_type="message_event_decision",
            workspace_ref=event.workspace_ref,
            channel_ref=event.channel_ref,
            message_ref=event.message_ref,
            decision_ref=decision.decision_ref,
            receipt_ref=decision.receipt.receipt_ref,
            safe_summary="Mattermost message event processed without raw transcript persistence.",
            reason_codes=reason_codes,
        )
        return decision

    def _decision(
        self,
        *,
        event: MattermostMessageEvent,
        status: MattermostDecisionStatus,
        reason_codes: list[str],
        started: float,
        reply_commands: list[MattermostReplyCommand] | None = None,
        approval_required: bool = False,
        approval_ref: str | None = None,
    ) -> MattermostAgentDecision:
        latency_ms = (time.perf_counter() - started) * 1000
        decision_ref = f"mattermost-decision:{_suffix(event.message_ref)}"
        role_ids = [command.role_id for command in reply_commands or []]
        receipt = MattermostBridgeReceipt(
            receipt_ref=f"mattermost-receipt:{_suffix(event.message_ref)}",
            event_ref=event.event_ref,
            decision_ref=decision_ref,
            workspace_ref=event.workspace_ref,
            channel_ref=event.channel_ref,
            message_ref=event.message_ref,
            status=status,
            role_ids=role_ids,
            reply_command_count=len(reply_commands or []),
            approval_required=approval_required,
            approval_ref=approval_ref,
            latency_ms=latency_ms,
            reason_codes=reason_codes,
        )
        return MattermostAgentDecision(
            decision_ref=decision_ref,
            run_id=f"mattermost-run:{_suffix(event.message_ref)}",
            status=status,
            reason_codes=reason_codes,
            reply_commands=reply_commands or [],
            approval_required=approval_required,
            approval_ref=approval_ref,
            receipt=receipt,
            latency_ms=latency_ms,
        )

    def _record_audit(
        self,
        *,
        event_type: str,
        safe_summary: str,
        reason_codes: list[str],
        workspace_ref: str | None = None,
        channel_ref: str | None = None,
        message_ref: str | None = None,
        decision_ref: str | None = None,
        receipt_ref: str | None = None,
    ) -> None:
        ref_source = receipt_ref or decision_ref or message_ref or channel_ref or "system"
        self.store.append_audit_event(
            MattermostAuditEvent(
                audit_ref=f"mattermost-audit:{_suffix(ref_source)}:{event_type}",
                event_type=event_type,
                workspace_ref=workspace_ref,
                channel_ref=channel_ref,
                message_ref=message_ref,
                decision_ref=decision_ref,
                receipt_ref=receipt_ref,
                reason_codes=reason_codes,
                safe_summary=safe_summary,
            )
        )

    def _trigger_matches(self, event: MattermostMessageEvent, binding: MattermostRoleBinding) -> bool:
        mode = binding.trigger_policy.mode
        if event.command:
            return True
        if mode == MattermostTriggerMode.mention_command:
            return event.is_direct_mention or bool(set(event.mentioned_role_ids).intersection(binding.role_ids))
        if mode == MattermostTriggerMode.enabled_room:
            return True
        if mode == MattermostTriggerMode.always_on_by_role:
            return True
        return False

    def _select_roles(self, event: MattermostMessageEvent, binding: MattermostRoleBinding) -> list[str]:
        selected = [role_id for role_id in event.mentioned_role_ids if role_id in binding.role_ids]
        if not selected:
            selected = binding.role_ids
        return selected[: binding.trigger_policy.max_replies_per_thread]

    def _cooldown_active(self, event: MattermostMessageEvent, binding: MattermostRoleBinding) -> bool:
        cooldown_seconds = binding.trigger_policy.cooldown_seconds
        if cooldown_seconds <= 0:
            return False
        latest = self.store.latest_cooldown_at(self._cooldown_scope(event))
        if latest is None:
            return False
        try:
            elapsed_seconds = (utc_now() - latest).total_seconds()
        except TypeError:
            return False
        return elapsed_seconds < cooldown_seconds

    @staticmethod
    def _cooldown_scope(event: MattermostMessageEvent) -> str:
        thread_or_channel_ref = event.thread_ref or event.channel_ref
        return f"mattermost-cooldown:{_suffix(event.workspace_ref)}:{_suffix(thread_or_channel_ref)}"

    def _reply_command(
        self,
        event: MattermostMessageEvent,
        binding: MattermostRoleBinding,
        role_id: str,
        index: int,
    ) -> MattermostReplyCommand:
        role = self._role_for_binding(binding, role_id)
        if role is None:
            raise ValueError("MATTERMOST_UNKNOWN_ROLE")
        return MattermostReplyCommand(
            command_ref=f"mattermost-reply:{_suffix(event.message_ref)}:{index}",
            role_id=role.role_id,
            bot_username=role.bot_username,
            channel_ref=event.channel_ref,
            thread_ref=event.thread_ref,
            reply_preview=(
                f"{role.display_name}: I can help from the {role.role_id} role. "
                "Any tool or connector action will stay behind UAA approval."
            ),
        )

    @staticmethod
    def _requires_tool_approval(message_preview: str) -> bool:
        lowered = message_preview.lower()
        markers = ("execute", "delete", "write", "send", "publish", "external", "tool", "capability")
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _role_for_binding(binding: MattermostRoleBinding, role_id: str):
        predefined = get_predefined_role(role_id)
        if predefined is not None:
            return predefined
        for role in binding.custom_roles:
            if role.role_id == role_id:
                return role
        return None


def _suffix(value: str) -> str:
    return value.split(":")[-1].replace("_", "-")[:64]
