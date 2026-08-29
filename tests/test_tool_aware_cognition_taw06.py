from __future__ import annotations

import asyncio
from enum import Enum
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from starlette.types import Message

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.capability_diagnostics import (
    CapabilityDiagnosticBodyLimitMiddleware,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.capabilities import (
    AwarenessEvidenceStatus,
    ChatShadowDecision,
    ChatShadowEvidence,
    DiagnosticApprovalPosture,
    DiagnosticOperatorStatus,
    FamiliarityState,
    ShadowChatAction,
    ToolAwareDiagnosticRequest,
    ToolAwareOperatorDiagnostic,
    build_tool_aware_operator_diagnostic,
    evaluate_chat_shadow,
)
from ultimate_ai_agent.core.capabilities import chat_shadow, diagnostics


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/inspect_tool_aware_diagnostics.py"
ROUTE = "/api/capability-diagnostics/preview"
client = TestClient(app)


def _decision(
    familiarity_state: FamiliarityState | None,
    *,
    selected_operation_count: int | None = None,
    material_ambiguity: bool = True,
) -> ChatShadowDecision:
    if familiarity_state is None:
        return evaluate_chat_shadow(
            ChatShadowEvidence(awareness_status=AwarenessEvidenceStatus.missing)
        )
    material_effect_refs = (
        (
            "effect-class-ref:taw06:read",
            "effect-class-ref:taw06:write",
        )
        if familiarity_state == FamiliarityState.ambiguous and material_ambiguity
        else ()
    )
    (
        action,
        reason_refs,
        safe_disable_engaged,
        clarification_posture,
        clarification_contract_ref,
    ) = chat_shadow._derive_shadow_action(
        awareness_status=AwarenessEvidenceStatus.valid,
        familiarity_state=familiarity_state,
        material_effect_refs=material_effect_refs,
    )
    if selected_operation_count is None:
        selected_operation_count = (
            1 if action == ShadowChatAction.record_capability_candidate else 0
        )
    selected_operation_refs = tuple(
        f"operation-ref:taw06:reviewed-{index:02d}"
        for index in range(selected_operation_count)
    )
    base = evaluate_chat_shadow(
        ChatShadowEvidence(awareness_status=AwarenessEvidenceStatus.missing)
    ).model_dump(mode="python")
    base.update(
        {
            "awareness_status": AwarenessEvidenceStatus.valid,
            "action": action,
            "reason_refs": reason_refs,
            "safe_disable_engaged": safe_disable_engaged,
            "familiarity_state": familiarity_state,
            "assessment_fingerprint_ref": (
                "familiarity-assessment-ref:taw02:sha256:" + "6" * 64
            ),
            "hydration_fingerprint_ref": None,
            "selected_operation_refs": selected_operation_refs,
            "material_effect_refs": material_effect_refs,
            "clarification_posture": clarification_posture,
            "clarification_contract_ref": clarification_contract_ref,
        }
    )
    base["decision_fingerprint_ref"] = chat_shadow._fingerprint(
        {
            key: value
            for key, value in base.items()
            if key != "decision_fingerprint_ref"
        },
        prefix="chat-shadow-decision-ref:taw04",
    )
    return ChatShadowDecision.model_validate(base)


def _request(decision: ChatShadowDecision) -> dict[str, object]:
    return ToolAwareDiagnosticRequest(decision=decision).model_dump(mode="json")


def test_taw06_enums_keep_the_python_310_string_enum_shape() -> None:
    for enum_type in (
        DiagnosticOperatorStatus,
        DiagnosticApprovalPosture,
    ):
        assert enum_type.__bases__ == (str, Enum)


@pytest.mark.parametrize(
    ("state", "expected_status", "expected_approval"),
    [
        (
            FamiliarityState.familiar_supported,
            DiagnosticOperatorStatus.ready_for_review,
            DiagnosticApprovalPosture.not_required_or_already_validated,
        ),
        (
            FamiliarityState.familiar_input_required,
            DiagnosticOperatorStatus.input_required,
            DiagnosticApprovalPosture.deferred_until_input_complete,
        ),
        (
            FamiliarityState.familiar_unavailable,
            DiagnosticOperatorStatus.unavailable,
            DiagnosticApprovalPosture.deferred_until_available,
        ),
        (
            FamiliarityState.familiar_requires_approval,
            DiagnosticOperatorStatus.approval_required,
            DiagnosticApprovalPosture.exact_approval_required,
        ),
        (
            FamiliarityState.familiar_authority_blocked,
            DiagnosticOperatorStatus.blocked,
            DiagnosticApprovalPosture.authority_blocked,
        ),
        (
            FamiliarityState.capability_evidence_unavailable,
            DiagnosticOperatorStatus.evidence_unavailable,
            DiagnosticApprovalPosture.not_applicable,
        ),
        (
            FamiliarityState.ambiguous,
            DiagnosticOperatorStatus.clarification_required,
            DiagnosticApprovalPosture.unknown_until_clarified,
        ),
        (
            FamiliarityState.novel_unsupported,
            DiagnosticOperatorStatus.unsupported,
            DiagnosticApprovalPosture.not_applicable,
        ),
        (
            FamiliarityState.outcome_uncertain,
            DiagnosticOperatorStatus.outcome_uncertain,
            DiagnosticApprovalPosture.deferred_until_outcome_resolved,
        ),
    ],
)
def test_all_familiarity_states_have_readable_bounded_diagnostics(
    state: FamiliarityState,
    expected_status: DiagnosticOperatorStatus,
    expected_approval: DiagnosticApprovalPosture,
) -> None:
    diagnostic = build_tool_aware_operator_diagnostic(_decision(state))

    assert diagnostic.familiarity_state == state
    assert diagnostic.operator_status == expected_status
    assert diagnostic.approval_posture == expected_approval
    assert diagnostic.route_label
    assert diagnostic.route_summary
    assert diagnostic.familiarity_label
    assert diagnostic.familiarity_summary
    assert diagnostic.approval_summary
    assert diagnostic.limitation_summaries
    assert diagnostic.required_next_steps
    assert len(diagnostic.reason_refs) <= diagnostics.TAW06_MAX_REASON_REFS
    assert (
        len(diagnostic.selected_operation_refs)
        <= diagnostics.TAW06_MAX_SELECTED_OPERATION_REFS
    )
    assert len(diagnostic.evidence_refs) <= diagnostics.TAW06_MAX_EVIDENCE_REFS


def test_missing_awareness_preserves_direct_chat_and_fails_closed() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(_decision(None))

    assert diagnostic.awareness_status == AwarenessEvidenceStatus.missing
    assert diagnostic.safe_disable_engaged
    assert diagnostic.operator_status == DiagnosticOperatorStatus.evidence_unavailable
    assert "Direct chat preserved" in diagnostic.route_label
    assert not diagnostic.operator_visible_route_changed
    assert not diagnostic.execution_performed


def test_invalid_awareness_and_valid_capability_failure_name_distinct_layers() -> None:
    invalid_awareness = build_tool_aware_operator_diagnostic(
        evaluate_chat_shadow(
            ChatShadowEvidence(awareness_status=AwarenessEvidenceStatus.corrupt)
        )
    )
    capability_failure = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.capability_evidence_unavailable)
    )

    assert invalid_awareness.awareness_status == AwarenessEvidenceStatus.corrupt
    assert "awareness evidence invalid" in invalid_awareness.route_label.lower()
    assert "not trusted" in invalid_awareness.route_summary
    assert capability_failure.awareness_status == AwarenessEvidenceStatus.valid
    assert "capability evidence blocked" in capability_failure.route_label.lower()
    assert "Awareness is valid" in capability_failure.route_summary
    assert "not trusted" not in capability_failure.route_summary


