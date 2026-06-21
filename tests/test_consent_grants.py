from datetime import UTC, datetime, timedelta
import pytest
from ultimate_ai_agent.core.consent import (
    ConsentGrant,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
    validate_consent_grant,
)

def test_valid_consent_grant() -> None:
    grant = ConsentGrant(
        consent_id="grant_1",
        subject_type=ConsentSubjectType.tool,
        subject_id="file_writer",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.write],
        expires_at=datetime.now(UTC) + timedelta(days=1),
        source="user_interface"
    )
    assert validate_consent_grant(grant) is True

def test_invalid_consent_grant_missing_id() -> None:
    grant = ConsentGrant(
        consent_id="",
        subject_type=ConsentSubjectType.tool,
        subject_id="file_writer",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.write],
        source="user_interface"
    )
    with pytest.raises(ValueError, match="must have a valid non-empty consent_id"):
        validate_consent_grant(grant)

def test_invalid_consent_grant_expired() -> None:
    grant = ConsentGrant(
        consent_id="grant_expired",
        subject_type=ConsentSubjectType.tool,
        subject_id="file_writer",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.write],
        expires_at=datetime.now(UTC) - timedelta(days=1),
        source="user_interface"
    )
    with pytest.raises(ValueError, match="expires_at must be in the future"):
        validate_consent_grant(grant)

def test_invalid_consent_grant_overlapping_actions() -> None:
    grant = ConsentGrant(
        consent_id="grant_overlap",
        subject_type=ConsentSubjectType.tool,
        subject_id="file_writer",
        granted_to_actor="orchestrator",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.project,
        allowed_actions=[PermissionAction.write],
        denied_actions=[PermissionAction.write],
        source="user_interface"
    )
    with pytest.raises(ValueError, match="overlapping actions"):
        validate_consent_grant(grant)
