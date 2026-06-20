from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent import __version__


RUNTIME_HEALTH_STATUS_HEALTHY = "healthy"


class RuntimeHealthStatus(BaseModel):
    status: str
    version: str

    model_config = ConfigDict(extra="forbid")


def build_runtime_health_status(version: str | None = None) -> RuntimeHealthStatus:
    return RuntimeHealthStatus(
        status=RUNTIME_HEALTH_STATUS_HEALTHY,
        version=version or __version__,
    )
