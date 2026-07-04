#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.evidence_memory_loop_binding import (  # noqa: E402
    EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS,
    EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF,
    EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF,
    EvidenceMemoryLoopBindingReadModel,
)
from ultimate_ai_agent.core.control_center.founder_loop import (  # noqa: E402
    FounderLoopControlCenterService,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/evidence_memory_loop_binding.py"
PROOF = ROOT / "src/ultimate_ai_agent/core/control_center/proof.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
FOCUSED_TEST = ROOT / "tests/test_evidence_memory_loop_binding.py"
PROOF_TEST = ROOT / "tests/test_control_center_proof_spine.py"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
BOARD = ROOT / "docs/kanban/current_board.md"

FORBIDDEN_TEXT = [
    "raw prompt",
    "raw response",
    "provider payload",
    "api key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/etc/",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _assert_safe_payload(payload: dict[str, Any], failures: list[str]) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for snippet in FORBIDDEN_TEXT:
        if snippet in text:
            failures.append(f"payload contains forbidden snippet {snippet!r}")
    denied_fragments = [
        '"memory_truth_authority": true',
        '"context_injection_authorized": true',
        '"automatic_memory_write_authorized": true',
        '"memory_delete_enabled": true',
        '"memory_export_enabled": true',
        '"action_execution_enabled": true',
        '"connector_write_enabled": true',
        '"connector_send_enabled": true',
        '"provider_model_call_enabled": true',
        '"shell_subprocess_execution_enabled": true',
        '"browser_execution_enabled": true',
        '"background_autonomy_enabled": true',
        '"production_authority_enabled": true',
        '"raw_content_included": true',
    ]
    for fragment in denied_fragments:
        if fragment in text:
            failures.append(f"payload enables forbidden authority {fragment}")


def _verify_runtime_contract(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        service = FounderLoopControlCenterService(repo)

        today = service.today_summary()
        memory = service.memory_review()
        evidence = service.evidence_timeline()
        read_model = today["evidence_memory_loop_binding_read_model"]
        parsed = EvidenceMemoryLoopBindingReadModel(**read_model)

        if today["evidence_memory_loop_binding_contract_ref"] != (
            EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF
        ):
            failures.append("Today binding contract ref drifted")
        if memory["evidence_memory_loop_binding_read_model"] != read_model:
            failures.append("Memory Review binding does not match Today")
        if evidence["evidence_memory_loop_binding_read_model"] != read_model:
            failures.append("Evidence Timeline binding does not match Today")
        if parsed.shared_loop_ref != EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF:
            failures.append("Shared loop ref drifted")
        if parsed.shared_run_refs != parsed.run_refs:
            failures.append("Shared run refs drifted")
        if parsed.shared_action_refs != parsed.action_refs:
            failures.append("Shared action refs drifted")
        if parsed.shared_proof_refs != parsed.proof_refs:
            failures.append("Shared proof refs drifted")
        if parsed.reviewed_memory_write_authorized_decisions != ["accept", "correct"]:
            failures.append("Reviewed memory write decisions broadened")
        if not parsed.broad_memory_write_blocked:
            failures.append("Broad memory write is not blocked")
        if not set(EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS).issubset(
            set(parsed.blocked_authority_refs)
        ):
            failures.append("Missing Evidence/Memory blocked authority refs")
        for binding in [*parsed.evidence_bindings, *parsed.memory_bindings]:
            if binding.shared_loop_refs != [parsed.shared_loop_ref]:
                failures.append("Nested binding shared loop refs drifted")
            if binding.shared_run_refs != parsed.shared_run_refs:
                failures.append("Nested binding shared run refs drifted")
            if binding.shared_action_refs != parsed.shared_action_refs:
                failures.append("Nested binding shared action refs drifted")
            if binding.shared_proof_refs != parsed.shared_proof_refs:
                failures.append("Nested binding shared proof refs drifted")

        proof_index = service.proof_index()
        proof_refs = set(proof_index["proof_refs"])
        if not set(parsed.proof_refs).issubset(proof_refs):
            failures.append("Evidence/Memory proof refs do not resolve to proof index")
        for proof_ref in parsed.proof_refs:
            detail = service.proof_detail(proof_ref)
            if detail["record"]["status"] == "missing_proof_ref":
                failures.append(f"Proof detail missing for {proof_ref}")

        _assert_safe_payload(read_model, failures)
        _assert_safe_payload(proof_index, failures)


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT,
        PROOF,
        STORAGE,
        CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        FOCUSED_TEST,
        PROOF_TEST,
        RELEASE_SURFACE,
        TRUTH_PACKET,
        BOARD,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if not failures:
        _verify_runtime_contract(failures)

    _require(
        CONTRACT,
        [
            "EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF",
            "shared_action_refs",
            "shared_proof_refs",
            "reviewed_memory_write_authorized_decisions",
            "broad_memory_write_blocked",
            "derive_control_center_proof_ref",
        ],
        failures,
    )
    _require(
        PROOF,
        [
            "derive_control_center_proof_ref",
            "_memory_decision_records",
            "_evidence_event_records",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:founder-loop-evidence-memory-binding",
            "inspect-evidence-memory-binding",
            "raw_content_omitted",
            "raw_paths_omitted",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "shared_loop_ref: string",
            "shared_action_refs: string[]",
            "reviewed_memory_write_authorized_decisions: string[]",
            "broad_memory_write_blocked: boolean",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeEvidenceMemoryLoopBindingReadModel",
            "hasEvidenceMemoryAggregateSharedRefs",
            "hasEvidenceMemoryBindingSharedRefs",
            "reviewed_memory_write_authorized_decisions",
            "broad_memory_write_blocked",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Evidence and Memory loop binding unavailable",
            "Shared action refs",
            "Shared proof refs",
            "Reviewed write",
            "Broad memory write",
            "Promotion path refs",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_evidence_memory_binding_proof_refs_resolve_to_proof_detail",
            "test_evidence_memory_binding_rejects_shared_ref_drift",
            "broad_memory_write_blocked",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "fails closed when Evidence/Memory shared refs drift",
            "loop-binding-ref:evidence-memory:daily-loop-v1",
            "shared_proof_refs: []",
        ],
        failures,
    )
    _require(
        RELEASE_SURFACE,
        [
            "Proof Detail resolves the",
            "binding's universal Proof refs",
            "scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "Proof Detail resolves those proof refs",
            "does not expose the full binding read model",
            "scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "Beta 06 Evidence/Memory binding",
            "verify_beta_06_evidence_memory_binding.py",
        ],
        failures,
    )

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Beta 06 Evidence/Memory binding verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
