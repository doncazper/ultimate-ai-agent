from typing import List

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.gate.enums import FoundationGateCategory


class FoundationGateCriterion(BaseModel):
    criterion_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    required: bool = True
    category: FoundationGateCategory
    evaluator_ref: str = Field(..., min_length=1)
    pass_condition: str = Field(..., min_length=1)
    failure_message: str = Field(..., min_length=1)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def _criterion(
    criterion_id: str,
    name: str,
    category: FoundationGateCategory,
    evaluator_ref: str,
    pass_condition: str,
    failure_message: str,
    severity: str = "high",
) -> FoundationGateCriterion:
    return FoundationGateCriterion(
        criterion_id=criterion_id,
        name=name,
        description=pass_condition,
        severity=severity,
        required=True,
        category=category,
        evaluator_ref=evaluator_ref,
        pass_condition=pass_condition,
        failure_message=failure_message,
    )


def default_foundation_gate_criteria() -> List[FoundationGateCriterion]:
    return [
        _criterion(
            "versioning_consistent",
            "Versioning Consistency",
            FoundationGateCategory.versioning,
            "FoundationGateEvaluator.check_versioning_consistent",
            "VERSION.md, pyproject.toml, package __version__, README start refs, and release docs agree.",
            "Versioned baseline files are inconsistent.",
        ),
        _criterion(
            "release_docs_present",
            "Release Documentation Present",
            FoundationGateCategory.documentation,
            "FoundationGateEvaluator.check_release_docs_present",
            "M6 import README, master plan, release notes, and implementation plan are present.",
            "M6 release documentation is missing.",
        ),
        _criterion(
            "foundation_modules_present",
            "Foundation Modules Present",
            FoundationGateCategory.contracts,
            "FoundationGateEvaluator.check_foundation_modules_present",
            "M1 through M6 foundation packages and scripts exist.",
            "Required foundation module files are missing.",
        ),
        _criterion(
            "blocked_modules_absent",
            "Blocked Modules Absent",
            FoundationGateCategory.blocked_modules,
            "FoundationGateEvaluator.check_blocked_modules_absent",
            "Scanners, companion proactivity, Skill Factory, self-improvement, autopilot, SDK/A2A delegation, and browser automation runtimes are absent.",
            "A module blocked for M6 exists in runtime source.",
            "critical",
        ),
        _criterion(
            "forbidden_runtime_integrations_absent",
            "Forbidden Runtime Integrations Absent",
            FoundationGateCategory.security,
            "FoundationGateEvaluator.check_forbidden_runtime_integrations_absent",
            "Runtime source has no real provider, model, web, vector DB, pgvector, embedding, or production truth imports.",
            "Forbidden runtime integration import or call was detected.",
            "critical",
        ),
        _criterion(
            "shell_execution_absent",
            "Runtime Shell Execution Absent",
            FoundationGateCategory.security,
            "FoundationGateEvaluator.check_shell_execution_absent",
            "Runtime source does not load process-spawning modules or execute shell commands.",
            "Runtime source contains shell execution capability.",
            "critical",
        ),
        _criterion(
            "broad_filesystem_scanning_absent",
            "Broad Filesystem Scanning Absent",
            FoundationGateCategory.security,
            "FoundationGateEvaluator.check_broad_filesystem_scanning_absent",
            "Runtime source does not use broad filesystem walks or home-directory traversal.",
            "Runtime source contains broad filesystem scanning.",
            "critical",
        ),
        _criterion(
            "secret_hygiene_clean",
            "Secret Hygiene Clean",
            FoundationGateCategory.security,
            "FoundationGateEvaluator.check_secret_hygiene_clean",
            "Gate outputs and runtime source contain no raw secrets, private keys, or secret assignment payloads.",
            "Secret-like content was detected.",
            "critical",
        ),
        _criterion(
            "tool_broker_blocks_advanced_adapters",
            "Tool Broker Blocks Advanced Adapters",
            FoundationGateCategory.tool_broker,
            "FoundationGateEvaluator.check_tool_broker_blocks_advanced_adapters",
            "MCP, A2A, SDK adapter, and Skill tool categories remain blocked by the Tool Broker.",
            "An advanced adapter category was not blocked.",
            "critical",
        ),
        _criterion(
            "truth_evidence_contracts_valid",
            "Truth Evidence Contracts Valid",
            FoundationGateCategory.truth,
            "FoundationGateEvaluator.check_truth_evidence_contracts_valid",
            "Truth source and evidence governance contracts require references for supported claims.",
            "Truth/evidence contract validation failed.",
        ),
        _criterion(
            "memory_file_contracts_valid",
            "Memory and File Contracts Valid",
            FoundationGateCategory.memory,
            "FoundationGateEvaluator.check_memory_file_contracts_valid",
            "Memory remains recall-only and file references reject unsafe paths and secrets.",
            "Memory/file contract validation failed.",
        ),
        _criterion(
            "m5_shadow_replay_passes",
            "M5 Shadow Replay Passes",
            FoundationGateCategory.rollback,
            "FoundationGateEvaluator.check_m5_shadow_replay_passes",
            "The M5 local/dev kernel trace replays with ordered events, receipt, rollback, memory refs, and no secret leakage.",
            "M5 shadow replay failed.",
            "critical",
        ),
        _criterion(
            "m7_modules_present",
            "M7 Modules Present",
            FoundationGateCategory.contracts,
            "FoundationGateEvaluator.check_m7_modules_present",
            "M7 model router and cost/resource governor policy modules exist.",
            "Required M7 module files are missing.",
        ),
        _criterion(
            "model_router_decision_only",
            "Model Router Decision Only",
            FoundationGateCategory.model_router,
            "FoundationGateEvaluator.check_model_router_decision_only",
            "Model Router produces deterministic metadata-only route decisions without model/provider execution.",
            "Model Router decision-only contract failed.",
            "critical",
        ),
        _criterion(
            "cost_governor_blocks_over_budget",
            "Cost Governor Blocks Over Budget",
            FoundationGateCategory.cost_governor,
            "FoundationGateEvaluator.check_cost_governor_blocks_over_budget",
            "Cost Governor denies over-budget routes deterministically.",
            "Cost Governor over-budget denial failed.",
            "critical",
        ),
        _criterion(
            "m7_arbitrary_approval_ref_rejected",
            "M7 Arbitrary Approval Ref Rejected",
            FoundationGateCategory.model_router,
            "FoundationGateEvaluator.check_m7_arbitrary_approval_ref_rejected",
            "Arbitrary approval_ref values do not authorize sensitive cloud model routes.",
            "Arbitrary approval_ref authorized a sensitive cloud route.",
            "critical",
        ),
        _criterion(
            "m7_context_budget_exhaustion_blocks_route",
            "M7 Context Budget Exhaustion Blocks Route",
            FoundationGateCategory.model_router,
            "FoundationGateEvaluator.check_m7_context_budget_exhaustion_blocks_route",
            "Exhausted available history budget prevents model route selection.",
            "Exhausted context budget allowed a model route.",
            "critical",
        ),
        _criterion(
            "m7_soft_budget_warning_allows_route",
            "M7 Soft Budget Warning Allows Route",
            FoundationGateCategory.cost_governor,
            "FoundationGateEvaluator.check_m7_soft_budget_warning_allows_route",
            "Soft budget overages remain allowed with warning.",
            "Soft budget overage did not allow with warning.",
            "critical",
        ),
        _criterion(
            "m7_hard_budget_denies_route",
            "M7 Hard Budget Denies Route",
            FoundationGateCategory.cost_governor,
            "FoundationGateEvaluator.check_m7_hard_budget_denies_route",
            "Hard budget overages deny routes.",
            "Hard budget overage did not deny the route.",
            "critical",
        ),
        _criterion(
            "m7_cost_warnings_visible_in_route_decision",
            "M7 Cost Warnings Visible In Route Decision",
            FoundationGateCategory.model_router,
            "FoundationGateEvaluator.check_m7_cost_warnings_visible_in_route_decision",
            "Route decisions preserve soft-budget warning reason codes.",
            "Route decision did not preserve cost warning reason codes.",
            "critical",
        ),
    ]
