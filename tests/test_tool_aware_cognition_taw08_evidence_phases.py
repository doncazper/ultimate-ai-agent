from __future__ import annotations

import base64
import ast
import builtins
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
from types import SimpleNamespace
import subprocess
import sys
import tempfile

import pytest
from packaging.tags import Tag

from ultimate_ai_agent.core.private_path_security import (
    require_private_tree,
    require_safe_private_ancestor_chain,
)


ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "scripts/run_tool_aware_cognition_taw08_evidence_phases.py"
WORKER_PATH = ROOT / "scripts/taw08_evidence_phase_worker.py"
VERIFIER_PATH = ROOT / "scripts/verify_tool_aware_cognition_taw08.py"


def _load(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


driver = _load("taw08_evidence_phase_driver", DRIVER_PATH)
worker = _load("taw08_evidence_phase_worker_test", WORKER_PATH)
SOURCE_DIGESTS = {
    "driver_source_digest_ref": "sha256:" + "d" * 64,
    "worker_source_digest_ref": "sha256:" + "e" * 64,
}


class _Dumpable(SimpleNamespace):
    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return dict(vars(self))


def _receipt(phase: str) -> dict[str, object]:
    payload = {
        "schema_version": f"test-{phase}.v1",
        "phase": phase,
        "status": driver.STATUS_BY_PHASE[phase],
        "independent_promotion_ready": False,
        "public_quality_claims_allowed": False,
        "production_authority_added": False,
        "runtime_model_calls_added": False,
        "provider_calls_added": False,
        "execution_authority_added": False,
        "raw_content_persisted": False,
        **SOURCE_DIGESTS,
    }
    return {**payload, "receipt_digest_ref": driver._canonical_digest(payload)}


def _artifact(path_ref: str, kind: str, content: bytes) -> dict[str, object]:
    return {
        "path_ref": path_ref,
        "artifact_kind": kind,
        "content_digest_ref": f"sha256:{hashlib.sha256(content).hexdigest()}",
        "content_base64": base64.b64encode(content).decode("ascii"),
    }


def _response(phase: str) -> dict[str, object]:
    expected = (
        driver.PREPARE_PATHS
        if phase == "prepare_delta"
        else driver.FINAL_PATHS
        if phase == "verify_delta"
        else {}
    )
    return {
        "schema_version": "uaa-taw08-phase-worker-response.v1",
        "phase": phase,
        "receipt": _receipt(phase),
        "artifacts": [
            _artifact(path_ref, kind, f"content:{path_ref}".encode())
            for path_ref, kind in expected.items()
        ],
    }


def test_response_validator_requires_exact_phase_paths_and_authority() -> None:
    receipt, artifacts = driver._validate_response(
        _response("prepare_delta"),
        expected_phase="prepare_delta",
        expected_source_digests=SOURCE_DIGESTS,
    )
    assert receipt["status"] == "founder_private_accepted_postmerge_pending"
    assert len(artifacts) == 3

    substituted = _response("prepare_delta")
    substituted["artifacts"] = substituted["artifacts"][:-1]
    with pytest.raises(ValueError, match="artifact census"):
        driver._validate_response(
            substituted,
            expected_phase="prepare_delta",
            expected_source_digests=SOURCE_DIGESTS,
        )

    expanded = _response("verify_publication")
    expanded_receipt = expanded["receipt"]
    assert isinstance(expanded_receipt, dict)
    expanded_receipt["public_quality_claims_allowed"] = True
    digest_payload = {
        key: value
        for key, value in expanded_receipt.items()
        if key != "receipt_digest_ref"
    }
    expanded_receipt["receipt_digest_ref"] = driver._canonical_digest(digest_payload)
    with pytest.raises(ValueError, match="authority"):
        driver._validate_response(
            expanded,
            expected_phase="verify_publication",
            expected_source_digests=SOURCE_DIGESTS,
        )

    rebound = _response("prepare_delta")
    rebound_receipt = rebound["receipt"]
    assert isinstance(rebound_receipt, dict)
    rebound_receipt["worker_source_digest_ref"] = "sha256:" + "f" * 64
    rebound_receipt["receipt_digest_ref"] = driver._canonical_digest(
        {
            key: value
            for key, value in rebound_receipt.items()
            if key != "receipt_digest_ref"
        }
    )
    with pytest.raises(ValueError, match="status, digest, or authority"):
        driver._validate_response(
            rebound,
            expected_phase="prepare_delta",
            expected_source_digests=SOURCE_DIGESTS,
        )


def test_worker_binds_its_staged_bytes_and_driver_to_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker_digest = f"sha256:{hashlib.sha256(WORKER_PATH.read_bytes()).hexdigest()}"
    driver_digest = "sha256:" + "d" * 64
    entries = (
        SimpleNamespace(
            path_ref=worker.DRIVER_PATH_REF,
            content_digest_ref=driver_digest,
        ),
        SimpleNamespace(
            path_ref=worker.WORKER_PATH_REF,
            content_digest_ref=worker_digest,
        ),
    )
    verifier = SimpleNamespace(
        _candidate_lock=lambda *_args, **_kwargs: (
            SimpleNamespace(entries=entries),
            {},
        )
    )
    monkeypatch.setenv("UAA_TAW08_LOCKED_CHILD_REVISION", "a" * 40)
    request = {
        "driver_source_digest_ref": driver_digest,
        "worker_source_digest_ref": worker_digest,
    }
    worker._verify_candidate_operational_sources(
        verifier,
        candidate_root=tmp_path,
        request=request,
    )
    request["driver_source_digest_ref"] = "sha256:" + "f" * 64
    with pytest.raises(RuntimeError, match="source binding drift"):
        worker._verify_candidate_operational_sources(
            verifier,
            candidate_root=tmp_path,
            request=request,
        )


def test_reconciliation_replaces_only_exact_marker_span() -> None:
    start = "[//]: # (TAW08-RECONCILIATION:START)"
    middle = "[//]: # (TAW08-RECONCILIATION:JSON)"
    end = "[//]: # (TAW08-RECONCILIATION:END)"
    prefix = b"prefix\nwith-bytes\n"
    suffix = b"\nsuffix\nwith-bytes\n"
    candidate = (
        prefix
        + start.encode()
        + b"\nold narrative\n"
        + middle.encode()
        + b"\n{}\n"
        + end.encode()
        + suffix
    )
    changed = worker.replace_reconciliation_block(
        candidate,
        start_marker=start,
        json_marker=middle,
        end_marker=end,
        narrative="implemented narrative",
        artifact_json='{"status":"implemented"}',
    )
    assert changed.startswith(prefix + start.encode())
    assert changed.endswith(end.encode() + suffix)
    assert b"implemented narrative" in changed
    assert b"old narrative" not in changed

    with pytest.raises(ValueError, match="marker census"):
        worker.replace_reconciliation_block(
            candidate + start.encode(),
            start_marker=start,
            json_marker=middle,
            end_marker=end,
            narrative="implemented narrative",
            artifact_json="{}",
        )


def test_private_inputs_and_outputs_fail_closed(tmp_path: Path) -> None:
    private = tmp_path / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o600)
    assert (
        driver._require_owner_only_file(private.resolve(), purpose="test input")
        == private.resolve()
    )
    private.chmod(0o644)
    with pytest.raises(ValueError, match="owner-only"):
        driver._require_owner_only_file(private.resolve(), purpose="test input")

    output = tmp_path / "artifact.json"
    driver._write_private(output, b"first\n")
    assert stat_mode(output) == 0o600
    driver._write_private(output, b"first\n")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        driver._write_private(output, b"second\n")


