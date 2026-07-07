#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_SESSION_SEARCH_AUTHORITY_MAPPING_REF,
    RUNTIME_SESSION_SEARCH_AUTHORITY_STATE_CLI_REF,
    RUNTIME_SESSION_SEARCH_AUTHORITY_STATE_ROUTE_REF,
    RUNTIME_SESSION_SEARCH_CONTRACT_REF,
    build_runtime_session_search_read_model,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_session_search_authority(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden_fragments = [
        '"raw_transcript_persistence_enabled": true',
        '"raw_prompt_response_exposure_enabled": true',
        '"semantic_provider_call_enabled": true',
        '"embedding_vector_index_enabled": true',
        '"hidden_context_injection_authorized": true',
        '"memory_write_authorized": true',
        '"action_execution_authorized": true',
        '"production_authority_enabled": true',
        '"raw_transcript_persisted": true',
        '"raw_prompt_persisted": true',
        '"raw_response_persisted": true',
        '"raw_provider_payload_persisted": true',
        '"semantic_provider_call_performed": true',
        '"embedding_vector_index_used": true',
        '"memory_write_performed": true',
        '"context_injection_authorized": true',
    ]
    for fragment in forbidden_fragments:
        if fragment in serialized:
            _fail(f"forbidden session search authority present: {fragment}")


def _assert_session_search(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "runtime_session_search.v1":
        _fail("session search schema drifted")
    if payload.get("contract_ref") != RUNTIME_SESSION_SEARCH_CONTRACT_REF:
        _fail("session search contract ref drifted")
    if payload.get("status") != "read_only_safe_ref_session_run_search":
        _fail("session search status drifted")
    if payload.get("route_ref") != "GET /api/runtime/session-search":
        _fail("session search route ref drifted")
    if payload.get("cli_ref") != "uaa runtime inspect-session-search":
        _fail("session search CLI ref drifted")
    if (
        payload.get("authority_state_route_ref")
        != RUNTIME_SESSION_SEARCH_AUTHORITY_STATE_ROUTE_REF
    ):
        _fail("session search authority state route ref drifted")
    if (
        payload.get("authority_state_cli_ref")
        != RUNTIME_SESSION_SEARCH_AUTHORITY_STATE_CLI_REF
    ):
        _fail("session search authority state CLI ref drifted")
    if (
        payload.get("authority_state_mapping_ref")
        != RUNTIME_SESSION_SEARCH_AUTHORITY_MAPPING_REF
    ):
        _fail("session search authority mapping drifted")
    if payload.get("authority_state_decision_outcome") != "allow":
        _fail("session search authority decision must be allowed by read lease")
    if "reason-ref:authority:active-lease-grants-domain-capability" not in (
        payload.get("authority_state_reason_refs") or []
    ):
        _fail("session search authority reason refs missing active lease reason")
    if "adapter-ref:session-search-memory-write:not-implemented" not in (
        payload.get("unsupported_adapter_refs") or []
    ):
        _fail("session search unsupported adapter refs missing memory write")
    if payload.get("query_mode") != "safe_ref_match_only":
        _fail("session search must remain safe-ref-match only")
    results = payload.get("results")
    if not isinstance(results, list) or len(results) < 5:
        _fail("session search results missing")
    if payload.get("result_count") != len(results):
        _fail("session search result count mismatch")
    posture = payload.get("memory_separation_posture")
    if not isinstance(posture, dict):
        _fail("session search memory separation posture missing")
    if posture.get("status") != "separate_from_durable_memory":
        _fail("session search must stay separate from durable memory")
    if posture.get("memory_write_performed") is not False:
        _fail("session search performed a memory write")
    if posture.get("memory_recall_used_as_truth") is not False:
        _fail("session search treated memory recall as truth")
    if posture.get("operator_selected_attach_required") is not True:
        _fail("session search must require explicit operator attach")
    if "proof-ref:hermes-runtime-adoption:phase-12:session-search" not in (
        payload.get("proof_refs") or []
    ):
        _fail("session search proof ref missing")
    if "blocked-authority:session-search-no-memory-write" not in (
        payload.get("blocked_authority_refs") or []
    ):
        _fail("session search memory-write blocker missing")
    for result in results:
        if not isinstance(result, dict):
            _fail("session search result is invalid")
        if not str(result.get("attachable_context_ref") or "").startswith(
            "context-ref:session-search:"
        ):
            _fail("session search result context ref missing")
        if not result.get("why_matched_refs"):
            _fail("session search result why-matched refs missing")
        if not result.get("blocked_authority_refs"):
            _fail("session search result blockers missing")
    _assert_no_session_search_authority(payload)


def main() -> None:
    core_payload = build_runtime_session_search_read_model().model_dump(mode="json")
    _assert_session_search(core_payload)

    filtered = build_runtime_session_search_read_model(
        query_ref="run-ref:mock-fallback:proof"
    ).model_dump(mode="json")
    if filtered.get("result_count") != 1:
        _fail("session search query_ref filter drifted")
    _assert_no_session_search_authority(filtered)

    client = TestClient(app)
    response = client.get("/api/runtime/session-search")
    if response.status_code != 200:
        _fail(f"session search route returned {response.status_code}")
    body = response.json()
    api_payload = body.get("data")
    if not isinstance(api_payload, dict):
        _fail("session search route did not return data")
    _assert_session_search(api_payload)

    unsafe = client.get("/api/runtime/session-search?query_ref=raw_prompt")
    if unsafe.status_code != 200:
        _fail("unsafe session search query should return safe envelope")
    unsafe_body = unsafe.json()
    if unsafe_body.get("success") is not False:
        _fail("unsafe session search query was not blocked")
    if "raw_prompt" in unsafe.text:
        _fail("unsafe session search query leaked rejected text")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-session-search",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    read_model_payload = cli_payload.get("runtime_session_search")
    if not isinstance(read_model_payload, dict):
        _fail("CLI did not return runtime session search data")
    if cli_payload.get("execution_performed") is not False:
        _fail("CLI claimed execution")
    if cli_payload.get("memory_write_performed") is not False:
        _fail("CLI claimed memory write")
    if cli_payload.get("context_injection_performed") is not False:
        _fail("CLI claimed context injection")
    authority_state = cli_payload.get("authority_state")
    if not isinstance(authority_state, dict):
        _fail("CLI did not return session search authority state")
    if authority_state.get("mapping_ref") != RUNTIME_SESSION_SEARCH_AUTHORITY_MAPPING_REF:
        _fail("CLI authority mapping drifted")
    if authority_state.get("decision_outcome") != "allow":
        _fail("CLI authority decision drifted")
    _assert_session_search(read_model_payload)
    print("Hermes Runtime Adoption Phase 12 session search verification passed.")


if __name__ == "__main__":
    main()
