#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)


CONTRACT_DOC = "docs/macos/UAA_P1_087_1_LOCAL_LAUNCHER_DUAL_SURFACE_BOOT_READINESS.md"
LAUNCHER_PATH = "scripts/dev/uaa_launcher.py"
LOCAL_LAUNCHER_DOC = "docs/developer/LOCAL_LAUNCHER.md"
SEQUENCE_DOC = "docs/macos/UAA_P1_087_PRIVATE_OPERATOR_BOOT_AND_UI_TRIAL_SEQUENCE.md"
SUCCESS_MESSAGE = "UAA-P1-087.1 local launcher dual-surface boot readiness verification passed."

REQUIRED_DOC_SNIPPETS = {
    CONTRACT_DOC: [
        "Status: Implemented",
        "Control Center is the first-party product surface",
        "OpenWebUI is the secondary local shell",
        "`./scripts/dev/uaa trial-boot`",
        "primary_ready_secondary_blocked",
        "No packages are installed and no images are pulled",
        "No new runtime authority",
    ],
    LOCAL_LAUNCHER_DOC: [
        "`uaa trial-boot`",
        "Control Center is the first-party product surface",
        "OpenWebUI is the secondary local shell",
        "primary_ready_secondary_blocked",
        "No packages are installed and no images are pulled by `uaa trial-boot`",
    ],
    SEQUENCE_DOC: [
        "`UAA-P1-087.1` Local Launcher Dual-Surface Boot Readiness is implemented",
    ],
}

FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "public release ready",
    "production authority is granted",
    "production ready",
    "signed installer is ready",
    "notarized app is ready",
    "launchagent is installed",
    "daemon is installed",
    "openwebui plugin is installed",
]


def _load_launcher() -> Any:
    launcher_path = ROOT / LAUNCHER_PATH
    spec = importlib.util.spec_from_file_location("uaa_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/dev/uaa_launcher.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify(
    launcher_module: Any | None = None,
    *,
    launcher_source: str | None = None,
    check_docs: bool = True,
) -> list[str]:
    launcher = launcher_module or _load_launcher()
    source = launcher_source if launcher_source is not None else read_text(LAUNCHER_PATH)
    failures: list[str] = []
    _append_launcher_contract_failures(failures, launcher, source)
    if check_docs:
        _append_docs_failures(failures)
    return failures


def _append_launcher_contract_failures(
    failures: list[str],
    launcher: Any,
    source: str,
) -> None:
    content = launcher.render_macos_launcher()
    for snippet in [
        "./scripts/dev/uaa trial-boot",
        "./scripts/dev/uaa status",
        "./scripts/dev/uaa openwebui status",
        "Trial boot reached a blocked or degraded state",
    ]:
        if snippet not in content:
            failures.append(f"macOS launcher missing {snippet!r}")
    for forbidden in ["sudo", "launchctl", "LaunchAgent", "/usr/local/bin", "brew install"]:
        if forbidden.lower() in content.lower():
            failures.append(f"macOS launcher contains forbidden {forbidden!r}")

    parsed = launcher.parse_args(["trial-boot"])
    if parsed.command != "trial-boot":
        failures.append("launcher parser does not register trial-boot")
    launch_ui = launcher.parse_args(["launch-ui"])
    if launch_ui.target != "control-center":
        failures.append("launch-ui no longer defaults to the first-party Control Center surface")

    required_source_snippets = [
        'DESIGNATED_UI_TARGET = "control-center"',
        "PRIMARY_READY_SECONDARY_BLOCKED",
        "def service_identity_ready",
        'url_status(f"{BACKEND_URL}/api/manifest") == 200',
        '"Ultimate AI Agent Control Center" in body',
        "def command_trial_boot",
        'command_launch_ui(root, target="control-center")',
        'command_launch_ui(root, target="openwebui")',
        'for name in ["backend", "frontend", "openwebui"]',
        "command_openwebui_stop(root)",
        "No packages were installed and no images were pulled by uaa trial-boot.",
    ]
    for snippet in required_source_snippets:
        if snippet not in source:
            failures.append(f"launcher source missing {snippet!r}")

    for service_name in ["backend", "frontend", "openwebui"]:
        status = launcher.status_for_service(launcher.service_config(ROOT, service_name))
        if f"log_ref=launcher-log:{service_name}" not in status:
            failures.append(f"{service_name} status missing safe log ref")

    forbidden_source_snippets = [
        "shell=True",
        "0.0.0.0",
        "launchctl",
        "osascript",
        "sudo ",
        "brew install",
    ]
    for forbidden in forbidden_source_snippets:
        if forbidden in source:
            failures.append(f"launcher source contains forbidden {forbidden!r}")


def _append_docs_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    append_forbidden_claims(
        failures,
        [
            CONTRACT_DOC,
            LOCAL_LAUNCHER_DOC,
            SEQUENCE_DOC,
            "README.md",
            "docs/README.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/kanban/current_board.md",
            "docs/kanban/founder_command_center_board.md",
            "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        ],
        FORBIDDEN_CLAIMS,
    )


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