def test_private_tree_walk_is_explicit_bounded_and_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "private-tree"
    root.mkdir(mode=0o700)
    nested = root / "nested"
    nested.mkdir(mode=0o700)
    evidence = nested / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    evidence.chmod(0o600)

    assert require_private_tree(root, purpose="private tree") == root.resolve()
    with pytest.raises(ValueError, match="census is too large"):
        require_private_tree(root, purpose="private tree", max_entries=1)

    evidence.chmod(0o644)
    with pytest.raises(ValueError, match="unsafe entry"):
        require_private_tree(root, purpose="private tree")


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_phase_private_inputs_and_output_dir_reject_extended_acl(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o600)
    output_dir = tmp_path / "output"
    output_dir.mkdir(mode=0o700)
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow read", str(private)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            driver._require_owner_only_file(private.resolve(), purpose="phase input")
        with pytest.raises(ValueError, match="extended ACL"):
            worker._owner_only_file(private.resolve(), purpose="phase input")
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(private)),
            check=False,
            capture_output=True,
        )
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow read", str(output_dir)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            driver._prepare_output_directory(output_dir.resolve())
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(output_dir)),
            check=False,
            capture_output=True,
        )


def test_private_path_checks_allow_admin_alias_and_reject_user_symlink() -> None:
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="uaa-taw08-path-") as value:
        alias_root = Path(value)
        private = alias_root / "private.json"
        private.write_text("{}\n", encoding="utf-8")
        private.chmod(0o600)

        assert driver._require_owner_only_file(
            private,
            purpose="phase input",
        ) == private.resolve()
        assert worker._owner_only_file(private, purpose="phase input") == private.resolve()
        assert driver._prepare_output_directory(alias_root / "output") == (
            alias_root / "output"
        ).resolve()

        target = alias_root / "target"
        target.mkdir(mode=0o700)
        target_file = target / "request.json"
        target_file.write_text("{}\n", encoding="utf-8")
        target_file.chmod(0o600)
        linked = alias_root / "linked"
        linked.symlink_to(target, target_is_directory=True)
        with pytest.raises(ValueError, match="unsafe linked ancestor"):
            driver._require_owner_only_file(
                linked / "request.json",
                purpose="phase input",
            )
        with pytest.raises(ValueError, match="unsafe linked ancestor"):
            worker._owner_only_file(
                linked / "request.json",
                purpose="phase input",
            )


