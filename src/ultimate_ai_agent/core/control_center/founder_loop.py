from __future__ import annotations

from ultimate_ai_agent.core.storage import FounderLoopRepository


class FounderLoopControlCenterService:
    """API-facing summary service for storage-backed Founder Loop surfaces."""

    def __init__(self, repository: FounderLoopRepository) -> None:
        self.repository = repository

    @classmethod
    def from_env(cls) -> "FounderLoopControlCenterService":
        return cls(FounderLoopRepository.from_env())

    def today_summary(self) -> dict:
        return self.repository.today_summary()

    def actions_inbox(self) -> dict:
        return self.repository.actions_inbox()

    def morning_briefing_summary(self) -> dict:
        return self.repository.morning_briefing()

    def storage_status(self) -> dict:
        status = self.repository.storage_status()
        status["backup_manifest"] = self.repository.backup_manifest()
        return status
