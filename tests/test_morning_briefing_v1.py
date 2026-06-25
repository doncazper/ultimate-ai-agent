from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.morning_briefing import (
    MORNING_BRIEFING_V1_CONTRACT_REF,
    MORNING_BRIEFING_V1_READ_MODEL_SOURCE,
    MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS,
    MorningBriefingV1ReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_morning_briefing_v1(read_model: dict[str, Any]) -> None:
    assert read_model["contract_ref"] == MORNING_BRIEFING_V1_CONTRACT_REF
    assert read_model["source"] == MORNING_BRIEFING_V1_READ_MODEL_SOURCE
    assert read_model["backend_owned"] is True
    assert read_model["local_read_model_only"] is True
    assert read_model["safe_refs_only"] is True
    assert read_model["raw_content_included"] is False
    assert read_model["bounded_preview_only"] is True
    assert read_model["source_readiness_required"] is True
    assert read_model["missing_sources_visible"] is True
    assert read_model["repo_status_refs"]
    assert read_model["workbench_status_refs"]
    assert read_model["source_readiness_refs"]
    assert read_model["missing_source_refs"]
    assert read_model["open_action_refs"]
    assert read_model["memory_review_refs"]
    assert read_model["evidence_timeline_refs"]
    assert read_model["evidence_refs"]
    assert set(MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS) <= set(
        read_model["blocked_state_refs"]
    )
    for flag in [
        "connector_read_enabled",
        "connector_runtime_enabled",
        "connector_write_enabled",
        "email_calendar_fetch_enabled",
        "account_auth_enabled",
        "live_web_enabled",
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "automatic_recommendations_enabled",
        "hidden_memory_write_authorized",
        "memory_write_authorized",
        "context_injection_authorized",
        "action_execution_enabled",
        "repo_write_enabled",
        "workbench_apply_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "notification_delivery_enabled",
        "source_refresh_enabled",
        "production_authority_enabled",
    ]:
        assert read_model[flag] is False


def test_morning_briefing_v1_surfaces_from_storage(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    briefing = repo.morning_briefing()

    assert briefing["morning_briefing_v1_contract_ref"] == (
        MORNING_BRIEFING_V1_CONTRACT_REF
    )
    _assert_morning_briefing_v1(briefing["morning_briefing_v1_read_model"])
    assert briefing["morning_briefing_v1_read_model"]["item_count"] == len(
        briefing["items"]
    )
    assert briefing["morning_briefing_v1_read_model"]["section_count"] == len(
        briefing["daily_loop_sections"]
    )
    missing_refs = set(briefing["morning_briefing_v1_read_model"]["missing_source_refs"])
    assert "source-ref:founder-loop:plans-actions" not in missing_refs
    assert "status-ref:control-center-route-manifest" not in missing_refs


def test_morning_briefing_v1_rejects_authority_and_raw_content(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    read_model = repo.morning_briefing()["morning_briefing_v1_read_model"]

    payload = dict(read_model)
    payload["connector_runtime_enabled"] = True
    with pytest.raises(ValidationError, match="connector_runtime_enabled"):
        MorningBriefingV1ReadModel(**payload)

    payload = dict(read_model)
    payload["safe_summary"] = "Contains raw prompt material."
    with pytest.raises(ValidationError, match="unsafe/private content"):
        MorningBriefingV1ReadModel(**payload)

    payload = dict(read_model)
    payload["contract_ref"] = "contract-ref:product-loop-007-other:v1"
    with pytest.raises(ValidationError, match="contract ref"):
        MorningBriefingV1ReadModel(**payload)

    payload = dict(read_model)
    payload["schema_version"] = "product-loop-007-other.v1"
    with pytest.raises(ValidationError, match="schema version"):
        MorningBriefingV1ReadModel(**payload)


def test_morning_briefing_v1_cli_is_read_only_and_redacted(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.morning_briefing()
    state_dir = tmp_path / "founder_loop"
    recall_db = state_dir / "memory_review_recall.sqlite3"
    if recall_db.exists():
        recall_db.unlink()
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_morning_briefing_v1.py"),
            "--state-dir",
            str(state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    after_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }
    payload = json.loads(result.stdout)

    assert after_files == before_files
    assert not recall_db.exists()
    assert payload["contract_ref"] == MORNING_BRIEFING_V1_CONTRACT_REF
    assert payload["command_ref"] == "repo-local-command:inspect-morning-briefing-v1"
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["raw_paths_omitted"] is True
    assert payload["connector_runtime_enabled"] is False
    assert payload["email_calendar_fetch_enabled"] is False
    assert payload["live_web_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["runtime_model_call_enabled"] is False
    assert payload["automatic_recommendations_enabled"] is False
    assert payload["hidden_memory_write_authorized"] is False
    assert payload["memory_write_authorized"] is False
    assert payload["repo_write_enabled"] is False
    assert payload["workbench_apply_enabled"] is False
    assert payload["shell_subprocess_execution_enabled"] is False
    assert payload["browser_execution_enabled"] is False
    assert payload["notification_delivery_enabled"] is False
    assert payload["source_refresh_enabled"] is False
    _assert_morning_briefing_v1(payload["morning_briefing_v1_read_model"])

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_morning_briefing_v1.py"),
            "--state-dir",
            str(missing_state_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    missing_payload = json.loads(missing_result.stdout)
    assert missing_payload["storage_state"] == "state_not_found_no_write"
    assert not missing_state_dir.exists()