def test_lexical_ancestor_identity_drift_fails_before_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ancestor = tmp_path / "ancestor"
    ancestor.mkdir(mode=0o700)
    private = ancestor / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o600)
    real_lstat = driver.os.lstat
    observed = 0

    def drifting_lstat(path: object) -> object:
        nonlocal observed
        metadata = real_lstat(path)
        if Path(path) == ancestor:
            observed += 1
            if observed == 2:
                return SimpleNamespace(
                    st_dev=metadata.st_dev,
                    st_ino=metadata.st_ino + 1,
                    st_mode=metadata.st_mode,
                    st_uid=metadata.st_uid,
                    st_nlink=metadata.st_nlink,
                    st_size=metadata.st_size,
                    st_mtime_ns=metadata.st_mtime_ns,
                    st_ctime_ns=metadata.st_ctime_ns,
                )
        return metadata

    monkeypatch.setattr(driver.os, "lstat", drifting_lstat)
    with pytest.raises(ValueError, match="lexical ancestor changed"):
        driver._require_safe_private_ancestor_chain(
            private,
            purpose="phase input",
        )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_lexical_ancestor_rejects_extended_acl_grants(tmp_path: Path) -> None:
    ancestor = tmp_path / "acl-ancestor"
    ancestor.mkdir(mode=0o700)
    private = ancestor / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o600)
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow write", str(ancestor)),
            check=True,
            capture_output=True,
        )
        for checker in (
            driver._require_safe_private_ancestor_chain,
            worker._require_safe_private_ancestor_chain,
            require_safe_private_ancestor_chain,
        ):
            with pytest.raises(ValueError, match="unsafe extended ACL grants"):
                checker(private, purpose="phase input")
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(ancestor)),
            check=False,
            capture_output=True,
        )


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_lexical_ancestor_rejects_grant_after_deny_acl(tmp_path: Path) -> None:
    ancestor = tmp_path / "multiple-acl-ancestor"
    ancestor.mkdir(mode=0o700)
    private = ancestor / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o600)
    try:
        subprocess.run(
            ("/bin/chmod", "+a#", "0", "everyone deny delete", str(ancestor)),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ("/bin/chmod", "+a#", "1", "everyone allow write", str(ancestor)),
            check=True,
            capture_output=True,
        )
        for checker in (
            driver._require_safe_private_ancestor_chain,
            worker._require_safe_private_ancestor_chain,
            require_safe_private_ancestor_chain,
        ):
            with pytest.raises(ValueError, match="unsafe extended ACL grants"):
                checker(private, purpose="phase input")
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(ancestor)),
            check=False,
            capture_output=True,
        )


def test_output_directory_rejects_unsafe_parent_before_creation(
    tmp_path: Path,
) -> None:
    unsafe_parent = tmp_path / "unsafe"
    unsafe_parent.mkdir(mode=0o700)
    unsafe_parent.chmod(0o777)
    output = unsafe_parent / "new-output"
    try:
        with pytest.raises(ValueError, match="parent is unsafe"):
            driver._prepare_output_directory(output)
        assert not output.exists()
    finally:
        unsafe_parent.chmod(0o700)


def test_output_directory_rejects_immediate_symlink_parent_before_creation(
    tmp_path: Path,
) -> None:
    target_parent = tmp_path / "target-parent"
    target_parent.mkdir(mode=0o700)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(target_parent, target_is_directory=True)
    output = linked_parent / "new-output"

    with pytest.raises(ValueError, match="parent must already exist"):
        driver._prepare_output_directory(output)

    assert not (target_parent / output.name).exists()


