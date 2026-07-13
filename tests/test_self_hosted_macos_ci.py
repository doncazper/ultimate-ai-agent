from pathlib import Path

import scripts.verify_self_hosted_macos_ci as verifier
from scripts.verification.ci_command_manifest import command_registry, lane_registry


ROOT = Path(__file__).resolve().parents[1]


def test_current_self_hosted_macos_ci_contract_passes() -> None:
    assert verifier.verify(ROOT) == []


def test_provisioner_keeps_root_owned_helper_directory_traversable() -> None:
    provisioner = (
        ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
    ).read_text(encoding="utf-8")

    assert "install -d -o root -g wheel -m 0755 /usr/local/libexec\n" in provisioner
    assert (
        "install -d -o root -g wheel -m 0755 /usr/local/libexec/uaa-ci" in provisioner
    )
    assert "mkdir -p /usr/local/libexec/uaa-ci" not in provisioner


def test_provisioner_retries_transient_launchd_bootstrap_failure() -> None:
    provisioner = (
        ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
    ).read_text(encoding="utf-8")

    assert "launchd did not settle after bootout" in provisioner
    assert "/bin/sleep 2" in provisioner
    assert provisioner.count('launchctl bootstrap system "$service_path"') == 2
    assert 'launchctl print "system/${service_label}"' in provisioner


def test_provisioner_uses_standard_not_interactive_runner_scheduling() -> None:
    provisioner = (
        ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
    ).read_text(encoding="utf-8")

    assert "<key>ProcessType</key>\n  <string>Standard</string>" in provisioner
    assert "<string>Background</string>" not in provisioner
    assert "<string>Interactive</string>" not in provisioner


def test_workflow_uses_non_admin_preprovisioned_toolchains() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "actions/setup-python" not in workflow
    assert "actions/setup-node" not in workflow
    assert "python3.12 -m venv .venv" in workflow
    assert "/opt/homebrew/opt/python@3.12/libexec/bin" in workflow
    assert "/opt/homebrew/opt/node@22/bin" in workflow
    assert "shell: /usr/sbin/taskpolicy -c utility /bin/bash --noprofile --norc -e -o pipefail {0}" in workflow
    assert "shell: bash" not in workflow


def test_base_controlled_workflow_rejects_forks_without_checkout() -> None:
    policy = (
        ROOT / ".github/workflows/fork-pr-policy.yml"
    ).read_text(encoding="utf-8")

    assert "pull_request_target:" in policy
    assert "permissions: {}" in policy
    assert "EXPECTED_REPOSITORY: ${{ github.repository }}" in policy
    assert (
        "PR_HEAD_REPOSITORY: ${{ github.event.pull_request.head.repo.full_name }}"
        in policy
    )
    assert 'if [ "$PR_HEAD_REPOSITORY" != "$EXPECTED_REPOSITORY" ]; then' in policy
    assert "uses:" not in policy
    assert "checkout" not in policy
    assert "secrets." not in policy


def test_runner_bootstrap_keeps_tokens_out_of_argv_and_rejects_stale_state() -> None:
    provisioner = (
        ROOT / "scripts/ci/provision_self_hosted_macos_runners.sh"
    ).read_text(encoding="utf-8")
    bootstrap = (
        ROOT / "scripts/ci/bootstrap_self_hosted_macos_runner.sh"
    ).read_text(encoding="utf-8")

    assert 'remote_registration_state="registered"' in provisioner
    assert 'remote_registration_state="absent"' in provisioner
    assert 'ACTIONS_RUNNER_INPUT_TOKEN="$registration_token" ./config.sh' in bootstrap
    assert '--token "$registration_token"' not in bootstrap
    assert "local runner registration is stale" in bootstrap
    assert "regular non-symlink file" in bootstrap
    assert 'settings.get("agentName")' in bootstrap
    assert 'settings.get("gitHubUrl"' in bootstrap
    assert 'settings.get("workFolder")' in bootstrap


