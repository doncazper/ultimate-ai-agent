from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.chat.workspace import (
    CHAT_DRAFT_EMPTY_FINGERPRINT_REF,
    CHAT_WORKSPACE_CONTRACT_REF,
    CHAT_WORKSPACE_MAX_REQUEST_BYTES,
    CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH,
    ChatDraftCheckpointRequest,
    ChatThreadLifecycleRequest,
)
from ultimate_ai_agent.core.chat.workspace_repository import ChatWorkspaceRepository
from ultimate_ai_agent.core.chat.workspace_service import (
    ChatWorkspaceApprovalError,
    ChatWorkspaceControlCenterService,
)
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.storage import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


THREAD_REF = "chat-thread:q33-workspace-test"


def _checkpoint(
    *, count: int = 24, expected_revision: int = 0
) -> ChatDraftCheckpointRequest:
    return ChatDraftCheckpointRequest(
        confirmed=True,
        expected_revision=expected_revision,
        draft_present=count > 0,
        draft_character_count=count,
        draft_fingerprint_ref=(
            "draft-fingerprint-ref:chat:local-a001c0250539fdc1a001c0250539fdc1"
            if count > 0
            else CHAT_DRAFT_EMPTY_FINGERPRINT_REF
        ),
        metadata_refs=[f"metadata-ref:chat-workspace:revision-{expected_revision}"],
    )


def _record_checkpoint(
    repo: ChatWorkspaceRepository,
    *,
    request: ChatDraftCheckpointRequest,
    key: str,
    thread_ref: str = THREAD_REF,
) -> dict:
    return ChatWorkspaceControlCenterService(repo).record_draft_checkpoint(
        thread_ref=thread_ref,
        request=request,
        idempotency_key_ref=f"idempotency-ref:chat-workspace:{key}",
    )


def _record_lifecycle(
    repo: ChatWorkspaceRepository,
    *,
    action: str,
    expected_revision: int,
    key: str,
) -> dict:
    return ChatWorkspaceControlCenterService(repo).record_lifecycle(
        thread_ref=THREAD_REF,
        request=ChatThreadLifecycleRequest(
            confirmed=True,
            action=action,
            expected_revision=expected_revision,
        ),
        idempotency_key_ref=f"idempotency-ref:chat-workspace:{key}",
    )


def _mutation_binding_headers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    origin: str | None = None,
) -> dict[str, str]:
    source_revision = "7" * 40
    monkeypatch.setenv("UAA_BUILD_COMMIT", source_revision)
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "binding-state"),
        identity=build_identity(env={"UAA_BUILD_COMMIT": source_revision}),
    )
    return {
        **({"origin": origin} if origin else {}),
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{source_revision}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }


def test_chat_draft_checkpoint_schema_never_accepts_a_draft_body() -> None:
    without_confirmation = _checkpoint().model_dump(mode="json")
    without_confirmation.pop("confirmed")
    with pytest.raises(ValidationError, match="Field required"):
        ChatDraftCheckpointRequest.model_validate(without_confirmation)

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ChatDraftCheckpointRequest.model_validate(
            {
                **_checkpoint().model_dump(mode="json"),
                "draft_body": "x" * 24,
            }
        )

    with pytest.raises(ValidationError, match="String should match pattern"):
        ChatDraftCheckpointRequest(
            confirmed=True,
            expected_revision=0,
            draft_present=True,
            draft_character_count=24,
            draft_fingerprint_ref="draft-fingerprint-ref:chat:not-a-fingerprint",
        )

    with pytest.raises(ValidationError, match="at most 200 characters"):
        ChatDraftCheckpointRequest(
            confirmed=True,
            expected_revision=0,
            draft_present=False,
            draft_character_count=0,
            draft_fingerprint_ref=CHAT_DRAFT_EMPTY_FINGERPRINT_REF,
            metadata_refs=["metadata-ref:" + "x" * 201],
        )

    with pytest.raises(
        ValidationError,
        match="metadata refs must bind the expected revision",
    ):
        ChatDraftCheckpointRequest(
            confirmed=True,
            expected_revision=0,
            draft_present=False,
            draft_character_count=0,
            draft_fingerprint_ref=CHAT_DRAFT_EMPTY_FINGERPRINT_REF,
            metadata_refs=["metadata-ref:chat-workspace:private-note"],
        )


