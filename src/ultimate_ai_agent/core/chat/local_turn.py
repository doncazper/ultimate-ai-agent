"""One explicit first-party Send, one approved local turn, no transcript store."""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import timedelta
from typing import Any

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest, ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority,
)
from ultimate_ai_agent.core.control_center.backend_truth import backend_instance_ref
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.decision_router import build_chat_turn_harness_binding
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.local_model_management.gateway import (
    M164ChatCompletionRequest, M164GatewayTransport, M164LocalGatewayModel,
    build_m164_chat_completion_response, build_m164_gateway_model_from_env,
    llama_cpp_backend_api_key, llama_cpp_gateway_enabled, llama_cpp_gateway_key,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.time import utc_now


LOCAL_TURN_CONTRACT_REF = "contract-ref:chat-explicit-local-turn:v1"
LOCAL_TURN_CONFIRMATION = "send-one-local-turn.v1"
LOCAL_TURN_HISTORY_LIMIT = 10_000
# A commitment is not a reusable dictionary of prompt hashes. This key never
# leaves process memory; restart-stable attempt identity is separate below.
_COMMITMENT_KEY = secrets.token_bytes(32)
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,199}$")
_ATTEMPT_RE = re.compile(r"^chat-attempt-ref:sha256:[0-9a-f]{64}$")


class LocalTurnError(ValueError):
    def __init__(self, code: str, status_code: int) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(code)


def _encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _ordinary_request(request: M164ChatCompletionRequest) -> M164ChatCompletionRequest:
    snapshot = M164ChatCompletionRequest.model_validate(request.model_dump(mode="python"))
    if (
        not 1 <= len(snapshot.messages) <= 63
        or len(snapshot.messages) % 2 != 1
        or any(
            message.role != ("user" if index % 2 == 0 else "assistant")
            or not isinstance(message.content, str)
            or not message.content.strip()
            for index, message in enumerate(snapshot.messages)
        )
        or sum(len(message.content or "") for message in snapshot.messages) > 64_000
        or snapshot.tools is not None or snapshot.functions is not None
        or (snapshot.max_tokens is not None and snapshot.max_tokens > 1024)
        or (snapshot.temperature is not None and (
            not math.isfinite(snapshot.temperature) or not 0 <= snapshot.temperature <= 2
        ))
    ):
        raise LocalTurnError("LOCAL_TURN_REQUEST_DENIED", 422)
    # An omitted limit cannot turn this bounded lane into an unbounded request.
    snapshot.max_tokens = snapshot.max_tokens or 1024
    return snapshot


def _require_current_target(
    model: M164LocalGatewayModel, revision_ref: str, instance_ref: str,
) -> None:
    identity = build_identity()
    if not llama_cpp_gateway_enabled() or not llama_cpp_gateway_key():
        raise LocalTurnError("LOCAL_TURN_DISABLED", 403)
    if (
        not identity.source_revision_bound
        or revision_ref != identity.commit_ref
        or instance_ref != backend_instance_ref()
        or model != build_m164_gateway_model_from_env()
    ):
        raise LocalTurnError("LOCAL_TURN_TARGET_CHANGED", 409)


