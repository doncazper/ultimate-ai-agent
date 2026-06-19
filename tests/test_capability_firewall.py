import pytest
from ultimate_ai_agent.core.tools import (
    ToolManifest,
    ToolPermissionManifest,
    ToolCategory,
    ToolExecutionMode,
    ToolRiskLevel,
    ToolPermissionKind,
    CapabilityFirewallPolicy,
)

@pytest.fixture
def base_manifest_factory():
    def _make(tool_id="test_tool", category=ToolCategory.file, risk=ToolRiskLevel.safe, perm_manifest=None):
        return ToolManifest(
            tool_id=tool_id,
            display_name="Test Tool",
            category=category,
            description="Testing capability firewall",
            execution_mode=ToolExecutionMode.dry_run,
            risk_level=risk,
            permissions_required=[ToolPermissionKind.filesystem_read] if perm_manifest else [],
            permission_manifest=perm_manifest,
            capability_flag="test_active",
            owner="orchestrator",
            source="system",
            version="1.0.0"
        )
    return _make

def test_firewall_denies_unbounded_filesystem(base_manifest_factory):
    # Unbounded root request ("/")
    perm = ToolPermissionManifest(
        required_permissions=[ToolPermissionKind.filesystem_read],
        filesystem_roots=["/"]
    )
    manifest = base_manifest_factory(perm_manifest=perm)
    
    firewall = CapabilityFirewallPolicy()
    passed, reasons = firewall.check_firewall(manifest)
    assert passed is False
    assert "UNBOUNDED_FILESYSTEM_ACCESS_DENIED" in reasons

def test_firewall_reason_codes_are_deduplicated(base_manifest_factory):
    # Two filesystem roots with an empty allowlist previously appended
    # FILESYSTEM_ACCESS_NOT_ALLOWLISTED once per root, polluting the reason list.
    perm = ToolPermissionManifest(
        required_permissions=[ToolPermissionKind.filesystem_read],
        filesystem_roots=["/workspace/a", "/workspace/b"],
    )
    manifest = base_manifest_factory(perm_manifest=perm)

    firewall = CapabilityFirewallPolicy()  # empty allowlist -> access not allowlisted
    passed, reasons = firewall.check_firewall(manifest)

    assert passed is False
    assert "FILESYSTEM_ACCESS_NOT_ALLOWLISTED" in reasons
    assert len(reasons) == len(set(reasons))

def test_firewall_denies_network_domain(base_manifest_factory):
    perm = ToolPermissionManifest(
        required_permissions=[ToolPermissionKind.network],
        network_domains=["untrusted-domain.com"]
    )
    manifest = base_manifest_factory(perm_manifest=perm)
    
    # Untrusted domain blocks
    firewall = CapabilityFirewallPolicy(
        denied_network_domains=["untrusted-domain.com"]
    )
    passed, reasons = firewall.check_firewall(manifest)
    assert passed is False
    assert "NETWORK_DOMAIN_DENIED" in reasons

def test_firewall_denies_unpermitted_credentials(base_manifest_factory):
    perm = ToolPermissionManifest(
        required_permissions=[ToolPermissionKind.credential],
        credentials_keys=["AWS_SECRET_KEY"]
    )
    manifest = base_manifest_factory(perm_manifest=perm)
    
    firewall = CapabilityFirewallPolicy(
        allowed_credentials=["GITHUB_TOKEN"]  # AWS is not whitelisted
    )
    passed, reasons = firewall.check_firewall(manifest)
    assert passed is False
    assert "CREDENTIAL_ACCESS_NOT_PERMITTED" in reasons