def test_chat_workspace_persists_metadata_and_lifecycle_without_content(
    tmp_path: Path,
) -> None:
    repo = ChatWorkspaceRepository(tmp_path / "founder-loop")

    clean_start = repo.workspace()
    assert clean_start["status"] == "safe_demo_ready"
    assert clean_start["threads"] == []
    assert clean_start["draft_body_stored"] is False
    assert clean_start["model_call_enabled"] is False
    assert clean_start["send_enabled"] is False

    receipt = _record_checkpoint(repo, request=_checkpoint(), key="checkpoint-1")
    replay = _record_checkpoint(repo, request=_checkpoint(), key="checkpoint-1")

    assert receipt["contract_ref"] == CHAT_WORKSPACE_CONTRACT_REF
    assert receipt["raw_draft_received"] is False
    assert receipt["draft_body_stored"] is False
    assert receipt["model_call_performed"] is False
    assert receipt["approval_ref"].startswith(
        "approval-ref:chat-workspace:sha256:"
    )
    assert receipt["exact_approval_scope_ref"].startswith(
        "approval-scope-ref:chat-workspace:sha256:"
    )
    assert replay["replayed"] is True
    assert replay["receipt_ref"] == receipt["receipt_ref"]

    with pytest.raises(FounderLoopStorageDuplicateError):
        _record_checkpoint(
            repo,
            request=ChatDraftCheckpointRequest(
                confirmed=True,
                expected_revision=0,
                draft_present=True,
                draft_character_count=25,
                draft_fingerprint_ref=(
                    "draft-fingerprint-ref:chat:local-b001c0250539fdc1b001c0250539fdc1"
                ),
            ),
            key="checkpoint-1",
        )

    archived = _record_lifecycle(
        repo,
        action="archive",
        expected_revision=1,
        key="archive-1",
    )
    assert archived["thread"]["state"] == "archived"
    assert archived["tool_execution_performed"] is False
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_THREAD_ALREADY_ARCHIVED",
    ):
        _record_lifecycle(
            repo,
            action="archive",
            expected_revision=2,
            key="archive-2",
        )
    with pytest.raises(FounderLoopStorageError, match="CHAT_THREAD_ARCHIVED"):
        _record_checkpoint(
            repo,
            request=_checkpoint(expected_revision=2),
            key="checkpoint-2",
        )

    recovered = _record_lifecycle(
        repo,
        action="recover",
        expected_revision=2,
        key="recover-1",
    )
    workspace = repo.workspace()

    assert recovered["thread"]["state"] == "active"
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_THREAD_ALREADY_ACTIVE",
    ):
        _record_lifecycle(
            repo,
            action="recover",
            expected_revision=3,
            key="recover-2",
        )
    assert workspace["status"] == "workspace_ready"
    assert workspace["active_thread_ref"] == THREAD_REF
    assert workspace["threads"][0]["display_name"] == "Conversation 1"
    assert workspace["threads"][0]["draft_character_count"] == 24
    assert workspace["threads"][0]["draft_recovery_state"] == (
        "metadata_only_reentry_required"
    )
    assert workspace["threads"][0]["draft_body_stored"] is False


def test_chat_workspace_validates_exact_local_approval_before_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo = ChatWorkspaceRepository(tmp_path / "founder-loop")
    authority = LocalApprovalAuthority()
    monkeypatch.setattr(
        authority,
        "validate_for_request",
        lambda *_args, **_kwargs: SimpleNamespace(allowed=False),
    )
    service = ChatWorkspaceControlCenterService(
        repo,
        approval_authority=authority,
    )

    with pytest.raises(ChatWorkspaceApprovalError, match="APPROVAL_DENIED"):
        service.record_draft_checkpoint(
            thread_ref=THREAD_REF,
            request=_checkpoint(),
            idempotency_key_ref="idempotency-ref:chat-workspace:approval-denied",
        )

    assert repo.workspace()["threads"] == []


