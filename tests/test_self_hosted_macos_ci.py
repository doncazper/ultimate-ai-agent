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
