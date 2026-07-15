from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from ultimate_ai_agent.core.communications.matrix_sync import (
    InMemoryMatrixCacheCryptoBackend,
    MatrixCacheKeyUnavailable,
    MatrixNormalizedEventKind,
    MatrixProtectedCache,
    MatrixProtectedCacheError,
    MatrixProtectedCacheState,
    normalize_matrix_sync_response,
    normalize_matrix_timeline_response,
)


ACCOUNT_REF = "account-ref:matrix:test"
CACHE_REF = "cache-ref:matrix:test"
KEY_ITEM_REF = "cache-key-item-ref:matrix:test"
KEY_VERSION_REF = "cache-key-version-ref:matrix:test:1"
GENERATION_REF_0 = "cache-generation-ref:matrix:test:0"
GENERATION_REF_1 = "cache-generation-ref:matrix:test:1"
GENERATION_REF_2 = "cache-generation-ref:matrix:test:2"
SALT = b"s" * 32


def _sync_payload(
    *,
    next_batch: str = "cursor-private-one",
    body: str = "content-ref:matrix:test-body",
) -> bytes:
    return json.dumps(
        {
            "next_batch": next_batch,
            "rooms": {
                "join": {
                    "!room-private:example.invalid": {
                        "state": {
                            "events": [
                                {
                                    "type": "m.room.name",
                                    "content": {"name": "room-name-ref:matrix:test"},
                                },
                                {
                                    "type": "m.room.topic",
                                    "content": {"topic": "room-topic-ref:matrix:test"},
                                },
                                {
                                    "type": "m.room.avatar",
                                    "content": {"url": "mxc://private/avatar"},
                                },
                                {
                                    "type": "m.space.parent",
                                    "state_key": "!private-space:example.invalid",
                                    "content": {"canonical": True},
                                },
                            ]
                        },
                        "timeline": {
                            "events": [
                                {
                                    "event_id": "$event-private-one",
                                    "sender": "@sender-private:example.invalid",
                                    "origin_server_ts": 10,
                                    "type": "m.room.message",
                                    "content": {"msgtype": "m.text", "body": body},
                                },
                                {
                                    "event_id": "$event-private-two",
                                    "sender": "@sender-private:example.invalid",
                                    "origin_server_ts": 20,
                                    "type": "m.room.message",
                                    "content": {
                                        "msgtype": "m.text",
                                        "body": "content-ref:matrix:test-reply",
                                        "m.relates_to": {
                                            "m.in_reply_to": {
                                                "event_id": "$event-private-one"
                                            }
                                        },
                                    },
                                },
                                {
                                    "event_id": "$event-private-three",
                                    "sender": "@sender-private:example.invalid",
                                    "origin_server_ts": 30,
                                    "type": "m.room.encrypted",
                                    "content": {
                                        "ciphertext": "private-ciphertext-marker"
                                    },
                                },
                            ]
                        },
                        "unread_notifications": {
                            "notification_count": 2,
                            "highlight_count": 1,
                        },
                        "ephemeral": {
                            "events": [
                                {
                                    "type": "m.typing",
                                    "content": {
                                        "user_ids": ["@typing-private:example.invalid"]
                                    },
                                },
                                {
                                    "type": "m.receipt",
                                    "content": {"$event-private-one": {"m.read": {}}},
                                },
                            ]
                        },
                    }
                }
            },
            "account_data": {
                "events": [
                    {
                        "type": "m.direct",
                        "content": {
                            "@dm-private:example.invalid": [
                                "!room-private:example.invalid"
                            ]
                        },
                    }
                ]
            },
        },
        separators=(",", ":"),
    ).encode()


