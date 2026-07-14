from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.verification.ci_command_manifest import (
    CI_JOB_GRAPH,
    PLAYWRIGHT_BROWSER_DIRNAME,
    PRIVATE_BASE_REF,
    PROFILE_REF,
    VerificationPlan,
    build_plan,
    command_registry,
    lane_registry,
    visual_scope_for_paths,
)
from scripts.verification.ci_fallback_contracts import (
    SAFE_REF_PATTERN,
    SHA_PATTERN,
    PrivateVerificationResult,
    has_valid_command_result_evidence,
    has_valid_timing_window,
)
from scripts.verification.pytest_shard_processes import (
    cancellation_signals,
    installed_signal_handlers,
    stop_processes,
)
from scripts.verification.run_ci_lane import expected_pytest_shard_plan_ref


def _safe_subprocess(
    argv: tuple[str, ...],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> tuple[int, int, str]:
    started = time.perf_counter()
    process: subprocess.Popen[bytes] | None = None

    def handle_signal(signum: int, _frame: object) -> None:
        if process is not None:
            stop_processes((process,), 10.0)
        raise KeyboardInterrupt(f"private CI process interrupted by signal {signum}")

    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=os.name == "posix",
    )
    try:
        with installed_signal_handlers(cancellation_signals(), handle_signal):
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                stop_processes((process,), 10.0)
                returncode = 124
    except KeyboardInterrupt:
        stop_processes((process,), 10.0)
        returncode = 130
    duration_ms = max(0, int((time.perf_counter() - started) * 1000))
    result_ref = (
        "result-ref:ci:"
        + hashlib.sha256(
            ("|".join(argv) + f"|{returncode}|{duration_ms}").encode()
        ).hexdigest()
    )
    return returncode, duration_ms, result_ref


def _minimal_env(temp_root: Path) -> dict[str, str]:
    home = temp_root / "home"
    runtime_tmp = temp_root / "tmp"
    playwright_browsers = temp_root / "lane-temp" / PLAYWRIGHT_BROWSER_DIRNAME
    home.mkdir(parents=True, exist_ok=True)
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    playwright_browsers.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": "/opt/homebrew/opt/python@3.12/libexec/bin:/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home),
        "TEMP": str(runtime_tmp),
        "TMP": str(runtime_tmp),
        "TMPDIR": str(runtime_tmp),
        "CI": "true",
        "LANG": "C.UTF-8",
        "PLAYWRIGHT_BROWSERS_PATH": str(playwright_browsers),
    }


