import uuid
from typing import Optional
from ultimate_ai_agent.core.tools.enums import ToolDecisionStatus, ToolRiskLevel, ToolCategory, ToolExecutionMode
from ultimate_ai_agent.core.tools.manifests import DryRunPlan
from ultimate_ai_agent.core.tools.requests import ToolRequest
from ultimate_ai_agent.core.tools.decisions import ToolDecision
from ultimate_ai_agent.core.tools.registry import ToolRegistry
from ultimate_ai_agent.core.tools.capability_firewall import CapabilityFirewallPolicy
from ultimate_ai_agent.core.consent.ledger import ConsentLedger
from ultimate_ai_agent.core.consent.decisions import ConsentQuery
from ultimate_ai_agent.core.consent.enums import PermissionAction, PermissionRisk
from ultimate_ai_agent.core.contracts.execution_contract import ExecutionContract
from ultimate_ai_agent.core.contracts.context_pack import ContextPack

class ToolBroker:
    def __init__(self, registry: ToolRegistry, firewall_policy: CapabilityFirewallPolicy):
        self.registry = registry
        self.firewall_policy = firewall_policy

    def evaluate_request(
        self,
        request: ToolRequest,
        consent_ledger: ConsentLedger,
        execution_contract: Optional[ExecutionContract] = None,
        context_pack: Optional[ContextPack] = None
    ) -> ToolDecision:
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"
        tool_id = request.tool_id
        
        manifest = self.registry.get_tool(tool_id)
        if not manifest:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.denied,
                risk_level=ToolRiskLevel.forbidden,
                reason_codes=["TOOL_NOT_FOUND"],
                safe_message=f"Tool '{tool_id}' not registered in the system."
            )

        # M1 Integration: Respect ExecutionContract allowed/forbidden list
        if execution_contract:
            # Let's mock a simple dict lookup or list lookup.
            # In M1 execution_contract, we can have forbidden_tools list or allowed_tools list if we set them,
            # or check custom contract properties.
            # Let's check metadata or custom fields in execution_contract.
            if hasattr(execution_contract, "forbidden_tools") and execution_contract.forbidden_tools:
                if tool_id in execution_contract.forbidden_tools:
                    return ToolDecision(
                        decision_id=decision_id,
                        request_id=request.request_id,
                        tool_id=tool_id,
                        status=ToolDecisionStatus.denied,
                        risk_level=manifest.risk_level,
                        reason_codes=["CONTRACT_FORBIDDEN_TOOL"],
                        safe_message="Tool execution is explicitly blocked by the Execution Contract policy."
                    )
            if hasattr(execution_contract, "allowed_tools") and execution_contract.allowed_tools:
                if tool_id not in execution_contract.allowed_tools:
                    return ToolDecision(
                        decision_id=decision_id,
                        request_id=request.request_id,
                        tool_id=tool_id,
                        status=ToolDecisionStatus.denied,
                        risk_level=manifest.risk_level,
                        reason_codes=["CONTRACT_NOT_ALLOWED_TOOL"],
                        safe_message="Tool execution is not in the Execution Contract allowed list."
                    )

        # M1 Integration: Respect ContextPack tool_permissions
        if context_pack:
            # In ContextPack we can check allowed scopes or custom tool permissions
            if hasattr(context_pack, "tool_permissions") and context_pack.tool_permissions:
                if tool_id not in context_pack.tool_permissions:
                    return ToolDecision(
                        decision_id=decision_id,
                        request_id=request.request_id,
                        tool_id=tool_id,
                        status=ToolDecisionStatus.denied,
                        risk_level=manifest.risk_level,
                        reason_codes=["CONTEXT_PACK_RESTRICTED_TOOL"],
                        safe_message="Tool execution is restricted by Context Pack boundaries."
                    )

        # Rule: MCP/A2A/SDK/Skill package categories are blocked by Foundation Gate
        if manifest.category in [ToolCategory.mcp, ToolCategory.a2a, ToolCategory.skill, ToolCategory.sdk_adapter]:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.blocked_by_foundation_gate,
                risk_level=manifest.risk_level,
                reason_codes=["FOUNDATION_GATE_BLOCKED"],
                safe_message="MCP/A2A/SDK/Skill adapters are blocked by the Foundation Gate security rule."
            )

        # Rule: Tools in production mode are denied in M3 (Dry-run/mock/local-dev only)
        if manifest.execution_mode == ToolExecutionMode.production:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.denied,
                risk_level=manifest.risk_level,
                reason_codes=["PRODUCTION_MODE_BLOCKED"],
                safe_message="Production-level tool execution is disabled before the Foundation Gate validation passes."
            )

        # Rule: Secret Broker / Credentials dependencies are blocked until M3.5
        if manifest.permission_manifest and manifest.permission_manifest.credentials_keys:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.denied,
                risk_level=manifest.risk_level,
                reason_codes=["SECRET_BROKER_REQUIRED"],
                safe_message="Tools requesting credentials are blocked until the Secret Broker (M3.5) is implemented."
            )

        # Rule: Capability Firewall checks
        passed, firewall_reasons = self.firewall_policy.check_firewall(manifest)
        if not passed:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.denied,
                risk_level=manifest.risk_level,
                reason_codes=firewall_reasons,
                safe_message="Blocked by Capability Firewall policy: " + ", ".join(firewall_reasons)
            )

        # Rule: Check Consent
        action_map = {
            "read": PermissionAction.read,
            "write": PermissionAction.write,
            "execute": PermissionAction.execute,
            "delete": PermissionAction.delete,
            "send": PermissionAction.send,
            "publish": PermissionAction.publish,
            "spend": PermissionAction.spend,
        }
        mapped_action = action_map.get(request.requested_action, PermissionAction.execute)

        risk_map = {
            ToolRiskLevel.safe: PermissionRisk.safe,
            ToolRiskLevel.low: PermissionRisk.low,
            ToolRiskLevel.medium: PermissionRisk.medium,
            ToolRiskLevel.high: PermissionRisk.high,
            ToolRiskLevel.critical: PermissionRisk.critical,
            ToolRiskLevel.forbidden: PermissionRisk.forbidden,
        }
        mapped_risk = risk_map.get(manifest.risk_level, PermissionRisk.low)

        consent_query = ConsentQuery(
            actor_id=request.actor_context.actor_id,
            action=mapped_action,
            resource=tool_id,
            data_classification=request.data_classification,
            purpose=request.purpose,
            risk_level=mapped_risk
        )

        consent_decision = consent_ledger.evaluate(consent_query)
        if not consent_decision.allowed:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.denied,
                risk_level=manifest.risk_level,
                consent_required=True,
                reason_codes=consent_decision.reason_codes,
                safe_message="Consent required: " + consent_decision.safe_message
            )

        # Rule: High/Critical risks and external mutations require human approval
        requires_approval = False
        approval_reasons = []

        if manifest.risk_level in [ToolRiskLevel.high, ToolRiskLevel.critical]:
            requires_approval = True
            approval_reasons.append("HIGH_RISK_LEVEL")
        
        # External mutable actions
        if request.requested_action in ["send", "publish", "delete", "spend"]:
            requires_approval = True
            approval_reasons.append("EXTERNAL_MUTATION_ACTION")

        if requires_approval and not request.approval_ref:
            return ToolDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                tool_id=tool_id,
                status=ToolDecisionStatus.approval_required,
                risk_level=manifest.risk_level,
                approval_required=True,
                matched_consent_refs=consent_decision.matched_grants,
                reason_codes=approval_reasons,
                safe_message="This tool requires manual human approval to execute."
            )

        # Rule: Dry-run handling
        dry_run_plan = None
        status = ToolDecisionStatus.allowed
        if request.dry_run_requested or self.firewall_policy.dry_run_required:
            if not manifest.supports_dry_run:
                return ToolDecision(
                    decision_id=decision_id,
                    request_id=request.request_id,
                    tool_id=tool_id,
                    status=ToolDecisionStatus.denied,
                    risk_level=manifest.risk_level,
                    reason_codes=["DRY_RUN_UNSUPPORTED"],
                    safe_message="Dry-run was requested or required, but the tool manifest does not support it."
                )
            dry_run_plan = DryRunPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                tool_id=tool_id,
                estimated_risk=manifest.risk_level,
                steps=[f"Simulate tool start for '{tool_id}'", "Verify payload format", "Generate Dry-run receipt"],
                side_effects_prevented=["Mutable disk write", "External API post call"]
            )
            status = ToolDecisionStatus.dry_run_only

        return ToolDecision(
            decision_id=decision_id,
            request_id=request.request_id,
            tool_id=tool_id,
            status=status,
            risk_level=manifest.risk_level,
            matched_consent_refs=consent_decision.matched_grants,
            reason_codes=["AUTHORIZED"],
            safe_message="Tool request successfully authorized.",
            dry_run_plan=dry_run_plan
        )

    def dry_run(self, request: ToolRequest) -> DryRunPlan:
        manifest = self.registry.get_tool(request.tool_id)
        if not manifest or not manifest.supports_dry_run:
            raise ValueError(f"Tool '{request.tool_id}' does not support dry-run mode.")
        return DryRunPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            tool_id=request.tool_id,
            estimated_risk=manifest.risk_level,
            steps=[f"Verify request schema for '{request.tool_id}'", "Evaluate parameter borders"],
            side_effects_prevented=["Disk write block", "Memory cache bypass block"]
        )
