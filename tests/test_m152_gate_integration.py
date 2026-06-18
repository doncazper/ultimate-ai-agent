from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    M151_LOCAL_OPENWEBUI_TEST_ROUTES,
    m152_local_model_management_forbidden_fragment_failures,
    m152_openapi_route_failures,
)


def test_m152_gate_criteria_are_registered_and_pass(foundation_gate_results) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    expected = [
        "m152_local_model_management_contracts",
        "m152_local_model_management_static_safety",
        "m152_local_model_management_route_boundary",
    ]

    for criterion_id in expected:
        assert criterion_id in criterion_ids
        assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m152_route_boundary_allows_only_existing_m151_smoke_routes() -> None:
    assert not m152_openapi_route_failures(
        M151_LOCAL_OPENWEBUI_TEST_ROUTES,
        expected_path_count=0,
    )
    failures = m152_openapi_route_failures(
        {
            *M151_LOCAL_OPENWEBUI_TEST_ROUTES,
            "/local-models/download",
            "/models/load",
            "/control-center/local-models/execute",
        },
        expected_path_count=0,
    )

    assert any("/local-models/download" in failure for failure in failures)
    assert any("/models/load" in failure for failure in failures)
    assert any("/control-center/local-models/execute" in failure for failure in failures)


def test_m152_static_safety_detects_future_live_runtime_fragments(tmp_path: Path) -> None:
    unsafe_file = (
        tmp_path
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "local_model_management"
        / "unsafe.py"
    )
    unsafe_file.parent.mkdir(parents=True)
    unsafe_file.write_text(
        "import subprocess\n"
        "from huggingface_hub import HfApi\n"
        "model_download_enabled=True\n",
        encoding="utf-8",
    )

    failures = m152_local_model_management_forbidden_fragment_failures(tmp_path)

    assert any("import subprocess" in failure for failure in failures)
    assert any("from huggingface_hub import" in failure for failure in failures)
    assert any("model_download_enabled=True" in failure for failure in failures)


def test_m152_static_safety_detects_forbidden_dependencies(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies = ["llama-cpp-python"]\n', encoding="utf-8")

    failures = m152_local_model_management_forbidden_fragment_failures(tmp_path)

    assert any("llama-cpp-python" in failure for failure in failures)
