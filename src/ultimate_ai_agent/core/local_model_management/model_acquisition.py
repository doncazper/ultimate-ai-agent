from __future__ import annotations

import hashlib
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Protocol
from urllib import parse, request

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.local_model_management.contracts import (
    _SECRET_LIKE_RE,
    _URL_RE,
    _validate_m61_ref,
    _validate_safe_payload,
)


HF_MODEL_RESOLVE_URL_PREFIX = "https://huggingface.co"
HF_MODEL_RESOLVE_HOST = "huggingface.co"
M162_DEFAULT_MAX_ARTIFACT_BYTES = 32 * 1024 * 1024 * 1024
M162_MIN_CHUNK_BYTES = 64 * 1024
M162_DEFAULT_CHUNK_BYTES = 1024 * 1024
M162_MAX_ARTIFACTS_PER_REQUEST = 32
M162_ALLOWED_REDIRECT_HOST_SUFFIXES = (
    "huggingface.co",
    ".huggingface.co",
    ".hf.co",
)


class ArtifactRole(str, Enum):
    primary = "primary"
    shard = "shard"
    mmproj = "mmproj"


class _M162Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class M162ModelAcquisitionPolicy(_M162Model):
    policy_ref: str = "model-acquisition-policy:m162"
    exact_user_approval_required: bool = True
    pinned_revision_required: bool = True
    exact_filename_required: bool = True
    explicit_artifact_refs_required: bool = True
    uaa_owned_cache_required: bool = True
    gguf_artifacts_only: bool = True
    sharded_artifacts_explicit_only: bool = True
    mmproj_artifacts_explicit_only: bool = True
    unauthenticated_by_default: bool = True
    https_get_only: bool = True
    raw_response_storage_allowed: bool = False
    raw_url_storage_allowed: bool = False
    token_use_allowed: bool = False
    request_body_allowed: bool = False
    model_call_allowed: bool = False
    llama_cpp_process_allowed: bool = False
    subprocess_allowed: bool = False
    backend_route_allowed: bool = False
    control_center_control_allowed: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class M162GgufArtifactRequest(_M162Model):
    artifact_ref: str
    repo_id: str
    revision: str
    filename: str
    role: ArtifactRole = ArtifactRole.primary
    expected_size_bytes: int | None = Field(default=None, ge=0)
    expected_sha256: str | None = None
    license_ref: str = "license:unknown"
    provenance_ref: str = "provenance:hugging-face-public-artifact"

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.artifact_ref, "artifact_ref")
        _validate_repo_id(self.repo_id)
        _validate_pinned_revision(self.revision)
        _validate_remote_gguf_filename(self.filename)
        _validate_m61_ref(self.license_ref, "license_ref")
        _validate_m61_ref(self.provenance_ref, "provenance_ref")
        if self.expected_sha256 is not None:
            _validate_sha256(self.expected_sha256)
        basename = self.filename.rsplit("/", 1)[-1].lower()
        if self.role == ArtifactRole.mmproj and not basename.startswith("mmproj"):
            raise ValueError("M162_MMPROJ_FILENAME_REQUIRED")
        if self.role == ArtifactRole.shard and "-of-" not in basename:
            raise ValueError("M162_SHARDED_FILENAME_REQUIRED")
        return self


