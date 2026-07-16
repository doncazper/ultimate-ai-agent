from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.verification.ci_command_manifest import (
    PLAYWRIGHT_BROWSER_DIRNAME,
    PRIVATE_BASE_REF,
    PROFILE_REF,
    VERIFICATION_DAG,
    CommandSpec,
    VerificationPlan,
    command_registry,
    lane_registry,
)
from scripts.verification.ci_fallback_contracts import (
    SAFE_REF_PATTERN,
    SHA_PATTERN,
    PrivateVerificationScope,
    PrivateVerificationResult,
    has_valid_command_result_evidence,
    has_valid_timing_window,
)
from scripts.verification.ci_fallback_private_scope import (
    build_private_verification_scope,
)
from scripts.verification.pytest_shard_processes import (
    cancellation_signals,
    installed_signal_handlers,
    stop_processes,
)
from scripts.verification.run_ci_lane import expected_pytest_shard_plan_ref


REMOTE_HEAD_QUERY_TIMEOUT_SECONDS = 20
REMOTE_HEAD_OUTPUT_LIMIT_BYTES = 256 * 1024
REMOTE_HEAD_COUNT_LIMIT = 512
REMOTE_HEAD_REF_PATTERN = re.compile(r"^refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,239}$")
BRANCH_BINDING_PREFIX = "branch-binding-ref:private-ci:"


class RemoteHeadAttestationError(RuntimeError):
    """Safe, typed failure to prove the exact SHA against live remote heads."""

    def __init__(self, reason_ref: str) -> None:
        if SAFE_REF_PATTERN.fullmatch(reason_ref) is None:
            raise ValueError("remote attestation reason ref is unsafe")
        super().__init__(reason_ref)
        self.reason_ref = reason_ref


def _valid_head_ref(ref: str) -> bool:
    ref_parts = ref.removeprefix("refs/heads/").split("/")
    return bool(
        REMOTE_HEAD_REF_PATTERN.fullmatch(ref)
        and ".." not in ref
        and "@{" not in ref
        and all(
            part
            and not part.startswith(".")
            and not part.endswith(".")
            and not part.endswith(".lock")
            for part in ref_parts
        )
    )


def _source_branch_binding_ref(
    *,
    branch_ref: str,
    repository_sha: str,
    origin_main_sha: str,
) -> str:
    if (
        not _valid_head_ref(branch_ref)
        or SHA_PATTERN.fullmatch(repository_sha) is None
        or SHA_PATTERN.fullmatch(origin_main_sha) is None
    ):
        raise ValueError("private CI branch binding input is unsafe")
    payload = (
        "remote-ref:github:doncazper:ultimate-ai-agent",
        branch_ref,
        repository_sha,
        origin_main_sha,
    )
    return BRANCH_BINDING_PREFIX + hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()
    ).hexdigest()


def _parse_advertised_heads(raw: bytes) -> tuple[tuple[str, str], ...]:
    if not isinstance(raw, bytes) or len(raw) > REMOTE_HEAD_OUTPUT_LIMIT_BYTES:
        raise RemoteHeadAttestationError(
            "reason-ref:private-ci:remote-advertisement-invalid"
        )
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise RemoteHeadAttestationError(
            "reason-ref:private-ci:remote-advertisement-invalid"
        ) from exc
    lines = text.splitlines()
    if not lines or len(lines) > REMOTE_HEAD_COUNT_LIMIT:
        raise RemoteHeadAttestationError(
            "reason-ref:private-ci:remote-advertisement-invalid"
        )
    heads: list[tuple[str, str]] = []
    observed_refs: set[str] = set()
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 2:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:remote-advertisement-invalid"
            )
        sha, ref = parts
        if (
            SHA_PATTERN.fullmatch(sha) is None
            or not _valid_head_ref(ref)
            or ref in observed_refs
        ):
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:remote-advertisement-invalid"
            )
        observed_refs.add(ref)
        heads.append((sha, ref))
    return tuple(sorted(heads, key=lambda item: item[1]))


