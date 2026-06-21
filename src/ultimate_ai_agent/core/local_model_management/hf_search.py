from __future__ import annotations

import json
from typing import Any, Protocol
from urllib import parse, request

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _SECRET_LIKE_RE,
    _URL_RE,
    _validate_m61_ref,
    _validate_safe_payload,
)


HF_MODELS_API_URL = "https://huggingface.co/api/models"
HF_MODELS_API_HOST = "huggingface.co"
M160_DEFAULT_RESULT_LIMIT = 10
M160_MAX_RESULT_LIMIT = 20
M160_MAX_RESPONSE_BYTES = 512_000


class _M160Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class M160HuggingFaceGgufSearchPolicy(_M160Model):
    policy_ref: str = "hf-gguf-search-policy:m160"
    bounded_read_only: bool = True
    unauthenticated_only: bool = True
    https_get_only: bool = True
    metadata_only: bool = True
    gguf_candidates_only: bool = True
    raw_response_storage_allowed: bool = False
    request_body_allowed: bool = False
    custom_headers_allowed: bool = False
    token_use_allowed: bool = False
    download_allowed: bool = False
    model_call_allowed: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class M160HuggingFaceGgufSearchRequest(_M160Model):
    request_ref: str
    query: str
    task_ref: str = "task:text-generation"
    limit: int = Field(default=M160_DEFAULT_RESULT_LIMIT, ge=1, le=M160_MAX_RESULT_LIMIT)
    include_gated: bool = False
    policy_ref: str = "hf-gguf-search-policy:m160"
    audit_ref: str = "audit:m160-hf-gguf-search"
    replay_ref: str = "replay:m160-hf-gguf-search"
    receipt_plan_ref: str = "receipt-plan:m160-hf-gguf-search"
    authenticated_request_requested: bool = False
    token_use_requested: bool = False
    download_requested: bool = False
    raw_response_requested: bool = False
    model_call_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.task_ref, "task_ref"),
            (self.policy_ref, "policy_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_m160_query(self.query)
        _validate_safe_payload(self.metadata)
        return self


class M160HuggingFaceGgufFileCandidate(_M160Model):
    filename: str
    size_bytes: int | None = Field(default=None, ge=0)
    quantization_ref: str = "quant:unknown"
    file_ref: str

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_remote_filename(self.filename)
        _validate_m61_ref(self.quantization_ref, "quantization_ref")
        _validate_m61_ref(self.file_ref, "file_ref")
        return self


class M160HuggingFaceGgufModelCandidate(_M160Model):
    candidate_ref: str
    repo_id: str
    revision: str = "main"
    task_ref: str
    license_ref: str = "license:unknown"
    gated: bool = False
    downloads: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    last_modified_ref: str = "last-modified:unknown"
    gguf_files: list[M160HuggingFaceGgufFileCandidate]
    tags: list[str] = Field(default_factory=list)
    provenance_ref: str = "provenance:hugging-face-public-metadata"

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.candidate_ref, "candidate_ref")
        _validate_repo_id(self.repo_id)
        _validate_safe_text(self.revision, "revision", max_length=96)
        _validate_m61_ref(self.task_ref, "task_ref")
        _validate_m61_ref(self.license_ref, "license_ref")
        _validate_m61_ref(self.last_modified_ref, "last_modified_ref")
        _validate_m61_ref(self.provenance_ref, "provenance_ref")
        if not self.gguf_files:
            raise ValueError("M160_GGUF_FILE_REQUIRED")
        for tag in self.tags:
            _validate_safe_text(tag, "tag", max_length=80)
        return self


class M160HuggingFaceGgufSearchResult(_M160Model):
    result_ref: str
    request_ref: str
    query: str
    candidates: list[M160HuggingFaceGgufModelCandidate]
    candidate_refs: list[str]
    live_search_performed: bool = True
    network_access_performed: bool = True
    https_get_only: bool = True
    unauthenticated: bool = True
    metadata_only: bool = True
    raw_response_stored: bool = False
    request_body_sent: bool = False
    custom_headers_sent: bool = False
    token_used: bool = False
    download_performed: bool = False
    model_file_read_performed: bool = False
    model_call_performed: bool = False
    prompt_processed: bool = False
    backend_route_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    safe_summary: str = "Bounded Hugging Face GGUF metadata search completed."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.result_ref, "result_ref")
        _validate_m61_ref(self.request_ref, "request_ref")
        _validate_m160_query(self.query)
        if [candidate.candidate_ref for candidate in self.candidates] != self.candidate_refs:
            raise ValueError("M160_CANDIDATE_REFS_MISMATCH")
        for ref in self.candidate_refs:
            _validate_m61_ref(ref, "candidate_ref")
        _validate_safe_text(self.safe_summary, "safe_summary", max_length=240)
        return self


