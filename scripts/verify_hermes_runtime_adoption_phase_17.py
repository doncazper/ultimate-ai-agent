#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS,
    SENSITIVE_CONTEXT_GUARD_REF,
    build_runtime_context_references_read_model,
    build_runtime_session_search_read_model,
    classify_sensitive_context_candidate,
)


def _fail(message: str) -> None:
    raise SystemExit(f"Hermes Runtime Adoption Phase 17 verification failed: {message}")


def verify_classifier() -> None:
    for candidate in (
        "file-ref:protected-config-blocked",
        ".env",
        "keys/id_rsa",
        "../outside",
        "file-ref:credential-material-blocked",
    ):
        classification = classify_sensitive_context_candidate(candidate)
        if not classification.sensitive:
            _fail(f"classifier allowed sensitive candidate {candidate!r}")
        serialized = classification.model_dump_json().lower()
        if candidate.lower() in serialized or "/users/" in serialized:
            _fail("classifier persisted raw candidate material")
        if (
            classification.blocked_authority_refs
            != SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS
        ):
            _fail("classifier missing blocked authority refs")


def verify_read_models() -> None:
    context_model = build_runtime_context_references_read_model()
    if context_model.sensitive_context_guard_ref != SENSITIVE_CONTEXT_GUARD_REF:
        _fail("context references missing sensitive guard ref")
    if context_model.sensitive_context_bypass_enabled:
        _fail("context references enabled bypass authority")
    if set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS) - set(
        context_model.sensitive_context_blocked_authority_refs
    ):
        _fail("context references missing sensitive blocker refs")
    session_model = build_runtime_session_search_read_model()
    if session_model.sensitive_context_guard_ref != SENSITIVE_CONTEXT_GUARD_REF:
        _fail("session search missing sensitive guard ref")
    try:
        build_runtime_session_search_read_model(
            query_ref="context-ref:session-search:protected-config"
        )
    except ValueError:
        pass
    else:
        _fail("session search accepted sensitive query ref")


def verify_api() -> None:
    os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")
    client = TestClient(app)
    context_response = client.get("/api/runtime/context-references")
    if context_response.status_code != 200:
        _fail("context references API route failed")
    context_data = context_response.json().get("data") or {}
    if context_data.get("sensitive_context_guard_ref") != SENSITIVE_CONTEXT_GUARD_REF:
        _fail("context references API missing sensitive guard")
    session_response = client.get(
        "/api/runtime/session-search",
        params={"query_ref": "context-ref:session-search:protected-config"},
    )
    if session_response.status_code != 200:
        _fail("session search API did not return a governed envelope")
    if session_response.json().get("success") is not False:
        _fail("session search API accepted sensitive query ref")


def verify_cli() -> None:
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
    model = payload.get("runtime_context_references") or {}
    if model.get("sensitive_context_guard_ref") != SENSITIVE_CONTEXT_GUARD_REF:
        _fail("CLI output missing sensitive guard")
    if model.get("sensitive_context_bypass_enabled") is not False:
        _fail("CLI output enabled sensitive bypass")


def main() -> int:
    verify_classifier()
    verify_read_models()
    verify_api()
    verify_cli()
    print("Hermes Runtime Adoption Phase 17 sensitive context guards verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
