from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Ultimate AI Agent API Boundary",
    version="0.5.8",
    description="The secure control boundary for the Ultimate AI Agent"
)

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "healthy", "version": "0.5.8"}

@app.get("/version")
def get_version():
    return {"version": "0.5.8"}
