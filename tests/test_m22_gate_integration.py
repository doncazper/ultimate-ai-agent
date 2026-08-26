from pathlib import Path
from ultimate_ai_agent.core.gate import (
    FoundationGateEvaluator,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluators import (
    EXPECTED_M22_OPENAPI_PATH_COUNT,
    M22_FORBIDDEN_BACKEND_ROUTES,
    TASK_DECOMPOSITION_CANONICAL_ROUTES,
    m22_local_runtime_forbidden_fragment_failures,
    m22_openapi_route_failures,
)
from scripts.verify_all import find_m22_local_runtime_forbidden_fragment_failures


def test_m22_local_runtime_activation_contract_criterion_exists_and_passes() -> None:
    criteria = default_foundation_gate_criteria()
    criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}

    assert "m22_local_model_runtime_activation_contract_safe" in criteria_by_id
    criterion = criteria_by_id["m22_local_model_runtime_activation_contract_safe"]
    assert "contract-only" in criterion.pass_condition
    assert "no model was called" in criterion.pass_condition
    assert "no runtime was activated" in criterion.pass_condition
    assert "OpenAPI path count at 78" in criterion.pass_condition
    assert "M23 planned" in criterion.pass_condition

    report = FoundationGateEvaluator().evaluate([criterion])

    assert report.failed_count == 0
    assert report.passed_count == 1


def test_m22_openapi_route_guard_rejects_activation_or_probe_routes() -> None:
    failures = m22_openapi_route_failures(
        {
            "/health",
            "/runtime/activate",
            "/runtime/probe",
            "/runtime/local/activate",
            "/model-runtime/activate",
            "/model-runtime/probe",
            "/model-runtime/local/call",
        },
        expected_path_count=EXPECTED_M22_OPENAPI_PATH_COUNT,
    )

    assert EXPECTED_M22_OPENAPI_PATH_COUNT == 80
    assert "/runtime/activate" in M22_FORBIDDEN_BACKEND_ROUTES
    assert "/model-runtime/probe" in M22_FORBIDDEN_BACKEND_ROUTES
    assert "/model-runtime/local/call" in M22_FORBIDDEN_BACKEND_ROUTES
    assert any("OpenAPI path count" in failure for failure in failures)
    assert any("/runtime/activate" in failure for failure in failures)
    assert any("/model-runtime/local/call" in failure for failure in failures)


def test_m22_route_guard_allows_exact_task_decomposition_canonical_surface() -> None:
    historical_paths = {
        f"/historical-contract-path-{index}"
        for index in range(EXPECTED_M22_OPENAPI_PATH_COUNT)
    }
    current_paths = historical_paths | set(TASK_DECOMPOSITION_CANONICAL_ROUTES)

    assert m22_openapi_route_failures(current_paths) == []

    failures = m22_openapi_route_failures(
        current_paths | {"/task-decomposition/unreviewed-route"}
    )

    assert any("OpenAPI path count" in failure for failure in failures)


def test_m22_route_guard_allows_exact_news_signals_read_surface_only() -> None:
    historical_paths = {
        f"/historical-contract-path-{index}"
        for index in range(EXPECTED_M22_OPENAPI_PATH_COUNT)
    }
    current_paths = historical_paths | {"/control-center/news-signals/summary"}

    assert m22_openapi_route_failures(current_paths) == []

    failures = m22_openapi_route_failures(
        current_paths | {"/control-center/news-signals/unreviewed-route"}
    )

    assert any("OpenAPI path count" in failure for failure in failures)


def test_m22_gate_scans_local_runtime_contract_sources_for_forbidden_fragments(
    tmp_path: Path,
) -> None:
    source_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "model_runtime"
        / "runtime_client.py"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "import ollama\nclient.generate('hello')\n", encoding="utf-8"
    )

    failures = m22_local_runtime_forbidden_fragment_failures(tmp_path)

    assert any(
        "src/ultimate_ai_agent/core/model_runtime/runtime_client.py" in failure
        for failure in failures
    )
    assert any("import ollama" in failure for failure in failures)


def test_m22_gate_scan_allows_harmless_get_method_usage(tmp_path: Path) -> None:
    source_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "model_runtime"
        / "metadata_contract.py"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "def read_ref(metadata):\n    return metadata.get('runtime_profile_ref')\n",
        encoding="utf-8",
    )

    failures = m22_local_runtime_forbidden_fragment_failures(tmp_path)

    assert failures == []


def test_m22_gate_scan_blocks_qualified_runtime_network_calls(tmp_path: Path) -> None:
    source_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "model_runtime"
        / "runtime_client.py"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "import requests\n"
        "requests.get('http://localhost:11434/api/generate')\n"
        "ollama.generate(model='demo')\n",
        encoding="utf-8",
    )

    failures = m22_local_runtime_forbidden_fragment_failures(tmp_path)

    assert any("requests.get(" in failure for failure in failures)
    assert any("ollama.generate(" in failure for failure in failures)


def test_verify_all_m22_helper_matches_gate_scan(tmp_path: Path) -> None:
    source_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "model_runtime"
        / "runtime_client.py"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "import httpx\nhttpx.post('http://localhost')\n", encoding="utf-8"
    )

    failures = find_m22_local_runtime_forbidden_fragment_failures(tmp_path)

    assert any(
        "src/ultimate_ai_agent/core/model_runtime/runtime_client.py" in failure
        for failure in failures
    )
    assert any("import httpx" in failure for failure in failures)


def test_verify_all_m22_helper_allows_harmless_get_method_usage(tmp_path: Path) -> None:
    source_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "model_runtime"
        / "metadata_contract.py"
    )
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        "def read_ref(metadata):\n    return metadata.get('runtime_profile_ref')\n",
        encoding="utf-8",
    )

    failures = find_m22_local_runtime_forbidden_fragment_failures(tmp_path)

    assert failures == []
