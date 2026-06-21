import pytest
from ultimate_ai_agent.core.adapters import (
    A2AAgentCardMinimal,
    validate_a2a_delegation_block,
)

def test_a2a_card_validation() -> None:
    card = A2AAgentCardMinimal(
        agent_id="agent_assistant",
        name="Research Assistant",
        owner="user_123",
        declared_capabilities=["web_search", "summarize"],
        version="0.1.0"
    )
    assert card.agent_id == "agent_assistant"
    assert card.name == "Research Assistant"

def test_a2a_delegation_is_blocked() -> None:
    card = A2AAgentCardMinimal(
        agent_id="agent_assistant",
        name="Research Assistant",
        owner="user_123",
        version="0.1.0"
    )
    with pytest.raises(ValueError, match="Real A2A delegation to agent.*is blocked"):
        validate_a2a_delegation_block(card)
