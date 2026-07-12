from copy import deepcopy
from pathlib import Path

import pytest

from tests.test_runtime_agent_loop_spine import _repo
from ultimate_ai_agent.core.control_center.agent_loop import (
    build_agent_loop_thread_read_model,
)


def test_agent_loop_thread_plan_snapshot_identity_changes_with_plan_content(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    today = repo.today_summary(limit=12)
    common = {
        "actions_inbox": repo.actions_inbox(limit=50),
        "evidence_timeline": repo.evidence_timeline(limit=50),
        "memory_review": repo.memory_review(limit=20),
        "proof_index": {"items": []},
        "trust_authority_matrix": {"lanes": []},
    }
    original = build_agent_loop_thread_read_model(
        today_summary=today,
        **common,
    )
    unchanged = build_agent_loop_thread_read_model(
        today_summary=deepcopy(today),
        **common,
    )
    assert original["plan_revision"] == unchanged["plan_revision"]

    changed_definition = deepcopy(today)
    changed_definition["plans"][0]["task_decomposition_steps"][0][
        "safe_summary"
    ] = "Review a changed safe plan-step definition."
    definition_thread = build_agent_loop_thread_read_model(
        today_summary=changed_definition,
        **common,
    )

    changed_dependency = deepcopy(today)
    changed_dependency["plans"][0]["task_decomposition_steps"][1][
        "depends_on"
    ] = []
    dependency_thread = build_agent_loop_thread_read_model(
        today_summary=changed_dependency,
        **common,
    )

    original_revision = original["plan_revision"]
    for changed in (definition_thread, dependency_thread):
        changed_revision = changed["plan_revision"]
        assert changed_revision["revision_ref"] != original_revision["revision_ref"]
        assert changed_revision["revision_fingerprint_ref"] != (
            original_revision["revision_fingerprint_ref"]
        )
        assert changed_revision["decomposition"]["decomposition_ref"] != (
            original_revision["decomposition"]["decomposition_ref"]
        )
