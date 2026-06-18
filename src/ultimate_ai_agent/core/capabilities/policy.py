from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.capabilities.enums import CapabilityHealthStatus, PolicyDecisionStatus, RiskLevel as CoordinationRiskLevel
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    CapabilityRunContext,
    CapabilitySpec,
    PolicyDecision,
    TaskEnvelope,
    TaskPlan,
    is_mutating_side_effect,
    is_read_only_side_effect,
    risk_rank,
)


def normalize_run_context(run_context: Any) -> CapabilityRunContext:
    if isinstance(run_context, CapabilityRunContext):
        return run_context
    if isinstance(run_context, dict):
        return CapabilityRunContext.model_validate(run_context)
    agent_name = getattr(run_context, "agent_name", None) or getattr(run_context, "actor_id", None) or "default"
    user_scopes = getattr(run_context, "user_scopes", None) or getattr(run_context, "scopes", None) or set()
    approval_ref = getattr(run_context, "approval_ref", None)
    trace_id = getattr(run_context, "trace_id", None)
    metadata = getattr(run_context, "metadata", None) or {}
    return CapabilityRunContext(
        agent_name=str(agent_name),
        user_scopes=set(user_scopes),
        approval_ref=approval_ref,
        trace_id=trace_id,
        metadata=dict(metadata),
    )


def policy_denial_reasons(spec: CapabilitySpec, agent_name: str, user_scopes: set[str]) -> list[str]:
    reasons: list[str] = []
    if spec.policy.allowed_agents and agent_name not in spec.policy.allowed_agents:
        reasons.append("AGENT_NOT_ALLOWED")
    missing_scopes = spec.policy.required_scopes - user_scopes
    if missing_scopes:
        reasons.append("REQUIRED_SCOPE_MISSING")
    if spec.policy.sandbox_required:
        reasons.append("SANDBOX_REQUIRED")
    return reasons


def can_retry(spec: CapabilitySpec) -> bool:
    return spec.policy.idempotent or spec.metadata.get("allow_non_idempotent_retries") is True


