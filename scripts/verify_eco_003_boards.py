#!/usr/bin/env python3
"""Verify the bounded ECO-003 reusable Boards core."""

from __future__ import annotations

import tempfile
from datetime import timedelta
from pathlib import Path

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.boards import (
    ECO_BOARD_MUTATION_ACTION,
    Board,
    BoardLane,
    BoardRepository,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
)
from ultimate_ai_agent.core.ecosystem.tasks import TaskRepository
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/boards.py",
    "tests/test_eco_003_boards.py",
    "docs/architecture/ECO_003_REUSABLE_BOARDS_AND_TASK_PROJECTIONS.md",
    "docs/decisions/ADR-0065-reusable-boards-and-task-projections.md",
)
FORBIDDEN_SOURCE_MARKERS = (
    "requests.",
    "httpx.",
    "urllib.request",
    "subprocess.",
    "schedule.run_pending",
)


def _approval(
    authority: LocalApprovalAuthority,
    *,
    suffix: str,
    action: str,
    resource_refs: tuple[str, ...],
):
    request = ApprovalRequest(
        approval_request_id=f"approval_request_{suffix}",
        run_id="run_eco_003_verification",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco_003_verifier",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify the bounded ECO-003 Board mutation contract.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-003-verifier",
            requires_redaction=True,
        ),
        resource_refs=list(resource_refs),
        expires_at=utc_now() + timedelta(minutes=5),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id, approval_ref=f"approval_{suffix}"
    )
    return request.to_validation_request(grant.approval_ref)


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-003 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in source:
            failures.append(f"forbidden ECO-003 runtime marker: {marker}")

    private_marker = "synthetic-private-marker-eco003"
    try:
        with tempfile.TemporaryDirectory() as directory:
            database_path = (Path(directory) / "ecosystem.sqlite3").resolve()
            authority = LocalApprovalAuthority()
            platform = EcosystemLocalDataPlatform(
                database_path=database_path,
                crypto_backend=InMemoryLocalDataCryptoBackend(),
                approval_authority=authority,
                path_resolver=InMemoryLocalDataPathResolver(),
            )
            workspace_ref = "workspace-ref:eco-003-verification"
            key_ref = "key-version-ref:v1"
            platform.create_workspace(
                workspace_ref=workspace_ref,
                key_version_ref=key_ref,
                approval=_approval(
                    authority,
                    suffix="workspace",
                    action="ecosystem.local_data.create_workspace",
                    resource_refs=(workspace_ref, key_ref),
                ),
            )
            repository = BoardRepository(
                platform, task_repository=TaskRepository(platform)
            )
            board = Board(
                workspace_ref=workspace_ref,
                board_ref="board-ref:eco-003-verification",
                name=private_marker,
                lanes=(BoardLane(lane_ref="lane-ref:inbox", name="Inbox", position=0),),
            )
            operation_ref = "operation-ref:eco-003-verification"
            idempotency_ref = "idempotency-ref:eco-003-verification"
            resources = repository.mutation_resource_refs(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                record_ref=board.board_ref,
            )
            repository.create_board(
                board=board,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=_approval(
                    authority,
                    suffix="board",
                    action=ECO_BOARD_MUTATION_ACTION,
                    resource_refs=resources,
                ),
            )
            if (
                repository.read(workspace_ref=workspace_ref, board_ref=board.board_ref)
                != board
            ):
                failures.append("ECO-003 canonical Board read mismatch")
            if private_marker.encode() in database_path.read_bytes():
                failures.append("private Board marker leaked into SQLite data plane")
    except Exception as exc:
        failures.append(f"ECO-003 smoke verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: ECO-003 reusable Boards and Task projection boundary verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
