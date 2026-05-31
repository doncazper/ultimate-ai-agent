from datetime import datetime, timedelta
import pytest
from ultimate_ai_agent.core.consent import (
    ConsentLedger,
    ConsentGrant,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
    ConsentStatus,
)

@pytest.fixture
def dummy_grant_factory():
    def _make(consent_id="grant_123", actor="orchestrator", action=PermissionAction.read, status=ConsentStatus.active, denied_actions=None, expires_at=None):
        return ConsentGrant(
            consent_id=consent_id,
            subject_type=ConsentSubjectType.tool,
            subject_id="tool_abc",
            granted_to_actor=actor,
            on_behalf_of_user_id="user_123",
            scope_type=ConsentScopeType.project,
            allowed_actions=[action] if action else [],
            denied_actions=denied_actions or [],
            expires_at=expires_at,
            status=status,
            source="test"
        )
    return _make

def test_consent_ledger_add_and_revoke(dummy_grant_factory):
    ledger = ConsentLedger()
    grant = dummy_grant_factory(consent_id="g1")
    ledger.add_grant(grant)
    
    assert len(ledger.list_grants()) == 1
    
    ledger.revoke_grant("g1", "User revoked it")
    grants = ledger.list_grants()
    assert grants[0].status == ConsentStatus.revoked
    assert grants[0].revoked_at is not None

def test_consent_ledger_check_expiration(dummy_grant_factory):
    ledger = ConsentLedger()
    # Expired 1 hour ago
    grant = dummy_grant_factory(
        consent_id="g_exp",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    # Bypass validator check for future dates by manually appending/mocking status check
    ledger._grants.append(grant)
    
    ledger.check_expiration(datetime.utcnow())
    assert ledger.list_grants()[0].status == ConsentStatus.expired
