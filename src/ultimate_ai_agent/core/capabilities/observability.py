from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from ultimate_ai_agent.core.time import utc_now


@dataclass(frozen=True)
class CapabilityEvent:
    event_type: str
    capability_name: str | None = None
    agent_name: str | None = None
    status: str | None = None
    duration_ms: float | None = None
    error_class: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: object = field(default_factory=utc_now)

    def as_safe_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "capability_name": self.capability_name,
            "agent_name": self.agent_name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_class": self.error_class,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, "isoformat") else str(self.created_at),
        }


class CapabilityEventSink(Protocol):
    def emit(self, event: CapabilityEvent) -> None:
        ...


class NoopCapabilityEventSink:
    def emit(self, event: CapabilityEvent) -> None:
        return None


class LoggerCapabilityEventSink:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("ultimate_ai_agent.capabilities")

    def emit(self, event: CapabilityEvent) -> None:
        self.logger.info("capability event", extra={"capability_event": event.as_safe_dict()})
