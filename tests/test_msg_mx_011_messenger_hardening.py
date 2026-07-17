from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import ultimate_ai_agent.core.communications.matrix_messaging.outbox as outbox_module
import ultimate_ai_agent.core.communications.matrix_sync.cache as cache_module
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.communications.matrix_hardening import (
    MatrixHardeningCheckCategory,
    MatrixHardeningCheckStatus,
    build_default_matrix_hardening_posture,
)
from ultimate_ai_agent.core.communications.matrix_messaging.constants import (
    MATRIX_MESSAGING_MAX_OUTBOX_RECORDS,
    MatrixMessagingOperation,
)
from ultimate_ai_agent.core.communications.matrix_messaging.contracts import (
    MatrixOutboxState,
)
from ultimate_ai_agent.core.communications.matrix_messaging.outbox import (
    MatrixEncryptedOutbox,
    MatrixOutboxError,
    MatrixOutboxRecord,
    matrix_outbox_content_fingerprint_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync.cache import (
    InMemoryMatrixCacheCryptoBackend,
    MatrixProtectedCache,
    MatrixProtectedCacheError,
    MatrixProtectedCacheState,
)
from ultimate_ai_agent.core.communications.matrix_sync.constants import (
    MATRIX_SYNC_MAX_CACHE_EVENTS,
    MATRIX_SYNC_MAX_ROOM_EVENT_REFS,
)
from ultimate_ai_agent.core.communications.matrix_sync.contracts import (
    MatrixSyncFreshness,
)
from ultimate_ai_agent.core.communications.matrix_sync.normalization import (
    MatrixNormalizedEventKind,
    MatrixPrivateEvent,
    MatrixPrivateRoom,
    MatrixPrivateSyncBatch,
)


LOCAL_BEARER = "msg-mx-011-local-bearer"
POSTURE_PATH = "/control-center/communications/matrix-hardening/posture"
ACCOUNT_REF = "account-ref:matrix:hardening"
ROOM_REF = "room-ref:matrix:hardening"
KEY_ITEM_REF = "key-item-ref:matrix-hardening:cache"
KEY_VERSION_REF = "key-version-ref:matrix-hardening:cache-v1"


def _batch(start: int, *, count: int = 500) -> MatrixPrivateSyncBatch:
    events = tuple(
        MatrixPrivateEvent(
            event_ref=f"event-ref:matrix:hardening-{index}",
            room_ref=ROOM_REF,
            sender_ref="participant-ref:matrix:hardening",
            event_kind=MatrixNormalizedEventKind.message,
            origin_server_ts=index,
            body="bounded-untrusted-content",
        )
        for index in range(start, start + count)
    )
    room = MatrixPrivateRoom(
        room_ref=ROOM_REF,
        membership="join",
        event_refs=tuple(event.event_ref for event in events),
    )
    return MatrixPrivateSyncBatch(
        account_ref=ACCOUNT_REF,
        next_batch_token=f"private-cursor-{start}",
        next_batch_ref=f"sync-cursor-ref:matrix:hardening-{start}",
        rooms=(room,),
        events=events,
        event_count=len(events),
        byte_count=len(events) * 64,
    )


def _cache(tmp_path: Path) -> tuple[MatrixProtectedCache, MatrixProtectedCacheState]:
    backend = InMemoryMatrixCacheCryptoBackend()
    backend.create(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    cache = MatrixProtectedCache(root=tmp_path / "cache", crypto_backend=backend)
    state = MatrixProtectedCacheState.empty(
        account_ref=ACCOUNT_REF,
        cache_ref="cache-ref:matrix:hardening",
        generation_ref="generation-ref:matrix:hardening-0",
        key_version_ref=KEY_VERSION_REF,
    )
    return cache, state


def _outbox_record(index: int) -> MatrixOutboxRecord:
    now = datetime.now(UTC)
    transaction_id = f"transaction-hardening-{index}"
    body = f"transient-hardening-body-{index}"
    fingerprint = matrix_outbox_content_fingerprint_ref(
        operation=MatrixMessagingOperation.send,
        room_id="!private-hardening:localhost",
        event_id=None,
        transaction_id=transaction_id,
        body=body,
        formatted_body=None,
        mention_user_ids=(),
        reaction_key=None,
    )
    return MatrixOutboxRecord(
        outbox_ref=f"outbox-ref:matrix:hardening-{index}",
        generation_ref=f"generation-ref:matrix:hardening-{index}",
        account_ref=ACCOUNT_REF,
        room_ref=ROOM_REF,
        transaction_ref=f"transaction-ref:matrix:hardening-{index}",
        operation=MatrixMessagingOperation.send,
        content_fingerprint_ref=fingerprint,
        state=MatrixOutboxState.queued,
        created_at=now,
        expires_at=now + timedelta(hours=1),
        room_id="!private-hardening:localhost",
        transaction_id=transaction_id,
        body=body,
    )


def _outbox(tmp_path: Path) -> MatrixEncryptedOutbox:
    backend = InMemoryMatrixCacheCryptoBackend()
    outbox = MatrixEncryptedOutbox(
        root=(tmp_path / "outbox").resolve(),
        crypto_backend=backend,
        key_item_ref="key-item-ref:matrix-hardening:outbox",
        key_version_ref="key-version-ref:matrix-hardening:outbox-v1",
    )
    outbox.create_key()
    return outbox


def test_hardening_posture_is_content_free_partial_and_non_authorizing() -> None:
    posture = build_default_matrix_hardening_posture()
    assert posture.runtime_status == "partial_hardening_evidence"
    assert len(posture.checks) == 12
    assert len(posture.budgets) == 8
    assert posture.new_runtime_authority_granted is False
    assert posture.calls_enabled is False
    assert posture.agent_participants_enabled is False
    assert posture.hosted_infrastructure_enabled is False
    assert posture.public_federation_enabled is False
    assert posture.production_deployment_enabled is False
    assert posture.element_interoperability_status == "external_facility_required"
    checks = {check.category: check for check in posture.checks}
    assert checks[MatrixHardeningCheckCategory.migration_multi_device].status == (
        MatrixHardeningCheckStatus.blocked
    )
    assert checks[MatrixHardeningCheckCategory.localization_readiness].status == (
        MatrixHardeningCheckStatus.partial
    )
    assert checks[MatrixHardeningCheckCategory.element_interoperability].status == (
        MatrixHardeningCheckStatus.external_facility_required
    )
    encoded = posture.model_dump_json().lower()
    for forbidden in ("/users/", "file://", "password", "access_token", "raw_message"):
        assert forbidden not in encoded


def test_cumulative_cache_history_is_bounded_with_deterministic_backpressure() -> None:
    state = MatrixProtectedCacheState.empty(
        account_ref=ACCOUNT_REF,
        cache_ref="cache-ref:matrix:hardening",
        generation_ref="generation-ref:matrix:hardening-0",
        key_version_ref=KEY_VERSION_REF,
    )
    started = time.perf_counter()
    for batch_index in range(11):
        state = state.apply_batch(
            _batch(batch_index * 500),
            next_generation_ref=f"generation-ref:matrix:hardening-{batch_index + 1}",
        )
    elapsed = time.perf_counter() - started
    assert elapsed < 3.0
    assert len(state.events) == MATRIX_SYNC_MAX_CACHE_EVENTS
    assert state.events[0].origin_server_ts == 500
    assert state.events[-1].origin_server_ts == 5_499
    assert len(state.rooms) == 1
    assert len(state.rooms[0].event_refs) == MATRIX_SYNC_MAX_ROOM_EVENT_REFS
    assert state.freshness == MatrixSyncFreshness.current


def test_protected_cache_low_disk_fails_before_stage_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache, state = _cache(tmp_path)
    monkeypatch.setattr(
        cache_module.os,
        "fstatvfs",
        lambda _descriptor: SimpleNamespace(f_bavail=0, f_frsize=1),
    )
    with pytest.raises(MatrixProtectedCacheError, match="MATRIX_CACHE_LOW_DISK"):
        cache.write(state, key_item_ref=KEY_ITEM_REF)
    assert list((tmp_path / "cache").iterdir()) == []


def test_protected_cache_unsupported_schema_fails_closed(tmp_path: Path) -> None:
    backend = InMemoryMatrixCacheCryptoBackend()
    backend.create(key_item_ref=KEY_ITEM_REF, key_version_ref=KEY_VERSION_REF)
    root = (tmp_path / "cache").resolve()
    cache = MatrixProtectedCache(root=root, crypto_backend=backend)
    state = MatrixProtectedCacheState.empty(
        account_ref=ACCOUNT_REF,
        cache_ref="cache-ref:matrix:hardening",
        generation_ref="generation-ref:matrix:hardening-0",
        key_version_ref=KEY_VERSION_REF,
    )
    payload = state.model_dump(mode="json")
    payload["schema_ref"] = "cache-schema-ref:matrix:unsupported-v2"
    encrypted = backend.encrypt(
        key_item_ref=KEY_ITEM_REF,
        key_version_ref=KEY_VERSION_REF,
        plaintext=json.dumps(payload, sort_keys=True).encode("utf-8"),
        aad=cache_module._aad(
            account_ref=ACCOUNT_REF,
            cache_ref=state.cache_ref,
            key_version_ref=KEY_VERSION_REF,
        ),
    )
    cache_path = root / cache._cache_name(state.cache_ref)
    cache_path.write_bytes(cache_module._CONTAINER_MAGIC + encrypted)

    with pytest.raises(MatrixProtectedCacheError, match="MATRIX_CACHE_SCHEMA_UNSUPPORTED"):
        cache.read(
            account_ref=ACCOUNT_REF,
            cache_ref=state.cache_ref,
            key_item_ref=KEY_ITEM_REF,
            key_version_ref=KEY_VERSION_REF,
            expected_generation_ref=state.generation_ref,
        )


def test_outbox_queue_limit_blocks_before_new_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MATRIX_MESSAGING_MAX_OUTBOX_RECORDS == 256
    monkeypatch.setattr(outbox_module, "MATRIX_MESSAGING_MAX_OUTBOX_RECORDS", 2)
    outbox = _outbox(tmp_path)
    outbox.write(_outbox_record(1))
    outbox.write(_outbox_record(2))
    with pytest.raises(MatrixOutboxError, match="MATRIX_OUTBOX_QUEUE_LIMIT_EXCEEDED"):
        outbox.write(_outbox_record(3))
    records = list((tmp_path / "outbox").glob("*.uaamxoutbox"))
    assert len(records) == 2


def test_outbox_hostile_queue_entry_fails_closed(tmp_path: Path) -> None:
    outbox = _outbox(tmp_path)
    hostile = tmp_path / "outbox" / "hostile.uaamxoutbox"
    hostile.symlink_to(tmp_path / "outside")
    with pytest.raises(MatrixOutboxError, match="MATRIX_OUTBOX_FILE_INVALID"):
        outbox.write(_outbox_record(1))


def test_outbox_low_disk_error_is_content_free_and_cleans_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outbox = _outbox(tmp_path)

    def fail_write(_descriptor: int, _value: bytes) -> int:
        raise OSError(getattr(os, "ENOSPC", 28), "private-path-must-not-escape")

    monkeypatch.setattr(outbox_module.os, "write", fail_write)
    with pytest.raises(MatrixOutboxError) as raised:
        outbox.write(_outbox_record(1))
    assert str(raised.value) == "MATRIX_OUTBOX_LOW_DISK"
    assert not list((tmp_path / "outbox").glob("*.tmp"))


def test_hardening_api_is_protected_no_store_and_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, raising=False)
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, LOCAL_BEARER)
    client = TestClient(app)
    assert client.get(POSTURE_PATH).status_code == 401
    response = client.get(
        POSTURE_PATH,
        headers={"Authorization": f"Bearer {LOCAL_BEARER}"},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["data"] == build_default_matrix_hardening_posture().model_dump(
        mode="json"
    )
    routes = {route.path: route for route in build_api_manifest(app).routes}
    route = routes[POSTURE_PATH]
    assert route.method == "GET"
    assert route.side_effect_class == "none"
    assert route.route_classification == "local_sensitive"
    assert route.idempotency_required is False
    assert route.operation_id == (
        "get_control_center_communications_matrix_hardening_posture"
    )


def test_hardening_cli_shares_core_truth() -> None:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    human = subprocess.run(
        [sys.executable, "scripts/dev/uaa_communications.py", "matrix-hardening-status"],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert "Matrix reliability and security hardening" in human.stdout
    assert "migration_multi_device: blocked" in human.stdout
    assert "Element interoperability: external_facility_required" in human.stdout
    assert "New runtime authority: denied" in human.stdout
    assert "{" not in human.stdout

    structured = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_communications.py",
            "matrix-hardening-status",
            "--json",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    assert json.loads(structured.stdout) == (
        build_default_matrix_hardening_posture().model_dump(mode="json")
    )
