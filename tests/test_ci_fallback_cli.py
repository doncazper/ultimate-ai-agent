from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from scripts.ci import verify_with_fallback as cli
from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    SCHEMA_VERSION,
    definition_fingerprint,
)
from scripts.verification.ci_fallback_contracts import (
    FallbackState,
    GitHubObservation,
)


SHA = "a" * 40


def green_observation() -> GitHubObservation:
    return GitHubObservation(
        repository_sha=SHA,
        run_ref="run-ref:github:test",
        status="completed",
        conclusion="success",
        repository_command_started=True,
        reason_ref="reason-ref:github:exact-sha-green",
        manifest_version=SCHEMA_VERSION,
        manifest_fingerprint=definition_fingerprint(),
        manifest_attested=True,
        observation_source="live_github",
    )


def test_no_private_is_inspection_only_for_every_classification() -> None:
    green = cli.inspection_status(green_observation())
    assert green.state == FallbackState.GITHUB_GREEN
    assert green.merge_gate_satisfied is True
    infrastructure = cli.inspection_status(
        replace(
            green_observation(),
            status="unavailable",
            conclusion="",
            repository_command_started=False,
            reason_ref="reason-ref:github:api-unavailable",
        )
    )
    assert infrastructure.state == FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
    assert infrastructure.merge_gate_satisfied is False
    code = cli.inspection_status(
        replace(
            green_observation(),
            conclusion="failure",
            reason_ref="reason-ref:github:repository-command-failed",
        )
    )
    assert code.state == FallbackState.GITHUB_CODE_FAILURE
    assert cli.status_exit_code(green) == 0
    assert cli.status_exit_code(infrastructure) == 1
    assert cli.status_exit_code(
        replace(green, state=FallbackState.PRIVATE_GREEN_PENDING_GITHUB)
    ) == 2


def _run_payload(*, conclusion: str = "success") -> list[dict[str, object]]:
    return [
        {
            "databaseId": 123,
            "headSha": SHA,
            "status": "completed",
            "conclusion": conclusion,
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:01:00Z",
            "attempt": 1,
        }
    ]


def _green_jobs() -> dict[str, object]:
    jobs = []
    for job in CI_JOB_GRAPH:
        steps = [
            {
                "name": "Run canonical manifest attestation",
                "status": "completed",
                "conclusion": "success",
            }
        ] if job.job_ref == "manifest-attestation" else [
            {
                "name": "Run canonical lane",
                "status": "completed",
                "conclusion": "success",
            }
        ]
        jobs.append(
            {
                "name": job.display_name,
                "status": "completed",
                "conclusion": "success",
                "startedAt": "2026-01-01T00:00:00Z",
                "completedAt": "2026-01-01T00:01:00Z",
                "steps": steps,
            }
        )
    return {"jobs": jobs}


def test_live_github_green_requires_complete_attested_canonical_jobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter((_run_payload(), _green_jobs()))
    monkeypatch.setattr(cli, "_run_json", lambda *_args, **_kwargs: next(responses))
    observed = cli.observe_github(tmp_path, SHA)
    assert observed.manifest_attested is True
    assert observed.observation_source == "live_github"
    assert cli.inspection_status(observed).state == FallbackState.GITHUB_GREEN


def test_missing_github_job_evidence_fails_closed_as_code_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_run_json(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _run_payload(conclusion="failure")
        raise RuntimeError("unavailable")

    monkeypatch.setattr(cli, "_run_json", fake_run_json)
    observed = cli.observe_github(tmp_path, SHA)
    assert observed.repository_command_started is True
    assert observed.reason_ref == "reason-ref:github:job-evidence-unavailable"
    assert cli.inspection_status(observed).state == FallbackState.GITHUB_CODE_FAILURE


@pytest.mark.parametrize("job_payload", ({"jobs": []}, {"jobs": [{"name": "lint"}]}))
def test_empty_or_partial_job_evidence_cannot_claim_prestart_infrastructure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    job_payload: dict[str, object],
) -> None:
    responses = iter((_run_payload(conclusion="failure"), job_payload))
    monkeypatch.setattr(cli, "_run_json", lambda *_args, **_kwargs: next(responses))

    observed = cli.observe_github(tmp_path, SHA)

    assert observed.repository_command_started is True
    assert observed.reason_ref == "reason-ref:github:job-evidence-unavailable"
    assert cli.inspection_status(observed).state == FallbackState.GITHUB_CODE_FAILURE