class PolicyEngine:
    def __init__(
        self,
        *,
        default_max_risk: CoordinationRiskLevel = CoordinationRiskLevel.critical,
        deny_deprecated: bool = True,
        deny_unhealthy: bool = True,
    ):
        self.default_max_risk = default_max_risk
        self.deny_deprecated = deny_deprecated
        self.deny_unhealthy = deny_unhealthy

    def can_select(self, capability: CapabilityManifest, context: dict[str, Any]) -> PolicyDecision:
        reasons = self._capability_denial_reasons(capability, context)
        if reasons:
            return PolicyDecision(
                status=PolicyDecisionStatus.denied,
                allowed=False,
                reason_codes=reasons,
                safe_message="Capability selection was denied by policy.",
                capability_id=capability.id,
            )
        return PolicyDecision(
            status=PolicyDecisionStatus.allowed,
            allowed=True,
            reason_codes=["CAPABILITY_SELECTION_ALLOWED"],
            safe_message="Capability selection is allowed.",
            capability_id=capability.id,
        )

    def can_execute(
        self,
        capability: CapabilityManifest,
        task: TaskEnvelope,
        context: dict[str, Any],
    ) -> PolicyDecision:
        reasons = self._capability_denial_reasons(capability, context)
        missing_context = [
            key for key in capability.context_policy.required_context_keys if key not in task.context and key not in context
        ]
        if missing_context:
            reasons.append("REQUIRED_CONTEXT_MISSING")
        if capability.allowed_coordination_modes and context.get("coordination_mode"):
            mode = context["coordination_mode"]
            allowed_modes = {item.value for item in capability.allowed_coordination_modes}
            if str(mode) not in allowed_modes:
                reasons.append("COORDINATION_MODE_DENIED")
        if context.get("coordination_mode") == "handoff" and not context.get("allow_handoff"):
            reasons.append("HANDOFF_REQUIRES_USER_FACING_OWNERSHIP")
        if reasons:
            return PolicyDecision(
                status=PolicyDecisionStatus.denied,
                allowed=False,
                reason_codes=list(dict.fromkeys(reasons)),
                safe_message="Capability execution was denied by policy.",
                capability_id=capability.id,
                task_id=task.task_id,
            )
        approval_required = self.requires_approval(capability, task, context)
        if approval_required.requires_approval and not task.context.get("approval_ref") and not context.get("approval_ref"):
            return approval_required
        return PolicyDecision(
            status=PolicyDecisionStatus.allowed,
            allowed=True,
            reason_codes=["CAPABILITY_EXECUTION_ALLOWED"],
            safe_message="Capability execution is allowed.",
            capability_id=capability.id,
            task_id=task.task_id,
        )

    def requires_approval(
        self,
        capability: CapabilityManifest,
        task: TaskEnvelope,
        context: dict[str, Any],
    ) -> PolicyDecision:
        reason_codes: list[str] = []
        if capability.approval_required:
            reason_codes.append("CAPABILITY_APPROVAL_REQUIRED")
        if capability.safety.approval_required:
            reason_codes.append("SAFETY_APPROVAL_REQUIRED")
        if capability.risk_level in {CoordinationRiskLevel.high, CoordinationRiskLevel.critical}:
            reason_codes.append("HIGH_RISK_REQUIRES_APPROVAL")
        if is_mutating_side_effect(capability.side_effects) and context.get("external_side_effect"):
            reason_codes.append("EXTERNAL_SIDE_EFFECT_REQUIRES_APPROVAL")
        if reason_codes:
            return PolicyDecision(
                status=PolicyDecisionStatus.approval_required,
                allowed=False,
                requires_approval=True,
                reason_codes=list(dict.fromkeys(reason_codes)),
                safe_message="Human approval is required before capability execution.",
                capability_id=capability.id,
                task_id=task.task_id,
            )
        return PolicyDecision(
            status=PolicyDecisionStatus.allowed,
            allowed=True,
            requires_approval=False,
            reason_codes=["APPROVAL_NOT_REQUIRED"],
            safe_message="Approval is not required.",
            capability_id=capability.id,
            task_id=task.task_id,
        )

    def validate_side_effects(self, plan: TaskPlan, registry: Any) -> PolicyDecision:
        reason_codes: list[str] = []
        mutating_nodes = []
        for node in plan.nodes:
            manifest = registry.load_manifest(node.capability_id)
            if node.expected_side_effects != manifest.side_effects:
                reason_codes.append("NODE_SIDE_EFFECT_MANIFEST_MISMATCH")
            if is_mutating_side_effect(node.expected_side_effects):
                mutating_nodes.append(node)
            if node.parallel_group and is_mutating_side_effect(node.expected_side_effects):
                reason_codes.append("PARALLEL_MUTATION_DENIED")
            if node.parallel_group and not is_read_only_side_effect(node.expected_side_effects):
                reason_codes.append("PARALLEL_NON_READ_ONLY_DENIED")
        if len(mutating_nodes) > 1:
            reason_codes.append("MULTIPLE_WRITER_NODES_DENIED")
        if len(mutating_nodes) == 1:
            writer_id = mutating_nodes[0].node_id
            if plan.single_writer_node_id not in {None, writer_id}:
                reason_codes.append("SINGLE_WRITER_NODE_MISMATCH")
        if reason_codes:
            return PolicyDecision(
                status=PolicyDecisionStatus.denied,
                allowed=False,
                reason_codes=list(dict.fromkeys(reason_codes)),
                safe_message="Plan side effects were denied by single-writer policy.",
            )
        return PolicyDecision(
            status=PolicyDecisionStatus.allowed,
            allowed=True,
            reason_codes=["PLAN_SIDE_EFFECTS_ALLOWED"],
            safe_message="Plan side effects satisfy read fan-out and single-writer policy.",
        )

    def _capability_denial_reasons(self, capability: CapabilityManifest, context: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        context_auth = set(context.get("auth_scopes", []))
        missing_auth = set(capability.auth_scopes) - context_auth
        if missing_auth:
            reasons.append("AUTH_SCOPE_MISSING")
        max_risk = CoordinationRiskLevel(context.get("max_risk_level", self.default_max_risk.value))
        if risk_rank(capability.risk_level) > risk_rank(max_risk):
            reasons.append("RISK_LEVEL_DENIED")
        if capability.quality.deprecated and self.deny_deprecated and capability.safety.deny_if_deprecated:
            reasons.append("DEPRECATED_CAPABILITY_DENIED")
        health_status = context.get("capability_health", {}).get(capability.id)
        if (
            health_status == CapabilityHealthStatus.unhealthy.value
            and self.deny_unhealthy
            and capability.safety.deny_if_unhealthy
        ):
            reasons.append("UNHEALTHY_CAPABILITY_DENIED")
        allowed_ids = set(context.get("allowed_capability_ids", []))
        denied_ids = set(context.get("denied_capability_ids", []))
        if allowed_ids and capability.id not in allowed_ids:
            reasons.append("CAPABILITY_NOT_IN_ALLOWLIST")
        if capability.id in denied_ids:
            reasons.append("CAPABILITY_DENYLISTED")
        return reasons