def test_pytest_shards_use_runner_scoped_temp_directory() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    argv = command_registry()["command:pytest.sharded-suite"].argv

    assert "{temp_root}/uaa_pytest_shards" in argv
    assert "{temp_root}/uaa_pytest_performance_report.json" in argv
    assert argv[argv.index("--stretch-goal-seconds") + 1] == "900"
    assert argv[argv.index("--target-seconds") + 1] == "1200"
    assert argv[argv.index("--hard-timeout-seconds") + 1] == "1800"
    assert '--temp-root "$RUNNER_TEMP"' in workflow


def test_static_verification_uses_runner_scoped_timing_output() -> None:
    argv = command_registry()["command:static.verify-all"].argv
    assert "{temp_root}/uaa_static_verification_timings.json" in argv


def test_release_lanes_capture_failures_and_isolate_performance_measurement() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "run_lane_command()" not in workflow
    assert "scripts/verification/run_ci_lane.py" in workflow
    performance_job = workflow.split("  release-lane-performance:\n", 1)[1].split(
        "\n  release-lane-visual-regression:", 1
    )[0]
    assert "    needs:\n" in performance_job
    assert "      - pytest\n" in performance_job
    assert "      - static-verification\n" in performance_job
    assert "      - control-center-frontend\n" in performance_job


def test_shared_mac_ci_stages_cpu_and_io_heavy_job_classes() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    pytest_shards_job = verifier.job_section(workflow, "pytest-shards")
    assert "      - lint\n" in pytest_shards_job
    assert "      - affected-preflight\n" in pytest_shards_job
    affected_preflight_job = verifier.job_section(workflow, "affected-preflight")
    assert "      - manifest-attestation\n" in affected_preflight_job
    assert "          fetch-depth: 0\n" in affected_preflight_job
    assert "git update-ref refs/uaa-ci/base-main" in affected_preflight_job
    assert "--lane ci-affected-preflight" in affected_preflight_job
    assert command_registry()["command:affected.preflight"].argv[-2:] == (
        "--tier",
        "fast",
    )
    assert command_registry()["command:pytest.sharded-suite"].argv[
        command_registry()["command:pytest.sharded-suite"].argv.index("--max-workers")
        + 1
    ] == "4"
    assert "/usr/sbin/taskpolicy -c utility .venv/bin/python scripts/verification/run_ci_lane.py" in pytest_shards_job
    assert "trap terminate_shard_runner EXIT INT TERM HUP" in pytest_shards_job
    assert 'kill -TERM "$shard_runner_pid"' in pytest_shards_job
    assert "for _ in {1..100}" in pytest_shards_job
    assert 'kill -KILL "$shard_runner_pid"' in pytest_shards_job
    assert "--shard-index" not in pytest_shards_job
    assert "matrix:" not in pytest_shards_job
    for job_name in (
        "static-verification",
        "release-lane-docs",
        "release-lane-openapi",
        "release-lane-api-safety",
        "release-lane-security-redaction",
        "release-lane-product-truth",
        "release-lane-local-model-e2e",
        "release-lane-durability",
        "release-lane-desktop-packaging",
    ):
        assert "      - pytest\n" in verifier.job_section(workflow, job_name)

    control_center_job = verifier.job_section(workflow, "control-center-frontend")
    assert "      - static-verification\n" in control_center_job
    assert "      - release-lane-desktop-packaging\n" in control_center_job
    assert "      - control-center-frontend\n" in verifier.job_section(
        workflow, "release-lane-visual-regression"
    )


