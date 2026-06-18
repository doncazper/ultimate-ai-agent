import hashlib
import os

import pytest

from ultimate_ai_agent.core.local_model_management import (
    ArtifactRole,
    FakeM162ModelAcquisitionTransport,
    M162GgufArtifactRequest,
    M162ModelAcquisitionPolicy,
    M162ModelAcquisitionRequest,
    StdlibM162HuggingFaceArtifactTransport,
    acquire_huggingface_gguf_artifacts,
    build_m162_huggingface_resolve_url,
    validate_m162_cache_root,
    validate_m162_model_acquisition_policy,
    validate_m162_model_acquisition_request,
    validate_m162_model_acquisition_result,
)


PINNED_REVISION = "0123456789abcdef0123456789abcdef01234567"


def _artifact(**overrides):
    data = {
        "artifact_ref": "gguf-artifact:m162-qwopus-primary",
        "repo_id": "org/qwopus",
        "revision": PINNED_REVISION,
        "filename": "qwopus-q4_k_m.gguf",
        "role": ArtifactRole.primary,
        "expected_size_bytes": len(b"primary-gguf"),
        "expected_sha256": hashlib.sha256(b"primary-gguf").hexdigest(),
        "license_ref": "license:apache-2.0",
        "provenance_ref": "provenance:hugging-face-public-artifact",
    }
    data.update(overrides)
    return M162GgufArtifactRequest(**data)


def _request(**overrides):
    data = {
        "request_ref": "model-acquisition-request:m162-qwopus",
        "approval_ref": "approval:m162-gguf-acquisition-qwopus",
        "artifacts": [_artifact()],
    }
    data.update(overrides)
    return M162ModelAcquisitionRequest(**data)


def test_m162_policy_allows_only_exact_approved_gguf_cache_acquisition():
    policy = validate_m162_model_acquisition_policy(M162ModelAcquisitionPolicy())

    assert policy.exact_user_approval_required is True
    assert policy.pinned_revision_required is True
    assert policy.exact_filename_required is True
    assert policy.uaa_owned_cache_required is True
    assert policy.unauthenticated_by_default is True
    assert policy.token_use_allowed is False
    assert policy.model_call_allowed is False
    assert policy.llama_cpp_process_allowed is False
    assert policy.subprocess_allowed is False
    assert policy.dependency_added is False

    with pytest.raises(ValueError, match="M162_TOKEN_USE_DENIED"):
        validate_m162_model_acquisition_policy(M162ModelAcquisitionPolicy(token_use_allowed=True))


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"revision": "main"}, "M162_PINNED_REVISION_REQUIRED"),
        ({"filename": "model.safetensors"}, "M162_GGUF_FILENAME_REQUIRED"),
        ({"filename": "../model.gguf"}, "M162_REMOTE_FILENAME_UNSAFE"),
        ({"repo_id": "https://huggingface.co/org/qwopus"}, "repo_id contains unsafe content"),
        ({"role": ArtifactRole.mmproj, "filename": "vision-projector.gguf"}, "M162_MMPROJ_FILENAME_REQUIRED"),
        ({"role": ArtifactRole.shard, "filename": "model-q4.gguf"}, "M162_SHARDED_FILENAME_REQUIRED"),
    ],
)
def test_m162_artifact_requests_require_exact_safe_refs(update, reason):
    with pytest.raises(ValueError, match=reason):
        _artifact(**update)


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"user_approved": False}, "M162_EXACT_USER_APPROVAL_REQUIRED"),
        ({"approval_ref": "approval:m162-all"}, "M162_APPROVAL_REF_SCOPE_REQUIRED"),
        ({"approval_ref": "approval:m162-gguf-acquisition:all"}, "M162_APPROVAL_REF_NOT_EXACT"),
        ({"token_use_requested": True}, "M162_TOKEN_USE_DENIED"),
        ({"authenticated_request_requested": True}, "M162_AUTHENTICATED_REQUEST_DENIED"),
        ({"model_call_requested": True}, "M162_MODEL_CALL_DENIED"),
        ({"llama_cpp_process_requested": True}, "M162_LLAMA_CPP_PROCESS_DENIED"),
        ({"subprocess_requested": True}, "M162_SUBPROCESS_DENIED"),
    ],
)
def test_m162_request_denies_broad_approval_auth_model_and_process_authority(update, reason):
    with pytest.raises(ValueError, match=reason):
        validate_m162_model_acquisition_request(_request(**update))


def test_m162_builds_exact_huggingface_resolve_url_without_tokens():
    url = build_m162_huggingface_resolve_url(
        _artifact(filename="subdir/qwopus-q4_k_m.gguf")
    )

    assert url == (
        "https://huggingface.co/org/qwopus/resolve/"
        f"{PINNED_REVISION}/subdir/qwopus-q4_k_m.gguf"
    )
    assert "token" not in url.lower()
    assert "api_key" not in url.lower()