class M162ModelAcquisitionRequest(_M162Model):
    request_ref: str
    actor_ref: str = "actor:local-user"
    approval_ref: str
    cache_ref: str = "uaa-model-cache:m162-local"
    artifacts: list[M162GgufArtifactRequest]
    policy_ref: str = "model-acquisition-policy:m162"
    audit_ref: str = "audit:m162-model-acquisition"
    replay_ref: str = "replay:m162-model-acquisition"
    receipt_plan_ref: str = "receipt-plan:m162-model-acquisition"
    user_approved: bool = True
    exact_artifacts_only: bool = True
    unauthenticated: bool = True
    token_use_requested: bool = False
    authenticated_request_requested: bool = False
    model_call_requested: bool = False
    llama_cpp_process_requested: bool = False
    subprocess_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.approval_ref, "approval_ref"),
            (self.cache_ref, "cache_ref"),
            (self.policy_ref, "policy_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_m162_approval_ref(self.approval_ref)
        if not self.artifacts:
            raise ValueError("M162_ARTIFACTS_REQUIRED")
        if len(self.artifacts) > M162_MAX_ARTIFACTS_PER_REQUEST:
            raise ValueError("M162_TOO_MANY_ARTIFACTS")
        seen_refs: set[str] = set()
        seen_exact_artifacts: set[tuple[str, str, str]] = set()
        has_model_artifact = False
        for artifact in self.artifacts:
            if artifact.artifact_ref in seen_refs:
                raise ValueError("M162_DUPLICATE_ARTIFACT_REF")
            seen_refs.add(artifact.artifact_ref)
            exact_key = (artifact.repo_id, artifact.revision, artifact.filename)
            if exact_key in seen_exact_artifacts:
                raise ValueError("M162_DUPLICATE_EXACT_ARTIFACT")
            seen_exact_artifacts.add(exact_key)
            if artifact.role in {ArtifactRole.primary, ArtifactRole.shard}:
                has_model_artifact = True
        if not has_model_artifact:
            raise ValueError("M162_MODEL_ARTIFACT_REQUIRED")
        _validate_safe_payload(self.metadata)
        return self


class M162ArtifactTransferReceipt(_M162Model):
    artifact_ref: str
    bytes_written: int = Field(ge=0)
    sha256: str
    final_host_ref: str = "host:hugging-face"
    network_access_performed: bool = True
    https_get_only: bool = True
    raw_response_stored: bool = False
    raw_url_stored: bool = False
    token_used: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.artifact_ref, "artifact_ref")
        _validate_sha256(self.sha256)
        _validate_m61_ref(self.final_host_ref, "final_host_ref")
        return self


class M162AcquiredArtifactReceipt(_M162Model):
    artifact_ref: str
    repo_id: str
    revision: str
    filename: str
    role: ArtifactRole
    cache_artifact_ref: str
    size_bytes: int = Field(ge=0)
    sha256_ref: str
    cache_hit: bool = False
    download_performed: bool = True
    cache_write_performed: bool = True
    network_access_performed: bool = True
    local_path_included: bool = False
    raw_url_included: bool = False
    raw_response_stored: bool = False
    token_used: bool = False
    model_file_read_performed: bool = False
    model_call_performed: bool = False
    llama_cpp_process_started: bool = False
    subprocess_execution_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.artifact_ref, "artifact_ref")
        _validate_repo_id(self.repo_id)
        _validate_pinned_revision(self.revision)
        _validate_remote_gguf_filename(self.filename)
        _validate_m61_ref(self.cache_artifact_ref, "cache_artifact_ref")
        if not self.sha256_ref.startswith("sha256:"):
            raise ValueError("M162_SHA256_REF_REQUIRED")
        _validate_sha256(self.sha256_ref.split(":", 1)[1])
        return self


