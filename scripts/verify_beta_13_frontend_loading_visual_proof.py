#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scripts.verify_control_center_frontend as frontend
import scripts.verify_control_center_visual_regression as visual
from scripts.verification.api_routes import EXPECTED_OPENAPI_PATH_COUNT


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    failures.extend(frontend._route_state_grammar_failures(root))
    failures.extend(frontend._frontend_route_doc_failures(root))
    failures.extend(visual.validate_manifest(visual.load_manifest()))
    manifest_path = root / "docs/control_center/visual_regression_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    state_scenarios = manifest.get("state_scenarios", [])
    if not isinstance(state_scenarios, list):
        failures.append("beta-13 visual manifest state_scenarios must be a list")
        state_scenarios = []
    scenario_names = {
        str(scenario.get("scenario"))
        for scenario in state_scenarios
        if isinstance(scenario, dict)
    }
    if scenario_names != visual.REQUIRED_STATE_SCENARIOS:
        failures.append("beta-13 visual state scenarios must cover loading, empty, error, blocked, partial, and success")

    required_docs = {
        "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md": [
            "Beta 13 frontend route states and visual proof",
            "Full-strength",
            "Repo-safe",
            "Blocked / needs authority",
            "Exact promotion path",
        ],
        "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md": [
            "exact route proof",
            f"current backend path count is `{EXPECTED_OPENAPI_PATH_COUNT}`",
        ],
    }
    for rel_path, fragments in required_docs.items():
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing beta-13 doc: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in text:
                failures.append(f"{rel_path} missing beta-13 fragment: {fragment}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: beta-13 frontend loading, route states, and visual proof are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
