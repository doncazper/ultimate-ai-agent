import json
from pathlib import Path

from pydantic import ValidationError

from ultimate_ai_agent.core.execution import (
    ProviderToolRuntimeInvocationEnvelope,
    ProviderToolRuntimeResultContract,
    ProviderToolRuntimeStreamEventContract,
    ProviderToolRuntimeValidationContext,
    sanitize_provider_tool_runtime_replay,
    validate_provider_tool_runtime_invocation,
    validate_provider_tool_stream_events,
)


KNOWN_PROVIDER_REF = "provider-ref:test:exact"
KNOWN_TOOL_REF = "tool-ref:test:exact"


def _provider_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_ref": "run-ref:test:provider-tool",
        "invocation_ref": "invocation-ref:test:provider-tool",
        "target_kind": "provider",
        "provider_ref": KNOWN_PROVIDER_REF,
        "exact_approval_scope_ref": "approval-scope-ref:test:exact",
        "approval_ref": "approval-ref:test:exact",
        "idempotency_ref": "idempotency-ref:test:provider-tool",
        "redacted_input_ref": "redacted-input-ref:test:provider-tool",
        "expected_result_schema_ref": "result-schema-ref:test:provider-tool",
        "cost_estimate_ref": "cost-estimate-ref:test:provider-tool",
        "max_approved_usd_ref": "max-usd-ref:test:provider-tool",
        "privacy_posture_ref": "privacy-posture-ref:test:provider-tool",
        "replay_posture_ref": "replay-posture-ref:test:provider-tool",
        "rollback_posture_ref": "rollback-posture-ref:test:provider-tool",
        "safe_disable_posture_ref": "safe-disable-posture-ref:test:provider-tool",
        "redaction_posture_ref": "redaction-posture-ref:test:provider-tool",
        "authority_boundary_refs": ["authority-boundary-ref:test:provider-tool"],
        "evidence_refs": ["evidence-ref:test:provider-tool"],
        "safe_summary": "Contract-only provider runtime metadata for future exact-approved execution.",
    }
    payload.update(overrides)
    return payload


def _tool_payload(**overrides: object) -> dict[str, object]:
    payload = _provider_payload(
        target_kind="tool",
        provider_ref=None,
        tool_ref=KNOWN_TOOL_REF,
        safe_summary="Contract-only tool runtime metadata for future exact-approved execution.",
    )
    payload.update(overrides)
    return payload


def _valid_context(**overrides: object) -> ProviderToolRuntimeValidationContext:
    payload: dict[str, object] = {
        "known_provider_refs": [KNOWN_PROVIDER_REF],
        "known_tool_refs": [KNOWN_TOOL_REF],
        "local_approval_authority_validated": True,
        "approval_scope_matches": True,
        "paid_cost_known": True,
        "actual_cost_complete": True,
    }
    payload.update(overrides)
    return ProviderToolRuntimeValidationContext.model_validate(payload)


def test_valid_provider_contract_validates_without_execution_authority() -> None:
    envelope = ProviderToolRuntimeInvocationEnvelope.model_validate(_provider_payload())

    decision = validate_provider_tool_runtime_invocation(envelope, _valid_context())

    assert decision.validation_status == "valid_contract_only"
    assert decision.contract_valid is True
    assert decision.blocked is False
    assert decision.execution_permitted is False
    assert decision.execution_performed is False
    assert decision.runtime_activation_enabled is False
    assert decision.reason_codes == ["CONTRACT_VALID_NO_EXECUTION"]


def test_unknown_provider_and_tool_block_by_default() -> None:
    provider_decision = validate_provider_tool_runtime_invocation(
        _provider_payload(provider_ref="provider-ref:test:unknown"),
        _valid_context(known_provider_refs=[]),
    )
    tool_decision = validate_provider_tool_runtime_invocation(
        _tool_payload(tool_ref="tool-ref:test:unknown"),
        _valid_context(known_tool_refs=[]),
    )

    assert provider_decision.blocked is True
    assert "UNKNOWN_PROVIDER_BLOCKED" in provider_decision.reason_codes
    assert tool_decision.blocked is True
    assert "UNKNOWN_TOOL_BLOCKED" in tool_decision.reason_codes