def test_visual_regression_runs_only_for_affected_control_center_paths() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    visual_job = verifier.job_section(workflow, "release-lane-visual-regression")

    assert "          fetch-depth: 0\n" in visual_job
    assert "PULL_REQUEST_BASE_SHA: ${{ github.event.pull_request.base.sha }}" in visual_job
    assert "PUSH_BEFORE_SHA: ${{ github.event.before }}" in visual_job
    assert 'if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then' in visual_job
    assert 'git cat-file -e "${range_base}^{commit}"' in visual_job
    assert 'git diff --no-renames --quiet "$range_base" "$RANGE_HEAD_SHA" --' in visual_job
    for path in (
        "apps/control-center",
        "docs/control_center",
        "docs/design/control_center_north_star",
        "docs/schemas/control_center_release_surface.schema.json",
        "scripts/verify_beta_local.py",
        "scripts/verify_beta_13_frontend_loading_visual_proof.py",
        "scripts/verify_control_center_visual_regression.py",
        "scripts/verify_control_center_release_surface.py",
        "scripts/verify_fcc_polish_001_native_apple_grade_ux_layer.py",
        "tests/test_control_center_release_surface_manifest.py",
        "tests/test_control_center_visual_and_packaging_proofs.py",
        "tests/test_fcc_polish_001_native_apple_grade_ux_layer.py",
    ):
        assert path in visual_job
    assert visual_job.count(
        "if: steps.visual-scope.outputs.run_visual == 'true'"
    ) == 2
    assert 'if [ "$RUN_VISUAL" = "true" ]; then' in visual_job
    assert "reason-ref:visual-regression:not-affected" in visual_job
    assert (
        "PLAYWRIGHT_BROWSERS_PATH: ${{ runner.temp }}/playwright-browsers"
        in visual_job
    )
    assert (
        "--lane visual-regression"
        in visual_job
    )
    assert "command:frontend.visual-regression-contract" in lane_registry()[
        "visual-regression"
    ].command_refs


def test_checkout_matches_repository_actions_allow_policy() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    checkout_action = "uses: actions/checkout@v4"
    assert workflow.count(checkout_action) == workflow.count(
        "persist-credentials: false"
    )


def test_desktop_packaging_preserves_non_admin_docker_boundary() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "docker info >/dev/null 2>&1" in workflow
    assert "steps.docker.outputs.available == 'true'" in workflow
    desktop_job = verifier.job_section(workflow, "release-lane-desktop-packaging")
    assert (
        "PLAYWRIGHT_BROWSERS_PATH: ${{ runner.temp }}/playwright-browsers"
        in desktop_job
    )
    assert '--docker-available "$docker_posture"' in workflow
    assert "command:desktop-packaging.contract" in lane_registry()[
        "desktop-packaging"
    ].command_refs


def test_verifier_rejects_hosted_runner_and_cache_regression(tmp_path: Path) -> None:
    workflow = tmp_path / ".github/workflows/ci.yml"
    fork_policy = tmp_path / ".github/workflows/fork-pr-policy.yml"
    actionlint_config = tmp_path / ".github/actionlint.yaml"
    provisioner = tmp_path / "scripts/ci/provision_self_hosted_macos_runners.sh"
    bootstrap = tmp_path / "scripts/ci/bootstrap_self_hosted_macos_runner.sh"
    workflow.parent.mkdir(parents=True)
    provisioner.parent.mkdir(parents=True)
    workflow.write_text(
        "name: unsafe\njobs:\n  unsafe:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/cache@v4\n",
        encoding="utf-8",
    )
    fork_policy.write_text("name: unsafe fork policy\n", encoding="utf-8")
    actionlint_config.write_text(
        "self-hosted-runner:\n  labels:\n    - uaa-ci\n",
        encoding="utf-8",
    )
    provisioner.write_text("unsafe", encoding="utf-8")
    bootstrap.write_text("unsafe", encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any(
        "exact UAA self-hosted macOS selector" in failure for failure in failures
    )
    assert any("fork pull requests" in failure for failure in failures)
    assert any(
        "forbidden self-hosted CI workflow fragment: ubuntu-latest" in failure
        for failure in failures
    )
    assert any(
        "forbidden self-hosted CI workflow fragment: actions/cache" in failure
        for failure in failures
    )
