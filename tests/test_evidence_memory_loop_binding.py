from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.evidence_memory_loop_binding import (
    EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS,
    EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF,
    EVIDENCE_MEMORY_LOOP_BINDING_PROMOTION_PATH_REFS,
    EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF,
    EvidenceMemoryLoopBindingReadModel,
)
from ultimate_ai_agent.core.control_center.founder_loop import (
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ROOT = Path(__file__).resolve().parents[1]


def _assert_no_runtime_authority(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    forbidden = [
        'memory_truth_authority": true',
        'context_injection_authorized": true',
        'automatic_memory_write_authorized": true',
        'memory_delete_enabled": true',
        'memory_export_enabled": true',
        'action_execution_enabled": true',
        'connector_write_enabled": true',
        'connector_send_enabled": true',
        'provider_model_call_enabled": true',
        'shell_subprocess_execution_enabled": true',
        'browser_execution_enabled": true',
        'background_autonomy_enabled": true',
        'production_authority_enabled": true',
        'raw_content_included": true',
        "/users/",
        "raw prompt",
        "raw response",
        "provider payload",
        "credential",
        "secret",
    ]
    for fragment in forbidden:
        assert fragment not in text


def test_today_exposes_backend_owned_evidence_memory_loop_binding(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today = repo.today_summary()
    read_model = today["evidence_memory_loop_binding_read_model"]
    parsed = EvidenceMemoryLoopBindingReadModel(**read_model)

    assert today["evidence_memory_loop_binding_contract_ref"] == (
        EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF
    )
    assert parsed.backend_owned is True
    assert parsed.safe_refs_only is True
    assert parsed.raw_content_included is False
    assert parsed.evidence_binding_count == len(parsed.evidence_bindings)
    assert parsed.memory_binding_count == len(parsed.memory_bindings)
    assert parsed.evidence_binding_count > 0
    assert parsed.memory_binding_count > 0
    assert parsed.run_refs
    assert parsed.proof_refs
    assert parsed.action_refs
    assert parsed.shared_loop_ref == EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF
    assert parsed.shared_run_refs == parsed.run_refs
    assert parsed.shared_action_refs == parsed.action_refs
    assert parsed.shared_proof_refs == parsed.proof_refs
    assert parsed.reviewed_memory_write_scope_ref.startswith(
        "exact-scope-ref:memory-review:"
    )
    assert parsed.reviewed_memory_write_authorized_decisions == ["accept", "correct"]
    assert parsed.reviewed_memory_write_authorized is any(
        binding.reviewed_memory_write_authorized for binding in parsed.memory_bindings
    )
    assert parsed.broad_memory_write_blocked is True
    assert parsed.memory_write_safe_disable_ref.startswith(
        "safe-disable-ref:memory-review:"
    )
    assert parsed.memory_write_rollback_ref.startswith("rollback-ref:memory-review:")
    assert set(EVIDENCE_MEMORY_LOOP_BINDING_PROMOTION_PATH_REFS).issubset(
        set(parsed.promotion_path_refs)
    )
    assert parsed.memory_candidate_refs
    assert set(EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS).issubset(
        set(parsed.blocked_authority_refs)
    )

    memory_binding = parsed.memory_bindings[0]
    assert memory_binding.why_shown_refs
    assert memory_binding.related_evidence_refs
    assert memory_binding.related_proof_refs
    assert memory_binding.shared_loop_refs == [EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF]
    assert memory_binding.shared_run_refs == parsed.shared_run_refs
    assert memory_binding.shared_action_refs == parsed.shared_action_refs
    assert memory_binding.shared_proof_refs == parsed.shared_proof_refs
    assert memory_binding.reviewed_recall_only is True
    assert memory_binding.reviewed_memory_write_scope_ref == (
        parsed.reviewed_memory_write_scope_ref
    )
    assert memory_binding.broad_memory_write_blocked is True
    assert memory_binding.memory_truth_authority is False
    assert memory_binding.context_injection_authorized is False

    evidence_binding = parsed.evidence_bindings[0]
    assert evidence_binding.timeline_item_ref.startswith("evidence-timeline:")
    assert evidence_binding.event_ref.startswith("evidence-event:")
    assert evidence_binding.proof_refs
    assert evidence_binding.run_refs
    assert evidence_binding.shared_loop_refs == [EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF]
    assert evidence_binding.shared_run_refs == parsed.shared_run_refs
    assert evidence_binding.shared_action_refs == parsed.shared_action_refs
    assert evidence_binding.shared_proof_refs == parsed.shared_proof_refs
    assert evidence_binding.action_refs or evidence_binding.memory_candidate_refs
    _assert_no_runtime_authority(read_model)


def test_memory_and_evidence_routes_forward_same_binding_model(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")

    today_model = repo.today_summary(limit=6)[
        "evidence_memory_loop_binding_read_model"
    ]
    memory_model = repo.memory_review(limit=6)[
        "evidence_memory_loop_binding_read_model"
    ]
    evidence_model = repo.evidence_timeline(limit=6)[
        "evidence_memory_loop_binding_read_model"
    ]

    assert memory_model == today_model
    assert evidence_model == today_model
    EvidenceMemoryLoopBindingReadModel(**memory_model)
    EvidenceMemoryLoopBindingReadModel(**evidence_model)


def test_evidence_memory_binding_cli_outputs_safe_refs_only(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_founder_loop.py",
            "--state-dir",
            str(state_dir),
            "inspect-evidence-memory-binding",
            "--limit",
            "5",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["command_ref"] == (
        "repo-local-command:founder-loop-evidence-memory-binding"
    )
    assert payload["safe_refs_only"] is True
    assert payload["raw_content_omitted"] is True
    read_model = payload["evidence_memory_loop_binding_read_model"]
    EvidenceMemoryLoopBindingReadModel(**read_model)
    _assert_no_runtime_authority(payload)
    assert str(state_dir).lower() not in result.stdout.lower()


def test_proof_spine_links_real_memory_and_evidence_refs(tmp_path: Path) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    index = service.proof_index()
    records = {record["proof_kind"]: record for record in index["records"]}

    memory_record = records["memory_decision"]
    assert memory_record["memory_candidate_refs"]
    assert memory_record["memory_candidate_refs"][0].startswith(
        "business-memory-candidate:"
    )
    assert "evidence-ref:founder-loop:memory" in memory_record["evidence_refs"]
    assert memory_record["evidence_refs"]

    evidence_records = [
        record for record in index["records"] if record["proof_kind"] == "evidence_event"
    ]
    assert evidence_records
    assert all(
        record["proof_ref"].startswith("proof-ref:evidence-event:")
        for record in evidence_records
    )
    assert all(record["evidence_refs"] for record in evidence_records)
    assert any(record["approval_refs"] for record in evidence_records)
    assert any(record["receipt_refs"] for record in evidence_records)
    _assert_no_runtime_authority(index)


def test_evidence_memory_binding_proof_refs_resolve_to_proof_detail(
    tmp_path: Path,
) -> None:
    service = FounderLoopControlCenterService(
        FounderLoopRepository(tmp_path / "founder_loop")
    )

    today = service.today_summary()
    parsed = EvidenceMemoryLoopBindingReadModel(
        **today["evidence_memory_loop_binding_read_model"]
    )
    proof_refs = set(service.proof_index()["proof_refs"])

    assert set(parsed.proof_refs) <= proof_refs
    assert set(parsed.shared_proof_refs) <= proof_refs
    for proof_ref in parsed.proof_refs:
        detail = service.proof_detail(proof_ref)
        assert detail["requested_proof_ref"] == proof_ref
        assert detail["record"]["status"] != "missing_proof_ref"
        _assert_no_runtime_authority(detail)


@pytest.mark.parametrize("flag", [
    "memory_truth_authority",
    "context_injection_authorized",
    "automatic_memory_write_authorized",
    "action_execution_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "production_authority_enabled",
])
def test_evidence_memory_binding_rejects_authority_creep(
    tmp_path: Path,
    flag: str,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    payload = repo.today_summary()["evidence_memory_loop_binding_read_model"]
    payload[flag] = True

    with pytest.raises(ValidationError):
        EvidenceMemoryLoopBindingReadModel(**payload)


def test_evidence_memory_binding_rejects_memory_write_boundary_drift(
    tmp_path: Path,
) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    payload = repo.today_summary()["evidence_memory_loop_binding_read_model"]
    payload["broad_memory_write_blocked"] = False

    with pytest.raises(ValidationError):
        EvidenceMemoryLoopBindingReadModel(**payload)


def test_evidence_memory_binding_rejects_shared_ref_drift(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    payload = repo.today_summary()["evidence_memory_loop_binding_read_model"]
    payload["shared_proof_refs"] = payload["shared_proof_refs"][1:]

    with pytest.raises(ValidationError):
        EvidenceMemoryLoopBindingReadModel(**payload)


def test_memory_binding_rejects_broad_memory_write_drift(tmp_path: Path) -> None:
    repo = FounderLoopRepository(tmp_path / "founder_loop")
    payload = repo.today_summary()["evidence_memory_loop_binding_read_model"]
    payload["memory_bindings"][0]["broad_memory_write_blocked"] = False

    with pytest.raises(ValidationError):
        EvidenceMemoryLoopBindingReadModel(**payload)