class M162ModelAcquisitionResult(_M162Model):
    result_ref: str
    request_ref: str
    approval_ref: str
    cache_ref: str
    artifact_receipts: list[M162AcquiredArtifactReceipt]
    artifact_refs: list[str]
    exact_user_approved: bool = True
    exact_artifacts_only: bool = True
    uaa_owned_cache: bool = True
    pinned_revision_used: bool = True
    unauthenticated: bool = True
    https_get_only: bool = True
    download_performed: bool = True
    cache_write_performed: bool = True
    network_access_performed: bool = True
    raw_response_stored: bool = False
    raw_url_stored: bool = False
    local_path_included: bool = False
    token_used: bool = False
    request_body_sent: bool = False
    model_file_read_performed: bool = False
    model_call_performed: bool = False
    prompt_processed: bool = False
    llama_cpp_process_started: bool = False
    subprocess_execution_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    safe_summary: str = "Exact approved GGUF artifacts were acquired into the UAA-owned cache."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.result_ref, "result_ref")
        _validate_m61_ref(self.request_ref, "request_ref")
        _validate_m61_ref(self.approval_ref, "approval_ref")
        _validate_m61_ref(self.cache_ref, "cache_ref")
        if [receipt.artifact_ref for receipt in self.artifact_receipts] != self.artifact_refs:
            raise ValueError("M162_ARTIFACT_REFS_MISMATCH")
        for artifact_ref in self.artifact_refs:
            _validate_m61_ref(artifact_ref, "artifact_ref")
        _validate_safe_text(self.safe_summary, "safe_summary", max_length=240)
        return self


class M162ModelAcquisitionTransport(Protocol):
    def fetch_artifact(
        self,
        artifact: M162GgufArtifactRequest,
        *,
        destination_path: Path,
        max_bytes: int,
    ) -> M162ArtifactTransferReceipt:
        ...


class FakeM162ModelAcquisitionTransport:
    def __init__(self, payload_by_artifact_ref: dict[str, bytes]) -> None:
        self.payload_by_artifact_ref = payload_by_artifact_ref
        self.calls: list[M162GgufArtifactRequest] = []

    def fetch_artifact(
        self,
        artifact: M162GgufArtifactRequest,
        *,
        destination_path: Path,
        max_bytes: int,
    ) -> M162ArtifactTransferReceipt:
        self.calls.append(artifact)
        try:
            payload = self.payload_by_artifact_ref[artifact.artifact_ref]
        except KeyError as exc:
            raise ValueError("M162_FAKE_ARTIFACT_PAYLOAD_MISSING") from exc
        if len(payload) > max_bytes:
            raise ValueError("M162_ARTIFACT_TOO_LARGE")
        destination_path.write_bytes(payload)
        return M162ArtifactTransferReceipt(
            artifact_ref=artifact.artifact_ref,
            bytes_written=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            final_host_ref="host:fake-hugging-face",
        )


class StdlibM162HuggingFaceArtifactTransport:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        chunk_bytes: int = M162_DEFAULT_CHUNK_BYTES,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.chunk_bytes = max(chunk_bytes, M162_MIN_CHUNK_BYTES)

    def fetch_artifact(
        self,
        artifact: M162GgufArtifactRequest,
        *,
        destination_path: Path,
        max_bytes: int,
    ) -> M162ArtifactTransferReceipt:
        url = build_m162_huggingface_resolve_url(artifact)
        parsed = parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != HF_MODEL_RESOLVE_HOST:
            raise ValueError("M162_HF_RESOLVE_URL_DENIED")
        sha = hashlib.sha256()
        total = 0
        with request.urlopen(url, timeout=self.timeout_seconds) as response:
            final_url = getattr(response, "url", url)
            final = parse.urlparse(final_url)
            if final.scheme != "https" or not _allowed_m162_redirect_host(final.netloc):
                raise ValueError("M162_HF_RESOLVE_REDIRECT_DENIED")
            status = getattr(response, "status", 200)
            if status != 200:
                raise ValueError("M162_HF_RESOLVE_HTTP_STATUS_DENIED")
            with destination_path.open("wb") as handle:
                while True:
                    chunk = response.read(self.chunk_bytes)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("M162_ARTIFACT_TOO_LARGE")
                    sha.update(chunk)
                    handle.write(chunk)
        return M162ArtifactTransferReceipt(
            artifact_ref=artifact.artifact_ref,
            bytes_written=total,
            sha256=sha.hexdigest(),
            final_host_ref=f"host:{_safe_slug(final.netloc)}",
        )


def default_m162_model_cache_root(base_dir: Path | None = None) -> Path:
    base = base_dir or Path.cwd()
    return base / ".uaa" / "model-cache"


