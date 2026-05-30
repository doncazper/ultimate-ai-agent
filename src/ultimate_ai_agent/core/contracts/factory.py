from typing import List, Optional
from ultimate_ai_agent.core.contracts.enums import AgentMode, RiskLevel, AutonomyLevel, GroundingMode, ContractStatus
from ultimate_ai_agent.core.contracts.execution_contract import ExecutionContract

def create_answer_only_contract(
    contract_id: str,
    run_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    deliverable: str,
    project_id: Optional[str] = None
) -> ExecutionContract:
    return ExecutionContract(
        contract_id=contract_id,
        run_id=run_id,
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        goal=goal,
        deliverable=deliverable,
        mode=AgentMode.answer,
        risk_level=RiskLevel.low,
        autonomy_level=AutonomyLevel.L0_answer_only,
        grounding_mode=GroundingMode.none,
        acceptance_criteria=["Direct answer is provided to the user"],
        status=ContractStatus.draft
    )

def create_research_contract(
    contract_id: str,
    run_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    deliverable: str,
    required_evidence: List[str],
    project_id: Optional[str] = None
) -> ExecutionContract:
    return ExecutionContract(
        contract_id=contract_id,
        run_id=run_id,
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        goal=goal,
        deliverable=deliverable,
        mode=AgentMode.research,
        risk_level=RiskLevel.medium,
        autonomy_level=AutonomyLevel.L2_recommend,
        grounding_mode=GroundingMode.hybrid,
        required_evidence=required_evidence,
        acceptance_criteria=[
            "Evidence is gathered and cited",
            "Research deliverable is produced"
        ],
        status=ContractStatus.draft
    )

def create_artifact_contract(
    contract_id: str,
    run_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    deliverable: str,
    project_id: Optional[str] = None
) -> ExecutionContract:
    return ExecutionContract(
        contract_id=contract_id,
        run_id=run_id,
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        goal=goal,
        deliverable=deliverable,
        mode=AgentMode.create,
        risk_level=RiskLevel.medium,
        autonomy_level=AutonomyLevel.L1_draft_only,
        acceptance_criteria=["Artifact is created"],
        status=ContractStatus.draft
    )

def create_file_mutation_prep_contract(
    contract_id: str,
    run_id: str,
    workspace_id: str,
    user_id: str,
    goal: str,
    deliverable: str,
    project_id: Optional[str] = None
) -> ExecutionContract:
    # Remains non-executing in M1 (no mutating actions permitted)
    return ExecutionContract(
        contract_id=contract_id,
        run_id=run_id,
        workspace_id=workspace_id,
        user_id=user_id,
        project_id=project_id,
        goal=goal,
        deliverable=deliverable,
        mode=AgentMode.code,
        risk_level=RiskLevel.medium,
        autonomy_level=AutonomyLevel.L3_prepare_and_request_approval,
        acceptance_criteria=["File changes are prepared for review"],
        status=ContractStatus.draft
    )
