import pytest

from ultimate_ai_agent.core.extension_catalog import (
    ExtensionActivationGrantRecord,
    ExtensionActivationGrantStaleness,
    ExtensionActivationGrantStatus,
    ExtensionActivationRevocationRecord,
    ExtensionRevocationStatus,
    assert_extension_activation_grant_treatable_as_active,
    revoke_extension_activation_grant,
    validate_extension_activation_grant_batch,
    validate_extension_activation_grant_record,
    validate_extension_activation_revocation_record,
)


def _grant(**updates: object) -> ExtensionActivationGrantRecord:
    record = ExtensionActivationGrantRecord(
        activation_grant_ref="activation-grant:extension-inspection-demo",
        package_ref="extension-package:uaa-plugin-skill-boundary",
        manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
        version_ref="version:uaa-p2-050",
        actor_ref="actor:security-reviewer",
        approval_ref="approval:extension-inspection-demo",
        scope_ref="scope:read-only-inspection",
        capability_refs=["capability:extension-metadata-inspection"],
        requested_grant_refs=["grant-request:read-only-inspection"],
        grant_status=ExtensionActivationGrantStatus.granted,
        revocation_ref="revocation:extension-inspection-demo",
        audit_refs=["audit:uaa-p2-050"],
        receipt_refs=["receipt:extension-inspection-demo"],
        replay_ref="replay:extension-inspection-demo",
        safe_summary=(
            "Exact-scope extension activation grant record for inspection only; "
            "runtime import and execution remain disabled."
        ),
    )
    if updates:
        return record.model_copy(update=updates)
    return record


def _revocation(**updates: object) -> ExtensionActivationRevocationRecord:
    record = ExtensionActivationRevocationRecord(
        revocation_ref="revocation:extension-inspection-demo",
        activation_grant_ref="activation-grant:extension-inspection-demo",
        package_ref="extension-package:uaa-plugin-skill-boundary",
        manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
        version_ref="version:uaa-p2-050",
        actor_ref="actor:security-reviewer",
        approval_ref="approval:extension-inspection-demo",
        scope_ref="scope:read-only-inspection",
        revocation_status=ExtensionRevocationStatus.revoked,
        audit_refs=["audit:uaa-p2-050-revocation"],
        receipt_refs=["receipt:extension-inspection-demo-revoked"],
        replay_ref="replay:extension-inspection-demo-revoked",
        safe_summary=(
            "Exact-scope extension activation revocation record; runtime import "
            "and execution remain disabled."
        ),
    )
    if updates:
        return record.model_copy(update=updates)
    return record


def test_extension_activation_grant_is_exact_scope_and_no_runtime_authority() -> None:
    record = assert_extension_activation_grant_treatable_as_active(_grant())

    payload = record.model_dump(mode="json")
    assert payload["schema_version"] == "uaa_extension_activation_grant.v1"
    assert payload["exact_scope"] is True
    assert payload["overbroad_scope"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["network_access_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["mobile_control_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert payload["approval_ref"].startswith("approval:")
    assert payload["audit_refs"] == ["audit:uaa-p2-050"]


@pytest.mark.parametrize(
    "updates",
    [
        {"exact_scope": False},
        {"overbroad_scope": True},
    ],
)
def test_extension_activation_grant_denies_overbroad_scope(updates: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_EXACT_SCOPE_REQUIRED"):
        validate_extension_activation_grant_record(_grant(**updates))


def test_extension_activation_grant_denies_missing_approval() -> None:
    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_APPROVAL_REQUIRED"):
        validate_extension_activation_grant_record(
            _grant(approval_ref="approval:missing")
        )


def test_extension_activation_grant_denies_duplicate_attempts() -> None:
    first = _grant()
    duplicate_binding = _grant(
        activation_grant_ref="activation-grant:extension-inspection-demo-copy"
    )

    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_DUPLICATE_GRANT_DENIED"):
        validate_extension_activation_grant_batch([first, duplicate_binding])


def test_revoked_extension_activation_grant_cannot_be_treated_active() -> None:
    revoked = revoke_extension_activation_grant(_grant(), _revocation())

    assert revoked.grant_status == ExtensionActivationGrantStatus.revoked
    assert revoked.revocation_ref == "revocation:extension-inspection-demo"
    assert "audit:uaa-p2-050-revocation" in revoked.audit_refs
    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_REVOKED_GRANT_DENIED"):
        assert_extension_activation_grant_treatable_as_active(revoked)


def test_stale_extension_activation_grants_are_denied_for_active_use() -> None:
    granted_but_stale = _grant(
        staleness_status=ExtensionActivationGrantStaleness.stale
    )
    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_STALE_GRANT_DENIED"):
        validate_extension_activation_grant_record(granted_but_stale)

    stale_record = _grant(
        grant_status=ExtensionActivationGrantStatus.stale,
        staleness_status=ExtensionActivationGrantStaleness.stale,
    )
    with pytest.raises(ValueError, match="EXTENSION_ACTIVATION_STALE_GRANT_DENIED"):
        assert_extension_activation_grant_treatable_as_active(stale_record)


@pytest.mark.parametrize(
    "field",
    [
        "runtime_import_enabled",
        "execution_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "mobile_control_enabled",
        "public_distribution_claimed",
    ],
)
def test_activation_grant_and_revocation_deny_runtime_authority_flags(field: str) -> None:
    with pytest.raises(ValueError, match=f"EXTENSION_ACTIVATION_{field.upper()}_DENIED"):
        validate_extension_activation_grant_record(_grant(**{field: True}))
    with pytest.raises(ValueError, match=f"EXTENSION_ACTIVATION_{field.upper()}_DENIED"):
        validate_extension_activation_revocation_record(_revocation(**{field: True}))
