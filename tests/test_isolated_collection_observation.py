from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import sysconfig
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.verification import isolated_collection_observation as lane
from scripts.verification import isolated_collection_worker as worker


MODULES = ("ultimate_ai_agent.probe",)
TESTS = ("tests/test_probe.py",)


def _payload() -> dict[str, object]:
    return {
        "schema_version": lane.WORKER_SCHEMA,
        "nonce": "bound",
        "exit_code": 0,
        "item_refs": ["a" * 64],
        "posture_refs": ["b" * 64],
        "collection_errors": 0,
        "collection_skips": 0,
        "deselected": 0,
        "disabled_items": 0,
        "model_counts": [1],
        "builtin_bindings_preserved": True,
    }


def _observation() -> lane.CollectionObservation:
    return lane.CollectionObservation(
        source_ref="a" * 64,
        environment_ref="b" * 64,
        harness_ref="c" * 64,
        selection_ref="d" * 64,
        test_inputs_ref="e" * 64,
        ordered_collection_ref="f" * 64,
        collected_count=1,
        model_counts=(1,),
    )


def _source(root: Path, *, prefix: str = "", value: int = 1) -> Path:
    files = {
        "src/ultimate_ai_agent/__init__.py": "",
        "src/ultimate_ai_agent/probe.py": prefix
        + (
            "from pydantic import BaseModel, Field, field_validator\n"
            "class Probe(BaseModel):\n"
            "    values: list[int] = Field(default_factory=list)\n"
            "    @field_validator('values')\n"
            "    @classmethod\n"
            "    def validate_values(cls, values):\n"
            f"        return values + [{value}]\n"
        ),
        "tests/test_probe.py": (
            "import os, pytest\n"
            "from ultimate_ai_agent.probe import Probe\n"
            "@pytest.mark.skipif(os.name != 'posix', reason='synthetic platform posture')\n"
            "def test_probe():\n"
            "    raise AssertionError('a collection-only probe must not run this body')\n"
        ),
        "scripts/__init__.py": "",
        "pyproject.toml": "[tool.pytest.ini_options]\n",
        "uv.lock": "version = 1\n",
    }
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    return root.resolve()


def test_valid_observation_is_content_free_and_never_acceptance() -> None:
    decoded = lane._decode(json.dumps(_payload()).encode(), "bound", 1)
    assert decoded["model_counts"] == [1]
    before = _observation()
    result = lane.compare_observations(before, replace(before, source_ref="0" * 64))
    assert result["status"] == "observed_equal"
    assert result["acceptance_authority"] is False
    assert result["pytest_mode"] == "collection_only"
    assert "probe" not in json.dumps(result)


@pytest.mark.parametrize(
    "field", ["environment_ref", "harness_ref", "selection_ref", "test_inputs_ref"]
)
def test_changed_comparison_inputs_refuse(field: str) -> None:
    before = _observation()
    with pytest.raises(lane.ObservationError, match="comparison_inputs_changed"):
        lane.compare_observations(before, replace(before, **{field: "0" * 64}))


@pytest.mark.parametrize(
    "mutation",
    [
        {"ordered_collection_ref": "0" * 64},
        {"collected_count": 2},
        {"model_counts": (2,)},
    ],
)
def test_changed_collection_or_construction_is_not_equal(
    mutation: dict[str, object],
) -> None:
    before = _observation()
    assert (
        lane.compare_observations(before, replace(before, **mutation))["status"]
        == "observed_difference"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": "other"},
        {"nonce": "stale"},
        {"exit_code": 1},
        {"exit_code": False},
        {"collection_errors": 1},
        {"collection_skips": 1},
        {"deselected": 1},
        {"disabled_items": 1},
        {"item_refs": []},
        {"item_refs": ["a" * 64, "a" * 64]},
        {"item_refs": ["raw-name"]},
        {"item_refs": None},
        {"model_counts": []},
        {"model_counts": [0]},
        {"posture_refs": []},
        {"posture_refs": ["raw-value"]},
        {"model_counts": [True]},
        {"model_counts": [100_001]},
        {"builtin_bindings_preserved": False},
        {"builtin_bindings_preserved": 1},
        {"extra": "not-allowed"},
    ],
)
def test_untrusted_observation_is_fail_closed(mutation: dict[str, object]) -> None:
    with pytest.raises(lane.ObservationError):
        lane._decode(json.dumps({**_payload(), **mutation}).encode(), "bound", 1)