def test_main_redacts_path_bearing_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret_path = str(tmp_path / "founder-private" / "evidence.json")

    def fail_with_path(*_args: object, **_kwargs: object) -> Path:
        raise subprocess.TimeoutExpired(cmd=secret_path, timeout=1)

    monkeypatch.setattr(driver, "_require_owner_only_file", fail_with_path)
    result = driver.main(
        [
            "prepare_delta",
            "--candidate-worktree",
            str(tmp_path / "candidate"),
            "--founder-evidence",
            secret_path,
            "--locked-wheelhouse",
            str(tmp_path / "wheelhouse"),
            "--output-dir",
            str(tmp_path / "output"),
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == "TAW-08 evidence phase blocked: bounded failure\n"
    assert secret_path not in captured.err


def test_owner_checks_fail_closed_when_posix_identity_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = tmp_path / "private.json"
    private.write_text("{}\n", encoding="utf-8")
    private.chmod(0o644)
    output = tmp_path / "output"
    output.mkdir(mode=0o755)

    def forbidden_getuid() -> int:
        raise AssertionError("Windows ownership checks must not call os.getuid")

    monkeypatch.setattr(driver.os, "name", "nt")
    monkeypatch.setattr(driver.os, "getuid", forbidden_getuid)

    with pytest.raises(ValueError, match="unavailable on this platform"):
        driver._require_owner_only_file(private, purpose="test")
    with pytest.raises(ValueError, match="unavailable on this platform"):
        driver._prepare_output_directory(output)
    with pytest.raises(ValueError, match="unavailable on this platform"):
        worker._owner_only_file(private, purpose="test")


def test_python_310_import_uses_locked_dev_environment_tomli_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__
    fake_tomli = SimpleNamespace(TOMLDecodeError=ValueError, loads=lambda _value: {})

    def import_without_tomllib(name: str, *args: object, **kwargs: object) -> object:
        if name == "tomllib":
            raise ModuleNotFoundError("No module named 'tomllib'")
        if name == "tomli":
            return fake_tomli
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_tomllib)
    driver_namespace = runpy.run_path(
        str(DRIVER_PATH), run_name="python310_compat_driver"
    )
    verifier_tree = ast.parse(
        VERIFIER_PATH.read_text(encoding="utf-8"), filename=str(VERIFIER_PATH)
    )
    verifier_fallback = next(
        node
        for node in verifier_tree.body
        if isinstance(node, ast.Try)
        and any(
            isinstance(imported, ast.Import)
            and any(alias.name == "tomllib" for alias in imported.names)
            for imported in node.body
        )
    )
    verifier_namespace: dict[str, object] = {}
    exec(
        compile(
            ast.Module(body=[verifier_fallback], type_ignores=[]),
            str(VERIFIER_PATH),
            "exec",
        ),
        verifier_namespace,
    )
    locked_packages = driver.tomllib.loads(
        (ROOT / "uv.lock").read_text(encoding="utf-8")
    )["package"]

    assert driver_namespace["tomllib"] is fake_tomli
    assert verifier_namespace["tomllib"] is fake_tomli
    assert any(package.get("name") == "tomli" for package in locked_packages)


def stat_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def test_clean_worktree_precheck_rejects_dirty_and_hidden_entries(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(("git", "init", "-q"), cwd=repository, check=True)
    tracked = repository / "tracked.txt"
    tracked.write_text("one\n", encoding="utf-8")
    subprocess.run(("git", "add", "tracked.txt"), cwd=repository, check=True)
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=TAW08 Test",
            "-c",
            "user.email=taw08@example.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ),
        cwd=repository,
        check=True,
    )
    root, revision = driver._precheck_clean_worktree(repository.resolve())
    assert root == repository.resolve()
    assert len(revision) == 40

    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be clean"):
        driver._precheck_clean_worktree(repository.resolve())
    tracked.write_text("one\n", encoding="utf-8")
    subprocess.run(
        ("git", "update-index", "--skip-worktree", "tracked.txt"),
        cwd=repository,
        check=True,
    )
    with pytest.raises(ValueError, match="hidden index"):
        driver._precheck_clean_worktree(repository.resolve())


def test_worker_rechecks_candidate_before_repository_import(tmp_path: Path) -> None:
    repository = (tmp_path / "repository").resolve()
    verifier_path = repository / "scripts/verify_tool_aware_cognition_taw08.py"
    acceptance_path = (
        repository
        / "src/ultimate_ai_agent/core/evals/tool_aware_acceptance.py"
    )
    verifier_path.parent.mkdir(parents=True)
    acceptance_path.parent.mkdir(parents=True)
    for package in (
        repository / "scripts/__init__.py",
        repository / "src/ultimate_ai_agent/__init__.py",
        repository / "src/ultimate_ai_agent/core/__init__.py",
        repository / "src/ultimate_ai_agent/core/evals/__init__.py",
    ):
        package.write_text("", encoding="utf-8")
    verifier_path.write_text("SAFE = True\n", encoding="utf-8")
    acceptance_path.write_text("SAFE = True\n", encoding="utf-8")
    subprocess.run(("git", "init", "-q"), cwd=repository, check=True)
    subprocess.run(("git", "add", "."), cwd=repository, check=True)
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=TAW08 Test",
            "-c",
            "user.email=taw08@example.invalid",
            "commit",
            "-q",
            "-m",
            "fixture",
        ),
        cwd=repository,
        check=True,
    )
    _root, revision = driver._precheck_clean_worktree(repository)
    sentinel = tmp_path / "candidate-import-ran"
    verifier_path.write_text(
        "import os\nfrom pathlib import Path\n"
        'Path(os.environ["UAA_TEST_IMPORT_SENTINEL"]).write_text("ran")\n',
        encoding="utf-8",
    )
    environment = driver._sanitized_environment()
    environment.update(
        {
            "UAA_TAW08_PREFLIGHT_COMPLETE": "1",
            "UAA_TAW08_LOCKED_CHILD_REVISION": revision,
            "UAA_TEST_CANDIDATE": str(repository),
            "UAA_TEST_IMPORT_SENTINEL": str(sentinel),
            "UAA_TEST_WORKER": str(WORKER_PATH),
        }
    )
    code = (
        "import os, runpy\n"
        "from pathlib import Path\n"
        'worker = runpy.run_path(os.environ["UAA_TEST_WORKER"])\n'
        'worker["_load_repository_modules"]('
        'Path(os.environ["UAA_TEST_CANDIDATE"]).resolve())\n'
    )

    completed = subprocess.run(
        (sys.executable, "-I", "-B", "-S", "-c", code),
        env=environment,
        check=False,
        capture_output=True,
        timeout=30,
    )

    assert completed.returncode != 0
    assert b"must be clean before import" in completed.stderr
    assert not sentinel.exists()

    substituted_bin = tmp_path / "substituted-bin"
    substituted_bin.mkdir()
    substituted_git = substituted_bin / "git"
    substituted_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    substituted_git.chmod(0o755)
    environment["PATH"] = str(substituted_bin) + os.pathsep + environment["PATH"]
    substituted = subprocess.run(
        (sys.executable, "-I", "-B", "-S", "-c", code),
        env=environment,
        check=False,
        capture_output=True,
        timeout=30,
    )

    assert substituted.returncode != 0
    assert b"trusted provenance" in substituted.stderr
    assert not sentinel.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX provenance regression")
