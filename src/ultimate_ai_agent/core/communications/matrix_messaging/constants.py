from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_MESSAGING_SCHEMA_VERSION = "uaa-matrix-messaging.v1"
MATRIX_MESSAGING_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_MESSAGING_RUNTIME_REF = "runtime-ref:matrix-rust-sdk:0.18.0"
MATRIX_MESSAGING_TARGET_REF = "target-ref:communications:matrix-exact-message"
MATRIX_MESSAGING_BUDGET_REF = "budget-ref:matrix-messaging:zero-cost-v1"
MATRIX_MESSAGING_SAFE_DISABLE_REF = "safe-disable-ref:matrix-messenger:enabled"
MATRIX_MESSAGING_KILL_SWITCH_REF = "kill-switch-ref:matrix-messenger:clear"
MATRIX_MESSAGING_OUTBOX_SCHEMA_REF = "outbox-schema-ref:matrix:encrypted-v1"
MATRIX_MESSAGING_OUTBOX_KEY_ITEM_REF = "key-item-ref:matrix-outbox:dedicated-v1"
MATRIX_MESSAGING_OUTBOX_KEY_VERSION_REF = "key-version-ref:matrix-outbox:v1"
MATRIX_MESSAGING_NOTIFICATION_TARGET_REF = (
    "notification-target-ref:macos:user-session"
)
MATRIX_MESSAGING_NOTIFICATION_POLICY_REF = (
    "notification-policy-ref:matrix-messenger:manual-approved-v1"
)
MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF = (
    "notification-disclosure-ref:matrix-messenger:generic-no-content-v1"
)
MATRIX_MESSAGING_MAX_OUTBOX_RECORDS = 256


class MatrixMessagingOperation(str, Enum):
    send = "send"
    reply = "reply"
    thread = "thread"
    reaction = "reaction"
    edit = "edit"
    redaction = "redaction"
    typing = "typing"
    read_receipt = "read_receipt"
    draft_write = "draft_write"
    draft_read = "draft_read"
    outbox_enqueue = "outbox_enqueue"
    outbox_read = "outbox_read"
    outbox_transition = "outbox_transition"
    outbox_discard = "outbox_discard"
    desktop_notify = "desktop_notify"


NETWORK_OPERATIONS = frozenset(
    {
        MatrixMessagingOperation.send,
        MatrixMessagingOperation.reply,
        MatrixMessagingOperation.thread,
        MatrixMessagingOperation.reaction,
        MatrixMessagingOperation.edit,
        MatrixMessagingOperation.redaction,
        MatrixMessagingOperation.typing,
        MatrixMessagingOperation.read_receipt,
    }
)
MESSAGE_CONTENT_OPERATIONS = frozenset(
    {
        MatrixMessagingOperation.send,
        MatrixMessagingOperation.reply,
        MatrixMessagingOperation.thread,
        MatrixMessagingOperation.edit,
        MatrixMessagingOperation.draft_write,
        MatrixMessagingOperation.outbox_enqueue,
    }
)
CONTENT_FINGERPRINT_OPERATIONS = MESSAGE_CONTENT_OPERATIONS | {
    MatrixMessagingOperation.reaction,
    MatrixMessagingOperation.desktop_notify,
}
EVENT_SCOPED_OPERATIONS = frozenset(
    {
        MatrixMessagingOperation.reply,
        MatrixMessagingOperation.thread,
        MatrixMessagingOperation.reaction,
        MatrixMessagingOperation.edit,
        MatrixMessagingOperation.redaction,
        MatrixMessagingOperation.read_receipt,
        MatrixMessagingOperation.desktop_notify,
    }
)
TRANSACTION_SCOPED_OPERATIONS = frozenset(
    {
        MatrixMessagingOperation.send,
        MatrixMessagingOperation.reply,
        MatrixMessagingOperation.thread,
        MatrixMessagingOperation.reaction,
        MatrixMessagingOperation.edit,
        MatrixMessagingOperation.redaction,
    }
)
LOCAL_OUTBOX_OPERATIONS = frozenset(
    {
        MatrixMessagingOperation.draft_write,
        MatrixMessagingOperation.draft_read,
        MatrixMessagingOperation.outbox_enqueue,
        MatrixMessagingOperation.outbox_read,
        MatrixMessagingOperation.outbox_transition,
        MatrixMessagingOperation.outbox_discard,
    }
)
OUTBOX_SCOPED_OPERATIONS = LOCAL_OUTBOX_OPERATIONS | TRANSACTION_SCOPED_OPERATIONS


