#!/usr/bin/env python3
"""Verify the bounded ECO-007 Inbox and source-artifact workbench."""

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
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.inbox import (
    ECO_INBOX_MUTATION_ACTION,
    InboxArtifactKind,
    InboxProposalKind,
    InboxRepository,
    InboxSourceBinding,
    InboxSourceMode,
    InboxSourceProposal,
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
INBOX_SOURCE = "src/ultimate_ai_agent/core/ecosystem/inbox.py"
REQUIRED_FILES = (
    INBOX_SOURCE,
    "tests/test_eco_007_inbox.py",
    "docs/architecture/ECO_007_INBOX_SOURCE_ARTIFACT_WORKBENCH.md",
    "docs/decisions/ADR-0069-inbox-source-artifact-workbench.md",
)
PROHIBITED_RUNTIME_IMPORTS = (
    "http.client",
    "httpx",
    "playwright",
    "requests",
    "selenium",
    "subprocess",
    "urllib.request",
    "urllib3",
)
DENIED_SOURCE_FRAGMENTS = (
    "account_auth_enabled: Literal[True]",
    "background_sync_enabled: Literal[True]",
    "connector_read_enabled: Literal[True]",
    "external_write_enabled: Literal[True]",
    "model_call_performed: Literal[True]",
    "mutation_authorized: Literal[True]",
    "target_write_performed: Literal[True]",
)


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value, aliases)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _prohibited_match(name: str) -> str | None:
    for prohibited in PROHIBITED_RUNTIME_IMPORTS:
        if name == prohibited or name.startswith(f"{prohibited}."):
            return prohibited
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
                if prohibited := _prohibited_match(item.name):
                    findings.add(prohibited)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for item in node.names:
                qualified = f"{node.module}.{item.name}"
                aliases[item.asname or item.name] = qualified
                if prohibited := _prohibited_match(qualified):
                    findings.add(prohibited)
            if prohibited := _prohibited_match(node.module):
                findings.add(prohibited)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.Attribute)):
            continue
        if isinstance(node, ast.Call):
            callee = _qualified_name(node.func, aliases)
            if callee in {"importlib.import_module", "__import__"} and node.args:
                argument = node.args[0]
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    if prohibited := _prohibited_match(argument.value):
                        findings.add(prohibited)
        target = node.func if isinstance(node, ast.Call) else node
        qualified = _qualified_name(target, aliases)
        if qualified is not None:
            if prohibited := _prohibited_match(qualified):
                findings.add(prohibited)
    return tuple(sorted(findings))


def _approval(
    authority: LocalApprovalAuthority,
    *,
    action: str,
    resources: tuple[str, ...],
    suffix: str,
):
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco007_verifier_{suffix}",
        run_id="run_eco_007_verifier",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco007_verifier_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco007_verifier",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-007 repository mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-007-verifier",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=5),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval_eco007_verifier_{suffix}",
    )
    return request.to_validation_request(grant.approval_ref)