def _ensure_schema(repository: FounderLoopRepository) -> None:
    with closing(repository._connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_local_turn_attempts (
                attempt_ref TEXT PRIMARY KEY,
                scope_ref TEXT NOT NULL,
                approval_request_json TEXT NOT NULL,
                approval_grant_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('started', 'completed', 'outcome_uncertain')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def _settle(repository: FounderLoopRepository, attempt_ref: str, status: str) -> None:
    with closing(repository._connect()) as conn, conn:
        changed = conn.execute(
            "UPDATE chat_local_turn_attempts SET status = ?, updated_at = ? "
            "WHERE attempt_ref = ? AND status = 'started'",
            (status, utc_now().isoformat(), attempt_ref),
        ).rowcount
        if changed != 1:
            raise LocalTurnError("LOCAL_TURN_SETTLEMENT_UNCERTAIN", 503)


def send_local_conversation_turn(
    request: M164ChatCompletionRequest,
    *,
    confirmed: bool,
    idempotency_key_ref: str,
    backend_revision_ref: str,
    expected_backend_instance_ref: str,
    gateway_model: M164LocalGatewayModel,
    repository: FounderLoopRepository | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
    transport: M164GatewayTransport | None = None,
) -> dict[str, Any]:
    """Capture Send's exact approval and durably consume it before any transport.

    API callers must first authenticate the local operator and validate fresh
    backend truth. A generic session or diagnostic probe is not confirmation.
    This mirrors the existing confirmed Finance operator workflow, not a new
    standing lease. Every repeated attempt is denied, even after a lost reply.
    """
    if confirmed is not True:
        raise LocalTurnError("LOCAL_TURN_CONFIRMATION_REQUIRED", 403)
    if not _IDEMPOTENCY_RE.fullmatch(idempotency_key_ref):
        raise LocalTurnError("LOCAL_TURN_IDEMPOTENCY_REQUIRED", 428)
    local_request = _ordinary_request(request)
    model = M164LocalGatewayModel.model_validate(gateway_model.model_dump())
    _require_current_target(model, backend_revision_ref, expected_backend_instance_ref)
    if local_request.model != model.model_id:
        raise LocalTurnError("LOCAL_TURN_MODEL_NOT_APPROVED", 422)
    api_key = llama_cpp_backend_api_key()
    attempt_ref = "chat-attempt-ref:sha256:" + hashlib.sha256(
        idempotency_key_ref.encode("utf-8")
    ).hexdigest()
    scope_ref = "chat-turn-scope-ref:hmac-sha256:" + hmac.new(
        _COMMITMENT_KEY,
        _encoded({
            "contract": LOCAL_TURN_CONTRACT_REF,
            "attempt": attempt_ref,
            "request": local_request.model_dump(mode="json"),
            "target": model.model_dump(mode="json"),
            "revision": backend_revision_ref,
            "instance": expected_backend_instance_ref,
        }).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    digest = scope_ref.rsplit(":", 1)[-1]
    now = utc_now()
    approval_request = ApprovalRequest(
        approval_request_id=f"approval-request-ref:chat-turn:{digest}",
        run_id=attempt_ref,
        subject_type=ApprovalSubjectType.model_runtime_request,
        subject_id=scope_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="operator-ref:local-user",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action="send_one_local_chat_turn",
        purpose="Approve one explicit bounded local conversation turn.",
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="explicit_local_chat",
            requires_redaction=True,
        ),
        resource_refs=[LOCAL_TURN_CONTRACT_REF, attempt_ref, scope_ref,
                       backend_revision_ref, expected_backend_instance_ref],
        created_at=now,
        expires_at=now + timedelta(minutes=2),
    )
    authority = approval_authority or LocalApprovalAuthority()
    repo = repository
    started = False
    try:
        repo = repo or FounderLoopRepository.from_env(seed_defaults=False)
        _ensure_schema(repo)
        with authority.hold_validation_lock(), closing(repo._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute(
                "SELECT 1 FROM chat_local_turn_attempts WHERE attempt_ref = ?",
                (attempt_ref,),
            ).fetchone() is not None:
                raise LocalTurnError("LOCAL_TURN_ALREADY_ATTEMPTED", 409)
            if conn.execute("SELECT COUNT(*) FROM chat_local_turn_attempts").fetchone()[0] >= LOCAL_TURN_HISTORY_LIMIT:
                raise LocalTurnError("LOCAL_TURN_HISTORY_FULL", 503)
            authority.create_request(approval_request)
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id="operator-ref:local-user",
                approval_ref=f"approval-ref:chat-turn:{digest}",
                expires_at=approval_request.expires_at,
            )
            if not authority.validate_for_request(approval_request, grant.approval_ref).allowed:
                raise LocalTurnError("LOCAL_TURN_APPROVAL_DENIED", 403)
            _require_current_target(model, backend_revision_ref, expected_backend_instance_ref)
            conn.execute(
                "INSERT INTO chat_local_turn_attempts VALUES (?, ?, ?, ?, 'started', ?, ?)",
                (attempt_ref, scope_ref, _encoded(approval_request.model_dump(mode="json")),
                 _encoded(grant.model_dump(mode="json")), now.isoformat(), now.isoformat()),
            )
        # The transaction is committed before transport. No error path removes
        # this start, including a crash, cancellation or response validation error.
        started = True
        with authority.hold_validation_lock():
            _require_current_target(model, backend_revision_ref, expected_backend_instance_ref)
            if not authority.validate_for_request(approval_request, grant.approval_ref).allowed:
                raise LocalTurnError("LOCAL_TURN_APPROVAL_DENIED", 403)
            if llama_cpp_backend_api_key() != api_key:
                raise LocalTurnError("LOCAL_TURN_TARGET_CHANGED", 409)
            response = build_m164_chat_completion_response(
                local_request, gateway_model=model, api_key=api_key, transport=transport,
                allow_repeated_assistant_reply=True,
                turn_harness_binding=build_chat_turn_harness_binding(
                    local_request.messages, model_ref=local_request.model,
                ),
            )
        _settle(repo, attempt_ref, "completed")
    except LocalTurnError:
        raise
    except (OSError, RuntimeError, ValueError, sqlite3.Error):
        # Best effort changes only a committed start. Storage failure leaves a
        # start unresolved and still non-replayable; never report a false success.
        if started and repo is not None:
            try:
                _settle(repo, attempt_ref, "outcome_uncertain")
            except (OSError, RuntimeError, ValueError, sqlite3.Error):
                pass
        raise LocalTurnError(
            "LOCAL_TURN_OUTCOME_UNCERTAIN" if started else "LOCAL_TURN_STORAGE_UNAVAILABLE", 503,
        ) from None
    response["uaa_safety"]["local_turn_approval"] = {
        "contract_ref": LOCAL_TURN_CONTRACT_REF,
        "attempt_ref": attempt_ref,
        "idempotency_key_ref": idempotency_key_ref,
        "approval_ref": grant.approval_ref,
        "scope_ref": scope_ref,
        "status": "completed",
        "exact_approval_validated": True,
        "durable_start_recorded": True,
        "raw_content_persisted": False,
    }
    return response


def inspect_local_turn_attempt(
    attempt_ref: str, *, repository: FounderLoopRepository | None = None,
) -> dict[str, Any]:
    """Read-only CLI/API parity: inspect safe evidence, never replay a turn."""
    if not _ATTEMPT_RE.fullmatch(attempt_ref):
        raise LocalTurnError("LOCAL_TURN_ATTEMPT_REF_INVALID", 422)
    repo = repository or FounderLoopRepository.from_env(
        seed_defaults=False, ensure_storage=False, read_only=True,
    )
    if not repo.db_path.exists():
        return {"attempt_ref": attempt_ref, "status": "missing"}
    with closing(repo._connect()) as conn:
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'chat_local_turn_attempts'"
        ).fetchone() is None:
            return {"attempt_ref": attempt_ref, "status": "missing"}
        row = conn.execute(
            "SELECT status FROM chat_local_turn_attempts WHERE attempt_ref = ?", (attempt_ref,),
        ).fetchone()
    value = str(row[0]) if row else "missing"
    return {
        "contract_ref": LOCAL_TURN_CONTRACT_REF,
        "attempt_ref": attempt_ref,
        "status": value if value in {"started", "completed", "outcome_uncertain", "missing"} else "outcome_uncertain",
        "automatic_replay_allowed": False,
        "raw_content_persisted": False,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect one content-free local Chat attempt; never execute.")
    parser.add_argument("--attempt-ref", required=True)
    arguments = parser.parse_args()
    try:
        print(json.dumps(inspect_local_turn_attempt(arguments.attempt_ref), sort_keys=True))
    except (OSError, RuntimeError, ValueError, sqlite3.Error):
        print('{"status":"unavailable","automatic_replay_allowed":false}')
        raise SystemExit(1) from None
