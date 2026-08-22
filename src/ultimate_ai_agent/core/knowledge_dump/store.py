from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
from typing import Iterable, Iterator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel as CapabilityRiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.knowledge_dump.extractors import (
    ExtractedSection,
    MAX_SOURCE_BYTES,
    detect_format,
    extract_sections,
)
from ultimate_ai_agent.core.knowledge_dump.models import (
    KNOWLEDGE_DUMP_CONTRACT_REF,
    KnowledgeAuditRecord,
    KnowledgeCitation,
    KnowledgeContextPack,
    KnowledgeDocument,
    KnowledgeEncryptionPosture,
    KnowledgeExtractionMethod,
    KnowledgeGovernanceUpdatePlan,
    KnowledgeGovernanceUpdateReceipt,
    KnowledgeHit,
    KnowledgeIngestPlan,
    KnowledgeIngestReceipt,
    KnowledgeInventory,
    KnowledgeLifecycleState,
    KnowledgeMetadataUpdatePlan,
    KnowledgeMetadataUpdateReceipt,
    KnowledgeOcrReviewStatus,
    KnowledgeRemovalPlan,
    KnowledgeRemovalReceipt,
    KnowledgeRightsBasis,
    KnowledgeRightsStatus,
    KnowledgeSourceKind,
)
from ultimate_ai_agent.core.medical_knowledge import (
    MedicalSourceAccessClass,
    get_medical_knowledge_source,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


MAX_CHUNK_CHARACTERS = 1_800
CHUNK_OVERLAP_CHARACTERS = 180
MAX_QUERY_CHARACTERS = 500
_TOKEN_RE = re.compile(r"[^\W_][\w-]*", re.UNICODE)


def _hash_ref(prefix: str, value: str | bytes, length: int = 24) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return f"{prefix}:sha256:{hashlib.sha256(raw).hexdigest()[:length]}"


@dataclass(frozen=True)
class _PreparedChunk:
    chunk_ref: str
    locator: str
    text: str
    text_ref: str


@dataclass(frozen=True)
class PreparedKnowledgeIngest:
    """Ephemeral source payload plus its persistable, content-free plan."""

    plan: KnowledgeIngestPlan
    chunks: tuple[_PreparedChunk, ...]


@dataclass(frozen=True)
class PreparedKnowledgeMetadataUpdate:
    plan: KnowledgeMetadataUpdatePlan


@dataclass(frozen=True)
class PreparedKnowledgeGovernanceUpdate:
    plan: KnowledgeGovernanceUpdatePlan


@dataclass(frozen=True)
class PreparedKnowledgeRemoval:
    plan: KnowledgeRemovalPlan


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _chunk_manifest_ref(chunks: tuple[_PreparedChunk, ...]) -> str:
    manifest = [
        {
            "chunk_ref": chunk.chunk_ref,
            "character_count": len(chunk.text),
            "locator": chunk.locator,
            "ordinal": ordinal,
            "text_ref": chunk.text_ref,
        }
        for ordinal, chunk in enumerate(chunks)
    ]
    return _hash_ref(
        "knowledge-chunk-manifest-ref",
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
        40,
    )


def _ingest_scope_ref(plan: KnowledgeIngestPlan) -> str:
    material = {
        "catalog_citation_locator_refs": list(plan.catalog_citation_locator_refs),
        "catalog_source_id": plan.catalog_source_id,
        "category": plan.category,
        "chunk_manifest_ref": plan.chunk_manifest_ref,
        "collection": plan.collection,
        "idempotency_key": plan.idempotency_key,
        "extraction_method": _enum_value(plan.extraction_method),
        "ocr_review_evidence_ref": plan.ocr_review_evidence_ref,
        "ocr_review_status": _enum_value(plan.ocr_review_status),
        "planned_character_count": plan.planned_character_count,
        "planned_chunk_count": plan.planned_chunk_count,
        "rights_basis": _enum_value(plan.rights_basis),
        "rights_evidence_ref": plan.rights_evidence_ref,
        "rights_status": _enum_value(plan.rights_status),
        "source_content_ref": plan.source_content_ref,
        "source_format": _enum_value(plan.source_format),
        "source_kind": _enum_value(plan.source_kind),
        "source_size_bytes": plan.source_size_bytes,
        "store_ref": plan.store_ref,
        "tags": sorted(plan.tags),
        "title": plan.title,
    }
    return _hash_ref(
        "knowledge-ingest-scope-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _legacy_ingest_scope_ref(plan: KnowledgeIngestPlan) -> str:
    """Reconstruct the v1 scope so pre-v2 successful ingests remain replayable."""

    material = {
        "catalog_citation_locator_refs": list(plan.catalog_citation_locator_refs),
        "catalog_source_id": plan.catalog_source_id,
        "category": plan.category,
        "chunk_manifest_ref": plan.chunk_manifest_ref,
        "collection": plan.collection,
        "idempotency_key": plan.idempotency_key,
        "planned_character_count": plan.planned_character_count,
        "planned_chunk_count": plan.planned_chunk_count,
        "rights_basis": _enum_value(plan.rights_basis),
        "rights_evidence_ref": plan.rights_evidence_ref,
        "source_content_ref": plan.source_content_ref,
        "source_format": _enum_value(plan.source_format),
        "source_kind": _enum_value(plan.source_kind),
        "source_size_bytes": plan.source_size_bytes,
        "store_ref": plan.store_ref,
        "tags": sorted(plan.tags),
        "title": plan.title,
    }
    return _hash_ref(
        "knowledge-ingest-scope-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _metadata_ref(
    source_kind: object,
    category: str,
    collection: str | None,
    tags: list[str],
) -> str:
    material = {
        "category": category,
        "collection": collection,
        "source_kind": _enum_value(source_kind),
        "tags": sorted(tags),
    }
    return _hash_ref(
        "knowledge-metadata-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _metadata_scope_ref(plan: KnowledgeMetadataUpdatePlan) -> str:
    material = {
        "category": plan.category,
        "collection": plan.collection,
        "document_ref": plan.document_ref,
        "expected_metadata_ref": plan.expected_metadata_ref,
        "idempotency_key": plan.idempotency_key,
        "source_kind": _enum_value(plan.source_kind),
        "store_ref": plan.store_ref,
        "tags": sorted(plan.tags),
    }
    return _hash_ref(
        "knowledge-metadata-scope-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _governance_ref(
    *,
    lifecycle_state: object,
    rights_status: object,
    rights_evidence_ref: str,
    extraction_method: object,
    ocr_review_status: object,
    ocr_review_evidence_ref: str | None,
) -> str:
    material = {
        "extraction_method": _enum_value(extraction_method),
        "lifecycle_state": _enum_value(lifecycle_state),
        "ocr_review_evidence_ref": ocr_review_evidence_ref,
        "ocr_review_status": _enum_value(ocr_review_status),
        "rights_evidence_ref": rights_evidence_ref,
        "rights_status": _enum_value(rights_status),
    }
    return _hash_ref(
        "knowledge-governance-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _governance_scope_ref(plan: KnowledgeGovernanceUpdatePlan) -> str:
    material = {
        "document_ref": plan.document_ref,
        "expected_governance_ref": plan.expected_governance_ref,
        "extraction_method": _enum_value(plan.extraction_method),
        "idempotency_key": plan.idempotency_key,
        "lifecycle_state": _enum_value(plan.lifecycle_state),
        "ocr_review_evidence_ref": plan.ocr_review_evidence_ref,
        "ocr_review_status": _enum_value(plan.ocr_review_status),
        "rights_evidence_ref": plan.rights_evidence_ref,
        "rights_status": _enum_value(plan.rights_status),
        "store_ref": plan.store_ref,
    }
    return _hash_ref(
        "knowledge-governance-scope-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


def _removal_scope_ref(plan: KnowledgeRemovalPlan) -> str:
    material = {
        "backup_disposition_ref": plan.backup_disposition_ref,
        "document_ref": plan.document_ref,
        "expected_document_revision_ref": plan.expected_document_revision_ref,
        "idempotency_key": plan.idempotency_key,
        "planned_character_count": plan.planned_character_count,
        "planned_chunk_count": plan.planned_chunk_count,
        "retention_decision_ref": plan.retention_decision_ref,
        "store_ref": plan.store_ref,
    }
    return _hash_ref(
        "knowledge-removal-scope-ref",
        json.dumps(material, sort_keys=True, separators=(",", ":")),
    )


class KnowledgeDumpStore:
    """SQLite-backed local corpus with exact approval and cited lexical retrieval."""

    def __init__(
        self,
        root: str | Path,
        *,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.database_path = self.root / "knowledge.sqlite3"
        self.policy_engine = policy_engine or PolicyEngine(
            default_max_risk=CapabilityRiskLevel.high
        )

    @property
    def store_ref(self) -> str:
        return _hash_ref("knowledge-store-ref", str(self.root))

    def prepare_ingest(
        self,
        source_path: str | Path,
        *,
        title: str,
        rights_basis: KnowledgeRightsBasis,
        rights_evidence_ref: str,
        idempotency_key: str,
        catalog_source_id: str | None = None,
        catalog_citation_locator_refs: list[str] | None = None,
        source_kind: KnowledgeSourceKind = KnowledgeSourceKind.reference,
        category: str = "uncategorized",
        collection: str | None = None,
        tags: list[str] | None = None,
        extraction_method: KnowledgeExtractionMethod = KnowledgeExtractionMethod.native_text,
        ocr_review_status: KnowledgeOcrReviewStatus = KnowledgeOcrReviewStatus.not_required,
        ocr_review_evidence_ref: str | None = None,
    ) -> PreparedKnowledgeIngest:
        path = Path(source_path).expanduser().resolve()
        if not title.strip():
            raise ValueError("KNOWLEDGE_TITLE_REQUIRED")
        if contains_obvious_secret({"title": title}):
            raise ValueError("KNOWLEDGE_TITLE_SECRET_LIKE")
        if contains_obvious_secret({"rights_evidence_ref": rights_evidence_ref}):
            raise ValueError("KNOWLEDGE_RIGHTS_EVIDENCE_REF_SECRET_LIKE")
        if contains_obvious_secret({"idempotency_key": idempotency_key}):
            raise ValueError("KNOWLEDGE_IDEMPOTENCY_KEY_SECRET_LIKE")
        if ocr_review_evidence_ref and contains_obvious_secret(
            {"ocr_review_evidence_ref": ocr_review_evidence_ref}
        ):
            raise ValueError("KNOWLEDGE_OCR_EVIDENCE_REF_SECRET_LIKE")
        if catalog_source_id and not re.fullmatch(
            r"[a-z][a-z0-9_]{2,80}", catalog_source_id
        ):
            raise ValueError("KNOWLEDGE_CATALOG_SOURCE_ID_INVALID")
        source_format = detect_format(path)
        if not path.is_file():
            raise ValueError("KNOWLEDGE_SOURCE_FILE_REQUIRED")
        source_size = path.stat().st_size
        if source_size <= 0 or source_size > MAX_SOURCE_BYTES:
            raise ValueError("KNOWLEDGE_SOURCE_SIZE_OUT_OF_BOUNDS")
        source_bytes = path.read_bytes()
        if len(source_bytes) != source_size:
            raise ValueError("KNOWLEDGE_SOURCE_CHANGED_DURING_PREPARATION")
        sections = extract_sections(path, source_format)
        if path.read_bytes() != source_bytes:
            raise ValueError("KNOWLEDGE_SOURCE_CHANGED_DURING_PREPARATION")
        if any(
            contains_obvious_secret({"content": section.text}) for section in sections
        ):
            raise ValueError("KNOWLEDGE_SOURCE_CONTAINS_SECRET_LIKE_CONTENT")
        locator_refs = tuple(catalog_citation_locator_refs or ())
        self._validate_catalog_binding(
            catalog_source_id=catalog_source_id,
            catalog_citation_locator_refs=locator_refs,
            rights_basis=rights_basis,
        )
        source_content_ref = _hash_ref("knowledge-content-ref", source_bytes, 40)
        chunks = tuple(self._chunk_sections(source_content_ref, sections))
        character_count = sum(len(chunk.text) for chunk in chunks)
        plan = KnowledgeIngestPlan(
            plan_ref="knowledge-ingest-plan-ref:pending",
            exact_scope_ref="knowledge-ingest-scope-ref:pending",
            source_content_ref=source_content_ref,
            chunk_manifest_ref=_chunk_manifest_ref(chunks),
            store_ref=self.store_ref,
            title=title.strip(),
            source_format=source_format,
            source_size_bytes=source_size,
            rights_basis=rights_basis,
            rights_evidence_ref=rights_evidence_ref,
            rights_status=KnowledgeRightsStatus.current,
            extraction_method=extraction_method,
            ocr_review_status=ocr_review_status,
            ocr_review_evidence_ref=ocr_review_evidence_ref,
            catalog_source_id=catalog_source_id,
            catalog_citation_locator_refs=locator_refs,
            source_kind=source_kind,
            category=category,
            collection=collection,
            tags=tags or [],
            planned_chunk_count=len(chunks),
            planned_character_count=character_count,
            idempotency_key=idempotency_key,
            rollback_ref=_hash_ref("knowledge-rollback-ref", source_content_ref),
        )
        exact_scope_ref = _ingest_scope_ref(plan)
        plan = plan.model_copy(
            update={
                "exact_scope_ref": exact_scope_ref,
                "plan_ref": _hash_ref("knowledge-ingest-plan-ref", exact_scope_ref),
            }
        )
        return PreparedKnowledgeIngest(plan=plan, chunks=chunks)

    def approval_request_for_ingest(
        self,
        prepared: PreparedKnowledgeIngest,
        *,
        actor_context: ActorContext,
        run_id: str,
    ) -> ApprovalRequest:
        self._validate_prepared_ingest(prepared)
        plan = prepared.plan
        return ApprovalRequest(
            approval_request_id=_hash_ref(
                "knowledge-approval-request", plan.exact_scope_ref
            ),
            run_id=run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=plan.plan_ref,
            actor_context=actor_context,
            requested_action="knowledge_dump.ingest",
            purpose="Persist exact rights-attested source chunks in the local Knowledge Dump.",
            risk_level=ApprovalRiskLevel.medium,
            data_classification=DataClassification(
                classification=ClassificationValue.third_party_confidential,
                source="local_operator_knowledge_ingest",
                reason="Operator-supplied source content remains local and rights-gated.",
                allowed_sinks=["local_knowledge_dump", "explicit_context_pack"],
                forbidden_sinks=[
                    "network",
                    "provider",
                    "model_training",
                    "logs",
                    "receipts",
                ],
                requires_consent=True,
                retention_policy="until_exact_approved_removal",
            ),
            resource_refs=[
                plan.exact_scope_ref,
                plan.source_content_ref,
                plan.chunk_manifest_ref,
                plan.store_ref,
                plan.rights_evidence_ref,
                *(
                    [plan.ocr_review_evidence_ref]
                    if plan.ocr_review_evidence_ref is not None
                    else []
                ),
            ],
            consent_refs=[
                plan.rights_evidence_ref,
                *(
                    [plan.ocr_review_evidence_ref]
                    if plan.ocr_review_evidence_ref is not None
                    else []
                ),
            ],
            trace_id=plan.plan_ref,
        )

    def ingest(
        self,
        prepared: PreparedKnowledgeIngest,
        *,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeIngestReceipt:
        if contains_obvious_secret({"approval_ref": approval_ref}):
            raise ValueError("KNOWLEDGE_APPROVAL_REF_SECRET_LIKE")
        request = self.approval_request_for_ingest(
            prepared, actor_context=actor_context, run_id=run_id
        )
        self._require_mutation_policy(
            operation="ingest",
            plan_ref=prepared.plan.plan_ref,
            exact_scope_ref=prepared.plan.exact_scope_ref,
            idempotency_key=prepared.plan.idempotency_key,
        )
        with approval_authority.hold_validation_lock():
            decision = approval_authority.validate_for_request(request, approval_ref)
            if not decision.allowed:
                raise PermissionError("KNOWLEDGE_INGEST_EXACT_APPROVAL_REQUIRED")
            grant = approval_authority.get_grant(approval_ref)
            if grant is None:
                raise PermissionError("KNOWLEDGE_INGEST_EXACT_APPROVAL_REQUIRED")
            return self._persist_approved_ingest(
                prepared,
                approval_ref=approval_ref,
                approver_actor_id=grant.approved_by_actor_id,
                actor_context=actor_context,
                run_id=run_id,
            )

    def _persist_approved_ingest(
        self,
        prepared: PreparedKnowledgeIngest,
        *,
        approval_ref: str,
        approver_actor_id: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeIngestReceipt:
        self._initialize()
        plan = prepared.plan
        document_ref = _hash_ref("knowledge-document-ref", plan.source_content_ref)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_prepared_ingest(prepared)
            removed_binding = connection.execute(
                """SELECT document_ref FROM document_removals
                   WHERE source_content_ref = ? OR ingest_idempotency_key = ?""",
                (plan.source_content_ref, plan.idempotency_key),
            ).fetchone()
            if removed_binding is not None:
                raise ValueError(
                    "KNOWLEDGE_REMOVED_CONTENT_REQUIRES_NEW_SOURCE_REVISION"
                )
            existing_by_idempotency = connection.execute(
                """SELECT document_ref, source_content_ref, idempotency_key,
                          exact_scope_ref, rights_basis, rights_evidence_ref,
                          rights_status, extraction_method, ocr_review_status,
                          ocr_review_evidence_ref, chunk_count, character_count
                   FROM documents WHERE idempotency_key = ?""",
                (plan.idempotency_key,),
            ).fetchone()
            existing_by_content = connection.execute(
                """SELECT document_ref, source_content_ref, idempotency_key,
                          exact_scope_ref
                   FROM documents WHERE source_content_ref = ?""",
                (plan.source_content_ref,),
            ).fetchone()
            legacy_scope_ref = _legacy_ingest_scope_ref(plan)
            legacy_replay = False
            if existing_by_idempotency is not None:
                legacy_replay = (
                    existing_by_idempotency["exact_scope_ref"] == legacy_scope_ref
                )
                if existing_by_idempotency[
                    "source_content_ref"
                ] != plan.source_content_ref or (
                    existing_by_idempotency["exact_scope_ref"] != plan.exact_scope_ref
                    and not legacy_replay
                ):
                    raise ValueError("KNOWLEDGE_INGEST_IDEMPOTENCY_CONFLICT")
            if (
                existing_by_content is not None
                and existing_by_content["idempotency_key"] != plan.idempotency_key
            ):
                raise ValueError("KNOWLEDGE_INGEST_CONTENT_ALREADY_BOUND")
            existing = existing_by_idempotency
            mutation_performed = existing is None
            if mutation_performed:
                connection.execute(
                    """INSERT INTO documents
                    (document_ref, source_content_ref, exact_scope_ref, title, source_format, rights_basis,
                     rights_evidence_ref, rights_status, lifecycle_state, extraction_method,
                     ocr_review_status, ocr_review_evidence_ref, catalog_source_id,
                     catalog_citation_locator_refs_json,
                     chunk_count, character_count, idempotency_key, created_at, source_kind,
                     category, collection, tags_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        document_ref,
                        plan.source_content_ref,
                        plan.exact_scope_ref,
                        plan.title,
                        plan.source_format,
                        plan.rights_basis,
                        plan.rights_evidence_ref,
                        plan.rights_status,
                        KnowledgeLifecycleState.active,
                        plan.extraction_method,
                        plan.ocr_review_status,
                        plan.ocr_review_evidence_ref,
                        plan.catalog_source_id,
                        json.dumps(
                            plan.catalog_citation_locator_refs,
                            separators=(",", ":"),
                        ),
                        len(prepared.chunks),
                        plan.planned_character_count,
                        plan.idempotency_key,
                        utc_now().isoformat(),
                        plan.source_kind,
                        plan.category,
                        plan.collection,
                        json.dumps(plan.tags, separators=(",", ":")),
                    ),
                )
                for ordinal, chunk in enumerate(prepared.chunks):
                    connection.execute(
                        "INSERT INTO chunks (chunk_ref, document_ref, ordinal, locator, text, text_ref) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            chunk.chunk_ref,
                            document_ref,
                            ordinal,
                            chunk.locator,
                            chunk.text,
                            chunk.text_ref,
                        ),
                    )
                    connection.execute(
                        "INSERT INTO chunks_fts (chunk_ref, text) VALUES (?, ?)",
                        (chunk.chunk_ref, chunk.text),
                    )
            else:
                document_ref = str(existing["document_ref"])
            receipt_rights_status = (
                existing["rights_status"] if legacy_replay else plan.rights_status
            )
            receipt_extraction_method = (
                existing["extraction_method"]
                if legacy_replay
                else plan.extraction_method
            )
            receipt_ocr_status = (
                existing["ocr_review_status"]
                if legacy_replay
                else plan.ocr_review_status
            )
            receipt = KnowledgeIngestReceipt(
                receipt_ref=_hash_ref(
                    "knowledge-ingest-receipt-ref", f"{plan.plan_ref}|{document_ref}"
                ),
                plan_ref=plan.plan_ref,
                exact_scope_ref=plan.exact_scope_ref,
                document_ref=document_ref,
                source_content_ref=plan.source_content_ref,
                chunk_count=(
                    int(existing["chunk_count"])
                    if legacy_replay
                    else len(prepared.chunks)
                ),
                character_count=(
                    int(existing["character_count"])
                    if legacy_replay
                    else plan.planned_character_count
                ),
                rights_basis=(
                    existing["rights_basis"] if legacy_replay else plan.rights_basis
                ),
                rights_evidence_ref=(
                    existing["rights_evidence_ref"]
                    if legacy_replay
                    else plan.rights_evidence_ref
                ),
                rights_status=receipt_rights_status,
                extraction_method=receipt_extraction_method,
                ocr_review_status=receipt_ocr_status,
                ocr_review_evidence_ref=(
                    existing["ocr_review_evidence_ref"]
                    if legacy_replay
                    else plan.ocr_review_evidence_ref
                ),
                approval_ref=approval_ref,
                idempotency_key=plan.idempotency_key,
                rollback_ref=plan.rollback_ref,
                mutation_performed=mutation_performed,
                reason_codes=[
                    "KNOWLEDGE_SOURCE_INGESTED"
                    if mutation_performed
                    else (
                        "KNOWLEDGE_LEGACY_SOURCE_ALREADY_PRESENT_QUARANTINED"
                        if legacy_replay
                        and receipt_extraction_method
                        == KnowledgeExtractionMethod.legacy_unclassified
                        else "KNOWLEDGE_SOURCE_ALREADY_PRESENT"
                    ),
                    "KNOWLEDGE_RIGHTS_ATTESTED",
                    "KNOWLEDGE_EXACT_APPROVAL_VALIDATED",
                ],
            )
            self._insert_audit_record(
                connection,
                self._audit_record(
                    operation="ingest",
                    receipt=receipt,
                    subject_ref=document_ref,
                    approver_actor_id=approver_actor_id,
                    actor_context=actor_context,
                    run_id=run_id,
                ),
            )
        return receipt

    def list_documents(
        self,
        *,
        source_kind: KnowledgeSourceKind | None = None,
        category: str | None = None,
        collection: str | None = None,
        tag: str | None = None,
        lifecycle_state: KnowledgeLifecycleState | None = None,
        rights_status: KnowledgeRightsStatus | None = None,
        sort_by: str = "newest",
    ) -> list[KnowledgeDocument]:
        if not self.database_path.exists():
            return []
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents").fetchall()
        documents = [self._document_from_row(row) for row in rows]
        if source_kind is not None:
            documents = [
                item for item in documents if item.source_kind == source_kind.value
            ]
        if category is not None:
            documents = [item for item in documents if item.category == category]
        if collection is not None:
            documents = [item for item in documents if item.collection == collection]
        if tag is not None:
            documents = [item for item in documents if tag in item.tags]
        if lifecycle_state is not None:
            documents = [
                item
                for item in documents
                if item.lifecycle_state == _enum_value(lifecycle_state)
            ]
        if rights_status is not None:
            documents = [
                item
                for item in documents
                if item.rights_status == _enum_value(rights_status)
            ]
        sort_keys = {
            "newest": lambda item: (item.created_at, item.document_ref),
            "oldest": lambda item: (item.created_at, item.document_ref),
            "title": lambda item: (item.title.casefold(), item.document_ref),
            "category": lambda item: (
                item.category,
                item.title.casefold(),
                item.document_ref,
            ),
            "source_kind": lambda item: (
                item.source_kind,
                item.title.casefold(),
                item.document_ref,
            ),
        }
        if sort_by not in sort_keys:
            raise ValueError("KNOWLEDGE_DOCUMENT_SORT_UNSUPPORTED")
        return sorted(documents, key=sort_keys[sort_by], reverse=sort_by == "newest")

    def inventory(self) -> KnowledgeInventory:
        documents = self.list_documents(sort_by="oldest")
        return KnowledgeInventory(
            document_count=len(documents),
            chunk_count=sum(item.chunk_count for item in documents),
            character_count=sum(item.character_count for item in documents),
            by_source_kind=dict(
                sorted(Counter(item.source_kind for item in documents).items())
            ),
            by_category=dict(
                sorted(Counter(item.category for item in documents).items())
            ),
            by_collection=dict(
                sorted(
                    Counter(
                        item.collection or "uncollected" for item in documents
                    ).items()
                )
            ),
            by_tag=dict(
                sorted(Counter(tag for item in documents for tag in item.tags).items())
            ),
            by_format=dict(
                sorted(Counter(item.source_format for item in documents).items())
            ),
            by_lifecycle_state=dict(
                sorted(Counter(item.lifecycle_state for item in documents).items())
            ),
            by_rights_status=dict(
                sorted(Counter(item.rights_status for item in documents).items())
            ),
            by_ocr_review_status=dict(
                sorted(Counter(item.ocr_review_status for item in documents).items())
            ),
        )

    def list_audit_records(self) -> list[KnowledgeAuditRecord]:
        if not self.database_path.exists():
            return []
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_records ORDER BY created_at, audit_ref"
            ).fetchall()
        return [
            KnowledgeAuditRecord(
                audit_ref=row["audit_ref"],
                operation=row["operation"],
                receipt_ref=row["receipt_ref"],
                exact_scope_ref=row["exact_scope_ref"],
                subject_ref=row["subject_ref"],
                approval_ref=row["approval_ref"],
                actor_ref=row["actor_ref"],
                approver_ref=row["approver_ref"],
                run_ref=row["run_ref"],
                idempotency_key=row["idempotency_key"],
                mutation_performed=bool(row["mutation_performed"]),
                reason_codes=json.loads(row["reason_codes_json"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def prepare_metadata_update(
        self,
        document_ref: str,
        *,
        source_kind: KnowledgeSourceKind,
        category: str,
        collection: str | None,
        tags: list[str],
        idempotency_key: str,
    ) -> PreparedKnowledgeMetadataUpdate:
        if not re.fullmatch(
            r"knowledge-document-ref:sha256:[0-9a-f]{24}", document_ref
        ):
            raise ValueError("KNOWLEDGE_DOCUMENT_REF_INVALID")
        if contains_obvious_secret({"idempotency_key": idempotency_key}):
            raise ValueError("KNOWLEDGE_IDEMPOTENCY_KEY_SECRET_LIKE")
        document = next(
            (
                item
                for item in self.list_documents()
                if item.document_ref == document_ref
            ),
            None,
        )
        if document is None:
            raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{document_ref}")
        plan = KnowledgeMetadataUpdatePlan(
            plan_ref="knowledge-metadata-plan-ref:pending",
            exact_scope_ref="knowledge-metadata-scope-ref:pending",
            store_ref=self.store_ref,
            document_ref=document_ref,
            expected_metadata_ref=_metadata_ref(
                document.source_kind,
                document.category,
                document.collection,
                document.tags,
            ),
            source_kind=source_kind,
            category=category,
            collection=collection,
            tags=tags,
            idempotency_key=idempotency_key,
        )
        exact_scope_ref = _metadata_scope_ref(plan)
        plan = plan.model_copy(
            update={
                "exact_scope_ref": exact_scope_ref,
                "plan_ref": _hash_ref("knowledge-metadata-plan-ref", exact_scope_ref),
            }
        )
        return PreparedKnowledgeMetadataUpdate(plan=plan)

    def approval_request_for_metadata_update(
        self,
        prepared: PreparedKnowledgeMetadataUpdate,
        *,
        actor_context: ActorContext,
        run_id: str,
    ) -> ApprovalRequest:
        self._validate_prepared_metadata_update(prepared)
        plan = prepared.plan
        return ApprovalRequest(
            approval_request_id=_hash_ref(
                "knowledge-metadata-approval-request", plan.exact_scope_ref
            ),
            run_id=run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=plan.plan_ref,
            actor_context=actor_context,
            requested_action="knowledge_dump.update_metadata",
            purpose="Update navigation metadata for one exact local Knowledge Dump document.",
            risk_level=ApprovalRiskLevel.low,
            data_classification=DataClassification(
                classification=ClassificationValue.project_private,
                source="local_knowledge_metadata_update",
                allowed_sinks=["local_knowledge_dump", "receipts"],
                forbidden_sinks=["network", "provider", "model_training"],
            ),
            resource_refs=[
                plan.exact_scope_ref,
                plan.document_ref,
                plan.expected_metadata_ref,
                plan.store_ref,
            ],
            trace_id=plan.plan_ref,
        )

    def update_metadata(
        self,
        prepared: PreparedKnowledgeMetadataUpdate,
        *,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeMetadataUpdateReceipt:
        if contains_obvious_secret({"approval_ref": approval_ref}):
            raise ValueError("KNOWLEDGE_APPROVAL_REF_SECRET_LIKE")
        request = self.approval_request_for_metadata_update(
            prepared, actor_context=actor_context, run_id=run_id
        )
        self._require_mutation_policy(
            operation="metadata_update",
            plan_ref=prepared.plan.plan_ref,
            exact_scope_ref=prepared.plan.exact_scope_ref,
            idempotency_key=prepared.plan.idempotency_key,
        )
        with approval_authority.hold_validation_lock():
            decision = approval_authority.validate_for_request(request, approval_ref)
            if not decision.allowed:
                raise PermissionError("KNOWLEDGE_METADATA_EXACT_APPROVAL_REQUIRED")
            grant = approval_authority.get_grant(approval_ref)
            if grant is None:
                raise PermissionError("KNOWLEDGE_METADATA_EXACT_APPROVAL_REQUIRED")
            return self._persist_approved_metadata_update(
                prepared,
                approval_ref=approval_ref,
                approver_actor_id=grant.approved_by_actor_id,
                actor_context=actor_context,
                run_id=run_id,
            )

    def _persist_approved_metadata_update(
        self,
        prepared: PreparedKnowledgeMetadataUpdate,
        *,
        approval_ref: str,
        approver_actor_id: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeMetadataUpdateReceipt:
        self._initialize()
        plan = prepared.plan
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_prepared_metadata_update(prepared)
            existing = connection.execute(
                "SELECT exact_scope_ref FROM metadata_updates WHERE idempotency_key = ?",
                (plan.idempotency_key,),
            ).fetchone()
            audited_replay = self._audit_idempotency_replay(
                connection,
                operation="metadata_update",
                idempotency_key=plan.idempotency_key,
                exact_scope_ref=plan.exact_scope_ref,
                subject_ref=plan.document_ref,
                conflict_code="KNOWLEDGE_METADATA_IDEMPOTENCY_CONFLICT",
            )
            if (
                existing is not None
                and existing["exact_scope_ref"] != plan.exact_scope_ref
            ):
                raise ValueError("KNOWLEDGE_METADATA_IDEMPOTENCY_CONFLICT")
            mutation_performed = existing is None and not audited_replay
            if mutation_performed:
                current = connection.execute(
                    """SELECT source_kind, category, collection, tags_json
                       FROM documents WHERE document_ref = ?""",
                    (plan.document_ref,),
                ).fetchone()
                if current is None:
                    raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{plan.document_ref}")
                current_metadata_ref = _metadata_ref(
                    current["source_kind"],
                    current["category"],
                    current["collection"],
                    json.loads(current["tags_json"]),
                )
                if current_metadata_ref != plan.expected_metadata_ref:
                    raise ValueError("KNOWLEDGE_METADATA_STALE_REVISION")
                updated = connection.execute(
                    "UPDATE documents SET source_kind = ?, category = ?, collection = ?, tags_json = ? WHERE document_ref = ?",
                    (
                        plan.source_kind,
                        plan.category,
                        plan.collection,
                        json.dumps(plan.tags, separators=(",", ":")),
                        plan.document_ref,
                    ),
                )
                if updated.rowcount != 1:
                    raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{plan.document_ref}")
                connection.execute(
                    "INSERT INTO metadata_updates (idempotency_key, exact_scope_ref, document_ref, created_at) VALUES (?, ?, ?, ?)",
                    (
                        plan.idempotency_key,
                        plan.exact_scope_ref,
                        plan.document_ref,
                        utc_now().isoformat(),
                    ),
                )
            receipt = KnowledgeMetadataUpdateReceipt(
                receipt_ref=_hash_ref(
                    "knowledge-metadata-receipt-ref", plan.exact_scope_ref
                ),
                plan_ref=plan.plan_ref,
                exact_scope_ref=plan.exact_scope_ref,
                document_ref=plan.document_ref,
                source_kind=plan.source_kind,
                category=plan.category,
                collection=plan.collection,
                tags=plan.tags,
                approval_ref=approval_ref,
                idempotency_key=plan.idempotency_key,
                mutation_performed=mutation_performed,
                reason_codes=[
                    "KNOWLEDGE_METADATA_UPDATED"
                    if mutation_performed
                    else "KNOWLEDGE_METADATA_ALREADY_APPLIED",
                    "KNOWLEDGE_METADATA_EXACT_APPROVAL_VALIDATED",
                ],
            )
            self._insert_audit_record(
                connection,
                self._audit_record(
                    operation="metadata_update",
                    receipt=receipt,
                    subject_ref=plan.document_ref,
                    approver_actor_id=approver_actor_id,
                    actor_context=actor_context,
                    run_id=run_id,
                ),
            )
        return receipt

    def prepare_governance_update(
        self,
        document_ref: str,
        *,
        lifecycle_state: KnowledgeLifecycleState,
        rights_status: KnowledgeRightsStatus,
        rights_evidence_ref: str,
        extraction_method: KnowledgeExtractionMethod | None = None,
        ocr_review_status: KnowledgeOcrReviewStatus,
        ocr_review_evidence_ref: str | None,
        idempotency_key: str,
    ) -> PreparedKnowledgeGovernanceUpdate:
        if contains_obvious_secret(
            {
                "rights_evidence_ref": rights_evidence_ref,
                "ocr_review_evidence_ref": ocr_review_evidence_ref,
                "idempotency_key": idempotency_key,
            }
        ):
            raise ValueError("KNOWLEDGE_GOVERNANCE_REF_SECRET_LIKE")
        document = self._require_document(document_ref)
        target_extraction_method = extraction_method or KnowledgeExtractionMethod(
            document.extraction_method
        )
        stored_plan: KnowledgeGovernanceUpdatePlan | None = None
        if self.database_path.exists():
            with self._connect() as connection:
                table_exists = connection.execute(
                    """SELECT 1 FROM sqlite_master
                       WHERE type = 'table' AND name = 'governance_updates'"""
                ).fetchone()
                if table_exists is not None:
                    columns = {
                        row["name"]
                        for row in connection.execute(
                            "PRAGMA table_info(governance_updates)"
                        ).fetchall()
                    }
                    row = connection.execute(
                        "SELECT * FROM governance_updates WHERE idempotency_key = ?",
                        (idempotency_key,),
                    ).fetchone()
                    if row is not None:
                        if "plan_json" not in columns or row["plan_json"] is None:
                            raise ValueError(
                                "KNOWLEDGE_GOVERNANCE_REPLAY_SCOPE_UNAVAILABLE"
                            )
                        stored_plan = KnowledgeGovernanceUpdatePlan.model_validate_json(
                            row["plan_json"]
                        )
        if stored_plan is not None:
            requested_posture = (
                document_ref,
                _enum_value(lifecycle_state),
                _enum_value(rights_status),
                rights_evidence_ref,
                _enum_value(target_extraction_method),
                _enum_value(ocr_review_status),
                ocr_review_evidence_ref,
                idempotency_key,
                self.store_ref,
            )
            stored_posture = (
                stored_plan.document_ref,
                _enum_value(stored_plan.lifecycle_state),
                _enum_value(stored_plan.rights_status),
                stored_plan.rights_evidence_ref,
                _enum_value(stored_plan.extraction_method),
                _enum_value(stored_plan.ocr_review_status),
                stored_plan.ocr_review_evidence_ref,
                stored_plan.idempotency_key,
                stored_plan.store_ref,
            )
            if requested_posture != stored_posture:
                raise ValueError("KNOWLEDGE_GOVERNANCE_IDEMPOTENCY_CONFLICT")
            prepared = PreparedKnowledgeGovernanceUpdate(plan=stored_plan)
            self._validate_prepared_governance_update(prepared, document=document)
            return prepared
        plan = KnowledgeGovernanceUpdatePlan(
            plan_ref="knowledge-governance-plan-ref:pending",
            exact_scope_ref="knowledge-governance-scope-ref:pending",
            store_ref=self.store_ref,
            document_ref=document_ref,
            expected_governance_ref=self._governance_ref_for_document(document),
            lifecycle_state=lifecycle_state,
            rights_status=rights_status,
            rights_evidence_ref=rights_evidence_ref,
            extraction_method=target_extraction_method,
            ocr_review_status=ocr_review_status,
            ocr_review_evidence_ref=ocr_review_evidence_ref,
            idempotency_key=idempotency_key,
        )
        exact_scope_ref = _governance_scope_ref(plan)
        plan = plan.model_copy(
            update={
                "exact_scope_ref": exact_scope_ref,
                "plan_ref": _hash_ref("knowledge-governance-plan-ref", exact_scope_ref),
            }
        )
        prepared = PreparedKnowledgeGovernanceUpdate(plan=plan)
        self._validate_prepared_governance_update(prepared, document=document)
        return prepared

    def approval_request_for_governance_update(
        self,
        prepared: PreparedKnowledgeGovernanceUpdate,
        *,
        actor_context: ActorContext,
        run_id: str,
    ) -> ApprovalRequest:
        document = self._require_document(prepared.plan.document_ref)
        self._validate_prepared_governance_update(prepared, document=document)
        plan = prepared.plan
        return ApprovalRequest(
            approval_request_id=_hash_ref(
                "knowledge-governance-approval-request", plan.exact_scope_ref
            ),
            run_id=run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=plan.plan_ref,
            actor_context=actor_context,
            requested_action="knowledge_dump.update_governance",
            purpose=(
                "Update lifecycle, rights, and OCR review posture for one exact "
                "local Knowledge Dump document."
            ),
            risk_level=ApprovalRiskLevel.medium,
            data_classification=DataClassification(
                classification=ClassificationValue.project_private,
                source="local_knowledge_governance_update",
                allowed_sinks=["local_knowledge_dump", "receipts"],
                forbidden_sinks=["network", "provider", "model_training"],
                requires_consent=True,
                retention_policy="until_exact_approved_removal",
            ),
            resource_refs=[
                plan.exact_scope_ref,
                plan.document_ref,
                plan.expected_governance_ref,
                plan.rights_evidence_ref,
                plan.store_ref,
                *(
                    [plan.ocr_review_evidence_ref]
                    if plan.ocr_review_evidence_ref is not None
                    else []
                ),
            ],
            consent_refs=[
                plan.rights_evidence_ref,
                *(
                    [plan.ocr_review_evidence_ref]
                    if plan.ocr_review_evidence_ref is not None
                    else []
                ),
            ],
            trace_id=plan.plan_ref,
        )

    def update_governance(
        self,
        prepared: PreparedKnowledgeGovernanceUpdate,
        *,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeGovernanceUpdateReceipt:
        if contains_obvious_secret({"approval_ref": approval_ref}):
            raise ValueError("KNOWLEDGE_APPROVAL_REF_SECRET_LIKE")
        request = self.approval_request_for_governance_update(
            prepared, actor_context=actor_context, run_id=run_id
        )
        self._require_mutation_policy(
            operation="governance_update",
            plan_ref=prepared.plan.plan_ref,
            exact_scope_ref=prepared.plan.exact_scope_ref,
            idempotency_key=prepared.plan.idempotency_key,
        )
        with approval_authority.hold_validation_lock():
            decision = approval_authority.validate_for_request(request, approval_ref)
            if not decision.allowed:
                raise PermissionError("KNOWLEDGE_GOVERNANCE_EXACT_APPROVAL_REQUIRED")
            grant = approval_authority.get_grant(approval_ref)
            if grant is None:
                raise PermissionError("KNOWLEDGE_GOVERNANCE_EXACT_APPROVAL_REQUIRED")
            return self._persist_approved_governance_update(
                prepared,
                approval_ref=approval_ref,
                approver_actor_id=grant.approved_by_actor_id,
                actor_context=actor_context,
                run_id=run_id,
            )

    def _persist_approved_governance_update(
        self,
        prepared: PreparedKnowledgeGovernanceUpdate,
        *,
        approval_ref: str,
        approver_actor_id: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeGovernanceUpdateReceipt:
        self._initialize()
        plan = prepared.plan
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM documents WHERE document_ref = ?",
                (plan.document_ref,),
            ).fetchone()
            if row is None:
                raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{plan.document_ref}")
            document = self._document_from_row(row)
            self._validate_prepared_governance_update(prepared, document=document)
            existing = connection.execute(
                "SELECT exact_scope_ref FROM governance_updates WHERE idempotency_key = ?",
                (plan.idempotency_key,),
            ).fetchone()
            audited_replay = self._audit_idempotency_replay(
                connection,
                operation="governance_update",
                idempotency_key=plan.idempotency_key,
                exact_scope_ref=plan.exact_scope_ref,
                subject_ref=plan.document_ref,
                conflict_code="KNOWLEDGE_GOVERNANCE_IDEMPOTENCY_CONFLICT",
            )
            if (
                existing is not None
                and existing["exact_scope_ref"] != plan.exact_scope_ref
            ):
                raise ValueError("KNOWLEDGE_GOVERNANCE_IDEMPOTENCY_CONFLICT")
            mutation_performed = existing is None and not audited_replay
            if mutation_performed:
                if (
                    self._governance_ref_for_document(document)
                    != plan.expected_governance_ref
                ):
                    raise ValueError("KNOWLEDGE_GOVERNANCE_STALE_REVISION")
                connection.execute(
                    """UPDATE documents
                       SET lifecycle_state = ?, rights_status = ?, rights_evidence_ref = ?,
                           extraction_method = ?, ocr_review_status = ?,
                           ocr_review_evidence_ref = ?
                       WHERE document_ref = ?""",
                    (
                        plan.lifecycle_state,
                        plan.rights_status,
                        plan.rights_evidence_ref,
                        plan.extraction_method,
                        plan.ocr_review_status,
                        plan.ocr_review_evidence_ref,
                        plan.document_ref,
                    ),
                )
                connection.execute(
                    """INSERT INTO governance_updates
                       (idempotency_key, exact_scope_ref, document_ref, plan_json,
                        created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        plan.idempotency_key,
                        plan.exact_scope_ref,
                        plan.document_ref,
                        plan.model_dump_json(),
                        utc_now().isoformat(),
                    ),
                )
            receipt = KnowledgeGovernanceUpdateReceipt(
                receipt_ref=_hash_ref(
                    "knowledge-governance-receipt-ref", plan.exact_scope_ref
                ),
                plan_ref=plan.plan_ref,
                exact_scope_ref=plan.exact_scope_ref,
                document_ref=plan.document_ref,
                lifecycle_state=plan.lifecycle_state,
                rights_status=plan.rights_status,
                rights_evidence_ref=plan.rights_evidence_ref,
                extraction_method=plan.extraction_method,
                ocr_review_status=plan.ocr_review_status,
                ocr_review_evidence_ref=plan.ocr_review_evidence_ref,
                approval_ref=approval_ref,
                idempotency_key=plan.idempotency_key,
                mutation_performed=mutation_performed,
                reason_codes=[
                    "KNOWLEDGE_GOVERNANCE_UPDATED"
                    if mutation_performed
                    else "KNOWLEDGE_GOVERNANCE_ALREADY_APPLIED",
                    "KNOWLEDGE_GOVERNANCE_EXACT_APPROVAL_VALIDATED",
                ],
            )
            self._insert_audit_record(
                connection,
                self._audit_record(
                    operation="governance_update",
                    receipt=receipt,
                    subject_ref=plan.document_ref,
                    approver_actor_id=approver_actor_id,
                    actor_context=actor_context,
                    run_id=run_id,
                ),
            )
        return receipt

    def prepare_removal(
        self,
        document_ref: str,
        *,
        retention_decision_ref: str,
        backup_disposition_ref: str,
        idempotency_key: str,
    ) -> PreparedKnowledgeRemoval:
        if contains_obvious_secret(
            {
                "retention_decision_ref": retention_decision_ref,
                "backup_disposition_ref": backup_disposition_ref,
                "idempotency_key": idempotency_key,
            }
        ):
            raise ValueError("KNOWLEDGE_REMOVAL_REF_SECRET_LIKE")
        if not self.database_path.exists():
            raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{document_ref}")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT chunk_count, character_count FROM documents WHERE document_ref = ?",
                (document_ref,),
            ).fetchone()
            if row is None:
                removal_table_exists = connection.execute(
                    """SELECT 1 FROM sqlite_master
                       WHERE type = 'table' AND name = 'document_removals'"""
                ).fetchone()
                removed = (
                    connection.execute(
                        """SELECT * FROM document_removals
                           WHERE idempotency_key = ?""",
                        (idempotency_key,),
                    ).fetchone()
                    if removal_table_exists is not None
                    else None
                )
                if removed is None:
                    raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{document_ref}")
                if (
                    removed["document_ref"] != document_ref
                    or removed["retention_decision_ref"] != retention_decision_ref
                    or removed["backup_disposition_ref"] != backup_disposition_ref
                ):
                    raise ValueError("KNOWLEDGE_REMOVAL_IDEMPOTENCY_CONFLICT")
                revision_ref = str(removed["expected_document_revision_ref"])
                planned_chunk_count = int(removed["deleted_chunk_count"])
                planned_character_count = int(removed["deleted_character_count"])
                stored_scope_ref = str(removed["exact_scope_ref"])
            else:
                revision_ref = self._document_revision_ref(connection, document_ref)
                planned_chunk_count = int(row["chunk_count"])
                planned_character_count = int(row["character_count"])
                stored_scope_ref = None
        plan = KnowledgeRemovalPlan(
            plan_ref="knowledge-removal-plan-ref:pending",
            exact_scope_ref="knowledge-removal-scope-ref:pending",
            store_ref=self.store_ref,
            document_ref=document_ref,
            expected_document_revision_ref=revision_ref,
            retention_decision_ref=retention_decision_ref,
            backup_disposition_ref=backup_disposition_ref,
            idempotency_key=idempotency_key,
            planned_chunk_count=planned_chunk_count,
            planned_character_count=planned_character_count,
        )
        exact_scope_ref = _removal_scope_ref(plan)
        if stored_scope_ref is not None and stored_scope_ref != exact_scope_ref:
            raise ValueError("KNOWLEDGE_REMOVAL_IDEMPOTENCY_CONFLICT")
        plan = plan.model_copy(
            update={
                "exact_scope_ref": exact_scope_ref,
                "plan_ref": _hash_ref("knowledge-removal-plan-ref", exact_scope_ref),
            }
        )
        prepared = PreparedKnowledgeRemoval(plan=plan)
        self._validate_prepared_removal(prepared)
        return prepared

    def approval_request_for_removal(
        self,
        prepared: PreparedKnowledgeRemoval,
        *,
        actor_context: ActorContext,
        run_id: str,
    ) -> ApprovalRequest:
        self._validate_prepared_removal(prepared)
        plan = prepared.plan
        return ApprovalRequest(
            approval_request_id=_hash_ref(
                "knowledge-removal-approval-request", plan.exact_scope_ref
            ),
            run_id=run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=plan.plan_ref,
            actor_context=actor_context,
            requested_action="knowledge_dump.remove",
            purpose=(
                "Permanently remove one exact local source and its chunks after "
                "reviewing retention and external-backup posture."
            ),
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.third_party_confidential,
                source="local_knowledge_exact_removal",
                allowed_sinks=["local_knowledge_dump", "redacted_receipts"],
                forbidden_sinks=["network", "provider", "model_training", "logs"],
                requires_consent=True,
                retention_policy="exact_approved_removal",
            ),
            resource_refs=[
                plan.exact_scope_ref,
                plan.document_ref,
                plan.expected_document_revision_ref,
                plan.retention_decision_ref,
                plan.backup_disposition_ref,
                plan.store_ref,
            ],
            consent_refs=[plan.retention_decision_ref, plan.backup_disposition_ref],
            trace_id=plan.plan_ref,
        )

    def remove(
        self,
        prepared: PreparedKnowledgeRemoval,
        *,
        approval_authority: LocalApprovalAuthority,
        approval_ref: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeRemovalReceipt:
        if contains_obvious_secret({"approval_ref": approval_ref}):
            raise ValueError("KNOWLEDGE_APPROVAL_REF_SECRET_LIKE")
        request = self.approval_request_for_removal(
            prepared, actor_context=actor_context, run_id=run_id
        )
        self._require_mutation_policy(
            operation="removal",
            plan_ref=prepared.plan.plan_ref,
            exact_scope_ref=prepared.plan.exact_scope_ref,
            idempotency_key=prepared.plan.idempotency_key,
        )
        with approval_authority.hold_validation_lock():
            decision = approval_authority.validate_for_request(request, approval_ref)
            if not decision.allowed:
                raise PermissionError("KNOWLEDGE_REMOVAL_EXACT_APPROVAL_REQUIRED")
            grant = approval_authority.get_grant(approval_ref)
            if grant is None:
                raise PermissionError("KNOWLEDGE_REMOVAL_EXACT_APPROVAL_REQUIRED")
            return self._persist_approved_removal(
                prepared,
                approval_ref=approval_ref,
                approver_actor_id=grant.approved_by_actor_id,
                actor_context=actor_context,
                run_id=run_id,
            )

    def _persist_approved_removal(
        self,
        prepared: PreparedKnowledgeRemoval,
        *,
        approval_ref: str,
        approver_actor_id: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeRemovalReceipt:
        self._initialize()
        plan = prepared.plan
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_prepared_removal(prepared)
            existing = connection.execute(
                "SELECT * FROM document_removals WHERE idempotency_key = ?",
                (plan.idempotency_key,),
            ).fetchone()
            if (
                existing is not None
                and existing["exact_scope_ref"] != plan.exact_scope_ref
            ):
                raise ValueError("KNOWLEDGE_REMOVAL_IDEMPOTENCY_CONFLICT")
            mutation_performed = existing is None
            if mutation_performed:
                current_revision_ref = self._document_revision_ref(
                    connection, plan.document_ref
                )
                if current_revision_ref != plan.expected_document_revision_ref:
                    raise ValueError("KNOWLEDGE_REMOVAL_STALE_REVISION")
                source_binding = connection.execute(
                    """SELECT source_content_ref, idempotency_key FROM documents
                       WHERE document_ref = ?""",
                    (plan.document_ref,),
                ).fetchone()
                if source_binding is None:
                    raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{plan.document_ref}")
                chunk_rows = connection.execute(
                    "SELECT chunk_ref FROM chunks WHERE document_ref = ? ORDER BY ordinal",
                    (plan.document_ref,),
                ).fetchall()
                if len(chunk_rows) != plan.planned_chunk_count:
                    raise ValueError("KNOWLEDGE_REMOVAL_STALE_REVISION")
                connection.executemany(
                    "DELETE FROM chunks_fts WHERE chunk_ref = ?",
                    ((row["chunk_ref"],) for row in chunk_rows),
                )
                deleted = connection.execute(
                    "DELETE FROM documents WHERE document_ref = ?",
                    (plan.document_ref,),
                )
                if deleted.rowcount != 1:
                    raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{plan.document_ref}")
                connection.execute(
                    """INSERT INTO document_removals
                       (idempotency_key, exact_scope_ref, document_ref,
                        expected_document_revision_ref, retention_decision_ref,
                        backup_disposition_ref, source_content_ref,
                        ingest_idempotency_key, deleted_chunk_count,
                        deleted_character_count, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        plan.idempotency_key,
                        plan.exact_scope_ref,
                        plan.document_ref,
                        plan.expected_document_revision_ref,
                        plan.retention_decision_ref,
                        plan.backup_disposition_ref,
                        source_binding["source_content_ref"],
                        source_binding["idempotency_key"],
                        plan.planned_chunk_count,
                        plan.planned_character_count,
                        utc_now().isoformat(),
                    ),
                )
                deleted_chunk_count = plan.planned_chunk_count
                deleted_character_count = plan.planned_character_count
            else:
                deleted_chunk_count = int(existing["deleted_chunk_count"])
                deleted_character_count = int(existing["deleted_character_count"])
            receipt = KnowledgeRemovalReceipt(
                receipt_ref=_hash_ref(
                    "knowledge-removal-receipt-ref", plan.exact_scope_ref
                ),
                plan_ref=plan.plan_ref,
                exact_scope_ref=plan.exact_scope_ref,
                document_ref=plan.document_ref,
                expected_document_revision_ref=plan.expected_document_revision_ref,
                retention_decision_ref=plan.retention_decision_ref,
                backup_disposition_ref=plan.backup_disposition_ref,
                approval_ref=approval_ref,
                idempotency_key=plan.idempotency_key,
                deleted_chunk_count=deleted_chunk_count,
                deleted_character_count=deleted_character_count,
                mutation_performed=mutation_performed,
                reason_codes=[
                    "KNOWLEDGE_DOCUMENT_REMOVED"
                    if mutation_performed
                    else "KNOWLEDGE_DOCUMENT_REMOVAL_ALREADY_APPLIED",
                    "KNOWLEDGE_REMOVAL_EXACT_APPROVAL_VALIDATED",
                    "KNOWLEDGE_RESTORE_REQUIRES_EXTERNAL_BACKUP",
                ],
            )
            self._insert_audit_record(
                connection,
                self._audit_record(
                    operation="removal",
                    receipt=receipt,
                    subject_ref=plan.document_ref,
                    approver_actor_id=approver_actor_id,
                    actor_context=actor_context,
                    run_id=run_id,
                ),
            )
        return receipt

    def encryption_posture(self) -> KnowledgeEncryptionPosture:
        root_private = (
            self.root.exists() and stat.S_IMODE(self.root.stat().st_mode) == 0o700
        )
        database_private = (
            self.database_path.exists()
            and not self.database_path.is_symlink()
            and self.database_path.is_file()
            and stat.S_IMODE(self.database_path.stat().st_mode) == 0o600
        )
        return KnowledgeEncryptionPosture(
            store_ref=self.store_ref,
            owner_only_directory_permissions=root_private,
            owner_only_database_permissions=database_private,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        source_kind: KnowledgeSourceKind | None = None,
        category: str | None = None,
        collection: str | None = None,
        tag: str | None = None,
    ) -> list[KnowledgeHit]:
        if len(query) > MAX_QUERY_CHARACTERS or limit < 1 or limit > 50:
            raise ValueError("KNOWLEDGE_QUERY_OUT_OF_BOUNDS")
        tokens = list(dict.fromkeys(_TOKEN_RE.findall(query.casefold())))
        if not tokens:
            raise ValueError("KNOWLEDGE_QUERY_OUT_OF_BOUNDS")
        if contains_obvious_secret({"query": query}):
            raise ValueError("KNOWLEDGE_QUERY_SECRET_LIKE")
        if not self.database_path.exists():
            return []
        match_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
        with self._connect() as connection:
            connection.execute("BEGIN")
            document_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(documents)").fetchall()
            }
            clauses: list[str] = []
            parameters: list[str] = []
            if source_kind is not None:
                clauses.append("source_kind = ?")
                parameters.append(_enum_value(source_kind))
            if category is not None:
                clauses.append("category = ?")
                parameters.append(category)
            if collection is not None:
                clauses.append("collection = ?")
                parameters.append(collection)
            where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
            lifecycle_expression = (
                "lifecycle_state"
                if "lifecycle_state" in document_columns
                else "'active'"
            )
            rights_expression = (
                "rights_status"
                if "rights_status" in document_columns
                else "'review_required'"
            )
            extraction_expression = (
                "extraction_method"
                if "extraction_method" in document_columns
                else "'legacy_unclassified'"
            )
            ocr_expression = (
                "ocr_review_status"
                if "ocr_review_status" in document_columns
                else "'pending_review'"
            )
            ocr_evidence_expression = (
                "ocr_review_evidence_ref"
                if "ocr_review_evidence_ref" in document_columns
                else "NULL"
            )
            membership_rows = connection.execute(
                f"""SELECT document_ref, tags_json,
                           {lifecycle_expression} AS lifecycle_state,
                           {rights_expression} AS rights_status,
                           {extraction_expression} AS extraction_method,
                           {ocr_expression} AS ocr_review_status,
                           {ocr_evidence_expression} AS ocr_review_evidence_ref
                    FROM documents{where}""",
                parameters,
            ).fetchall()
            allowed_document_refs = {
                str(row["document_ref"])
                for row in membership_rows
                if (tag is None or tag in json.loads(row["tags_json"]))
                and row["lifecycle_state"] == KnowledgeLifecycleState.active
                and row["rights_status"] == KnowledgeRightsStatus.current
                and (
                    (
                        row["extraction_method"]
                        == KnowledgeExtractionMethod.native_text
                        and row["ocr_review_status"]
                        == KnowledgeOcrReviewStatus.not_required
                    )
                    or (
                        row["extraction_method"]
                        == KnowledgeExtractionMethod.operator_supplied_ocr
                        and row["ocr_review_status"]
                        == KnowledgeOcrReviewStatus.reviewed
                        and row["ocr_review_evidence_ref"] is not None
                    )
                )
            }
            if not allowed_document_refs:
                return []
            connection.execute(
                "CREATE TEMP TABLE allowed_document_refs "
                "(document_ref TEXT PRIMARY KEY)"
            )
            connection.executemany(
                "INSERT INTO allowed_document_refs (document_ref) VALUES (?)",
                ((document_ref,) for document_ref in sorted(allowed_document_refs)),
            )
            filtered = any(
                value is not None for value in (source_kind, category, collection, tag)
            )
            fts_table = "chunks_fts"
            if filtered:
                connection.execute(
                    "CREATE VIRTUAL TABLE temp.filtered_chunks_fts USING fts5("
                    "chunk_ref UNINDEXED, text, "
                    "tokenize='unicode61 remove_diacritics 2')"
                )
                connection.execute(
                    "INSERT INTO filtered_chunks_fts (chunk_ref, text) "
                    "SELECT c.chunk_ref, c.text FROM chunks c "
                    "JOIN allowed_document_refs a "
                    "ON a.document_ref = c.document_ref"
                )
                fts_table = "filtered_chunks_fts"
            catalog_locator_expression = (
                "d.catalog_citation_locator_refs_json"
                if "catalog_citation_locator_refs_json" in document_columns
                else "'[]'"
            )
            rows = connection.execute(
                f"""SELECT c.chunk_ref, c.locator, c.text, c.text_ref,
                          d.document_ref, d.source_content_ref, d.title,
                          d.catalog_source_id,
                          {catalog_locator_expression} AS catalog_citation_locator_refs_json,
                          bm25({fts_table}) AS rank
                   FROM {fts_table}
                   JOIN chunks c ON c.chunk_ref = {fts_table}.chunk_ref
                   JOIN documents d ON d.document_ref = c.document_ref
                   JOIN allowed_document_refs a ON a.document_ref = d.document_ref
                   WHERE {fts_table} MATCH ?
                   ORDER BY rank ASC, c.chunk_ref ASC LIMIT ?""",
                (match_query, limit),
            ).fetchall()
        hits = [
            KnowledgeHit(
                citation=KnowledgeCitation(
                    document_ref=row["document_ref"],
                    chunk_ref=row["chunk_ref"],
                    source_content_ref=row["source_content_ref"],
                    title=row["title"],
                    locator=row["locator"],
                    catalog_source_id=row["catalog_source_id"],
                    catalog_citation_locator_refs=tuple(
                        json.loads(row["catalog_citation_locator_refs_json"])
                    ),
                ),
                text=row["text"],
                score=max(0.0, -float(row["rank"])),
            )
            for row in rows
        ]
        return hits

    def prepare_context(
        self,
        query: str,
        *,
        limit: int = 8,
        max_characters: int = 8_000,
        source_kind: KnowledgeSourceKind | None = None,
        category: str | None = None,
        collection: str | None = None,
        tag: str | None = None,
    ) -> KnowledgeContextPack:
        if max_characters < 1 or max_characters > 50_000:
            raise ValueError("KNOWLEDGE_CONTEXT_BUDGET_OUT_OF_BOUNDS")
        selected: list[KnowledgeHit] = []
        used = 0
        for hit in self.search(
            query,
            limit=limit,
            source_kind=source_kind,
            category=category,
            collection=collection,
            tag=tag,
        ):
            if used + len(hit.text) > max_characters:
                continue
            selected.append(hit)
            used += len(hit.text)
        query_ref = _hash_ref("knowledge-query-ref", query)
        selection_refs = "|".join(hit.citation.chunk_ref for hit in selected)
        return KnowledgeContextPack(
            context_pack_ref=_hash_ref(
                "knowledge-context-pack-ref", f"{query_ref}|{selection_refs}"
            ),
            query_ref=query_ref,
            hits=tuple(selected),
            selection_mode="query_ranked",
            selected_chunk_refs=tuple(hit.citation.chunk_ref for hit in selected),
            used_characters=used,
            max_characters=max_characters,
        )

    def prepare_selected_context(
        self,
        chunk_refs: Iterable[str],
        *,
        max_characters: int = 8_000,
    ) -> KnowledgeContextPack:
        """Prepare cited context from an exact operator-selected chunk set."""

        selected_refs = tuple(dict.fromkeys(chunk_refs))
        if (
            not selected_refs
            or len(selected_refs) > 32
            or max_characters < 1
            or max_characters > 50_000
            or any(
                not re.fullmatch(r"knowledge-chunk-ref:sha256:[0-9a-f]{24}", chunk_ref)
                for chunk_ref in selected_refs
            )
        ):
            raise ValueError("KNOWLEDGE_CONTEXT_SELECTION_OUT_OF_BOUNDS")
        if not self.database_path.exists():
            raise ValueError("KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE")
        placeholders = ",".join("?" for _ in selected_refs)
        with self._connect() as connection:
            document_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(documents)").fetchall()
            }

            def column(name: str, fallback: str) -> str:
                return f"d.{name}" if name in document_columns else f"'{fallback}'"

            ocr_evidence_expression = (
                "d.ocr_review_evidence_ref"
                if "ocr_review_evidence_ref" in document_columns
                else "NULL"
            )
            catalog_locator_expression = (
                "d.catalog_citation_locator_refs_json"
                if "catalog_citation_locator_refs_json" in document_columns
                else "'[]'"
            )
            rows = connection.execute(
                f"""SELECT c.chunk_ref, c.locator, c.text,
                           d.document_ref, d.source_content_ref, d.title,
                           d.catalog_source_id,
                           {catalog_locator_expression} AS catalog_citation_locator_refs_json,
                           {column("lifecycle_state", "active")} AS lifecycle_state,
                           {column("rights_status", "review_required")} AS rights_status,
                           {column("extraction_method", "legacy_unclassified")} AS extraction_method,
                           {column("ocr_review_status", "pending_review")} AS ocr_review_status,
                           {ocr_evidence_expression} AS ocr_review_evidence_ref
                    FROM chunks c
                    JOIN documents d ON d.document_ref = c.document_ref
                    WHERE c.chunk_ref IN ({placeholders})""",
                selected_refs,
            ).fetchall()
        rows_by_ref = {str(row["chunk_ref"]): row for row in rows}
        if set(rows_by_ref) != set(selected_refs):
            raise ValueError("KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE")
        ordered_rows = [rows_by_ref[chunk_ref] for chunk_ref in selected_refs]
        for row in ordered_rows:
            eligible = (
                row["lifecycle_state"] == KnowledgeLifecycleState.active
                and row["rights_status"] == KnowledgeRightsStatus.current
                and (
                    (
                        row["extraction_method"]
                        == KnowledgeExtractionMethod.native_text
                        and row["ocr_review_status"]
                        == KnowledgeOcrReviewStatus.not_required
                    )
                    or (
                        row["extraction_method"]
                        == KnowledgeExtractionMethod.operator_supplied_ocr
                        and row["ocr_review_status"]
                        == KnowledgeOcrReviewStatus.reviewed
                        and row["ocr_review_evidence_ref"] is not None
                    )
                )
            )
            if not eligible:
                raise ValueError("KNOWLEDGE_CONTEXT_SELECTION_INELIGIBLE")
        used_characters = sum(len(str(row["text"])) for row in ordered_rows)
        if used_characters > max_characters:
            raise ValueError("KNOWLEDGE_CONTEXT_CHARACTER_BUDGET_EXCEEDED")
        hits = tuple(
            KnowledgeHit(
                citation=KnowledgeCitation(
                    document_ref=row["document_ref"],
                    chunk_ref=row["chunk_ref"],
                    source_content_ref=row["source_content_ref"],
                    title=row["title"],
                    locator=row["locator"],
                    catalog_source_id=row["catalog_source_id"],
                    catalog_citation_locator_refs=tuple(
                        json.loads(row["catalog_citation_locator_refs_json"])
                    ),
                ),
                text=row["text"],
                score=0.0,
            )
            for row in ordered_rows
        )
        selection_material = "|".join(selected_refs)
        query_ref = _hash_ref("knowledge-query-ref", f"selected|{selection_material}")
        return KnowledgeContextPack(
            context_pack_ref=_hash_ref(
                "knowledge-context-pack-ref",
                f"{query_ref}|{max_characters}|{selection_material}",
            ),
            query_ref=query_ref,
            hits=hits,
            selection_mode="operator_selected",
            selected_chunk_refs=selected_refs,
            used_characters=used_characters,
            max_characters=max_characters,
        )

    def _validate_prepared_ingest(self, prepared: PreparedKnowledgeIngest) -> None:
        plan = prepared.plan
        chunks = tuple(prepared.chunks)
        if plan.store_ref != self.store_ref:
            raise ValueError("KNOWLEDGE_INGEST_STORE_SCOPE_MISMATCH")
        if (
            len(chunks) != plan.planned_chunk_count
            or sum(len(chunk.text) for chunk in chunks) != plan.planned_character_count
        ):
            raise ValueError("KNOWLEDGE_INGEST_CHUNK_MANIFEST_MISMATCH")
        for ordinal, chunk in enumerate(chunks):
            text_ref = _hash_ref("knowledge-chunk-content-ref", chunk.text, 40)
            chunk_ref = _hash_ref(
                "knowledge-chunk-ref",
                f"{plan.source_content_ref}|{ordinal}|{text_ref}",
            )
            if (
                not chunk.text
                or not chunk.locator
                or chunk.text_ref != text_ref
                or chunk.chunk_ref != chunk_ref
                or contains_obvious_secret({"content": chunk.text})
            ):
                raise ValueError("KNOWLEDGE_INGEST_CHUNK_MANIFEST_MISMATCH")
        if plan.chunk_manifest_ref != _chunk_manifest_ref(chunks):
            raise ValueError("KNOWLEDGE_INGEST_CHUNK_MANIFEST_MISMATCH")
        self._validate_catalog_binding(
            catalog_source_id=plan.catalog_source_id,
            catalog_citation_locator_refs=plan.catalog_citation_locator_refs,
            rights_basis=plan.rights_basis,
        )
        if (
            plan.contract_ref != KNOWLEDGE_DUMP_CONTRACT_REF
            or plan.exact_scope_ref != _ingest_scope_ref(plan)
            or plan.plan_ref
            != _hash_ref("knowledge-ingest-plan-ref", plan.exact_scope_ref)
            or plan.rollback_ref
            != _hash_ref("knowledge-rollback-ref", plan.source_content_ref)
            or not plan.approval_required
            or any(
                (
                    plan.source_path_persistence_enabled,
                    plan.network_access_enabled,
                    plan.model_call_enabled,
                    plan.model_training_enabled,
                    plan.automatic_chat_injection_enabled,
                )
            )
        ):
            raise ValueError("KNOWLEDGE_INGEST_PLAN_INTEGRITY_MISMATCH")

    def _validate_prepared_metadata_update(
        self, prepared: PreparedKnowledgeMetadataUpdate
    ) -> None:
        plan = prepared.plan
        if plan.store_ref != self.store_ref:
            raise ValueError("KNOWLEDGE_METADATA_STORE_SCOPE_MISMATCH")
        if (
            plan.contract_ref != KNOWLEDGE_DUMP_CONTRACT_REF
            or plan.exact_scope_ref != _metadata_scope_ref(plan)
            or plan.plan_ref
            != _hash_ref("knowledge-metadata-plan-ref", plan.exact_scope_ref)
            or not plan.approval_required
            or any(
                (
                    plan.source_content_mutation_enabled,
                    plan.network_access_enabled,
                    plan.model_call_enabled,
                )
            )
        ):
            raise ValueError("KNOWLEDGE_METADATA_PLAN_INTEGRITY_MISMATCH")

    def _validate_prepared_governance_update(
        self,
        prepared: PreparedKnowledgeGovernanceUpdate,
        *,
        document: KnowledgeDocument,
    ) -> None:
        plan = prepared.plan
        if plan.store_ref != self.store_ref:
            raise ValueError("KNOWLEDGE_GOVERNANCE_STORE_SCOPE_MISMATCH")
        if (
            plan.contract_ref != KNOWLEDGE_DUMP_CONTRACT_REF
            or plan.exact_scope_ref != _governance_scope_ref(plan)
            or plan.plan_ref
            != _hash_ref("knowledge-governance-plan-ref", plan.exact_scope_ref)
            or not plan.approval_required
            or any(
                (
                    plan.source_content_mutation_enabled,
                    plan.network_access_enabled,
                    plan.model_call_enabled,
                    plan.model_training_enabled,
                )
            )
        ):
            raise ValueError("KNOWLEDGE_GOVERNANCE_PLAN_INTEGRITY_MISMATCH")
        if plan.extraction_method == KnowledgeExtractionMethod.legacy_unclassified:
            if (
                plan.rights_status != KnowledgeRightsStatus.review_required
                or plan.ocr_review_status != KnowledgeOcrReviewStatus.pending_review
                or plan.ocr_review_evidence_ref is not None
            ):
                raise ValueError("KNOWLEDGE_LEGACY_CLASSIFICATION_REQUIRED")
        elif plan.extraction_method == KnowledgeExtractionMethod.native_text:
            if (
                plan.ocr_review_status != KnowledgeOcrReviewStatus.not_required
                or plan.ocr_review_evidence_ref is not None
            ):
                raise ValueError("KNOWLEDGE_OCR_POSTURE_INVALID")
        elif plan.ocr_review_status == KnowledgeOcrReviewStatus.not_required:
            raise ValueError("KNOWLEDGE_OCR_POSTURE_INVALID")

    def _validate_prepared_removal(self, prepared: PreparedKnowledgeRemoval) -> None:
        plan = prepared.plan
        if plan.store_ref != self.store_ref:
            raise ValueError("KNOWLEDGE_REMOVAL_STORE_SCOPE_MISMATCH")
        if (
            plan.contract_ref != KNOWLEDGE_DUMP_CONTRACT_REF
            or plan.exact_scope_ref != _removal_scope_ref(plan)
            or plan.plan_ref
            != _hash_ref("knowledge-removal-plan-ref", plan.exact_scope_ref)
            or not plan.approval_required
            or not plan.external_backup_restore_only
            or any(
                (
                    plan.automatic_restore_enabled,
                    plan.network_access_enabled,
                    plan.model_call_enabled,
                    plan.model_training_enabled,
                )
            )
        ):
            raise ValueError("KNOWLEDGE_REMOVAL_PLAN_INTEGRITY_MISMATCH")

    def _require_document(self, document_ref: str) -> KnowledgeDocument:
        if not re.fullmatch(
            r"knowledge-document-ref:sha256:[0-9a-f]{24}", document_ref
        ):
            raise ValueError("KNOWLEDGE_DOCUMENT_REF_INVALID")
        document = next(
            (
                item
                for item in self.list_documents()
                if item.document_ref == document_ref
            ),
            None,
        )
        if document is None:
            raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{document_ref}")
        return document

    @staticmethod
    def _governance_ref_for_document(document: KnowledgeDocument) -> str:
        return _governance_ref(
            lifecycle_state=document.lifecycle_state,
            rights_status=document.rights_status,
            rights_evidence_ref=document.rights_evidence_ref,
            extraction_method=document.extraction_method,
            ocr_review_status=document.ocr_review_status,
            ocr_review_evidence_ref=document.ocr_review_evidence_ref,
        )

    def _document_revision_ref(
        self, connection: sqlite3.Connection, document_ref: str
    ) -> str:
        row = connection.execute(
            "SELECT * FROM documents WHERE document_ref = ?", (document_ref,)
        ).fetchone()
        if row is None:
            raise KeyError(f"UNKNOWN_KNOWLEDGE_DOCUMENT:{document_ref}")
        document = self._document_from_row(row)
        chunks = connection.execute(
            """SELECT chunk_ref, text_ref, ordinal, locator
               FROM chunks WHERE document_ref = ? ORDER BY ordinal""",
            (document_ref,),
        ).fetchall()
        material = {
            "document": document.model_dump(mode="json"),
            "chunks": [dict(chunk) for chunk in chunks],
        }
        return _hash_ref(
            "knowledge-document-revision-ref",
            json.dumps(material, sort_keys=True, separators=(",", ":")),
            40,
        )

    def _initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if stat.S_IMODE(self.root.stat().st_mode) != 0o700:
            os.chmod(self.root, 0o700)
        if not self.database_path.exists():
            flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self.database_path, flags, 0o600)
            os.close(descriptor)
        if self.database_path.is_symlink() or not self.database_path.is_file():
            raise ValueError("KNOWLEDGE_STORE_PATH_UNSAFE")
        if stat.S_IMODE(self.database_path.stat().st_mode) != 0o600:
            os.chmod(self.database_path, 0o600)
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS documents (
                    document_ref TEXT PRIMARY KEY,
                    source_content_ref TEXT NOT NULL UNIQUE,
                    exact_scope_ref TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    rights_basis TEXT NOT NULL,
                    rights_evidence_ref TEXT NOT NULL,
                    rights_status TEXT NOT NULL DEFAULT 'review_required',
                    lifecycle_state TEXT NOT NULL DEFAULT 'active',
                    extraction_method TEXT NOT NULL DEFAULT 'legacy_unclassified',
                    ocr_review_status TEXT NOT NULL DEFAULT 'pending_review',
                    ocr_review_evidence_ref TEXT,
                    catalog_source_id TEXT,
                    catalog_citation_locator_refs_json TEXT NOT NULL DEFAULT '[]',
                    chunk_count INTEGER NOT NULL,
                    character_count INTEGER NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    source_kind TEXT NOT NULL DEFAULT 'reference',
                    category TEXT NOT NULL DEFAULT 'uncategorized',
                    collection TEXT,
                    tags_json TEXT NOT NULL DEFAULT '[]'
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_ref TEXT PRIMARY KEY,
                    document_ref TEXT NOT NULL REFERENCES documents(document_ref) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    locator TEXT NOT NULL,
                    text TEXT NOT NULL,
                    text_ref TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_ref UNINDEXED, text, tokenize='unicode61 remove_diacritics 2'
                );
                CREATE TABLE IF NOT EXISTS metadata_updates (
                    idempotency_key TEXT PRIMARY KEY,
                    exact_scope_ref TEXT NOT NULL,
                    document_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS governance_updates (
                    idempotency_key TEXT PRIMARY KEY,
                    exact_scope_ref TEXT NOT NULL,
                    document_ref TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS document_removals (
                    idempotency_key TEXT PRIMARY KEY,
                    exact_scope_ref TEXT NOT NULL,
                    document_ref TEXT NOT NULL,
                    expected_document_revision_ref TEXT NOT NULL,
                    retention_decision_ref TEXT NOT NULL,
                    backup_disposition_ref TEXT NOT NULL,
                    source_content_ref TEXT NOT NULL,
                    ingest_idempotency_key TEXT NOT NULL,
                    deleted_chunk_count INTEGER NOT NULL,
                    deleted_character_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_records (
                    audit_ref TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    receipt_ref TEXT NOT NULL,
                    exact_scope_ref TEXT NOT NULL,
                    subject_ref TEXT NOT NULL,
                    approval_ref TEXT NOT NULL,
                    actor_ref TEXT NOT NULL,
                    approver_ref TEXT NOT NULL,
                    run_ref TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    mutation_performed INTEGER NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            existing_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(documents)").fetchall()
            }
            additions = {
                "source_kind": "TEXT NOT NULL DEFAULT 'reference'",
                "category": "TEXT NOT NULL DEFAULT 'uncategorized'",
                "collection": "TEXT",
                "tags_json": "TEXT NOT NULL DEFAULT '[]'",
                "catalog_citation_locator_refs_json": "TEXT NOT NULL DEFAULT '[]'",
                "rights_status": "TEXT NOT NULL DEFAULT 'review_required'",
                "lifecycle_state": "TEXT NOT NULL DEFAULT 'active'",
                "extraction_method": "TEXT NOT NULL DEFAULT 'legacy_unclassified'",
                "ocr_review_status": "TEXT NOT NULL DEFAULT 'pending_review'",
                "ocr_review_evidence_ref": "TEXT",
            }
            for name, declaration in additions.items():
                if name not in existing_columns:
                    connection.execute(
                        f"ALTER TABLE documents ADD COLUMN {name} {declaration}"
                    )
            audit_columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(audit_records)"
                ).fetchall()
            }
            if "approver_ref" not in audit_columns:
                connection.execute(
                    "ALTER TABLE audit_records ADD COLUMN approver_ref TEXT NOT NULL "
                    "DEFAULT 'knowledge-approver-ref:legacy-unknown'"
                )
            governance_columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(governance_updates)"
                ).fetchall()
            }
            if "plan_json" not in governance_columns:
                connection.execute(
                    "ALTER TABLE governance_updates ADD COLUMN plan_json TEXT"
                )

    def _require_mutation_policy(
        self,
        *,
        operation: str,
        plan_ref: str,
        exact_scope_ref: str,
        idempotency_key: str,
    ) -> None:
        manifest = CapabilityManifest(
            id=f"knowledge.dump.{operation}",
            version="q18-v2",
            kind=CapabilityKind.tool,
            name=f"knowledge.dump.{operation}",
            description="Policy gate for exact-approved local knowledge mutation.",
            owner="core.knowledge_dump",
            tags=["knowledge", "local", "approval"],
            examples=["Apply one exact-approved local knowledge mutation."],
            anti_examples=["Persist source content without policy and exact approval."],
            input_schema={
                "type": "object",
                "required": ["exact_scope_ref", "idempotency_key"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "required": ["approval_required"],
                "additionalProperties": True,
            },
            input_modes=["safe_ref", "redacted_summary"],
            output_modes=["policy_decision"],
            side_effects=SideEffectLevel.write,
            risk_level=CapabilityRiskLevel.high,
            approval_required=True,
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            single_writer_required=True,
            safety=SafetyPolicy(
                require_single_writer=True,
                approval_required=True,
                max_risk_level=CapabilityRiskLevel.high,
                max_side_effect_level=SideEffectLevel.write,
            ),
        )
        task = TaskEnvelope(
            task_id=f"knowledge-mutation-policy:{plan_ref}",
            user_request=f"Evaluate approval-bound local knowledge {operation} policy.",
            objective="Require policy eligibility before exact approval validation.",
            selected_capability_ids=[manifest.id],
            allowed_tool_ids=[manifest.id],
            context={
                "exact_scope_ref": exact_scope_ref,
                "idempotency_key": idempotency_key,
            },
        )
        decision = self.policy_engine.can_execute(
            manifest,
            task,
            {
                "max_risk_level": self.policy_engine.default_max_risk.value,
                "idempotency_key": idempotency_key,
            },
        )
        if not (
            decision.status == PolicyDecisionStatus.approval_required
            and decision.requires_approval
        ):
            raise PermissionError("KNOWLEDGE_MUTATION_POLICY_DENIED")

    @staticmethod
    def _audit_record(
        *,
        operation: str,
        receipt: (
            KnowledgeIngestReceipt
            | KnowledgeMetadataUpdateReceipt
            | KnowledgeGovernanceUpdateReceipt
            | KnowledgeRemovalReceipt
        ),
        subject_ref: str,
        approver_actor_id: str,
        actor_context: ActorContext,
        run_id: str,
    ) -> KnowledgeAuditRecord:
        actor_ref = _hash_ref("knowledge-actor-ref", actor_context.actor_id)
        approver_ref = _hash_ref("knowledge-approver-ref", approver_actor_id)
        run_ref = _hash_ref("knowledge-run-ref", run_id)
        audit_ref = _hash_ref(
            "knowledge-audit-ref",
            "|".join(
                (
                    operation,
                    receipt.exact_scope_ref,
                    receipt.approval_ref,
                    actor_ref,
                    approver_ref,
                    run_ref,
                )
            ),
        )
        return KnowledgeAuditRecord(
            audit_ref=audit_ref,
            operation=operation,
            receipt_ref=receipt.receipt_ref,
            exact_scope_ref=receipt.exact_scope_ref,
            subject_ref=subject_ref,
            approval_ref=receipt.approval_ref,
            actor_ref=actor_ref,
            approver_ref=approver_ref,
            run_ref=run_ref,
            idempotency_key=receipt.idempotency_key,
            mutation_performed=receipt.mutation_performed,
            reason_codes=receipt.reason_codes,
        )

    @staticmethod
    def _audit_idempotency_replay(
        connection: sqlite3.Connection,
        *,
        operation: str,
        idempotency_key: str,
        exact_scope_ref: str,
        subject_ref: str,
        conflict_code: str,
    ) -> bool:
        rows = connection.execute(
            """SELECT exact_scope_ref, subject_ref FROM audit_records
               WHERE operation = ? AND idempotency_key = ?""",
            (operation, idempotency_key),
        ).fetchall()
        if any(
            row["exact_scope_ref"] != exact_scope_ref
            or row["subject_ref"] != subject_ref
            for row in rows
        ):
            raise ValueError(conflict_code)
        return bool(rows)

    @staticmethod
    def _insert_audit_record(
        connection: sqlite3.Connection, record: KnowledgeAuditRecord
    ) -> None:
        connection.execute(
            """INSERT OR IGNORE INTO audit_records
               (audit_ref, operation, receipt_ref, exact_scope_ref, subject_ref,
                approval_ref, actor_ref, approver_ref, run_ref, idempotency_key,
                mutation_performed, reason_codes_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.audit_ref,
                record.operation,
                record.receipt_ref,
                record.exact_scope_ref,
                record.subject_ref,
                record.approval_ref,
                record.actor_ref,
                record.approver_ref,
                record.run_ref,
                record.idempotency_key,
                int(record.mutation_performed),
                json.dumps(record.reason_codes, separators=(",", ":")),
                record.created_at.isoformat(),
            ),
        )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        if self.root.exists() and stat.S_IMODE(self.root.stat().st_mode) != 0o700:
            raise PermissionError("KNOWLEDGE_STORE_PERMISSIONS_UNSAFE")
        if self.database_path.exists():
            if self.database_path.is_symlink() or not self.database_path.is_file():
                raise ValueError("KNOWLEDGE_STORE_PATH_UNSAFE")
            if stat.S_IMODE(self.database_path.stat().st_mode) != 0o600:
                raise PermissionError("KNOWLEDGE_STORE_PERMISSIONS_UNSAFE")
        connection = sqlite3.connect(self.database_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA secure_delete = ON")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _chunk_sections(
        self, source_content_ref: str, sections: Iterable[ExtractedSection]
    ) -> Iterable[_PreparedChunk]:
        ordinal = 0
        for section in sections:
            start = 0
            while start < len(section.text):
                end = min(len(section.text), start + MAX_CHUNK_CHARACTERS)
                if end < len(section.text):
                    boundary = section.text.rfind(
                        " ", start + MAX_CHUNK_CHARACTERS // 2, end
                    )
                    if boundary > start:
                        end = boundary
                text = section.text[start:end].strip()
                if text:
                    locator = f"{section.locator}#chunk:{ordinal + 1}"
                    text_ref = _hash_ref("knowledge-chunk-content-ref", text, 40)
                    yield _PreparedChunk(
                        chunk_ref=_hash_ref(
                            "knowledge-chunk-ref",
                            f"{source_content_ref}|{ordinal}|{text_ref}",
                        ),
                        locator=locator,
                        text=text,
                        text_ref=text_ref,
                    )
                    ordinal += 1
                if end >= len(section.text):
                    break
                start = max(start + 1, end - CHUNK_OVERLAP_CHARACTERS)

    @staticmethod
    def _validate_catalog_binding(
        *,
        catalog_source_id: str | None,
        catalog_citation_locator_refs: tuple[str, ...],
        rights_basis: KnowledgeRightsBasis | str,
    ) -> None:
        if catalog_source_id is None:
            if catalog_citation_locator_refs:
                raise ValueError("KNOWLEDGE_CITATION_LOCATORS_REQUIRE_CATALOG_SOURCE")
            return
        catalog_source = get_medical_knowledge_source(catalog_source_id)
        if (
            _enum_value(catalog_source.access_class)
            == MedicalSourceAccessClass.licensed_proprietary.value
            and _enum_value(rights_basis)
            != KnowledgeRightsBasis.licensed_for_local_retrieval.value
        ):
            raise ValueError(
                "KNOWLEDGE_PROPRIETARY_SOURCE_REQUIRES_LICENSED_RETRIEVAL_RIGHTS"
            )
        if len(catalog_citation_locator_refs) != len(
            catalog_source.citation_locator_requirements
        ):
            raise ValueError("KNOWLEDGE_MEDICAL_CITATION_LOCATORS_REQUIRED")

    @staticmethod
    def _document_from_row(row: sqlite3.Row) -> KnowledgeDocument:
        keys = set(row.keys())
        return KnowledgeDocument(
            document_ref=row["document_ref"],
            source_content_ref=row["source_content_ref"],
            title=row["title"],
            source_format=row["source_format"],
            rights_basis=row["rights_basis"],
            rights_evidence_ref=row["rights_evidence_ref"],
            rights_status=(
                row["rights_status"] if "rights_status" in keys else "review_required"
            ),
            lifecycle_state=(
                row["lifecycle_state"] if "lifecycle_state" in keys else "active"
            ),
            extraction_method=(
                row["extraction_method"]
                if "extraction_method" in keys
                else "legacy_unclassified"
            ),
            ocr_review_status=(
                row["ocr_review_status"]
                if "ocr_review_status" in keys
                else "pending_review"
            ),
            ocr_review_evidence_ref=(
                row["ocr_review_evidence_ref"]
                if "ocr_review_evidence_ref" in keys
                else None
            ),
            catalog_source_id=row["catalog_source_id"],
            catalog_citation_locator_refs=tuple(
                json.loads(row["catalog_citation_locator_refs_json"])
                if "catalog_citation_locator_refs_json" in keys
                else []
            ),
            source_kind=row["source_kind"] if "source_kind" in keys else "reference",
            category=row["category"] if "category" in keys else "uncategorized",
            collection=row["collection"] if "collection" in keys else None,
            tags=json.loads(row["tags_json"]) if "tags_json" in keys else [],
            chunk_count=row["chunk_count"],
            character_count=row["character_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