def test_non_material_ambiguity_does_not_require_clarification() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.ambiguous, material_ambiguity=False)
    )

    assert diagnostic.shadow_action == ShadowChatAction.preserve_direct_chat
    assert diagnostic.source_inspection.clarification_posture == "not_applicable"
    assert diagnostic.operator_status == DiagnosticOperatorStatus.ready_for_review
    assert diagnostic.approval_posture == DiagnosticApprovalPosture.not_applicable
    assert "no clarification is required" in diagnostic.familiarity_summary


def test_missing_input_defers_instead_of_waiving_later_approval() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_input_required)
    )

    assert (
        diagnostic.approval_posture
        == DiagnosticApprovalPosture.deferred_until_input_complete
    )
    assert "may still be required afterward" in diagnostic.approval_summary


def test_supported_capability_does_not_erase_validated_approval_evidence() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_supported)
    )

    assert (
        diagnostic.approval_posture
        == DiagnosticApprovalPosture.not_required_or_already_validated
    )
    assert "already validated" in diagnostic.approval_summary
    assert "grants no approval" in diagnostic.approval_summary


def test_unavailable_capability_defers_instead_of_waiving_later_approval() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_unavailable)
    )

    assert (
        diagnostic.approval_posture
        == DiagnosticApprovalPosture.deferred_until_available
    )
    assert "may still be required afterward" in diagnostic.approval_summary


