from __future__ import annotations

from typing import Protocol

from ultimate_ai_agent.core.capabilities.models import TelemetryEvent


class TelemetrySink(Protocol):
    def record(self, event: TelemetryEvent) -> None:
        ...


class NoOpTelemetrySink:
    def record(self, event: TelemetryEvent) -> None:
        return None


class InMemoryTelemetrySink:
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []

    def record(self, event: TelemetryEvent) -> None:
        self.events.append(event)
