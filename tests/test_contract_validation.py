from ultimate_ai_agent.core.contracts import (
    ExecutionContract,
    ContextPack,
    validate_execution_contract,
    validate_context_pack,
    AgentMode,
    RiskLevel,
    GroundingMode,
    ContractStatus,
    ContextSource,
    AuthorityType,
)
from ultimate_ai_agent.core.hygiene.policies import DataClassification, ClassificationValue

def test_validation_low_risk_success():
    contract = ExecutionContract(
        contract_id="ec_test_001",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Valid minimal task",
        goal="Provide answer",
        deliverable="String output",
        mode=AgentMode.answer,
        risk_level=RiskLevel.low,
        acceptance_criteria=["Output must exist"],
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is True

def test_validation_high_risk_missing_approval_policy():
    contract = ExecutionContract(
        contract_id="ec_test_002",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="High risk action",
        goal="Publish code to production",
        deliverable="Production build",
        mode=AgentMode.execute,
        risk_level=RiskLevel.high,
        acceptance_criteria=["Done"],
        approval_policy={},  # Empty approval policy
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "MISSING_APPROVAL_POLICY"

def test_validation_high_risk_standing_approval_blocked():
    contract = ExecutionContract(
        contract_id="ec_test_003",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="High risk standing approval",
        goal="Delete records",
        deliverable="Success indicator",
        mode=AgentMode.execute,
        risk_level=RiskLevel.critical,
        acceptance_criteria=["Done"],
        approval_policy={"standing_approval": True},  # Standing approval enabled
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "STANDING_APPROVAL_NOT_ALLOWED"

def test_validation_grounding_required_for_research():
    contract = ExecutionContract(
        contract_id="ec_test_004",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Research task without grounding",
        goal="Research competitive tools",
        deliverable="Report",
        mode=AgentMode.research,
        risk_level=RiskLevel.high,
        grounding_mode=GroundingMode.none,  # Grounding none not allowed for high-risk research
        acceptance_criteria=["Done"],
        approval_policy={"require_human_signer": True},
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "GROUNDING_REQUIRED"

def test_validation_grounding_evidence_missing():
    contract = ExecutionContract(
        contract_id="ec_test_005",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Research task with empty evidence list",
        goal="Research competitors",
        deliverable="Report",
        mode=AgentMode.research,
        risk_level=RiskLevel.low,
        grounding_mode=GroundingMode.strict,
        required_evidence=[],  # Empty required evidence when grounding is requested
        acceptance_criteria=["Done"],
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "REQUIRED_EVIDENCE_EMPTY"

def test_validation_blocked_advanced_capability_tool():
    contract = ExecutionContract(
        contract_id="ec_test_006",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Try using reddit scanner",
        goal="Scan reddit",
        deliverable="Report",
        mode=AgentMode.research,
        allowed_tools=["reddit_scanner_fetch"],  # Blocked tool
        acceptance_criteria=["Done"],
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "BLOCKED_CAPABILITY"

def test_validation_blocked_advanced_capability_flag():
    contract = ExecutionContract(
        contract_id="ec_test_007",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Try enabling skill factory",
        goal="Build skill",
        deliverable="Skill package",
        mode=AgentMode.create,
        capability_flags_required=["skill_factory"],  # Blocked flag
        acceptance_criteria=["Done"],
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "BLOCKED_CAPABILITY"

def test_validation_redaction_policy_required_for_sensitive():
    classification = DataClassification(
        classification=ClassificationValue.sensitive_personal,
        source="profile"
    )
    contract = ExecutionContract(
        contract_id="ec_test_008",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Processing sensitive data",
        goal="Format profile",
        deliverable="Formatted report",
        mode=AgentMode.answer,
        data_classification=classification,
        redaction_policy=None,  # Missing redaction policy for sensitive data classification
        acceptance_criteria=["Done"],
        status=ContractStatus.draft
    )
    result = validate_execution_contract(contract)
    assert result.success is False
    assert result.error.code == "REDACTION_POLICY_REQUIRED"

def test_context_pack_secret_scan():
    src = ContextSource(
        source_id="src_1",
        source_type="memory",
        authority=AuthorityType.memory,
        summary="User preferences containing secret: api_key = \"abcd1234efgh5678ijkl9012\""  # Raw secret pattern
    )
    pack = ContextPack(
        context_pack_id="cp_test_001",
        contract_id="ec_test_001",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        active_goal="Goal",
        canonical_sources=[src],
        token_budget=1000
    )
    result = validate_context_pack(pack)
    assert result.success is False
    assert result.error.code == "SECRET_EXPOSURE_BLOCKED"
