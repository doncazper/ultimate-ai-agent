from pathlib import Path

import scripts.verify_github_hosted_ci as verifier
from scripts.verification.ci_command_manifest import (
    CI_HOSTED_RUNNER_LABELS,
    CI_JOB_GRAPH,
    command_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_contract_files(tmp_path: Path) -> None:
    for source in (
        ".github/workflows/ci.yml",
        ".github/workflows/fork-pr-policy.yml",
        ".github/workflows/supply-chain.yml",
        ".github/workflows/macos-release.yml",
        ".github/actions/setup-toolchain/action.yml",
        ".github/actionlint.yaml",
    ):
        destination = tmp_path / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            (ROOT / source).read_text(encoding="utf-8"), encoding="utf-8"
        )


def test_current_github_hosted_ci_contract_passes() -> None:
    assert verifier.verify(ROOT) == []


def test_ci_uses_only_standard_hosted_runners() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    jobs = verifier.job_names(workflow)

    assert workflow.count("runs-on: macos-15") == len(jobs) == len(CI_JOB_GRAPH)
    assert "self-hosted" not in workflow
    assert "xlarge" not in workflow
    assert CI_HOSTED_RUNNER_LABELS == ("macos-15", "ubuntu-24.04")


def test_approved_forks_use_read_only_ephemeral_ci() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    fork_policy = (ROOT / ".github/workflows/fork-pr-policy.yml").read_text(
        encoding="utf-8"
    )

    assert "permissions:\n  contents: read" in workflow
    assert "head.repo.full_name == github.repository" not in workflow
    assert "pull_request_target" not in workflow
    assert "pull_request_target:" in fork_policy
    assert "permissions: {}" in fork_policy
    assert "runs-on: ubuntu-24.04" in fork_policy
    assert "uses:" not in fork_policy
    assert "secrets." not in fork_policy
    assert "approved GitHub-hosted read-only CI" in fork_policy


def test_hosted_toolchain_is_pinned_and_cacheless() -> None:
    action = (ROOT / ".github/actions/setup-toolchain/action.yml").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert (
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
        in action
    )
    assert 'python-version: "3.12.13"' in action
    assert "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in action
    assert 'node-version: "22.23.1"' in action
    assert "cache:" not in action
    assert (
        "UAA_CI_DECLARED_RUNNER_PROFILE: "
        "github-hosted-macos-15-python-3.12.13-node-22.23.1"
        in workflow
    )
    assert workflow.count("uses: ./.github/actions/setup-toolchain") == len(
        CI_JOB_GRAPH
    )


def test_exact_head_and_evidence_contexts_are_preserved() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    checkout_count = workflow.count("uses: actions/checkout@v4")

    assert checkout_count > 0
    assert workflow.count("persist-credentials: false") == checkout_count
    assert workflow.count("ref: ${{ env.UAA_CI_EXACT_SHA }}") == checkout_count
    assert {job.job_ref for job in CI_JOB_GRAPH} == set(verifier.job_names(workflow))
    assert (
        command_registry()["command:pytest.sharded-suite"].argv[
            command_registry()["command:pytest.sharded-suite"].argv.index(
                "--max-workers"
            )
            + 1
        ]
        == "4"
    )


def test_execution_fences_use_ephemeral_runner_storage() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert (
        workflow.count(
            '--verification-execution-fence-root "$RUNNER_TEMP/'
            'uaa-verification-execution-fence-v2"'
        )
        == 2
    )
    assert "/private/tmp/uaa-verification-execution-fence-v2" not in workflow
    assert "/usr/sbin/taskpolicy" not in workflow


def test_public_source_does_not_auto_publish_binary_releases() -> None:
    workflow = (ROOT / ".github/workflows/macos-release.yml").read_text(
        encoding="utf-8"
    )

    assert "runs-on: macos-15" in workflow
    assert "permissions: {}\n" in workflow
    assert "  verify-source:\n" in workflow
    assert "    permissions:\n      contents: read\n" in workflow
    assert "  build-and-publish:\n" in workflow
    assert "    permissions:\n      contents: write\n" in workflow
    assert "ref: ${{ github.workflow_sha }}" in workflow
    assert workflow.index("ref: ${{ github.workflow_sha }}") < workflow.index(
        "ref: refs/tags/${{ steps.source.outputs.tag }}"
    )
    assert "needs: verify-source" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
    assert (
        "if: github.event_name == 'workflow_dispatch' && inputs.publish_release == true"
        in workflow
    )
    assert (
        "if: github.event_name == 'push' || inputs.publish_release == true"
        not in workflow
    )


def test_verifier_rejects_private_runner_regression(tmp_path: Path) -> None:
    _copy_contract_files(tmp_path)
    workflow_path = tmp_path / ".github/workflows/ci.yml"
    workflow_path.write_text(
        workflow_path.read_text(encoding="utf-8").replace(
            "runs-on: macos-15",
            "runs-on: [self-hosted, macOS, ARM64, uaa-ci]",
            1,
        ),
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)
    assert "every CI job must use the standard hosted macOS selector" in failures
    assert any("forbidden hosted CI workflow fragment" in item for item in failures)


def test_verifier_rejects_fork_checkout(tmp_path: Path) -> None:
    _copy_contract_files(tmp_path)
    policy_path = tmp_path / ".github/workflows/fork-pr-policy.yml"
    policy_path.write_text(
        policy_path.read_text(encoding="utf-8")
        + "\n# checkout of pull request code is forbidden\n",
        encoding="utf-8",
    )

    assert (
        "fork policy must not execute or check out pull request code"
        in verifier.verify(tmp_path)
    )
