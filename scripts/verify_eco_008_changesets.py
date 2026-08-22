#!/usr/bin/env python3
"""Verify the bounded ECO-008 EntityLink and local ChangeSet engine."""

from __future__ import annotations

import ast
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MODULE_REF,
    ECO_CALENDAR_RECORD_KIND_REF,
    CalendarSet,
    LocalCalendar,
)
from ultimate_ai_agent.core.ecosystem.changesets import (
    ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
    ChangeSetEngine,
    LocalUpdateIntent,
)
from ultimate_ai_agent.core.ecosystem.contracts import EntityKind, WorkspaceScope
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
)
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MODULE_REF,
    ECO_TASK_RECORD_KIND_REF,
    CanonicalTask,
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
    "src/ultimate_ai_agent/core/ecosystem/changesets.py",
    "tests/test_eco_008_changesets.py",
    "tests/test_eco_008_verifier.py",
    "docs/architecture/ECO_008_ENTITY_LINK_AND_CHANGESET_ENGINE.md",
    "docs/decisions/ADR-0071-entitylink-and-changeset-engine.md",
)
PROHIBITED_IMPORTS = {
    "http.client",
    "httpx",
    "playwright",
    "requests",
    "selenium",
    "subprocess",
    "urllib.request",
    "urllib3",
}
DENIED_FRAGMENTS = (
    "external_execution_performed: Literal[True]",
    "external_write_performed: Literal[True]",
    "unscoped_atomicity_claimed: Literal[True]",
    "claims_external_atomicity=True",
)
WORKSPACE_REF = "workspace-ref:q19-verifier"


class _Approvals:
    def __init__(self) -> None:
        self.authority = LocalApprovalAuthority()
        self.counter = 0

    def grant(self, action: str, resources: tuple[str, ...]):
        self.counter += 1
        request = ApprovalRequest(
            approval_request_id=f"approval_request_q19_verifier_{self.counter}",
            run_id="run_q19_verifier",
            subject_type=ApprovalSubjectType.kernel_task,
            subject_id=f"subject_q19_verifier_{self.counter}",
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="actor_q19_verifier",
                authority_source=AuthoritySource.foundation_test,
            ),
            requested_action=action,
            purpose="Verify the bounded ECO-008 local contract.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.user_private,
                source="source-ref:q19-verifier",
                requires_redaction=True,
            ),
            resource_refs=list(resources),
            expires_at=utc_now() + timedelta(minutes=10),
        )
        self.authority.create_request(request)
        grant = self.authority.create_test_grant(
            request.approval_request_id,
            approval_ref=f"approval_q19_verifier_{self.counter}",
        )
        return request.to_validation_request(grant.approval_ref)


def _prohibited_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [
                node.module,
                *(f"{node.module}.{item.name}" for item in node.names),
            ]
        else:
            continue
        for name in names:
            findings.update(
                prohibited
                for prohibited in PROHIBITED_IMPORTS
                if name == prohibited or name.startswith(f"{prohibited}.")
            )
    return findings


def _seed(
    platform: EcosystemLocalDataPlatform,
    approvals: _Approvals,
    *,
    operation: PutRecord,
    action: str,
    idempotency_ref: str,
) -> None:
    resources = (
        WORKSPACE_REF,
        idempotency_ref,
        operation.operation_ref,
        operation.record_ref,
    )
    platform._apply_registered_domain(
        workspace_ref=WORKSPACE_REF,
        idempotency_ref=idempotency_ref,
        operations=(operation,),
        approval=approvals.grant(action, resources),
        requested_action=action,
        request_context_ref=f"request-context-ref:{operation.operation_ref}",
    )


