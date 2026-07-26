#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CANONICAL_PYTEST_SHARD_COUNT,
    CI_JOB_GRAPH,
    command_registry,
    validate_definition,
)

WORKFLOW = ROOT / ".github/workflows/ci.yml"
TOOLCHAIN_ACTION = ROOT / ".github/actions/setup-toolchain/action.yml"
ACTIONLINT_CONFIG = ROOT / ".github/actionlint.yaml"
FORK_POLICY_WORKFLOW = ROOT / ".github/workflows/fork-pr-policy.yml"
SUPPLY_CHAIN_WORKFLOW = ROOT / ".github/workflows/supply-chain.yml"
MACOS_RELEASE_WORKFLOW = ROOT / ".github/workflows/macos-release.yml"

CI_RUNNER_SELECTOR = "runs-on: macos-15"
FORK_POLICY_RUNNER_SELECTOR = "runs-on: ubuntu-24.04"
SETUP_TOOLCHAIN_ACTION = "uses: ./.github/actions/setup-toolchain"
CHECKOUT_ACTION = (
    "uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
)
FORBIDDEN_CI_FRAGMENTS = (
    "runs-on: [self-hosted",
    "self-hosted, macOS",
    "/usr/sbin/taskpolicy",
    "/private/tmp/uaa-verification-execution-fence-v2",
    "github.event.pull_request.head.repo.full_name == github.repository",
    "actions/cache",
    "actions/upload-artifact",
    "actions/download-artifact",
    "pull_request_target",
    "macos-15-xlarge",
    "macos-latest-xlarge",
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


def _verify_exact_receipt_graph(workflow: str, failures: list[str]) -> None:
    pytest_shards_job = job_section(workflow, "pytest-shards")
    if not all(
        f"      - {dependency}\n" in pytest_shards_job
        for dependency in ("lint", "affected-preflight")
    ):
        failures.append("pytest shards must wait for lint and fast affected preflight")
    if "trap terminate_shard_runner EXIT INT TERM HUP" not in pytest_shards_job:
        failures.append("pytest cancellation must reach the shard runner")
    if "for _ in {1..100}" not in pytest_shards_job:
        failures.append("pytest cancellation cleanup must remain bounded")
    if 'kill -KILL "$shard_runner_pid"' not in pytest_shards_job:
        failures.append("pytest cancellation must escalate after the bounded wait")
    if "--shard-index" in pytest_shards_job or "matrix:" in pytest_shards_job:
        failures.append("pytest shards must remain one bounded installed job")
    if (
        '--verification-execution-fence-root "$RUNNER_TEMP/'
        'uaa-verification-execution-fence-v2"' not in pytest_shards_job
    ):
        failures.append(
            "pytest execution fence must use the ephemeral runner temp root"
        )

    receipt_source_jobs = tuple(
        job.job_ref for job in CI_JOB_GRAPH if job.lane_ref is not None
    )
    for job_name in receipt_source_jobs:
        section = job_section(workflow, job_name)
        if not all(
            fragment in section
            for fragment in (
                "verification-envelope:",
                "steps.canonical.outputs.verification_envelope",
                "        id: canonical\n",
                '--github-output-file "$GITHUB_OUTPUT"',
                "--visual-scope",
            )
        ):
            failures.append(
                f"{job_name} must emit one exact non-authoritative receipt envelope"
            )

    pytest_aggregate = job_section(workflow, "pytest")
    if (
        not all(
            fragment in pytest_aggregate
            for fragment in (
                "verification_github_prerequisites.py",
                "            aggregate \\\n",
                "needs.manifest-attestation.outputs.verification-envelope",
                "needs.pytest-shards.outputs.verification-envelope",
                '--github-output-file "$GITHUB_OUTPUT"',
                "    if: always()\n",
            )
        )
        or pytest_aggregate.count('--envelope "$') != 11
    ):
        failures.append("pytest aggregate must derive one exact receipt")

    control_center_job = job_section(workflow, "control-center-frontend")
    if not all(
        fragment in control_center_job
        for fragment in (
            "verification-envelope:",
            "steps.canonical.outputs.verification_envelope",
            '--verification-execution-fence-root "$RUNNER_TEMP/'
            'uaa-verification-execution-fence-v2"',
            '--github-output-file "$GITHUB_OUTPUT"',
        )
    ):
        failures.append("Control Center verification must emit one fenced receipt")

    foundation_job = job_section(workflow, "foundation-gate-report")
    if (
        not all(
            fragment in foundation_job
            for fragment in (
                "foundation-manifest",
                "verify_ci_evidence_dag.py",
                "uaa_ci_evidence_dag_gate.json",
                "Install canonical frontend runtime",
                '--dependency-envelope "$PYTEST_ENVELOPE"',
                '--dependency-envelope "$PERFORMANCE_ENVELOPE"',
                '--dependency-envelope "$VISUAL_ENVELOPE"',
                '--dependency-envelope "$DESKTOP_ENVELOPE"',
                "    if: always()\n",
            )
        )
        or foundation_job.count('--envelope "$') != 12
        or foundation_job.count('--dependency-envelope "$') != 18
    ):
        failures.append("Foundation Gate must revalidate every prerequisite receipt")


def _verify_supporting_workflows(root: Path, failures: list[str]) -> None:
    toolchain = (root / TOOLCHAIN_ACTION.relative_to(ROOT)).read_text(encoding="utf-8")
    for fragment in (
        "using: composite",
        "uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        'python-version: "3.12.10"',
        "uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020",
        'node-version: "22.23.1"',
    ):
        if fragment not in toolchain:
            failures.append("hosted toolchain action must use immutable tool revisions")
    for forbidden in ("cache:", "curl ", "wget ", "secrets."):
        if forbidden in toolchain:
            failures.append(
                "hosted toolchain action must remain cacheless and secret-free"
            )

    fork_policy = (root / FORK_POLICY_WORKFLOW.relative_to(ROOT)).read_text(
        encoding="utf-8"
    )
    required_fork_fragments = (
        "pull_request_target:",
        "permissions: {}",
        "name: fork-policy",
        FORK_POLICY_RUNNER_SELECTOR,
        "BASE_REPOSITORY: ${{ github.repository }}",
        "PR_HEAD_REPOSITORY: ${{ github.event.pull_request.head.repo.full_name }}",
        "approved GitHub-hosted read-only CI",
    )
    if any(fragment not in fork_policy for fragment in required_fork_fragments):
        failures.append("fork policy must remain metadata-only and hosted")
    for forbidden in (
        "uses:",
        "checkout",
        "github.event.pull_request.head.sha",
        "github.event.pull_request.head.ref",
        "secrets.",
        "contents:",
        "self-hosted",
    ):
        if forbidden in fork_policy:
            failures.append(
                "fork policy must not execute or check out pull request code"
            )

    supply_chain = (root / SUPPLY_CHAIN_WORKFLOW.relative_to(ROOT)).read_text(
        encoding="utf-8"
    )
    if supply_chain.count(CI_RUNNER_SELECTOR) != 4:
        failures.append("every supply-chain job must use standard hosted macOS")
    if supply_chain.count(SETUP_TOOLCHAIN_ACTION) != 4:
        failures.append("every supply-chain job must use the pinned toolchain")
    if (
        supply_chain.count(CHECKOUT_ACTION) != 4
        or supply_chain.count("uses: actions/checkout@") != 4
    ):
        failures.append("every supply-chain checkout must use the immutable revision")
    for fragment in (
        "uv sync --frozen --extra dev",
        "uv export --quiet --frozen --extra dev --no-emit-project",
        "pip-audit --strict",
        "npm audit --audit-level=high",
        "cyclonedx-py environment",
        "persist-credentials: false",
    ):
        if fragment not in supply_chain:
            failures.append("supply-chain workflow lost a mandatory frozen audit gate")
    for forbidden in (
        "self-hosted",
        "taskpolicy",
        "github.event.pull_request.head.repo.full_name == github.repository",
    ):
        if forbidden in supply_chain:
            failures.append(
                "supply-chain workflow must be safe for approved public forks"
            )

    macos_release = (root / MACOS_RELEASE_WORKFLOW.relative_to(ROOT)).read_text(
        encoding="utf-8"
    )
    for fragment in (
        CI_RUNNER_SELECTOR,
        SETUP_TOOLCHAIN_ACTION,
        CHECKOUT_ACTION,
        "permissions: {}",
        "  verify-source:",
        "      contents: read",
        "persist-credentials: false",
        "ref: ${{ github.workflow_sha }}",
        "refs/tags/${{ steps.source.outputs.tag }}",
        "Reject unsupported hosted publication",
        "inputs.publish_release == true",
        "inputs.publish_installer_bootstrap == true",
    ):
        if fragment not in macos_release:
            failures.append(
                "macOS release workflow lost a hosted verification or publication block"
            )
    if (
        macos_release.count(CHECKOUT_ACTION) != 2
        or macos_release.count("uses: actions/checkout@") != 2
    ):
        failures.append("every macOS release checkout must use the immutable revision")
    for forbidden in (
        "self-hosted",
        "taskpolicy",
        "contents: write",
        "build-and-publish",
        "GH_TOKEN",
        "github.token",
        "secrets.",
        "release create",
        "release upload",
        "if: github.event_name == 'push' || inputs.publish_release == true",
    ):
        if forbidden in macos_release:
            failures.append(
                "hosted macOS verification must not receive publication authority"
            )

    actionlint = (root / ACTIONLINT_CONFIG.relative_to(ROOT)).read_text(
        encoding="utf-8"
    )
    if "self-hosted-runner:" in actionlint or "uaa-ci" in actionlint:
        failures.append("actionlint must not retain private runner labels")


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    required_paths = (
        WORKFLOW,
        TOOLCHAIN_ACTION,
        ACTIONLINT_CONFIG,
        FORK_POLICY_WORKFLOW,
        SUPPLY_CHAIN_WORKFLOW,
        MACOS_RELEASE_WORKFLOW,
    )
    for path in required_paths:
        candidate = root / path.relative_to(ROOT)
        if not candidate.is_file():
            failures.append(
                f"missing hosted CI contract file: {candidate.relative_to(root)}"
            )
    if failures:
        return failures

    workflow = (root / WORKFLOW.relative_to(ROOT)).read_text(encoding="utf-8")
    jobs = job_names(workflow)
    if not jobs:
        failures.append("CI workflow does not define jobs")
    if workflow.count(CI_RUNNER_SELECTOR) != len(jobs):
        failures.append("every CI job must use the standard hosted macOS selector")
    if workflow.count(SETUP_TOOLCHAIN_ACTION) != len(jobs):
        failures.append("every CI job must use the pinned hosted toolchain")
    if "permissions:\n  contents: read" not in workflow:
        failures.append("CI token permissions must remain contents-read only")
    if (
        "UAA_CI_DECLARED_RUNNER_PROFILE: "
        "github-hosted-macos-15-python-3.12.10-node-22.23.1"
        not in workflow
    ):
        failures.append("CI must declare one stable hosted runner profile")
    if "cancel-in-progress: true" not in workflow:
        failures.append("CI must cancel superseded runs")
    if validate_definition():
        failures.append("canonical CI command manifest must validate")
    if (
        workflow.count("uv sync --frozen --extra dev --python python3.12")
        != len(jobs) - 1
    ):
        failures.append("every installed CI job must use the frozen uv lock")
    if "shell: /bin/bash --noprofile --norc -e -o pipefail {0}" not in workflow:
        failures.append("CI must use one bounded non-interactive shell")
    if set(jobs) != {job.job_ref for job in CI_JOB_GRAPH}:
        failures.append("CI workflow job refs must match the canonical job graph")

    for job in CI_JOB_GRAPH:
        section = job_section(workflow, job.job_ref)
        for dependency in job.needs:
            if f"      - {dependency}\n" not in section:
                failures.append(
                    f"{job.job_ref} must preserve canonical dependency {dependency}"
                )
        if job.lane_ref is not None:
            for fragment in (
                "scripts/verification/run_ci_lane.py",
                f"--lane {job.lane_ref}",
                '--sha "$UAA_CI_EXACT_SHA"',
                '--base-sha "$UAA_CI_COMPARISON_BASE_SHA"',
                '--temp-root "$RUNNER_TEMP"',
                '--summary-file "$GITHUB_STEP_SUMMARY"',
            ):
                if fragment not in section:
                    failures.append(
                        f"{job.job_ref} must invoke its canonical shared CI lane"
                    )
        if f"    timeout-minutes: {job.timeout_minutes}\n" not in section:
            failures.append(f"{job.job_ref} must have its canonical bounded timeout")

    affected_preflight = job_section(workflow, "affected-preflight")
    if not all(
        fragment in affected_preflight
        for fragment in (
            "      - manifest-attestation\n",
            "          fetch-depth: 0\n",
            "git update-ref refs/uaa-ci/base-main",
            "--lane ci-affected-preflight",
        )
    ):
        failures.append("affected preflight must bind the exact comparison base")

    checkout_count = workflow.count(CHECKOUT_ACTION)
    if checkout_count == 0:
        failures.append("CI workflow must check out the exact revision")
    if workflow.count("uses: actions/checkout@") != checkout_count:
        failures.append("every CI checkout must use the immutable revision")
    if workflow.count("persist-credentials: false") != checkout_count:
        failures.append("every checkout must avoid persisting GitHub credentials")
    if workflow.count("ref: ${{ env.UAA_CI_EXACT_SHA }}") != checkout_count:
        failures.append("every checkout must bind the explicit exact SHA")
    for fragment in FORBIDDEN_CI_FRAGMENTS:
        if fragment in workflow:
            failures.append(f"forbidden hosted CI workflow fragment: {fragment}")

    _verify_exact_receipt_graph(workflow, failures)
    _verify_supporting_workflows(root, failures)

    commands = command_registry()
    hosted_command = commands.get("command:ci.github-hosted-contract")
    if hosted_command is None or hosted_command.argv != (
        ".venv/bin/python",
        "scripts/verify_github_hosted_ci.py",
    ):
        failures.append("canonical manifest must invoke the hosted CI verifier")
    shard_argv = commands["command:pytest.sharded-suite"].argv
    if shard_argv[shard_argv.index("--shards") + 1] != str(
        CANONICAL_PYTEST_SHARD_COUNT
    ):
        failures.append("pytest must preserve the canonical logical shard count")
    if shard_argv[shard_argv.index("--max-workers") + 1] != "4":
        failures.append("pytest must preserve the four-worker budget")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: GitHub-hosted CI contract is safe and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