def build_m162_huggingface_resolve_url(artifact: M162GgufArtifactRequest) -> str:
    validated = M162GgufArtifactRequest.model_validate(artifact.model_dump())
    repo = _quote_slash_path(validated.repo_id)
    revision = parse.quote(validated.revision, safe="")
    filename = _quote_slash_path(validated.filename)
    return f"{HF_MODEL_RESOLVE_URL_PREFIX}/{repo}/resolve/{revision}/{filename}"


def acquire_huggingface_gguf_artifacts(
    acquisition_request: M162ModelAcquisitionRequest,
    *,
    cache_root: Path | None = None,
    transport: M162ModelAcquisitionTransport | None = None,
    max_artifact_bytes: int = M162_DEFAULT_MAX_ARTIFACT_BYTES,
) -> M162ModelAcquisitionResult:
    validated_request = validate_m162_model_acquisition_request(acquisition_request)
    policy = validate_m162_model_acquisition_policy(M162ModelAcquisitionPolicy())
    if not policy.unauthenticated_by_default:
        raise ValueError("M162_UNAUTHENTICATED_DEFAULT_REQUIRED")
    active_cache_root = validate_m162_cache_root(cache_root or default_m162_model_cache_root())
    active_cache_root.mkdir(parents=True, exist_ok=True)
    active_transport = transport or StdlibM162HuggingFaceArtifactTransport()
    receipts: list[M162AcquiredArtifactReceipt] = []
    for artifact in validated_request.artifacts:
        receipt = _acquire_one_artifact(
            artifact,
            cache_root=active_cache_root,
            cache_ref=validated_request.cache_ref,
            transport=active_transport,
            max_artifact_bytes=max_artifact_bytes,
        )
        receipts.append(receipt)
    return validate_m162_model_acquisition_result(
        M162ModelAcquisitionResult(
            result_ref=f"model-acquisition-result:m162-{_safe_suffix(validated_request.request_ref)}",
            request_ref=validated_request.request_ref,
            approval_ref=validated_request.approval_ref,
            cache_ref=validated_request.cache_ref,
            artifact_receipts=receipts,
            artifact_refs=[receipt.artifact_ref for receipt in receipts],
        )
    )


