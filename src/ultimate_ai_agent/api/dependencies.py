from __future__ import annotations

import os
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore, authority_state_dir
from ultimate_ai_agent.core.control_center.founder_loop_attention_workflow import (
    FounderLoopAttentionWorkflow,
)
from ultimate_ai_agent.core.control_center.founder_loop import FounderLoopControlCenterService
from ultimate_ai_agent.core.control_center.founder_loop_mission import (
    FounderLoopFilesystemMissionService,
    FounderLoopFilesystemTarget,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.news_signals import NewsSignalsRepository
from ultimate_ai_agent.core.tools.runtime import (
    FilesystemSafeRoot,
    filesystem_opaque_path_ref,
)


_ROOT = Path(__file__).resolve().parents[3]
_ATTENTION_ROOT_REF = "safe-root:uaa-repository"
_ATTENTION_TARGET_REF = "target-ref:founder-loop:canonical-readme-metadata"
_ATTENTION_RELATIVE_PATH = "README.md"
_attention_workflows: dict[str, FounderLoopAttentionWorkflow] = {}


def get_founder_loop_repository() -> FounderLoopRepository:
    return FounderLoopRepository.from_env()


def get_founder_loop_service() -> FounderLoopControlCenterService:
    return FounderLoopControlCenterService(get_founder_loop_repository())


def get_news_signals_repository() -> NewsSignalsRepository:
    """Return the local safe-ref News and Signals repository.

    The repository contains only normalized artifacts supplied by separately
    admitted source lanes. Creating it performs no external read or account
    connection.
    """

    return NewsSignalsRepository.from_env()


def get_founder_attention_workflow() -> FounderLoopAttentionWorkflow:
    repository = get_founder_loop_repository()
    mission_state_dir = authority_state_dir()
    cache_key = "|".join(
        (str(repository.state_dir.resolve()), str(mission_state_dir.resolve()))
    )
    existing = _attention_workflows.get(cache_key)
    if existing is not None:
        return existing
    path_ref = filesystem_opaque_path_ref(
        _ATTENTION_ROOT_REF,
        _ATTENTION_RELATIVE_PATH,
    )
    target = FounderLoopFilesystemTarget(
        target_ref=_ATTENTION_TARGET_REF,
        root_ref=_ATTENTION_ROOT_REF,
        relative_path=_ATTENTION_RELATIVE_PATH,
        path_ref=path_ref,
        safe_label="Canonical repository overview metadata",
    )
    mission_service = FounderLoopFilesystemMissionService(
        state_dir=mission_state_dir,
        root=FilesystemSafeRoot(
            root_ref=_ATTENTION_ROOT_REF,
            root_path=_ROOT,
            safe_label="UAA repository root",
        ),
        targets=(target,),
        lease_store=AuthorityLeaseStore(mission_state_dir),
        approval_authority=LocalApprovalAuthority(),
        readiness=lambda: (
            "safe_disabled"
            if os.getenv("UAA_FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLED") == "1"
            else "ready"
        ),
    )
    workflow = FounderLoopAttentionWorkflow(
        repository=repository,
        mission_service=mission_service,
    )
    _attention_workflows[cache_key] = workflow
    return workflow


def clear_founder_attention_workflow_cache() -> None:
    _attention_workflows.clear()
