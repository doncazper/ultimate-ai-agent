from typing import Any
import os

import pytest

from ultimate_ai_agent.core.local_model_management import (
    FakeM160HuggingFaceSearchTransport,
    M160HuggingFaceGgufSearchPolicy,
    M160HuggingFaceGgufSearchRequest,
    StdlibM160HuggingFaceSearchTransport,
    build_m160_huggingface_search_url,
    search_huggingface_gguf_models,
    validate_m160_huggingface_gguf_search_policy,
    validate_m160_huggingface_gguf_search_request,
    validate_m160_huggingface_gguf_search_result,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "hf-gguf-search-request:m160-qwopus",
        "query": "qwopus",
        "limit": 5,
    }
    data.update(overrides)
    return M160HuggingFaceGgufSearchRequest(**data)


def test_m160_policy_allows_only_bounded_unauthenticated_metadata_search() -> None:
    policy = validate_m160_huggingface_gguf_search_policy(M160HuggingFaceGgufSearchPolicy())

    assert policy.bounded_read_only is True
    assert policy.unauthenticated_only is True
    assert policy.https_get_only is True
    assert policy.metadata_only is True
    assert policy.gguf_candidates_only is True
    assert policy.raw_response_storage_allowed is False
    assert policy.token_use_allowed is False
    assert policy.download_allowed is False
    assert policy.model_call_allowed is False
    assert policy.dependency_added is False

    with pytest.raises(ValueError, match="M160_DOWNLOAD_DENIED"):
        validate_m160_huggingface_gguf_search_policy(
            M160HuggingFaceGgufSearchPolicy(download_allowed=True)
        )