def _owned_live_process_group_members(process_group: int) -> tuple[int, ...]:
    """Return live same-owner members, failing closed on an unsafe group."""

    try:
        completed = subprocess.run(
            ("/bin/ps", "-axo", "pid=,pgid=,uid=,state="),
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("private CI process-group inspection failed") from exc
    if completed.returncode != 0 or len(completed.stdout) > 1024 * 1024:
        raise RuntimeError("private CI process-group inspection failed")
    live_members: list[int] = []
    for line in completed.stdout.decode("ascii", errors="strict").splitlines():
        parts = line.split()
        if len(parts) != 4:
            raise RuntimeError("private CI process-group inspection failed")
        try:
            pid, pgid, uid = (int(value) for value in parts[:3])
        except ValueError as exc:
            raise RuntimeError("private CI process-group inspection failed") from exc
        if pgid != process_group or parts[3].startswith("Z"):
            continue
        if uid != os.getuid() or pid <= 0:
            raise RuntimeError("private CI process-group ownership is indeterminate")
        live_members.append(pid)
    return tuple(sorted(set(live_members)))


def _settle_permission_denied_process_group(process_group: int) -> None:
    """Handle the macOS exited-leader race without accepting live descendants."""

    deadline = time.monotonic() + 1.0
    while True:
        live_members = _owned_live_process_group_members(process_group)
        if not live_members:
            return
        for pid in live_members:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError as exc:
                raise RuntimeError(
                    "private CI process-group ownership is indeterminate"
                ) from exc
        if time.monotonic() >= deadline:
            raise RuntimeError("private CI process-group cleanup is incomplete")
        time.sleep(0.05)


def _safe_subprocess(
    argv: tuple[str, ...],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> tuple[int, int, str]:
    started = time.perf_counter()
    process: subprocess.Popen[bytes] | None = None
    cleanup_grace_seconds = 0.25

    def handle_signal(signum: int, _frame: object) -> None:
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
                cleanup_grace_seconds = 10.0
                returncode = 124
    except KeyboardInterrupt:
        cleanup_grace_seconds = 10.0
        returncode = 130
    finally:
        if process is not None:
            # A successful parent may still leave descendants in its process group.
            # Always settle that group before private verification can advance.
            try:
                stop_processes((process,), cleanup_grace_seconds)
            except PermissionError:
                # A successful leader can exit just before the final group probe;
                # enumerate only PID/PGID/UID/state and either kill every live
                # same-owner member or fail closed. No process command lines are
                # captured or persisted.
                _settle_permission_denied_process_group(process.pid)
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


ALLOWED_ORIGIN_URLS = frozenset(
    {
        "git@github.com:doncazper/ultimate-ai-agent.git",
        "https://github.com/doncazper/ultimate-ai-agent.git",
        "ssh://git@github.com/doncazper/ultimate-ai-agent.git",
    }
)
UV_VERSION = "0.11.21"
_FORBIDDEN_PRIVATE_COMMAND_REFS = frozenset(
    {
        "command:pytest.sharded-suite",
        "command:frontend.typecheck",
        "command:frontend.check",
    }
)
_FORBIDDEN_PRIVATE_UNIT_REFS = frozenset(
    {"pytest-shards", "pytest", "control-center-frontend"}
)


def _dependency_setup_commands() -> tuple[tuple[str, ...], ...]:
    return (
        ("python3.12", "-m", "venv", ".ci-bootstrap"),
        (
            ".ci-bootstrap/bin/python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"uv=={UV_VERSION}",
        ),
        (
            ".ci-bootstrap/bin/uv",
            "sync",
            "--frozen",
            "--extra",
            "dev",
            "--python",
            "python3.12",
        ),
    )


class IsolatedPrivateExecutor:
    def __init__(self, repo: Path) -> None:
        if repo.is_symlink() or not repo.is_dir():
            raise ValueError("private CI repository path is unsafe")
        self.repo = repo.resolve()

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

    def _live_advertised_heads(self) -> tuple[tuple[str, str], ...]:
        try:
            completed = subprocess.run(
                ("git", "ls-remote", "--heads", "origin"),
                cwd=self.repo,
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                timeout=REMOTE_HEAD_QUERY_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:remote-attestation-unavailable"
            ) from exc
        if completed.returncode != 0:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:remote-attestation-unavailable"
            )
        return _parse_advertised_heads(completed.stdout)

    def _attest_live_remote_heads(
        self,
        repository_sha: str,
        *,
        branch_ref: str,
    ) -> tuple[str, str]:
        if not _valid_head_ref(branch_ref):
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:current-branch-invalid"
            )
        heads = self._live_advertised_heads()
        main_shas = tuple(
            sha for sha, ref in heads if ref == "refs/heads/main"
        )
        if len(main_shas) != 1:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:remote-advertisement-invalid"
            )
        origin_main_sha = main_shas[0]
        branch_shas = tuple(sha for sha, ref in heads if ref == branch_ref)
        if len(branch_shas) != 1 or branch_shas[0] != repository_sha:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:exact-branch-head-not-advertised"
            )
        return (
            origin_main_sha,
            _source_branch_binding_ref(
                branch_ref=branch_ref,
                repository_sha=repository_sha,
                origin_main_sha=origin_main_sha,
            ),
        )

    def _preflight(self, repository_sha: str) -> tuple[str, str]:
        if not SHA_PATTERN.fullmatch(repository_sha):
            raise ValueError("private CI requires an exact lowercase SHA")
        if self._git("rev-parse", "HEAD") != repository_sha:
            raise ValueError("private CI source worktree must be on the exact SHA")
        if self._git("status", "--porcelain"):
            raise ValueError("private CI source worktree must be clean")
        if self._git("remote", "get-url", "origin") not in ALLOWED_ORIGIN_URLS:
            raise ValueError("private CI origin is not the canonical UAA repository")
        current_branch = self._git("branch", "--show-current")
        if not current_branch:
            raise RemoteHeadAttestationError(
                "reason-ref:private-ci:current-branch-required"
            )
        branch_ref = f"refs/heads/{current_branch}"
        return self._attest_live_remote_heads(
            repository_sha,
            branch_ref=branch_ref,
        )

    def prepare_scope(
        self,
        repository_sha: str,
        *,
        diagnostic_unit_refs: tuple[str, ...] = (),
    ) -> PrivateVerificationScope:
        origin_main_sha, source_branch_binding_ref = self._preflight(repository_sha)
        scope, _plan = build_private_verification_scope(
            self.repo,
            repository_sha=repository_sha,
            base_sha=origin_main_sha,
            source_branch_binding_ref=source_branch_binding_ref,
            diagnostic_unit_refs=diagnostic_unit_refs,
        )
        return scope

    def plan_fingerprint(self, repository_sha: str) -> str:
        """Compatibility shim for read-only callers during Phase 03 cutover."""

        return self.prepare_scope(repository_sha).plan_fingerprint

    def verify(
        self,
        repository_sha: str,
        *,
        series_ref: str,
        scope: PrivateVerificationScope,
    ) -> PrivateVerificationResult:
        del series_ref
        scope.validate()
        if scope.repository_sha != repository_sha:
            raise ValueError("private CI scope SHA does not match its request")
        origin_main_sha, source_branch_binding_ref = self._preflight(repository_sha)
        if (
            origin_main_sha != scope.base_sha
            or source_branch_binding_ref != scope.source_branch_binding_ref
        ):
            raise ValueError("private CI source binding changed after scope preparation")
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
                scope,
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
            "base_sha": scope.base_sha,
            "source_branch_binding_ref": scope.source_branch_binding_ref,
            "authoritative_plan_fingerprint": scope.authoritative_plan_fingerprint,
            "plan_fingerprint": scope.plan_fingerprint,
            "dependency_state_fingerprint": scope.dependency_state_fingerprint,
            "selected_unit_refs": scope.selected_unit_refs,
            "diagnostic_unit_refs": scope.diagnostic_unit_refs,
            "deferred_unit_refs": scope.deferred_unit_refs,
            "status": status_value,
            "command_result_refs": tuple(result_refs),
            "timings_ms": tuple(timings),
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "github_gate_satisfied": False,
            "merge_gate_satisfied": False,
            "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
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
        scope: PrivateVerificationScope,
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
                scope.base_sha,
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
        isolated_scope, isolated_plan = build_private_verification_scope(
            worktree,
            repository_sha=repository_sha,
            base_sha=scope.base_sha,
            source_branch_binding_ref=scope.source_branch_binding_ref,
            diagnostic_unit_refs=scope.diagnostic_unit_refs,
        )
        if isolated_scope != scope:
            raise ValueError("private CI isolated scope differs from prepared scope")
        env = _minimal_env(root)
        setup_commands = _dependency_setup_commands()
        for index, argv in enumerate(setup_commands, start=1):
            returncode, duration_ms, result_ref = _safe_subprocess(
                argv, cwd=worktree, timeout=900, env=env
            )
            timings.append((f"phase-ref:private-ci:install-{index}", duration_ms))
            result_refs.append(result_ref)
            if returncode != 0:
                return "fail", isolated_plan
        return (
            self._run_scope(
                repository_sha=repository_sha,
                scope=scope,
                root=root,
                worktree=worktree,
                env=env,
                timings=timings,
                result_refs=result_refs,
                isolated_plan=isolated_plan,
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
    def _assert_private_command_allowed(unit_ref: str, command: CommandSpec) -> None:
        units = {unit.unit_ref: unit for unit in VERIFICATION_DAG}
        unit = units[unit_ref]
        lowered = " ".join(command.argv).lower()
        if (
            unit_ref in _FORBIDDEN_PRIVATE_UNIT_REFS
            or command.command_ref in _FORBIDDEN_PRIVATE_COMMAND_REFS
            or unit.unit_kind.value in {"aggregate", "audit"}
            or "private" not in unit.execution_surfaces
            or "resource-ref:complete-pytest" in unit.exclusive_resource_refs
            or "resource-ref:typescript-typecheck" in unit.exclusive_resource_refs
            or "frontend-check" in lowered
            or "typecheck" in lowered
            or " tsc" in f" {lowered}"
            or (
                "run_pytest_shards.py" in lowered and "--shard-index" not in command.argv
            )
        ):
            raise ValueError("private CI command is reserved for authoritative GitHub")

    @staticmethod
    def _command_argv(
        command: CommandSpec,
        *,
        scope: PrivateVerificationScope,
        plan: VerificationPlan,
        root: Path,
    ) -> tuple[str, ...]:
        argv: list[str] = []
        for token in command.argv:
            if token == "{selected_test_refs}":
                if not plan.selected_test_refs:
                    raise ValueError("private focused pytest has no exact test ownership")
                argv.extend(plan.selected_test_refs)
                continue
            argv.append(
                token.replace("{repository_sha}", scope.repository_sha)
                .replace("{base_sha}", scope.base_sha)
                .replace("{temp_root}", str(root / "lane-temp"))
            )
        return tuple(argv)

    @staticmethod
    def _run_scope(
        *,
        repository_sha: str,
        scope: PrivateVerificationScope,
        root: Path,
        worktree: Path,
        env: dict[str, str],
        timings: list[tuple[str, int]],
        result_refs: list[str],
        isolated_plan: VerificationPlan,
    ) -> str:
        if any(
            command_ref.startswith("command:frontend.")
            for command_ref in scope.selected_command_refs
        ):
            returncode, duration_ms, result_ref = _safe_subprocess(
                ("npm", "ci"),
                cwd=worktree / "apps/control-center",
                timeout=900,
                env=env,
            )
            timings.append(("phase-ref:private-ci:frontend-install", duration_ms))
            result_refs.append(result_ref)
            if returncode != 0:
                return "fail"

        commands = command_registry()
        executed: set[str] = set()
        executed_order: list[str] = []
        for unit in VERIFICATION_DAG:
            if unit.unit_ref not in scope.selected_unit_refs:
                continue
            for command_ref in unit.command_refs:
                if command_ref in executed:
                    continue
                command = commands[command_ref]
                IsolatedPrivateExecutor._assert_private_command_allowed(
                    unit.unit_ref, command
                )
                IsolatedPrivateExecutor._validate_tracked_state(
                    worktree, repository_sha
                )
                current_scope, current_plan = build_private_verification_scope(
                    worktree,
                    repository_sha=repository_sha,
                    base_sha=scope.base_sha,
                    source_branch_binding_ref=scope.source_branch_binding_ref,
                    diagnostic_unit_refs=scope.diagnostic_unit_refs,
                    verify_repository_state=False,
                )
                if current_scope != scope or current_plan != isolated_plan:
                    raise ValueError("private CI scope changed before command start")
                command_env = {**env, **dict(command.env)}
                argv = IsolatedPrivateExecutor._command_argv(
                    command,
                    scope=scope,
                    plan=isolated_plan,
                    root=root,
                )
                returncode, duration_ms, result_ref = _safe_subprocess(
                    argv,
                    cwd=worktree,
                    timeout=command.timeout_seconds,
                    env=command_env,
                )
                timings.append((f"unit-ref:{unit.unit_ref}", duration_ms))
                result_refs.append(result_ref)
                executed.add(command_ref)
                executed_order.append(command_ref)
                if returncode != 0:
                    return "fail"
        if tuple(executed_order) != scope.selected_command_refs:
            raise ValueError("private CI did not execute its exact selected commands")
        return "pass"

    @staticmethod
    def _validate_tracked_state(worktree: Path, repository_sha: str) -> None:
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
        for argv in (("git", "diff", "--quiet"), ("git", "diff", "--cached", "--quiet")):
            completed = subprocess.run(
                argv,
                cwd=worktree,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            )
            if completed.returncode != 0:
                raise ValueError("private CI tracked worktree state changed")

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
