from __future__ import annotations

from ultimate_ai_agent.core.control_center.founder_loop import FounderLoopControlCenterService
from ultimate_ai_agent.core.storage import FounderLoopRepository


def get_founder_loop_repository() -> FounderLoopRepository:
    return FounderLoopRepository.from_env()


def get_founder_loop_service() -> FounderLoopControlCenterService:
    return FounderLoopControlCenterService(get_founder_loop_repository())