def test_m162_fake_transport_acquires_primary_shards_and_mmproj_into_uaa_cache(tmp_path):
    primary = _artifact()
    shard = _artifact(
        artifact_ref="gguf-artifact:m162-qwopus-shard-00001",
        filename="qwopus-00001-of-00002.gguf",
        role=ArtifactRole.shard,
        expected_size_bytes=len(b"shard-one"),
        expected_sha256=hashlib.sha256(b"shard-one").hexdigest(),
    )
    mmproj = _artifact(
        artifact_ref="gguf-artifact:m162-qwopus-mmproj",
        filename="mmproj-qwopus.gguf",
        role=ArtifactRole.mmproj,
        expected_size_bytes=len(b"mmproj"),
        expected_sha256=hashlib.sha256(b"mmproj").hexdigest(),
    )
    cache_root = tmp_path / ".uaa" / "model-cache"
    transport = FakeM162ModelAcquisitionTransport(
        {
            primary.artifact_ref: b"primary-gguf",
            shard.artifact_ref: b"shard-one",
            mmproj.artifact_ref: b"mmproj",
        }
    )

    result = acquire_huggingface_gguf_artifacts(
        _request(artifacts=[primary, shard, mmproj]),
        cache_root=cache_root,
        transport=transport,
        max_artifact_bytes=128,
    )
    payload = result.model_dump_json()
    cached_files = sorted(path.name for path in cache_root.rglob("*.gguf"))

    assert [artifact.artifact_ref for artifact in transport.calls] == [
        primary.artifact_ref,
        shard.artifact_ref,
        mmproj.artifact_ref,
    ]
    assert cached_files == [
        "mmproj-qwopus.gguf",
        "qwopus-00001-of-00002.gguf",
        "qwopus-q4_k_m.gguf",
    ]
    assert result.exact_user_approved is True
    assert result.download_performed is True
    assert result.cache_write_performed is True
    assert result.unauthenticated is True
    assert result.token_used is False
    assert result.model_file_read_performed is False
    assert result.model_call_performed is False
    assert result.llama_cpp_process_started is False
    assert result.subprocess_execution_performed is False
    assert result.backend_route_added is False
    assert str(tmp_path) not in payload
    assert "/Users/" not in payload
    assert "https://huggingface.co" not in payload


def test_m162_checksum_mismatch_removes_partial_cache_file(tmp_path):
    bad_artifact = _artifact(expected_sha256="0" * 64)
    cache_root = tmp_path / ".uaa" / "model-cache"

    with pytest.raises(ValueError, match="M162_ARTIFACT_SHA256_MISMATCH"):
        acquire_huggingface_gguf_artifacts(
            _request(artifacts=[bad_artifact]),
            cache_root=cache_root,
            transport=FakeM162ModelAcquisitionTransport({bad_artifact.artifact_ref: b"primary-gguf"}),
            max_artifact_bytes=128,
        )

    assert list(cache_root.rglob("*.part")) == []
    assert list(cache_root.rglob("*.gguf")) == []


def test_m162_requires_uaa_owned_cache_root(tmp_path):
    with pytest.raises(ValueError, match="M162_UAA_OWNED_CACHE_REQUIRED"):
        validate_m162_cache_root(tmp_path / "model-cache")


def test_m162_result_validation_rejects_unsafe_mutations(tmp_path):
    result = acquire_huggingface_gguf_artifacts(
        _request(),
        cache_root=tmp_path / ".uaa" / "model-cache",
        transport=FakeM162ModelAcquisitionTransport(
            {"gguf-artifact:m162-qwopus-primary": b"primary-gguf"}
        ),
        max_artifact_bytes=128,
    )

    with pytest.raises(ValueError, match="M162_TOKEN_USE_DENIED"):
        validate_m162_model_acquisition_result(result.model_copy(update={"token_used": True}))
    with pytest.raises(ValueError, match="M162_MODEL_CALL_DENIED"):
        validate_m162_model_acquisition_result(result.model_copy(update={"model_call_performed": True}))
    with pytest.raises(ValueError, match="M162_RAW_PATH_DENIED"):
        validate_m162_model_acquisition_result(result.model_copy(update={"local_path_included": True}))


@pytest.mark.skipif(
    os.getenv("UAA_M162_LIVE_HF_ACQUISITION") != "1",
    reason="explicit live M162 acquisition smoke only",
)
def test_m162_optional_live_hf_acquisition_smoke(tmp_path):
    repo_id = os.environ["UAA_M162_LIVE_HF_REPO"]
    revision = os.environ["UAA_M162_LIVE_HF_REVISION"]
    filename = os.environ["UAA_M162_LIVE_HF_FILENAME"]
    expected_sha256 = os.getenv("UAA_M162_LIVE_HF_SHA256")
    expected_size = os.getenv("UAA_M162_LIVE_HF_SIZE_BYTES")
    artifact = M162GgufArtifactRequest(
        artifact_ref="gguf-artifact:m162-live-smoke",
        repo_id=repo_id,
        revision=revision,
        filename=filename,
        expected_sha256=expected_sha256,
        expected_size_bytes=int(expected_size) if expected_size else None,
    )

    result = acquire_huggingface_gguf_artifacts(
        M162ModelAcquisitionRequest(
            request_ref="model-acquisition-request:m162-live-smoke",
            approval_ref="approval:m162-gguf-acquisition-live-smoke",
            artifacts=[artifact],
        ),
        cache_root=tmp_path / ".uaa" / "model-cache",
        transport=StdlibM162HuggingFaceArtifactTransport(timeout_seconds=30.0),
        max_artifact_bytes=int(os.getenv("UAA_M162_LIVE_HF_MAX_BYTES", "10485760")),
    )

    assert result.artifact_refs == ["gguf-artifact:m162-live-smoke"]
    assert result.artifact_receipts[0].size_bytes > 0
    assert result.unauthenticated is True
    assert result.token_used is False
    assert result.model_call_performed is False
    assert result.llama_cpp_process_started is False
