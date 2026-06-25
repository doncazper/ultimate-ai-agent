#!/usr/bin/env python3
"""Verify Product Loop 010 Evidence Timeline narrative safety posture."""
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

from ultimate_ai_agent.core.storage import (  # noqa: E402
    EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF,
    EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE,
    FounderLoopEvidenceTimelineNarrativeReadModel,
    FounderLoopRepository,
)


STORAGE = SRC / "ultimate_ai_agent/core/storage/founder_loop.py"
STORAGE_INIT = SRC / "ultimate_ai_agent/core/storage/__init__.py"
CLI = ROOT / "scripts/inspect_evidence_timeline_narrative.py"
FOCUSED_TEST = ROOT / "tests/test_evidence_timeline_narrative_v1.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_CLIENT = ROOT / "apps/control-center/src/api/client.ts"
FRONTEND_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/PRODUCT_LOOP_010_EVIDENCE_TIMELINE_NARRATIVE.md"
BOARD = ROOT / "docs/kanban/current_board.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"

DENIED_FLAGS = [
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
    try:
        parsed = FounderLoopEvidenceTimelineNarrativeReadModel(**model)
    except Exception as exc:
        failures.append(f"Evidence Timeline narrative model rejected: {exc}")
        return
    if parsed.contract_ref != EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF:
        failures.append("Evidence Timeline narrative contract ref drifted")
    if parsed.source != EVIDENCE_TIMELINE_NARRATIVE_READ_MODEL_SOURCE:
        failures.append("Evidence Timeline narrative source drifted")
    if not parsed.entries:
        failures.append("Evidence Timeline narrative must include local entries")
    if parsed.narrative_refs != [entry.narrative_ref for entry in parsed.entries]:
        failures.append("Evidence Timeline narrative refs drifted from entries")
    for flag in DENIED_FLAGS:
        if getattr(parsed, flag):
            failures.append(f"Evidence Timeline narrative enables {flag}")
        for entry in parsed.entries:
            if getattr(entry, flag):
                failures.append(f"Evidence Timeline narrative entry enables {flag}")


def _validate_live(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-010-live-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir) / "founder_loop")
        payload = repo.evidence_timeline()
        if payload.get("narrative_contract_ref") != EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF:
            failures.append("Evidence Timeline payload missing narrative contract ref")
        read_model = payload.get("narrative_read_model")
        if not isinstance(read_model, dict):
            failures.append("Evidence Timeline payload missing narrative read model")
            return
        _assert_read_model(read_model, failures)
        for flag in DENIED_FLAGS:
            payload_copy = dict(read_model)
            payload_copy[flag] = True
            try:
                FounderLoopEvidenceTimelineNarrativeReadModel(**payload_copy)
            except ValueError:
                continue
            failures.append(f"Evidence Timeline narrative accepted unsafe flag {flag}")
        for unsafe_ref in (
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
        ):
            payload_copy = json.loads(json.dumps(read_model))
            entry_refs = list(payload_copy["entries"][0]["evidence_refs"])
            entry_refs.append(unsafe_ref)
            payload_copy["entries"][0]["evidence_refs"] = entry_refs
            payload_copy["evidence_refs"] = sorted(
                {*payload_copy["evidence_refs"], unsafe_ref}
            )
            try:
                FounderLoopEvidenceTimelineNarrativeReadModel(**payload_copy)
            except ValueError:
                continue
            failures.append(f"Evidence Timeline narrative accepted unsafe ref {unsafe_ref}")
        for unsafe_text in (
            "raw prompt",
            "raw-prompt",
            "raw response",
            "raw-response",
            "provider_payload",
            "provider-exchange-content",
            "raw-provider",
            "raw-path",
            "raw-log",
            "raw_private_content",
            "/Users/alice/project",
            "username alice was present",
            "username: alice was present",
            "hostname workstation.local was present",
            "hostname: workstation was present",
            "serial C02ABC123 was present",
            "serial: C02ABC123 was present",
            "actor-ref:username was present",
            "host-ref:hostname was present",
            "device-ref:serial was present",
            "Bearer token should fail",
        ):
            payload_copy = json.loads(json.dumps(read_model))
            payload_copy["entries"][0]["what_happened"] = unsafe_text
            try:
                FounderLoopEvidenceTimelineNarrativeReadModel(**payload_copy)
            except ValueError:
                continue
            failures.append(f"Evidence Timeline narrative accepted unsafe text {unsafe_text}")