def validate_m162_model_acquisition_policy(
    policy: M162ModelAcquisitionPolicy,
) -> M162ModelAcquisitionPolicy:
    validated = M162ModelAcquisitionPolicy.model_validate(policy.model_dump())
    for field_name, reason in [
        ("exact_user_approval_required", "M162_EXACT_USER_APPROVAL_REQUIRED"),
        ("pinned_revision_required", "M162_PINNED_REVISION_REQUIRED"),
        ("exact_filename_required", "M162_EXACT_FILENAME_REQUIRED"),
        ("explicit_artifact_refs_required", "M162_EXPLICIT_ARTIFACT_REFS_REQUIRED"),
        ("uaa_owned_cache_required", "M162_UAA_CACHE_REQUIRED"),
        ("gguf_artifacts_only", "M162_GGUF_ONLY_REQUIRED"),
        ("sharded_artifacts_explicit_only", "M162_SHARDS_EXPLICIT_REQUIRED"),
        ("mmproj_artifacts_explicit_only", "M162_MMPROJ_EXPLICIT_REQUIRED"),
        ("unauthenticated_by_default", "M162_UNAUTHENTICATED_DEFAULT_REQUIRED"),
        ("https_get_only", "M162_HTTPS_GET_ONLY_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("raw_response_storage_allowed", "M162_RAW_RESPONSE_STORAGE_DENIED"),
        ("raw_url_storage_allowed", "M162_RAW_URL_STORAGE_DENIED"),
        ("token_use_allowed", "M162_TOKEN_USE_DENIED"),
        ("request_body_allowed", "M162_REQUEST_BODY_DENIED"),
        ("model_call_allowed", "M162_MODEL_CALL_DENIED"),
        ("llama_cpp_process_allowed", "M162_LLAMA_CPP_PROCESS_DENIED"),
        ("subprocess_allowed", "M162_SUBPROCESS_DENIED"),
        ("backend_route_allowed", "M162_BACKEND_ROUTE_DENIED"),
        ("control_center_control_allowed", "M162_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M162_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M162_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m162_model_acquisition_request(
    acquisition_request: M162ModelAcquisitionRequest,
) -> M162ModelAcquisitionRequest:
    validated = M162ModelAcquisitionRequest.model_validate(acquisition_request.model_dump())
    for field_name, reason in [
        ("user_approved", "M162_EXACT_USER_APPROVAL_REQUIRED"),
        ("exact_artifacts_only", "M162_EXACT_ARTIFACTS_REQUIRED"),
        ("unauthenticated", "M162_UNAUTHENTICATED_DEFAULT_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("token_use_requested", "M162_TOKEN_USE_DENIED"),
        ("authenticated_request_requested", "M162_AUTHENTICATED_REQUEST_DENIED"),
        ("model_call_requested", "M162_MODEL_CALL_DENIED"),
        ("llama_cpp_process_requested", "M162_LLAMA_CPP_PROCESS_DENIED"),
        ("subprocess_requested", "M162_SUBPROCESS_DENIED"),
        ("backend_route_requested", "M162_BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "M162_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "M162_DEPENDENCY_DENIED"),
        ("production_authority_requested", "M162_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m162_model_acquisition_result(
    result: M162ModelAcquisitionResult,
) -> M162ModelAcquisitionResult:
    validated = M162ModelAcquisitionResult.model_validate(result.model_dump())
    for field_name, reason in [
        ("exact_user_approved", "M162_EXACT_USER_APPROVAL_REQUIRED"),
        ("exact_artifacts_only", "M162_EXACT_ARTIFACTS_REQUIRED"),
        ("uaa_owned_cache", "M162_UAA_CACHE_REQUIRED"),
        ("pinned_revision_used", "M162_PINNED_REVISION_REQUIRED"),
        ("unauthenticated", "M162_UNAUTHENTICATED_DEFAULT_REQUIRED"),
        ("https_get_only", "M162_HTTPS_GET_ONLY_REQUIRED"),
        ("download_performed", "M162_DOWNLOAD_PERFORMED_REQUIRED"),
        ("cache_write_performed", "M162_CACHE_WRITE_REQUIRED"),
        ("network_access_performed", "M162_NETWORK_ACCESS_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("raw_response_stored", "M162_RAW_RESPONSE_STORAGE_DENIED"),
        ("raw_url_stored", "M162_RAW_URL_STORAGE_DENIED"),
        ("local_path_included", "M162_RAW_PATH_DENIED"),
        ("token_used", "M162_TOKEN_USE_DENIED"),
        ("request_body_sent", "M162_REQUEST_BODY_DENIED"),
        ("model_file_read_performed", "M162_MODEL_FILE_READ_DENIED"),
        ("model_call_performed", "M162_MODEL_CALL_DENIED"),
        ("prompt_processed", "M162_PROMPT_PROCESSING_DENIED"),
        ("llama_cpp_process_started", "M162_LLAMA_CPP_PROCESS_DENIED"),
        ("subprocess_execution_performed", "M162_SUBPROCESS_DENIED"),
        ("backend_route_added", "M162_BACKEND_ROUTE_DENIED"),
        ("control_center_control_added", "M162_CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_added", "M162_DEPENDENCY_DENIED"),
        ("production_authority_granted", "M162_PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    for receipt in validated.artifact_receipts:
        validate_m162_acquired_artifact_receipt(receipt)
    return validated


def validate_m162_acquired_artifact_receipt(
    receipt: M162AcquiredArtifactReceipt,
) -> M162AcquiredArtifactReceipt:
    validated = M162AcquiredArtifactReceipt.model_validate(receipt.model_dump())
    for field_name, reason in [
        ("download_performed", "M162_DOWNLOAD_PERFORMED_REQUIRED"),
        ("cache_write_performed", "M162_CACHE_WRITE_REQUIRED"),
        ("network_access_performed", "M162_NETWORK_ACCESS_REQUIRED"),
    ]:
        if getattr(validated, field_name) is not True:
            raise ValueError(reason)
    for field_name, reason in [
        ("local_path_included", "M162_RAW_PATH_DENIED"),
        ("raw_url_included", "M162_RAW_URL_STORAGE_DENIED"),
        ("raw_response_stored", "M162_RAW_RESPONSE_STORAGE_DENIED"),
        ("token_used", "M162_TOKEN_USE_DENIED"),
        ("model_file_read_performed", "M162_MODEL_FILE_READ_DENIED"),
        ("model_call_performed", "M162_MODEL_CALL_DENIED"),
        ("llama_cpp_process_started", "M162_LLAMA_CPP_PROCESS_DENIED"),
        ("subprocess_execution_performed", "M162_SUBPROCESS_DENIED"),
    ]:
        if getattr(validated, field_name) is not False:
            raise ValueError(reason)
    return validated


def validate_m162_cache_root(cache_root: Path) -> Path:
    root = Path(cache_root)
    if ".uaa" not in root.parts:
        raise ValueError("M162_UAA_OWNED_CACHE_REQUIRED")
    resolved = root.resolve()
    if resolved == resolved.parent:
        raise ValueError("M162_CACHE_ROOT_DENIED")
    return resolved


def _acquire_one_artifact(
    artifact: M162GgufArtifactRequest,
    *,
    cache_root: Path,
    cache_ref: str,
    transport: M162ModelAcquisitionTransport,
    max_artifact_bytes: int,
) -> M162AcquiredArtifactReceipt:
    destination = _artifact_cache_path(cache_root, artifact)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".part",
        dir=destination.parent,
        delete=False,
    ) as temp_handle:
        temp_path = Path(temp_handle.name)
    try:
        transfer = transport.fetch_artifact(
            artifact,
            destination_path=temp_path,
            max_bytes=max_artifact_bytes,
        )
        _validate_transfer_against_artifact(transfer, artifact)
        temp_path.replace(destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    cache_artifact_ref = (
        f"{cache_ref}-artifact:{_safe_slug(artifact.repo_id)}-"
        f"{_safe_slug(artifact.revision)}-{_safe_slug(artifact.filename)}"
    )
    return validate_m162_acquired_artifact_receipt(
        M162AcquiredArtifactReceipt(
            artifact_ref=artifact.artifact_ref,
            repo_id=artifact.repo_id,
            revision=artifact.revision,
            filename=artifact.filename,
            role=artifact.role,
            cache_artifact_ref=cache_artifact_ref,
            size_bytes=transfer.bytes_written,
            sha256_ref=f"sha256:{transfer.sha256}",
        )
    )


def _validate_transfer_against_artifact(
    transfer: M162ArtifactTransferReceipt,
    artifact: M162GgufArtifactRequest,
) -> None:
    if transfer.artifact_ref != artifact.artifact_ref:
        raise ValueError("M162_TRANSFER_ARTIFACT_REF_MISMATCH")
    if artifact.expected_size_bytes is not None and transfer.bytes_written != artifact.expected_size_bytes:
        raise ValueError("M162_ARTIFACT_SIZE_MISMATCH")
    if artifact.expected_sha256 is not None and transfer.sha256.lower() != artifact.expected_sha256.lower():
        raise ValueError("M162_ARTIFACT_SHA256_MISMATCH")
    if transfer.raw_response_stored or transfer.raw_url_stored or transfer.token_used:
        raise ValueError("M162_TRANSFER_UNSAFE")


def _artifact_cache_path(cache_root: Path, artifact: M162GgufArtifactRequest) -> Path:
    repo_parts = [_safe_slug(part) for part in artifact.repo_id.split("/")]
    filename_parts = [_safe_slug(part) for part in artifact.filename.split("/")]
    relative = Path(*repo_parts) / _safe_slug(artifact.revision) / Path(*filename_parts)
    destination = (cache_root / relative).resolve()
    if cache_root not in destination.parents:
        raise ValueError("M162_CACHE_PATH_ESCAPE_DENIED")
    return destination


def _quote_slash_path(value: str) -> str:
    return "/".join(parse.quote(part, safe="") for part in value.split("/"))


def _allowed_m162_redirect_host(host: str) -> bool:
    lowered = host.lower()
    return any(lowered == suffix or lowered.endswith(suffix) for suffix in M162_ALLOWED_REDIRECT_HOST_SUFFIXES)


def _validate_repo_id(repo_id: str) -> None:
    _validate_safe_text(repo_id, "repo_id", max_length=160)
    if repo_id.startswith("/") or repo_id.endswith("/") or "//" in repo_id or ".." in repo_id:
        raise ValueError("M162_REPO_ID_UNSAFE")
    parts = repo_id.split("/")
    if len(parts) not in {1, 2}:
        raise ValueError("M162_REPO_ID_UNSAFE")


def _validate_pinned_revision(revision: str) -> None:
    _validate_safe_text(revision, "revision", max_length=80)
    lowered = revision.lower()
    if lowered in {"main", "master", "latest", "HEAD".lower()}:
        raise ValueError("M162_PINNED_REVISION_REQUIRED")
    if len(revision) != 40 or any(char not in "0123456789abcdefABCDEF" for char in revision):
        raise ValueError("M162_PINNED_REVISION_REQUIRED")


def _validate_remote_gguf_filename(filename: str) -> None:
    _validate_safe_text(filename, "filename", max_length=240)
    if not filename.lower().endswith(".gguf"):
        raise ValueError("M162_GGUF_FILENAME_REQUIRED")
    if filename.startswith("/") or filename.startswith("~") or "\\" in filename or ".." in filename:
        raise ValueError("M162_REMOTE_FILENAME_UNSAFE")
    if "?" in filename or "#" in filename:
        raise ValueError("M162_REMOTE_FILENAME_UNSAFE")


def _validate_m162_approval_ref(approval_ref: str) -> None:
    lowered = approval_ref.lower()
    _validate_m61_ref(approval_ref, "approval_ref")
    if "m162" not in lowered or not ("gguf" in lowered or "model-acquisition" in lowered):
        raise ValueError("M162_APPROVAL_REF_SCOPE_REQUIRED")
    if ":all" in lowered or ":*" in lowered or "*" in lowered or "approval_test_" in lowered:
        raise ValueError("M162_APPROVAL_REF_NOT_EXACT")
    for fragment in ["expired", "revoked", "replay-used"]:
        if fragment in lowered:
            raise ValueError("M162_APPROVAL_REF_NOT_ACTIVE")


def _validate_sha256(value: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
        raise ValueError("M162_SHA256_REQUIRED")


def _validate_safe_text(value: str, field_name: str, *, max_length: int) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long")
    if _URL_RE.search(value) or _SECRET_LIKE_RE.search(value):
        raise ValueError(f"{field_name} contains unsafe content")
    _validate_safe_payload(value)


def _safe_suffix(ref: str) -> str:
    return _safe_slug(ref.split(":", 1)[-1])


def _safe_slug(value: str) -> str:
    safe_chars: list[str] = []
    for char in value.strip().lower():
        if char.isalnum() or char in {"-", ".", "_"}:
            safe_chars.append(char)
        elif char in {"/", " ", ":", "@"}:
            safe_chars.append("-")
    return "".join(safe_chars).strip("-")[:96] or "unknown"