@pytest.mark.parametrize(
    "encoded", [b"{", b"[]", b"\xff", b'{"nonce":1,"nonce":2}', b"[" * 20_000]
)
def test_malformed_duplicate_or_recursive_observation_refuses(encoded: bytes) -> None:
    with pytest.raises(lane.ObservationError, match="observation_invalid"):
        lane._decode(encoded, "bound", 1)


@pytest.mark.parametrize(
    "name,args,kwargs",
    [
        ("skip", (), {"reason": "fixture"}),
        ("xfail", (False,), {"reason": "fixture"}),
        ("skipif", (), {"reason": "fixture"}),
        ("skipif", (True,), {"reason": "fixture"}),
        ("skipif", (0,), {"reason": "fixture"}),
        ("skipif", ("False",), {"reason": "fixture"}),
        ("skipif", (False,), {}),
        ("skipif", (False,), {"reason": "fixture", "unknown": 0}),
        ("skipif", (False,), {"reason": "fixture", "condition": True}),
    ],
)
def test_mark_recognition_never_evaluates_conditions(
    name: str, args: tuple[object, ...], kwargs: dict[str, object]
) -> None:
    mark = SimpleNamespace(name=name, args=args, kwargs=kwargs)
    assert worker.inactive_skipif_marker(mark) is None


def test_inactive_boolean_mark_preserves_posture_without_evaluation() -> None:
    mark = SimpleNamespace(
        name="skipif", args=(False, False), kwargs={"reason": "fixture"}
    )
    assert worker.inactive_skipif_marker(mark) == {
        "conditions": [False, False],
        "reason": "fixture",
    }
    mark = SimpleNamespace(
        name="skipif", args=(), kwargs={"condition": False, "reason": "fixture"}
    )
    assert worker.inactive_skipif_marker(mark) == {
        "conditions": [False],
        "reason": "fixture",
    }


@pytest.mark.parametrize(
    "tests,modules",
    [
        ((), MODULES),
        (("/tests/test_probe.py",), MODULES),
        (("tests/../test_probe.py",), MODULES),
        (("tests/test_probe.py::one",), MODULES),
        (("tests/test_probe.py", "tests/test_probe.py"), MODULES),
        (("tests/fixture.py",), MODULES),
        (TESTS, ()),
        (TESTS, ("os",)),
        (TESTS, ("ultimate_ai_agent.probe;other",)),
        (TESTS, MODULES * 2),
    ],
)
def test_selection_cannot_be_a_command_or_module_import(
    tests: tuple[str, ...], modules: tuple[str, ...]
) -> None:
    with pytest.raises(lane.ObservationError, match="selection_invalid"):
        lane._selection(tests, modules)


def test_snapshots_reject_links_special_files_and_exceeded_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _source(tmp_path / "source")
    source = root / "src/ultimate_ai_agent/probe.py"
    link = root / "src/link.py"
    link.symlink_to(source)
    with pytest.raises(lane.ObservationError, match="unsafe_input"):
        lane._tree(root, source=True)
    link.unlink()
    fifo = root / "src/fifo"
    os.mkfifo(fifo)
    with pytest.raises(lane.ObservationError, match="unsafe_input"):
        lane._tree(root, source=True)
    fifo.unlink()
    monkeypatch.setattr(lane, "MAX_TREE_BYTES", 1)
    with pytest.raises(lane.ObservationError, match="input_capacity"):
        lane._tree(root, source=True)


