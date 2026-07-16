from typing import Any
from pathlib import Path

from ultimate_ai_agent.core.gate import (
    FoundationGateStatus,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.sandbox_calculation.static_safety import (
    is_exact_sealed_calculation_forbidden_fragment_exception,
    is_exact_sealed_calculation_subprocess_site,
)
from ultimate_ai_agent.core.evidence_signing.static_safety import (
    is_exact_portable_evidence_helper_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_harness.static_safety import (
    is_exact_matrix_harness_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_session.static_safety import (
    is_exact_matrix_session_bounded_filesystem_site,
    is_exact_matrix_session_subprocess_site,
)
from ultimate_ai_agent.core.communications.matrix_sync.static_safety import (
    is_exact_matrix_cache_crypto_subprocess_site,
    is_exact_matrix_sync_transport_subprocess_site,
)


def _assert_exact_governed_runtime_command_subprocess_site(source: str) -> None:
    assert source.count("subprocess.run(") == 1
    assert source.count("subprocess.TimeoutExpired") == 1
    assert "shell=False" in source
    assert "shell=True" not in source
    assert "subprocess.Popen(" not in source
    allowed_removed = source.replace("subprocess.run(", "").replace(
        "subprocess.TimeoutExpired", ""
    )
    assert "subprocess." not in allowed_removed


def _assert_exact_portable_evidence_helper_subprocess_site(source: str) -> None:
    rel = "src/ultimate_ai_agent/core/evidence_signing/macos_keychain.py"
    assert is_exact_portable_evidence_helper_subprocess_site(
        rel_path=rel,
        source=source,
        fragment="subprocess.run(",
    )
    assert source.count("subprocess.run(") == 1
    assert source.count("subprocess.TimeoutExpired") == 1
    assert "shell=False" in source
    assert "shell=True" not in source
    assert "subprocess.Popen(" not in source
    assert source.count("subprocess.PIPE") == 2
    allowed_removed = (
        source.replace("subprocess.run(", "")
        .replace("subprocess.TimeoutExpired", "")
        .replace("subprocess.PIPE", "")
    )
    assert "subprocess." not in allowed_removed
    assert 'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}' in source
    assert "start_new_session=True" in source
    for drift in (
        "\nos.system('unsafe')\n",
        "\nsubprocess.call(['unsafe'])\n",
        "\nimport requests\n",
        "\nimport httpx\n",
    ):
        assert not is_exact_portable_evidence_helper_subprocess_site(
            rel_path=rel,
            source=source + drift,
            fragment="subprocess.run(",
        )


def test_foundation_gate_criteria_include_m7_policy_only_surface() -> None:
    criteria = default_foundation_gate_criteria()
    by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert {
        "m7_modules_present",
        "model_router_decision_only",
        "cost_governor_blocks_over_budget",
        "m7_arbitrary_approval_ref_rejected",
        "m7_context_budget_exhaustion_blocks_route",
        "m7_soft_budget_warning_allows_route",
        "m7_hard_budget_denies_route",
        "m7_cost_warnings_visible_in_route_decision",
    }.issubset(by_id)


def test_foundation_gate_evaluator_passes_m7_policy_only_checks(
    foundation_gate_results: Any,
) -> None:
    assert (
        foundation_gate_results["m7_modules_present"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["model_router_decision_only"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["cost_governor_blocks_over_budget"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["m7_arbitrary_approval_ref_rejected"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["m7_context_budget_exhaustion_blocks_route"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["m7_soft_budget_warning_allows_route"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["m7_hard_budget_denies_route"].status
        == FoundationGateStatus.passed
    )
    assert (
        foundation_gate_results["m7_cost_warnings_visible_in_route_decision"].status
        == FoundationGateStatus.passed
    )


def test_m7_does_not_add_runtime_execution_integrations() -> None:
    forbidden = [
        "import openai",
        "import anthropic",
        "import requests",
        "import httpx",
        "subprocess.",
    ]
    allowed_subprocess_path = (
        Path("src") / "ultimate_ai_agent" / "core" / "runtime_gateway" / "command.py"
    )
    allowed_signing_helper_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "evidence_signing"
        / "macos_keychain.py"
    )
    sealed_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "sandbox_calculation"
        / "backend.py"
    )
    matrix_harness_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_harness"
        / "backend.py"
    )
    matrix_session_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_session"
        / "backend.py"
    )
    matrix_cache_crypto_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_sync"
        / "macos_cache_crypto.py"
    )
    matrix_sync_transport_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_sync"
        / "transport.py"
    )
    sources = {
        path: path.read_text(encoding="utf-8")
        for path in (Path("src") / "ultimate_ai_agent" / "core").rglob("*.py")
    }
    command_source = sources.pop(allowed_subprocess_path)
    sealed_source = sources[sealed_subprocess_path]
    matrix_harness_source = sources.pop(matrix_harness_subprocess_path)
    matrix_session_source = sources.pop(matrix_session_subprocess_path)
    matrix_cache_crypto_source = sources.pop(matrix_cache_crypto_subprocess_path)
    matrix_sync_transport_source = sources.pop(matrix_sync_transport_subprocess_path)
    _assert_exact_governed_runtime_command_subprocess_site(command_source)
    signing_source = sources.pop(allowed_signing_helper_path)
    _assert_exact_portable_evidence_helper_subprocess_site(signing_source)
    assert is_exact_sealed_calculation_subprocess_site(
        rel_path=sealed_subprocess_path.as_posix(),
        source=sealed_source,
        fragment="subprocess.run(",
    )
    assert is_exact_matrix_harness_subprocess_site(
        rel_path=matrix_harness_subprocess_path.as_posix(),
        source=matrix_harness_source,
        fragment="subprocess.Popen(",
    )
    assert is_exact_matrix_session_subprocess_site(
        rel_path=matrix_session_subprocess_path.as_posix(),
        source=matrix_session_source,
        fragment="subprocess.Popen(",
    )
    assert is_exact_matrix_session_bounded_filesystem_site(
        rel_path=matrix_session_subprocess_path.as_posix(),
        source=matrix_session_source,
        fragment="Path.home(",
    )
    assert is_exact_matrix_session_bounded_filesystem_site(
        rel_path=matrix_session_subprocess_path.as_posix(),
        source=matrix_session_source,
        fragment='.rglob("*")',
    )
    assert is_exact_matrix_cache_crypto_subprocess_site(
        rel_path=matrix_cache_crypto_subprocess_path.as_posix(),
        source=matrix_cache_crypto_source,
        fragment="subprocess.run(",
    )
    assert is_exact_matrix_sync_transport_subprocess_site(
        rel_path=matrix_sync_transport_subprocess_path.as_posix(),
        source=matrix_sync_transport_source,
        fragment="subprocess.Popen(",
    )
    assert is_exact_sealed_calculation_subprocess_site(
        rel_path=sealed_subprocess_path.as_posix(),
        source=sealed_source,
        fragment="subprocess.Popen(",
    )

    for path, source in sources.items():
        for marker in forbidden:
            if path == sealed_subprocess_path and marker == "subprocess.":
                assert is_exact_sealed_calculation_subprocess_site(
                    rel_path=path.as_posix(),
                    source=source,
                    fragment="subprocess.run(",
                )
                continue
            assert marker not in source


def test_sealed_backend_subprocess_exception_rejects_unrelated_drift() -> None:
    backend_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "sandbox_calculation"
        / "backend.py"
    )
    source = backend_path.read_text(encoding="utf-8")
    drift_markers = (
        "\nimport " + "requests\n",
        "\nsubprocess" + ".call(['unsafe'])\n",
        "\nsp = subprocess\nsp.call(['unsafe'])\n",
        "\ngetattr(subprocess, 'call')(['unsafe'])\n",
        "\nnetwork_access_enabled" + "=True\n",
        "\nos" + ".environ\n",
    )
    for drift in drift_markers:
        assert not is_exact_sealed_calculation_subprocess_site(
            rel_path=backend_path.as_posix(),
            source=source + drift,
            fragment="subprocess.run(",
        )
    assert is_exact_sealed_calculation_forbidden_fragment_exception(
        rel_path=backend_path.as_posix(),
        source=source,
        fragment="import " + "subprocess",
    )
    assert not is_exact_sealed_calculation_forbidden_fragment_exception(
        rel_path=backend_path.as_posix(),
        source=source,
        fragment="import " + "requests",
    )


def test_matrix_harness_subprocess_exception_binds_exact_containment_profile() -> None:
    backend_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_harness"
        / "backend.py"
    )
    rel_path = backend_path.as_posix()
    source = backend_path.read_text(encoding="utf-8")

    assert is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.Popen(",
    )
    assert not is_exact_matrix_harness_subprocess_site(
        rel_path="src/ultimate_ai_agent/core/unrelated.py",
        source=source,
        fragment="subprocess.Popen(",
    )
    assert is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.run(",
    )

    critical_markers = (
        "MATRIX_HARNESS_DOCKER_BINARY_ABSOLUTE_REQUIRED",
        "MATRIX_HARNESS_DOCKER_BINARY_UNSAFE",
        '"--project-name",\n            "uaa-matrix-harness",',
        '"--pull",\n                "never",',
        '_MATRIX_HARNESS_SPAWN_GATE = """',
        "token = os.read(gate_fd, 1)",
        "liveness_fd = int(sys.argv[2])",
        "watchdog_pid = os.fork()",
        "if not os.read(liveness_fd, 1):",
        "os.killpg(os.getpgrp(), signal.SIGTERM)",
        "os.killpg(os.getpgrp(), signal.SIGKILL)",
        "gate_read_fd, gate_write_fd = os.pipe()",
        "liveness_read_fd, liveness_write_fd = os.pipe()",
        "pass_fds=(gate_read_fd, liveness_read_fd)",
        "self._capture_process_group(process)",
        "self._process_liveness_write_fds[process] = liveness_write_fd",
        "inventory = self._process_group_inventory(process, process_group_id)",
        "self._signal_process_group(process_group_id, signal.SIGTERM)",
        "self._signal_process_group(process_group_id, signal.SIGKILL)",
        "result = subprocess.run(",
        '"/bin/ps",',
        '"pid=,pgid=,uid=,stat=",',
        "MATRIX_HARNESS_PROCESS_INVENTORY_TIMEOUT_SECONDS = 1.0",
        "MATRIX_HARNESS_PROCESS_INVENTORY_LIMIT_BYTES = 16 * 1024",
        "MATRIX_HARNESS_PROCESS_GROUP_MEMBER_LIMIT = 64",
        'cwd="/"',
        'env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}',
        "check=False",
        "start_new_session=True",
        "shell=False",
        "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES = 64 * 1024",
        "if total_bytes > MATRIX_HARNESS_OUTPUT_LIMIT_BYTES:",
    )
    for marker in critical_markers:
        assert marker in source
        assert not is_exact_matrix_harness_subprocess_site(
            rel_path=rel_path,
            source=source.replace(marker, ""),
            fragment="subprocess.Popen(",
        )

    assert not is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source + "\nsubprocess.Popen(['unsafe'])\n",
        fragment="subprocess.Popen(",
    )
    assert not is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source + "\nsubprocess.run(['unsafe'])\n",
        fragment="subprocess.run(",
    )
    for unsafe_attribute in (
        "subprocess.getoutput('unsafe')",
        "subprocess.getstatusoutput('unsafe')",
        "extra_pipe = subprocess.PIPE",
    ):
        assert not is_exact_matrix_harness_subprocess_site(
            rel_path=rel_path,
            source=source + f"\n{unsafe_attribute}\n",
            fragment="subprocess.Popen(",
        )

    capture_line = "            self._capture_process_group(process)\n"
    release_block = (
        '            if os.write(gate_write_fd, b"1") != 1:\n'
        "                raise _MatrixHarnessCleanupError(\n"
        '                    "MATRIX_HARNESS_SPAWN_GATE_RELEASE_UNCONFIRMED"\n'
        "                )\n"
    )
    assert capture_line in source
    assert release_block in source
    release_before_capture = source.replace(
        capture_line,
        "",
        1,
    ).replace(release_block, release_block + capture_line, 1)
    assert release_before_capture != source
    assert not is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=release_before_capture,
        fragment="subprocess.Popen(",
    )
    semantic_keyword_mutations = (
        (
            "start_new_session=True",
            "start_new_session=False  # start_new_session=True",
        ),
        (
            "pass_fds=(gate_read_fd, liveness_read_fd)",
            "pass_fds=()  # pass_fds=(gate_read_fd, liveness_read_fd)",
        ),
        ("shell=False", "shell=True  # shell=False"),
        (
            "stdin=subprocess.DEVNULL",
            "stdin=subprocess.PIPE  # stdin=subprocess.DEVNULL",
        ),
    )
    for reviewed, unsafe in semantic_keyword_mutations:
        mutated = source.replace(reviewed, unsafe, 1)
        assert mutated != source
        assert not is_exact_matrix_harness_subprocess_site(
            rel_path=rel_path,
            source=mutated,
            fragment="subprocess.Popen(",
        )
    gate_semantic_mutations = (
        ('if token != b"1":', 'if False:  # if token != b"1":'),
        (
            "if not os.read(liveness_fd, 1):",
            "if False:  # if not os.read(liveness_fd, 1):",
        ),
        (
            "os.killpg(os.getpgrp(), signal.SIGKILL)",
            "pass  # os.killpg(os.getpgrp(), signal.SIGKILL)",
        ),
        (
            "os.execve(sys.argv[3], sys.argv[3:], os.environ)",
            "os._exit(0)  # os.execve(sys.argv[3], sys.argv[3:], os.environ)",
        ),
    )
    for reviewed, unsafe in gate_semantic_mutations:
        mutated = source.replace(reviewed, unsafe, 1)
        assert mutated != source
        assert not is_exact_matrix_harness_subprocess_site(
            rel_path=rel_path,
            source=mutated,
            fragment="subprocess.Popen(",
        )
    runtime_containment_mutations = (
        (
            "            self._capture_process_group(process)",
            "            if False:\n                self._capture_process_group(process)",
        ),
        (
            "            with self._process_group_lock:\n"
            "                self._process_liveness_write_fds[process] = liveness_write_fd",
            "            if False:\n"
            "                with self._process_group_lock:\n"
            "                    self._process_liveness_write_fds[process] = liveness_write_fd",
        ),
        (
            "        self._signal_process_group(process_group_id, signal.SIGKILL)",
            "        pass  # self._signal_process_group("
            "process_group_id, signal.SIGKILL)",
        ),
        (
            "                    if total_bytes > MATRIX_HARNESS_OUTPUT_LIMIT_BYTES:",
            "                    if False:  # if total_bytes > "
            "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES:",
        ),
    )
    for reviewed, unsafe in runtime_containment_mutations:
        mutated = source.replace(reviewed, unsafe, 1)
        assert mutated != source
        assert not is_exact_matrix_harness_subprocess_site(
            rel_path=rel_path,
            source=mutated,
            fragment="subprocess.Popen(",
        )


