from typing import Optional
from pydantic import BaseModel

class ModelRuntimeHealth(BaseModel):
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[float] = None
    error_count: int = 0
    uptime_seconds: float = 0.0
    last_checked_at: str