@dataclass(frozen=True)
class MatrixMessagingLane:
    operation: MatrixMessagingOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    approval_required: bool
    side_effect_class: str
    risk: str


def _lane(operation: MatrixMessagingOperation) -> MatrixMessagingLane:
    slug = operation.value.replace("_", "-")
    if operation in {
        MatrixMessagingOperation.draft_read,
        MatrixMessagingOperation.outbox_read,
    }:
        capability = AuthorityCapability.read
        side_effect = "local_sensitive"
    elif operation == MatrixMessagingOperation.outbox_discard:
        capability = AuthorityCapability.destructive
        side_effect = "destructive_local_sensitive"
    elif operation == MatrixMessagingOperation.desktop_notify:
        capability = AuthorityCapability.execute
        side_effect = "local_notification"
    elif operation in NETWORK_OPERATIONS:
        capability = (
            AuthorityCapability.destructive
            if operation == MatrixMessagingOperation.redaction
            else AuthorityCapability.send
        )
        side_effect = (
            "destructive_external"
            if operation == MatrixMessagingOperation.redaction
            else "authenticated_connector_mutation"
        )
    else:
        capability = AuthorityCapability.mutate
        side_effect = "local_sensitive"
    mode = (
        TrustMode.full_machine_access_session
        if capability == AuthorityCapability.destructive
        else TrustMode.ask_before_changes
    )
    return MatrixMessagingLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:matrix-messaging-{slug}",
        capability_ref=f"authority-capability-ref:matrix-messaging-{slug}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-messaging-{slug}-v1",
        tool_ref=f"tool-ref:matrix-messaging-{slug}-v1",
        tool_name=f"matrix_messaging_{operation.value}",
        authority_domain=(
            AuthorityDomain.apps
            if operation == MatrixMessagingOperation.desktop_notify
            else AuthorityDomain.messages
        ),
        authority_capability=capability,
        required_mode=mode,
        approval_required=True,
        side_effect_class=side_effect,
        risk="high",
    )


MATRIX_MESSAGING_LANES = {
    operation: _lane(operation) for operation in MatrixMessagingOperation
}


def matrix_messaging_lane(
    operation: MatrixMessagingOperation | str,
) -> MatrixMessagingLane:
    return MATRIX_MESSAGING_LANES[MatrixMessagingOperation(operation)]


def matrix_messaging_rollback_ref(operation: MatrixMessagingOperation | str) -> str:
    operation = MatrixMessagingOperation(operation)
    slug = operation.value.replace("_", "-")
    if operation in NETWORK_OPERATIONS:
        return f"compensation-readiness-ref:matrix-messaging:{slug}"
    return f"rollback-readiness-ref:matrix-messaging:{slug}"


__all__ = [
    "EVENT_SCOPED_OPERATIONS",
    "CONTENT_FINGERPRINT_OPERATIONS",
    "MATRIX_MESSAGING_BUDGET_REF",
    "MATRIX_MESSAGING_KILL_SWITCH_REF",
    "MATRIX_MESSAGING_MAX_OUTBOX_RECORDS",
    "MATRIX_MESSAGING_LANES",
    "MATRIX_MESSAGING_OUTBOX_KEY_ITEM_REF",
    "MATRIX_MESSAGING_OUTBOX_KEY_VERSION_REF",
    "MATRIX_MESSAGING_OUTBOX_SCHEMA_REF",
    "MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF",
    "MATRIX_MESSAGING_NOTIFICATION_POLICY_REF",
    "MATRIX_MESSAGING_NOTIFICATION_TARGET_REF",
    "MATRIX_MESSAGING_PROVIDER_REF",
    "MATRIX_MESSAGING_RUNTIME_REF",
    "MATRIX_MESSAGING_SAFE_DISABLE_REF",
    "MATRIX_MESSAGING_SCHEMA_VERSION",
    "MATRIX_MESSAGING_TARGET_REF",
    "MESSAGE_CONTENT_OPERATIONS",
    "LOCAL_OUTBOX_OPERATIONS",
    "NETWORK_OPERATIONS",
    "OUTBOX_SCOPED_OPERATIONS",
    "TRANSACTION_SCOPED_OPERATIONS",
    "MatrixMessagingLane",
    "MatrixMessagingOperation",
    "matrix_messaging_lane",
    "matrix_messaging_rollback_ref",
]