def test_matrix_sync_subprocess_exception_binds_permission_and_cleanup_profile() -> (
    None
):
    transport_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_sync"
        / "transport.py"
    )
    rel_path = transport_path.as_posix()
    source = transport_path.read_text(encoding="utf-8")
    assert is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.Popen(",
    )

    critical_markers = (
        '"--permission"',
        'f"--allow-fs-read={runtime_snapshot.adapter_root}"',
        "os.killpg(process.pid, signal.SIGTERM)",
        "os.killpg(process.pid, signal.SIGKILL)",
        "process.wait(timeout=grace_seconds)",
        'getattr(process, "stdin", None)',
        'getattr(process, "stdout", None)',
        'getattr(process, "stderr", None)',
        "stream.close()",
    )
    for marker in critical_markers:
        assert marker in source
        assert not is_exact_matrix_sync_transport_subprocess_site(
            rel_path=rel_path,
            source=source.replace(marker, "", 1),
            fragment="subprocess.Popen(",
        )

    assert not is_exact_matrix_sync_transport_subprocess_site(
        rel_path=rel_path,
        source=source.replace(
            '"--permission"',
            '"--allow-child-process"',
            1,
        ),
        fragment="subprocess.Popen(",
    )
    for forbidden_permission in (
        '"--allow-worker"',
        '"--allow-addons"',
        '"NODE_OPTIONS"',
    ):
        assert not is_exact_matrix_sync_transport_subprocess_site(
            rel_path=rel_path,
            source=source + f"\n{forbidden_permission}\n",
            fragment="subprocess.Popen(",
        )