class M160HuggingFaceSearchTransport(Protocol):
    def fetch_model_search(self, search_request: M160HuggingFaceGgufSearchRequest) -> Any:
        ...


class FakeM160HuggingFaceSearchTransport:
    def __init__(self, payload: Any) -> None:
        self.payload = payload
        self.calls: list[M160HuggingFaceGgufSearchRequest] = []

    def fetch_model_search(self, search_request: M160HuggingFaceGgufSearchRequest) -> Any:
        self.calls.append(search_request)
        return self.payload


class StdlibM160HuggingFaceSearchTransport:
    def __init__(self, *, timeout_seconds: float = 10.0, max_response_bytes: int = M160_MAX_RESPONSE_BYTES) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes

    def fetch_model_search(self, search_request: M160HuggingFaceGgufSearchRequest) -> Any:
        url = build_m160_huggingface_search_url(search_request)
        parsed = parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != HF_MODELS_API_HOST or parsed.path != "/api/models":
            raise ValueError("M160_HF_SEARCH_URL_DENIED")
        with request.urlopen(url, timeout=self.timeout_seconds) as response:
            final_url = getattr(response, "url", url)
            final = parse.urlparse(final_url)
            if final.scheme != "https" or final.netloc != HF_MODELS_API_HOST:
                raise ValueError("M160_HF_SEARCH_REDIRECT_DENIED")
            status = getattr(response, "status", 200)
            if status != 200:
                raise ValueError("M160_HF_SEARCH_HTTP_STATUS_DENIED")
            raw = response.read(self.max_response_bytes + 1)
        if len(raw) > self.max_response_bytes:
            raise ValueError("M160_HF_SEARCH_RESPONSE_TOO_LARGE")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("M160_HF_SEARCH_JSON_REQUIRED") from exc


def build_m160_huggingface_search_url(search_request: M160HuggingFaceGgufSearchRequest) -> str:
    validated = validate_m160_huggingface_gguf_search_request(search_request)
    query = {
        "search": validated.query,
        "filter": "gguf",
        "limit": str(validated.limit),
        "full": "true",
        "sort": "downloads",
        "direction": "-1",
    }
    return f"{HF_MODELS_API_URL}?{parse.urlencode(query)}"


def search_huggingface_gguf_models(
    search_request: M160HuggingFaceGgufSearchRequest,
    *,
    transport: M160HuggingFaceSearchTransport | None = None,
) -> M160HuggingFaceGgufSearchResult:
    validated_request = validate_m160_huggingface_gguf_search_request(search_request)
    active_transport = transport or StdlibM160HuggingFaceSearchTransport()
    payload = active_transport.fetch_model_search(validated_request)
    candidates = _parse_hf_model_payload(payload, validated_request)
    candidates = sorted(
        candidates,
        key=lambda candidate: (
            -candidate.downloads,
            -candidate.likes,
            candidate.repo_id.lower(),
            candidate.gguf_files[0].filename.lower(),
        ),
    )[: validated_request.limit]
    return validate_m160_huggingface_gguf_search_result(
        M160HuggingFaceGgufSearchResult(
            result_ref=f"hf-gguf-search-result:m160-{_safe_slug(validated_request.query)}",
            request_ref=validated_request.request_ref,
            query=validated_request.query,
            candidates=candidates,
            candidate_refs=[candidate.candidate_ref for candidate in candidates],
        )
    )


