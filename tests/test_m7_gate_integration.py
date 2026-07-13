from typing import Any
from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.sandbox_calculation.static_safety import (
    is_exact_sealed_calculation_forbidden_fragment_exception,
    is_exact_sealed_calculation_subprocess_site,
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
    assert source.count("subprocess.run(") == 1
    assert source.count("subprocess.TimeoutExpired") == 1
    assert "shell=False" in source
    assert "shell=True" not in source
    assert "subprocess.Popen(" not in source
    assert source.count("subprocess.PIPE") == 2
    allowed_removed = source.replace("subprocess.run(", "").replace(
        "subprocess.TimeoutExpired", ""
    ).replace("subprocess.PIPE", "")
    assert "subprocess." not in allowed_removed
    assert 'env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"}' in source
    assert "start_new_session=True" in source


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


def test_foundation_gate_evaluator_passes_m7_policy_only_checks(foundation_gate_results: Any) -> None:
    assert foundation_gate_results["m7_modules_present"].status == FoundationGateStatus.passed
    assert foundation_gate_results["model_router_decision_only"].status == FoundationGateStatus.passed
    assert foundation_gate_results["cost_governor_blocks_over_budget"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_arbitrary_approval_ref_rejected"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_context_budget_exhaustion_blocks_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_soft_budget_warning_allows_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_hard_budget_denies_route"].status == FoundationGateStatus.passed
    assert foundation_gate_results["m7_cost_warnings_visible_in_route_decision"].status == FoundationGateStatus.passed


def test_m7_does_not_add_runtime_execution_integrations() -> None:
    forbidden = [
        "import openai",
        "import anthropic",
        "import requests",
        "import httpx",
        "subprocess.",
    ]
    allowed_subprocess_path = (
        Path("src")
        / "ultimate_ai_agent"
        / "core"
        / "runtime_gateway"
        / "command.py"
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
    sources = {
        path: path.read_text(encoding="utf-8")
        for path in (Path("src") / "ultimate_ai_agent" / "core").rglob("*.py")
    }
    command_source = sources.pop(allowed_subprocess_path)
    sealed_source = sources[sealed_subprocess_path]
    _assert_exact_governed_runtime_command_subprocess_site(command_source)
    signing_source = sources.pop(allowed_signing_helper_path)
    _assert_exact_portable_evidence_helper_subprocess_site(signing_source)
    assert is_exact_sealed_calculation_subprocess_site(
        rel_path=sealed_subprocess_path.as_posix(),
        source=sealed_source,
        fragment="subprocess.run(",
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