def test_matrix_session_subprocess_exception_rejects_decoy_permission_markers() -> (
    None
):
    backend_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_session"
        / "backend.py"
    )
    rel_path = backend_path.as_posix()
    source = backend_path.read_text(encoding="utf-8")
    assert is_exact_matrix_session_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.Popen(",
    )
    mutations = (
        source.replace(
            '"--permission"',
            '"--no-permission"  # "--permission"',
            1,
        ),
        source.replace(
            'f"--allow-fs-read={runtime_snapshot.adapter_root}"',
            '"--allow-fs-read=/"  # '
            'f"--allow-fs-read={runtime_snapshot.adapter_root}"',
            1,
        ),
        source.replace(
            "start_new_session=True",
            "start_new_session=False  # start_new_session=True",
            1,
        ),
    )
    for mutated in mutations:
        assert mutated != source
        assert not is_exact_matrix_session_subprocess_site(
            rel_path=rel_path,
            source=mutated,
            fragment="subprocess.Popen(",
        )


def test_matrix_session_filesystem_exception_binds_all_reviewed_tree_scans() -> None:
    backend_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_session"
        / "backend.py"
    )
    rel_path = backend_path.as_posix()
    source = backend_path.read_text(encoding="utf-8")
    assert source.count('.rglob("*")') == 3
    assert is_exact_matrix_session_bounded_filesystem_site(
        rel_path=rel_path,
        source=source,
        fragment='.rglob("*")',
    )

    critical_markers = (
        "os.chmod(path, 0o500 if path.is_dir() else 0o400)",
        "if len(entries) > 100_000:",
        "not (stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode))",
        "metadata.st_uid != os.getuid()",
        "metadata.st_mode & 0o022",
        "_require_safe_regular_file(path)",
        "relative = path.relative_to(root).as_posix().encode()",
        "shutil.rmtree(root)",
    )
    for marker in critical_markers:
        assert marker in source
        assert not is_exact_matrix_session_bounded_filesystem_site(
            rel_path=rel_path,
            source=source.replace(marker, "", 1),
            fragment='.rglob("*")',
        )

    assert not is_exact_matrix_session_bounded_filesystem_site(
        rel_path=rel_path,
        source=source + '\nPath("/").rglob("*")\n',
        fragment='.rglob("*")',
    )


def test_matrix_cache_crypto_subprocess_exception_rejects_decoys_and_extra_calls() -> (
    None
):
    helper_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "communications"
        / "matrix_sync"
        / "macos_cache_crypto.py"
    )
    rel_path = helper_path.as_posix()
    source = helper_path.read_text(encoding="utf-8")
    assert is_exact_matrix_cache_crypto_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment="subprocess.run(",
    )
    mutations = (
        source + "\nsubprocess.getoutput('unsafe')\n",
        source.replace(
            "shell=False",
            "shell=bool(1)  # shell=False",
            1,
        ),
        source.replace(
            "start_new_session=True",
            "start_new_session=False  # start_new_session=True",
            1,
        ),
    )
    for mutated in mutations:
        assert mutated != source
        assert not is_exact_matrix_cache_crypto_subprocess_site(
            rel_path=rel_path,
            source=mutated,
            fragment="subprocess.run(",
        )
