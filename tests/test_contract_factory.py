from ultimate_ai_agent.core.contracts.factory import (
    create_answer_only_contract,
    create_artifact_contract,
    create_file_mutation_prep_contract,
    create_research_contract,
)


def test_factory_helpers_populate_request_summary():
    contract = create_answer_only_contract(
        contract_id="ec_factory_answer",
        run_id="run_factory",
        workspace_id="ws",
        user_id="user",
        goal="Explain the current state",
        deliverable="Short answer",
    )

    assert contract.request_summary == "Explain the current state"


def test_factory_helpers_redact_secret_like_request_summary():
    contract = create_artifact_contract(
        contract_id="ec_factory_artifact",
        run_id="run_factory",
        workspace_id="ws",
        user_id="user",
        goal="Use api_key = \"abcdefghijklmnop\" to build a draft",
        deliverable="Draft artifact",
    )

    assert "abcdefghijklmnop" not in contract.request_summary
    assert "[REDACTED_SECRET]" in contract.request_summary


def test_all_factory_helpers_create_valid_contracts():
    contracts = [
        create_answer_only_contract(
            contract_id="ec_factory_answer_all",
            run_id="run_factory",
            workspace_id="ws",
            user_id="user",
            goal="Answer",
            deliverable="Answer",
        ),
        create_research_contract(
            contract_id="ec_factory_research_all",
            run_id="run_factory",
            workspace_id="ws",
            user_id="user",
            goal="Research",
            deliverable="Report",
            required_evidence=["source_refs"],
        ),
        create_artifact_contract(
            contract_id="ec_factory_artifact_all",
            run_id="run_factory",
            workspace_id="ws",
            user_id="user",
            goal="Create",
            deliverable="Artifact",
        ),
        create_file_mutation_prep_contract(
            contract_id="ec_factory_file_all",
            run_id="run_factory",
            workspace_id="ws",
            user_id="user",
            goal="Prepare patch",
            deliverable="Patch preview",
        ),
    ]

    assert all(contract.request_summary for contract in contracts)