def _cache(
    tmp_path: Path,
) -> tuple[MatrixProtectedCache, InMemoryMatrixCacheCryptoBackend]:
    backend = InMemoryMatrixCacheCryptoBackend()
    backend.create(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    return MatrixProtectedCache(
        root=tmp_path / "protected", crypto_backend=backend
    ), backend


def _empty_state() -> MatrixProtectedCacheState:
    state = MatrixProtectedCacheState.empty(
        account_ref=ACCOUNT_REF,
        cache_ref=CACHE_REF,
        generation_ref=GENERATION_REF_0,
        key_version_ref=KEY_VERSION_REF,
    )
    return state.model_copy(
        update={
            "pseudonymization_salt_base64url": "c3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3M"
        }
    )


def test_normalization_pseudonymizes_ids_and_preserves_untrusted_content() -> None:
    raw = _sync_payload()
    batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=raw,
        pseudonymization_salt=SALT,
    )
    assert batch.event_count == 3
    assert batch.content_untrusted is True
    assert batch.not_instruction_authority is True
    assert [event.event_kind for event in batch.events] == [
        MatrixNormalizedEventKind.message,
        MatrixNormalizedEventKind.reply,
        MatrixNormalizedEventKind.encrypted_placeholder,
    ]
    assert batch.events[0].body == "content-ref:matrix:test-body"
    assert batch.events[2].body is None
    room = batch.rooms[0]
    assert room.is_direct is True
    assert room.avatar_ref is not None
    assert room.space_parent_refs
    assert room.typing_participant_refs
    assert room.receipt_event_refs
    assert room.notification_decision.value == "highlight"
    projected = batch.model_dump_json()
    for raw_identifier in (
        "!room-private",
        "$event-private",
        "@sender-private",
        "private-ciphertext-marker",
    ):
        assert raw_identifier not in projected


def test_timeline_pagination_has_a_distinct_bounded_normalizer() -> None:
    sync_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    room_ref = sync_batch.rooms[0].room_ref
    payload = json.dumps(
        {
            "chunk": [
                {
                    "event_id": "$page-private-event",
                    "sender": "@page-private-sender:example.invalid",
                    "origin_server_ts": 5,
                    "type": "m.room.message",
                    "content": {"msgtype": "m.text", "body": "private page body"},
                }
            ],
            "end": "private-page-end",
        },
        separators=(",", ":"),
    ).encode()
    batch = normalize_matrix_timeline_response(
        account_ref=ACCOUNT_REF,
        raw_room_id="!room-private:example.invalid",
        payload=payload,
        pseudonymization_salt=SALT,
        allowed_room_refs={room_ref},
    )
    assert batch.event_count == 1
    assert batch.events[0].body == "private page body"
    assert batch.byte_count == len(payload)
    assert "private-page-end" not in batch.next_batch_ref


def test_timeline_terminal_page_without_end_is_preserved() -> None:
    sync_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    payload = json.dumps({"chunk": []}, separators=(",", ":")).encode()
    batch = normalize_matrix_timeline_response(
        account_ref=ACCOUNT_REF,
        raw_room_id="!room-private:example.invalid",
        payload=payload,
        pseudonymization_salt=SALT,
        allowed_room_refs={sync_batch.rooms[0].room_ref},
    )
    assert batch.pagination_complete is True
    assert batch.next_batch_token is None
    assert batch.next_batch_ref == "pagination-cursor-ref:matrix:terminal"


@pytest.mark.parametrize(
    "updates",
    [
        {
            "pagination_complete": False,
            "next_batch_token": "cursor-live",
            "next_batch_ref": "pagination-cursor-ref:matrix:terminal",
        },
        {
            "pagination_complete": True,
            "next_batch_token": "cursor-live",
            "next_batch_ref": "pagination-cursor-ref:matrix:terminal",
        },
        {
            "pagination_complete": True,
            "next_batch_token": None,
            "next_batch_ref": "pagination-cursor-ref:matrix:live",
        },
    ],
)
def test_terminal_cursor_evidence_cannot_be_contradictory(
    updates: dict[str, object],
) -> None:
    batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    payload = batch.model_dump(mode="python")
    payload.update(updates)
    with pytest.raises(ValueError, match="MATRIX_SYNC_TERMINAL_CURSOR_INVALID"):
        type(batch).model_validate(payload)


def test_v11_redaction_purges_cached_target_and_prevents_rehydration() -> None:
    initial = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    state = _empty_state().apply_batch(initial, next_generation_ref=GENERATION_REF_1)
    payload = json.loads(_sync_payload(next_batch="cursor-private-two"))
    timeline = payload["rooms"]["join"]["!room-private:example.invalid"]["timeline"][
        "events"
    ]
    timeline[:] = [
        {
            "event_id": "$event-private-redaction",
            "sender": "@sender-private:example.invalid",
            "origin_server_ts": 40,
            "type": "m.room.redaction",
            "content": {"redacts": "$event-private-one"},
        }
    ]
    redaction = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=json.dumps(payload).encode(),
        pseudonymization_salt=SALT,
    )
    redacted = state.apply_batch(redaction, next_generation_ref=GENERATION_REF_2)
    target = next(
        event
        for event in redacted.events
        if event.event_kind == MatrixNormalizedEventKind.message
    )
    assert target.body is None
    assert target.redacted is True
    replayed = redacted.apply_batch(
        initial, next_generation_ref="cache-generation-ref:matrix:test:3"
    )
    replayed_target = next(
        event for event in replayed.events if event.event_ref == target.event_ref
    )
    assert replayed_target.body is None
    assert replayed_target.redacted is True


