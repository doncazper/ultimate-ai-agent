from fastapi import FastAPI
from pydantic import BaseModel

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.contracts import (
    ExecutionContract,
    ContextPack,
    validate_execution_contract,
    validate_context_pack,
)
from ultimate_ai_agent.core.hygiene.envelopes import ResultEnvelope

app = FastAPI(
    title="Ultimate AI Agent API Boundary",
    version=__version__,
    description="The secure control boundary for the Ultimate AI Agent"
)

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "healthy", "version": __version__}

@app.get("/version")
def get_version():
    return {"version": __version__}

@app.post("/contracts/validate", response_model=ResultEnvelope)
def post_validate_contract(contract: ExecutionContract):
    return validate_execution_contract(contract)

@app.post("/context-packs/validate", response_model=ResultEnvelope)
def post_validate_context_pack(pack: ContextPack):
    return validate_context_pack(pack)
