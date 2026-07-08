#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.memory import (  # noqa: E402
    MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS,
    MEMORY_LEARNING_POSTURE_CONTRACT_REF,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


BROAD_AUTHORITY_FLAGS = (
    "forget_execution_authorized",
    "broad_memory_write_authorized",
    "automatic_memory_write_authorized",
    "hidden_context_injection_authorized",
    "automatic_context_injection_authorized",
    "memory_truth_authority",
    "policy_override_authorized",
    "action_execution_authorized",
    "connector_write_authorized",
    "model_provider_call_authorized",
    "live_web_fetch_authorized",
    "background_autonomy_authorized",
    "hard_delete_authorized",
    "export_execution_authorized",
    "production_authority_enabled",
)


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="uaa-memory-learning-") as temp:
        repo = FounderLoopRepository(Path(temp) / "founder-loop")
        workbench = repo.memory_workbench(limit=50)
        posture = workbench.get("learning_posture") or {}

    if posture.get("contract_ref") != MEMORY_LEARNING_POSTURE_CONTRACT_REF:
        failures.append("memory learning posture contract ref drifted")
    if posture.get("source") != "python_core_memory_workbench_learning_posture":
        failures.append("memory learning posture source drifted")
    for field in [
        "backend_owned",
        "control_center_presentation_only",
        "safe_refs_only",
        "proposal_first_intake",
        "review_required_before_recall",
        "feedback_receipts_supported",
        "correction_receipts_supported",
        "rejection_receipts_supported",
        "forget_request_receipts_supported",
    ]:
        if posture.get(field) is not True:
            failures.append(f"memory learning posture {field} must be true")
    if posture.get("raw_content_included") is not False:
        failures.append("memory learning posture raw content must be omitted")
    for flag in BROAD_AUTHORITY_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"memory learning posture broadened {flag}")
    if set(MEMORY_LEARNING_POSTURE_BLOCKED_STATE_REFS) - set(
        posture.get("blocked_state_refs") or []
    ):
        failures.append("memory learning posture lost blocked authority refs")
    lifecycle_counts = posture.get("lifecycle_state_counts") or {}
    for state in [
        "proposed",
        "active",
        "needs_review",
        "corrected",
        "rejected",
        "stale",
        "forgotten",
        "blocked",
    ]:
        if state not in lifecycle_counts:
            failures.append(f"memory learning lifecycle count missing {state}")
    context_pack_posture = posture.get("context_pack_posture") or {}
    for flag in [
        "context_injection_authorized",
        "hidden_prompt_context_authorized",
        "prompt_context_written",
        "provider_model_call_performed",
        "action_execution_authorized",
    ]:
        if context_pack_posture.get(flag) is not False:
            failures.append(f"context-pack posture broadened {flag}")
    quality_posture = posture.get("quality_posture") or {}
    for flag in [
        "semantic_search_enabled",
        "vector_db_enabled",
        "embedding_search_enabled",
    ]:
        if quality_posture.get(flag) is not False:
            failures.append(f"quality posture broadened {flag}")
    provenance_posture = posture.get("provenance_posture") or {}
    for field in [
        "source_refs_required",
        "evidence_refs_required",
        "receipt_refs_required_for_reviewed_recall",
        "safe_summary_only",
    ]:
        if provenance_posture.get(field) is not True:
            failures.append(f"provenance posture {field} must be true")

    docs = [
        ROOT / "docs/control_center/UAA_RUNTIME_MEMORY_LEARNING.md",
        ROOT / "docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md",
    ]
    for doc in docs:
        if not doc.exists():
            failures.append(f"required doc missing: {doc.name}")
            continue
        text = doc.read_text(encoding="utf-8")
        if MEMORY_LEARNING_POSTURE_CONTRACT_REF not in text:
            failures.append(f"memory learning contract ref missing from {doc.name}")
        if "memory-learning-posture" not in text:
            failures.append(f"CLI inspection ref missing from {doc.name}")
        normalized_text = " ".join(text.lower().split())
        if "memory remains recall and reviewable context" not in normalized_text:
            failures.append(f"memory authority boundary missing from {doc.name}")

    cli_text = (ROOT / "scripts/dev/uaa_founder_loop.py").read_text(
        encoding="utf-8"
    )
    if "memory-learning-posture" not in cli_text:
        failures.append("Founder Loop CLI memory learning command missing")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA runtime memory learning verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
