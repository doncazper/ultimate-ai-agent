from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from ultimate_ai_agent.api.local_auth import local_api_authorized
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.storage.founder_loop import (
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
)


@given(
    expected=st.from_regex(r"[A-Za-z0-9._:-]{12,64}", fullmatch=True),
    supplied=st.from_regex(r"[A-Za-z0-9._:-]{12,64}", fullmatch=True),
)
@settings(max_examples=100, deadline=None)
def test_local_auth_accepts_only_the_exact_bearer(expected: str, supplied: str) -> None:
    authorized = local_api_authorized(
        f"Bearer {supplied}",
        env={"UAA_API_LOCAL_BEARER": expected},
    )
    assert authorized is (supplied == expected)


@given(
    unsafe_build_id=st.tuples(
        st.text(max_size=39),
        st.sampled_from(["/", " ", "\\"]),
        st.text(max_size=39),
    ).map("".join)
)
@settings(max_examples=50, deadline=None)
def test_build_identity_never_echoes_unsafe_build_ids(
    unsafe_build_id: str,
) -> None:
    identity = build_identity(
        env={"UAA_BUILD_ID": unsafe_build_id, "UAA_BUILD_COMMIT": "invalid"},
        repo_root=Path("/uaa-build-identity-unavailable"),
    )
    assert unsafe_build_id not in identity.model_dump_json()
    assert identity.source_revision_bound is False


@given(suffix=st.from_regex(r"[a-z][a-z0-9]{7,24}", fullmatch=True))
@settings(max_examples=25, deadline=None)
def test_storage_idempotency_is_duplicate_denying(
    suffix: str,
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repository = FounderLoopRepository(Path(temp_dir), seed_defaults=False)
        kwargs = {
            "key_ref": f"idempotency-ref:property:{suffix}",
            "scope_ref": f"scope-ref:property:{suffix}",
            "receipt_ref": f"receipt-ref:property:{suffix}",
        }
        repository.record_idempotency_key(**kwargs)
        with pytest.raises(FounderLoopStorageDuplicateError):
            repository.record_idempotency_key(**kwargs)
