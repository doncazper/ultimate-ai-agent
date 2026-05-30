from pydantic import ValidationError
import pytest

from ultimate_ai_agent.core.contracts import ExecutionContract, AgentMode, ContractStatus

def test_minimal_valid_contract():
    contract = ExecutionContract(
        contract_id="ec_test_123",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Testing minimal contract",
        goal="Test contract creation",
        deliverable="Passing unit test",
        mode=AgentMode.answer,
        acceptance_criteria=["Tests must compile and run successfully"],
        status=ContractStatus.draft
    )
    assert contract.contract_id == "ec_test_123"
    assert contract.mode == "answer"
    assert contract.autonomy_level == 0
    assert contract.risk_level == "low"

def test_contract_invalid_id():
    with pytest.raises(ValidationError):
        # ID does not match ec_ pattern
        ExecutionContract(
            contract_id="invalid_id",
            run_id="run_123",
            workspace_id="ws_1",
            user_id="usr_alice",
            request_summary="Testing invalid ID",
            goal="Fail validation",
            deliverable="N/A",
            mode=AgentMode.answer,
            acceptance_criteria=["Fail"]
        )

def test_contract_missing_acceptance_criteria():
    with pytest.raises(ValidationError):
        ExecutionContract(
            contract_id="ec_test_123",
            run_id="run_123",
            workspace_id="ws_1",
            user_id="usr_alice",
            request_summary="Testing empty criteria",
            goal="Fail validation",
            deliverable="N/A",
            mode=AgentMode.answer,
            acceptance_criteria=[]
        )
