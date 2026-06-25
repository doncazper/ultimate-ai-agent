#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT = ROOT / "src/ultimate_ai_agent/core/control_center/morning_briefing.py"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
CLI = ROOT / "scripts/inspect_morning_briefing_v1.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_007_MORNING_BRIEFING_V1.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
FOCUSED_TEST = ROOT / "tests/test_morning_briefing_v1.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"


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
    from ultimate_ai_agent.core.control_center.morning_briefing import (
        MORNING_BRIEFING_V1_CONTRACT_REF,
        MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS,
        MorningBriefingV1ReadModel,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="product-loop-007-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        briefing = repo.morning_briefing()
        source_readiness = repo.source_readiness(briefing_items=briefing["items"])

    read_model = briefing.get("morning_briefing_v1_read_model")
    if not isinstance(read_model, dict):
        failures.append("morning_briefing() missing morning_briefing_v1_read_model")
        return
    if briefing.get("morning_briefing_v1_contract_ref") != (
        MORNING_BRIEFING_V1_CONTRACT_REF
    ):
        failures.append("morning_briefing() contract ref drifted")
    try:
        parsed = MorningBriefingV1ReadModel(**read_model)
    except Exception as exc:
        failures.append(f"Morning Briefing V1 model failed validation: {exc}")
        return

    if set(MORNING_BRIEFING_V1_REQUIRED_BLOCKED_REFS) - set(
        parsed.blocked_state_refs
    ):
        failures.append("Morning Briefing V1 missing required blocked refs")
    if not parsed.source_readiness_refs:
        failures.append("Morning Briefing V1 missing source readiness refs")
    if not parsed.missing_source_refs:
        failures.append("Morning Briefing V1 missing missing-source refs")
    if not parsed.open_action_refs:
        failures.append("Morning Briefing V1 missing open Action refs")
    if not parsed.memory_review_refs:
        failures.append("Morning Briefing V1 missing memory review refs")
    if not parsed.evidence_timeline_refs:
        failures.append("Morning Briefing V1 missing evidence timeline refs")
    if not parsed.repo_status_refs or not parsed.workbench_status_refs:
        failures.append("Morning Briefing V1 missing repo/workbench refs")

    denied_flags = [
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
        "notification_delivery_enabled",
        "source_refresh_enabled",
        "production_authority_enabled",
    ]
    for flag in denied_flags:
        if getattr(parsed, flag):
            failures.append(f"Morning Briefing V1 enables {flag}")

    if briefing.get("bounded_preview_only") is not True:
        failures.append("Morning Briefing lost bounded_preview_only")
    if briefing.get("refresh_enabled") is not False:
        failures.append("Morning Briefing enables refresh")
    if briefing.get("notification_delivery_enabled") is not False:
        failures.append("Morning Briefing enables notification delivery")
    posture = source_readiness.get("source_readiness_posture", {})
    for flag in [
        "connector_runtime_enabled",
        "source_refresh_enabled",
        "notification_delivery_enabled",
        "account_auth_enabled",
        "raw_source_ingestion_enabled",
        "write_authority_enabled",
    ]:
        if posture.get(flag) is not False:
            failures.append(f"Source readiness posture enables {flag}")


def _validate_cli(failures: list[str]) -> None:
    denied_flags = [
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
        "action_execution_enabled",
        "context_injection_authorized",
        "repo_write_enabled",
        "workbench_apply_enabled",
        "shell_subprocess_execution_enabled",
        "browser_execution_enabled",
        "notification_delivery_enabled",
        "source_refresh_enabled",
        "production_authority_enabled",
    ]
    with tempfile.TemporaryDirectory(prefix="product-loop-007-cli-") as temp_dir:
        state_dir = Path(temp_dir) / "missing-state"
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--state-dir",
                str(state_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        if state_dir.exists():
            failures.append("Morning Briefing V1 CLI created missing state dir")
        if payload.get("storage_state") != "state_not_found_no_write":
            failures.append("Morning Briefing V1 CLI did not fail closed on no state")
        if not payload.get("safe_refs_only") or not payload.get("raw_content_omitted"):
            failures.append("Morning Briefing V1 CLI lost redaction posture")
        for flag in denied_flags:
            if payload.get(flag) is not False:
                failures.append(f"Morning Briefing V1 missing-state CLI enables {flag}")

    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="product-loop-007-cli-existing-") as temp_dir:
        state_dir = Path(temp_dir) / "state"
        repo = FounderLoopRepository(state_dir, seed_defaults=True)
        repo.morning_briefing()
        recall_db = state_dir / "memory_review_recall.sqlite3"
        if recall_db.exists():
            recall_db.unlink()
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--state-dir",
                str(state_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        if recall_db.exists():
            failures.append("Morning Briefing V1 CLI created recall store in read-only mode")
        if payload.get("storage_state") != "existing_state_read_only":
            failures.append("Morning Briefing V1 CLI did not read existing state")
        for flag in denied_flags:
            if payload.get(flag) is not False:
                failures.append(f"Morning Briefing V1 existing-state CLI enables {flag}")
        lowered_stdout = result.stdout.lower()
        for marker in [
            "raw prompt",
            "raw response",
            "provider payload",
            "provider exchange",
            "credential",
            "password",
            "bearer ",
            "cookie",
            "secret=",
            "/users/",
            "/home/",
            "\\users\\",
        ]:
            if marker in lowered_stdout:
                failures.append(f"Morning Briefing V1 CLI leaked marker {marker!r}")


def main() -> int:
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
        BOARD,
        TRUTH_PACKET,
        INDEX,
        FOCUSED_TEST,
        API_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    forbidden_runtime_snippets = [
        "import subprocess",
        "subprocess.",
        "requests.",
        "httpx.",
        "urllib.request",
        "urllib3",
        "http.client",
        "playwright",
        "selenium",
        "firecrawl",
        "browserbase",
        "import provider_sdk",
        "provider_sdk.",
        "connector_read(",
        "execute_action(",
        "execute_workflow(",
        "connector_write(",
        "connector_runtime(",
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "from litellm",
        "import litellm",
        "litellm.",
        "provider_model_call(",
        "runtime_model_call(",
        "model_provider_call(",
    ]
    for path in [CONTRACT, STORAGE, CLI, FRONTEND_CLIENT, FRONTEND_PANEL, DOC]:
        _require_absent(path, forbidden_runtime_snippets, failures)
    for path in [CONTRACT, STORAGE, CLI, FRONTEND_CLIENT, FRONTEND_PANEL]:
        _require_absent(
            path,
            [
                "raw_prompt_content",
                "raw_response_content",
                "provider_payload_content",
                "provider_exchange_payload",
                "raw_local_path",
                "raw_log_content",
                "credential_value",
                "secret_value",
            ],
            failures,
        )

    _require(
        CONTRACT,
        [
            "MORNING_BRIEFING_V1_CONTRACT_REF",
            "MorningBriefingV1ReadModel",
            "build_morning_briefing_v1_read_model",
            "blocked-state:morning-briefing-no-email-calendar-fetch",
            "blocked-state:morning-briefing-no-live-web",
            "blocked-state:morning-briefing-no-connector-runtime",
            "blocked-state:morning-briefing-no-model-provider-call",
            "blocked-state:morning-briefing-no-automatic-recommendations",
            "blocked-state:morning-briefing-no-hidden-memory-write",
            "blocked-state:morning-briefing-no-repo-write",
            "blocked-state:morning-briefing-no-workbench-apply",
            "blocked-state:morning-briefing-no-shell-subprocess",
            "blocked-state:morning-briefing-no-browser-execution",
            "connector_read_enabled: bool = False",
            "provider_model_call_enabled: bool = False",
            "automatic_recommendations_enabled: bool = False",
            "hidden_memory_write_authorized: bool = False",
            "repo_write_enabled: bool = False",
            "workbench_apply_enabled: bool = False",
        ],
        failures,
    )
    _require(
        STORAGE,
        [
            "MORNING_BRIEFING_V1_CONTRACT_REF",
            "build_morning_briefing_v1_read_model(",
            '"morning_briefing_v1_contract_ref"',
            '"morning_briefing_v1_read_model"',
            "evidence_timeline = self._build_evidence_timeline(",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "repo-local-command:inspect-morning-briefing-v1",
            "seed_defaults=False",
            "ensure_storage=False",
            "read_only=True",
            "state_not_found_no_write",
            "raw_content_omitted",
            "raw_paths_omitted",
            '"connector_read_enabled": False',
            '"connector_runtime_enabled": False',
            '"provider_model_call_enabled": False',
            '"runtime_model_call_enabled": False',
            '"automatic_recommendations_enabled": False',
            '"hidden_memory_write_authorized": False',
            '"repo_write_enabled": False',
            '"workbench_apply_enabled": False',
            '"shell_subprocess_execution_enabled": False',
            '"browser_execution_enabled": False',
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopMorningBriefingV1ReadModel",
            "morning_briefing_v1_contract_ref?: string",
            "morning_briefing_v1_read_model?: FounderLoopMorningBriefingV1ReadModel",
            "connector_read_enabled: boolean",
            "automatic_recommendations_enabled: boolean",
            "hidden_memory_write_authorized: boolean",
            "repo_write_enabled: boolean",
            "workbench_apply_enabled: boolean",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "normalizeFounderMorningBriefing",
            "isSafeMorningBriefingV1ReadModel",
            "python_core_morning_briefing_v1_read_model",
            "delete normalized.morning_briefing_v1_read_model",
            "delete normalized.morning_briefing_v1_contract_ref",
            "MORNING_BRIEFING_V1_DENIED_FLAGS",
            "automatic_recommendations_enabled",
            "hidden_memory_write_authorized",
            "repo_write_enabled",
            "workbench_apply_enabled",
            "shell_subprocess_execution_enabled",
            "browser_execution_enabled",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "MorningBriefingV1Panel",
            "Morning Briefing V1",
            "backend read model missing",
            "Backend-owned local briefing",
            "Open Action refs",
            "Source readiness",
            "Missing sources",
            "Repo/workbench status",
            "Email/calendar fetch",
            "Automatic recommendations",
            "Hidden memory write",
            "Repo write",
            "Workbench apply",
            "Authority boundary",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "contract-ref:product-loop-007-morning-briefing-v1:v1",
            "Backend-owned Morning Briefing V1 read model",
            "Connector runtime",
            "Email/calendar fetch",
            "Automatic recommendations",
            "morning_briefing_v1_read_model",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "contract-ref:product-loop-007-morning-briefing-v1:v1",
            "scripts/inspect_morning_briefing_v1.py",
            "safe-ref-only",
            "backend-owned",
            "no connector reads",
            "no connector runtime",
            "no connector writes",
            "no email/calendar/account fetch",
            "no live web",
            "no runtime model/provider calls",
            "no automatic recommendations",
            "no hidden memory writes",
            "no repo writes",
            "no workbench apply",
            "missing integrations remain blocked/readiness states",
            "review candidates only",
            "raw prompt content",
            "raw response content",
            "raw provider",
            "raw local path content",
            "raw log content",
            "account identifiers",
            "usernames",
            "hostnames",
            "credentials",
            "secrets",
            "## Verification Lane",
            "tests/test_morning_briefing_v1.py",
            "scripts/verify_product_loop_007_morning_briefing_v1.py",
        ],
        failures,
    )
    _require(
        BOARD,
        [
            "Product Loop 007 Morning Briefing V1",
            "`morning_briefing_v1_read_model`",
            "`scripts/inspect_morning_briefing_v1.py`",
            "safe-ref-only",
            "blocked/readiness states",
            "review candidates only",
            "no connector reads",
            "no connector runtime",
            "no connector writes",
            "no email/calendar/account fetch",
            "no live web",
            "no runtime model/provider calls",
            "no automatic recommendations",
            "no hidden memory writes",
            "no repo writes",
            "no workbench apply",
            "no action execution",
            "no public beta",
            "no production authority",
        ],
        failures,
    )
    _require(
        TRUTH_PACKET,
        [
            "`morning_briefing_v1_read_model`",
            "scripts/inspect_morning_briefing_v1.py",
            "docs/control_center/PRODUCT_LOOP_007_MORNING_BRIEFING_V1.md",
            "missing integrations blocked/readiness-only",
            "review candidates only",
            "no connector reads",
            "no connector runtime",
            "no connector writes",
            "no email/calendar/account fetch",
            "no automatic recommendations",
            "no hidden memory writes",
            "no repo writes",
            "no workbench apply",
            "no runtime model/provider calls",
            "no source refresh",
            "no notification delivery",
            "no production authority",
        ],
        failures,
    )
    _require(
        INDEX,
        ["docs/control_center/PRODUCT_LOOP_007_MORNING_BRIEFING_V1.md"],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_morning_briefing_v1_surfaces_from_storage",
            "test_morning_briefing_v1_rejects_authority_and_raw_content",
            "test_morning_briefing_v1_cli_is_read_only_and_redacted",
        ],
        failures,
    )
    _require(
        API_TEST,
        [
            "morning_briefing_v1_contract_ref",
            "morning_briefing_v1_read_model",
            "python_core_morning_briefing_v1_read_model",
        ],
        failures,
    )

    panel_text = _read(FRONTEND_PANEL).lower()
    for forbidden in [
        "connector runtime enabled",
        "email/calendar fetch enabled",
        "provider calls enabled",
        "automatic recommendations enabled",
        "hidden memory write enabled",
        "action execution enabled",
    ]:
        if forbidden in panel_text:
            failures.append(f"Control Center wording implies authority: {forbidden}")

    _validate_live_read_model(failures)
    _validate_cli(failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Product Loop 007 Morning Briefing V1 verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
