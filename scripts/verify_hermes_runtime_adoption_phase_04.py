#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    build_runtime_approval_bridge_read_model,
    validate_runtime_approval_scope,
)


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_bridge_payload(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "runtime_approval_bridge.v1":
        _fail("unexpected approval bridge schema")
    if payload.get("status") != "read_model_resolution_blocked":
        _fail("approval bridge must stay read-model resolution blocked")
    if payload.get("uaa_controls_authority") is not True:
        _fail("UAA must remain the authority owner")
    if payload.get("control_center_talks_directly_to_runtime") is not False:
        _fail("Control Center must not talk directly to runtime")
    if payload.get("safe_refs_only") is not True:
        _fail("approval bridge must use safe refs only")
    if payload.get("runtime_resolution_sent_count") != 0:
        _fail("runtime resolution send count must remain zero")
    for flag in [
        "approval_resolution_route_enabled",
        "deny_resolution_route_enabled",
        "timeout_resolution_route_enabled",
        "raw_runtime_payload_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
    ]:
        if payload.get(flag) is not False:
            _fail(f"{flag} must remain false")
    if payload.get("pending_runtime_approval_count") != 1:
        _fail("expected one pending runtime approval sample")
    if payload.get("denied_preview_count") != 1:
        _fail("expected one denial preview")
    if payload.get("timeout_preview_count") != 1:
        _fail("expected one timeout preview")
    if payload.get("scope_mismatch_count") != 1:
        _fail("expected one scope mismatch preview")
    projection = payload.get("action_inbox_projection")
    if not isinstance(projection, dict):
        _fail("missing Action Inbox projection")
    if projection.get("status") != "review_required_resolution_blocked":
        _fail("Action Inbox projection status drifted")
    if projection.get("approval_controls_visible") is not False:
        _fail("approval controls must remain hidden")
    if projection.get("runtime_resolution_controls_visible") is not False:
        _fail("runtime resolution controls must remain hidden")
    envelopes = payload.get("envelopes")
    if not isinstance(envelopes, list) or len(envelopes) != 1:
        _fail("expected one approval envelope")
    envelope = envelopes[0]
    if not isinstance(envelope, dict):
        _fail("approval envelope payload is invalid")
    for flag in [
        "runtime_resolution_sent",
        "approval_resolution_enabled",
        "denial_resolution_enabled",
        "raw_runtime_payload_persisted",
        "raw_prompt_persisted",
        "raw_response_persisted",
    ]:
        if envelope.get(flag) is not False:
            _fail(f"envelope {flag} must remain false")
    if envelope.get("approval_refs_are_identifiers_only") is not True:
        _fail("approval refs must remain identifiers only")
    if envelope.get("timeout_defaults_to_deny") is not True:
        _fail("timeout must default to deny")
    decisions = payload.get("decision_previews")
    if not isinstance(decisions, list) or len(decisions) != 3:
        _fail("expected denial, timeout, and scope-mismatch previews")
    for decision in decisions:
        if not isinstance(decision, dict):
            _fail("decision preview payload is invalid")
        if decision.get("runtime_resolution_sent") is not False:
            _fail("decision previews must not send runtime resolutions")
    blocked = payload.get("blocked_authority_refs")
    if not isinstance(blocked, list) or (
        "blocked-authority:runtime-approval-resolution-send" not in blocked
    ):
        _fail("missing runtime approval resolution blocked ref")
    proofs = payload.get("proof_refs")
    if not isinstance(proofs, list) or not proofs:
        _fail("missing proof refs")


def main() -> None:
    read_model = build_runtime_approval_bridge_read_model()
    payload = read_model.model_dump(mode="json")
    _assert_bridge_payload(payload)

    mismatch = read_model.scope_validation
    if mismatch.scope_matches:
        _fail("sample scope validation must demonstrate mismatch blocking")
    match = validate_runtime_approval_scope(
        "runtime-approval-scope-ref:verifier",
        "runtime-approval-scope-ref:verifier",
    )
    if not match.scope_matches or match.status != "scope_match_review_only":
        _fail("matching scope validation should stay review-only")

    client = TestClient(app)
    response = client.get("/api/runtime/approval-bridge")
    if response.status_code != 200:
        _fail(f"approval bridge route returned {response.status_code}")
    body = response.json()
    _assert_bridge_payload(body.get("data", {}))
    if body.get("redactions_applied") is None:
        _fail("approval bridge route must report redactions")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-approval-bridge",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(result.stdout)
    if cli_payload.get("execution_performed") is not False:
        _fail("CLI must report no execution")
    for field in [
        "approval_resolution_sent",
        "denial_resolution_sent",
        "timeout_resolution_sent",
    ]:
        if cli_payload.get(field) is not False:
            _fail(f"CLI {field} must remain false")
    _assert_bridge_payload(cli_payload.get("runtime_approval_bridge", {}))
    print("Hermes Runtime Adoption Phase 04 approval bridge verification passed.")


if __name__ == "__main__":
    main()