def test_parent_symlink_is_not_followed(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    (actual / "input").write_text("fixture")
    link = tmp_path / "link"
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(lane.ObservationError, match="input_unavailable"):
        lane._read(link / "input")


def test_runtime_links_are_bound_and_may_not_escape(tmp_path: Path) -> None:
    (tmp_path / "binary").write_text("fixture")
    alias = tmp_path / "alias"
    alias.symlink_to("binary")
    snapshot = lane._tree(tmp_path, runtime=True)
    assert snapshot["alias\0link"] == b"binary"
    alias.unlink()
    alias.symlink_to(tmp_path.parent)
    with pytest.raises(lane.ObservationError, match="unsafe_input"):
        lane._tree(tmp_path, runtime=True)


def test_environment_does_not_copy_ambient_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UAA_SYNTHETIC_CREDENTIAL_SLOT", "private-fixture")
    environment = lane._environment(tmp_path)
    assert "UAA_SYNTHETIC_CREDENTIAL_SLOT" not in environment
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert environment["PYDANTIC_DISABLE_PLUGINS"] == "__all__"
    assert "PYTHONPATH" not in environment


def test_profile_denies_ambient_capabilities_and_limits_write_target(
    tmp_path: Path,
) -> None:
    profile = lane._profile(
        python=tmp_path / "python",
        runtime=tmp_path / "runtime",
        dependencies=tmp_path / "dependencies",
        source=tmp_path / "source",
        harness=tmp_path / "harness",
        scratch=tmp_path / "scratch",
    )
    assert "(deny default)" in profile
    assert "network" not in profile
    assert "process-fork" not in profile
    assert "mach-lookup" not in profile
    assert "(allow file-write* (literal " in profile
    assert profile.count("(allow file-write* (subpath ") == 1
    assert str(tmp_path / "scratch" / "cache") in profile
    assert "observation.json" in profile


def test_unsupported_platform_never_launches_unsandboxed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane.sys, "platform", "unsupported")
    with pytest.raises(lane.ObservationError, match="os_isolation_unavailable"):
        lane.observe_pair(tmp_path, tmp_path, tests=TESTS, model_modules=MODULES)


def test_changed_test_inputs_rejected_before_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lane.sys, "platform", "darwin")
    before = _source(tmp_path / "before")
    after = _source(tmp_path / "after")
    (after / TESTS[0]).write_text("def test_replaced(): pass\n")
    monkeypatch.setattr(Path, "is_file", lambda _path: True)
    with pytest.raises(lane.ObservationError, match="comparison_inputs_changed"):
        lane.observe_pair(before, after, tests=TESTS, model_modules=MODULES)


