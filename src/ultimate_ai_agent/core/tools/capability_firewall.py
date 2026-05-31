from pathlib import PurePosixPath
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from ultimate_ai_agent.core.tools.enums import ToolRiskLevel, ToolCategory
from ultimate_ai_agent.core.tools.manifests import ToolManifest

class CapabilityFirewallPolicy(BaseModel):
    allowed_filesystem_roots: List[str] = Field(default_factory=list)
    denied_filesystem_roots: List[str] = Field(default_factory=list)
    allowed_network_domains: List[str] = Field(default_factory=list)
    denied_network_domains: List[str] = Field(default_factory=list)
    allowed_credentials: List[str] = Field(default_factory=list)
    allowed_actions: List[str] = Field(default_factory=list)
    approval_required_actions: List[str] = Field(default_factory=list)
    audit_required: bool = False
    dry_run_required: bool = False
    diff_preview_required: bool = False
    quarantine_mode: bool = False
    max_risk_level: ToolRiskLevel = ToolRiskLevel.medium

    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def _is_unbounded_root(root: str) -> bool:
        return root in {"/", "*", "", "~"}

    @staticmethod
    def _is_root_allowed(requested_root: str, allowed_root: str) -> bool:
        requested = PurePosixPath(requested_root)
        allowed = PurePosixPath(allowed_root)
        return requested == allowed or allowed in requested.parents

    def check_firewall(self, manifest: ToolManifest) -> tuple[bool, List[str]]:
        reasons = []

        # Rule: MCP/A2A/SDK/Skill category tools are blocked by Foundation Gate
        # (Blocked list: mcp, a2a, skill, sdk_adapter)
        if manifest.category in [ToolCategory.mcp, ToolCategory.a2a, ToolCategory.skill, ToolCategory.sdk_adapter]:
            reasons.append("FOUNDATION_GATE_BLOCKED")
            return False, reasons

        # If permission manifest exists, check details
        if manifest.permission_manifest:
            # Filesystem check
            for root in manifest.permission_manifest.filesystem_roots:
                if self._is_unbounded_root(root):
                    reasons.append("UNBOUNDED_FILESYSTEM_ACCESS_DENIED")

                for denied in self.denied_filesystem_roots:
                    if root == denied or self._is_root_allowed(root, denied):
                        reasons.append("FILESYSTEM_ROOT_DENIED")

                if not self.allowed_filesystem_roots:
                    reasons.append("FILESYSTEM_ACCESS_NOT_ALLOWLISTED")
                elif not any(self._is_root_allowed(root, allowed) for allowed in self.allowed_filesystem_roots):
                    reasons.append("FILESYSTEM_ACCESS_NOT_ALLOWLISTED")

            for domain in manifest.permission_manifest.network_domains:
                if domain == "*":
                    reasons.append("ARBITRARY_NETWORK_ACCESS_DENIED")
                for denied in self.denied_network_domains:
                    if domain == denied or domain.endswith("." + denied):
                        reasons.append("NETWORK_DOMAIN_DENIED")
                if not self.allowed_network_domains:
                    reasons.append("NETWORK_ACCESS_NOT_ALLOWLISTED")
                elif domain not in self.allowed_network_domains:
                    reasons.append("NETWORK_ACCESS_NOT_ALLOWLISTED")

            for cred in manifest.permission_manifest.credentials_keys:
                reasons.append("CREDENTIAL_ACCESS_NOT_PERMITTED")

        # Risk level check
        risk_map = {
            ToolRiskLevel.safe: 0,
            ToolRiskLevel.low: 1,
            ToolRiskLevel.medium: 2,
            ToolRiskLevel.high: 3,
            ToolRiskLevel.critical: 4,
            ToolRiskLevel.forbidden: 5,
        }
        if risk_map[manifest.risk_level] > risk_map[self.max_risk_level]:
            reasons.append("EXCEEDS_MAX_RISK_LEVEL")

        return len(reasons) == 0, reasons

class ToolBrokerPolicy(BaseModel):
    policy_id: str
    firewall_policy: CapabilityFirewallPolicy
    enable_foundation_gate_blocks: bool = True

    model_config = ConfigDict(extra="forbid")
