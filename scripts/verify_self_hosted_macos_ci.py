#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"
PROVISIONER = ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
BOOTSTRAP = ROOT / "scripts/ci/bootstrap_self_hosted_macos_runner.sh"
ACTIONLINT_CONFIG = ROOT / ".github/actionlint.yaml"

RUNNER_SELECTOR = "runs-on: [self-hosted, macOS, ARM64, uaa-ci]"
FORK_GUARD = (
    "github.event_name == 'push' || "
    "github.event.pull_request.head.repo.full_name == github.repository"
)
FORBIDDEN_WORKFLOW_FRAGMENTS = (
    "ubuntu-latest",
    "macos-15",
    "windows-latest",
    "cache: pip",
    "cache: npm",
    "actions/cache",
    "actions/upload-artifact",
    "actions/download-artifact",
    "pull_request_target",
)


def job_names(workflow: str) -> tuple[str, ...]:
    jobs_section = workflow.split("\njobs:\n", 1)
    if len(jobs_section) != 2:
        return ()
    return tuple(
        match.group(1)
        for match in re.finditer(r"(?m)^  ([a-zA-Z0-9_-]+):$", jobs_section[1])
    )


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    workflow_path = root / WORKFLOW.relative_to(ROOT)
    provisioner_path = root / PROVISIONER.relative_to(ROOT)
    bootstrap_path = root / BOOTSTRAP.relative_to(ROOT)
    actionlint_path = root / ACTIONLINT_CONFIG.relative_to(ROOT)
    for path in (workflow_path, provisioner_path, bootstrap_path, actionlint_path):
        if not path.is_file():
            failures.append(f"missing self-hosted CI contract file: {path.relative_to(root)}")
    if failures:
        return failures

    workflow = workflow_path.read_text(encoding="utf-8")
    jobs = job_names(workflow)
    if not jobs:
        failures.append("CI workflow does not define jobs")
    if workflow.count(RUNNER_SELECTOR) != len(jobs):
        failures.append("every CI job must use the exact UAA self-hosted macOS selector")
    if workflow.count(FORK_GUARD) != len(jobs):
        failures.append("every CI job must fail closed for fork pull requests")
    if "permissions:\n  contents: read" not in workflow:
        failures.append("CI workflow token permissions must be contents-read only")
    if "cancel-in-progress: true" not in workflow:
        failures.append("CI workflow must cancel superseded local runs")
    checkout_count = workflow.count("uses: actions/checkout@v4")
    if checkout_count == 0 or workflow.count("persist-credentials: false") != checkout_count:
        failures.append("every checkout must avoid persisting GitHub credentials")
    for fragment in FORBIDDEN_WORKFLOW_FRAGMENTS:
        if fragment in workflow:
            failures.append(f"forbidden self-hosted CI workflow fragment: {fragment}")

    provisioner = provisioner_path.read_text(encoding="utf-8")
    bootstrap = bootstrap_path.read_text(encoding="utf-8")
    actionlint_config = actionlint_path.read_text(encoding="utf-8")
    if "self-hosted-runner:\n  labels:\n    - uaa-ci" not in actionlint_config:
        failures.append("actionlint must recognize only the custom UAA runner label")
    required_provisioner_fragments = (
        'readonly RUNNER_ACCOUNT="uaa-ci"',
        'readonly DEFAULT_RUNNER_COUNT=4',
        'readonly MAX_RUNNER_COUNT=4',
        "actions/runners/registration-token",
        'self-hosted runners require the UAA repository to remain private',
        'install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci',
        'UserName</key>\n  <string>${RUNNER_ACCOUNT}</string>',
        "launchctl bootstrap system",
        "launchctl kickstart -k",
    )
    required_bootstrap_fragments = (
        'readonly RUNNER_VERSION="2.335.1"',
        'readonly RUNNER_SHA256="e1a9bc7a3661e06fa0b129d15c2064fe65dc81a431001d8958a9db1409b73769"',
        '[[ "$(id -u)" -ne 0 ]]',
        "must not be an administrator",
        "registration token on stdin",
        "--unattended",
        "--replace",
    )
    for fragment in required_provisioner_fragments:
        if fragment not in provisioner:
            failures.append("runner provisioner is missing a required hardening control")
    for fragment in required_bootstrap_fragments:
        if fragment not in bootstrap:
            failures.append("runner bootstrap is missing a required hardening control")
    if "--disableupdate" in provisioner or "--disableupdate" in bootstrap:
        failures.append("automatic GitHub runner security updates must remain enabled")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: self-hosted macOS CI is repo-scoped, fork-guarded, and storage-cache free")
    return 0


if __name__ == "__main__":
    sys.exit(main())