def validate_m160_huggingface_gguf_search_policy(
    policy: M160HuggingFaceGgufSearchPolicy,
) -> M160HuggingFaceGgufSearchPolicy:
    validated = M160HuggingFaceGgufSearchPolicy.model_validate(policy.model_dump())
    for field_name, reason in [
        ("bounded_read_only", "M160_BOUNDED_READ_ONLY_REQUIRED"),
        ("unauthenticated_only", "M160_UNAUTHENTICATED_ONLY_REQUIRED"),
        ("https_get_only", "M160_HTTPS_GET_ONLY_REQUIRED"),
        ("metadata_only", "M160_METADATA_ONLY_REQUIRED"),
        ("gguf_candidates_only", "M160_GGUF_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("raw_response_storage_allowed", "M160_RAW_RESPONSE_STORAGE_DENIED"),
        ("request_body_allowed", "M160_REQUEST_BODY_DENIED"),
        ("custom_headers_allowed", "M160_CUSTOM_HEADERS_DENIED"),
        ("token_use_allowed", "M160_TOKEN_USE_DENIED"),
        ("download_allowed", "M160_DOWNLOAD_DENIED"),
        ("model_call_allowed", "M160_MODEL_CALL_DENIED"),
        ("dependency_added", "M160_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M160_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m160_huggingface_gguf_search_request(
    search_request: M160HuggingFaceGgufSearchRequest,
) -> M160HuggingFaceGgufSearchRequest:
    validated = M160HuggingFaceGgufSearchRequest.model_validate(search_request.model_dump())
    for field_name, reason in [
        ("authenticated_request_requested", "M160_AUTHENTICATED_REQUEST_DENIED"),
        ("token_use_requested", "M160_TOKEN_USE_DENIED"),
        ("download_requested", "M160_DOWNLOAD_DENIED"),
        ("raw_response_requested", "M160_RAW_RESPONSE_STORAGE_DENIED"),
        ("model_call_requested", "M160_MODEL_CALL_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m160_huggingface_gguf_search_result(
    result: M160HuggingFaceGgufSearchResult,
) -> M160HuggingFaceGgufSearchResult:
    validated = M160HuggingFaceGgufSearchResult.model_validate(result.model_dump())
    for field_name, reason in [
        ("live_search_performed", "M160_LIVE_SEARCH_PERFORMED_REQUIRED"),
        ("network_access_performed", "M160_NETWORK_ACCESS_PERFORMED_REQUIRED"),
        ("https_get_only", "M160_HTTPS_GET_ONLY_REQUIRED"),
        ("unauthenticated", "M160_UNAUTHENTICATED_ONLY_REQUIRED"),
        ("metadata_only", "M160_METADATA_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("raw_response_stored", "M160_RAW_RESPONSE_STORAGE_DENIED"),
        ("request_body_sent", "M160_REQUEST_BODY_DENIED"),
        ("custom_headers_sent", "M160_CUSTOM_HEADERS_DENIED"),
        ("token_used", "M160_TOKEN_USE_DENIED"),
        ("download_performed", "M160_DOWNLOAD_DENIED"),
        ("model_file_read_performed", "M160_MODEL_FILE_READ_DENIED"),
        ("model_call_performed", "M160_MODEL_CALL_DENIED"),
        ("prompt_processed", "M160_PROMPT_PROCESSING_DENIED"),
        ("backend_route_added", "M160_BACKEND_ROUTE_DENIED"),
        ("dependency_added", "M160_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M160_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def _parse_hf_model_payload(
    payload: Any,
    search_request: M160HuggingFaceGgufSearchRequest,
) -> list[M160HuggingFaceGgufModelCandidate]:
    if not isinstance(payload, list):
        raise ValueError("M160_HF_SEARCH_LIST_PAYLOAD_REQUIRED")
    candidates: list[M160HuggingFaceGgufModelCandidate] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        repo_id = item.get("id") or item.get("modelId")
        if not isinstance(repo_id, str):
            continue
        gated_value = item.get("gated", False)
        gated = bool(gated_value) and gated_value != "false"
        if gated and not search_request.include_gated:
            continue
        siblings = item.get("siblings")
        if not isinstance(siblings, list):
            siblings = []
        files = _gguf_files_from_siblings(repo_id, siblings)
        if not files:
            continue
        tags = [tag for tag in item.get("tags", []) if isinstance(tag, str)]
        license_ref = _license_ref_from_item(item, tags)
        last_modified_ref = _last_modified_ref(item.get("lastModified"))
        revision = item.get("sha") if isinstance(item.get("sha"), str) else "main"
        candidates.append(
            M160HuggingFaceGgufModelCandidate(
                candidate_ref=f"hf-gguf-candidate:m160-{_safe_slug(repo_id)}",
                repo_id=repo_id,
                revision=revision,
                task_ref=search_request.task_ref,
                license_ref=license_ref,
                gated=gated,
                downloads=_nonnegative_int(item.get("downloads")),
                likes=_nonnegative_int(item.get("likes")),
                last_modified_ref=last_modified_ref,
                gguf_files=files,
                tags=sorted(_safe_tag_subset(tags))[:20],
            )
        )
    return candidates


def _gguf_files_from_siblings(
    repo_id: str,
    siblings: list[Any],
) -> list[M160HuggingFaceGgufFileCandidate]:
    files: list[M160HuggingFaceGgufFileCandidate] = []
    for sibling in siblings:
        if not isinstance(sibling, dict):
            continue
        filename = sibling.get("rfilename") or sibling.get("path")
        if not isinstance(filename, str) or not filename.lower().endswith(".gguf"):
            continue
        try:
            _validate_remote_filename(filename)
        except ValueError:
            continue
        files.append(
            M160HuggingFaceGgufFileCandidate(
                filename=filename,
                size_bytes=_optional_nonnegative_int(sibling.get("size")),
                quantization_ref=_quantization_ref(filename),
                file_ref=f"hf-gguf-file:m160-{_safe_slug(repo_id)}-{_safe_slug(filename)}",
            )
        )
    return sorted(files, key=lambda file: (file.size_bytes is None, file.size_bytes or 0, file.filename.lower()))


def _license_ref_from_item(item: dict[str, Any], tags: list[str]) -> str:
    card_data = item.get("cardData")
    license_value = None
    if isinstance(card_data, dict) and isinstance(card_data.get("license"), str):
        license_value = card_data["license"]
    if license_value is None:
        for tag in tags:
            if tag.startswith("license:"):
                license_value = tag.split(":", 1)[1]
                break
    if license_value is None:
        return "license:unknown"
    return f"license:{_safe_slug(license_value)}"


def _last_modified_ref(value: Any) -> str:
    if not isinstance(value, str):
        return "last-modified:unknown"
    safe_value = value.split("T", 1)[0]
    return f"last-modified:{_safe_slug(safe_value)}"


def _quantization_ref(filename: str) -> str:
    lowered = filename.lower()
    for marker in ["q2", "q3", "q4", "q5", "q6", "q8", "f16", "bf16"]:
        if marker in lowered:
            return f"quant:{marker}"
    return "quant:unknown"


def _safe_tag_subset(tags: list[str]) -> list[str]:
    safe_tags: list[str] = []
    for tag in tags:
        try:
            _validate_safe_text(tag, "tag", max_length=80)
        except ValueError:
            continue
        safe_tags.append(tag)
    return safe_tags


def _validate_m160_query(query: str) -> None:
    _validate_safe_text(query, "query", max_length=120)
    if _URL_RE.search(query):
        raise ValueError("M160_QUERY_MUST_BE_INERT_TEXT")
    if query.startswith(("/", "~")) or "\\" in query or ".." in query:
        raise ValueError("M160_QUERY_MUST_BE_INERT_TEXT")


def _validate_repo_id(repo_id: str) -> None:
    _validate_safe_text(repo_id, "repo_id", max_length=160)
    if repo_id.startswith("/") or repo_id.endswith("/") or "//" in repo_id or ".." in repo_id:
        raise ValueError("M160_REPO_ID_UNSAFE")


def _validate_remote_filename(filename: str) -> None:
    _validate_safe_text(filename, "filename", max_length=220)
    if not filename.lower().endswith(".gguf"):
        raise ValueError("M160_GGUF_FILENAME_REQUIRED")
    if filename.startswith("/") or filename.startswith("~") or ".." in filename:
        raise ValueError("M160_REMOTE_FILENAME_UNSAFE")


def _validate_safe_text(value: str, field_name: str, *, max_length: int) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long")
    if _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)


def _optional_nonnegative_int(value: Any) -> int | None:
    if value is None:
        return None
    return _nonnegative_int(value)


def _nonnegative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


def _safe_slug(value: str) -> str:
    lowered = value.strip().lower()
    slug = re_sub_unsafe(lowered)
    return slug.strip("-") or "unknown"


def re_sub_unsafe(value: str) -> str:
    safe_chars = []
    for char in value:
        if char.isalnum() or char in {"-", ".", "_"}:
            safe_chars.append(char)
        elif char in {"/", " ", ":", "@"}:
            safe_chars.append("-")
    return "".join(safe_chars)[:96]