@pytest.mark.parametrize(
    "posture,reason",
    [
        ("missing", "observation_unavailable"),
        ("timeout", "isolated_run_timeout"),
        ("launch-failed", "isolated_run_unavailable"),
        ("nonzero", "isolated_run_failed"),
        ("source-drift", "source_changed"),
        ("snapshot-drift", "source_changed"),
        ("unsafe-mode", "observation_unsafe"),
        ("linked-output", "observation_unsafe"),
    ],
)
def test_executor_failures_and_drift_cannot_produce_an_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    posture: str,
    reason: str,
) -> None:
    source = _source(tmp_path / "source")
    files = lane._tree(source, source=True)
    temporary_directory = lane.tempfile.TemporaryDirectory
    # This unit test substitutes the process itself; keep its scratch portable
    # on non-macOS CI. Real OS executor tests use the unmodified macOS path.
    monkeypatch.setattr(
        lane.tempfile,
        "TemporaryDirectory",
        lambda **options: temporary_directory(prefix=options["prefix"], dir=tmp_path),
    )

    def synthetic_run(
        command: list[str], **options: object
    ) -> subprocess.CompletedProcess:
        assert command[:2] == ["/usr/bin/sandbox-exec", "-p"]
        assert command[4:7] == ["-I", "-B", "-S"]
        assert (
            options["stdin"]
            == options["stdout"]
            == options["stderr"]
            == subprocess.DEVNULL
        )
        assert options["timeout"] == lane.TIMEOUT_SECONDS
        if posture == "timeout":
            raise subprocess.TimeoutExpired("fixed-probe", 180)
        if posture == "launch-failed":
            raise OSError("synthetic failure")
        if posture in {"missing", "nonzero"}:
            return subprocess.CompletedProcess(
                command, 1 if posture == "nonzero" else 0
            )
        request = json.loads(Path(command[-2]).read_bytes())
        output = Path(command[-1])
        output.write_text(json.dumps({**_payload(), "nonce": request["nonce"]}))
        output.chmod(0o600)
        if posture == "source-drift":
            (source / TESTS[0]).write_text("changed")
        elif posture == "snapshot-drift":
            frozen = Path(command[-5]) / TESTS[0]
            frozen.chmod(0o600)
            frozen.write_text("changed")
        elif posture == "unsafe-mode":
            output.chmod(0o644)
        elif posture == "linked-output":
            os.link(output, output.with_name("other"))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(lane.subprocess, "run", synthetic_run)
    with pytest.raises(lane.ObservationError, match=f"^{reason}$"):
        lane._observe(
            source,
            files,
            {"synthetic.py": b""},
            tmp_path,
            "a" * 64,
            tmp_path / "python",
            b"# synthetic worker",
            "b" * 64,
            TESTS,
            MODULES,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        {"source_ref": "not-a-digest"},
        {"environment_ref": 1},
        {"collected_count": True},
        {"collected_count": 0},
        {"collected_count": 100_001},
        {"model_counts": ()},
        {"model_counts": (True,)},
        {"model_counts": (0,)},
    ],
)
def test_direct_observation_records_reject_invalid_shapes(
    mutation: dict[str, object],
) -> None:
    with pytest.raises(lane.ObservationError):
        replace(_observation(), **mutation)


def test_real_host_os_bootstrap_policy_is_reviewed() -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    assert Path("/usr/bin/sandbox-exec").is_file()
    assert (
        hashlib.sha256(lane._read(lane.DYLD_PROFILE)).hexdigest()
        == lane.DYLD_PROFILE_SHA256
    )


def test_real_host_interpreter_layout_is_supported() -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    runtime = Path(sys.base_prefix).resolve(strict=True)
    python = Path(sys.executable).resolve(strict=True)
    assert python.is_relative_to(runtime)


def test_real_host_runtime_census_is_supported() -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    assert lane._tree(Path(sys.base_prefix).resolve(strict=True), runtime=True)


def test_real_host_dependency_census_is_supported() -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    assert lane._tree(Path(sysconfig.get_path("purelib")).resolve(strict=True))


def test_real_host_isolated_interpreter_bootstrap_succeeds(tmp_path: Path) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    assert (
        hashlib.sha256(lane._read(lane.DYLD_PROFILE)).hexdigest()
        == lane.DYLD_PROFILE_SHA256
    )
    root = tmp_path.resolve()
    scratch = root / "scratch"
    scratch.mkdir()
    (scratch / "cache").mkdir()
    python = Path(sys.executable).resolve(strict=True)
    policy = lane._profile(
        python=python,
        runtime=Path(sys.base_prefix).resolve(strict=True),
        dependencies=root / "dependencies",
        source=root / "source",
        harness=root / "harness",
        scratch=scratch,
    )
    # Isolate startup from dependency imports and collection. Do not expose
    # child output or relax the same deny-default executor policy.
    result = subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-p",
            policy,
            str(python),
            "-I",
            "-B",
            "-S",
            "-c",
            "pass",
        ],
        cwd=root,
        env=lane._environment(scratch),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=lane.TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == 0


