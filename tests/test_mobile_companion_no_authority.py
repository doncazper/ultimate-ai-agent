import pytest

from ultimate_ai_agent.core.mobile_companion import MobileClientPlatform, MobileCompanionSurface
from ultimate_ai_agent.core.mobile_companion.contracts import MobileClientPlan, MobileCompanionManifest
from ultimate_ai_agent.core.mobile_companion.planning import assert_mobile_contract_only


def test_mobile_client_authority_claim_is_rejected():
    client = MobileClientPlan(
        platform=MobileClientPlatform.android_planned,
        surfaces=[MobileCompanionSurface.approval_status_planned],
        safe_summary="Android status surface planning only",
        authority_claimed=True,
    )
    manifest = MobileCompanionManifest(
        clients=[client],
        capabilities=[],
        safe_summary="mobile companion planning manifest",
    )

    with pytest.raises(ValueError, match="authority"):
        assert_mobile_contract_only(manifest)


def test_mobile_approval_execution_claim_is_rejected():
    manifest = MobileCompanionManifest(
        clients=[],
        capabilities=[],
        safe_summary="mobile companion planning manifest",
        mobile_approval_execution_implemented=True,
    )

    with pytest.raises(ValueError, match="approval execution"):
        assert_mobile_contract_only(manifest)


def test_secret_like_safe_summary_is_rejected():
    manifest = MobileCompanionManifest(
        clients=[],
        capabilities=[],
        safe_summary="token=abc123secret should never appear",
    )

    with pytest.raises(ValueError, match="secret"):
        assert_mobile_contract_only(manifest)
