from typing import List, Optional
from pydantic import BaseModel, Field

class A2AAgentCardMinimal(BaseModel):
    """Inert metadata only model representing an external agent's capabilities.

    Real delegation remains blocked.
    """
    agent_id: str
    schema_version: str = "a2a_agent_card.v0"
    name: str
    owner: str
    declared_capabilities: List[str] = Field(default_factory=list)
    endpoint_url: Optional[str] = None
    version: str
