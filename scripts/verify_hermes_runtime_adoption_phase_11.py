#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "1")

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.core.memory import (  # noqa: E402
    MEMORY_BOUNDED_POSTURE_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


def _fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _assert_no_broad_memory_authority(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, sort_keys=True)
    forbidden_fragments = [
        '"automatic_memory_write_authorized": true',
        '"autonomous_memory_write_authorized": true',
        '"hidden_prompt_injection_authorized": true',
        '"external_memory_provider_write_authorized": true',
        '"context_injection_authorized": true',
        '"memory_truth_authority": true',
        '"semantic_provider_enabled": true',
        '"vector_db_enabled": true',
        '"embedding_search_enabled": true',
        '"model_provider_call_authorized": true',
        '"live_web_fetch_authorized": true',
        '"connector_write_authorized": true',
        '"delete_export_execution_authorized": true',
        '"background_autonomy_authorized": true',
        '"production_authority_enabled": true',
        '"raw_content_included": true',
        '"raw_content_stored": true',
    ]
    for fragment in forbidden_fragments:
        if fragment in serialized:
            _fail(f"forbidden bounded memory authority/content present: {fragment}")


def _assert_bounded_posture(payload: dict[str, Any]) -> None:
    if (
        payload.get("schema_version")
        != "hermes_runtime_adoption_bounded_memory_posture.v1"
    ):
        _fail("bounded memory schema drifted")
    if payload.get("contract_ref") != MEMORY_BOUNDED_POSTURE_CONTRACT_REF:
        _fail("bounded memory contract ref drifted")
    if payload.get("status") != "implemented_backend_owned_bounded_memory_posture":
        _fail("bounded memory status drifted")
    if payload.get("backend_owned") is not True:
        _fail("bounded memory posture must be backend-owned")
    if payload.get("control_center_presentation_only") is not True:
        _fail("Control Center must remain presentation-only")
    if payload.get("safe_refs_only") is not True:
        _fail("bounded memory posture must be safe-ref-only")
    if payload.get("raw_content_included") is not False:
        _fail("bounded memory posture must omit raw content")
    target = payload.get("target_posture")
    capacity = payload.get("capacity_posture")
    source = payload.get("source_posture")
    staleness = payload.get("staleness_posture")
    why_shown = payload.get("why_shown_posture")
    quality = payload.get("quality_review_posture")
    context_pack = payload.get("context_pack_posture")
    for label, value in {
        "target_posture": target,
        "capacity_posture": capacity,
        "source_posture": source,
        "staleness_posture": staleness,
        "why_shown_posture": why_shown,
        "quality_review_posture": quality,
        "context_pack_posture": context_pack,
    }.items():
        if not isinstance(value, dict):
            _fail(f"{label} missing")
    assert isinstance(target, dict)
    assert isinstance(capacity, dict)
    assert isinstance(source, dict)
    assert isinstance(staleness, dict)
    assert isinstance(why_shown, dict)
    assert isinstance(quality, dict)
    assert isinstance(context_pack, dict)
    if target.get("supported_target_kinds") != ["user", "profile", "project"]:
        _fail("bounded memory target kinds drifted")
    if target.get("operator_selected_context_required") is not True:
        _fail("bounded memory must require operator-selected context")
    if int(capacity.get("max_visible_items") or 0) != 80:
        _fail("bounded memory visible item cap drifted")
    if int(capacity.get("visible_item_count") or 0) < 1:
        _fail("bounded memory visible items missing")
    if source.get("safe_summary_only") is not True:
        _fail("bounded memory source posture must be safe-summary-only")
    if source.get("source_refs_required") is not True:
        _fail("bounded memory source refs must be required")
    if not source.get("source_refs"):
        _fail("bounded memory source refs missing")
    if int(staleness.get("stale_count") or 0) < 1:
        _fail("bounded memory staleness posture missing")
    if why_shown.get("why_shown_required") is not True:
        _fail("bounded memory why-shown posture must be required")
    if not why_shown.get("why_shown_refs"):
        _fail("bounded memory why-shown refs missing")
    if quality.get("review_required_before_recall") is not True:
        _fail("bounded memory must require review before recall")
    if quality.get("correction_supported") is not True:
        _fail("bounded memory correction posture missing")
    if quality.get("rejection_supported") is not True:
        _fail("bounded memory rejection posture missing")
    if quality.get("memory_write_requires_review_receipt") is not True:
        _fail("bounded memory write receipt requirement missing")
    if context_pack.get("context_pack_preview_only") is not True:
        _fail("bounded memory context packs must remain preview-only")
    if context_pack.get("context_injection_authorized") is not False:
        _fail("bounded memory context injection was authorized")
    blockers = payload.get("blocked_state_refs")
    if not isinstance(blockers, list) or (
        "blocked-state:bounded-memory-no-autonomous-memory-write" not in blockers
    ):
        _fail("bounded memory blocker refs missing")
    _assert_no_broad_memory_authority(payload)


def main() -> None:
    with TemporaryDirectory() as state_dir:
        repo = FounderLoopRepository(Path(state_dir))
        workbench = repo.memory_workbench()
        posture = workbench.get("bounded_memory_posture")
        if not isinstance(posture, dict):
            _fail("core workbench did not return bounded memory posture")
        _assert_bounded_posture(posture)

        review = repo.memory_review()
        review_posture = review.get("bounded_memory_posture")
        if not isinstance(review_posture, dict):
            _fail("core memory review did not return bounded memory posture")
        _assert_bounded_posture(review_posture)

    client = TestClient(app)
    workbench_response = client.get("/control-center/memory/workbench")
    if workbench_response.status_code != 200:
        _fail(f"memory workbench route returned {workbench_response.status_code}")
    api_workbench = workbench_response.json().get("data")
    if not isinstance(api_workbench, dict):
        _fail("memory workbench route did not return data")
    api_posture = api_workbench.get("bounded_memory_posture")
    if not isinstance(api_posture, dict):
        _fail("memory workbench route did not return bounded memory posture")
    _assert_bounded_posture(api_posture)

    review_response = client.get("/control-center/memory/review")
    if review_response.status_code != 200:
        _fail(f"memory review route returned {review_response.status_code}")
    api_review = review_response.json().get("data")
    if not isinstance(api_review, dict):
        _fail("memory review route did not return data")
    api_review_posture = api_review.get("bounded_memory_posture")
    if not isinstance(api_review_posture, dict):
        _fail("memory review route did not return bounded memory posture")
    _assert_bounded_posture(api_review_posture)

    with TemporaryDirectory() as state_dir:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/dev/uaa_founder_loop.py",
                "--state-dir",
                state_dir,
                "memory-bounded-posture",
                "--limit",
                "5",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    cli_payload = json.loads(result.stdout)
    cli_posture = cli_payload.get("bounded_memory_posture")
    if not isinstance(cli_posture, dict):
        _fail("CLI did not return bounded memory posture")
    if cli_payload.get("raw_prompt_omitted") is not True:
        _fail("CLI raw prompt omission flag missing")
    if cli_payload.get("raw_response_omitted") is not True:
        _fail("CLI raw response omission flag missing")
    if cli_payload.get("raw_provider_payload_omitted") is not True:
        _fail("CLI raw provider payload omission flag missing")
    _assert_bounded_posture(cli_posture)
    print("Hermes Runtime Adoption Phase 11 bounded memory verification passed.")


if __name__ == "__main__":
    main()