def test_cross_sha_superseded_churn_is_bounded_to_the_branch_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC).replace(microsecond=0)

    def timestamp(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    current = _run_payload()[0]
    current.update(
        status="queued",
        conclusion="",
        createdAt=timestamp(now),
    )
    runs = [
        current,
        {
            **current,
            "databaseId": 122,
            "headSha": "b" * 40,
            "status": "completed",
            "conclusion": "cancelled",
            "createdAt": timestamp(now - timedelta(minutes=10)),
        },
        {
            **current,
            "databaseId": 121,
            "headSha": "c" * 40,
            "status": "completed",
            "conclusion": "cancelled",
            "createdAt": timestamp(now - timedelta(minutes=20)),
        },
    ]
    responses = iter((runs, {"jobs": []}))
    monkeypatch.setattr(cli, "_run_json", lambda *_args, **_kwargs: next(responses))

    observed = cli.observe_github(tmp_path, SHA)

    assert observed.superseded_run_count == 2
    assert cli.inspection_status(observed).state == (
        FallbackState.GITHUB_INFRASTRUCTURE_BLOCKED
    )


@pytest.mark.parametrize("run_status", ("requested", "waiting", "pending"))
def test_live_github_prequeue_statuses_are_observed_as_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_status: str,
) -> None:
    run = _run_payload()[0]
    run.update(
        status=run_status,
        conclusion="",
        createdAt=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    responses = iter(([run], {"jobs": []}))
    monkeypatch.setattr(cli, "_run_json", lambda *_args, **_kwargs: next(responses))

    observed = cli.observe_github(tmp_path, SHA)

    assert observed.status == run_status
    assert observed.reason_ref == "reason-ref:github:run-active"
    assert cli.inspection_status(observed).state == FallbackState.GITHUB_RUNNING


def test_authoritative_checkout_rejects_dirty_manifest_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_git_value", lambda *_args: " M scripts/verification/ci_command_manifest.py")

    with pytest.raises(ValueError, match="clean exact-SHA"):
        cli._require_clean_checkout(tmp_path)


def test_observation_fixture_rejects_unknown_fields(tmp_path: Path) -> None:
    fixture = tmp_path / "observation.json"
    fixture.write_text('{"repository_sha":"' + SHA + '","raw_log":"unsafe"}')
    with pytest.raises(ValueError, match="unknown fields"):
        cli._observation_from_file(fixture)


def test_observation_fixture_can_never_forge_a_green_merge_gate(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "observation.json"
    payload = {
        **green_observation().__dict__,
        "observation_source": "live_github",
        "manifest_attested": True,
    }
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    observation = cli._observation_from_file(fixture)
    status = cli.inspection_status(observation)
    assert observation.observation_source == "injected_simulation"
    assert observation.manifest_attested is False
    assert status.state == FallbackState.GITHUB_CODE_FAILURE
    assert status.merge_gate_satisfied is False


def test_controller_source_has_no_github_mutation_or_billing_commands() -> None:
    source = Path(cli.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "gh run rerun",
        "gh workflow run",
        "gh run cancel",
        "gh pr merge",
        "git push",
        "billing",
        "spending-limit",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "argv",
    (
        ("--sha", SHA, "--mode", "status", "--diagnose-pytest-shard", "2"),
        ("--sha", SHA, "--no-private", "--diagnose-pytest-shard", "2"),
        (
            "--sha",
            SHA,
            "--diagnose-pytest-shard",
            "2",
            "--diagnose-pytest-shard",
            "2",
        ),
    ),
)
def test_cli_rejects_non_active_or_duplicate_private_shard_diagnosis(
    argv: tuple[str, ...],
) -> None:
    with pytest.raises(SystemExit):
        cli.main(list(argv))


def test_cli_forwards_explicit_private_shard_diagnosis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    failed = replace(
        green_observation(),
        conclusion="failure",
        reason_ref="reason-ref:github:repository-command-failed",
    )

    class FakeController:
        def evaluate(self, observation, *, series_ref, diagnostic_unit_refs):
            captured.update(
                observation=observation,
                series_ref=series_ref,
                diagnostics=diagnostic_unit_refs,
            )
            return cli.inspection_status(observation)

    monkeypatch.setattr(
        cli,
        "_git_value",
        lambda _repo, *args: SHA if args == ("rev-parse", "HEAD") else "",
    )
    monkeypatch.setattr(cli, "_require_clean_checkout", lambda _repo: None)
    monkeypatch.setattr(cli, "_ledger_directory", lambda _repo: tmp_path / "ledger")
    monkeypatch.setattr(cli, "_series_ref", lambda _repo: "series-ref:ci:test")
    monkeypatch.setattr(cli, "AttemptLedger", lambda _path: object())
    monkeypatch.setattr(cli, "IsolatedPrivateExecutor", lambda _repo: object())
    monkeypatch.setattr(cli, "FallbackController", lambda *_args: FakeController())
    monkeypatch.setattr(cli, "observe_github", lambda _repo, _sha: failed)

    exit_code = cli.main(
        [
            "--repo",
            str(tmp_path),
            "--sha",
            SHA,
            "--diagnose-pytest-shard",
            "5",
            "--json",
        ]
    )

    assert exit_code == 1
    assert captured["diagnostics"] == ("diagnostic-pytest-shard-5",)


def test_cli_redacts_unexpected_controller_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FailingController:
        def evaluate(self, *_args, **_kwargs):
            raise RuntimeError("executor failure at /private/secret/path")

    monkeypatch.setattr(
        cli,
        "_git_value",
        lambda _repo, *args: SHA if args == ("rev-parse", "HEAD") else "",
    )
    monkeypatch.setattr(cli, "_require_clean_checkout", lambda _repo: None)
    monkeypatch.setattr(cli, "_ledger_directory", lambda _repo: tmp_path / "ledger")
    monkeypatch.setattr(cli, "_series_ref", lambda _repo: "series-ref:ci:test")
    monkeypatch.setattr(cli, "AttemptLedger", lambda _path: object())
    monkeypatch.setattr(cli, "IsolatedPrivateExecutor", lambda _repo: object())
    monkeypatch.setattr(cli, "FallbackController", lambda *_args: FailingController())
    monkeypatch.setattr(cli, "observe_github", lambda _repo, _sha: green_observation())

    exit_code = cli.main(["--repo", str(tmp_path), "--sha", SHA])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == (
        "Private CI stopped: reason-ref:private-ci:controller-failure\n"
    )
    assert "/private/secret/path" not in captured.err
    assert "Traceback" not in captured.err