@pytest.mark.parametrize(
    "query",
    [
        "https://huggingface.co/models",
        "/Users/sam/private/model.gguf",
        "../models",
        "token=hf_secret",
        "Authorization: Bearer x",
        "x" * 129,
    ],
)
def test_m160_rejects_unsafe_queries(query: str) -> None:
    with pytest.raises(ValueError):
        _request(query=query)


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"authenticated_request_requested": True}, "M160_AUTHENTICATED_REQUEST_DENIED"),
        ({"token_use_requested": True}, "M160_TOKEN_USE_DENIED"),
        ({"download_requested": True}, "M160_DOWNLOAD_DENIED"),
        ({"raw_response_requested": True}, "M160_RAW_RESPONSE_STORAGE_DENIED"),
        ({"model_call_requested": True}, "M160_MODEL_CALL_DENIED"),
    ],
)
def test_m160_request_denies_auth_download_raw_response_and_model_calls(update: Any, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_m160_huggingface_gguf_search_request(_request(**update))


def test_m160_builds_expected_huggingface_models_url_without_tokens_or_bodies() -> None:
    url = build_m160_huggingface_search_url(_request(query="qwen gguf", limit=3))

    assert url.startswith("https://huggingface.co/api/models?")
    assert "search=qwen+gguf" in url
    assert "filter=gguf" in url
    assert "limit=3" in url
    assert "full=true" in url
    assert "token" not in url.lower()
    assert "api_key" not in url.lower()


def test_m160_fake_transport_filters_gguf_and_redacts_raw_payload() -> None:
    transport = FakeM160HuggingFaceSearchTransport(
        [
            {
                "id": "org/qwopus",
                "gated": False,
                "downloads": 50,
                "likes": 7,
                "lastModified": "2026-01-02T00:00:00.000Z",
                "cardData": {"license": "apache-2.0"},
                "tags": ["gguf", "license:apache-2.0", "text-generation"],
                "siblings": [
                    {"rfilename": "qwopus-q4_k_m.gguf", "size": 4_294_967_296},
                    {"rfilename": "model.safetensors", "size": 1_000},
                ],
                "raw_card": "token=should-not-leak /Users/sam/private",
            },
            {
                "id": "org/gated-qwopus",
                "gated": True,
                "downloads": 100,
                "siblings": [{"rfilename": "gated-q5_k_m.GGUF", "size": 8_589_934_592}],
            },
            {
                "id": "org/no-gguf",
                "gated": False,
                "siblings": [{"rfilename": "model.bin", "size": 1}],
            },
        ]
    )

    result = search_huggingface_gguf_models(_request(), transport=transport)
    payload = result.model_dump_json()

    assert len(transport.calls) == 1
    assert result.live_search_performed is True
    assert result.network_access_performed is True
    assert result.unauthenticated is True
    assert result.token_used is False
    assert result.download_performed is False
    assert result.model_call_performed is False
    assert result.raw_response_stored is False
    assert [candidate.repo_id for candidate in result.candidates] == ["org/qwopus"]
    assert result.candidates[0].license_ref == "license:apache-2.0"
    assert result.candidates[0].provenance_ref == "provenance:hugging-face-public-metadata"
    assert result.candidates[0].gguf_files[0].filename == "qwopus-q4_k_m.gguf"
    assert result.candidates[0].gguf_files[0].size_bytes == 4_294_967_296
    assert "org/no-gguf" not in payload
    assert "token=should-not-leak" not in payload
    assert "/Users/" not in payload
    assert "raw_card" not in payload


def test_m160_can_include_gated_metadata_only_when_explicitly_requested() -> None:
    transport = FakeM160HuggingFaceSearchTransport(
        [
            {
                "id": "org/gated-qwopus",
                "gated": True,
                "downloads": 100,
                "siblings": [{"rfilename": "gated-q5_k_m.GGUF", "size": 8_589_934_592}],
            },
        ]
    )

    result = search_huggingface_gguf_models(
        _request(include_gated=True),
        transport=transport,
    )

    assert result.candidates[0].repo_id == "org/gated-qwopus"
    assert result.candidates[0].gated is True
    assert result.candidates[0].license_ref == "license:unknown"
    assert result.download_performed is False


def test_m160_fake_search_output_is_stable() -> None:
    request = _request(query="qwopus", limit=2)
    transport = FakeM160HuggingFaceSearchTransport(
        [
            {
                "id": "org/b",
                "downloads": 1,
                "likes": 0,
                "siblings": [{"rfilename": "b-q4.gguf", "size": 20}],
            },
            {
                "id": "org/a",
                "downloads": 10,
                "likes": 0,
                "siblings": [{"rfilename": "a-q4.gguf", "size": 10}],
            },
        ]
    )

    first = search_huggingface_gguf_models(request, transport=transport).model_dump()
    second = search_huggingface_gguf_models(request, transport=transport).model_dump()

    assert first == second
    assert first["candidate_refs"] == [
        "hf-gguf-candidate:m160-org-a",
        "hf-gguf-candidate:m160-org-b",
    ]


def test_m160_live_transport_result_validation_rejects_unsafe_mutations() -> None:
    result = search_huggingface_gguf_models(
        _request(),
        transport=FakeM160HuggingFaceSearchTransport(
            [{"id": "org/qwopus", "siblings": [{"rfilename": "q4.gguf", "size": 1234}]}]
        ),
    )

    with pytest.raises(ValueError, match="M160_RAW_RESPONSE_STORAGE_DENIED"):
        validate_m160_huggingface_gguf_search_result(
            result.model_copy(update={"raw_response_stored": True})
        )
    with pytest.raises(ValueError, match="M160_MODEL_CALL_DENIED"):
        validate_m160_huggingface_gguf_search_result(
            result.model_copy(update={"model_call_performed": True})
        )


@pytest.mark.skipif(
    os.getenv("UAA_M160_LIVE_HF_GGUF_SEARCH") != "1",
    reason="explicit live smoke only",
)
def test_m160_optional_live_hf_smoke_shape() -> None:
    result = search_huggingface_gguf_models(
        _request(query=os.getenv("UAA_M160_LIVE_HF_QUERY", "qwen gguf"), limit=3),
        transport=StdlibM160HuggingFaceSearchTransport(),
    )

    assert len(result.candidates) <= 3
    assert all(
        file.filename.lower().endswith(".gguf")
        for candidate in result.candidates
        for file in candidate.gguf_files
    )
    assert result.unauthenticated is True
    assert result.token_used is False
    assert result.download_performed is False
    assert result.model_call_performed is False
    assert result.raw_response_stored is False