def _validate_cli(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="product-loop-010-cli-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        repo = FounderLoopRepository(state_dir)
        repo.evidence_timeline()
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
            failures.append("Evidence Timeline narrative CLI modified existing state")
        payload = json.loads(result.stdout)
        if payload["storage_state"] != "existing_state_read_only":
            failures.append("Evidence Timeline narrative CLI did not report read-only state")
        _assert_read_model(payload["narrative_read_model"], failures)
        missing_state = Path(temp_dir) / "missing_state"
        missing_result = subprocess.run(
            [sys.executable, str(CLI), "--state-dir", str(missing_state)],
            check=True,
            capture_output=True,
            text=True,
        )
        missing_payload = json.loads(missing_result.stdout)
        if missing_payload["storage_state"] != "state_not_found_no_write":
            failures.append("Evidence Timeline narrative CLI missing-state posture drifted")
        if missing_state.exists():
            failures.append("Evidence Timeline narrative CLI created missing state")
        try:
            FounderLoopEvidenceTimelineNarrativeReadModel(
                **missing_payload["narrative_read_model"]
            )
        except Exception as exc:
            failures.append(f"Evidence Timeline missing-state read model rejected: {exc}")


def _validate_static(failures: list[str]) -> None:
    _require(
        STORAGE,
        [
            "EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF",
            "FounderLoopEvidenceNarrativeEntry",
            "FounderLoopEvidenceTimelineNarrativeReadModel",
            '"narrative_read_model"',
            "_evidence_timeline_narrative_read_model",
            "_validate_evidence_narrative_ref",
            "_validate_evidence_narrative_text",
            "_evidence_narrative_status_ref",
        ],
        failures,
    )
    _require(
        STORAGE_INIT,
        [
            "EVIDENCE_TIMELINE_NARRATIVE_CONTRACT_REF",
            "FounderLoopEvidenceTimelineNarrativeReadModel",
        ],
        failures,
    )
    _require(
        CLI,
        [
            "state_not_found_no_write",
            "ensure_storage=False",
            "read_only=True",
            "raw_content_omitted",
            "narrative_from_existing_refs_only",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_evidence_timeline_narrative_surfaces_existing_safe_refs",
            "test_evidence_timeline_narrative_rejects_authority_flags",
            "test_evidence_timeline_narrative_rejects_raw_private_text",
            "test_evidence_timeline_narrative_rejects_unsafe_refs",
            "test_evidence_timeline_narrative_rejects_aggregate_ref_drift",
            "test_evidence_timeline_narrative_cli_is_read_only_and_redacted",
            "evidence-ref:alice@example.com",
            "evidence-ref:workstation.local",
            "evidence-ref:relative/path/project",
            "actor-ref:username",
            "source-ref:private_key",
            "evidence-ref:raw-prompt",
            "evidence-ref:provider-exchange-content",
            "Bearer token should fail",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopEvidenceNarrativeEntry",
            "FounderLoopEvidenceTimelineNarrativeReadModel",
            "narrative_read_model",
        ],
        failures,
    )
    _require(
        FRONTEND_CLIENT,
        [
            "normalizeFounderEvidenceTimeline",
            "isSafeEvidenceTimelineNarrativeReadModel",
            "EVIDENCE_NARRATIVE_UNSAFE_TEXT_FRAGMENTS",
            "delete fallbackWithoutNarrative.narrative_read_model",
            "narrative_from_existing_refs_only",
        ],
        failures,
    )
    _require(
        FRONTEND_PANELS,
        [
            "EvidenceTimelineNarrativeSection",
            "narrative_read_model",
            "What happened",
            "Still blocked",
            "approval refs are identifiers only",
        ],
        failures,
    )
    _require(
        FRONTEND_MOCK,
        [
            "evidenceTimelineNarrativeReadModel",
            "product-loop-010-evidence-timeline-narrative.v1",
            "approval_ref_authority: false",
        ],
        failures,
    )
    _require(
        APP_TEST,
        [
            "renders Evidence Timeline narrative entries",
            "fails closed for unsafe Evidence Timeline narrative payloads",
            "does not backfill Evidence Timeline narrative from mocks",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "Product Loop 010",
            "Evidence Timeline narrative",
            "safe refs only",
            "scripts/inspect_evidence_timeline_narrative.py",
            "No approval authority",
            "No rollback execution",
            "No action execution",
            "No provider SDK calls",
            "No runtime model calls",
            "No live web",
            "No shell/browser execution",
            "No public beta",
            "No production authority",
        ],
        failures,
    )
    for doc in [BOARD, TRUTH_PACKET, INDEX, GAP_MAP]:
        _require(
            doc,
            [
                "Product Loop 010",
                "Evidence Timeline narrative",
                "no live web",
                "no public beta",
                "no production authority",
            ],
            failures,
        )
    for path in [STORAGE, CLI]:
        _require_absent(
            path,
            [
                "requests.",
                "httpx.",
                "urllib.request",
                "from openai",
                "import openai",
                "from anthropic",
                "import anthropic",
                "playwright",
                "selenium",
                "firecrawl",
                "browserbase",
                "execute_workflow(",
                "connector_write(",
            ],
            failures,
        )


def main() -> int:
    failures: list[str] = []
    _validate_live(failures)
    _validate_cli(failures)
    _validate_static(failures)
    if failures:
        print("Product Loop 010 Evidence Timeline narrative verifier failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Product Loop 010 Evidence Timeline narrative verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
