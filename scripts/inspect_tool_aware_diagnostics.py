#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.capabilities import (  # noqa: E402
    ToolAwareOperatorDiagnostic,
    build_tool_aware_operator_diagnostic,
)


TAW06_MAX_STDIN_BYTES = 262_144


def inspect_request_payload(payload: dict[str, Any]) -> ToolAwareOperatorDiagnostic:
    return build_tool_aware_operator_diagnostic(payload)


def _read_request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(TAW06_MAX_STDIN_BYTES + 1)
    if not raw or len(raw) > TAW06_MAX_STDIN_BYTES:
        raise ValueError("TAW06_DIAGNOSTIC_INPUT_INVALID")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("TAW06_DIAGNOSTIC_INPUT_INVALID")
    return payload


def render_human(diagnostic: ToolAwareOperatorDiagnostic) -> str:
    lines = [
        "Tool-aware operator diagnostic",
        f"Route: {diagnostic.route_label}",
        f"Familiarity: {diagnostic.familiarity_label}",
        f"Approval: {diagnostic.approval_summary}",
        f"Status: {diagnostic.operator_status.value}",
        "Limitations:",
        *(f"- {item}" for item in diagnostic.limitation_summaries),
        "Next:",
        *(f"- {item}" for item in diagnostic.required_next_steps),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a safe-ref-only TAW-04 shadow decision through the shared "
            "TAW-06 read model. Reads one JSON request from stdin."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the exact shared API read model instead of readable text.",
    )
    args = parser.parse_args()
    try:
        diagnostic = inspect_request_payload(_read_request())
    except (
        json.JSONDecodeError,
        RecursionError,
        UnicodeError,
        ValidationError,
        ValueError,
    ):
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason_ref": "reason-ref:taw06:diagnostic-input-invalid",
                    "safe_summary": (
                        "Diagnostic input must be one bounded safe-ref-only TAW-06 request."
                    ),
                    "raw_content_included": False,
                    "raw_local_paths_included": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    if args.json:
        print(json.dumps(diagnostic.model_dump(mode="json"), sort_keys=True))
    else:
        print(render_human(diagnostic))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
