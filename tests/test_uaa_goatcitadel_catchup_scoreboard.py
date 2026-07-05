from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = ROOT / "scripts" / "verify_uaa_goatcitadel_catchup_scoreboard.py"
SCOREBOARD = ROOT / "docs" / "control_center" / "UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md"


def test_goatcitadel_catchup_scoreboard_verifier_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--report", str(SCOREBOARD)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "scoreboard verified" in result.stdout


def test_goatcitadel_catchup_scoreboard_verifier_blocks_absolute_paths(
    tmp_path: Path,
) -> None:
    unsafe_report = tmp_path / "unsafe_scoreboard.md"
    unsafe_report.write_text(
        "\n".join(
            [
                "# UAA GoatCitadel Catch-Up Scoreboard",
                "not runtime authority",
                "not copied from GoatCitadel",
                "read-only reference comparator",
                "safe refs",
                "does not change Control Center behavior",
                "/Users/example/private",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--report", str(unsafe_report)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "absolute local path" in result.stderr
