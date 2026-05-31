from typing import List, Optional
from pydantic import BaseModel, Field

class AgentRuntimeAdapterManifest(BaseModel):
    adapter_id: str
    adapter_type: str  # openai_agents_sdk, claude_agent_sdk, gemini_cli, openhands, goose, aider, continue_dev_aid
    version: str
    description: Optional[str] = None
    exposed_capabilities: List[str] = Field(default_factory=list)

class SDKAdapterBoundaryPolicy(BaseModel):
    policy_id: str
    bypass_execution_contract_allowed: bool = False
    bypass_context_pack_allowed: bool = False
    bypass_consent_ledger_allowed: bool = False
    bypass_tool_broker_allowed: bool = False
    bypass_secret_broker_allowed: bool = False
    direct_tool_access_allowed: bool = False
    direct_memory_access_allowed: bool = False
    direct_secret_access_allowed: bool = False
