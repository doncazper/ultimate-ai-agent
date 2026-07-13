from pathlib import Path

import scripts.verify_self_hosted_macos_ci as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_current_self_hosted_macos_ci_contract_passes() -> None:
    assert verifier.verify(ROOT) == []


def test_provisioner_keeps_root_owned_helper_directory_traversable() -> None:
    provisioner = (
        ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
    ).read_text(encoding="utf-8")

    assert "install -d -o root -g wheel -m 0755 /usr/local/libexec\n" in provisioner
    assert "install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci" in provisioner
    assert "mkdir -p /usr/local/libexec/uaa-ci" not in provisioner


def test_workflow_uses_non_admin_preprovisioned_toolchains() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "actions/setup-python" not in workflow
    assert "actions/setup-node" not in workflow
    assert "python3.12 -m venv .venv" in workflow
    assert "/opt/homebrew/opt/python@3.12/libexec/bin" in workflow
    assert "/opt/homebrew/opt/node@22/bin" in workflow


def test_pytest_shards_use_runner_scoped_temp_directory() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert '--basetemp "${RUNNER_TEMP}/uaa_pytest_shards"' in workflow
    assert (
        '--performance-report "${RUNNER_TEMP}/uaa_pytest_performance_report.json"'
        in workflow
    )
    assert "--basetemp /tmp/uaa_pytest_shards" not in workflow
    assert "--stretch-goal-seconds 180" in workflow
    assert "--target-seconds 240" in workflow
    assert "--hard-timeout-seconds 300" in workflow


def test_desktop_packaging_preserves_non_admin_docker_boundary() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "docker info >/dev/null 2>&1" in workflow
    assert "steps.docker.outputs.available == 'true'" in workflow
    assert "reason-ref:self-hosted-runner-docker-unavailable" in workflow
    assert 'run_lane_command "command:desktop-packaging.contract"' in workflow


def test_verifier_rejects_hosted_runner_and_cache_regression(tmp_path: Path) -> None:
    workflow = tmp_path / ".github/workflows/ci.yml"
    actionlint_config = tmp_path / ".github/actionlint.yaml"
    provisioner = tmp_path / "scripts/ci/provision_self_hosted_macos_runners.sh"
    bootstrap = tmp_path / "scripts/ci/bootstrap_self_hosted_macos_runner.sh"
    workflow.parent.mkdir(parents=True)
    provisioner.parent.mkdir(parents=True)
    workflow.write_text(
        "name: unsafe\njobs:\n  unsafe:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/cache@v4\n",
        encoding="utf-8",
    )
    actionlint_config.write_text(
        "self-hosted-runner:\n  labels:\n    - uaa-ci\n",
        encoding="utf-8",
    )
    provisioner.write_text("unsafe", encoding="utf-8")
    bootstrap.write_text("unsafe", encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any("exact UAA self-hosted macOS selector" in failure for failure in failures)
    assert any("fork pull requests" in failure for failure in failures)
    assert any("forbidden self-hosted CI workflow fragment: ubuntu-latest" in failure for failure in failures)
    assert any("forbidden self-hosted CI workflow fragment: actions/cache" in failure for failure in failures)
