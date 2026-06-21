from typing import Any
from pathlib import Path

import pytest

from ultimate_ai_agent.core.gate import FoundationGateStatus, default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import (
    M151_LOCAL_OPENWEBUI_TEST_ROUTES,
    m152_local_model_management_forbidden_fragment_failures,
    m152_openapi_route_failures,
)
from ultimate_ai_agent.core.local_model_management import (
    FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS,
    SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS,
    FutureLiveContractStatus,
    FutureLiveLocalModelCapabilityKind,
    LocalModelManagementLane,
    build_future_live_local_model_contract,
    build_local_model_management_m153_m165_progression_plan,
    build_m160_m165_disabled_future_live_contracts,
    build_m161_m165_disabled_future_live_contracts,
    build_m162_m165_disabled_future_live_contracts,
    build_m163_m165_disabled_future_live_contracts,
    validate_future_live_local_model_contract,
    validate_local_model_management_m153_m165_progression_plan,
)


def test_m153_m165_progression_gate_criterion_is_registered_and_passes(
    foundation_gate_results: Any,
) -> None:
    criteria = default_foundation_gate_criteria()
    criterion_ids = {criterion.criterion_id for criterion in criteria}
    criterion_id = "m153_m165_local_model_management_progression"

    assert criterion_id in criterion_ids
    assert foundation_gate_results[criterion_id].status == FoundationGateStatus.passed