@pytest.mark.parametrize("module", (driver, worker))
def test_phase_git_rejects_path_substitution(
    module: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    substituted_git = tmp_path / "git"
    substituted_git.write_bytes(b"substituted git")
    substituted_git.chmod(0o777)
    monkeypatch.setattr(
        module.shutil,
        "which",
        lambda _name: str(substituted_git),
    )

    with pytest.raises(RuntimeError, match="trusted provenance"):
        module._trusted_git_executable()


@pytest.mark.parametrize("module", (driver, worker))
def test_phase_git_commands_use_authenticated_absolute_executable(
    module: object,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        module,
        "_trusted_git_executable",
        lambda: Path("/trusted/git"),
    )

    def successful_run(command: tuple[str, ...], **_kwargs: object):
        observed.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=b"trusted output")

    monkeypatch.setattr(module.subprocess, "run", successful_run)
    if module is driver:
        output = module._git(tmp_path, "status")
    else:
        output = module._preimport_git(tmp_path, "status")

    assert output == b"trusted output"
    assert observed == [("/trusted/git", "--no-replace-objects", "status")]


def test_locked_wheel_selection_uses_reachable_compatible_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filenames = {
        "pip": "pip-26.2.1-py3-none-any.whl",
        "compatible": "demo-1.0-py3-none-any.whl",
        "incompatible": "demo-1.0-cp310-cp310-win_amd64.whl",
        "inactive": "inactive-1.0-py3-none-any.whl",
        "unreachable": "unreachable-1.0-py3-none-any.whl",
    }
    content_by_name = {
        filename: f"locked:{kind}".encode()
        for kind, filename in filenames.items()
    }

    def wheel(filename: str) -> str:
        content = content_by_name[filename]
        return (
            "{ url = \"https://files.pythonhosted.org/packages/"
            f"{filename}\", hash = \"sha256:{hashlib.sha256(content).hexdigest()}\", "
            f"size = {len(content)} }}"
        )

    pyproject = b'[project]\nname = "sample-project"\nversion = "1.0"\n'
    uv_lock = "\n".join(
        (
            "version = 1",
            "[[package]]",
            'name = "sample-project"',
            'version = "1.0"',
            "[package.optional-dependencies]",
            'dev = [{ name = "demo" }, { name = "pip" }, '
            '{ name = "inactive", marker = "python_version < \'1\'" }]',
            "[[package]]",
            'name = "demo"',
            'version = "1.0"',
            f"wheels = [{wheel(filenames['incompatible'])}, "
            f"{wheel(filenames['compatible'])}]",
            "[[package]]",
            'name = "pip"',
            'version = "26.2.1"',
            f"wheels = [{wheel(filenames['pip'])}]",
            "[[package]]",
            'name = "inactive"',
            'version = "1.0"',
            f"wheels = [{wheel(filenames['inactive'])}]",
            "[[package]]",
            'name = "unreachable"',
            'version = "1.0"',
            f"wheels = [{wheel(filenames['unreachable'])}]",
        )
    ).encode()
    provisioned = tmp_path / "provisioned"
    selected = tmp_path / "selected"
    provisioned.mkdir()
    for filename, content in content_by_name.items():
        (provisioned / filename).write_bytes(content)
    monkeypatch.setattr(driver, "sys_tags", lambda: (Tag("py3", "none", "any"),))

    copied = driver._copy_locked_wheelhouse(
        provisioned=provisioned.resolve(),
        selected=selected,
        pyproject=pyproject,
        uv_lock=uv_lock,
    )

    assert tuple(path.name for path in copied) == (
        filenames["compatible"],
        filenames["pip"],
    )
    assert {path.name for path in selected.iterdir()} == {
        filenames["compatible"],
        filenames["pip"],
    }


def test_locked_wheel_selection_rejects_untrusted_or_incompatible_only_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pyproject = b'[project]\nname = "sample-project"\nversion = "1.0"\n'
    uv_lock = b"""version = 1
[[package]]
name = "sample-project"
version = "1.0"
[package.optional-dependencies]
dev = [{ name = "demo" }]
[[package]]
name = "demo"
version = "1.0"
wheels = [
  { url = "https://example.invalid/demo-1.0-py3-none-any.whl", hash = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", size = 10 },
]
"""
    monkeypatch.setattr(driver, "sys_tags", lambda: (Tag("py3", "none", "any"),))

    with pytest.raises(ValueError, match="no compatible locked wheel"):
        driver._compatible_locked_wheel_identities(
            pyproject=pyproject,
            uv_lock=uv_lock,
        )


