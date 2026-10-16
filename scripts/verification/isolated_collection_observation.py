"""Dependency-bound, offline collection observations, never corpus authority.

The initial executor is macOS-only and fails closed elsewhere. Source-only
guard behavior and the canonical test runner are deliberately unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import sysconfig
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "uaa-isolated-collection-observation.v1"
WORKER_SCHEMA = "uaa-isolated-collection-worker.v1"
MAX_FILES = 30_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TREE_BYTES = 512 * 1024 * 1024
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_ITEMS = 100_000
MAX_TEST_FILES = 128
TIMEOUT_SECONDS = 180
SOURCE_ROOTS = ("src", "tests", "scripts")
SOURCE_FILES = ("pyproject.toml", "uv.lock")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
MODEL_MODULE = re.compile(r"ultimate_ai_agent(?:\.[a-zA-Z_]\w*)+\Z", re.ASCII)
WORKER = Path(__file__).with_name("isolated_collection_worker.py")
DYLD_PROFILE = Path("/System/Library/Sandbox/Profiles/dyld-support.sb")
# Reviewed OS bootstrap rules only: system-image reads/mappings and loader
# syscalls; no network, process fork, Mach lookup, or writable-file grant.
# An OS policy change requires explicit review, not an allow-default fallback.
DYLD_PROFILE_SHA256 = "06215a5d32689aefe395c29710e182eb54ba22162f50df8b4842290f8a19bf1c"


class ObservationError(ValueError):
    """Only constant, content-free reason codes leave this boundary."""


def _ref(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read(
    path: Path, maximum: int = MAX_FILE_BYTES, *, private_output: bool = False
) -> bytes:
    """Reject links/special files and changed reads, including parent links."""
    descriptor = None
    directory = None
    try:
        if not path.is_absolute() or ".." in path.parts:
            raise ObservationError("unsafe_input")
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        directory = os.open(path.anchor, flags | os.O_DIRECTORY)
        for component in path.parts[1:-1]:
            child = os.open(component, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(path.name, flags, dir_fd=directory)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= maximum:
            raise ObservationError("unsafe_input")
        if private_output and (
            before.st_nlink != 1
            or before.st_uid != os.getuid()
            or stat.S_IMODE(before.st_mode) != 0o600
        ):
            raise ObservationError("unsafe_input")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read(maximum + 1)
        if len(data) != before.st_size or _identity(before) != _identity(
            os.fstat(descriptor)
        ):
            raise ObservationError("input_changed")
        return data
    except OSError:
        raise ObservationError("input_unavailable") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory is not None:
            os.close(directory)


def _tree(
    root: Path, *, source: bool = False, runtime: bool = False
) -> dict[str, bytes]:
    """Bound a complete declared input tree, not an imported-module sample."""
    result = {}
    total = 0
    pending = (
        [root / part for part in SOURCE_ROOTS + SOURCE_FILES] if source else [root]
    )
    while pending:
        path = pending.pop()
        if path.is_symlink():
            if not runtime:
                raise ObservationError("unsafe_input")
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ObservationError("unsafe_input")
            # Only the runtime census supports internal links; it is never
            # materialized. NUL separates this record from real file names.
            result[path.relative_to(root).as_posix() + "\0link"] = (
                target.relative_to(root).as_posix().encode()
            )
            if len(result) > MAX_FILES:
                raise ObservationError("input_capacity")
            continue
        if path.is_dir():
            try:
                children = sorted(path.iterdir(), reverse=True)
            except OSError:
                raise ObservationError("input_unavailable") from None
            pending.extend(
                child
                for child in children
                if runtime or (child.name != "__pycache__" and child.suffix != ".pyc")
            )
            if len(pending) + len(result) > MAX_FILES:
                raise ObservationError("input_capacity")
            continue
        data = _read(path)
        total += len(data)
        if len(result) >= MAX_FILES or total > MAX_TREE_BYTES:
            raise ObservationError("input_capacity")
        result[path.relative_to(root).as_posix()] = data
    return result


def _fingerprint(files: dict[str, bytes]) -> str:
    return _ref(
        [
            (name, hashlib.sha256(data).hexdigest())
            for name, data in sorted(files.items())
        ]
    )


def _platform_identity() -> tuple[str, ...]:
    identity = os.uname()
    # Exclude the node/host name; retain only the OS build and architecture.
    return (
        sys.platform,
        sys.version,
        identity.sysname,
        identity.release,
        identity.version,
        identity.machine,
    )


def _materialize(root: Path, files: dict[str, bytes]) -> None:
    root.mkdir(mode=0o700)
    for name, data in files.items():
        destination = root / name
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
        destination.chmod(0o400)


def _selection(tests: tuple[str, ...], modules: tuple[str, ...]) -> None:
    if not 1 <= len(tests) <= MAX_TEST_FILES or len(set(tests)) != len(tests):
        raise ObservationError("selection_invalid")
    for name in tests:
        if not isinstance(name, str) or len(name) > 1024:
            raise ObservationError("selection_invalid")
        path = PurePosixPath(name)
        if (
            not isinstance(name, str)
            or path.as_posix() != name
            or path.is_absolute()
            or ".." in path.parts
            or len(path.parts) < 2
            or path.parts[0] != "tests"
            or not name.endswith(".py")
            or not (path.name.startswith("test_") or path.name.endswith("_test.py"))
        ):
            raise ObservationError("selection_invalid")
    if (
        not 1 <= len(modules) <= 32
        or len(set(modules)) != len(modules)
        or any(
            not isinstance(name, str) or not MODEL_MODULE.fullmatch(name)
            for name in modules
        )
    ):
        raise ObservationError("selection_invalid")


def _profile(
    *,
    python: Path,
    runtime: Path,
    dependencies: Path,
    source: Path,
    harness: Path,
    scratch: Path,
) -> str:
    # JSON string quoting is compatible with the SBPL string grammar for
    # supported paths. Reject control/non-ASCII characters, not interpolate
    # arbitrary policy fragments. No network, process-fork or Mach lookup grant.
    def quoted(path: Path) -> str:
        text = str(path)
        if not text.isascii() or any(ord(char) < 32 for char in text):
            raise ObservationError("isolation_path_unsupported")
        return json.dumps(text)

    reads = (
        runtime,
        dependencies,
        source,
        harness,
        scratch,
        Path("/System/Library"),
        Path("/usr/lib"),
    )
    return "\n".join(
        [
            "(version 1)",
            "(deny default)",
            f"(import {quoted(DYLD_PROFILE)})",
            f"(allow process-exec (literal {quoted(python)}))",
            "(allow sysctl-read)",
            *(f"(allow file-read* (subpath {quoted(path)}))" for path in reads),
            *(
                f"(allow file-map-executable (subpath {quoted(path)}))"
                for path in (
                    runtime,
                    dependencies,
                    Path("/System/Library"),
                    Path("/usr/lib"),
                )
            ),
            # Existing import-cache code verifies directory ACLs by opening each
            # ancestor. This grants directory inspection only, not descendant
            # file reads. All writable cache data stays under this fresh run.
            *(
                f"(allow file-read* (require-all (vnode-type DIRECTORY) (literal {quoted(path)})))"
                for path in scratch.parents
            ),
            f"(allow file-write* (subpath {quoted(scratch / 'cache')}))",
            f"(allow file-write* (literal {quoted(scratch / 'observation.json')}))",
            '(allow file-read* file-write* (literal "/dev/null"))',
            '(allow file-read* (literal "/dev/urandom"))',
            "(allow file-read-metadata)",
        ]
    )


def _environment(scratch: Path) -> dict[str, str]:
    return {
        "HOME": str(scratch),
        "TMPDIR": str(scratch / "cache"),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYDANTIC_DISABLE_PLUGINS": "__all__",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _decode(data: bytes, nonce: str, model_count: int) -> dict[str, Any]:
    if type(data) is not bytes or not 0 < len(data) <= MAX_OUTPUT_BYTES:
        raise ObservationError("observation_invalid")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise ObservationError("observation_invalid")
            result[key] = value
        return result

    try:
        value = json.loads(data, object_pairs_hook=pairs)
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise ObservationError("observation_invalid") from None
    expected = {
        "schema_version",
        "nonce",
        "exit_code",
        "item_refs",
        "posture_refs",
        "collection_errors",
        "collection_skips",
        "deselected",
        "disabled_items",
        "model_counts",
        "builtin_bindings_preserved",
    }
    if not isinstance(value, dict) or value.keys() != expected:
        raise ObservationError("observation_invalid")
    if value["schema_version"] != WORKER_SCHEMA or value["nonce"] != nonce:
        raise ObservationError("observation_binding_invalid")
    counts = [
        value[key]
        for key in (
            "exit_code",
            "collection_errors",
            "collection_skips",
            "deselected",
            "disabled_items",
        )
    ]
    if any(type(count) is not int or count != 0 for count in counts):
        raise ObservationError("collection_incomplete")
    refs = value["item_refs"]
    if (
        not isinstance(refs, list)
        or not 0 < len(refs) <= MAX_ITEMS
        or any(
            not isinstance(item, str) or DIGEST.fullmatch(item) is None for item in refs
        )
        or len(set(refs)) != len(refs)
    ):
        raise ObservationError("collection_identity_invalid")
    postures = value["posture_refs"]
    if (
        not isinstance(postures, list)
        or len(postures) != len(refs)
        or any(
            not isinstance(ref, str) or DIGEST.fullmatch(ref) is None
            for ref in postures
        )
    ):
        raise ObservationError("collection_identity_invalid")
    models = value["model_counts"]
    if (
        not isinstance(models, list)
        or len(models) != model_count
        or any(type(count) is not int or not 0 < count <= MAX_ITEMS for count in models)
        or value["builtin_bindings_preserved"] is not True
    ):
        raise ObservationError("construction_not_observed")
    return value


@dataclass(frozen=True)
class CollectionObservation:
    source_ref: str
    environment_ref: str
    harness_ref: str
    selection_ref: str
    test_inputs_ref: str
    ordered_collection_ref: str
    collected_count: int
    model_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        refs = (
            self.source_ref,
            self.environment_ref,
            self.harness_ref,
            self.selection_ref,
            self.test_inputs_ref,
            self.ordered_collection_ref,
        )
        if any(
            not isinstance(ref, str) or DIGEST.fullmatch(ref) is None for ref in refs
        ):
            raise ObservationError("observation_binding_invalid")
        if (
            type(self.collected_count) is not int
            or not 0 < self.collected_count <= MAX_ITEMS
        ):
            raise ObservationError("collection_identity_invalid")
        if (
            not isinstance(self.model_counts, tuple)
            or not 1 <= len(self.model_counts) <= 32
            or any(
                type(count) is not int or not 0 < count <= MAX_ITEMS
                for count in self.model_counts
            )
        ):
            raise ObservationError("construction_not_observed")


def _observe(
    source: Path,
    files: dict[str, bytes],
    dependencies: dict[str, bytes],
    runtime: Path,
    runtime_ref: str,
    python: Path,
    worker: bytes,
    harness_ref: str,
    tests: tuple[str, ...],
    modules: tuple[str, ...],
) -> CollectionObservation:
    with tempfile.TemporaryDirectory(
        prefix="uaa-collection-", dir="/private/tmp"
    ) as temporary:
        root = Path(temporary).resolve()
        frozen = root / "source"
        packages = root / "dependencies"
        harness = root / "harness"
        scratch = root / "scratch"
        _materialize(frozen, files)
        _materialize(packages, dependencies)
        scratch.mkdir(mode=0o700)
        (scratch / "cache").mkdir(mode=0o700)
        nonce = secrets.token_hex(32)
        _materialize(
            harness,
            {
                "worker.py": worker,
                "request.json": json.dumps(
                    {"nonce": nonce, "tests": tests, "model_modules": modules}
                ).encode(),
            },
        )
        request = harness / "request.json"
        output = scratch / "observation.json"
        policy = _profile(
            python=python,
            runtime=runtime,
            dependencies=packages,
            source=frozen,
            harness=harness,
            scratch=scratch,
        )
        command = [
            "/usr/bin/sandbox-exec",
            "-p",
            policy,
            str(python),
            "-I",
            "-B",
            "-S",
            str(harness / "worker.py"),
            str(frozen),
            str(packages),
            str(scratch),
            str(request),
            str(output),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=frozen,
                env=_environment(scratch),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise ObservationError("isolated_run_unavailable") from None
        if completed.returncode != 0:
            raise ObservationError("isolated_run_failed")
        observation = _decode(
            _read(output, MAX_OUTPUT_BYTES, private_output=True), nonce, len(modules)
        )
        if _tree(frozen, source=True) != files or _tree(source, source=True) != files:
            raise ObservationError("source_changed")
        test_inputs = {
            name: data
            for name, data in files.items()
            if name.startswith("tests/") or name in SOURCE_FILES
        }
        return CollectionObservation(
            source_ref=_fingerprint(files),
            environment_ref=_ref(
                [runtime_ref, _fingerprint(dependencies), sys.version]
            ),
            harness_ref=harness_ref,
            selection_ref=_ref([tests, modules]),
            test_inputs_ref=_fingerprint(test_inputs),
            ordered_collection_ref=_ref(
                [observation["item_refs"], observation["posture_refs"]]
            ),
            collected_count=len(observation["item_refs"]),
            model_counts=tuple(observation["model_counts"]),
        )


def compare_observations(
    before: CollectionObservation, after: CollectionObservation
) -> dict[str, object]:
    """Compare bounded observations, not attest to arbitrary Python behavior."""
    for field in ("environment_ref", "harness_ref", "selection_ref", "test_inputs_ref"):
        if getattr(before, field) != getattr(after, field):
            raise ObservationError("comparison_inputs_changed")
    equal = (
        before.ordered_collection_ref == after.ordered_collection_ref
        and before.collected_count == after.collected_count
        and before.model_counts == after.model_counts
    )
    return {
        "schema_version": SCHEMA,
        "status": "observed_equal" if equal else "observed_difference",
        "acceptance_authority": False,
        "pytest_mode": "collection_only",
        "baseline_source_ref": before.source_ref,
        "candidate_source_ref": after.source_ref,
        "environment_ref": before.environment_ref,
        "harness_ref": before.harness_ref,
        "selection_ref": before.selection_ref,
        "test_inputs_ref": before.test_inputs_ref,
        "baseline_collection_ref": before.ordered_collection_ref,
        "candidate_collection_ref": after.ordered_collection_ref,
        "baseline_collected_count": before.collected_count,
        "candidate_collected_count": after.collected_count,
        "baseline_model_counts": list(before.model_counts),
        "candidate_model_counts": list(after.model_counts),
        "redaction_status": "content_free",
    }


def observe_pair(
    baseline: Path,
    candidate: Path,
    *,
    tests: tuple[str, ...],
    model_modules: tuple[str, ...],
) -> dict[str, object]:
    _selection(tests, model_modules)
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        raise ObservationError("os_isolation_unavailable")
    baseline, candidate = baseline.resolve(strict=True), candidate.resolve(strict=True)
    before, after = _tree(baseline, source=True), _tree(candidate, source=True)
    if any(name not in before or name not in after for name in tests):
        raise ObservationError("selection_unavailable")

    def test_inputs(files: dict[str, bytes]) -> dict[str, bytes]:
        return {
            name: data
            for name, data in files.items()
            if name.startswith("tests/") or name in SOURCE_FILES
        }

    if test_inputs(before) != test_inputs(after):
        raise ObservationError("comparison_inputs_changed")
    os_policy = _read(DYLD_PROFILE)
    if hashlib.sha256(os_policy).hexdigest() != DYLD_PROFILE_SHA256:
        raise ObservationError("os_isolation_policy_unreviewed")
    sandbox_binary = _read(Path("/usr/bin/sandbox-exec"))
    platform_identity = _platform_identity()
    dependency_root = Path(sysconfig.get_path("purelib")).resolve(strict=True)
    dependencies = _tree(dependency_root)
    runtime = Path(sys.base_prefix).resolve(strict=True)
    python = Path(sys.executable).resolve(strict=True)
    # Bind the actual interpreter and standard library. The OS itself remains
    # the trusted isolation boundary, not a claim of a portable hermetic VM.
    if not python.is_relative_to(runtime):
        raise ObservationError("runtime_layout_unsupported")
    runtime_files = _tree(runtime, runtime=True)
    runtime_ref = _ref(
        [
            _fingerprint(runtime_files),
            DYLD_PROFILE_SHA256,
            hashlib.sha256(sandbox_binary).hexdigest(),
            platform_identity,
        ]
    )
    worker = _read(WORKER)
    parent = _read(Path(__file__))
    harness_ref = _ref(
        [hashlib.sha256(worker).hexdigest(), hashlib.sha256(parent).hexdigest()]
    )
    first = _observe(
        baseline,
        before,
        dependencies,
        runtime,
        runtime_ref,
        python,
        worker,
        harness_ref,
        tests,
        model_modules,
    )
    second = _observe(
        candidate,
        after,
        dependencies,
        runtime,
        runtime_ref,
        python,
        worker,
        harness_ref,
        tests,
        model_modules,
    )
    if (
        _tree(dependency_root) != dependencies
        or _read(WORKER) != worker
        or _read(Path(__file__)) != parent
    ):
        raise ObservationError("environment_changed")
    if _tree(runtime, runtime=True) != runtime_files:
        raise ObservationError("environment_changed")
    if _read(DYLD_PROFILE) != os_policy:
        raise ObservationError("environment_changed")
    if (
        _read(Path("/usr/bin/sandbox-exec")) != sandbox_binary
        or _platform_identity() != platform_identity
    ):
        raise ObservationError("environment_changed")
    if _tree(baseline, source=True) != before or _tree(candidate, source=True) != after:
        raise ObservationError("source_changed")
    return compare_observations(first, second)
