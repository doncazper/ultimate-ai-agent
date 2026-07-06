from __future__ import annotations

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS,
    SENSITIVE_CONTEXT_GUARD_REF,
    RuntimeContextReferencePostureReadModel,
    RuntimeSessionSearchReadModel,
    build_runtime_context_references_read_model,
    build_runtime_session_search_read_model,
    classify_sensitive_context_candidate,
)


client = TestClient(app)


@pytest.mark.parametrize(
    "candidate",
    [
        "file-ref:protected-config-blocked",
        ".env",
        "keys/id_rsa",
        "keys/private.key",
        "~/Library/Application Support/example",
        "../outside",
        "%2e%2e/outside",
        "file-ref:credential-material-blocked",
    ],
)
def test_sensitive_context_classifier_blocks_without_echoing_candidate(
    candidate: str,
) -> None:
    classification = classify_sensitive_context_candidate(candidate)

    assert classification.guard_ref == SENSITIVE_CONTEXT_GUARD_REF
    assert classification.sensitive is True
    assert classification.preview_allowed is False
    assert classification.bypass_approval_required is True
    assert classification.bypass_approval_enabled is False
    assert classification.reason_refs
    assert classification.blocked_authority_refs == SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS
    serialized = classification.model_dump_json()
    assert candidate.lower() not in serialized.lower()
    assert "/users/" not in serialized.lower()
    assert "redaction-ref:sensitive-context-raw-candidate-omitted" in serialized


def test_sensitive_context_classifier_allows_safe_context_ref() -> None:
    classification = classify_sensitive_context_candidate(
        "context-ref:session-search:operator-loop"
    )

    assert classification.sensitive is False
    assert classification.preview_allowed is True
    assert classification.reason_refs == []
    assert classification.blocked_authority_refs == []


def test_context_references_expose_sensitive_guard_posture() -> None:
    read_model = build_runtime_context_references_read_model()

    assert read_model.sensitive_context_guard_ref == SENSITIVE_CONTEXT_GUARD_REF
    assert read_model.sensitive_context_blocking_enabled is True
    assert read_model.sensitive_context_bypass_enabled is False
    assert read_model.sensitive_context_bypass_approval_required is True
    assert set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.sensitive_context_blocked_authority_refs)
    )
    blocked = [ref for ref in read_model.references if ref.status == "blocked"]
    assert blocked
    assert set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS).issubset(
        set(blocked[0].blocked_authority_refs)
    )


def test_context_reference_model_rejects_sensitive_unblocked_ref() -> None:
    payload = build_runtime_context_references_read_model().model_dump(mode="json")
    payload["references"][0]["context_ref"] = "file-ref:protected-config-active"

    with pytest.raises(ValueError, match="SENSITIVE_CONTEXT_REF_BLOCKED"):
        RuntimeContextReferencePostureReadModel(**payload)


def test_context_reference_model_rejects_sensitive_guard_disablement() -> None:
    payload = build_runtime_context_references_read_model().model_dump(mode="json")
    payload["sensitive_context_blocking_enabled"] = False

    with pytest.raises(ValueError, match="SENSITIVE_GUARD_REQUIRED"):
        RuntimeContextReferencePostureReadModel(**payload)


def test_session_search_rejects_sensitive_query_refs() -> None:
    with pytest.raises(ValueError, match="SENSITIVE_CONTEXT_REF_BLOCKED"):
        build_runtime_session_search_read_model(
            query_ref="context-ref:session-search:protected-config"
        )


def test_session_search_model_rejects_sensitive_attachable_ref() -> None:
    payload = build_runtime_session_search_read_model().model_dump(mode="json")
    payload["results"][0]["attachable_context_ref"] = (
        "context-ref:session-search:protected-config"
    )

    with pytest.raises(ValueError, match="SENSITIVE_CONTEXT_REF_BLOCKED"):
        RuntimeSessionSearchReadModel(**payload)


def test_api_and_cli_surface_sensitive_context_guard_posture() -> None:
    context_response = client.get("/api/runtime/context-references")
    assert context_response.status_code == 200
    context_data = context_response.json()["data"]
    assert context_data["sensitive_context_guard_ref"] == SENSITIVE_CONTEXT_GUARD_REF
    assert context_data["sensitive_context_bypass_enabled"] is False

    session_response = client.get(
        "/api/runtime/session-search",
        params={"query_ref": "context-ref:session-search:protected-config"},
    )
    assert session_response.status_code == 200
    assert session_response.json()["success"] is False
    assert session_response.json()["error"]["code"] == "RUNTIME_SESSION_SEARCH_REF_DENIED"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-context-references",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    read_model = payload["runtime_context_references"]
    assert read_model["sensitive_context_guard_ref"] == SENSITIVE_CONTEXT_GUARD_REF
    assert read_model["sensitive_context_bypass_enabled"] is False
