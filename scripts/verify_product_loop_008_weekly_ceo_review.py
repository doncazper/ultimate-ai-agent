#!/usr/bin/env python3
"""Verify Product Loop 008 Weekly CEO Review V1 safety posture."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.control_center.weekly_ceo_review import (  # noqa: E402
    WEEKLY_CEO_REVIEW_V1_CONTRACT_REF,
    WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE,
    WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS,
    WeeklyCeoReviewV1ReadModel,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


CONTRACT = SRC / "ultimate_ai_agent/core/control_center/weekly_ceo_review.py"
STORAGE = SRC / "ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_weekly_ceo_review.py"
FOCUSED_TEST = ROOT / "tests/test_weekly_ceo_review_v1.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_008_WEEKLY_CEO_REVIEW.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"

DENIED_FLAGS = [
    "raw_logs_included",
    "prompt_content_included",
    "response_content_included",
    "provider_exchange_content_included",
    "connector_read_enabled",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "email_calendar_fetch_enabled",
    "live_web_enabled",
    "model_summary_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "action_execution_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "public_beta_claim_enabled",
    "production_claim_enabled",
    "production_authority_enabled",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, fragments: list[str], failures: list[str]) -> None:
    text = _read(path)
    for fragment in fragments:
        if fragment not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {fragment!r}")


def _require_absent(path: Path, fragments: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for fragment in fragments:
        if fragment.lower() in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {fragment!r}")


def _assert_read_model(model: dict[str, Any], failures: list[str]) -> None:
    parsed = WeeklyCeoReviewV1ReadModel(**model)
    if parsed.contract_ref != WEEKLY_CEO_REVIEW_V1_CONTRACT_REF:
        failures.append("Weekly CEO Review V1 contract ref drifted")
    if parsed.source != WEEKLY_CEO_REVIEW_V1_READ_MODEL_SOURCE:
        failures.append("Weekly CEO Review V1 source drifted")
    missing = set(WEEKLY_CEO_REVIEW_V1_REQUIRED_BLOCKED_REFS) - set(
        parsed.blocked_authority_refs
    )
    if missing:
        failures.append("Weekly CEO Review V1 missing required blocked refs")
    for flag in DENIED_FLAGS:
        if getattr(parsed, flag):
            failures.append(f"Weekly CEO Review V1 enables {flag}")
    if not parsed.evidence_refs:
        failures.append("Weekly CEO Review V1 missing evidence refs")
    if not parsed.unresolved_refs:
        failures.append("Weekly CEO Review V1 missing unresolved refs")
    if not parsed.evidence_event_refs:
        failures.append("Weekly CEO Review V1 missing evidence event refs")


def _validate_live(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-008-live-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        weekly = repo.weekly_ceo_review()
        _assert_read_model(weekly["weekly_ceo_review_v1_read_model"], failures)
        today = repo.today_summary()
        briefing = repo.morning_briefing()
        if "weekly_ceo_review_v1_read_model" not in today:
            failures.append("Today missing Weekly CEO Review V1 read model")
        if "weekly_ceo_review_v1_read_model" not in briefing:
            failures.append("Morning Briefing missing Weekly CEO Review V1 read model")
        for flag in DENIED_FLAGS:
            payload = dict(weekly["weekly_ceo_review_v1_read_model"])
            payload[flag] = True
            try:
                WeeklyCeoReviewV1ReadModel(**payload)
            except ValueError:
                continue
            failures.append(f"Weekly CEO Review V1 accepted unsafe flag {flag}")
        for unsafe_ref in (
            "evidence-ref:alice@example.com",
            "evidence-ref:workstation.local",
            "evidence-ref:relative/path/project",
        ):
            payload = dict(weekly["weekly_ceo_review_v1_read_model"])
            payload["evidence_refs"] = [unsafe_ref]
            try:
                WeeklyCeoReviewV1ReadModel(**payload)
            except ValueError:
                continue
            failures.append(f"Weekly CEO Review V1 accepted unsafe ref {unsafe_ref}")
        payload = dict(weekly["weekly_ceo_review_v1_read_model"])
        payload["completed_count"] = len(payload["completed_refs"]) + 1
        try:
            WeeklyCeoReviewV1ReadModel(**payload)
        except ValueError:
            pass
        else:
            failures.append("Weekly CEO Review V1 accepted mismatched counts")


def _validate_cli(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-008-cli-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        repo = FounderLoopRepository(state_dir)
        repo.weekly_ceo_review()
        before_files = {
            path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in state_dir.rglob("*")
            if path.is_file()
        }
        result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(state_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        after_files = {
            path.relative_to(state_dir): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in state_dir.rglob("*")
            if path.is_file()
        }
        if after_files != before_files:
            failures.append("Weekly CEO Review CLI modified existing state")
        payload = json.loads(result.stdout)
        if payload["storage_state"] != "existing_state_read_only":
            failures.append("Weekly CEO Review CLI lost read-only state label")
        if payload["safe_refs_only"] is not True or payload["safe_summary_only"] is not True:
            failures.append("Weekly CEO Review CLI lost safe refs/summary posture")
        if payload["raw_content_omitted"] is not True or payload["raw_paths_omitted"] is not True:
            failures.append("Weekly CEO Review CLI lost raw omission posture")
        for flag in DENIED_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"Weekly CEO Review CLI enables {flag}")
        _assert_no_cli_leak(result.stdout, failures)
        _assert_read_model(payload["weekly_ceo_review_v1_read_model"], failures)

        missing_state = Path(temp_dir) / "missing_state"
        missing_result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(missing_state)],
            check=True,
            capture_output=True,
            text=True,
        )
        missing_payload = json.loads(missing_result.stdout)
        if missing_payload["storage_state"] != "state_not_found_no_write":
            failures.append("Weekly CEO Review CLI missing state label drifted")
        if missing_state.exists():
            failures.append("Weekly CEO Review CLI created missing state")
        if (
            missing_payload["safe_refs_only"] is not True
            or missing_payload["safe_summary_only"] is not True
        ):
            failures.append("Weekly CEO Review missing-state CLI lost safe posture")
        for flag in DENIED_FLAGS:
            if missing_payload.get(flag) is not False:
                failures.append(f"Weekly CEO Review missing-state CLI enables {flag}")
        _assert_no_cli_leak(missing_result.stdout, failures)
        _assert_read_model(
            missing_payload["weekly_ceo_review_v1_read_model"],
            failures,
        )


def _assert_no_cli_leak(stdout: str, failures: list[str]) -> None:
    lowered = stdout.lower()
    for marker in [
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "provider_exchange_payload",
        "username",
        "hostname",
        "credential",
        "secret",
        "cookie",
        "token",
        "password",
        "private_key",
        "env dump",
        "environment dump",
        "/users/",
        "/home/",
        "/private/",
        "\\users\\",
    ]:
        if marker in lowered:
            failures.append(f"Weekly CEO Review CLI emitted {marker}")


def _validate_static(failures: list[str]) -> None:
    for path in [
        CONTRACT,
        STORAGE,
        CLI,
        FOCUSED_TEST,
        FRONTEND_TYPES,
        FRONTEND_CLIENT,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        DOC,
        BOARD,
        TRUTH_PACKET,
        INDEX,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        return

    _require(
        CONTRACT,
        [
            "WEEKLY_CEO_REVIEW_V1_CONTRACT_REF",
            "WeeklyCeoReviewV1ReadModel",
            "build_weekly_ceo_review_v1_read_model",
            "model_summary_enabled",
            "provider_model_call_enabled",
            "production_claim_enabled",
            "extra=\"forbid\"",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "def weekly_ceo_review(",
            '"weekly_ceo_review_v1_read_model"',
            "build_weekly_ceo_review_v1_read_model(",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:inspect-weekly-ceo-review",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "sqlite_state = state_dir / \"founder_loop.sqlite3\"",
            "state_not_found_no_write",
            '"model_summary_enabled": False',
            '"provider_model_call_enabled": False',
            '"production_claim_enabled": False',
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "isSafeWeeklyCeoReviewV1ReadModel",
            "WEEKLY_CEO_REVIEW_V1_DENIED_FLAGS",
            "delete fallbackWithoutDigest.weekly_ceo_review_v1_read_model",
            "delete normalized.weekly_ceo_review_v1_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "WeeklyCeoReviewV1Panel",
            "Backend-owned Weekly CEO Review V1 read model",
            "Model summaries",
            "Production claim",
            "Weekly review authority blockers",
        ],
        failures,
    )
    _require(
        APP_TEST,
        [
            "renders backend-owned Weekly CEO Review V1 from backend data",
            "does not backfill Weekly CEO Review V1 from mocks",
            "fails closed for unsafe backend Weekly CEO Review V1 authority flags",
            "Backend-owned Weekly CEO Review V1 read model",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "Product Loop 008",
            "backend-owned",
            "safe-summary-only",
            "No connector reads",
            "No model summaries",
            "No production claims",
            "scripts/inspect_weekly_ceo_review.py",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_weekly_ceo_review_v1_surfaces_receipt_backed_safe_refs",
            "test_weekly_ceo_review_v1_rejects_authority_and_raw_content",
            "evidence-ref:alice@example.com",
            "evidence-ref:workstation.local",
            "evidence-ref:relative/path/project",
            "test_weekly_ceo_review_v1_excludes_planned_receipts_from_completed_refs",
            "test_weekly_ceo_review_cli_is_read_only_and_redacted",
        ],
        failures,
    )

    forbidden_runtime_snippets = [
        "import subprocess",
        "subprocess.",
        "requests.",
        "httpx.",
        "urllib.request",
        "playwright",
        "selenium",
        "firecrawl",
        "browserbase",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "from litellm",
        "import litellm",
        "connector_read(",
        "connector_runtime(",
        "provider_model_call(",
        "runtime_model_call(",
        "execute_action(",
        "execute_workflow(",
        "connector_write(",
    ]
    for path in [CONTRACT, STORAGE, CLI, FRONTEND_CLIENT, FRONTEND_PANEL]:
        _require_absent(path, forbidden_runtime_snippets, failures)


def main() -> int:
    failures: list[str] = []
    _validate_static(failures)
    _validate_live(failures)
    _validate_cli(failures)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Product Loop 008 Weekly CEO Review verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