def test_authority_block_does_not_claim_one_capability_matched() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_authority_blocked)
    )

    assert "exactly one reviewed capability matched" in diagnostic.familiarity_summary
    assert "A reviewed capability matches" not in diagnostic.familiarity_summary


def test_uncertain_outcome_defers_instead_of_erasing_approval_posture() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.outcome_uncertain)
    )

    assert (
        diagnostic.approval_posture
        == DiagnosticApprovalPosture.deferred_until_outcome_resolved
    )
    assert "required or already validated" in diagnostic.approval_summary
    assert "grants none" in diagnostic.approval_summary


def test_diagnostic_is_redacted_non_authoritative_and_zero_effect() -> None:
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_requires_approval)
    )

    assert diagnostic.routine_machinery_hidden_from_ordinary_chat
    assert diagnostic.relevant_limitations_disclosed
    assert diagnostic.approval_posture == "exact_approval_required"
    assert "has not been granted" in diagnostic.approval_summary
    assert not any(
        (
            diagnostic.operator_visible_route_changed,
            diagnostic.model_context_changed,
            diagnostic.raw_operator_content_included,
            diagnostic.raw_model_content_included,
            diagnostic.raw_provider_payload_included,
            diagnostic.raw_local_paths_included,
            diagnostic.provider_call_performed,
            diagnostic.proposal_constructed,
            diagnostic.approval_granted,
            diagnostic.execution_performed,
            diagnostic.connector_call_performed,
            diagnostic.external_write_performed,
            diagnostic.authority_granted,
            diagnostic.production_authority_granted,
            diagnostic.control_center_surface_added,
        )
    )
    assert diagnostic.model_call_count == 0
    assert diagnostic.second_ordinary_chat_model_call_count == 0


def test_read_model_rejects_human_label_substitution_even_with_rehashed_outer_ref() -> (
    None
):
    diagnostic = build_tool_aware_operator_diagnostic(
        _decision(FamiliarityState.familiar_supported)
    )
    payload = diagnostic.model_dump(mode="python")
    payload["familiarity_label"] = "Everything is approved"
    payload["diagnostic_fingerprint_ref"] = diagnostics._fingerprint(
        {
            key: value
            for key, value in payload.items()
            if key != "diagnostic_fingerprint_ref"
        },
        prefix="operator-diagnostic-ref:taw06",
    )

    with pytest.raises(ValidationError, match="familiarity_label binding drift"):
        ToolAwareOperatorDiagnostic.model_validate(payload)


def test_diagnostic_rejects_oversized_selected_operation_evidence() -> None:
    decision = _decision(
        FamiliarityState.familiar_supported,
        selected_operation_count=diagnostics.TAW06_MAX_SELECTED_OPERATION_REFS + 1,
    )

    with pytest.raises(ValueError, match="selected_operation_refs exceed"):
        build_tool_aware_operator_diagnostic(decision)


def test_api_rejects_oversized_evidence_as_typed_input_error() -> None:
    decision = _decision(
        FamiliarityState.familiar_supported,
        selected_operation_count=diagnostics.TAW06_MAX_SELECTED_OPERATION_REFS + 1,
    )
    response = client.post(
        ROUTE,
        json={
            "schema_version": "uaa-taw06-diagnostic-request.v1",
            "decision": decision.model_dump(mode="json"),
        },
    )

    assert response.status_code == 422