def test_chat_workspace_repairs_pending_evidence_on_exact_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = ChatWorkspaceRepository(state_dir)
    original_append = repo._founder_loop.append_log

    def fail_append(*_args, **_kwargs):
        raise OSError("simulated evidence sink failure")

    monkeypatch.setattr(repo._founder_loop, "append_log", fail_append)
    with pytest.raises(FounderLoopStorageError, match="EVIDENCE_PENDING"):
        _record_checkpoint(
            repo,
            request=_checkpoint(),
            key="pending-evidence",
        )

    monkeypatch.setattr(repo._founder_loop, "append_log", original_append)
    replay = _record_checkpoint(
        repo,
        request=_checkpoint(),
        key="pending-evidence",
    )
    records = [
        json.loads(line)
        for line in (state_dir / "logs" / "receipt.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert replay["replayed"] is True
    assert [record["event_ref"] for record in records] == [replay["receipt_ref"]]
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        delivered_at = conn.execute(
            "SELECT delivered_at FROM chat_workspace_evidence_outbox"
        ).fetchone()[0]
    assert delivered_at is not None


def test_chat_workspace_rejects_creation_beyond_visible_capacity(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = ChatWorkspaceRepository(state_dir)
    timestamp = "2026-09-08T01:00:00+00:00"
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        conn.executemany(
            """
            INSERT INTO chat_thread_states (
                thread_ref, display_name, state, revision, draft_present,
                draft_character_count, draft_fingerprint_ref, created_at, updated_at
            ) VALUES (?, ?, 'active', 1, 0, 0, ?, ?, ?)
            """,
            [
                (
                    f"chat-thread:capacity-{index:03d}",
                    f"Conversation {index}",
                    CHAT_DRAFT_EMPTY_FINGERPRINT_REF,
                    timestamp,
                    timestamp,
                )
                for index in range(1, 101)
            ],
        )

    assert len(repo.workspace()["threads"]) == 100
    with pytest.raises(FounderLoopStorageError, match="CAPACITY_REACHED"):
        _record_checkpoint(
            repo,
            request=_checkpoint(),
            key="capacity-overflow",
            thread_ref="chat-thread:capacity-overflow",
        )


def test_chat_workspace_serializes_concurrent_idempotent_checkpoints(
    tmp_path: Path,
) -> None:
    repo = ChatWorkspaceRepository(tmp_path / "founder-loop")
    idempotency_key_ref = "idempotency-ref:chat-workspace:concurrent-checkpoint"

    def record() -> dict:
        return _record_checkpoint(
            repo,
            request=_checkpoint(),
            key=idempotency_key_ref.removeprefix("idempotency-ref:chat-workspace:"),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(executor.map(lambda _: record(), range(8)))

    assert len({receipt["receipt_ref"] for receipt in receipts}) == 1
    assert sum(not receipt["replayed"] for receipt in receipts) == 1
    assert repo.workspace()["threads"][0]["revision"] == 1


def test_chat_workspace_rejects_stale_checkpoint_and_lifecycle_revisions(
    tmp_path: Path,
) -> None:
    repo = ChatWorkspaceRepository(tmp_path / "founder-loop")
    _record_checkpoint(
        repo,
        request=_checkpoint(),
        key="revision-create",
    )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT",
    ):
        _record_checkpoint(
            repo,
            request=_checkpoint(count=25),
            key="revision-stale-draft",
        )
    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_THREAD_REVISION_CONFLICT",
    ):
        _record_lifecycle(
            repo,
            action="archive",
            expected_revision=2,
            key="revision-stale-state",
        )

    thread = repo.workspace()["threads"][0]
    assert thread["revision"] == 1
    assert thread["state"] == "active"
    assert thread["draft_character_count"] == 24


def test_chat_workspace_revalidates_stored_replay_receipts(tmp_path: Path) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = ChatWorkspaceRepository(state_dir)
    key_ref = "idempotency-ref:chat-workspace:corrupt-replay"
    _record_checkpoint(
        repo,
        request=_checkpoint(),
        key=key_ref.removeprefix("idempotency-ref:chat-workspace:"),
    )
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        stored = json.loads(
            conn.execute(
                "SELECT receipt_json FROM chat_thread_mutation_replays WHERE key_ref = ?",
                (key_ref,),
            ).fetchone()[0]
        )
        stored["model_call_performed"] = True
        conn.execute(
            "UPDATE chat_thread_mutation_replays SET receipt_json = ? WHERE key_ref = ?",
            (json.dumps(stored), key_ref),
        )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT",
    ):
        _record_checkpoint(
            repo,
            request=_checkpoint(),
            key=key_ref.removeprefix("idempotency-ref:chat-workspace:"),
        )


def test_chat_workspace_rebinds_stored_replay_to_exact_request(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = ChatWorkspaceRepository(state_dir)
    key_ref = "idempotency-ref:chat-workspace:rebound-replay"
    _record_checkpoint(
        repo,
        request=_checkpoint(),
        key=key_ref.removeprefix("idempotency-ref:chat-workspace:"),
    )
    with sqlite3.connect(state_dir / "founder_loop.sqlite3") as conn:
        stored = json.loads(
            conn.execute(
                "SELECT receipt_json FROM chat_thread_mutation_replays WHERE key_ref = ?",
                (key_ref,),
            ).fetchone()[0]
        )
        stored["payload_fingerprint_ref"] = (
            "payload-fingerprint:chat-workspace:" + "a" * 64
        )
        conn.execute(
            "UPDATE chat_thread_mutation_replays SET receipt_json = ? WHERE key_ref = ?",
            (json.dumps(stored), key_ref),
        )

    with pytest.raises(
        FounderLoopStorageError,
        match="FOUNDER_LOOP_CHAT_WORKSPACE_REPLAY_CORRUPT",
    ):
        _record_checkpoint(
            repo,
            request=_checkpoint(),
            key=key_ref.removeprefix("idempotency-ref:chat-workspace:"),
        )


def test_chat_workspace_rejects_unbounded_or_wrong_namespace_thread_refs(
    tmp_path: Path,
) -> None:
    repo = ChatWorkspaceRepository(tmp_path / "founder-loop")

    for thread_ref in ("other-thread:q33", "chat-thread:" + "x" * 300):
        with pytest.raises(ValueError, match="bounded Chat workspace ref"):
            _record_checkpoint(
                repo,
                thread_ref=thread_ref,
                request=_checkpoint(),
                key="invalid-thread",
            )

    assert repo.workspace()["threads"] == []


def test_chat_workspace_api_exposes_clean_start_and_content_free_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "api-state"))
    client = TestClient(app)

    clean_start = client.get("/control-center/chat/workspace")
    assert clean_start.status_code == 200
    assert clean_start.json()["data"]["status"] == "safe_demo_ready"

    checkpoint = client.post(
        f"/control-center/chat/threads/{THREAD_REF}/draft-checkpoint",
        headers={
            **_mutation_binding_headers(monkeypatch, tmp_path),
            "X-UAA-Idempotency-Key": (
                "idempotency-ref:chat-workspace:api-checkpoint-1"
            ),
        },
        json=_checkpoint().model_dump(mode="json"),
    )
    assert checkpoint.status_code == 200
    assert checkpoint.json()["data"]["raw_draft_received"] is False
    assert checkpoint.json()["data"]["draft_body_stored"] is False

    workspace = client.get("/control-center/chat/workspace")
    assert workspace.status_code == 200
    assert workspace.json()["data"]["threads"][0]["thread_ref"] == THREAD_REF