def test_real_pydantic_construction_is_observed_without_running_test_body(
    tmp_path: Path,
) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    before = _source(tmp_path / "before")
    after = _source(tmp_path / "after", value=2)
    result = lane.observe_pair(before, after, tests=TESTS, model_modules=MODULES)
    assert result["status"] == "observed_equal"
    assert result["baseline_model_counts"] == [1]
    assert result["candidate_model_counts"] == [1]
    assert result["baseline_collected_count"] == 1
    assert result["baseline_source_ref"] != result["candidate_source_ref"]
    assert result["acceptance_authority"] is False
    assert result["pytest_mode"] == "collection_only"
    assert str(tmp_path) not in json.dumps(result)


def test_real_os_boundary_denies_host_reads_network_processes_and_source_writes(
    tmp_path: Path,
) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    canary = tmp_path / "canary"
    canary.write_text("synthetic-protected-resource")
    prefix = (
        "import pathlib, socket, subprocess, tempfile, os\n"
        "assert tempfile.gettempdir() == os.environ['TMPDIR']\n"
        "with tempfile.TemporaryFile() as cache: cache.write(b'bounded fixture')\n"
        "try: (pathlib.Path(tempfile.gettempdir()).parent / 'outside-cache').write_bytes(b'fixture')\n"
        "except PermissionError: pass\n"
        "else: raise AssertionError('isolation did not deny writes outside private cache')\n"
        f"paths = [{str(canary)!r}, __file__]\n"
        "for index, name in enumerate(paths):\n"
        "    try:\n"
        "        if index == 0: pathlib.Path(name).read_bytes()\n"
        "        else: pathlib.Path(name).write_text('changed')\n"
        "    except PermissionError: pass\n"
        "    else: raise AssertionError('isolation did not deny file operation')\n"
        "try: subprocess.run(['/usr/bin/true'], check=True)\n"
        "except PermissionError: pass\n"
        "else: raise AssertionError('isolation did not deny child process')\n"
        "try:\n"
        "    with socket.socket() as client: client.connect(('127.0.0.1', 9))\n"
        "except PermissionError: pass\n"
        "else: raise AssertionError('isolation did not deny network')\n"
    )
    before = _source(tmp_path / "before", prefix=prefix)
    after = _source(tmp_path / "after", prefix=prefix)
    assert (
        lane.observe_pair(before, after, tests=TESTS, model_modules=MODULES)["status"]
        == "observed_equal"
    )
    assert canary.read_text() == "synthetic-protected-resource"


@pytest.mark.parametrize(
    "prefix",
    [
        "import pytest\npytest.skip('synthetic collection skip', allow_module_level=True)\n",
        "raise RuntimeError('synthetic collection failure')\n",
    ],
)
def test_real_skipped_or_aborted_model_import_never_looks_equal(
    tmp_path: Path, prefix: str
) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    before = _source(tmp_path / "before")
    after = _source(tmp_path / "after", prefix=prefix)
    with pytest.raises(lane.ObservationError, match="collection_incomplete"):
        lane.observe_pair(before, after, tests=TESTS, model_modules=MODULES)


@pytest.mark.parametrize("condition", [True, "False"])
def test_real_changed_skip_condition_is_not_silently_accepted(
    tmp_path: Path, condition: object
) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only isolated observation executor")
    before = _source(tmp_path / "before", prefix="SKIP = False\n")
    after = _source(tmp_path / "after", prefix=f"SKIP = {condition!r}\n")
    test = (
        "import pytest\nfrom ultimate_ai_agent.probe import Probe, SKIP\n"
        "@pytest.mark.skipif(SKIP, reason='synthetic posture')\n"
        "def test_probe(): raise AssertionError('must not run')\n"
    )
    for root in (before, after):
        (root / TESTS[0]).write_text(test)
    with pytest.raises(lane.ObservationError, match="collection_incomplete"):
        lane.observe_pair(before, after, tests=TESTS, model_modules=MODULES)