def test_request_rejects_oversized_strings_and_total_materialization() -> None:
    payload = _request(_decision(FamiliarityState.familiar_supported))
    oversized_string = {
        **payload,
        "padding": "x" * (diagnostics.TAW06_MAX_STRING_CHARACTERS + 1),
    }
    oversized_request = {
        **payload,
        "padding": [
            "x" * diagnostics.TAW06_MAX_STRING_CHARACTERS
            for _ in range(
                diagnostics.TAW06_MAX_REQUEST_BYTES
                // diagnostics.TAW06_MAX_STRING_CHARACTERS
                + 1
            )
        ],
    }

    with pytest.raises(ValidationError, match="oversized string"):
        ToolAwareDiagnosticRequest.model_validate(oversized_string)
    with pytest.raises(ValidationError, match="request exceeds"):
        ToolAwareDiagnosticRequest.model_validate(oversized_request)


def test_api_rejects_deep_unknown_json_before_recursive_materialization() -> None:
    payload = _request(_decision(FamiliarityState.familiar_supported))
    nested: dict[str, object] = {}
    for _ in range(diagnostics.TAW06_MAX_REQUEST_NESTING_DEPTH + 2):
        nested = {"nested": nested}
    payload["padding"] = nested

    with pytest.raises(ValidationError, match="nesting depth bound"):
        ToolAwareDiagnosticRequest.model_validate(payload)

    response = client.post(ROUTE, json=payload)

    assert response.status_code == 422


def test_api_rejects_oversized_raw_body_before_json_decoding() -> None:
    response = client.post(
        ROUTE,
        content=b"{" + b"x" * diagnostics.TAW06_MAX_REQUEST_BYTES,
        headers={"content-type": "application/json", "content-length": "1"},
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "TAW-06 diagnostic request body exceeds the permitted bound.",
        "code": "TAW06_REQUEST_BODY_TOO_LARGE",
        "contract_ref": diagnostics.TAW06_CONTRACT_REF,
        "maximum_body_bytes": diagnostics.TAW06_MAX_REQUEST_BYTES,
    }


