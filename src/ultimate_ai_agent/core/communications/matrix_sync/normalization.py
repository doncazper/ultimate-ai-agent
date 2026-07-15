from __future__ import annotations

import hashlib
import hmac
import json
import unicodedata
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from .constants import MATRIX_SYNC_MAX_BYTES, MATRIX_SYNC_MAX_EVENTS, MATRIX_SYNC_MAX_ROOMS


class MatrixNormalizedEventKind(str, Enum):
    message = "message"
    reply = "reply"
    edit = "edit"
    redaction = "redaction"
    reaction = "reaction"
    poll = "poll"
    file_metadata = "file_metadata"
    thread_summary = "thread_summary"
    encrypted_placeholder = "encrypted_placeholder"
    unsupported = "unsupported"


class MatrixNotificationDecision(str, Enum):
    highlight = "highlight"
    notify = "notify"
    silent = "silent"


class MatrixPrivateEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    event_ref: str
    room_ref: str
    sender_ref: str
    event_kind: MatrixNormalizedEventKind
    origin_server_ts: int = Field(..., ge=0)
    body: str | None = Field(default=None, max_length=16_384)
    relation_event_ref: str | None = None
    redacted: StrictBool = False
    encrypted_placeholder: StrictBool = False
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_event(self) -> "MatrixPrivateEvent":
        if self.event_kind == MatrixNormalizedEventKind.encrypted_placeholder:
            if self.body is not None or not self.encrypted_placeholder:
                raise ValueError("MATRIX_SYNC_ENCRYPTED_PLACEHOLDER_INVALID")
        if self.event_kind in {
            MatrixNormalizedEventKind.reaction,
            MatrixNormalizedEventKind.redaction,
            MatrixNormalizedEventKind.edit,
            MatrixNormalizedEventKind.reply,
        } and not self.relation_event_ref:
            raise ValueError("MATRIX_SYNC_RELATION_TARGET_REQUIRED")
        return self