def test_missing_approval_and_scope_mismatch_block() -> None:
    missing_approval = _provider_payload()
    missing_approval.pop("approval_ref")

    missing_decision = validate_provider_tool_runtime_invocation(missing_approval, _valid_context())
    mismatch_decision = validate_provider_tool_runtime_invocation(
        _provider_payload(),
        _valid_context(approval_scope_matches=False),
    )

    assert missing_decision.validation_status == "approval_required"
    assert "MISSING_EXACT_APPROVAL_BLOCKED" in missing_decision.reason_codes
    assert mismatch_decision.blocked is True
    assert "APPROVAL_SCOPE_MISMATCH_BLOCKED" in mismatch_decision.reason_codes


def test_unknown_paid_cost_and_incomplete_actual_cost_block() -> None:
    unknown_cost = validate_provider_tool_runtime_invocation(
        _provider_payload(),
        _valid_context(paid_cost_known=False),
    )
    incomplete_cost = validate_provider_tool_runtime_invocation(
        _provider_payload(),
        _valid_context(actual_cost_complete=False),
    )

    assert unknown_cost.validation_status == "cost_blocked"
    assert "UNKNOWN_PAID_COST_BLOCKED" in unknown_cost.reason_codes
    assert incomplete_cost.validation_status == "cost_blocked"
    assert "INCOMPLETE_ACTUAL_COST_BLOCKED" in incomplete_cost.reason_codes


def test_missing_cost_idempotency_and_redaction_refs_block_before_execution() -> None:
    missing_cost = _provider_payload()
    missing_cost.pop("cost_estimate_ref")
    missing_idempotency = _provider_payload()
    missing_idempotency.pop("idempotency_ref")
    missing_redaction = _provider_payload()
    missing_redaction.pop("redaction_posture_ref")

    assert "MISSING_COST_ESTIMATE_REF_BLOCKED" in validate_provider_tool_runtime_invocation(
        missing_cost,
        _valid_context(),
    ).reason_codes
    assert "MISSING_IDEMPOTENCY_REF_BLOCKED" in validate_provider_tool_runtime_invocation(
        missing_idempotency,
        _valid_context(),
    ).reason_codes
    assert "MISSING_REDACTION_POSTURE_REF_BLOCKED" in validate_provider_tool_runtime_invocation(
        missing_redaction,
        _valid_context(),
    ).reason_codes


def test_raw_payload_like_fields_block() -> None:
    decision = validate_provider_tool_runtime_invocation(
        {
            **_provider_payload(),
            "raw_prompt": "Do a provider call with hidden content.",
        },
        _valid_context(),
    )

    assert decision.blocked is True
    assert "RAW_PAYLOAD_LIKE_FIELD_BLOCKED" in decision.reason_codes


def test_result_contract_rejects_execution_flags_and_requires_redacted_output() -> None:
    result = ProviderToolRuntimeResultContract(
        run_ref="run-ref:test:provider-tool",
        invocation_ref="invocation-ref:test:provider-tool",
        status="redacted_result_ready",
        redacted_output_ref="redacted-output-ref:test:provider-tool",
        usage_receipt_refs=["usage-receipt-ref:test:provider-tool"],
        cost_receipt_refs=["cost-receipt-ref:test:provider-tool"],
        evidence_refs=["evidence-ref:test:result"],
        safe_summary="Redacted result ref is available without runtime execution authority.",
    )

    assert result.execution_performed is False
    assert result.provider_model_called is False
    assert result.tool_executed is False
    try:
        ProviderToolRuntimeResultContract(
            run_ref="run-ref:test:provider-tool",
            invocation_ref="invocation-ref:test:provider-tool",
            status="redacted_result_ready",
            safe_summary="Missing redacted output ref must fail.",
        )
    except ValidationError as exc:
        assert "REDACTED_OUTPUT_REF_REQUIRED" in str(exc)
    else:
        raise AssertionError("missing redacted output ref should fail")


def test_stream_events_preserve_ordered_durable_run_shape() -> None:
    events = [
        ProviderToolRuntimeStreamEventContract(
            run_ref="run-ref:test:provider-tool",
            invocation_ref="invocation-ref:test:provider-tool",
            sequence=1,
            event_type="stream_started",
            durable_run_event_ref="run-event-ref:test:stream:1",
            safe_summary="Stream metadata started; no live stream opened.",
        ),
        ProviderToolRuntimeStreamEventContract(
            run_ref="run-ref:test:provider-tool",
            invocation_ref="invocation-ref:test:provider-tool",
            sequence=2,
            event_type="stream_delta_redacted",
            durable_run_event_ref="run-event-ref:test:stream:2",
            redacted_delta_ref="redacted-delta-ref:test:stream:2",
            safe_summary="Redacted delta ref recorded; raw chunk omitted.",
        ),
        ProviderToolRuntimeStreamEventContract(
            run_ref="run-ref:test:provider-tool",
            invocation_ref="invocation-ref:test:provider-tool",
            sequence=3,
            event_type="stream_completed",
            durable_run_event_ref="run-event-ref:test:stream:3",
            receipt_refs=["receipt-ref:test:stream:3"],
            evidence_refs=["evidence-ref:test:stream:3"],
            safe_summary="Stream metadata completed; no provider stream was called.",
        ),
    ]

    decision = validate_provider_tool_stream_events(events)

    assert decision.validation_status == "valid_contract_only"
    assert decision.execution_permitted is False
    assert decision.reason_codes == ["STREAM_EVENTS_ORDERED_UNDER_DURABLE_RUN_LOG"]


