from typing import Any, Iterator
from datetime import UTC, datetime

import pytest

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.hygiene.temporal_context import FreshnessClass, StalenessPolicy, TemporalContext
from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
from ultimate_ai_agent.core.observability import (
    ObservabilityExportFormat,
    RedactedObservabilityExportPolicy,
    RedactedObservabilityExportRequest,
    RedactedObservabilityExportStatus,
    build_redacted_observability_export,
    validate_redacted_observability_export_policy,
    validate_redacted_observability_export_request,
)


def _contexts() -> tuple[Any, ...]:
    return (
        ActorContext(
            actor_type=ActorType.orchestrator,
            actor_id="m55-orchestrator",
            authority_source=AuthoritySource.explicit_user_request,
            created_at=datetime.now(UTC),
        ),
        TemporalContext(
            current_time_utc=datetime.now(UTC),
            freshness_class=FreshnessClass.daily,
            staleness_policy=StalenessPolicy.allow_with_label,
        ),
        DataClassification(classification=ClassificationValue.project_private, source="m55-test"),
    )


def _event(**overrides: Any) -> Any:
    actor, temporal, classification = _contexts()
    data = {
        "event_id": "evt_m55_001",
        "event_type": "run",
        "event_name": EventName.run_completed,
        "run_id": "run_m55",
        "trace_id": "trace_m55",
        "span_id": "span_m55",
        "correlation_id": "corr_m55",
        "actor_context": actor,
        "temporal_context": temporal,
        "data_classification": classification,
        "redaction_summary": {"status": "redacted", "fields": ["prompt", "provider_payload"]},
        "event_source": "ultimate-ai-agent",
        "subject": "M55 redacted observability",
        "action": "summarize",
        "outcome": "completed",
        "status": "success",
        "severity": "info",
        "evidence_refs": ["evidence:m55-redacted"],
        "metadata": {"safe_summary": "Run completed with redacted summary only."},
    }
    data.update(overrides)
    return EventLedgerEvent(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "observability-export-request:m55",
        "run_ref": "run:run_m55",
        "export_ref": "observability-export:m55",
        "requested_formats": [ObservabilityExportFormat.internal_redacted_json],
        "source_event_refs": ["event:evt_m55_001"],
        "redaction_policy_ref": "redaction-policy:m55",
    }
    data.update(overrides)
    return RedactedObservabilityExportRequest(**data)


def test_redacted_observability_export_builds_safe_contract_bundle() -> None:
    bundle = build_redacted_observability_export(_request(), [_event()])

    assert bundle.status == RedactedObservabilityExportStatus.ready
    assert bundle.export_performed is False
    assert bundle.external_delivery_performed is False
    assert bundle.raw_prompt_exported is False
    assert bundle.raw_provider_payload_exported is False
    assert bundle.secret_exported is False
    assert bundle.saas_sdk_enabled is False
    assert bundle.network_call_performed is False
    assert bundle.receipt_plan is not None
    assert bundle.receipt_plan.side_effects_performed == []
    assert bundle.items[0].event_ref == "event:evt_m55_001"
    assert bundle.items[0].safe_summary == "Run completed with redacted summary only."
    assert "raw prompt body" not in str(bundle.model_dump())
    assert "provider payload body" not in str(bundle.model_dump())


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("raw_prompt_export_requested", "RAW_PROMPT_EXPORT_DENIED"),
        ("raw_provider_payload_export_requested", "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
        ("raw_private_content_export_requested", "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
        ("secret_export_requested", "SECRET_EXPORT_DENIED"),
        ("external_saas_export_requested", "EXTERNAL_SAAS_EXPORT_DENIED"),
        ("network_export_requested", "NETWORK_EXPORT_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ],
)
def test_redacted_observability_export_request_rejects_unsafe_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_redacted_observability_export_request(_request(**{field: True}))


def test_redacted_observability_export_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "raw_prompt_export_requested": True,
            "network_export_requested": True,
        }
    )

    with pytest.raises(ValueError, match="RAW_PROMPT_EXPORT_DENIED"):
        build_redacted_observability_export(request, [_event()])


def test_redacted_observability_export_rejects_secret_like_event_metadata() -> None:
    unsafe_event = _event(metadata={"safe_summary": "api_key='abcde12345678901234'"})

    with pytest.raises(ValueError, match="SECRET_LIKE_OBSERVABILITY_CONTENT_DENIED"):
        build_redacted_observability_export(_request(), [unsafe_event])


def test_redacted_observability_export_rejects_private_summary_identifiers() -> None:
    unsafe_event = _event(metadata={"safe_summary": "Contact alice@example.com for the raw trace."})

    with pytest.raises(ValueError, match="PRIVATE_OBSERVABILITY_SUMMARY_DENIED"):
        build_redacted_observability_export(_request(), [unsafe_event])


def test_redacted_observability_export_rejects_run_ref_mismatch() -> None:
    with pytest.raises(ValueError, match="OBSERVABILITY_EXPORT_RUN_REF_MISMATCH"):
        build_redacted_observability_export(_request(run_ref="run:other"), [_event()])


def test_redacted_observability_export_stops_after_requested_events() -> None:
    def event_stream() -> Iterator[Any]:
        yield _event()
        raise AssertionError("unrequested events should not be consumed")

    bundle = build_redacted_observability_export(_request(), event_stream())

    assert bundle.items[0].event_ref == "event:evt_m55_001"


def test_redacted_observability_export_policy_denies_transport_and_authority_flags() -> None:
    policy = RedactedObservabilityExportPolicy(
        external_saas_sdk_enabled=True,
        network_delivery_enabled=True,
        raw_prompt_export_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="EXTERNAL_SAAS_SDK_DENIED"):
        validate_redacted_observability_export_policy(policy)


def test_redacted_observability_export_denies_missing_event_ref_binding() -> None:
    with pytest.raises(ValueError, match="OBSERVABILITY_EXPORT_EVENT_REF_MISMATCH"):
        build_redacted_observability_export(_request(source_event_refs=["event:missing"]), [_event()])
