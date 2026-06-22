import re
from typing import Any

from pydantic import BaseModel

from ultimate_ai_agent.core.memory.enums import (
    MemoryAuthorityLevel,
    MemoryDataClassification,
    MemoryProviderKind,
    MemoryRecallEligibility,
    MemorySensitivity,
    MemorySourcePriority,
    MemoryWriteDecisionStatus,
)
from ultimate_ai_agent.core.memory.provider import (
    MemoryExportRequest,
    MemoryWriteRequest,
    build_memory_export_decision,
    build_memory_write_decision,
)
from ultimate_ai_agent.core.memory.records import MemoryLifecycleMetadata, MemoryProvenance, MemoryRecallMetadata, MemoryRecord, MemorySourceRef
from ultimate_ai_agent.core.memory.redaction import memory_contains_secret


SECRET_KEY_FRAGMENTS = ("api_key", "apikey", "secret", "password", "private_key", "authorization", "cookie")
SECRET_KEY_EXACT = {"token", "access_token", "refresh_token", "auth_token", "bearer_token"}
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|private[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token)\b\s*[:=]"
)
UNSAFE_PROVENANCE_KEY_PATTERN = re.compile(
    r"(?i)(raw|prompt|response|provider[_-]?payload|local[_-]?path|"
    r"account[_-]?id|account[_-]?identifier|username|hostname|credential|"
    r"password|token|secret|api[_-]?key|authorization|cookie)"
)
UNSAFE_PROVENANCE_VALUE_PATTERN = re.compile(
    r"(?i)(/users/|/home/|/var/|/etc/|[a-z]:\\|raw[_ -]?prompt|"
    r"raw[_ -]?response|provider[_-]?payload|raw[_ -]?log|account[_ -]?id|"
    r"account identifier|username\s*:|hostname\s*:|credential|password|"
    r"token|secret|api[_-]?key|authorization|cookie)"
)


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def _secret_like(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in SECRET_KEY_EXACT or any(fragment in key_text for fragment in SECRET_KEY_FRAGMENTS):
                return True
            if _secret_like(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_secret_like(item) for item in value)
    if isinstance(value, str) and SECRET_ASSIGNMENT_PATTERN.search(value):
        return True
    return memory_contains_secret({"value": value})


def _unsafe_provenance_like(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if UNSAFE_PROVENANCE_KEY_PATTERN.search(str(key)):
                return True
            if _unsafe_provenance_like(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_unsafe_provenance_like(item) for item in value)
    if isinstance(value, str):
        return bool(UNSAFE_PROVENANCE_VALUE_PATTERN.search(value))
    return False


def validate_memory_record(record: MemoryRecord) -> bool:
    if record.sensitivity == MemorySensitivity.credential_secret:
        raise ValueError("credential_secret memories are rejected by default.")
    if _value(record.authority_level) == MemoryAuthorityLevel.blocked_authority.value:
        raise ValueError("Memory record cannot claim authority.")
    if _value(record.data_classification) == MemoryDataClassification.forbidden.value:
        raise ValueError("Memory record uses forbidden data classification.")
    if _value(record.provider_kind) == MemoryProviderKind.blocked_cloud.value:
        raise ValueError("Cloud-backed memory providers are blocked for M24.")
    if _secret_like(record.model_dump()):
        raise ValueError("Memory record contains secret-like content.")
    return True


def validate_memory_source_ref(source_ref: MemorySourceRef) -> bool:
    if _secret_like(source_ref.model_dump()):
        raise ValueError("Memory source reference contains secret-like content.")
    if _unsafe_provenance_like(source_ref.model_dump()):
        raise ValueError("Memory source reference contains unsafe provenance content.")
    return True


def validate_memory_provenance(provenance: MemoryProvenance) -> bool:
    if _secret_like(provenance.model_dump()):
        raise ValueError("Memory provenance contains secret-like content.")
    if _unsafe_provenance_like(provenance.model_dump()):
        raise ValueError("Memory provenance contains unsafe provenance content.")
    return True


def validate_memory_recall_metadata(recall_metadata: MemoryRecallMetadata) -> bool:
    if _value(recall_metadata.recall_eligibility) == MemoryRecallEligibility.blocked.value:
        raise ValueError("Blocked recall eligibility is not allowed.")
    if _secret_like(recall_metadata.model_dump()):
        raise ValueError("Memory recall metadata contains secret-like content.")
    return True


def validate_memory_lifecycle_metadata(lifecycle: MemoryLifecycleMetadata) -> bool:
    if _secret_like(lifecycle.model_dump()):
        raise ValueError("Memory lifecycle metadata contains secret-like content.")
    return True


def _deny_write(request: MemoryWriteRequest, status: MemoryWriteDecisionStatus, reason: str, message: str) -> Any:
    return build_memory_write_decision(
        request_id=request.request_id,
        allowed=False,
        status=status,
        reason_codes=[reason],
        safe_message=message,
    )


def validate_memory_write_request(request: MemoryWriteRequest) -> Any:
    if request.automatic_write:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "AUTOMATIC_MEMORY_WRITE_BLOCKED", "Automatic memory writes are blocked.")
    if request.model_output_source:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "MODEL_OUTPUT_MEMORY_WRITE_BLOCKED", "Model output cannot write memory in M24.")
    if request.local_llm_output_source:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "LOCAL_LLM_OUTPUT_MEMORY_WRITE_BLOCKED", "Local LLM output cannot write memory in M24.")
    if request.openwebui_source:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "OPENWEBUI_MEMORY_WRITE_BLOCKED", "OpenWebUI cannot write memory in M24.")
    if request.mobile_capture_source:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "MOBILE_CAPTURE_MEMORY_WRITE_BLOCKED", "Mobile capture cannot write memory in M24.")
    if request.tool_output_source:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "TOOL_OUTPUT_MEMORY_WRITE_BLOCKED", "Tool output cannot write memory in M24.")
    if request.contains_secret_like_content:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "SECRET_LIKE_MEMORY_BLOCKED", "Secret-like memory content is blocked.")
    if request.contains_raw_prompt:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "RAW_PROMPT_MEMORY_BLOCKED", "Raw prompts cannot be stored in memory.")
    if request.contains_raw_model_output:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "RAW_MODEL_OUTPUT_MEMORY_BLOCKED", "Raw model output cannot be stored in memory.")
    if request.contains_raw_file_content:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "RAW_FILE_CONTENT_MEMORY_BLOCKED", "Raw file content cannot be stored in memory.")
    if request.contains_raw_transcript:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "RAW_TRANSCRIPT_MEMORY_BLOCKED", "Raw transcripts cannot be stored in memory.")
    if _value(request.data_classification) == MemoryDataClassification.forbidden.value:
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "FORBIDDEN_DATA_CLASSIFICATION", "Forbidden memory classification is blocked.")
    if _secret_like(request.safe_summary):
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "SECRET_LIKE_MEMORY_BLOCKED", "Secret-like memory summaries are blocked.")
    if _secret_like(request.metadata):
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "SECRET_LIKE_METADATA_BLOCKED", "Secret-like memory metadata is blocked.")
    if _secret_like(request.metadata_refs):
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "SECRET_LIKE_METADATA_REF_BLOCKED", "Secret-like memory metadata refs are blocked.")
    if _secret_like(request.tags):
        return _deny_write(request, MemoryWriteDecisionStatus.denied, "SECRET_LIKE_TAG_BLOCKED", "Secret-like memory tags are blocked.")
    if not request.user_reviewed:
        return _deny_write(request, MemoryWriteDecisionStatus.requires_user_review, "USER_REVIEW_REQUIRED", "Reviewed memory record contract is required.")
    if not request.source_refs:
        return _deny_write(request, MemoryWriteDecisionStatus.requires_evidence, "SOURCE_REF_REQUIRED", "M24 source_refs are required; evidence, event, and receipt refs are supplemental provenance.")
    return build_memory_write_decision(
        request_id=request.request_id,
        allowed=True,
        status=MemoryWriteDecisionStatus.allowed_for_local_store,
        reason_codes=["MEMORY_RECALL_NOT_AUTHORITY", "REVIEWED_SOURCE_LINKED_MEMORY_ALLOWED"],
        safe_message="Reviewed source-linked memory accepted as recall, not authority.",
    )


