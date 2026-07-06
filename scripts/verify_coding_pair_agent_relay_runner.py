#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.code import (  # noqa: E402
    CODING_PAIR_AGENT_RELAY_LANE_REF,
    CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS,
    build_coding_multi_agent_review,
    build_coding_pair_agent_relay_read_model,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    relay = build_coding_pair_agent_relay_read_model()
    review = build_coding_multi_agent_review()
    payload = relay.model_dump(mode="json")

    _require(relay.lane_ref == CODING_PAIR_AGENT_RELAY_LANE_REF, "lane ref drifted")
    _require(relay.status == "preview_readiness_execution_blocked", "status drifted")
    _require(relay.backend_owned is True, "relay must be backend owned")
    _require(relay.preview_only is True, "relay must stay preview only")
    _require(relay.readiness_only is True, "relay must stay readiness only")
    _require(relay.safe_refs_only is True, "relay must stay safe refs only")
    _require(relay.execution_promoted is False, "execution was promoted")
    _require(
        relay.foreground_adapter_execution_enabled is False,
        "foreground adapter execution enabled",
    )
    _require(relay.generic_agent_bus_enabled is False, "generic agent bus enabled")
    _require(
        relay.arbitrary_command_text_allowed is False,
        "arbitrary command text allowed",
    )
    _require(
        relay.raw_transcript_durable is False,
        "raw transcript durable persistence enabled",
    )
    _require(
        set(CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS).issubset(
            relay.blocked_authority_refs
        ),
        "required blockers missing",
    )
    _require(review.pair_agent_relay.lane_ref == relay.lane_ref, "review nesting drifted")
    _require(len(relay.run_contract.agent_slots) == 2, "pair run needs two slots")
    _require(relay.run_contract.state == "blocked", "preview run must be blocked")
    _require(relay.run_contract.max_turns <= 12, "turn budget too broad")
    _require(
        relay.run_contract.wall_clock_timeout_seconds <= 3600,
        "timeout budget too broad",
    )
    _require(
        relay.run_contract.per_turn_output_limit_bytes <= 20000,
        "output budget too broad",
    )
    _require(len(relay.artifacts) == 7, "artifact taxonomy incomplete")
    _require(len(relay.receipts) == 9, "receipt taxonomy incomplete")
    _require(
        all(not artifact.durable_evidence for artifact in relay.artifacts),
        "raw artifacts cannot be durable evidence",
    )
    _require(
        all(not receipt.raw_content_included for receipt in relay.receipts),
        "receipt raw content included",
    )
    serialized = json.dumps(payload).lower()
    for forbidden in [
        "/users/",
        "-----begin",
        "raw_prompt_value",
        "raw_response_value",
        "provider_payload_value",
    ]:
        _require(forbidden not in serialized, f"unsafe marker persisted: {forbidden}")

    doc = _read("docs/control_center/CODING_PAIR_AGENT_RELAY_RUNNER.md")
    _require("Full-Strength Version" in doc, "missing full-strength doc section")
    _require("Repo-Safe Current Version" in doc, "missing repo-safe doc section")
    _require("Blocked / Needs Authority" in doc, "missing blocked doc section")
    _require("Exact Promotion Path" in doc, "missing promotion doc section")
    _require(
        "Do not introduce broad process" in _read(
            "docs/prompts/authority_graduation_program/generated_unblock_prompts/"
            "unblock_coding_pair_agent_foreground_relay_runner.prompt.md"
        ),
        "unblock prompt missing broad-process guard",
    )
    product_truth = _read("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md")
    _require("Coding Pair Agent Relay Runner" in product_truth, "product truth missing")
    _require("preview/readiness" in product_truth, "product truth overclaim risk")
    gap_map = _read("docs/control_center/OPERATOR_SHELL_GAP_MAP.md")
    _require("Pair Agents" in gap_map, "operator shell gap map missing pair agents")

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_coding.py",
            "inspect-pair-agent-relay",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(cli.stdout)
    _require(
        cli_payload["execution_promoted"] is False,
        "CLI payload promoted execution",
    )
    _require(
        cli_payload["foreground_adapter_execution_enabled"] is False,
        "CLI payload enabled foreground execution",
    )
    print("Coding Pair Agent Relay Runner verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