def test_redaction_tombstone_applies_before_target_and_within_same_batch() -> None:
    redaction_payload = json.loads(_sync_payload(next_batch="cursor-redaction-first"))
    timeline = redaction_payload["rooms"]["join"]["!room-private:example.invalid"][
        "timeline"
    ]["events"]
    timeline[:] = [
        {
            "event_id": "$event-private-redaction-first",
            "sender": "@sender-private:example.invalid",
            "origin_server_ts": 1,
            "type": "m.room.redaction",
            "content": {"redacts": "$event-private-one"},
        }
    ]
    redaction_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=json.dumps(redaction_payload).encode(),
        pseudonymization_salt=SALT,
    )
    tombstoned = _empty_state().apply_batch(
        redaction_batch, next_generation_ref=GENERATION_REF_1
    )
    target_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    later_target = tombstoned.apply_batch(
        target_batch, next_generation_ref=GENERATION_REF_2
    )
    target_ref = target_batch.events[0].event_ref
    assert (
        next(
            event for event in later_target.events if event.event_ref == target_ref
        ).body
        is None
    )

    combined_payload = json.loads(_sync_payload(next_batch="cursor-combined"))
    combined_timeline = combined_payload["rooms"]["join"][
        "!room-private:example.invalid"
    ]["timeline"]["events"]
    combined_timeline[0]["content"] = {}
    combined_timeline.append(timeline[0])
    combined_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=json.dumps(combined_payload).encode(),
        pseudonymization_salt=SALT,
    )
    combined = _empty_state().apply_batch(
        combined_batch, next_generation_ref=GENERATION_REF_1
    )
    combined_target = next(
        event for event in combined.events if event.event_ref == target_ref
    )
    assert combined_target.body is None
    assert combined_target.redacted is True


def test_cross_room_redaction_and_conflicting_target_fail_closed() -> None:
    initial = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=SALT,
    )
    state = _empty_state().apply_batch(initial, next_generation_ref=GENERATION_REF_1)
    payload = json.loads(_sync_payload(next_batch="cursor-cross-room"))
    room = payload["rooms"]["join"].pop("!room-private:example.invalid")
    payload["rooms"]["join"]["!other-private:example.invalid"] = room
    room["timeline"]["events"][:] = [
        {
            "event_id": "$event-private-cross-room-redaction",
            "sender": "@sender-private:example.invalid",
            "origin_server_ts": 50,
            "type": "m.room.redaction",
            "redacts": "$event-private-other",
            "content": {"redacts": "$event-private-one"},
        }
    ]
    with pytest.raises(ValueError, match="MATRIX_SYNC_REDACTION_TARGET_CONFLICT"):
        normalize_matrix_sync_response(
            account_ref=ACCOUNT_REF,
            payload=json.dumps(payload).encode(),
            pseudonymization_salt=SALT,
        )
    del room["timeline"]["events"][0]["redacts"]
    cross_room_batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=json.dumps(payload).encode(),
        pseudonymization_salt=SALT,
    )
    with pytest.raises(
        MatrixProtectedCacheError,
        match="MATRIX_CACHE_CROSS_ROOM_REDACTION_DENIED",
    ):
        state.apply_batch(cross_room_batch, next_generation_ref=GENERATION_REF_2)


def test_normalization_is_deterministic_and_deduplicates_identical_events() -> None:
    payload = json.loads(_sync_payload())
    timeline = payload["rooms"]["join"]["!room-private:example.invalid"]["timeline"][
        "events"
    ]
    timeline.append(dict(timeline[0]))
    encoded = json.dumps(payload).encode()
    first = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=encoded,
        pseudonymization_salt=SALT,
    )
    second = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=encoded,
        pseudonymization_salt=SALT,
    )
    assert first == second
    assert first.event_count == 3


def test_exact_event_budget_counts_metadata_and_ephemeral_envelopes() -> None:
    with pytest.raises(ValueError, match="MATRIX_SYNC_EVENT_LIMIT_EXCEEDED"):
        normalize_matrix_sync_response(
            account_ref=ACCOUNT_REF,
            payload=_sync_payload(),
            pseudonymization_salt=SALT,
            max_event_envelopes=9,
        )


