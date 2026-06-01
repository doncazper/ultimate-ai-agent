from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.consent.decisions import ConsentDecision
from ultimate_ai_agent.core.files.operations import FileChange, FileWriteDecision
from ultimate_ai_agent.core.kernel.enums import KernelTaskStatus
from ultimate_ai_agent.core.ledger.receipts import RunReceipt
from ultimate_ai_agent.core.memory.decisions import MemoryWriteDecision
from ultimate_ai_agent.core.tools.decisions import ToolDecision
from ultimate_ai_agent.core.world_state.models import StructuredWorldState


class KernelTaskResult(BaseModel):
    result_id: str
    run_id: str
    success: bool
    status: KernelTaskStatus
    safe_message: str
    file_change: Optional[FileChange] = None
    write_decision: Optional[FileWriteDecision] = None
    tool_decision: Optional[ToolDecision] = None
    consent_decision: Optional[ConsentDecision] = None
    memory_decision: Optional[MemoryWriteDecision] = None
    world_state: Optional[StructuredWorldState] = None
    receipt: Optional[RunReceipt] = None
    rollback_ref: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
