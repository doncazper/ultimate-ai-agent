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


def test_capability_availability_can_be_the_first_core_import() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import ultimate_ai_agent.core.capability_availability as availability; "
                "assert availability.CAPABILITY_AVAILABILITY_SCHEMA_VERSION"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, "direct capability availability import failed"


def test_capabilities_lazy_exports_preserve_representative_public_api() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import ultimate_ai_agent.core.capabilities as capabilities; "
                "assert capabilities.PolicyDecisionStatus; "
                "assert capabilities.CoordinationRiskLevel; "
                "assert capabilities.CapabilityRegistry; "
                "assert capabilities.LocalApprovalAuthority; "
                "assert capabilities.Coordinator; "
                "assert set(capabilities.__all__) == set(capabilities._LAZY_EXPORTS); "
                "tuple(getattr(capabilities, name) for name in capabilities.__all__)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, "capabilities lazy public exports drifted"
