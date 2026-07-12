from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.storage import (
    EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF,
    EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE,
    FounderLoopEvidenceTimelineNarrativeReadModel,
    FounderLoopRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def _read_model(tmp_path: Path) -> dict[str, Any]:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    return repo.evidence_timeline()["narrative_read_model"]


def _clone(value: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(value)


@pytest.fixture(scope="module")
def narrative_read_model(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    return _read_model(tmp_path_factory.mktemp("evidence-timeline-narrative"))


def _assert_narrative_read_model(read_model: dict[str, Any]) -> None:
    parsed = FounderLoopEvidenceTimelineNarrativeReadModel(**read_model)
    assert parsed.schema_version == "product-loop-010-evidence-timeline-narrative.v1"
    assert parsed.contract_ref == EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF
    assert parsed.source == EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE
    assert parsed.backend_owned is True
    assert parsed.local_read_model_only is True
    assert parsed.safe_refs_only is True
    assert parsed.redacted_summaries_only is True
    assert parsed.narrative_from_existing_refs_only is True
    assert parsed.raw_content_included is False
    assert parsed.approval_ref_authority is False
    assert parsed.rollback_execution_enabled is False
    assert parsed.action_execution_enabled is False
    assert parsed.tool_execution_enabled is False
    assert parsed.workflow_execution_enabled is False
    assert parsed.connector_write_enabled is False
    assert parsed.connector_runtime_enabled is False
    assert parsed.provider_model_call_enabled is False
    assert parsed.runtime_model_calls_enabled is False
    assert parsed.provider_sdk_call_enabled is False
    assert parsed.live_web_enabled is False
    assert parsed.shell_subprocess_execution_enabled is False
    assert parsed.browser_execution_enabled is False
    assert parsed.public_beta_enabled is False
    assert parsed.distribution_enabled is False
    assert parsed.prompt_content_stored is False
    assert parsed.response_content_stored is False
    assert parsed.provider_exchange_content_stored is False
    assert parsed.memory_truth_authority is False
    assert parsed.context_injection_authorized is False
    assert parsed.production_authority_enabled is False
    assert parsed.entry_count == len(parsed.entries)
    assert parsed.narrative_refs == [entry.narrative_ref for entry in parsed.entries]
    assert parsed.entries


def test_evidence_timeline_narrative_surfaces_existing_safe_refs(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    payload = repo.evidence_timeline()
    read_model = payload["narrative_read_model"]

    assert payload["narrative_contract_ref"] == EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF
    _assert_narrative_read_model(read_model)
    first = read_model["entries"][0]
    assert first["what_happened"]
    assert first["why_recorded"]
    assert first["approval_posture"]
    assert first["change_summary"]
    assert first["remaining_blocked"]
    assert first["inspection_summary"]
    assert first["event_ref"] in read_model["event_refs"]
    assert first["timeline_item_ref"] in read_model["timeline_item_refs"]
    assert first["group_ref"] in read_model["group_refs"]
    assert set(first["evidence_refs"]) <= set(read_model["evidence_refs"])


@pytest.mark.parametrize(
    "field_name",
    [
        "raw_content_included",
        "approval_ref_authority",
        "rollback_execution_enabled",
        "action_execution_enabled",
        "tool_execution_enabled",
        "workflow_execution_enabled",
        "connector_write_enabled",
        "connector_runtime_enabled",
        "provider_model_call_enabled",
        "runtime_model_calls_enabled",
        "provider_sdk_call_enabled",
        "live_web_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "public_beta_enabled",
        "distribution_enabled",
        "prompt_content_stored",
        "response_content_stored",
        "provider_exchange_content_stored",
        "memory_truth_authority",
        "context_injection_authorized",
        "production_authority_enabled",
    ],
)
def test_evidence_timeline_narrative_rejects_authority_flags(
    narrative_read_model: dict[str, Any],
    field_name: str,
) -> None:
    payload = _clone(narrative_read_model)
    payload[field_name] = True

    with pytest.raises(ValidationError):
        FounderLoopEvidenceTimelineNarrativeReadModel(**payload)

    payload = _clone(narrative_read_model)
    payload["entries"][0][field_name] = True
    with pytest.raises(ValidationError):
        FounderLoopEvidenceTimelineNarrativeReadModel(**payload)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "This includes raw prompt material.",
        "This includes raw-prompt material.",
        "This includes raw response material.",
        "This includes raw-response material.",
        "provider_payload was visible.",
        "provider-exchange-content was visible.",
        "raw-provider was visible.",
        "raw-path was visible.",
        "raw-log was visible.",
        "raw_private_content was visible.",
        "/Users/alice/project was visible.",
        "username alice was present.",
        "username: alice was present.",
        "hostname workstation.local was present.",
        "hostname: workstation was present.",
        "serial C02ABC123 was present.",
        "serial: C02ABC123 was present.",
        "actor-ref:username was present.",
        "host-ref:hostname was present.",
        "device-ref:serial was present.",
        "Bearer token should fail.",
    ],
)
def test_evidence_timeline_narrative_rejects_raw_private_text(
    narrative_read_model: dict[str, Any],
    unsafe_text: str,
) -> None:
    payload = _clone(narrative_read_model)
    payload["entries"][0]["what_happened"] = unsafe_text

    with pytest.raises(ValidationError):
        FounderLoopEvidenceTimelineNarrativeReadModel(**payload)


@pytest.mark.parametrize(
    "unsafe_ref",
    [
        "evidence-ref:alice@example.com",
        "evidence-ref:workstation.local",
        "evidence-ref:relative/path/project",
        "evidence-ref:relative\\path\\project",
        "actor-ref:username",
        "host-ref:hostname",
        "device-ref:serial",
        "source-ref:private_key",
        "evidence-ref:raw-prompt",
        "evidence-ref:raw-response",
        "evidence-ref:raw-provider",
        "evidence-ref:raw-path",
        "evidence-ref:raw-log",
        "evidence-ref:provider-exchange-content",
    ],
)
def test_evidence_timeline_narrative_rejects_unsafe_refs(
    narrative_read_model: dict[str, Any],
    unsafe_ref: str,
) -> None:
    payload = _clone(narrative_read_model)
    entry_refs = list(payload["entries"][0]["evidence_refs"])
    entry_refs.append(unsafe_ref)
    payload["entries"][0]["evidence_refs"] = entry_refs
    payload["evidence_refs"] = sorted(set([*payload["evidence_refs"], unsafe_ref]))

    with pytest.raises(ValidationError, match="unsafe|safe ref"):
        FounderLoopEvidenceTimelineNarrativeReadModel(**payload)


def test_evidence_timeline_narrative_rejects_aggregate_ref_drift(
    narrative_read_model: dict[str, Any],
) -> None:
    payload = _clone(narrative_read_model)
    payload["receipt_refs"] = ["receipt-ref:drift"]

    with pytest.raises(ValidationError, match="receipt_refs"):
        FounderLoopEvidenceTimelineNarrativeReadModel(**payload)


def test_evidence_timeline_narrative_cli_is_read_only_and_redacted(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    repo.evidence_timeline()
    state_dir = tmp_path / "founder_loop"
    before_files = {
        path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in state_dir.rglob("*")
        if path.is_file()
    }

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_evidence_timeline_narrative.py"),
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
    assert payload["contract_ref"] == EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF
    assert (
        payload["command_ref"]
        == "repo-local-command:inspect-evidence-timeline-narrative"
    )
    assert payload["storage_state"] == "existing_state_read_only"
    assert payload["safe_refs_only"] is True
    assert payload["read_only"] is True
    assert payload["raw_content_omitted"] is True
    assert payload["approval_ref_authority"] is False
    assert payload["rollback_execution_enabled"] is False
    assert payload["action_execution_enabled"] is False
    assert payload["tool_execution_enabled"] is False
    assert payload["workflow_execution_enabled"] is False
    assert payload["connector_write_enabled"] is False
    assert payload["connector_runtime_enabled"] is False
    assert payload["provider_model_call_enabled"] is False
    assert payload["runtime_model_calls_enabled"] is False
    assert payload["provider_sdk_call_enabled"] is False
    assert payload["live_web_enabled"] is False
    assert payload["shell_subprocess_execution_enabled"] is False
    assert payload["browser_execution_enabled"] is False
    assert payload["public_beta_enabled"] is False
    assert payload["distribution_enabled"] is False
    assert payload["prompt_content_stored"] is False
    assert payload["response_content_stored"] is False
    assert payload["provider_exchange_content_stored"] is False
    assert payload["production_authority_enabled"] is False
    _assert_narrative_read_model(payload["narrative_read_model"])

    missing_state_dir = tmp_path / "missing_founder_loop"
    missing_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_evidence_timeline_narrative.py"),
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
    FounderLoopEvidenceTimelineNarrativeReadModel(
        **missing_payload["narrative_read_model"]
    )
