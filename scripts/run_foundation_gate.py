#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.gate import FoundationGateEvaluator, FoundationGateStatus  # noqa: E402


GATE_TESTS = [
    "tests/test_foundation_gate_criteria.py",
    "tests/test_foundation_gate_report.py",
    "tests/test_shadow_replay_m5.py",
    "tests/test_contract_compatibility.py",
    "tests/test_foundation_gate_blocked_modules.py",
    "tests/test_foundation_gate_secret_hygiene.py",
    "tests/test_foundation_gate_receipts.py",
    "tests/test_foundation_gate_rollback.py",
    "tests/test_foundation_gate_truth_evidence.py",
    "tests/test_foundation_gate_api_routes.py",
]


def run_command(args: list[str]) -> int:
    print(f"\nRunning: {' '.join(args)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(args, cwd=ROOT, env=env, text=True)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"Command status: {status}")
    return result.returncode


def write_markdown(report_path: Path, markdown_path: Path) -> None:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    lines = [
        "# Foundation Gate Report",
        "",
        f"- Report: `{payload['report_id']}`",
        f"- Version: `{payload['version']}`",
        f"- Overall status: `{payload['overall_status']}`",
        f"- Summary: {payload['summary']}",
        f"- Next action: {payload['next_recommended_action']}",
        "",
        "## Criteria",
        "",
    ]
    for result in payload["results"]:
        lines.append(f"- `{result['criterion_id']}`: `{result['status']}` - {result['safe_message']}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M6 Foundation Gate checks.")
    parser.add_argument("--skip-commands", action="store_true", help="Only generate the typed gate report.")
    args = parser.parse_args(argv)

    command_failures = []
    if not args.skip_commands:
        commands = [
            [sys.executable, "-m", "pytest", *GATE_TESTS],
            [sys.executable, "scripts/verify_current_baseline.py"],
            [sys.executable, "scripts/verify_skill_package_security_rule.py"],
            [sys.executable, "scripts/verify_all.py"],
        ]
        for command in commands:
            return_code = run_command(command)
            if return_code != 0:
                command_failures.append(" ".join(command))

    report = FoundationGateEvaluator(ROOT).evaluate()
    output_dir = ROOT / "reports" / "foundation_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "latest_foundation_gate_report.json"
    markdown_path = output_dir / "latest_foundation_gate_report.md"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    write_markdown(report_path, markdown_path)

    print("\n=== Foundation Gate Summary ===")
    print(f"Report: {report_path.relative_to(ROOT)}")
    print(f"Markdown: {markdown_path.relative_to(ROOT)}")
    print(f"Overall status: {report.overall_status}")
    print(report.summary)

    if command_failures:
        print("\nCommand failures:")
        for failure in command_failures:
            print(f"- {failure}")
        return 1

    if report.overall_status != FoundationGateStatus.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