class MatrixPrivateRoom(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    room_ref: str
    membership: Literal["join", "invite", "leave"]
    name: str | None = Field(default=None, max_length=256)
    topic: str | None = Field(default=None, max_length=1024)
    avatar_ref: str | None = None
    is_direct: StrictBool = False
    space_parent_refs: tuple[str, ...] = ()
    unread_count: int = Field(default=0, ge=0, le=100_000)
    mention_count: int = Field(default=0, ge=0, le=100_000)
    notification_decision: MatrixNotificationDecision = MatrixNotificationDecision.silent
    typing_participant_refs: tuple[str, ...] = ()
    receipt_event_refs: tuple[str, ...] = ()
    event_refs: tuple[str, ...] = ()
    content_untrusted: Literal[True] = True


class MatrixPrivateSyncBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    account_ref: str
    next_batch_token: str = Field(..., min_length=1, max_length=2048, repr=False)
    next_batch_ref: str
    rooms: tuple[MatrixPrivateRoom, ...]
    events: tuple[MatrixPrivateEvent, ...]
    event_count: int = Field(..., ge=0, le=MATRIX_SYNC_MAX_EVENTS)
    byte_count: int = Field(..., ge=0, le=MATRIX_SYNC_MAX_BYTES)
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_batch(self) -> "MatrixPrivateSyncBatch":
        if self.event_count != len(self.events):
            raise ValueError("MATRIX_SYNC_EVENT_COUNT_MISMATCH")
        known = {event.event_ref for event in self.events}
        for room in self.rooms:
            if not set(room.event_refs) <= known:
                raise ValueError("MATRIX_SYNC_ROOM_EVENT_REF_INVALID")
        return self


def _safe_private_text(value: object, *, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = unicodedata.normalize("NFC", value).replace("\x00", "")
    return normalized[:maximum]


def _hmac_ref(prefix: str, salt: bytes, raw_value: str) -> str:
    digest = hmac.new(salt, raw_value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix}:hmac-sha256:{digest}"


def matrix_sync_private_ref(prefix: str, salt: bytes, raw_value: str) -> str:
    """Bind a transient Matrix identifier to a safe ref without retaining it."""
    if len(salt) != 32:
        raise ValueError("MATRIX_SYNC_PSEUDONYMIZATION_SALT_INVALID")
    if not raw_value or len(raw_value.encode("utf-8")) > 4096:
        raise ValueError("MATRIX_SYNC_TRANSIENT_SCOPE_INVALID")
    return _hmac_ref(prefix, salt, raw_value)


def _event_kind(event: dict[str, Any]) -> tuple[MatrixNormalizedEventKind, str | None]:
    event_type = event.get("type")
    content = event.get("content") if isinstance(event.get("content"), dict) else {}
    unsigned = event.get("unsigned") if isinstance(event.get("unsigned"), dict) else {}
    if event_type == "m.room.encrypted":
        return MatrixNormalizedEventKind.encrypted_placeholder, None
    if event_type == "m.room.redaction":
        return MatrixNormalizedEventKind.redaction, event.get("redacts")
    relates = content.get("m.relates_to") if isinstance(content, dict) else None
    relation_type = relates.get("rel_type") if isinstance(relates, dict) else None
    relation_target = relates.get("event_id") if isinstance(relates, dict) else None
    if event_type == "m.reaction":
        return MatrixNormalizedEventKind.reaction, relation_target
    if event_type in {"org.matrix.msc3381.poll.start", "m.poll.start"}:
        return MatrixNormalizedEventKind.poll, None
    if event_type == "m.room.message":
        if relation_type == "m.replace" or isinstance(unsigned.get("replaces_state"), str):
            return MatrixNormalizedEventKind.edit, relation_target
        if relation_type == "m.thread":
            return MatrixNormalizedEventKind.thread_summary, relation_target
        reply = content.get("m.relates_to", {}).get("m.in_reply_to") if isinstance(content.get("m.relates_to"), dict) else None
        if isinstance(reply, dict) and isinstance(reply.get("event_id"), str):
            return MatrixNormalizedEventKind.reply, reply["event_id"]
        if content.get("msgtype") in {"m.file", "m.image", "m.audio", "m.video"}:
            return MatrixNormalizedEventKind.file_metadata, None
        return MatrixNormalizedEventKind.message, None
    return MatrixNormalizedEventKind.unsupported, None


def _event_body(event: dict[str, Any], kind: MatrixNormalizedEventKind) -> str | None:
    if kind in {
        MatrixNormalizedEventKind.encrypted_placeholder,
        MatrixNormalizedEventKind.redaction,
        MatrixNormalizedEventKind.reaction,
        MatrixNormalizedEventKind.unsupported,
    }:
        return None
    content = event.get("content") if isinstance(event.get("content"), dict) else {}
    if kind == MatrixNormalizedEventKind.poll:
        poll = content.get("org.matrix.msc3381.poll.start") or content.get("m.poll.start")
        question = poll.get("question") if isinstance(poll, dict) else None
        if isinstance(question, dict):
            return _safe_private_text(question.get("org.matrix.msc1767.text") or question.get("m.text"), maximum=4096)
    if kind == MatrixNormalizedEventKind.file_metadata:
        return _safe_private_text(content.get("body"), maximum=1024)
    new_content = content.get("m.new_content")
    if kind == MatrixNormalizedEventKind.edit and isinstance(new_content, dict):
        return _safe_private_text(new_content.get("body"), maximum=16_384)
    return _safe_private_text(content.get("body"), maximum=16_384)


def normalize_matrix_sync_response(
    *,
    account_ref: str,
    payload: bytes,
    pseudonymization_salt: bytes,
    allowed_room_refs: set[str] | None = None,
    allowed_event_types: set[str] | None = None,
    max_event_envelopes: int = MATRIX_SYNC_MAX_EVENTS,
) -> MatrixPrivateSyncBatch:
    if len(payload) > MATRIX_SYNC_MAX_BYTES:
        raise ValueError("MATRIX_SYNC_RESPONSE_TOO_LARGE")
    if len(pseudonymization_salt) != 32:
        raise ValueError("MATRIX_SYNC_PSEUDONYMIZATION_SALT_INVALID")
    if (
        type(max_event_envelopes) is not int
        or max_event_envelopes < 1
        or max_event_envelopes > MATRIX_SYNC_MAX_EVENTS
    ):
        raise ValueError("MATRIX_SYNC_EVENT_LIMIT_INVALID")
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("MATRIX_SYNC_RESPONSE_INVALID") from exc
    if not isinstance(data, dict) or not isinstance(data.get("next_batch"), str):
        raise ValueError("MATRIX_SYNC_RESPONSE_CONTRACT_INVALID")
    rooms_container = data.get("rooms") if isinstance(data.get("rooms"), dict) else {}
    account_data = data.get("account_data") if isinstance(data.get("account_data"), dict) else {}
    remaining_event_envelopes = max_event_envelopes

    def claim_event_envelopes(value: object) -> list[object]:
        nonlocal remaining_event_envelopes
        events = value if isinstance(value, list) else []
        if len(events) > remaining_event_envelopes:
            raise ValueError("MATRIX_SYNC_EVENT_LIMIT_EXCEEDED")
        remaining_event_envelopes -= len(events)
        return events

    direct_room_ids: set[str] = set()
    for account_event in claim_event_envelopes(account_data.get("events")):
        if not isinstance(account_event, dict) or account_event.get("type") != "m.direct":
            continue
        content = account_event.get("content")
        if not isinstance(content, dict):
            continue
        for room_ids in content.values():
            if isinstance(room_ids, list):
                direct_room_ids.update(value for value in room_ids if isinstance(value, str))
    normalized_events: dict[str, MatrixPrivateEvent] = {}
    normalized_rooms: list[MatrixPrivateRoom] = []
    relation_edges: dict[str, str] = {}
    for membership in ("join", "invite", "leave"):
        raw_rooms = rooms_container.get(membership)
        if not isinstance(raw_rooms, dict):
            continue
        for raw_room_id, raw_room in raw_rooms.items():
            if len(normalized_rooms) >= MATRIX_SYNC_MAX_ROOMS:
                raise ValueError("MATRIX_SYNC_ROOM_LIMIT_EXCEEDED")
            if not isinstance(raw_room_id, str) or not isinstance(raw_room, dict):
                raise ValueError("MATRIX_SYNC_ROOM_INVALID")
            room_ref = _hmac_ref("room-ref:matrix", pseudonymization_salt, raw_room_id)
            if allowed_room_refs is not None and room_ref not in allowed_room_refs:
                raise ValueError("MATRIX_SYNC_CROSS_ROOM_SCOPE_DENIED")
            state = raw_room.get("state") if isinstance(raw_room.get("state"), dict) else {}
            timeline = raw_room.get("timeline") if isinstance(raw_room.get("timeline"), dict) else {}
            state_events = claim_event_envelopes(state.get("events"))
            timeline_events = claim_event_envelopes(timeline.get("events"))
            room_name: str | None = None
            room_topic: str | None = None
            room_avatar_ref: str | None = None
            space_parent_refs: list[str] = []
            for state_event in state_events:
                if not isinstance(state_event, dict):
                    continue
                if (
                    allowed_event_types is not None
                    and state_event.get("type") not in allowed_event_types
                ):
                    raise ValueError("MATRIX_SYNC_EVENT_SCOPE_DENIED")
                content = state_event.get("content") if isinstance(state_event.get("content"), dict) else {}
                if state_event.get("type") == "m.room.name":
                    room_name = _safe_private_text(content.get("name"), maximum=256)
                elif state_event.get("type") == "m.room.topic":
                    room_topic = _safe_private_text(content.get("topic"), maximum=1024)
                elif state_event.get("type") == "m.room.avatar" and isinstance(content.get("url"), str):
                    room_avatar_ref = _hmac_ref(
                        "media-ref:matrix", pseudonymization_salt, content["url"]
                    )
                elif state_event.get("type") == "m.space.parent" and isinstance(state_event.get("state_key"), str):
                    space_parent_refs.append(
                        _hmac_ref(
                            "space-ref:matrix",
                            pseudonymization_salt,
                            state_event["state_key"],
                        )
                    )
            room_event_refs: list[str] = []
            for raw_event in timeline_events:
                if not isinstance(raw_event, dict):
                    raise ValueError("MATRIX_SYNC_EVENT_INVALID")
                raw_event_type = raw_event.get("type")
                if (
                    allowed_event_types is not None
                    and raw_event_type not in allowed_event_types
                ):
                    raise ValueError("MATRIX_SYNC_EVENT_SCOPE_DENIED")
                raw_event_id = raw_event.get("event_id")
                raw_sender = raw_event.get("sender")
                timestamp = raw_event.get("origin_server_ts")
                if not isinstance(raw_event_id, str) or not isinstance(raw_sender, str) or not isinstance(timestamp, int) or timestamp < 0:
                    raise ValueError("MATRIX_SYNC_EVENT_IDENTITY_INVALID")
                event_ref = _hmac_ref("event-ref:matrix", pseudonymization_salt, raw_event_id)
                sender_ref = _hmac_ref("participant-ref:matrix", pseudonymization_salt, raw_sender)
                kind, raw_relation = _event_kind(raw_event)
                relation_ref = None
                if isinstance(raw_relation, str):
                    relation_ref = _hmac_ref("event-ref:matrix", pseudonymization_salt, raw_relation)
                    relation_edges[event_ref] = relation_ref
                event = MatrixPrivateEvent(
                    event_ref=event_ref,
                    room_ref=room_ref,
                    sender_ref=sender_ref,
                    event_kind=kind,
                    origin_server_ts=timestamp,
                    body=_event_body(raw_event, kind),
                    relation_event_ref=relation_ref,
                    redacted=kind == MatrixNormalizedEventKind.redaction,
                    encrypted_placeholder=kind == MatrixNormalizedEventKind.encrypted_placeholder,
                )
                existing = normalized_events.get(event_ref)
                if existing is not None and existing != event:
                    raise ValueError("MATRIX_SYNC_DUPLICATE_EVENT_CONFLICT")
                normalized_events[event_ref] = event
                room_event_refs.append(event_ref)
                if len(normalized_events) > MATRIX_SYNC_MAX_EVENTS:
                    raise ValueError("MATRIX_SYNC_EVENT_LIMIT_EXCEEDED")
            unread = raw_room.get("unread_notifications")
            unread = unread if isinstance(unread, dict) else {}
            unread_count = max(
                0, min(int(unread.get("notification_count", 0) or 0), 100_000)
            )
            mention_count = max(
                0, min(int(unread.get("highlight_count", 0) or 0), 100_000)
            )
            ephemeral = (
                raw_room.get("ephemeral")
                if isinstance(raw_room.get("ephemeral"), dict)
                else {}
            )
            typing_participant_refs: list[str] = []
            receipt_event_refs: list[str] = []
            ephemeral_events = claim_event_envelopes(ephemeral.get("events"))
            for ephemeral_event in ephemeral_events:
                if not isinstance(ephemeral_event, dict):
                    continue
                if (
                    allowed_event_types is not None
                    and ephemeral_event.get("type") not in allowed_event_types
                ):
                    raise ValueError("MATRIX_SYNC_EVENT_SCOPE_DENIED")
                ephemeral_content = ephemeral_event.get("content")
                if not isinstance(ephemeral_content, dict):
                    continue
                if ephemeral_event.get("type") == "m.typing":
                    user_ids = ephemeral_content.get("user_ids")
                    if isinstance(user_ids, list):
                        typing_participant_refs.extend(
                            _hmac_ref(
                                "participant-ref:matrix",
                                pseudonymization_salt,
                                user_id,
                            )
                            for user_id in user_ids[:64]
                            if isinstance(user_id, str)
                        )
                elif ephemeral_event.get("type") == "m.receipt":
                    receipt_event_refs.extend(
                        _hmac_ref(
                            "event-ref:matrix", pseudonymization_salt, event_id
                        )
                        for event_id in list(ephemeral_content)[:128]
                        if isinstance(event_id, str)
                    )
            normalized_rooms.append(
                MatrixPrivateRoom(
                    room_ref=room_ref,
                    membership=membership,
                    name=room_name,
                    topic=room_topic,
                    avatar_ref=room_avatar_ref,
                    is_direct=raw_room_id in direct_room_ids,
                    space_parent_refs=tuple(dict.fromkeys(space_parent_refs)),
                    unread_count=unread_count,
                    mention_count=mention_count,
                    notification_decision=(
                        MatrixNotificationDecision.highlight
                        if mention_count
                        else MatrixNotificationDecision.notify
                        if unread_count
                        else MatrixNotificationDecision.silent
                    ),
                    typing_participant_refs=tuple(
                        dict.fromkeys(typing_participant_refs)
                    ),
                    receipt_event_refs=tuple(dict.fromkeys(receipt_event_refs)),
                    event_refs=tuple(dict.fromkeys(room_event_refs)),
                )
            )
    for source in relation_edges:
        seen: set[str] = set()
        cursor = source
        for _depth in range(16):
            if cursor in seen:
                raise ValueError("MATRIX_SYNC_RELATION_CYCLE_DENIED")
            seen.add(cursor)
            target = relation_edges.get(cursor)
            if target is None:
                break
            cursor = target
        else:
            raise ValueError("MATRIX_SYNC_RELATION_DEPTH_EXCEEDED")
    events = tuple(sorted(normalized_events.values(), key=lambda item: (item.origin_server_ts, item.event_ref)))
    rooms = tuple(sorted(normalized_rooms, key=lambda item: item.room_ref))
    next_batch = data["next_batch"]
    return MatrixPrivateSyncBatch(
        account_ref=account_ref,
        next_batch_token=next_batch,
        next_batch_ref=_hmac_ref("sync-cursor-ref:matrix", pseudonymization_salt, next_batch),
        rooms=rooms,
        events=events,
        event_count=len(events),
        byte_count=len(payload),
    )


def normalize_matrix_timeline_response(
    *,
    account_ref: str,
    raw_room_id: str,
    payload: bytes,
    pseudonymization_salt: bytes,
    allowed_room_refs: set[str],
    allowed_event_types: set[str] | None = None,
    max_event_envelopes: int = MATRIX_SYNC_MAX_EVENTS,
) -> MatrixPrivateSyncBatch:
    if len(payload) > MATRIX_SYNC_MAX_BYTES:
        raise ValueError("MATRIX_SYNC_RESPONSE_TOO_LARGE")
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("MATRIX_SYNC_RESPONSE_INVALID") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("chunk"), list)
        or not isinstance(data.get("end"), str)
    ):
        raise ValueError("MATRIX_SYNC_PAGINATION_CONTRACT_INVALID")
    wrapped = json.dumps(
        {
            "next_batch": data["end"],
            "rooms": {
                "join": {
                    raw_room_id: {
                        "timeline": {"events": data["chunk"]},
                    }
                }
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    batch = normalize_matrix_sync_response(
        account_ref=account_ref,
        payload=wrapped,
        pseudonymization_salt=pseudonymization_salt,
        allowed_room_refs=allowed_room_refs,
        allowed_event_types=allowed_event_types,
        max_event_envelopes=max_event_envelopes,
    )
    return batch.model_copy(update={"byte_count": len(payload)})