def validate_memory_write_decision(decision: BaseModel) -> bool:
    if _secret_like(decision.model_dump()):
        raise ValueError("Memory write decision contains secret-like content.")
    return True


def validate_memory_delete_request(request: BaseModel | dict) -> bool:
    payload = request.model_dump() if isinstance(request, BaseModel) else request
    if _secret_like(payload):
        raise ValueError("Memory delete request contains secret-like content.")
    return True


def validate_memory_export_request(request: MemoryExportRequest | dict) -> Any:
    export_request = request if isinstance(request, MemoryExportRequest) else MemoryExportRequest(**request)
    if export_request.include_raw_content or not export_request.redacted_only:
        return build_memory_export_decision(
            request_id=export_request.request_id,
            allowed=False,
            status=MemoryWriteDecisionStatus.denied,
            reason_codes=["RAW_MEMORY_EXPORT_BLOCKED"],
            safe_message="Memory export is redacted-summary-only in M24.",
        )
    if _secret_like(export_request.metadata) or _secret_like(export_request.metadata_refs):
        return build_memory_export_decision(
            request_id=export_request.request_id,
            allowed=False,
            status=MemoryWriteDecisionStatus.denied,
            reason_codes=["SECRET_LIKE_METADATA_BLOCKED"],
            safe_message="Secret-like export metadata is blocked.",
        )
    return build_memory_export_decision(
        request_id=export_request.request_id,
        allowed=True,
        status=MemoryWriteDecisionStatus.allowed_for_local_store,
        reason_codes=["REDACTED_MEMORY_EXPORT_ALLOWED"],
        safe_message="Memory export is redacted-summary-only.",
    )


