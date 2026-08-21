#!/usr/bin/env python3
"""Verify the bounded ECO-005 first-class private CRM foundation."""

from __future__ import annotations

import ast
import tempfile
from datetime import timedelta
from pathlib import Path

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.crm.private_repository import (
    ECO_CRM_MUTATION_ACTION,
    PrivateCrmPortfolio,
    PrivateCrmRepository,
)
from ultimate_ai_agent.core.ecosystem.boards import BoardRepository
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
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.time import utc_now


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/crm/private_repository.py",
    "tests/test_eco_005_private_crm.py",
    "docs/architecture/ECO_005_FIRST_CLASS_PRIVATE_CRM.md",
    "docs/decisions/ADR-0067-first-class-private-crm.md",
)
PROHIBITED_RUNTIME_IMPORTS = (
    "http.client",
    "httpx",
    "requests",
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
    resources: tuple[str, ...],
):
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco005_verify_{suffix}",
        run_id="run_eco_005_verification",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco005_verify_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco005_verifier",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify the bounded ECO-005 private CRM contract.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-005-verifier",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=5),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id, approval_ref=f"approval_eco005_verify_{suffix}"
    )
    return request.to_validation_request(grant.approval_ref)


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-005 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for runtime_ref in _forbidden_runtime_refs(source):
        failures.append(f"forbidden ECO-005 runtime ref: {runtime_ref}")

    private_marker = "synthetic-private-marker-eco005"
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
            workspace_ref = "workspace-ref:eco-005-verification"
            key_ref = "key-version-ref:v1"
            platform.create_workspace(
                workspace_ref=workspace_ref,
                key_version_ref=key_ref,
                approval=_approval(
                    authority,
                    suffix="workspace",
                    action="ecosystem.local_data.create_workspace",
                    resources=(workspace_ref, key_ref),
                ),
            )
            repository = PrivateCrmRepository(
                platform, board_repository=BoardRepository(platform)
            )
            portfolio_ref = "crm-portfolio-ref:verification"
            operation_ref = "operation-ref:create-portfolio"
            idempotency_ref = "idempotency-ref:create-portfolio"
            approval = _approval(
                authority,
                suffix="portfolio",
                action=ECO_CRM_MUTATION_ACTION,
                resources=PrivateCrmRepository.mutation_resource_refs(
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    operation_ref=operation_ref,
                    record_ref=portfolio_ref,
                ),
            )
            portfolio = PrivateCrmPortfolio(
                workspace_ref=workspace_ref,
                portfolio_ref=portfolio_ref,
                name=private_marker,
            )
            first = repository.create_portfolio(
                portfolio=portfolio,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
            )
            replay = repository.create_portfolio(
                portfolio=portfolio,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
                approval=approval,
            )
            if not replay.replayed or replay.receipt_ref != first.receipt_ref:
                failures.append("ECO-005 exact replay verification failed")
            if repository.read(
                workspace_ref=workspace_ref, portfolio_ref=portfolio_ref
            ).name != private_marker:
                failures.append("ECO-005 private CRM readback failed")
            if private_marker.encode("utf-8") in database_path.read_bytes():
                failures.append("ECO-005 private marker persisted as plaintext")
    except Exception as exc:  # pragma: no cover - surfaced as verifier output
        failures.append(f"ECO-005 operational verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("ECO-005 first-class private CRM verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
