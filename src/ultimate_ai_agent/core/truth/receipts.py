from typing import List

from pydantic import BaseModel, ConfigDict, Field


class TruthVerificationReceiptRef(BaseModel):
    receipt_ref: str = Field(..., min_length=1)
    claim_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")