def test_locked_worker_command_uses_isolated_preflight_not_pythonpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "candidate"
    scripts = candidate / "scripts"
    scripts.mkdir(parents=True)
    (candidate / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (candidate / "uv.lock").write_text("fixture\n", encoding="utf-8")
    preflight = scripts / "verify_taw08_environment_preflight.py"
    preflight.write_text("# fixture\n", encoding="utf-8")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    observed: dict[str, object] = {}
    events: list[str] = []

    def fake_copy(**kwargs: object) -> tuple[Path, ...]:
        selected = kwargs["selected"]
        assert isinstance(selected, Path)
        selected.mkdir(mode=0o700)
        return (selected / "pip-fixture.whl", selected / "dep-fixture.whl")

    def fake_materialize(**kwargs: object) -> Path:
        events.append("materialize")
        environment_root = kwargs["environment_root"]
        assert isinstance(environment_root, Path)
        executable = environment_root / "bin" / "python"
        executable.parent.mkdir(parents=True)
        executable.write_text("", encoding="utf-8")
        return executable

    def fake_run(command: tuple[str, ...], **kwargs: object) -> SimpleNamespace:
        events.append("invoke")
        observed["command"] = command
        observed.update(kwargs)
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(_response("prepare_delta")).encode(),
            stderr=b"",
        )

    monkeypatch.setattr(driver, "_copy_locked_wheelhouse", fake_copy)
    monkeypatch.setattr(driver, "_materialize_environment", fake_materialize)
    source_by_ref = {
        driver.DRIVER_PATH_REF: b"driver-source",
        driver.WORKER_PATH_REF: b"worker-source",
        driver.PREFLIGHT_PATH_REF: b"preflight-source",
    }
    expected_source_digests = {
        field: "sha256:" + hashlib.sha256(source_by_ref[path_ref]).hexdigest()
        for field, path_ref in (
            ("driver_source_digest_ref", driver.DRIVER_PATH_REF),
            ("worker_source_digest_ref", driver.WORKER_PATH_REF),
        )
    }

    def fake_candidate_source_bytes(**kwargs: object) -> bytes:
        path_ref = kwargs["path_ref"]
        assert isinstance(path_ref, str)
        return source_by_ref[path_ref]

    def fake_precheck(path: Path) -> tuple[Path, str]:
        events.append("recheck")
        return path, "a" * 40

    monkeypatch.setattr(driver, "_candidate_source_bytes", fake_candidate_source_bytes)
    monkeypatch.setattr(driver, "_precheck_clean_worktree", fake_precheck)
    monkeypatch.setattr(driver.subprocess, "run", fake_run)
    response, source_digests = driver._invoke_locked_worker(
        request={"phase": "prepare_delta"},
        candidate_root=candidate.resolve(),
        candidate_revision="a" * 40,
        locked_wheelhouse=wheelhouse.resolve(),
    )
    assert response["phase"] == "prepare_delta"
    assert source_digests == expected_source_digests
    command = observed["command"]
    assert isinstance(command, tuple)
    assert command[1:4] == ("-I", "-B", "-S")
    assert Path(command[4]).name == preflight.name
    assert command[4] != str(preflight)
    assert events == ["materialize", "recheck", "invoke"]
    environment = observed["env"]
    assert isinstance(environment, dict)
    assert "PYTHONPATH" not in environment
    assert environment["UAA_TAW08_LOCKED_CHILD_REVISION"] == "a" * 40
    assert environment["UAA_TAW08_PHASE_WORKER_DIGEST"].startswith("sha256:")


def test_publication_reverifies_stored_postmerge_foundation_receipt(
    tmp_path: Path,
) -> None:
    environment = SimpleNamespace(receipt_digest_ref="sha256:" + "e" * 64)
    stored_receipt = SimpleNamespace(
        stage="postmerge",
        revision_ref="git-sha:" + "1" * 40,
        command_mode="report-only",
        evaluator_environment_receipt=environment,
        evaluator_environment_digest_ref=environment.receipt_digest_ref,
        receipt_digest_ref="sha256:" + "a" * 64,
        report_ref="foundation-report-ref:stored",
        passed=True,
        redacted=True,
        raw_content_persisted=False,
    )
    current_receipt = SimpleNamespace(
        stage="postmerge",
        revision_ref=stored_receipt.revision_ref,
        command_mode="report-only",
        evaluator_environment_receipt=environment,
        evaluator_environment_digest_ref=environment.receipt_digest_ref,
        receipt_digest_ref="sha256:" + "b" * 64,
        report_ref="foundation-report-ref:fresh-rerun",
        passed=True,
        redacted=True,
        raw_content_persisted=False,
    )
    observed: dict[str, object] = {}

    def verify_repository_foundation_gate(**kwargs: object) -> object:
        observed.update(kwargs)
        return current_receipt

    verifier = SimpleNamespace(
        verify_repository_foundation_gate=verify_repository_foundation_gate
    )
    assert (
        worker._verify_current_postmerge_foundation_receipt(
            verifier,
            delta_root=tmp_path,
            stored_receipt=stored_receipt,
        )
        is stored_receipt
    )

    for field, value in (
        ("revision_ref", "git-sha:" + "2" * 40),
        ("stage", "exact_head"),
        ("passed", False),
        ("redacted", False),
        ("raw_content_persisted", True),
        ("evaluator_environment_digest_ref", "sha256:" + "f" * 64),
    ):
        invalid = SimpleNamespace(**vars(current_receipt))
        setattr(invalid, field, value)
        verifier.verify_repository_foundation_gate = lambda **_kwargs: invalid
        with pytest.raises(ValueError, match="differs from Git"):
            worker._verify_current_postmerge_foundation_receipt(
                verifier,
                delta_root=tmp_path,
                stored_receipt=stored_receipt,
            )

    assert observed == {"stage": "postmerge", "repository_root": tmp_path}