def test_chat_workspace_api_rejects_body_fields_and_missing_threads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "api-state"))
    client = TestClient(app)

    unsafe = client.post(
        f"/control-center/chat/threads/{THREAD_REF}/draft-checkpoint",
        headers={
            **_mutation_binding_headers(monkeypatch, tmp_path),
            "X-UAA-Idempotency-Key": "idempotency-ref:chat:unsafe",
        },
        json={**_checkpoint().model_dump(mode="json"), "draft_body": "x" * 24},
    )
    assert unsafe.status_code == 422

    missing = client.post(
        f"/control-center/chat/threads/{THREAD_REF}/lifecycle",
        headers={
            **_mutation_binding_headers(monkeypatch, tmp_path),
            "X-UAA-Idempotency-Key": "idempotency-ref:chat:missing",
        },
        json={"confirmed": True, "action": "archive", "expected_revision": 1},
    )
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "FOUNDER_LOOP_CHAT_THREAD_NOT_FOUND"


def test_chat_workspace_api_rejects_oversized_and_deep_json_before_decode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "api-state"))
    client = TestClient(app)
    route = f"/control-center/chat/threads/{THREAD_REF}/draft-checkpoint"
    origin = "http://localhost:5173"
    bound_headers = _mutation_binding_headers(
        monkeypatch,
        tmp_path,
        origin=origin,
    )

    oversized = client.post(
        route,
        content=b"{" + b"x" * CHAT_WORKSPACE_MAX_REQUEST_BYTES,
        headers={
            **bound_headers,
            "content-type": "application/json",
            "content-length": "1",
            "X-UAA-Idempotency-Key": "idempotency-ref:chat:oversized-body",
        },
    )
    assert oversized.status_code == 413
    assert oversized.headers["Cache-Control"] == "no-store"
    assert oversized.headers["Access-Control-Allow-Origin"] == origin
    assert oversized.json() == {
        "detail": (
            "The content-free Chat workspace request exceeds the permitted local bound."
        ),
        "code": "CHAT_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED",
        "contract_ref": CHAT_WORKSPACE_CONTRACT_REF,
        "maximum_body_bytes": CHAT_WORKSPACE_MAX_REQUEST_BYTES,
        "maximum_json_nesting_depth": CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH,
    }

    deeply_nested = b"[" * (CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH + 1)
    deeply_nested += b"]" * (CHAT_WORKSPACE_MAX_REQUEST_NESTING_DEPTH + 1)
    nested = client.post(
        route,
        content=deeply_nested,
        headers={
            **bound_headers,
            "content-type": "application/json",
            "X-UAA-Idempotency-Key": "idempotency-ref:chat:deep-body",
        },
    )
    assert nested.status_code == 422
    assert nested.headers["Cache-Control"] == "no-store"
    assert nested.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_chat_workspace_private_routes_are_no_store_and_publish_body_limit() -> None:
    client = TestClient(app)
    read_response = client.get("/control-center/chat/workspace")
    assert read_response.headers["Cache-Control"] == "no-store"
    route = f"/control-center/chat/threads/{THREAD_REF}/draft-checkpoint"
    missing_idempotency = client.post(route, json={})
    missing_binding = client.post(
        route,
        headers={
            "X-UAA-Idempotency-Key": "idempotency-ref:chat:no-store-binding"
        },
        json={},
    )

    assert missing_idempotency.status_code == 428
    assert missing_idempotency.headers["Cache-Control"] == "no-store"
    assert missing_binding.status_code == 409
    assert missing_binding.headers["Cache-Control"] == "no-store"

    paths = app.openapi()["paths"]
    for route in (
        "/control-center/chat/threads/{thread_ref}/draft-checkpoint",
        "/control-center/chat/threads/{thread_ref}/lifecycle",
    ):
        response = paths[route]["post"]["responses"]["413"]
        schema = response["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/ChatWorkspaceBodyTooLargeResponse")


def test_chat_workspace_cli_is_read_only_content_free_and_missing_state_safe(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "founder-loop"
    repo = ChatWorkspaceRepository(state_dir)
    _record_checkpoint(
        repo,
        request=_checkpoint(),
        key="cli-checkpoint",
    )
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).resolve().parents[1]
                / "scripts/inspect_chat_workspace.py"
            ),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    payload = json.loads(result.stdout)

    assert after_files == before_files
    assert payload["command_ref"] == "repo-local-command:inspect-chat-workspace"
    assert payload["storage_state"] == "existing_state_read_only"
    assert (
        payload["chat_workspace_read_model"]["threads"][0]["thread_ref"] == THREAD_REF
    )
    assert payload["draft_metadata_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["draft_body_stored"] is False
    assert payload["model_call_enabled"] is False
    assert payload["production_authority_enabled"] is False

    missing_state_dir = tmp_path / "missing-founder-loop"
    missing = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).resolve().parents[1]
                / "scripts/inspect_chat_workspace.py"
            ),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert missing_payload["chat_workspace_read_model"]["status"] == "safe_demo_ready"
    assert not missing_state_dir.exists()
