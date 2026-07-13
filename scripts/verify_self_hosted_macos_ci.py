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
    "actions/setup-python",
    "actions/setup-node",
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


def job_section(workflow: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n.*?(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
        workflow,
    )
    return match.group(0) if match is not None else ""


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
    lane_function_count = workflow.count("          run_lane_command() {")
    if workflow.count("          set +e\n          set -u") != lane_function_count:
        failures.append("every release lane must capture command failures before exiting")
    if "python3.12 -m venv .venv" not in workflow:
        failures.append("CI workflow must use the pre-provisioned Python 3.12 toolchain")
    if "/opt/homebrew/opt/node@22/bin" not in workflow:
        failures.append("CI workflow must use the pre-provisioned Node 22 toolchain")
    if '--basetemp "${RUNNER_TEMP}/uaa_pytest_shards"' not in workflow:
        failures.append("pytest shards must use the isolated per-job runner temp directory")
    if '--performance-report "${RUNNER_TEMP}/uaa_pytest_performance_report.json"' not in workflow:
        failures.append("pytest performance reports must use the isolated per-job runner temp directory")
    if '--timings-json "${RUNNER_TEMP}/uaa_static_verification_timings.json"' not in workflow:
        failures.append("static verification timings must use the isolated per-job runner temp directory")
    if "    needs:\n      - lint\n" not in job_section(workflow, "pytest-shards"):
        failures.append("pytest shards must start only after lint passes")
    pytest_shards_job = job_section(workflow, "pytest-shards")
    if "            --max-workers 2 \\\n" not in pytest_shards_job:
        failures.append("pytest shards must use the bounded two-worker single-host cap")
    if "--shard-index" in pytest_shards_job or "matrix:" in pytest_shards_job:
        failures.append("pytest shards must share one installed single-host environment")
    pytest_gated_jobs = (
        "static-verification",
        "release-lane-docs",
        "release-lane-openapi",
        "release-lane-api-safety",
        "release-lane-security-redaction",
        "release-lane-product-truth",
        "release-lane-local-model-e2e",
        "release-lane-durability",
        "release-lane-desktop-packaging",
    )
    if any(
        "    needs:\n      - pytest\n" not in job_section(workflow, job_name)
        for job_name in pytest_gated_jobs
    ):
        failures.append("backend release checks must wait for isolated pytest shards")
    control_center_job = job_section(workflow, "control-center-frontend")
    if not all(
        f"      - {dependency}\n" in control_center_job
        for dependency in (
            "static-verification",
            "release-lane-docs",
            "release-lane-api-safety",
            "release-lane-security-redaction",
            "release-lane-desktop-packaging",
        )
    ):
        failures.append("Control Center verification must wait for backend release checks")
    if "      - control-center-frontend\n" not in job_section(
        workflow, "release-lane-visual-regression"
    ):
        failures.append("visual regression must wait for Control Center verification")
    performance_job = job_section(workflow, "release-lane-performance")
    if not all(
        fragment in performance_job
        for fragment in (
            "    needs:\n",
            "      - pytest\n",
            "      - static-verification\n",
            "      - control-center-frontend\n",
        )
    ):
        failures.append("performance verification must run after the shared-Mac matrix")
    for fragment in (
        "--stretch-goal-seconds 900",
        "--target-seconds 1200",
        "--hard-timeout-seconds 1800",
    ):
        if fragment not in workflow:
            failures.append("pytest shards must declare the self-hosted runtime budget")
    if "reason-ref:self-hosted-runner-docker-unavailable" not in workflow:
        failures.append("desktop packaging must report an explicit unavailable Docker prerequisite")
    checkout_action = "uses: actions/checkout@v4"
    checkout_count = workflow.count(checkout_action)
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
        'install -d -o root -g wheel -m 0755 /usr/local/libexec\n',
        'install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci',
        'UserName</key>\n  <string>${RUNNER_ACCOUNT}</string>',
        "launchctl bootstrap system",
        "launchctl kickstart -k",
        "launchd did not settle after bootout",
        "/bin/sleep 2",
        'launchctl print "system/${service_label}"',
        "Homebrew python@3.12 is required",
        "Homebrew node@22 is required",
        "RUNNER_TOOL_CACHE</key>",
    )
    required_bootstrap_fragments = (
        'readonly RUNNER_VERSION="2.335.1"',
        'readonly RUNNER_SHA256="e1a9bc7a3661e06fa0b129d15c2064fe65dc81a431001d8958a9db1409b73769"',
        '[[ "$(id -u)" -ne 0 ]]',
        "must not be an administrator",
        "registration token on stdin",
        "--unattended",
        "--replace",
        ".metadata_never_index",
        "TOOLCHAIN_PATH",
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
