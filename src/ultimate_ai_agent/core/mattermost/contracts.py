from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from ultimate_ai_agent.core.mattermost.enums import (
    MattermostDecisionStatus,
    MattermostRoleCreationMode,
    MattermostRoleSuggestionStatus,
    MattermostTriggerMode,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret, redact_secret_value
from ultimate_ai_agent.core.time import utc_now

SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
ROLE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,48}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
MAX_PREVIEW_CHARS = 2000
MAX_REPLY_CHARS = 4000


def _validate_safe_ref(value: str, field_name: str) -> str:
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_REF")
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")
    return value


def _validate_role_id(value: str) -> str:
    if not ROLE_ID_RE.match(value):
        raise ValueError("MATTERMOST_ROLE_ID_UNSAFE")
    return value


def _safe_text(value: str, *, max_length: int, field_name: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    if len(text) > max_length:
        raise ValueError(f"{field_name.upper()}_TOO_LONG")
    redacted = redact_secret_value(text)
    if redacted != text or contains_obvious_secret(text):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")
    return text


def safe_hash_preview(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class MattermostWorkspaceRef(RootModel[str]):
    root: str

    @model_validator(mode="after")
    def validate_ref(self) -> Any:
        self.root = _validate_safe_ref(self.root, "workspace_ref")
        return self


class MattermostChannelRef(RootModel[str]):
    root: str

    @model_validator(mode="after")
    def validate_ref(self) -> Any:
        self.root = _validate_safe_ref(self.root, "channel_ref")
        return self


class MattermostThreadRef(RootModel[str]):
    root: str

    @model_validator(mode="after")
    def validate_ref(self) -> Any:
        self.root = _validate_safe_ref(self.root, "thread_ref")
        return self


class MattermostMessageRef(RootModel[str]):
    root: str

    @model_validator(mode="after")
    def validate_ref(self) -> Any:
        self.root = _validate_safe_ref(self.root, "message_ref")
        return self


class _MattermostModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MattermostRoleCard(_MattermostModel):
    role_id: str
    display_name: str
    bot_username: str
    summary: str
    instructions: list[str] = Field(default_factory=list)
    use_when: list[str] = Field(default_factory=list)
    do_not_use_when: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=lambda: ["speak"])
    tool_actions_require_approval: bool = True
    model_output_authoritative: bool = False
    speak_only_by_default: bool = True

    @model_validator(mode="after")
    def validate_role(self) -> Any:
        self.role_id = _validate_role_id(self.role_id)
        self.display_name = _safe_text(self.display_name, max_length=80, field_name="display_name")
        self.bot_username = _validate_role_id(self.bot_username)
        self.summary = _safe_text(self.summary, max_length=500, field_name="summary")
        self.instructions = [
            _safe_text(item, max_length=300, field_name="instruction") for item in self.instructions
        ]
        self.use_when = [_safe_text(item, max_length=200, field_name="use_when") for item in self.use_when]
        self.do_not_use_when = [
            _safe_text(item, max_length=200, field_name="do_not_use_when")
            for item in self.do_not_use_when
        ]
        if not self.allowed_actions:
            raise ValueError("MATTERMOST_ROLE_ALLOWED_ACTION_REQUIRED")
        for action in self.allowed_actions:
            _validate_role_id(action.replace("_", "-"))
        if self.model_output_authoritative:
            raise ValueError("MATTERMOST_MODEL_OUTPUT_AUTHORITY_DENIED")
        if not self.tool_actions_require_approval:
            raise ValueError("MATTERMOST_TOOL_APPROVAL_REQUIRED")
        return self


class MattermostTriggerPolicy(_MattermostModel):
    mode: MattermostTriggerMode = MattermostTriggerMode.mention_command
    mention_names: list[str] = Field(default_factory=list)
    cooldown_seconds: int = Field(default=20, ge=0, le=3600)
    max_replies_per_thread: int = Field(default=2, ge=1, le=12)
    respond_to_bot_messages: bool = False

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        self.mention_names = [
            _validate_role_id(item.lower().lstrip("@")) for item in self.mention_names
        ]
        if self.respond_to_bot_messages:
            raise ValueError("MATTERMOST_BOT_LOOP_DENIED")
        return self


class MattermostRoleBinding(_MattermostModel):
    binding_id: str
    workspace_ref: str
    channel_ref: str
    role_ids: list[str]
    custom_roles: list[MattermostRoleCard] = Field(default_factory=list)
    trigger_policy: MattermostTriggerPolicy = Field(default_factory=MattermostTriggerPolicy)
    role_creation_mode: MattermostRoleCreationMode = MattermostRoleCreationMode.predefined
    reply_enabled: bool = False
    enabled: bool = True
    created_by_ref: str = "mattermost-actor:local"
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_binding(self) -> Any:
        self.binding_id = _validate_safe_ref(self.binding_id, "binding_id")
        self.workspace_ref = _validate_safe_ref(self.workspace_ref, "workspace_ref")
        self.channel_ref = _validate_safe_ref(self.channel_ref, "channel_ref")
        self.created_by_ref = _validate_safe_ref(self.created_by_ref, "created_by_ref")
        if not self.role_ids:
            raise ValueError("MATTERMOST_ROLE_BINDING_ROLE_REQUIRED")
        self.role_ids = [_validate_role_id(role_id) for role_id in self.role_ids]
        return self


class MattermostRoleBindRequest(_MattermostModel):
    workspace_ref: str
    channel_ref: str
    role_ids: list[str]
    custom_roles: list[MattermostRoleCard] = Field(default_factory=list)
    trigger_policy: MattermostTriggerPolicy = Field(default_factory=MattermostTriggerPolicy)
    role_creation_mode: MattermostRoleCreationMode = MattermostRoleCreationMode.predefined
    reply_enabled: bool = False
    created_by_ref: str = "mattermost-actor:local"

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        self.workspace_ref = _validate_safe_ref(self.workspace_ref, "workspace_ref")
        self.channel_ref = _validate_safe_ref(self.channel_ref, "channel_ref")
        self.created_by_ref = _validate_safe_ref(self.created_by_ref, "created_by_ref")
        if not self.role_ids:
            raise ValueError("MATTERMOST_ROLE_BINDING_ROLE_REQUIRED")
        self.role_ids = [_validate_role_id(role_id) for role_id in self.role_ids]
        return self


class MattermostRoleUnbindRequest(_MattermostModel):
    workspace_ref: str
    channel_ref: str
    role_ids: list[str] = Field(default_factory=list)
    actor_ref: str = "mattermost-actor:local"

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        self.workspace_ref = _validate_safe_ref(self.workspace_ref, "workspace_ref")
        self.channel_ref = _validate_safe_ref(self.channel_ref, "channel_ref")
        self.actor_ref = _validate_safe_ref(self.actor_ref, "actor_ref")
        self.role_ids = [_validate_role_id(role_id) for role_id in self.role_ids]
        return self


class MattermostRoleSuggestionRequest(_MattermostModel):
    prompt_preview: str
    role_creation_mode: MattermostRoleCreationMode = MattermostRoleCreationMode.proposal_then_approve
    desired_count: int = Field(default=3, ge=1, le=6)
    auto_create_allowed: bool = False
    actor_ref: str = "mattermost-actor:local"

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        self.prompt_preview = _safe_text(
            self.prompt_preview,
            max_length=MAX_PREVIEW_CHARS,
            field_name="prompt_preview",
        )
        self.actor_ref = _validate_safe_ref(self.actor_ref, "actor_ref")
        return self


class MattermostRoleSuggestion(_MattermostModel):
    suggestion_id: str
    role: MattermostRoleCard
    status: MattermostRoleSuggestionStatus
    requires_approval: bool = True
    reason_codes: list[str] = Field(default_factory=list)


class MattermostMessageEvent(_MattermostModel):
    event_ref: str
    workspace_ref: str
    channel_ref: str
    message_ref: str
    thread_ref: str | None = None
    actor_ref: str = "mattermost-actor:local"
    user_ref: str | None = None
    message_preview: str
    message_sha256: str | None = None
    idempotency_key: str
    mentioned_role_ids: list[str] = Field(default_factory=list)
    is_bot_message: bool = False
    is_direct_mention: bool = False
    command: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_event(self) -> Any:
        self.event_ref = _validate_safe_ref(self.event_ref, "event_ref")
        self.workspace_ref = _validate_safe_ref(self.workspace_ref, "workspace_ref")
        self.channel_ref = _validate_safe_ref(self.channel_ref, "channel_ref")
        self.message_ref = _validate_safe_ref(self.message_ref, "message_ref")
        self.actor_ref = _validate_safe_ref(self.actor_ref, "actor_ref")
        self.idempotency_key = _validate_safe_ref(self.idempotency_key, "idempotency_key")
        if self.thread_ref is not None:
            self.thread_ref = _validate_safe_ref(self.thread_ref, "thread_ref")
        if self.user_ref is not None:
            self.user_ref = _validate_safe_ref(self.user_ref, "user_ref")
        self.message_preview = _safe_text(
            self.message_preview,
            max_length=MAX_PREVIEW_CHARS,
            field_name="message_preview",
        )
        if self.message_sha256 is None:
            self.message_sha256 = safe_hash_preview(self.message_preview)
        if not SHA256_RE.match(self.message_sha256):
            raise ValueError("MATTERMOST_MESSAGE_HASH_INVALID")
        self.mentioned_role_ids = [_validate_role_id(role_id) for role_id in self.mentioned_role_ids]
        if self.command is not None:
            self.command = _safe_text(self.command, max_length=400, field_name="command")
        return self


class MattermostReplyCommand(_MattermostModel):
    command_ref: str
    role_id: str
    bot_username: str
    channel_ref: str
    thread_ref: str | None = None
    reply_preview: str
    reply_kind: str = "in_channel"
    approval_required: bool = False
    approval_ref: str | None = None

    @model_validator(mode="after")
    def validate_command(self) -> Any:
        self.command_ref = _validate_safe_ref(self.command_ref, "command_ref")
        self.role_id = _validate_role_id(self.role_id)
        self.bot_username = _validate_role_id(self.bot_username)
        self.channel_ref = _validate_safe_ref(self.channel_ref, "channel_ref")
        if self.thread_ref is not None:
            self.thread_ref = _validate_safe_ref(self.thread_ref, "thread_ref")
        self.reply_preview = _safe_text(
            self.reply_preview,
            max_length=MAX_REPLY_CHARS,
            field_name="reply_preview",
        )
        if self.reply_kind not in {"in_channel", "ephemeral"}:
            raise ValueError("MATTERMOST_REPLY_KIND_UNSUPPORTED")
        if self.approval_ref is not None:
            self.approval_ref = _validate_safe_ref(self.approval_ref, "approval_ref")
        return self


class MattermostBridgeReceipt(_MattermostModel):
    receipt_ref: str
    event_ref: str | None = None
    decision_ref: str
    workspace_ref: str | None = None
    channel_ref: str | None = None
    message_ref: str | None = None
    status: MattermostDecisionStatus
    role_ids: list[str] = Field(default_factory=list)
    reply_command_count: int = Field(default=0, ge=0)
    approval_required: bool = False
    approval_ref: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    stored_raw_transcript: bool = False
    connector_write_performed_by_uaa: bool = False
    model_output_authoritative: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_receipt(self) -> Any:
        self.receipt_ref = _validate_safe_ref(self.receipt_ref, "receipt_ref")
        self.decision_ref = _validate_safe_ref(self.decision_ref, "decision_ref")
        for field_name in ("event_ref", "workspace_ref", "channel_ref", "message_ref", "approval_ref"):
            value = getattr(self, field_name)
            if value is not None:
                setattr(self, field_name, _validate_safe_ref(value, field_name))
        self.role_ids = [_validate_role_id(role_id) for role_id in self.role_ids]
        if self.stored_raw_transcript:
            raise ValueError("MATTERMOST_RAW_TRANSCRIPT_STORAGE_DENIED")
        if self.connector_write_performed_by_uaa:
            raise ValueError("MATTERMOST_UAA_CONNECTOR_WRITE_DENIED")
        if self.model_output_authoritative:
            raise ValueError("MATTERMOST_MODEL_OUTPUT_AUTHORITY_DENIED")
        return self


class MattermostAgentDecision(_MattermostModel):
    decision_ref: str
    run_id: str
    status: MattermostDecisionStatus
    reason_codes: list[str] = Field(default_factory=list)
    reply_commands: list[MattermostReplyCommand] = Field(default_factory=list)
    approval_required: bool = False
    approval_ref: str | None = None
    receipt: MattermostBridgeReceipt
    latency_ms: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        self.decision_ref = _validate_safe_ref(self.decision_ref, "decision_ref")
        self.run_id = _validate_safe_ref(self.run_id, "run_id")
        if self.approval_ref is not None:
            self.approval_ref = _validate_safe_ref(self.approval_ref, "approval_ref")
        if self.status == MattermostDecisionStatus.approval_required and not self.approval_required:
            raise ValueError("MATTERMOST_APPROVAL_FLAG_REQUIRED")
        return self


class MattermostAuditEvent(_MattermostModel):
    audit_ref: str
    event_type: str
    workspace_ref: str | None = None
    channel_ref: str | None = None
    message_ref: str | None = None
    decision_ref: str | None = None
    receipt_ref: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_audit(self) -> Any:
        self.audit_ref = _validate_safe_ref(self.audit_ref, "audit_ref")
        self.safe_summary = _safe_text(self.safe_summary, max_length=800, field_name="safe_summary")
        for field_name in ("workspace_ref", "channel_ref", "message_ref", "decision_ref", "receipt_ref"):
            value = getattr(self, field_name)
            if value is not None:
                setattr(self, field_name, _validate_safe_ref(value, field_name))
        return self


class MattermostBridgeStatus(_MattermostModel):
    bridge_ref: str = "mattermost-bridge:local"
    enabled: bool
    local_self_hosted: bool = True
    reply_enabled: bool = False
    auto_create_roles_enabled: bool = False
    storage_ref: str
    role_count: int
    trigger_modes: list[MattermostTriggerMode]
    role_creation_modes: list[MattermostRoleCreationMode]
    capabilities_declared: list[str]
    capabilities_blocked: list[str]


def safe_model_dump(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return dict(value)