def test_api_rejects_extreme_json_nesting_before_fastapi_decodes() -> None:
    body = b"[" * 10_000 + b"]" * 10_000
    assert len(body) < diagnostics.TAW06_MAX_REQUEST_BYTES

    response = client.post(
        ROUTE,
        content=body,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["operation"] == "request_validation"
    assert payload["error"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert payload["error"]["metadata"]["validation_errors"][0]["loc"] == [
        "body"
    ]
    assert (
        "nesting bound"
        in payload["error"]["metadata"]["validation_errors"][0]["msg"]
    )
    ordinary_validation = client.post(ROUTE, json={}).json()
    assert payload.keys() == ordinary_validation.keys()
    assert payload["error"].keys() == ordinary_validation["error"].keys()
    assert "detail" not in payload


def test_body_guard_replays_many_chunks_as_one_bounded_message() -> None:
    downstream_messages: list[dict[str, object]] = []

    async def downstream(scope, receive, send) -> None:
        downstream_messages.append(await receive())
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = CapabilityDiagnosticBodyLimitMiddleware(downstream)
    incoming = [
        {"type": "http.request", "body": b"", "more_body": True}
        for _ in range(5_000)
    ]
    incoming.extend(
        [
            {"type": "http.request", "body": b"{}", "more_body": False},
        ]
    )

    async def receive() -> Message:
        return incoming.pop(0)

    async def send(message: Message) -> None:
        return None

    asyncio.run(
        middleware(
            {
                "type": "http",
                "method": "POST",
                "path": ROUTE,
                "headers": [],
            },
            receive,
            send,
        )
    )

    assert downstream_messages == [
        {"type": "http.request", "body": b"{}", "more_body": False}
    ]


def test_body_guard_rejections_preserve_allowed_loopback_cors() -> None:
    origin = "http://localhost:5173"
    response = client.post(
        ROUTE,
        content=b"{" + b"x" * diagnostics.TAW06_MAX_REQUEST_BYTES,
        headers={
            "content-type": "application/json",
            "content-length": "1",
            "origin": origin,
        },
    )

    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == origin
    assert "Origin" in response.headers["vary"]


def test_request_rejects_excessive_node_count_before_materialization() -> None:
    payload = _request(_decision(FamiliarityState.familiar_supported))
    payload["padding"] = [None] * diagnostics.TAW06_MAX_REQUEST_NODES

    with pytest.raises(ValidationError, match="request node bound"):
        ToolAwareDiagnosticRequest.model_validate(payload)


def test_request_rejects_raw_or_unknown_fields() -> None:
    payload = _request(_decision(FamiliarityState.familiar_supported))
    payload["raw_prompt"] = "do not retain this"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ToolAwareDiagnosticRequest.model_validate(payload)


def test_cli_json_and_api_return_the_exact_shared_read_model() -> None:
    request_payload = _request(_decision(FamiliarityState.familiar_requires_approval))
    api_response = client.post(ROUTE, json=request_payload)

    completed = subprocess.run(
        [sys.executable, str(CLI), "--json"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        input=json.dumps(request_payload),
        capture_output=True,
        text=True,
        check=False,
    )

    assert api_response.status_code == 200
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == api_response.json()


def test_human_cli_hides_evidence_machinery_and_states_limits() -> None:
    request_payload = _request(_decision(FamiliarityState.ambiguous))
    completed = subprocess.run(
        [sys.executable, str(CLI)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        input=json.dumps(request_payload),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Route: Clarification recommended" in completed.stdout
    assert "Familiarity: Capability intent ambiguous" in completed.stdout
    assert "Approval posture remains unknown" in completed.stdout
    assert "decision_fingerprint_ref" not in completed.stdout
    assert "reason_refs" not in completed.stdout


def test_cli_translates_extreme_json_nesting_to_redacted_blocked_output() -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "--json"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "src"},
        input="[" * 10_000 + "]" * 10_000,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert json.loads(completed.stderr) == {
        "raw_content_included": False,
        "raw_local_paths_included": False,
        "reason_ref": "reason-ref:taw06:diagnostic-input-invalid",
        "safe_summary": (
            "Diagnostic input must be one bounded safe-ref-only TAW-06 request."
        ),
        "status": "blocked",
    }
    assert str(ROOT) not in completed.stderr


def test_api_rejects_raw_fields_and_is_protected_without_dev_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_payload = _request(_decision(FamiliarityState.familiar_supported))
    invalid = {**request_payload, "raw_response": "not allowed"}
    assert client.post(ROUTE, json=invalid).status_code == 422

    monkeypatch.delenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", raising=False)
    response = client.post(ROUTE, json=request_payload)
    assert response.status_code == 503
    assert response.json()["code"] == "LOCAL_API_AUTH_NOT_CONFIGURED"


def test_api_manifest_openapi_and_side_effect_contract_are_exact() -> None:
    manifest = build_api_manifest(app)
    route = next(
        item for item in manifest.routes if item.path == ROUTE and item.method == "POST"
    )
    openapi_operation = app.openapi()["paths"][ROUTE]["post"]

    assert route.operation_id == "preview_tool_aware_capability_diagnostics"
    assert route.side_effect_class == "validation_only"
    assert route.route_classification == "local_sensitive"
    assert route.protected_route
    assert route.auth_posture == "protected_local_bearer_required"
    assert not route.idempotency_required
    assert openapi_operation["operationId"] == route.operation_id
    response_413 = openapi_operation["responses"]["413"]
    assert response_413["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CapabilityDiagnosticBodyTooLargeResponse"
    }
    response_422 = openapi_operation["responses"]["422"]
    assert response_422["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ResultEnvelope"
    }
    assert "tool_aware_operator_diagnostics_shared_read_model" in (
        manifest.capabilities_declared
    )
    assert "tool_aware_operator_diagnostics_as_runtime_authority" in (
        manifest.capabilities_blocked
    )