def test_relation_cycle_fails_closed() -> None:
    payload = json.loads(_sync_payload())
    timeline = payload["rooms"]["join"]["!room-private:example.invalid"]["timeline"][
        "events"
    ]
    timeline[:2] = [
        {
            "event_id": "$cycle-one",
            "sender": "@sender:example.invalid",
            "origin_server_ts": 1,
            "type": "m.reaction",
            "content": {
                "m.relates_to": {"event_id": "$cycle-two", "rel_type": "m.annotation"}
            },
        },
        {
            "event_id": "$cycle-two",
            "sender": "@sender:example.invalid",
            "origin_server_ts": 2,
            "type": "m.reaction",
            "content": {
                "m.relates_to": {"event_id": "$cycle-one", "rel_type": "m.annotation"}
            },
        },
    ]
    with pytest.raises(ValueError, match="MATRIX_SYNC_RELATION_CYCLE_DENIED"):
        normalize_matrix_sync_response(
            account_ref=ACCOUNT_REF,
            payload=json.dumps(payload).encode(),
            pseudonymization_salt=SALT,
        )


def test_cross_room_scope_fails_closed() -> None:
    with pytest.raises(ValueError, match="MATRIX_SYNC_CROSS_ROOM_SCOPE_DENIED"):
        normalize_matrix_sync_response(
            account_ref=ACCOUNT_REF,
            payload=_sync_payload(),
            pseudonymization_salt=SALT,
            allowed_room_refs={"room-ref:matrix:not-the-room"},
        )


def test_cache_is_ciphertext_only_and_replays_without_duplicates(
    tmp_path: Path,
) -> None:
    cache, _backend = _cache(tmp_path)
    state = _empty_state()
    batch = normalize_matrix_sync_response(
        account_ref=ACCOUNT_REF,
        payload=_sync_payload(),
        pseudonymization_salt=state.pseudonymization_salt,
    )
    updated = state.apply_batch(batch, next_generation_ref=GENERATION_REF_1)
    result = cache.write(updated, key_item_ref=KEY_ITEM_REF)
    assert result.byte_count > 0
    cache_files = list((tmp_path / "protected").iterdir())
    assert len(cache_files) == 1
    ciphertext = cache_files[0].read_bytes()
    for marker in (
        b"content-ref:matrix:test-body",
        b"room-name-ref:matrix:test",
        b"cursor-private-one",
        b"event-private",
        b"sender-private",
    ):
        assert marker not in ciphertext
    restored = cache.read(
        account_ref=ACCOUNT_REF,
        cache_ref=CACHE_REF,
        key_item_ref=KEY_ITEM_REF,
        key_version_ref=KEY_VERSION_REF,
        expected_generation_ref=GENERATION_REF_1,
    )
    replayed = restored.apply_batch(batch, next_generation_ref=GENERATION_REF_2)
    assert len(replayed.events) == 3


def test_key_loss_lock_corruption_and_account_substitution_fail_closed(
    tmp_path: Path,
) -> None:
    cache, backend = _cache(tmp_path)
    state = _empty_state()
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    backend.locked = True
    with pytest.raises(
        MatrixCacheKeyUnavailable, match="MATRIX_CACHE_KEY_BACKEND_LOCKED"
    ):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )
    backend.locked = False
    backend.delete(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    with pytest.raises(MatrixCacheKeyUnavailable, match="MATRIX_CACHE_KEY_NOT_FOUND"):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )
    backend.create(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    with pytest.raises(
        MatrixProtectedCacheError, match="MATRIX_CACHE_INTEGRITY_FAILED"
    ):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    with pytest.raises(
        MatrixProtectedCacheError, match="MATRIX_CACHE_INTEGRITY_FAILED"
    ):
        cache.read(
            account_ref="account-ref:matrix:other",
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )


def test_path_substitution_and_deletion_residue_are_denied(tmp_path: Path) -> None:
    cache, _backend = _cache(tmp_path)
    state = _empty_state()
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    path = next((tmp_path / "protected").iterdir())
    path.unlink()
    target = tmp_path / "target"
    target.write_bytes(b"unrelated")
    path.symlink_to(target)
    with pytest.raises(
        MatrixProtectedCacheError, match="MATRIX_CACHE_PATH_SUBSTITUTION_DENIED"
    ):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )
    path.unlink()
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    cache.purge(cache_ref=CACHE_REF)
    assert list((tmp_path / "protected").iterdir()) == []