def _read_lane_receipt(
    path: Path,
    *,
    lane_ref: str,
    expected_plan: VerificationPlan,
) -> str:
    repository_sha = expected_plan.repository_sha
    descriptor = -1
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
            or info.st_size > 1024 * 1024
        ):
            raise ValueError("private CI lane receipt is unsafe")
        raw = os.read(descriptor, 1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("private CI lane receipt exceeds its byte bound")
        payload = json.loads(raw.decode("utf-8"))
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        path.unlink(missing_ok=True)
    allowed_receipt_fields = {
        "schema_version",
        "profile_ref",
        "repository_sha",
        "lane_ref",
        "plan",
        "started_at",
        "completed_at",
        "duration_ms",
        "status",
        "command_results",
        "github_gate_satisfied",
        "merge_gate_satisfied",
        "redaction_status",
        "receipt_ref",
    }
    lane = lane_registry()[lane_ref]
    plan = payload.get("plan") if isinstance(payload, dict) else None
    if not isinstance(plan, dict):
        raise ValueError("private CI lane receipt does not contain a plan")
    command_results = payload.get("command_results")
    if not isinstance(command_results, list) or [
        result.get("command_ref") if isinstance(result, dict) else None
        for result in command_results
    ] != list(lane.command_refs):
        raise ValueError("private CI lane receipt command membership is invalid")
    expected_pytest_plan_ref = expected_pytest_shard_plan_ref()
    if any(
        not has_valid_command_result_evidence(
            result,
            lane_ref=lane_ref,
            repository_sha=repository_sha,
            expected_category=command_registry()[result["command_ref"]].category,
            expected_pytest_plan_ref=expected_pytest_plan_ref,
            satisfied_by_dependency=(
                result["command_ref"] in lane.satisfied_command_refs
            ),
        )
        for result in command_results
    ):
        raise ValueError("private CI lane receipt command evidence is unsafe")
    if (
        not isinstance(payload, dict)
        or set(payload) != allowed_receipt_fields
        or payload.get("schema_version") != "uaa_ci_lane_receipt.v1"
        or payload.get("profile_ref") != PROFILE_REF
        or payload.get("repository_sha") != repository_sha
        or payload.get("lane_ref") != lane_ref
        or payload.get("status") != "pass"
        or payload.get("github_gate_satisfied") is not False
        or payload.get("merge_gate_satisfied") is not False
        or payload.get("redaction_status")
        != "content_free_refs_hashes_counts_and_durations_only"
        or not has_valid_timing_window(
            payload.get("started_at"),
            payload.get("completed_at"),
            payload.get("duration_ms"),
        )
        or plan != json.loads(json.dumps(asdict(expected_plan)))
    ):
        raise ValueError("private CI lane receipt does not match its exact plan")
    receipt_ref = payload.get("receipt_ref")
    expected_receipt_ref = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(
                {key: value for key, value in payload.items() if key != "receipt_ref"},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    )
    if (
        not isinstance(receipt_ref, str)
        or not SAFE_REF_PATTERN.fullmatch(receipt_ref)
        or receipt_ref != expected_receipt_ref
    ):
        raise ValueError("private CI lane receipt ref is unsafe")
    return receipt_ref


_JOB_LANES = (job.lane_ref for job in CI_JOB_GRAPH if job.lane_ref)
PRIVATE_LANE_REFS = tuple(dict.fromkeys(("ci-affected-preflight", *_JOB_LANES)))
ALLOWED_ORIGIN_URLS = frozenset(
    {
        "git@github.com:doncazper/ultimate-ai-agent.git",
        "https://github.com/doncazper/ultimate-ai-agent.git",
        "ssh://git@github.com/doncazper/ultimate-ai-agent.git",
    }
)


def private_verification_plan(repo: Path, repository_sha: str) -> VerificationPlan:
    return build_plan(repo, repository_sha, lane_refs=PRIVATE_LANE_REFS)


class IsolatedPrivateExecutor:
    def __init__(self, repo: Path) -> None:
        if repo.is_symlink() or not repo.is_dir():
            raise ValueError("private CI repository path is unsafe")
        self.repo = repo.resolve()

    def plan_fingerprint(self, repository_sha: str) -> str:
        return private_verification_plan(self.repo, repository_sha).plan_fingerprint

    def _git(self, *args: str, timeout: int = 30) -> str:
        completed = subprocess.run(
            ("git", *args),
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return completed.stdout.strip()

    def _preflight(self, repository_sha: str) -> str:
        if not SHA_PATTERN.fullmatch(repository_sha):
            raise ValueError("private CI requires an exact lowercase SHA")
        if self._git("rev-parse", "HEAD") != repository_sha:
            raise ValueError("private CI source worktree must be on the exact SHA")
        if self._git("status", "--porcelain"):
            raise ValueError("private CI source worktree must be clean")
        if self._git("remote", "get-url", "origin") not in ALLOWED_ORIGIN_URLS:
            raise ValueError("private CI origin is not the canonical UAA repository")
        remote_contains = self._git("branch", "-r", "--contains", repository_sha)
        if not any(
            line.strip().startswith("origin/") for line in remote_contains.splitlines()
        ):
            raise ValueError("private CI exact SHA must already be pushed to origin")
        origin_main_sha = self._git("rev-parse", "refs/remotes/origin/main")
        if not SHA_PATTERN.fullmatch(origin_main_sha):
            raise ValueError("private CI origin/main ref is invalid")
        private_verification_plan(self.repo, repository_sha)
        return origin_main_sha

    def verify(
        self, repository_sha: str, *, series_ref: str
    ) -> PrivateVerificationResult:
        del series_ref
        origin_main_sha = self._preflight(repository_sha)
        started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        root = Path(tempfile.mkdtemp(prefix="uaa-private-ci-"))
        worktree = root / "worktree"
        timings: list[tuple[str, int]] = []
        result_refs: list[str] = []
        status_value = "recovery_required"
        isolated_plan: VerificationPlan | None = None
        try:
            status_value, isolated_plan = self._verify_isolated(
                repository_sha,
                origin_main_sha,
                root,
                worktree,
                timings,
                result_refs,
            )
        finally:
            status_value = self._remove_owned_worktree(worktree, root, status_value)

        if isolated_plan is None:
            raise RuntimeError("private CI did not prepare an isolated plan")
        receipt_payload = {
            "repository_sha": repository_sha,
            "plan_fingerprint": isolated_plan.plan_fingerprint,
            "status": status_value,
            "command_result_refs": tuple(result_refs),
            "timings_ms": tuple(timings),
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        receipt_ref = (
            "receipt-ref:private-ci:"
            + hashlib.sha256(
                json.dumps(
                    receipt_payload, sort_keys=True, separators=(",", ":")
                ).encode()
            ).hexdigest()
        )
        result = PrivateVerificationResult(**receipt_payload, receipt_ref=receipt_ref)
        result.validate()
        return result

    def _verify_isolated(
        self,
        repository_sha: str,
        origin_main_sha: str,
        root: Path,
        worktree: Path,
        timings: list[tuple[str, int]],
        result_refs: list[str],
    ) -> tuple[str, VerificationPlan]:
        returncode, duration_ms, result_ref = _safe_subprocess(
            (
                "git",
                "clone",
                "--no-local",
                "--no-checkout",
                "--config",
                "core.hooksPath=/dev/null",
                str(self.repo),
                str(worktree),
            ),
            cwd=self.repo,
            timeout=60,
        )
        if returncode != 0:
            raise RuntimeError("private CI standalone clone creation failed")
        timings.append(("phase-ref:private-ci:worktree", duration_ms))
        result_refs.append(result_ref)
        for argv in (
            ("git", "checkout", "--detach", repository_sha),
            (
                "git",
                "update-ref",
                PRIVATE_BASE_REF,
                origin_main_sha,
            ),
            ("git", "remote", "remove", "origin"),
        ):
            returncode, duration_ms, result_ref = _safe_subprocess(
                argv, cwd=worktree, timeout=60
            )
            timings.append(("phase-ref:private-ci:clone-isolation", duration_ms))
            result_refs.append(result_ref)
            if returncode != 0:
                raise RuntimeError("private CI standalone clone isolation failed")
        self._validate_worktree(worktree, repository_sha)
        isolated_plan = private_verification_plan(worktree, repository_sha)
        if isolated_plan.plan_fingerprint != self.plan_fingerprint(repository_sha):
            raise ValueError("private CI isolated plan differs from prepared plan")
        env = _minimal_env(root)
        setup_commands = (
            ("python3.12", "-m", "venv", ".venv"),
            (".venv/bin/python", "-m", "pip", "install", "--upgrade", "pip"),
            (".venv/bin/python", "-m", "pip", "install", "-e", ".[dev]"),
        )
        for index, argv in enumerate(setup_commands, start=1):
            returncode, duration_ms, result_ref = _safe_subprocess(
                argv, cwd=worktree, timeout=900, env=env
            )
            timings.append((f"phase-ref:private-ci:install-{index}", duration_ms))
            result_refs.append(result_ref)
            if returncode != 0:
                return "fail", isolated_plan
        return (
            self._run_graph(
                repository_sha,
                root,
                worktree,
                env,
                timings,
                result_refs,
                isolated_plan,
            ),
            isolated_plan,
        )

    @staticmethod
    def _validate_worktree(worktree: Path, repository_sha: str) -> None:
        if worktree.is_symlink() or not worktree.is_dir():
            raise ValueError("private CI worktree is unsafe")
        for ref in (
            "pyproject.toml",
            "uv.lock",
            "apps/control-center/package-lock.json",
            "scripts/verification/run_ci_lane.py",
        ):
            candidate = worktree / ref
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError("private CI selected repository path is unsafe")
        for command in command_registry().values():
            for token in command.argv:
                if not token.startswith(("scripts/", "tests/", "apps/", "docs/")):
                    continue
                if "{temp_root}" in token:
                    continue
                candidate = worktree / token
                if candidate.is_symlink() or not candidate.is_file():
                    raise ValueError("private CI command repository path is unsafe")
        tracked = subprocess.run(
            ("git", "ls-files", "-z"),
            cwd=worktree,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout.split(b"\0")
        for raw_ref in tracked:
            if not raw_ref:
                continue
            try:
                ref = raw_ref.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("private CI tracked path is unsafe") from exc
            candidate = worktree / ref
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise ValueError("private CI tracked path is not a regular file")
        head = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if head != repository_sha:
            raise ValueError("private CI isolated worktree SHA changed")
        base = subprocess.run(
            ("git", "rev-parse", PRIVATE_BASE_REF),
            cwd=worktree,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if not SHA_PATTERN.fullmatch(base):
            raise ValueError("private CI base ref is invalid")
        ancestor = subprocess.run(
            ("git", "merge-base", "--is-ancestor", base, repository_sha),
            cwd=worktree,
            check=False,
            capture_output=True,
            timeout=10,
        )
        if ancestor.returncode != 0:
            raise ValueError("private CI base ref is not an ancestor of the exact SHA")

    @staticmethod
    def _run_lane(
        lane_ref: str,
        *,
        repository_sha: str,
        root: Path,
        worktree: Path,
        env: dict[str, str],
        visual_scope: str,
        docker_available: str,
        timings: list[tuple[str, int]],
        result_refs: list[str],
        full_suite_lock_mode: str | None = None,
    ) -> bool:
        expected_plan = build_plan(
            worktree,
            repository_sha,
            lane_refs=(lane_ref,),
            frontend_visual_scope=visual_scope,
        )
        receipt_path = root / "lane-receipts" / f"{lane_ref}.json"
        lane_command = (
            ".venv/bin/python",
            "scripts/verification/run_ci_lane.py",
            "--lane",
            lane_ref,
            "--sha",
            repository_sha,
            "--profile",
            PROFILE_REF,
            "--temp-root",
            str(root / "lane-temp"),
            "--visual-scope",
            visual_scope,
            "--docker-available",
            docker_available,
            "--receipt-file",
            str(receipt_path),
        )
        if full_suite_lock_mode is not None:
            lane_command += ("--full-suite-lock-mode", full_suite_lock_mode)
        returncode, duration_ms, _wrapper_ref = _safe_subprocess(
            lane_command, cwd=worktree, timeout=2100, env=env
        )
        timings.append((f"lane-ref:{lane_ref}", duration_ms))
        if returncode != 0:
            receipt_path.unlink(missing_ok=True)
            return False
        result_refs.append(
            _read_lane_receipt(
                receipt_path,
                lane_ref=lane_ref,
                expected_plan=expected_plan,
            )
        )
        return True

    @staticmethod
    def _run_graph(
        repository_sha: str,
        root: Path,
        worktree: Path,
        env: dict[str, str],
        timings: list[tuple[str, int]],
        result_refs: list[str],
        isolated_plan: VerificationPlan,
    ) -> str:
        npm_ready = False
        if IsolatedPrivateExecutor._affected_preflight_requires_frontend(worktree):
            returncode, duration_ms, result_ref = _safe_subprocess(
                ("npm", "ci"),
                cwd=worktree / "apps/control-center",
                timeout=900,
                env=env,
            )
            timings.append(("phase-ref:private-ci:frontend-install", duration_ms))
            result_refs.append(result_ref)
            npm_ready = returncode == 0
            if not npm_ready:
                return "fail"
        if not IsolatedPrivateExecutor._run_lane(
            "ci-affected-preflight",
            repository_sha=repository_sha,
            root=root,
            worktree=worktree,
            env=env,
            visual_scope="unknown_fail_closed",
            docker_available="unknown_fail_closed",
            timings=timings,
            result_refs=result_refs,
        ):
            return "fail"
        visual_scope = visual_scope_for_paths(None)
        docker_available = "unavailable"
        if shutil.which("docker", path=env["PATH"]):
            returncode, duration_ms, result_ref = _safe_subprocess(
                ("docker", "info"), cwd=worktree, timeout=30, env=env
            )
            timings.append(("phase-ref:private-ci:docker-probe", duration_ms))
            result_refs.append(result_ref)
            if returncode == 0:
                docker_available = "available"
        playwright_ready = False
        for job in CI_JOB_GRAPH:
            if job.lane_ref is None or job.lane_ref == "ci-affected-preflight":
                continue
            needs_frontend = job.lane_ref in {
                "ci-control-center-frontend",
                "frontend",
                "visual-regression",
            } or (
                job.lane_ref == "desktop-packaging" and docker_available == "available"
            )
            if needs_frontend and not npm_ready:
                returncode, duration_ms, result_ref = _safe_subprocess(
                    ("npm", "ci"),
                    cwd=worktree / "apps/control-center",
                    timeout=900,
                    env=env,
                )
                timings.append(("phase-ref:private-ci:frontend-install", duration_ms))
                result_refs.append(result_ref)
                npm_ready = returncode == 0
                if not npm_ready:
                    return "fail"
            playwright_argv: tuple[str, ...] | None = None
            if job.lane_ref == "visual-regression" and not playwright_ready:
                playwright_argv = ("npx", "playwright", "install", "chromium")
            elif (
                job.lane_ref == "desktop-packaging"
                and docker_available == "available"
                and not playwright_ready
            ):
                playwright_argv = (
                    "npx",
                    "playwright",
                    "install",
                    "--with-deps",
                    "chromium",
                )
            if playwright_argv is not None:
                returncode, duration_ms, result_ref = _safe_subprocess(
                    playwright_argv,
                    cwd=worktree / "apps/control-center",
                    timeout=900,
                    env=env,
                )
                timings.append(("phase-ref:private-ci:playwright-install", duration_ms))
                result_refs.append(result_ref)
                playwright_ready = returncode == 0
                if not playwright_ready:
                    return "fail"
            if not IsolatedPrivateExecutor._run_lane(
                job.lane_ref,
                repository_sha=repository_sha,
                root=root,
                worktree=worktree,
                env=env,
                visual_scope=visual_scope,
                docker_available=docker_available,
                timings=timings,
                result_refs=result_refs,
                full_suite_lock_mode=(
                    "private" if job.lane_ref == "ci-pytest-shards" else None
                ),
            ):
                return "fail"
        return "pass"

    @staticmethod
    def _affected_preflight_requires_frontend(worktree: Path) -> bool:
        completed = subprocess.run(
            (
                "git",
                "diff",
                "--no-renames",
                "--quiet",
                f"{PRIVATE_BASE_REF}...HEAD",
                "--",
                "apps/control-center",
            ),
            cwd=worktree,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )
        return completed.returncode != 0

    def _remove_owned_worktree(
        self,
        worktree: Path,
        root: Path,
        status_value: str,
    ) -> str:
        if worktree.exists():
            status = subprocess.run(
                ("git", "status", "--porcelain", "--untracked-files=no"),
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if status.returncode != 0 or status.stdout.strip():
                return "recovery_required"
        if root.exists() and not root.is_symlink():
            try:
                shutil.rmtree(root)
            except OSError:
                return "recovery_required"
        if root.exists() or worktree.exists():
            return "recovery_required"
        return status_value
