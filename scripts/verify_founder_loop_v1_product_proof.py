#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/founder_loop_product_proof.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_founder_loop_v1_product_proof.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/FOUNDER_LOOP_V1_PRODUCT_PROOF_PASS.md"
MILESTONES = ROOT / "docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
README = ROOT / "docs/README.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
FOCUSED_TEST = ROOT / "tests/test_founder_loop_v1_product_proof.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for snippet in snippets:
        if snippet.lower() in text:
            failures.append(
                f"{path.relative_to(ROOT)} contains forbidden snippet {snippet!r}"
            )


def _validate_live_read_model(failures: list[str]) -> None:
    from ultimate_ai_agent.core.control_center.action_decisions import (
        FounderLoopActionDecisionRequest,
    )
    from ultimate_ai_agent.core.control_center.founder_loop_product_proof import (
        FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS,
        FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
        FounderLoopProductProofReadModel,
    )
    from ultimate_ai_agent.core.memory import (
        FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
        MemoryReviewDecisionRequest,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="founder-loop-proof-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        action_receipt = repo.record_action_decision(
            action_id="setup-assistant-hardening",
            decision="defer",
            request=FounderLoopActionDecisionRequest(
                decision_reason_ref="decision-reason-ref:proof-verifier-action"
            ),
            idempotency_key_ref="idempotency-ref:proof-verifier-action",
        )
        candidate_ref = str(
            repo.list_memory_review_queue(limit=1)[0][
                "business_memory_candidate_ref"
            ]
        )
        memory_receipt = repo.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision="defer",
            request=MemoryReviewDecisionRequest(
                reviewer_ref="actor-ref:proof-verifier",
                source_refs=["source-ref:manual-note:proof-verifier"],
                evidence_refs=["evidence-ref:memory-review:proof-verifier"],
                blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
            ),
            idempotency_key_ref="idempotency-ref:proof-verifier-memory",
        )
        today = repo.today_summary()
        briefing = repo.morning_briefing()
        proof = repo.founder_loop_product_proof()

    read_model = today.get("founder_loop_v1_product_proof_read_model")
    if not isinstance(read_model, dict):
        failures.append("today_summary() missing product proof read model")
        return
    try:
        parsed = FounderLoopProductProofReadModel(**read_model)
    except Exception as exc:
        failures.append(f"Founder Loop product proof failed validation: {exc}")
        return
    if parsed.loop_order != list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER):
        failures.append("Founder Loop product proof loop order drifted")
    if set(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS) - set(
        parsed.blocked_authority_refs
    ):
        failures.append("Founder Loop product proof missing blocked refs")
    if briefing.get("founder_loop_v1_product_proof_read_model") != read_model:
        failures.append("Morning Briefing and Today product proof models diverged")
    if proof.get("founder_loop_v1_product_proof_read_model") != read_model:
        failures.append("CLI/repo inspection source diverged from Today product proof")
    if action_receipt["receipt_ref"] not in parsed.receipt_refs:
        failures.append("Action decision receipt missing from product proof")
    if memory_receipt["receipt_ref"] not in parsed.receipt_refs:
        failures.append("Memory review receipt missing from product proof")
    for flag in [
        "provider_model_call_enabled",
        "runtime_model_call_enabled",
        "a2a_runtime_dispatch_enabled",
        "mcp_runtime_dispatch_enabled",
        "browser_execution_enabled",
        "live_web_enabled",
        "connector_write_enabled",
        "email_calendar_send_enabled",
        "crm_write_enabled",
        "account_sync_enabled",
        "shell_subprocess_execution_enabled",
        "background_autonomy_enabled",
        "memory_write_authorized",
        "context_injection_authorized",
        "public_beta_claim_enabled",
        "public_release_claim_enabled",
        "production_authority_enabled",
    ]:
        if getattr(parsed, flag):
            failures.append(f"Founder Loop product proof enables {flag}")


def _validate_cli(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="founder-loop-proof-cli-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        from ultimate_ai_agent.core.storage import FounderLoopRepository

        FounderLoopRepository(state_dir).today_summary()
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--state-dir",
                str(state_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        failures.append("product proof CLI failed")
    if str(state_dir) in result.stdout:
        failures.append("product proof CLI leaked state path")
    if "raw_content_omitted" not in result.stdout:
        failures.append("product proof CLI missing raw-content omission flag")


def verify() -> list[str]:
    failures: list[str] = []
    for path in [
        CONTRACT,
        STORAGE,
        CLI,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_TEST,
        DOC,
        MILESTONES,
        INDEX,
        README,
        TRUTH_PACKET,
        FOCUSED_TEST,
    ]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    _require(
        CONTRACT,
        [
            "FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF",
            "FounderLoopProductProofReadModel",
            "build_founder_loop_product_proof_read_model",
            "FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "founder_loop_v1_product_proof_read_model",
            "def founder_loop_product_proof(",
            "build_founder_loop_product_proof_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "FounderLoopProductProofPanel",
            "Founder Loop V1 product proof",
            "founder_loop_v1_product_proof_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeFounderLoopProductProofReadModel",
            "FOUNDER_LOOP_PRODUCT_PROOF_DENIED_FLAGS",
            "founder_loop_v1_product_proof_read_model",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "Founder Loop V1 Product Proof Pass",
            "Morning Briefing -> Today -> Action Inbox",
            "No provider/model calls",
            "No public beta, public release, or production readiness claim",
        ],
        failures,
    )
    _require(
        MILESTONES,
        [
            "Founder Loop V1 Product Proof Pass",
            "founder_loop_v1_product_proof_read_model",
            "Still denied: provider/model calls",
        ],
        failures,
    )
    _require(
        INDEX,
        [
            "Founder Loop V1 product proof pass",
            "docs/control_center/FOUNDER_LOOP_V1_PRODUCT_PROOF_PASS.md",
            "scripts/verify_founder_loop_v1_product_proof.py",
        ],
        failures,
    )
    _require(
        README,
        [
            "Founder Loop V1 product proof pass",
            "founder_loop_v1_product_proof_read_model",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "Founder Loop V1 product proof pass",
            "founder_loop_v1_product_proof_read_model",
            "no provider/model calls",
        ],
        failures,
    )
    for path in [CONTRACT, DOC, FRONTEND_PANEL, FOCUSED_TEST]:
        _require_absent(
            path,
            [
                "production ready",
                "public beta is enabled",
                "connector writes enabled",
                "provider calls enabled",
            ],
            failures,
        )
    _validate_live_read_model(failures)
    _validate_cli(failures)
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Founder Loop V1 product proof verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