def test_cache_root_identity_and_owner_are_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache, _backend = _cache(tmp_path)
    state = _empty_state()
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    root = tmp_path / "protected"
    original_root = tmp_path / "protected-original"
    root.rename(original_root)
    root.mkdir(mode=0o700)
    with pytest.raises(
        MatrixProtectedCacheError,
        match="MATRIX_CACHE_ROOT_SUBSTITUTION_DENIED",
    ):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_0,
        )

    owner_test_root = tmp_path / "owner-test"
    owner_test_root.mkdir(mode=0o700)
    actual_euid = os.geteuid()
    monkeypatch.setattr(os, "geteuid", lambda: actual_euid + 1)
    with pytest.raises(ValueError, match="MATRIX_CACHE_ROOT_OWNER_INVALID"):
        MatrixProtectedCache(
            root=owner_test_root,
            crypto_backend=InMemoryMatrixCacheCryptoBackend(),
        )


def test_cache_root_rejects_symlinked_ancestor(tmp_path: Path) -> None:
    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir(mode=0o700)
    alias_parent = tmp_path / "alias-parent"
    alias_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(ValueError, match="MATRIX_CACHE_ROOT_UNSAFE"):
        MatrixProtectedCache(
            root=alias_parent / "protected",
            crypto_backend=InMemoryMatrixCacheCryptoBackend(),
        )


def test_cache_generation_binding_rejects_old_ciphertext_replay(tmp_path: Path) -> None:
    cache, _backend = _cache(tmp_path)
    initial = _empty_state()
    cache.write(initial, key_item_ref=KEY_ITEM_REF)
    cache_path = next((tmp_path / "protected").iterdir())
    old_ciphertext = cache_path.read_bytes()
    current = initial.model_copy(update={"generation_ref": GENERATION_REF_1})
    cache.write(current, key_item_ref=KEY_ITEM_REF)

    replay_path = tmp_path / "protected" / "replay-candidate"
    replay_path.write_bytes(old_ciphertext)
    os.chmod(replay_path, 0o600)
    os.replace(replay_path, cache_path)

    with pytest.raises(
        MatrixProtectedCacheError,
        match="MATRIX_CACHE_GENERATION_MISMATCH",
    ):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=CACHE_REF,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=GENERATION_REF_1,
        )


def test_cache_purge_fsyncs_the_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache, _backend = _cache(tmp_path)
    cache.write(_empty_state(), key_item_ref=KEY_ITEM_REF)
    original_fsync = os.fsync
    directory_syncs: list[bool] = []

    def recording_fsync(descriptor: int) -> None:
        directory_syncs.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
        original_fsync(descriptor)

    monkeypatch.setattr(os, "fsync", recording_fsync)
    cache.purge(cache_ref=CACHE_REF)
    assert directory_syncs == [True]


def test_rotation_verifies_new_ciphertext_before_old_key_deletion(
    tmp_path: Path,
) -> None:
    cache, backend = _cache(tmp_path)
    state = _empty_state()
    cache.write(state, key_item_ref=KEY_ITEM_REF)
    result = cache.rotate(
        account_ref=ACCOUNT_REF,
        cache_ref=CACHE_REF,
        key_item_ref=KEY_ITEM_REF,
        old_key_version_ref=KEY_VERSION_REF,
        new_key_version_ref="cache-key-version-ref:matrix:test:2",
        expected_generation_ref=GENERATION_REF_0,
        next_generation_ref=GENERATION_REF_2,
    )
    assert result.generation_ref == GENERATION_REF_2
    with pytest.raises(MatrixCacheKeyUnavailable, match="MATRIX_CACHE_KEY_NOT_FOUND"):
        backend.probe(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    restored = cache.read(
        account_ref=ACCOUNT_REF,
        cache_ref=CACHE_REF,
        key_item_ref=KEY_ITEM_REF,
        key_version_ref="cache-key-version-ref:matrix:test:2",
        expected_generation_ref=GENERATION_REF_2,
    )
    assert restored.key_version_ref == "cache-key-version-ref:matrix:test:2"


def test_cache_does_not_create_wal_journal_temp_or_backup_files(tmp_path: Path) -> None:
    cache, _backend = _cache(tmp_path)
    cache.write(_empty_state(), key_item_ref=KEY_ITEM_REF)
    names = {path.name.lower() for path in (tmp_path / "protected").iterdir()}
    assert not any(
        marker in name
        for name in names
        for marker in ("wal", "journal", "tmp", "backup", ".stage-")
    )
    assert all(
        os.lstat(path).st_nlink == 1 for path in (tmp_path / "protected").iterdir()
    )
