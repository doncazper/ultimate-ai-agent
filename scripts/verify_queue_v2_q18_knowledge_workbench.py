#!/usr/bin/env python3
"""Verify Q18 Knowledge Workbench lifecycle and cited-context hardening."""

from __future__ import annotations

import ast
from pathlib import Path
from tempfile import TemporaryDirectory

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.knowledge_dump import (
    KnowledgeDumpStore,
    KnowledgeLifecycleState,
    KnowledgeOcrReviewStatus,
    KnowledgeRightsBasis,
    KnowledgeRightsStatus,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/knowledge_dump/models.py",
    "src/ultimate_ai_agent/core/knowledge_dump/store.py",
    "scripts/dev/uaa_knowledge.py",
    "tests/test_knowledge_workbench_hardening.py",
    "tests/test_knowledge_workbench_verifier.py",
    "docs/architecture/Q18_KNOWLEDGE_WORKBENCH_HARDENING.md",
    "docs/decisions/ADR-0070-knowledge-workbench-hardening.md",
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
    "application_level_encryption_enabled: bool = True",
    "automatic_chat_injection_performed: bool = True",
    "model_training_authorized: bool = True",
    "network_storage_authorized: bool = True",
    "runtime_volume_encryption_verified: bool = True",
)


def _actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="q18_verifier_operator",
        authority_source=AuthoritySource.foundation_test,
    )


def _approved(store: KnowledgeDumpStore, prepared, operation: str):  # type: ignore[no-untyped-def]
    actor = _actor()
    authority = LocalApprovalAuthority()
    request = getattr(store, f"approval_request_for_{operation}")(
        prepared,
        actor_context=actor,
        run_id=f"run:q18-verifier:{operation}",
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval:q18-verifier:{operation}",
    )
    return actor, authority, grant.approval_ref


def _prohibited_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            findings.update(
                prohibited
                for prohibited in PROHIBITED_IMPORTS
                if name == prohibited or name.startswith(f"{prohibited}.")
            )
    return findings


def _operational_failures() -> list[str]:
    failures: list[str] = []
    with TemporaryDirectory(prefix="uaa-q18-") as temporary_directory:
        root = Path(temporary_directory)
        source = root / "source.md"
        raw_content = "Synthetic Q18 cited lifecycle source."
        source.write_text(raw_content, encoding="utf-8")
        store = KnowledgeDumpStore(root / "dump")
        prepared = store.prepare_ingest(
            source,
            title="Synthetic Q18 source",
            rights_basis=KnowledgeRightsBasis.operator_authored,
            rights_evidence_ref="rights-evidence-ref:q18-verifier",
            idempotency_key="knowledge-q18-verifier-ingest",
        )
        actor, authority, approval_ref = _approved(store, prepared, "ingest")
        receipt = store.ingest(
            prepared,
            approval_authority=authority,
            approval_ref=approval_ref,
            actor_context=actor,
            run_id="run:q18-verifier:ingest",
        )
        pack = store.prepare_selected_context([prepared.chunks[0].chunk_ref])
        posture = store.encryption_posture()
        if (
            pack.selection_mode != "operator_selected"
            or pack.selected_chunk_refs != (prepared.chunks[0].chunk_ref,)
            or pack.hits[0].citation.chunk_ref != prepared.chunks[0].chunk_ref
            or pack.uncited_content_included
            or pack.model_training_authorized
        ):
            failures.append("Q18 explicit cited-context binding failed")
        if (
            posture.application_level_encryption_enabled
            or not posture.plaintext_source_content_at_rest
            or not posture.operator_controlled_encrypted_volume_required
        ):
            failures.append("Q18 encryption posture overclaimed protection")
        if raw_content in prepared.plan.model_dump_json():
            failures.append("Q18 raw source content reached the ingest plan")
        governance = store.prepare_governance_update(
            receipt.document_ref,
            lifecycle_state=KnowledgeLifecycleState.archived,
            rights_status=KnowledgeRightsStatus.current,
            rights_evidence_ref="rights-evidence-ref:q18-verifier",
            ocr_review_status=KnowledgeOcrReviewStatus.not_required,
            ocr_review_evidence_ref=None,
            idempotency_key="knowledge-q18-verifier-archive",
        )
        actor, authority, approval_ref = _approved(
            store, governance, "governance_update"
        )
        store.update_governance(
            governance,
            approval_authority=authority,
            approval_ref=approval_ref,
            actor_context=actor,
            run_id="run:q18-verifier:governance_update",
        )
        if store.search("lifecycle source"):
            failures.append("Q18 archived source remained retrieval eligible")
        try:
            store.prepare_selected_context([prepared.chunks[0].chunk_ref])
        except ValueError as exc:
            if str(exc) != "KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE":
                failures.append("Q18 ineligible context used an unsafe error")
        else:
            failures.append("Q18 archived selected context did not fail closed")
    return failures


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing Q18 artifact: {relative}")
    for relative in (
        "src/ultimate_ai_agent/core/knowledge_dump/models.py",
        "src/ultimate_ai_agent/core/knowledge_dump/store.py",
    ):
        path = ROOT / relative
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        for prohibited in sorted(_prohibited_imports(path)):
            failures.append(f"forbidden Q18 runtime import: {prohibited}")
        for fragment in DENIED_FRAGMENTS:
            if fragment in source:
                failures.append(f"denied Q18 authority fragment: {fragment}")
    try:
        failures.extend(_operational_failures())
    except Exception as exc:  # pragma: no cover - surfaced as bounded verifier output
        failures.append(f"Q18 operational verification failed: {type(exc).__name__}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q18 Knowledge Workbench hardening verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