def _operational_failures() -> list[str]:
    failures: list[str] = []
    with TemporaryDirectory(prefix="uaa-eco-007-") as temporary_directory:
        database_path = Path(temporary_directory).resolve() / "ecosystem.sqlite3"
        authority = LocalApprovalAuthority()
        platform = EcosystemLocalDataPlatform(
            database_path=database_path,
            crypto_backend=InMemoryLocalDataCryptoBackend(),
            approval_authority=authority,
            path_resolver=InMemoryLocalDataPathResolver(),
        )
        workspace_ref = "workspace-ref:eco-007-verifier"
        key_ref = "key-version-ref:eco-007-verifier"
        platform.create_workspace(
            workspace_ref=workspace_ref,
            key_version_ref=key_ref,
            approval=_approval(
                authority,
                action="ecosystem.local_data.create_workspace",
                resources=(workspace_ref, key_ref),
                suffix="workspace",
            ),
        )
        repository = InboxRepository(platform)
        binding = InboxSourceBinding(
            workspace_ref=workspace_ref,
            binding_ref="inbox-binding-ref:verifier",
            source_mode=InboxSourceMode.manual,
            source_type_ref="source-type-ref:manual",
            display_name="Private verifier source",
        )
        binding_operation = "operation-ref:eco-007-verifier-binding"
        binding_idempotency = "idempotency-ref:eco-007-verifier-binding"
        binding_resources = repository.mutation_resource_refs(
            workspace_ref=workspace_ref,
            record_ref=binding.binding_ref,
            operation_ref=binding_operation,
            idempotency_ref=binding_idempotency,
        )
        repository.create_binding(
            binding=binding,
            operation_ref=binding_operation,
            idempotency_ref=binding_idempotency,
            approval=_approval(
                authority,
                action=ECO_INBOX_MUTATION_ACTION,
                resources=binding_resources,
                suffix="binding",
            ),
        )
        raw_content = "Reviewed launch checklist artifact."
        prepared = repository.prepare_manual_import(
            workspace_ref=workspace_ref,
            binding_ref=binding.binding_ref,
            artifact_ref="inbox-artifact-ref:verifier",
            artifact_kind=InboxArtifactKind.note,
            title="Private verifier artifact",
            content=raw_content,
            source_locator_ref="source-locator-ref:verifier",
            received_at="2026-08-21T18:00:00Z",
            operation_ref="operation-ref:eco-007-verifier-import",
            idempotency_ref="idempotency-ref:eco-007-verifier-import",
            evidence_refs=("evidence-ref:manual-review",),
        )
        import_approval = _approval(
            authority,
            action=ECO_INBOX_MUTATION_ACTION,
            resources=prepared.plan.approval_resource_refs,
            suffix="import",
        )
        first = repository.commit_import(prepared, approval=import_approval)
        replay = repository.commit_import(prepared, approval=import_approval)
        search = repository.search_artifacts(
            workspace_ref=workspace_ref, query="launch checklist"
        )
        proposal = InboxSourceProposal(
            workspace_ref=workspace_ref,
            proposal_ref="inbox-proposal-ref:verifier",
            binding_ref=binding.binding_ref,
            artifact_ref=prepared.artifact.artifact_ref,
            proposal_kind=InboxProposalKind.task,
            target_owner=CanonicalOwnerId.tasks,
            proposed_target_ref="task-ref:verifier",
            proposal_summary_ref="proposal-summary-ref:verifier",
            evidence_refs=("evidence-ref:manual-review",),
        )
        if (
            first.replayed
            or not replay.replayed
            or first.receipt_ref != replay.receipt_ref
        ):
            failures.append("ECO-007 exact replay posture failed")
        if [item.artifact.artifact_ref for item in search.artifacts] != [
            prepared.artifact.artifact_ref
        ]:
            failures.append("ECO-007 blind-index search failed")
        if raw_content.encode() in database_path.read_bytes():
            failures.append("ECO-007 raw private content reached SQLite")
        if raw_content in prepared.plan.model_dump_json():
            failures.append("ECO-007 raw private content reached import plan")
        if proposal.mutation_authorized or proposal.target_write_performed:
            failures.append("ECO-007 proposal granted downstream mutation authority")
    return failures


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-007 artifact: {relative}")
    source_path = ROOT / INBOX_SOURCE
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for runtime_ref in _forbidden_runtime_refs(source):
        failures.append(f"forbidden ECO-007 runtime ref: {runtime_ref}")
    for fragment in DENIED_SOURCE_FRAGMENTS:
        if fragment in source:
            failures.append(f"denied ECO-007 authority fragment: {fragment}")
    try:
        failures.extend(_operational_failures())
    except Exception as exc:  # pragma: no cover - surfaced as verifier output
        failures.append(
            f"ECO-007 operational verification failed: {type(exc).__name__}"
        )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("ECO-007 Inbox and source-artifact verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
