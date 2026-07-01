#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center import (  # noqa: E402
    FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
    FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS,
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    FounderLoopProductProofReadModel,
    FounderLoopProductProofStep,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopRepository,
)


STEP_SURFACES = {
    "morning_briefing": ("Morning Briefing", "/briefing"),
    "today": ("Today", "/today"),
    "action_inbox": ("Action Inbox", "/actions"),
    "decision_receipt": ("Receipt", "/actions"),
    "evidence_timeline": ("Evidence Timeline", "/evidence"),
    "memory_review": ("Memory Review", "/memory"),
    "weekly_review": ("Weekly Review", "/today"),
}


def _state_dir(args: argparse.Namespace) -> Path:
    if args.state_dir:
        return Path(args.state_dir)
    configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _repo(state_dir: Path) -> FounderLoopRepository:
    return FounderLoopRepository(
        state_dir,
        seed_defaults=False,
        ensure_storage=False,
        read_only=True,
    )


def _empty_read_model() -> dict[str, Any]:
    steps = []
    for step_id in FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER:
        surface, frontend_route = STEP_SURFACES[step_id]
        steps.append(
            FounderLoopProductProofStep(
                step_id=step_id,  # type: ignore[arg-type]
                surface=surface,
                backend_route_ref="repo-local-inspection-no-state",
                frontend_route_ref=frontend_route,
                status="state_not_found_no_write",
                safe_summary=(
                    "Founder Loop product proof state is not available for "
                    "read-only inspection."
                ),
                evidence_refs=[
                    "evidence-ref:founder-loop-v1-product-proof:state-not-found"
                ],
                blocked_state_refs=list(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS),
                next_safe_action="Seed or inspect existing local Founder Loop state.",
            )
        )
    return FounderLoopProductProofReadModel(
        status="metadata_only_no_state_found",
        steps=steps,
        evidence_refs=["evidence-ref:founder-loop-v1-product-proof:state-not-found"],
        blocked_authority_refs=list(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS),
        weekly_review_status="state_not_found_no_write",
    ).model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the backend-owned Founder Loop V1 product proof read model."
    )
    parser.add_argument("--state-dir", default=None)
    parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args(argv)

    state_dir = _state_dir(args)
    db_path = state_dir / "founder_loop.sqlite3"
    inspection_error_ref: str | None = None
    if db_path.exists():
        try:
            repo = _repo(state_dir)
            payload = repo.founder_loop_product_proof(limit=args.limit)
            read_model = payload["founder_loop_v1_product_proof_read_model"]
            storage_state = "existing_state_read_only"
        except Exception:
            read_model = _empty_read_model()
            storage_state = "existing_state_unreadable_redacted"
            inspection_error_ref = (
                "error-ref:founder-loop-product-proof:read-failed-redacted"
            )
    else:
        read_model = _empty_read_model()
        storage_state = "state_not_found_no_write"

    output = {
        "schema_version": "founder-loop-v1-product-proof.inspect.v1",
        "command_ref": "repo-local-command:inspect-founder-loop-v1-product-proof",
        "contract_ref": FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "founder_loop_v1_product_proof_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "a2a_runtime_dispatch_enabled": False,
        "mcp_runtime_dispatch_enabled": False,
        "browser_execution_enabled": False,
        "live_web_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_send_enabled": False,
        "crm_write_enabled": False,
        "account_sync_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "background_autonomy_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "public_beta_claim_enabled": False,
        "public_release_claim_enabled": False,
        "production_authority_enabled": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