def test_stream_events_reject_raw_chunk_fields_and_bad_order() -> None:
    raw_event_decision = validate_provider_tool_stream_events(
        [
            {
                "run_ref": "run-ref:test:provider-tool",
                "invocation_ref": "invocation-ref:test:provider-tool",
                "sequence": 1,
                "event_type": "stream_delta_redacted",
                "durable_run_event_ref": "run-event-ref:test:stream:1",
                "raw_chunk": "raw response chunk",
                "safe_summary": "Raw chunk should not validate.",
            }
        ]
    )
    bad_order_decision = validate_provider_tool_stream_events(
        [
            ProviderToolRuntimeStreamEventContract(
                run_ref="run-ref:test:provider-tool",
                invocation_ref="invocation-ref:test:provider-tool",
                sequence=2,
                event_type="stream_started",
                durable_run_event_ref="run-event-ref:test:stream:2",
                safe_summary="Second sequence first.",
            ),
            ProviderToolRuntimeStreamEventContract(
                run_ref="run-ref:test:provider-tool",
                invocation_ref="invocation-ref:test:provider-tool",
                sequence=1,
                event_type="stream_completed",
                durable_run_event_ref="run-event-ref:test:stream:1",
                safe_summary="First sequence second.",
            ),
        ]
    )

    assert raw_event_decision.validation_status == "validation_failed"
    assert bad_order_decision.blocked is True
    assert "STREAM_EVENT_SEQUENCE_NOT_MONOTONIC" in bad_order_decision.reason_codes


def test_replay_sanitization_excludes_raw_content() -> None:
    envelope = ProviderToolRuntimeInvocationEnvelope.model_validate(_provider_payload())
    result = ProviderToolRuntimeResultContract(
        run_ref=envelope.run_ref,
        invocation_ref=envelope.invocation_ref,
        status="redacted_result_ready",
        redacted_output_ref="redacted-output-ref:test:provider-tool",
        usage_receipt_refs=["usage-receipt-ref:test:provider-tool"],
        cost_receipt_refs=["cost-receipt-ref:test:provider-tool"],
        evidence_refs=["evidence-ref:test:result"],
        safe_summary="Redacted result ref only.",
    )
    event = ProviderToolRuntimeStreamEventContract(
        run_ref=envelope.run_ref,
        invocation_ref=envelope.invocation_ref,
        sequence=1,
        event_type="stream_delta_redacted",
        durable_run_event_ref="run-event-ref:test:stream:1",
        redacted_delta_ref="redacted-delta-ref:test:stream:1",
        safe_summary="Redacted delta ref only.",
    )

    replay = sanitize_provider_tool_runtime_replay(envelope, result, [event])
    replay_json = json.dumps(replay.model_dump(mode="json"), sort_keys=True)

    assert replay.safe_refs_only is True
    assert replay.raw_content_omitted is True
    assert "redacted-input-ref:test:provider-tool" in replay.redacted_refs
    assert "redacted-output-ref:test:provider-tool" in replay.redacted_refs
    assert "raw prompt" not in replay_json.lower()
    assert "provider payload" not in replay_json.lower()
    assert "tool payload" not in replay_json.lower()


def test_contract_module_does_not_import_provider_sdk_network_or_executors() -> None:
    source = Path("src/ultimate_ai_agent/core/execution/provider_tool_runtime_safety.py").read_text()
    forbidden_snippets = [
        "import openai",
        "import anthropic",
        "import requests",
        "import httpx",
        "import urllib",
        "import selenium",
        "import playwright",
        "from ultimate_ai_agent.core.providers.live_invocation_adapter",
        "from ultimate_ai_agent.core.providers.invocation import",
        "from ultimate_ai_agent.core.tools.runtime.invocation",
    ]

    for snippet in forbidden_snippets:
        assert snippet not in source