def test_m153_m165_exact_checkpoint_refs_and_lanes() -> None:
    assert SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == tuple(
        f"checkpoint:m{index}" for index in range(153, 160)
    )
    assert LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == (
        "checkpoint:m160",
        "checkpoint:m161",
    )
    assert LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == ("checkpoint:m162",)
    assert LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == ("checkpoint:m163",)
    assert LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == ("checkpoint:m164",)
    assert LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == ("checkpoint:m165",)
    assert FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS == ()
    assert REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS == tuple(
        f"checkpoint:m{index}" for index in range(153, 166)
    )

    plan = validate_local_model_management_m153_m165_progression_plan(
        build_local_model_management_m153_m165_progression_plan()
    )

    assert plan.accepted_checkpoint_refs == list(REQUIRED_LOCAL_MODEL_MANAGEMENT_M153_M165_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.safe_contract
    ] == list(SAFE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.live_bounded_read_only
    ] == list(LIVE_READ_ONLY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.live_exact_approved_acquisition
    ] == list(LIVE_MODEL_ACQUISITION_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.live_llama_cpp_supervisor
    ] == list(LIVE_LLAMA_CPP_SUPERVISOR_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.live_openai_gateway
    ] == list(LIVE_OPENAI_GATEWAY_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.live_settings_tuning
    ] == list(LIVE_SETTINGS_TUNING_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert [
        contract.milestone_ref
        for contract in plan.milestone_contracts
        if contract.lane == LocalModelManagementLane.future_live_contract_only
    ] == list(FUTURE_LIVE_LANE_LOCAL_MODEL_MANAGEMENT_CHECKPOINT_REFS)
    assert plan.live_capability_authorized is False
    assert plan.network_access_performed is False
    assert plan.model_download_performed is False
    assert plan.llama_cpp_server_started is False
    assert plan.model_call_performed is False
    assert plan.settings_applied is False


def test_m163_m165_future_live_contracts_are_complete_no_pending_disabled_records() -> None:
    contracts = build_m163_m165_disabled_future_live_contracts()

    assert contracts == []
    for contract in contracts:
        validated = validate_future_live_local_model_contract(contract)
        assert validated.status == FutureLiveContractStatus.disabled_until_runtime_milestone
        assert validated.approval_refs_are_identifiers_only is True
        assert validated.live_capability_authorized is False
        assert validated.network_access_performed is False
        assert validated.local_system_probe_performed is False
        assert validated.download_performed is False
        assert validated.model_cache_write_performed is False
        assert validated.llama_cpp_import_performed is False
        assert validated.subprocess_execution_performed is False
        assert validated.server_started is False
        assert validated.prompt_processed is False
        assert validated.model_call_performed is False
        assert validated.settings_applied is False
        assert validated.runtime_restart_performed is False
        assert validated.backend_route_added is False
        assert validated.control_center_control_added is False
        assert validated.openwebui_settings_mutation_requested is False
        assert validated.openwebui_privileged_management_used is False
        assert validated.openwebui_plugin_added is False
        assert validated.openwebui_is_agent_brain is False
        assert validated.memory_write_performed is False
        assert validated.context_injection_performed is False
        assert validated.tool_execution_performed is False
        assert validated.production_authority_granted is False


def test_m160_m165_disabled_contract_builder_remains_m163_m165_compat_alias() -> None:
    assert [
        contract.contract_ref for contract in build_m160_m165_disabled_future_live_contracts()
    ] == [
        contract.contract_ref for contract in build_m163_m165_disabled_future_live_contracts()
    ]
    assert [
        contract.contract_ref for contract in build_m161_m165_disabled_future_live_contracts()
    ] == [
        contract.contract_ref for contract in build_m163_m165_disabled_future_live_contracts()
    ]
    assert [
        contract.contract_ref for contract in build_m162_m165_disabled_future_live_contracts()
    ] == [
        contract.contract_ref for contract in build_m163_m165_disabled_future_live_contracts()
    ]


@pytest.mark.parametrize(
    "update,reason",
    [
        ({"network_access_performed": True}, "M160_NETWORK_ACCESS_DENIED"),
        ({"local_system_probe_performed": True}, "M161_LOCAL_SYSTEM_PROBE_DENIED"),
        ({"download_performed": True}, "M162_MODEL_DOWNLOAD_DENIED"),
        ({"server_started": True}, "M163_LLAMA_CPP_SERVER_DENIED"),
        ({"model_call_performed": True}, "M164_MODEL_CALL_DENIED"),
        ({"settings_applied": True}, "M165_SETTINGS_APPLY_DENIED"),
        ({"openwebui_privileged_management_used": True}, "M164_OPENWEBUI_ADMIN_API_DENIED"),
        ({"openwebui_is_agent_brain": True}, "M164_OPENWEBUI_AUTHORITY_DENIED"),
    ],
)
def test_m160_m165_future_live_contracts_deny_live_mutations(update: Any, reason: str) -> None:
    contract = build_future_live_local_model_contract(
        contract_ref="future-live-contract:m164-openai-gateway",
        capability_kind=FutureLiveLocalModelCapabilityKind.openai_gateway,
        approval_ref="approval:m164-openai-gateway-reviewed-only",
        safe_summary="Record future UAA local gateway guidance only.",
    )

    with pytest.raises(ValueError, match=reason):
        validate_future_live_local_model_contract(contract.model_copy(update=update))


def test_m160_m165_approval_ref_is_not_runtime_authority() -> None:
    with pytest.raises(ValueError, match="M160_M165_APPROVAL_REF_NOT_AUTHORITY"):
        build_future_live_local_model_contract(
            contract_ref="future-live-contract:m160-hf-search",
            capability_kind=FutureLiveLocalModelCapabilityKind.hf_search,
            approval_ref="approval_test_m160-hf-search",
            safe_summary="Unsafe test approval ref.",
        )


def test_m153_m165_progression_docs_exist_and_name_every_checkpoint() -> None:
    docs = [
        Path("docs/model_management/M153_M165_LOCAL_MODEL_MANAGEMENT_PROGRESSION.md"),
        Path("docs/model_management/M160_M165_LIVE_LANE_BOUNDARY.md"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in docs)

    for index in range(153, 166):
        assert f"m{index}" in text
    assert "safe_contract" in text
    assert "live_bounded_read_only" in text
    assert "future_live_contract_only" in text
    assert "m160 live bounded read-only hf gguf search only" in text
    assert "m161 live bounded read-only local system capability probing only" in text
    assert "m162 live exact-approved gguf acquisition only" in text
    assert "m163 live loopback llama.cpp supervisor only" in text
    assert "m164 live local `/v1` gateway only" in text
    assert "m165 live approved settings tuning only" in text


def test_m153_m165_route_boundary_rejects_future_live_routes() -> None:
    assert not m152_openapi_route_failures(
        M151_LOCAL_OPENWEBUI_TEST_ROUTES,
        expected_path_count=0,
    )
    failures = m152_openapi_route_failures(
        {
            *M151_LOCAL_OPENWEBUI_TEST_ROUTES,
            "/hf/search",
            "/hardware/probe",
            "/models/download",
            "/llama-cpp/server",
            "/llama-cpp/settings/apply",
            "/v1/responses",
            "/control-center/local-models/start",
        },
        expected_path_count=0,
    )

    for route in [
        "/hf/search",
        "/hardware/probe",
        "/models/download",
        "/llama-cpp/server",
        "/llama-cpp/settings/apply",
        "/v1/responses",
        "/control-center/local-models/start",
    ]:
        assert any(route in failure for failure in failures)


def test_m153_m165_static_safety_detects_future_live_fragments(tmp_path: Path) -> None:
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
        "from huggingface_hub import HfApi\n"
        "HfApi().list_models()\n"
        "platform.uname()\n"
        "subprocess.check_output(['sysctl'])\n"
        "llama_cpp.Llama(model_path='x')\n"
        "openai.OpenAI()\n"
        "settings_applied=True\n",
        encoding="utf-8",
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\ndependencies = ["huggingface-hub"]\n', encoding="utf-8")

    failures = m152_local_model_management_forbidden_fragment_failures(tmp_path)

    for fragment in [
        "from huggingface_hub import",
        "HfApi().list_models",
        "platform.uname(",
        "subprocess.check_output(",
        "llama_cpp.Llama(",
        "openai.OpenAI(",
        "settings_applied=True",
        "huggingface-hub",
    ]:
        assert any(fragment in failure for failure in failures)
