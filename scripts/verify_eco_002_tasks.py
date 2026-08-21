#!/usr/bin/env python3
"""Verify the bounded ECO-002 canonical Tasks core."""

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
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
)
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MUTATION_ACTION,
    CanonicalTask,
    TaskMissionBinding,
    TaskQuery,
    TaskRepository,
    TaskView,
)
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
    "src/ultimate_ai_agent/core/ecosystem/tasks.py",
    "tests/test_eco_002_tasks.py",
    "docs/architecture/ECO_002_CANONICAL_TASKS_AND_MISSION_OWNERSHIP.md",
    "docs/decisions/ADR-0064-canonical-tasks-and-mission-ownership.md",
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
        run_id="run_eco_002_verification",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco_002_verifier",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify the bounded ECO-002 canonical Task mutation contract.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-002-verifier",
            requires_redaction=True,
        ),
        resource_refs=list(resource_refs),
        expires_at=utc_now() + timedelta(minutes=5),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval_{suffix}",
    )
    return request.to_validation_request(grant.approval_ref)


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-002 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        if marker in source:
            failures.append(f"forbidden ECO-002 runtime marker: {marker}")

    private_marker = "synthetic-private-marker-eco002"
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
            workspace_ref = "workspace-ref:eco-002-verification"
            key_version_ref = "key-version-ref:v1"
            platform.create_workspace(
                workspace_ref=workspace_ref,
                approval=_approval(
                    authority,
                    suffix="workspace",
                    action="ecosystem.local_data.create_workspace",
                    resource_refs=(workspace_ref, key_version_ref),
                ),
            )
            repository = TaskRepository(platform)
            task = CanonicalTask(
                workspace_ref=workspace_ref,
                task_ref="task-ref:eco-002-verification",
                title=private_marker,
                mission_binding=TaskMissionBinding(
                    mission_ref="mission-ref:eco-002-verification",
                    run_ref="run-ref:eco-002-verification",
                    plan_ref="plan-ref:eco-002-verification",
                    owner_ref="owner-ref:eco-002-verification",
                    binding_evidence_ref="evidence-ref:eco-002-verification",
                ),
            )
            operation_ref = "operation-ref:eco-002-verification"
            idempotency_ref = "idempotency-ref:eco-002-verification"
            resources = repository.mutation_resource_refs(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                task_ref=task.task_ref,
            )
            repository.create(
                task=task,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=_approval(
                    authority,
                    suffix="task",
                    action=ECO_TASK_MUTATION_ACTION,
                    resource_refs=resources,
                ),
            )
            result = repository.query(
                TaskQuery(
                    workspace_ref=workspace_ref,
                    view=TaskView.inbox,
                    as_of="2026-08-20T12:00:00Z",
                )
            )
            if tuple(item.task_ref for item in result.tasks) != (task.task_ref,):
                failures.append("ECO-002 canonical Inbox query mismatch")
            binding = result.tasks[0].mission_binding if result.tasks else None
            if binding is None or binding.mission_execution_state_owned_by_tasks:
                failures.append("ECO-002 mission ownership boundary mismatch")
            if private_marker.encode() in database_path.read_bytes():
                failures.append("private Task marker leaked into SQLite data plane")
    except Exception as exc:
        failures.append(f"ECO-002 smoke verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: ECO-002 canonical Tasks and mission ownership verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
