#!/usr/bin/env python3
"""Verify the bounded ECO-004 standalone local Calendar core."""

from __future__ import annotations

import ast
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MUTATION_ACTION,
    CalendarEvent,
    CalendarRepository,
    CalendarSet,
    LocalCalendar,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
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
    "src/ultimate_ai_agent/core/ecosystem/calendar.py",
    "tests/test_eco_004_calendar.py",
    "docs/architecture/ECO_004_STANDALONE_LOCAL_CALENDAR.md",
    "docs/decisions/ADR-0066-standalone-local-calendar.md",
)
PROHIBITED_RUNTIME_IMPORTS = (
    "http.client",
    "httpx",
    "requests",
    "schedule",
    "subprocess",
    "urllib.request",
    "urllib3",
)


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value, aliases)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _forbidden_runtime_refs(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("invalid-python-source",)
    aliases: dict[str, str] = {}
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".", 1)[0]] = item.name
                if item.name in PROHIBITED_RUNTIME_IMPORTS:
                    findings.add(item.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
            if node.module in PROHIBITED_RUNTIME_IMPORTS:
                findings.add(node.module)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.Attribute)):
            continue
        target = node.func if isinstance(node, ast.Call) else node
        qualified = _qualified_name(target, aliases)
        if qualified is None:
            continue
        for prohibited in PROHIBITED_RUNTIME_IMPORTS:
            if qualified == prohibited or qualified.startswith(f"{prohibited}."):
                findings.add(prohibited)
    return tuple(sorted(findings))


def _approval(
    authority: LocalApprovalAuthority,
    *,
    suffix: str,
    action: str,
    resource_refs: tuple[str, ...],
):
    request = ApprovalRequest(
        approval_request_id=f"approval_request_{suffix}",
        run_id="run_eco_004_verification",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco_004_verifier",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify the bounded ECO-004 Calendar mutation contract.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-004-verifier",
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
            failures.append(f"missing ECO-004 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for runtime_ref in _forbidden_runtime_refs(source):
        failures.append(f"forbidden ECO-004 runtime ref: {runtime_ref}")

    private_marker = "synthetic-private-marker-eco004"
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
            workspace_ref = "workspace-ref:eco-004-verification"
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
            repository = CalendarRepository(platform)
            calendar_set = CalendarSet(
                workspace_ref=workspace_ref,
                calendar_set_ref="calendar-set-ref:eco-004-verification",
                name=private_marker,
                calendars=(
                    LocalCalendar(
                        calendar_ref="calendar-ref:local",
                        name="Local",
                        timezone="America/Los_Angeles",
                    ),
                ),
                events=(
                    CalendarEvent(
                        event_ref="event-ref:local",
                        calendar_ref="calendar-ref:local",
                        title="Local event",
                        starts_at=datetime(
                            2026, 3, 8, 9, tzinfo=ZoneInfo("America/Los_Angeles")
                        ),
                        ends_at=datetime(
                            2026, 3, 8, 10, tzinfo=ZoneInfo("America/Los_Angeles")
                        ),
                        timezone="America/Los_Angeles",
                    ),
                ),
            )
            operation_ref = "operation-ref:eco-004-verification"
            idempotency_ref = "idempotency-ref:eco-004-verification"
            resources = repository.mutation_resource_refs(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operation_ref=operation_ref,
                record_ref=calendar_set.calendar_set_ref,
            )
            repository.create_calendar_set(
                calendar_set=calendar_set,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=_approval(
                    authority,
                    suffix="calendar",
                    action=ECO_CALENDAR_MUTATION_ACTION,
                    resource_refs=resources,
                ),
            )
            if (
                repository.read(
                    workspace_ref=workspace_ref,
                    calendar_set_ref=calendar_set.calendar_set_ref,
                )
                != calendar_set
            ):
                failures.append("ECO-004 canonical Calendar read mismatch")
            if private_marker.encode() in database_path.read_bytes():
                failures.append("private Calendar marker leaked into SQLite data plane")
    except Exception as exc:
        failures.append(f"ECO-004 smoke verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: ECO-004 standalone local Calendar boundary verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