def _operational_failures() -> list[str]:
    failures: list[str] = []
    with TemporaryDirectory(prefix="uaa-q19-") as temporary_directory:
        approvals = _Approvals()
        platform = EcosystemLocalDataPlatform(
            database_path=(Path(temporary_directory) / "ecosystem.sqlite3").resolve(),
            crypto_backend=InMemoryLocalDataCryptoBackend(),
            approval_authority=approvals.authority,
            path_resolver=InMemoryLocalDataPathResolver(),
        )
        key_version = "key-version-ref:v1"
        platform.create_workspace(
            workspace_ref=WORKSPACE_REF,
            key_version_ref=key_version,
            approval=approvals.grant(
                "ecosystem.local_data.create_workspace",
                (WORKSPACE_REF, key_version),
            ),
        )
        task = CanonicalTask(
            workspace_ref=WORKSPACE_REF,
            task_ref="task-ref:q19-verifier",
            title="Synthetic verifier task",
        )
        calendar = CalendarSet(
            workspace_ref=WORKSPACE_REF,
            calendar_set_ref="calendar-set-ref:q19-verifier",
            name="Synthetic verifier calendar",
            calendars=(
                LocalCalendar(
                    calendar_ref="calendar-ref:q19-verifier",
                    name="Primary",
                ),
            ),
        )
        _seed(
            platform,
            approvals,
            operation=PutRecord(
                operation_ref="operation-ref:q19-verifier-seed-task",
                module_ref=ECO_TASK_MODULE_REF,
                record_ref=task.task_ref,
                record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                safe_summary_ref=task.safe_summary_ref,
                private_payload=task.model_dump(mode="json"),
                search_terms=("entity-kind:canonical-task", "task-status:inbox"),
                retention_ref="retention-ref:tasks-operator-managed",
            ),
            action="ecosystem.tasks.apply",
            idempotency_ref="idempotency-ref:q19-verifier-seed-task",
        )
        _seed(
            platform,
            approvals,
            operation=PutRecord(
                operation_ref="operation-ref:q19-verifier-seed-calendar",
                module_ref=ECO_CALENDAR_MODULE_REF,
                record_ref=calendar.calendar_set_ref,
                record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
                safe_summary_ref=calendar.safe_summary_ref,
                private_payload=calendar.model_dump(mode="json"),
                search_terms=("entity-kind:calendar-set",),
                retention_ref="retention-ref:calendar-operator-managed",
            ),
            action="ecosystem.calendar.apply",
            idempotency_ref="idempotency-ref:q19-verifier-seed-calendar",
        )
        updated_task = task.model_copy(
            update={"title": "Updated verifier task", "version": 2}
        )
        updated_calendar = calendar.model_copy(
            update={"name": "Updated verifier calendar", "version": 2}
        )
        engine = ChangeSetEngine(platform)
        prepared = engine.prepare_local(
            workspace=WorkspaceScope(workspace_ref=WORKSPACE_REF),
            change_set_ref="change-set-ref:q19-verifier",
            intents=(
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-verifier-task",
                    record_ref=task.task_ref,
                    entity_kind=EntityKind.task,
                    module_ref=ECO_TASK_MODULE_REF,
                    record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-verifier-task",
                    replacement_payload=updated_task.model_dump(mode="json"),
                    search_terms=(
                        "entity-kind:canonical-task",
                        "task-status:inbox",
                    ),
                    retention_ref="retention-ref:tasks-operator-managed",
                ),
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-verifier-calendar",
                    record_ref=calendar.calendar_set_ref,
                    entity_kind=EntityKind.calendar_set,
                    module_ref=ECO_CALENDAR_MODULE_REF,
                    record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-verifier-calendar",
                    replacement_payload=updated_calendar.model_dump(mode="json"),
                    search_terms=("entity-kind:calendar-set",),
                    retention_ref="retention-ref:calendar-operator-managed",
                    depends_on=("operation-ref:q19-verifier-task",),
                ),
            ),
            approval_scope_ref="approval-scope-ref:q19-verifier",
            idempotency_ref="idempotency-ref:q19-verifier",
            expiry_ref="expiry-ref:q19-verifier",
            predicted_result_ref="predicted-result-ref:q19-verifier",
        )
        resources = engine.mutation_resource_refs(
            prepared, idempotency_ref=prepared.plan.idempotency_ref
        )
        receipt = engine.apply_local(
            prepared,
            idempotency_ref=prepared.plan.idempotency_ref,
            approval=approvals.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
        )
        if (
            receipt.external_write_performed
            or receipt.unscoped_atomicity_claimed
            or len(receipt.operation_results) != 2
            or not all(not item.raw_value_included for item in prepared.field_diffs)
        ):
            failures.append("ECO-008 local receipt or diff posture invalid")
        undo = engine.prepare_undo(
            workspace_ref=WORKSPACE_REF,
            change_set_ref=prepared.plan.change_set_ref,
        )
        undo_idempotency = "idempotency-ref:q19-verifier-rollback"
        undo_resources = engine.mutation_resource_refs(
            undo, idempotency_ref=undo_idempotency
        )
        engine.rollback(
            undo,
            idempotency_ref=undo_idempotency,
            approval=approvals.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, undo_resources),
        )
        restored = CanonicalTask.model_validate(
            platform.read(
                workspace_ref=WORKSPACE_REF, record_ref=task.task_ref
            ).private_payload
        )
        if restored.title != task.title or restored.version != 3:
            failures.append("ECO-008 exact rollback did not restore Task truth")
    return failures


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-008 artifact: {relative}")
    source_path = ROOT / "src/ultimate_ai_agent/core/ecosystem/changesets.py"
    if source_path.is_file():
        source = source_path.read_text(encoding="utf-8")
        for prohibited in sorted(_prohibited_imports(source_path)):
            failures.append(f"forbidden ECO-008 runtime import: {prohibited}")
        for fragment in DENIED_FRAGMENTS:
            if fragment in source:
                failures.append(f"denied ECO-008 authority fragment: {fragment}")
    try:
        failures.extend(_operational_failures())
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        failures.append(
            f"ECO-008 operational verification failed: {type(exc).__name__}"
        )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("ECO-008 EntityLink and ChangeSet verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
