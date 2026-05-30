from datetime import datetime
import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext, FreshnessClass, StalenessPolicy
from ultimate_ai_agent.core.hygiene.envelopes import ErrorEnvelope, ErrorCategory, Severity, ResultEnvelope, Classification
from ultimate_ai_agent.core.hygiene.policies import IdempotencyPolicy, OperationType, RetryClass, DataClassification, ClassificationValue, RedactionPolicy, RedactionSurface, RedactionAction, CapabilityFlag, Stage, Status

def test_actor_context_valid():
    ctx = ActorContext(
        actor_type=ActorType.human_user,
        actor_id="usr_123",
        actor_display_name="Alice",
        authority_source=AuthoritySource.explicit_user_request,
        workspace_id="ws_1",
        created_at=datetime.utcnow()
    )
    assert ctx.actor_id == "usr_123"
    assert ctx.actor_type == "human_user"

def test_actor_context_invalid_enum():
    with pytest.raises(ValidationError):
        ActorContext(
            actor_type="invalid_type",  # type: ignore
            actor_id="usr_123",
            authority_source=AuthoritySource.explicit_user_request
        )

def test_actor_context_extra_fields():
    with pytest.raises(ValidationError):
        ActorContext(
            actor_type=ActorType.human_user,
            actor_id="usr_123",
            authority_source=AuthoritySource.explicit_user_request,
            extra_field="not_allowed"  # type: ignore
        )

def test_temporal_context_valid():
    ctx = TemporalContext(
        current_time_utc=datetime.utcnow(),
        freshness_class=FreshnessClass.daily,
        staleness_policy=StalenessPolicy.allow_with_label
    )
    assert ctx.freshness_class == "daily"
    assert ctx.staleness_policy == "allow_with_label"

def test_temporal_context_invalid_negative_window():
    with pytest.raises(ValidationError):
        TemporalContext(
            freshness_class=FreshnessClass.hourly,
            freshness_window_seconds=-10
        )

def test_error_envelope_valid():
    err = ErrorEnvelope(
        code="ERR_AUTH_FAILED",
        category=ErrorCategory.authentication_error,
        message="Invalid API Key",
        safe_message="Authentication failed",
        severity=Severity.high,
        retryable=False,
        details_redacted=True,
        source="SecretBroker"
    )
    assert err.code == "ERR_AUTH_FAILED"
    assert err.severity == "high"

def test_result_envelope_valid():
    err = ErrorEnvelope(
        code="ERR_INVALID_INPUT",
        category=ErrorCategory.validation_error,
        safe_message="Input was validation error",
        severity=Severity.low,
        retryable=False,
        details_redacted=False,
        source="Gateway"
    )
    res = ResultEnvelope(
        success=False,
        operation="run_task",
        service="Orchestrator",
        trace_id="tr_999",
        data={"some": "data"},
        error=err,
        classification=Classification.project_private
    )
    assert res.success is False
    assert res.error is not None
    assert res.error.code == "ERR_INVALID_INPUT"

def test_idempotency_policy_valid():
    policy = IdempotencyPolicy(
        idempotency_key="key_12345678",
        operation_type=OperationType.file_write,
        retry_class=RetryClass.safe_retry,
        attempt_number=1,
        max_attempts=3
    )
    assert policy.idempotency_key == "key_12345678"
    assert policy.max_attempts == 3

def test_idempotency_policy_invalid_key_length():
    with pytest.raises(ValidationError):
        IdempotencyPolicy(
            idempotency_key="short",  # < 8 chars
            operation_type=OperationType.file_write,
            retry_class=RetryClass.safe_retry,
            attempt_number=1
        )

def test_data_classification_valid():
    cls = DataClassification(
        classification=ClassificationValue.sensitive_personal,
        source="user_profile",
        requires_redaction=True,
        requires_consent=True
    )
    assert cls.classification == "sensitive_personal"
    assert cls.requires_consent is True

def test_redaction_policy_valid():
    policy = RedactionPolicy(
        policy_id="pol_redact_secrets",
        surfaces=[RedactionSurface.prompts, RedactionSurface.event_ledger_payloads],
        actions=[RedactionAction.mask],
        default_action=RedactionAction.mask
    )
    assert policy.policy_id == "pol_redact_secrets"
    assert len(policy.surfaces) == 2

def test_capability_flag_valid():
    flag = CapabilityFlag(
        capability_id="cap_file_writer",
        enabled=True,
        stage=Stage.M0_5,
        requires_foundation_gate=True,
        status=Status.ready_for_build
    )
    assert flag.capability_id == "cap_file_writer"
    assert flag.stage == "M0.5"
