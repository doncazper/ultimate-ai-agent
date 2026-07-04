from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import scripts.verify_beta_local as beta_local


ROOT = Path(__file__).resolve().parents[1]


def test_makefile_exposes_beta_local_gate() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "verify-beta-local:" in makefile
    assert "$(PYTHON) scripts/verify_beta_local.py" in makefile
    assert "verify-beta-local-visual:" in makefile
    assert "$(PYTHON) scripts/verify_beta_local.py --include-live-visual" in makefile


def test_beta_local_gate_lane_manifest_is_complete_and_relative() -> None:
    commands = beta_local.build_beta_local_gate_commands()

    assert beta_local.validate_gate_commands(commands) == []
    lane_ids = {command.lane_id for command in commands}
    assert beta_local.REQUIRED_LANES.issubset(lane_ids)
    assert {
        "private_beta_readiness",
        "private_product_loop_trial",
        "private_trial_packet",
        "private_trial_ledger",
        "private_trial_manual_review",
        "dogfood_live_loop",
        "dogfood_private_harness",
        "web_runtime_authority",
        "security_redaction",
        "api_perimeter",
        "gate_architecture",
    }.issubset(lane_ids)

    listed = "\n".join(beta_local.format_command(command) for command in commands)
    assert "/Users/" not in listed
    assert "provider payload" not in listed.lower()
    assert "api key" not in listed.lower()
    assert "make frontend-visual-check" not in listed
    assert "playwright" not in listed.lower()


def test_beta_local_gate_referenced_scripts_exist() -> None:
    for command in beta_local.build_beta_local_gate_commands():
        for arg in command.argv:
            if arg.startswith("scripts/") or arg.startswith("tests/"):
                assert (ROOT / arg).exists(), f"{command.command_ref} references {arg}"


def test_beta_local_gate_foundation_gate_is_report_only() -> None:
    foundation = next(
        command
        for command in beta_local.build_beta_local_gate_commands()
        if command.lane_id == "foundation_gate"
    )

    assert foundation.argv == (
        ".venv/bin/python",
        "scripts/run_foundation_gate.py",
        "--command-mode",
        "report-only",
        "--no-write-latest",
    )


def test_beta_local_live_visual_lane_is_explicit_only() -> None:
    default_argvs = [command.argv for command in beta_local.build_beta_local_gate_commands()]
    live_visual_commands = beta_local.build_live_visual_gate_commands()
    live_visual_argvs = [command.argv for command in live_visual_commands]

    assert ("make", "frontend-visual-check") not in default_argvs
    assert live_visual_argvs == [("make", "frontend-visual-check")]
    assert beta_local.validate_live_visual_gate_commands(live_visual_commands) == []


def test_beta_local_list_output_is_safe(capsys) -> None:
    assert beta_local.main(["--list"]) == 0

    output = capsys.readouterr().out
    assert "command:beta.local" not in output
    assert "command:dogfood.live-loop" in output
    assert "command:private-beta.readiness-gate" in output
    assert "/Users/" not in output
    assert "make frontend-visual-check" not in output


def test_beta_local_visual_list_output_is_safe(capsys) -> None:
    assert beta_local.main(["--list", "--include-live-visual"]) == 0

    output = capsys.readouterr().out
    assert "command:frontend.visual-check" in output
    assert "make frontend-visual-check" in output
    assert "/Users/" not in output


def test_beta_local_runner_stops_on_first_failure(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(argv, **_kwargs):
        calls.append(tuple(argv))
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(beta_local.subprocess, "run", fake_run)
    failures = beta_local.run_commands(
        [
            beta_local.BetaGateCommand(
                lane_id="first",
                command_ref="command:first",
                argv=("git", "diff", "--check"),
                purpose="first",
            ),
            beta_local.BetaGateCommand(
                lane_id="second",
                command_ref="command:second",
                argv=("make", "frontend-check"),
                purpose="second",
            ),
        ]
    )

    assert calls == [("git", "diff", "--check")]
    assert failures == ["command:first failed with exit code 1"]


def test_beta_local_failure_output_is_bounded_and_redacted(monkeypatch, capsys) -> None:
    local_path = str(ROOT / "apps/control-center/src/App.test.tsx")

    def fake_run(_argv, **_kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="\n".join([f"line {index}" for index in range(90)]),
            stderr=f"failure at {local_path}",
        )

    monkeypatch.setattr(beta_local.subprocess, "run", fake_run)
    failures = beta_local.run_commands(
        [
            beta_local.BetaGateCommand(
                lane_id="first",
                command_ref="command:first",
                argv=("git", "diff", "--check"),
                purpose="first",
            )
        ]
    )

    output = capsys.readouterr().out
    assert failures == ["command:first failed with exit code 1"]
    assert str(ROOT) not in output
    assert "<repo-root>/apps/control-center/src/App.test.tsx" in output
    assert "earlier output lines omitted" in output
