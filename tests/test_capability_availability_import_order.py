from __future__ import annotations

import subprocess
import sys


def test_autonomy_can_import_before_capability_availability() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import ultimate_ai_agent.core.autonomy.modes; "
                "import ultimate_ai_agent.core.capability_availability"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, "capability availability import order failed"
