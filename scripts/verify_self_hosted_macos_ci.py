#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_JOB_GRAPH,
    command_registry,
    validate_definition,
)

WORKFLOW = ROOT / ".github/workflows/ci.yml"
PROVISIONER = ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
BOOTSTRAP = ROOT / "scripts/ci/bootstrap_self_hosted_macos_runner.sh"
ACTIONLINT_CONFIG = ROOT / ".github/actionlint.yaml"
FORK_POLICY_WORKFLOW = ROOT / ".github/workflows/fork-pr-policy.yml"

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
    fork_policy_path = root / FORK_POLICY_WORKFLOW.relative_to(ROOT)
    for path in (
        workflow_path,
        provisioner_path,
        bootstrap_path,
        actionlint_path,
        fork_policy_path,
    ):
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
    if validate_definition():
        failures.append("canonical CI command manifest must validate")
    if "python3.12 -m venv .venv" not in workflow:
        failures.append("CI workflow must use the pre-provisioned Python 3.12 toolchain")
    if "/opt/homebrew/opt/node@22/bin" not in workflow:
        failures.append("CI workflow must use the pre-provisioned Node 22 toolchain")
    utility_shell = "/usr/sbin/taskpolicy -c utility /bin/bash --noprofile --norc -e -o pipefail {0}"
    if f"defaults:\n  run:\n    shell: {utility_shell}" not in workflow:
        failures.append("every CI command must escape inherited macOS background QoS throttling")
    if re.search(r"(?m)^\s+shell: bash$", workflow):
        failures.append("CI steps must not override the utility-QoS default shell")
    if set(jobs) != {job.job_ref for job in CI_JOB_GRAPH}:
        failures.append("CI workflow job refs must match the canonical job graph")
    for job in CI_JOB_GRAPH:
        section = job_section(workflow, job.job_ref)
        for dependency in job.needs:
            if f"      - {dependency}\n" not in section:
                failures.append(f"{job.job_ref} must preserve canonical dependency {dependency}")
        if job.lane_ref is not None:
            for fragment in (
                "scripts/verification/run_ci_lane.py",
                f"--lane {job.lane_ref}",
                '--sha "$UAA_CI_EXACT_SHA"',
                '--temp-root "$RUNNER_TEMP"',
                '--summary-file "$GITHUB_STEP_SUMMARY"',
            ):
                if fragment not in section:
                    failures.append(
                        f"{job.job_ref} must invoke its canonical shared CI lane"
                    )
        if f"    timeout-minutes: {job.timeout_minutes}\n" not in section:
            failures.append(f"{job.job_ref} must have its canonical bounded timeout")
    if "    needs:\n      - lint\n" not in job_section(workflow, "pytest-shards"):
        failures.append("pytest shards must start only after lint passes")
    pytest_shards_job = job_section(workflow, "pytest-shards")
    if "/usr/sbin/taskpolicy -c utility .venv/bin/python scripts/verification/run_ci_lane.py" not in pytest_shards_job:
        failures.append("pytest shards must escape inherited macOS background QoS throttling")
    if "trap terminate_shard_runner EXIT INT TERM HUP" not in pytest_shards_job:
        failures.append("pytest job cancellation must reach the shard runner")
    if "for _ in {1..100}" not in pytest_shards_job:
        failures.append("pytest job cancellation cleanup must remain bounded")
    if 'kill -KILL "$shard_runner_pid"' not in pytest_shards_job:
        failures.append("pytest job cancellation must escalate after the bounded wait")
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
    visual_regression_job = job_section(workflow, "release-lane-visual-regression")
    if "      - control-center-frontend\n" not in visual_regression_job:
        failures.append("visual regression must wait for Control Center verification")
    for fragment in (
        "          fetch-depth: 0\n",
        "      - name: Determine visual regression scope\n",
        "          PULL_REQUEST_BASE_SHA: ${{ github.event.pull_request.base.sha }}\n",
        "          PUSH_BEFORE_SHA: ${{ github.event.before }}\n",
        '          if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then\n',
        'git cat-file -e "${range_base}^{commit}"',
        'git diff --no-renames --quiet "$range_base" "$RANGE_HEAD_SHA" --',
        "              apps/control-center \\\n",
        "              docs/control_center \\\n",
        "              docs/schemas/control_center_release_surface.schema.json \\\n",
        "              tests/test_control_center_visual_and_packaging_proofs.py \\\n",
        "          run_visual=false\n",
        '          echo "run_visual=${run_visual}" >> "$GITHUB_OUTPUT"\n',
        "        if: steps.visual-scope.outputs.run_visual == 'true'\n",
        '          if [ "$RUN_VISUAL" = "true" ]; then\n',
        "reason-ref:visual-regression:not-affected",
        "      PLAYWRIGHT_BROWSERS_PATH: ${{ runner.temp }}/playwright-browsers\n",
        "            --lane visual-regression \\\n",
        '            --visual-scope "$visual_scope" \\\n',
    ):
        if fragment not in visual_regression_job:
            failures.append("visual regression scope must be affected-path bound and fail closed")
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
    shard_argv = command_registry()["command:pytest.sharded-suite"].argv
    for fragment in ("--stretch-goal-seconds", "900", "--target-seconds", "1200", "--hard-timeout-seconds", "1800"):
        if fragment not in shard_argv:
            failures.append("pytest shards must declare the self-hosted runtime budget")
    desktop_lane = job_section(workflow, "release-lane-desktop-packaging")
    if '--docker-available "$docker_posture"' not in desktop_lane:
        failures.append("desktop packaging must report an explicit unavailable Docker prerequisite")
    if (
        "      PLAYWRIGHT_BROWSERS_PATH: ${{ runner.temp }}/playwright-browsers\n"
        not in desktop_lane
    ):
        failures.append(
            "desktop packaging must share the canonical Playwright browser cache"
        )
    checkout_action = "uses: actions/checkout@v4"
    checkout_count = workflow.count(checkout_action)
    if checkout_count == 0 or workflow.count("persist-credentials: false") != checkout_count:
        failures.append("every checkout must avoid persisting GitHub credentials")
    if workflow.count("ref: ${{ env.UAA_CI_EXACT_SHA }}") != checkout_count:
        failures.append("every checkout must bind the explicit exact SHA")
    for fragment in FORBIDDEN_WORKFLOW_FRAGMENTS:
        if fragment in workflow:
            failures.append(f"forbidden self-hosted CI workflow fragment: {fragment}")

    provisioner = provisioner_path.read_text(encoding="utf-8")
    bootstrap = bootstrap_path.read_text(encoding="utf-8")
    actionlint_config = actionlint_path.read_text(encoding="utf-8")
    fork_policy = fork_policy_path.read_text(encoding="utf-8")
    required_fork_policy_fragments = (
        "pull_request_target:",
        "permissions: {}",
        "name: fork-policy",
        RUNNER_SELECTOR,
        "EXPECTED_REPOSITORY: ${{ github.repository }}",
        "PR_HEAD_REPOSITORY: ${{ github.event.pull_request.head.repo.full_name }}",
        'if [ "$PR_HEAD_REPOSITORY" != "$EXPECTED_REPOSITORY" ]; then',
    )
    if any(fragment not in fork_policy for fragment in required_fork_policy_fragments):
        failures.append("fork policy workflow must be base-controlled and fail closed")
    for forbidden in (
        "uses:",
        "checkout",
        "github.event.pull_request.head.sha",
        "github.event.pull_request.head.ref",
        "secrets.",
        "contents:",
    ):
        if forbidden in fork_policy:
            failures.append("fork policy workflow must remain metadata-only")
    if "self-hosted-runner:\n  labels:\n    - uaa-ci" not in actionlint_config:
        failures.append("actionlint must recognize only the custom UAA runner label")
    required_provisioner_fragments = (
        'readonly RUNNER_ACCOUNT="uaa-ci"',
        'readonly DEFAULT_RUNNER_COUNT=4',
        'readonly MAX_RUNNER_COUNT=4',
        "actions/runners/registration-token",
        'remote_registration_state="registered"',
        'remote_registration_state="absent"',
        'self-hosted runners require the UAA repository to remain private',
        'install -d -o root -g wheel -m 0755 /usr/local/libexec\n',
        'install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci',
        'UserName</key>\n  <string>${RUNNER_ACCOUNT}</string>',
        'ProcessType</key>\n  <string>Standard</string>',
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
        'ACTIONS_RUNNER_INPUT_TOKEN="$registration_token" ./config.sh',
        "local runner registration is stale",
        "regular non-symlink file",
        'settings.get("agentName")',
        'settings.get("gitHubUrl"',
        'settings.get("workFolder")',
        "--unattended",
        "--replace",
        ".metadata_never_index",
        "TOOLCHAIN_PATH",
    )
    for fragment in required_provisioner_fragments:
        if fragment not in provisioner:
            failures.append("runner provisioner is missing a required hardening control")
    if 'ProcessType</key>\n  <string>Background</string>' in provisioner:
        failures.append("runner services must not inherit macOS background throttling")
    for fragment in required_bootstrap_fragments:
        if fragment not in bootstrap:
            failures.append("runner bootstrap is missing a required hardening control")
    if '--token "$registration_token"' in bootstrap:
        failures.append("runner registration tokens must not be exposed in process arguments")
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
