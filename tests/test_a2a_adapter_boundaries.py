import pytest
from ultimate_ai_agent.core.adapters import (
    A2AAgentCardMinimal,
    A2AAgentCardV1,
    UAAA2AAgentCardMetadataImport,
    validate_a2a_delegation_block,
)

def test_a2a_card_validation() -> None:
    card = UAAA2AAgentCardMetadataImport(
        agent_id="agent_assistant",
        name="Research Assistant",
        owner="user_123",
        declared_capabilities=["web_search", "summarize"],
        version="0.1.0"
    )
    assert card.agent_id == "agent_assistant"
    assert card.name == "Research Assistant"

def test_a2a_delegation_is_blocked() -> None:
    card = UAAA2AAgentCardMetadataImport(
        agent_id="agent_assistant",
        name="Research Assistant",
        owner="user_123",
        version="0.1.0"
    )
    with pytest.raises(ValueError, match="Real A2A delegation to agent.*is blocked"):
        validate_a2a_delegation_block(card)


def test_legacy_a2a_agent_card_name_is_metadata_import_alias() -> None:
    assert A2AAgentCardMinimal is UAAA2AAgentCardMetadataImport


def test_a2a_v1_agent_card_shape_parses_without_runtime_authority() -> None:
    card = A2AAgentCardV1.model_validate(
        {
            "name": "Research Agent",
            "description": "Research metadata fixture.",
            "supportedInterfaces": [
                {
                    "url": "https://research-agent.example.invalid/a2a/v1",
                    "protocolBinding": "HTTP+JSON",
                    "protocolVersion": "1.0",
                }
            ],
            "version": "1.0.0",
            "capabilities": {"streaming": False, "pushNotifications": False},
            "skills": [
                {
                    "id": "summarize",
                    "name": "Summarize",
                    "description": "Summarize reviewed refs.",
                }
            ],
        }
    )

    assert card.supported_interfaces[0].protocol_version == "1.0"
    assert card.skills[0].id == "summarize"
