#!/usr/bin/env python3
from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.sandbox_calculation.backend import (  # noqa: E402
    SealedCalculationBackendError,
    discover_local_docker_backend,
)
from ultimate_ai_agent.core.authority import (  # noqa: E402
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.runtime_gateway.storage import (  # noqa: E402
    RuntimeInvocationStore,
)


def main() -> int:
    try:
        backend = discover_local_docker_backend(
            seccomp_profile=(
                ROOT / "packaging" / "sealed-calculation" / "seccomp.json"
            ),
            kill_switch=authority_lease_kill_switch_engaged,
            safe_disabled=RuntimeInvocationStore().operator_safe_disable_active,
        )
    except (OSError, ValueError, SealedCalculationBackendError):
        print("FAIL: sealed calculation backend configuration is unavailable")
        return 1
    reasons = backend.readiness_reason_codes()
    if reasons:
        for reason in reasons:
            print(f"FAIL: {reason}")
        return 1
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "tests/test_sealed_calculation_runner.py",
        "tests/test_sealed_calculation_packaging.py",
        "tests/test_sealed_calculation_isolation.py",
        "tests/test_sealed_calculation_mission.py",
        "tests/test_sealed_calculation_cli.py",
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": "src",
            "UAA_REQUIRE_SEALED_BACKEND": "1",
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        return_code = process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
        print("FAIL: sealed calculation proof timed out")
        return 1
    if return_code != 0:
        print("FAIL: sealed calculation hostile proof suite failed")
        return 1
    print("UAA sealed calculation backend proof passed")
    print(f"Attestation: {backend.attestation.attestation_ref}")
    print(
        "Network, host mounts/files, unsafe environment, subprocesses, shells, and packages are denied."
    )
    print("Exact mission lease and current request-scoped evaluation remain required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