def validate_memory_provider_profile(profile: BaseModel) -> bool:
    payload = profile.model_dump()
    blocked_enabled = [
        "cloud_backed",
        "supports_vector_search",
        "supports_embeddings",
        "supports_automatic_writes",
        "supports_context_injection",
        "supports_background_workers",
        "production_ready",
    ]
    if any(payload.get(field) for field in blocked_enabled):
        raise ValueError("Memory provider profile enables blocked M24 capability.")
    return True


def validate_memory_provider_manifest(manifest: BaseModel) -> bool:
    payload = manifest.model_dump()
    blocked_enabled = [
        "cloud_providers_enabled",
        "vector_search_enabled",
        "embeddings_enabled",
        "automatic_writes_enabled",
        "recall_injection_enabled",
        "context_pack_injection_enabled",
        "auto_decay_enabled",
        "background_workers_enabled",
    ]
    if any(payload.get(field) for field in blocked_enabled):
        raise ValueError("Memory provider manifest enables blocked M24 capability.")
    return True


def assert_memory_recall_not_authority(record: MemoryRecord) -> bool:
    if _value(record.authority_level) == MemoryAuthorityLevel.blocked_authority.value:
        raise ValueError("Memory is recall, not authority.")
    return True


def assert_source_priority_does_not_make_memory_authority(record: MemoryRecord) -> bool:
    if _value(record.source_priority) == MemorySourcePriority.blocked.value:
        raise ValueError("Blocked memory source priority is not allowed.")
    assert_memory_recall_not_authority(record)
    return True


def assert_no_secret_memory_content(payload: Any) -> bool:
    if _secret_like(payload):
        raise ValueError("Memory payload contains secret-like content.")
    return True


def assert_no_automatic_memory_write(request: MemoryWriteRequest) -> bool:
    if request.automatic_write:
        raise ValueError("Automatic memory writes are blocked.")
    return True


def assert_no_model_output_write(request: MemoryWriteRequest) -> bool:
    if request.model_output_source:
        raise ValueError("Model output memory writes are blocked.")
    return True


def assert_no_local_llm_output_write(request: MemoryWriteRequest) -> bool:
    if request.local_llm_output_source:
        raise ValueError("Local LLM output memory writes are blocked.")
    return True


def assert_no_openwebui_memory_write(request: MemoryWriteRequest) -> bool:
    if request.openwebui_source:
        raise ValueError("OpenWebUI memory writes are blocked.")
    return True


def assert_no_mobile_capture_memory_write(request: MemoryWriteRequest) -> bool:
    if request.mobile_capture_source:
        raise ValueError("Mobile capture memory writes are blocked.")
    return True


def assert_no_tool_output_memory_write(request: MemoryWriteRequest) -> bool:
    if request.tool_output_source:
        raise ValueError("Tool output memory writes are blocked.")
    return True


def assert_no_vector_or_embedding_memory(manifest: BaseModel) -> bool:
    payload = manifest.model_dump()
    if payload.get("vector_search_enabled") or payload.get("embeddings_enabled"):
        raise ValueError("Vector or embedding memory is blocked.")
    return True


def assert_no_context_injection_runtime(manifest: BaseModel) -> bool:
    payload = manifest.model_dump()
    if payload.get("recall_injection_enabled") or payload.get("context_pack_injection_enabled"):
        raise ValueError("Context injection runtime is blocked.")
    return True


def assert_no_background_memory_workers(manifest: BaseModel) -> bool:
    if manifest.model_dump().get("background_workers_enabled"):
        raise ValueError("Background memory workers are blocked.")
    return True