def test_worker_phase_sequence_materializes_exact_receipts_and_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_root = (tmp_path / "candidate").resolve()
    delta_root = (tmp_path / "delta").resolve()
    publication_root = (tmp_path / "publication").resolve()
    for root in (candidate_root, delta_root, publication_root):
        root.mkdir()
    m1 = "1" * 40
    m2 = "2" * 40
    m3 = "3" * 40
    candidate_lock = SimpleNamespace(
        git_revision_ref=f"git-sha:{m1}",
        manifest_digest_ref="sha256:" + "a" * 64,
    )
    founder_evidence = SimpleNamespace(
        evidence_digest_ref="sha256:" + "b" * 64,
    )

    def report(status: str, fingerprint: str) -> SimpleNamespace:
        return SimpleNamespace(
            status=status,
            report_fingerprint_ref=fingerprint,
            founder_private_accepted=True,
            failure_refs=(),
            independent_promotion_blocker_refs=(
                "blocker-ref:taw08:independent-promotion-missing",
            ),
            independent_promotion_ready=False,
            sealed_holdout_evidence_verified=False,
            public_quality_claims_allowed=False,
            production_authority_added=False,
            runtime_model_calls_added=False,
            provider_calls_added=False,
            execution_authority_added=False,
            raw_content_persisted=False,
        )

    pre_report = report(
        "founder_private_accepted_postmerge_pending", "sha256:" + "c" * 64
    )
    intermediate_report = report(
        "founder_private_accepted_final_publication_pending",
        "sha256:" + "d" * 64,
    )
    final_report = report(
        "founder_private_accepted_promotion_blocked", "sha256:" + "e" * 64
    )
    manifest = _Dumpable(
        delta_revision_ref=f"git-sha:{m2}",
        manifest_digest_ref="sha256:" + "f" * 64,
    )
    delta_receipt = _Dumpable(receipt_digest_ref="sha256:" + "0" * 64)
    foundation_receipt = _Dumpable(
        stage="postmerge",
        revision_ref=f"git-sha:{m2}",
        command_mode="report-only",
        evaluator_environment_receipt={
            "receipt_digest_ref": "sha256:" + "3" * 64
        },
        evaluator_environment_digest_ref="sha256:" + "3" * 64,
        receipt_digest_ref="sha256:" + "4" * 64,
        passed=True,
        redacted=True,
        raw_content_persisted=False,
    )
    publication_receipt = _Dumpable(receipt_digest_ref="sha256:" + "5" * 64)
    final_artifact = _Dumpable(
        status="founder_private_accepted_final_publication_pending",
        independent_promotion_ready=False,
        public_quality_claims_allowed=False,
        raw_content_persisted=False,
    )

    class PhaseAcceptance:
        TAW08_ACCEPTANCE_REPORT_PATH_REF = (
            "repo-path-ref:docs/evals/"
            "tool_aware_cognition_taw08_acceptance_report_v1.json"
        )
        TAW08_ACTIVE_TRUTH_PATH_REFS = (
            "repo-path-ref:docs/kanban/current_board.md",
            "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        )
        TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF = (
            "repo-path-ref:docs/evals/"
            "tool_aware_cognition_taw08_final_acceptance_report_v1.json"
        )

        def redacted_acceptance_report_artifact(
            self, _report: object
        ) -> _Dumpable:
            return _Dumpable(status="founder_private_accepted_postmerge_pending")

        def evaluate_taw08_acceptance(self, **kwargs: object) -> SimpleNamespace:
            if kwargs.get("final_acceptance_publication_receipt") is not None:
                return final_report
            return intermediate_report

        def build_final_acceptance_publication_artifact(
            self, **_kwargs: object
        ) -> _Dumpable:
            return final_artifact

    acceptance = PhaseAcceptance()

    class PhaseVerifier:
        def __init__(self) -> None:
            self.foundation_roots: list[Path] = []
            self.expand_publication_history = False

        def verify_repository_evidence_delta(self, **_kwargs: object) -> object:
            return delta_receipt

        def verify_repository_foundation_gate(self, **kwargs: object) -> object:
            assert kwargs["stage"] == "postmerge"
            repository_root = kwargs["repository_root"]
            assert isinstance(repository_root, Path)
            self.foundation_roots.append(repository_root)
            return foundation_receipt

        def derive_publication_history_census(
            self, *_args: object, **_kwargs: object
        ) -> SimpleNamespace:
            paths = (acceptance.TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,)
            if self.expand_publication_history:
                paths += ("repo-path-ref:src/unexpected.py",)
            return SimpleNamespace(path_refs=paths, history_path_refs=paths)

        def verify_repository_final_acceptance_publication(
            self, **_kwargs: object
        ) -> object:
            return publication_receipt

    verifier = PhaseVerifier()
    revisions = {
        candidate_root: m1,
        delta_root: m2,
        publication_root: m3,
    }

    def load_founder_evidence(*_args: object, **_kwargs: object) -> object:
        return founder_evidence

    def candidate_context(*_args: object, **_kwargs: object) -> tuple[object, ...]:
        return candidate_lock, SimpleNamespace(verified=True), pre_report

    def require_clean(
        _verifier: object,
        repository_root: Path,
        *,
        expected_revision: str | None = None,
    ) -> str:
        revision = revisions[repository_root]
        if expected_revision is not None:
            assert expected_revision == revision
        return revision

    def manifest_from_git(*_args: object, **kwargs: object) -> tuple[object, ...]:
        assert kwargs["delta_revision"] == m2
        return manifest, SimpleNamespace(), {}

    stored_phase_receipt: dict[str, object] = {}

    def load_verified_delta_receipt(
        *_args: object, **_kwargs: object
    ) -> tuple[object, ...]:
        return (
            stored_phase_receipt,
            manifest,
            delta_receipt,
            foundation_receipt,
        )

    monkeypatch.setattr(worker, "_load_founder_evidence", load_founder_evidence)
    monkeypatch.setattr(worker, "_candidate_context", candidate_context)
    monkeypatch.setattr(worker, "_require_clean_exact_worktree", require_clean)
    monkeypatch.setattr(worker, "_manifest_from_git", manifest_from_git)
    monkeypatch.setattr(
        worker,
        "_reconciliation_content",
        lambda *_args, path_ref, **_kwargs: f"reconciled:{path_ref}\n".encode(),
    )
    monkeypatch.setattr(
        worker, "_load_verified_delta_receipt", load_verified_delta_receipt
    )

    prepare_request = {
        "schema_version": "uaa-taw08-phase-request.v1",
        "phase": "prepare_delta",
        "candidate_repository": str(candidate_root),
        "founder_evidence_path": str(tmp_path / "founder.json"),
        **SOURCE_DIGESTS,
    }
    prepare_response = worker._prepare_delta(verifier, acceptance, prepare_request)
    prepare_receipt, prepare_artifacts = driver._validate_response(
        prepare_response,
        expected_phase="prepare_delta",
        expected_source_digests=SOURCE_DIGESTS,
    )
    assert prepare_receipt["candidate_revision_ref"] == f"git-sha:{m1}"
    assert {path_ref for path_ref, _content in prepare_artifacts} == set(
        driver.PREPARE_PATHS
    )

    delta_request = {
        **prepare_request,
        "phase": "verify_delta",
        "delta_repository": str(delta_root),
    }
    delta_response = worker._verify_delta(verifier, acceptance, delta_request)
    delta_phase_receipt, delta_artifacts = driver._validate_response(
        delta_response,
        expected_phase="verify_delta",
        expected_source_digests=SOURCE_DIGESTS,
    )
    stored_phase_receipt.update(delta_phase_receipt)
    assert delta_phase_receipt["delta_revision_ref"] == f"git-sha:{m2}"
    assert [path_ref for path_ref, _content in delta_artifacts] == list(
        driver.FINAL_PATHS
    )

    publication_request = {
        **delta_request,
        "phase": "verify_publication",
        "publication_repository": str(publication_root),
        "verified_delta_receipt_path": str(tmp_path / "verified-delta.json"),
    }
    publication_response = worker._verify_publication(
        verifier, acceptance, publication_request
    )
    publication_phase_receipt, publication_artifacts = driver._validate_response(
        publication_response,
        expected_phase="verify_publication",
        expected_source_digests=SOURCE_DIGESTS,
    )
    assert publication_phase_receipt["publication_revision_ref"] == f"git-sha:{m3}"
    assert publication_phase_receipt["status"] == (
        "founder_private_accepted_promotion_blocked"
    )
    assert publication_artifacts == []
    assert verifier.foundation_roots == [delta_root, delta_root]

    verifier.expand_publication_history = True
    with pytest.raises(ValueError, match="M2-to-M3 path census drift"):
        worker._verify_publication(verifier, acceptance, publication_request)


def test_cli_has_only_three_explicit_non_mutating_phases() -> None:
    parser = driver._parser()
    subparsers = next(action for action in parser._actions if action.dest == "phase")
    assert set(subparsers.choices) == {
        "prepare_delta",
        "verify_delta",
        "verify_publication",
    }
    source = DRIVER_PATH.read_text(encoding="utf-8") + WORKER_PATH.read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "RuntimeGateway",
        "invoke_local_model",
        "requests.",
        "httpx.",
        "urllib.request",
        "git commit",
        "git push",
    ):
        assert forbidden not in source
