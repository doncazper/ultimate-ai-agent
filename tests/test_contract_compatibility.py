from datetime import UTC, datetime

from pydantic import ValidationError

from tests.test_kernel_minimum_lovable_happy_path import actor, consent, request

from ultimate_ai_agent.core.adapters import AgentRuntimeAdapterManifest
from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.contracts import ContextPack, ExecutionContract
from ultimate_ai_agent.core.contracts.enums import AgentMode, RiskLevel
from ultimate_ai_agent.core.files import FileKind, FileRef, FileSensitivity
from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.hygiene.temporal_context import FreshnessClass, StalenessPolicy, TemporalContext
from ultimate_ai_agent.core.kernel import KernelTaskResult, KernelTaskStatus
from ultimate_ai_agent.core.ledger import DeterministicRunState, EventLedgerEvent, RunState
from ultimate_ai_agent.core.ledger.enums import EventName
from ultimate_ai_agent.core.memory import MemoryRecord
from ultimate_ai_agent.core.memory.enums import MemoryAuthority, MemoryScope, MemorySensitivity, MemoryType
from ultimate_ai_agent.core.providers import (
    ProviderCapability,
    ProviderDomain,
    ProviderManifest,
)
from ultimate_ai_agent.core.secrets import CredentialReference
from ultimate_ai_agent.core.secrets.enums import CredentialAuthType, CredentialScope
from ultimate_ai_agent.core.tools import ToolCategory, ToolExecutionMode, ToolManifest, ToolRiskLevel
from ultimate_ai_agent.core.truth import EvidenceManifest, TruthSourceManifest
from ultimate_ai_agent.core.truth.enums import TruthAuthorityLevel, TruthSourceType
from ultimate_ai_agent.core.world_state import StructuredWorldState, WorldStateStep


def temporal_context() -> TemporalContext:
    return TemporalContext(
        current_time_utc=datetime.now(UTC),
        user_timezone="UTC",
        freshness_class=FreshnessClass.static,
        staleness_policy=StalenessPolicy.allow_with_label,
    )


def test_core_public_contracts_remain_instantiable_and_serializable(tmp_path):
    result_envelope = ResultEnvelope(
        success=True,
        operation="contract_compatibility",
        service="ContractTest",
        trace_id="trace_contract",
        data={"ok": True},
    )
    error_envelope = ErrorEnvelope(
        code="VALIDATION_FAILED",
        category=ErrorCategory.validation_error,
        safe_message="Validation failed safely.",
        severity=Severity.low,
        retryable=False,
        details_redacted=True,
        source="ContractTest",
    )
    contract = ExecutionContract(
        contract_id="ec_contract_compat",
        run_id="run_contract",
        workspace_id="workspace_contract",
        user_id="user_123",
        request_summary="Validate public contracts.",
        goal="Keep schemas compatible.",
        deliverable="Contract instances.",
        mode=AgentMode.answer,
        risk_level=RiskLevel.low,
        acceptance_criteria=["instances serialize"],
    )
    context_pack = ContextPack(
        context_pack_id="cp_contract_compat",
        run_id="run_contract",
        contract_id=contract.contract_id,
        workspace_id="workspace_contract",
        user_id="user_123",
        active_goal="Keep schemas compatible.",
        token_budget=1000,
    )
    event = EventLedgerEvent(
        event_id="evt_contract",
        event_type="contract",
        event_name=EventName.run_created,
        run_id="run_contract",
        trace_id="trace_contract",
        span_id="span_contract",
        correlation_id="corr_contract",
        actor_context=actor(),
        temporal_context=temporal_context(),
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="contract_test",
        ),
        event_source="contract_test",
        subject="run",
        action="create",
        outcome="created",
        status="ok",
        severity="info",
    )
    run_state = DeterministicRunState(run_id="run_contract", current_state=RunState.created)
    world_state = StructuredWorldState(
        world_state_id="ws_contract",
        run_id="run_contract",
        current_phase="verification",
        current_step="contract_compatibility",
        completed_steps=[WorldStateStep(step_id="step_contract", step_type="test", event_ids=[event.event_id])],
        last_event_id=event.event_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    budget = ContextBudget(model_context_limit=8000)
    runtime_manifest = __import__(
        "ultimate_ai_agent.core.runtime",
        fromlist=["LocalModelProfile", "LocalRuntimeManifest"],
    )
    local_runtime = runtime_manifest.LocalRuntimeManifest(
        runtime_id="runtime_contract",
        runtime_type="local_mock",
        model_profile=runtime_manifest.LocalModelProfile(model_id="local-model", context_window=8000),
    )
    adapter = AgentRuntimeAdapterManifest(
        adapter_id="adapter_contract",
        adapter_type="sdk_placeholder",
        version="0.0.0",
    )
    credential = CredentialReference(
        credential_ref="cred_contract",
        auth_type=CredentialAuthType.api_key,
        scope=CredentialScope.provider,
    )
    tool = ToolManifest(
        tool_id="file.write.contract",
        display_name="File Write Contract",
        category=ToolCategory.file,
        description="Contract-only tool manifest.",
        execution_mode=ToolExecutionMode.local_dev,
        risk_level=ToolRiskLevel.low,
        capability_flag="file_write_contract",
        owner="test",
        source="test",
        version="0.0.0",
    )
    provider = ProviderManifest(
        provider_id="provider_contract",
        display_name="Provider Contract",
        domain=ProviderDomain.generic,
        capabilities=[ProviderCapability.generic_query],
        owner="test",
        source="test",
        version="0.0.0",
    )
    memory = MemoryRecord(
        memory_id="mem_contract",
        memory_type=MemoryType.semantic,
        scope=MemoryScope.project,
        authority=MemoryAuthority.user_provided,
        sensitivity=MemorySensitivity.project_private,
        content="Memory remains recall, not authority.",
    )
    file_ref = FileRef(
        file_ref="file_contract",
        path="notes/contract.md",
        kind=FileKind.generated,
        sensitivity=FileSensitivity.project_private,
    )
    truth_source = TruthSourceManifest(
        source_id="truth_contract",
        source_type=TruthSourceType.canonical_file,
        authority_level=TruthAuthorityLevel.authoritative,
        display_name="Canonical Contract",
        owner="test",
        data_classification="project_private",
    )
    evidence = EvidenceManifest(manifest_id="evidence_contract", run_id="run_contract")
    kernel_request = request(tmp_path)
    kernel_result = KernelTaskResult(
        result_id="ktr_contract_result",
        run_id="run_contract",
        success=True,
        status=KernelTaskStatus.completed,
        safe_message="Contract result serialized.",
    )

    payloads = [
        result_envelope,
        error_envelope,
        actor(),
        temporal_context(),
        contract,
        context_pack,
        event,
        run_state,
        world_state,
        budget,
        local_runtime,
        adapter,
        consent(),
        tool,
        credential,
        provider,
        memory,
        file_ref,
        truth_source,
        evidence,
        kernel_request,
        kernel_result,
    ]

    for payload in payloads:
        serialized = payload.model_dump(mode="json")
        assert "raw_secret" not in serialized
        assert "secret_value" not in serialized

    assert contract.schema_version.endswith(".v0")
    assert context_pack.schema_version.endswith(".v0")
    assert event.event_version.endswith(".v0")
    assert run_state.schema_version.endswith(".v0")
    assert world_state.schema_version.endswith(".v0")
    assert "0.10.0" not in {
        contract.schema_version,
        context_pack.schema_version,
        event.event_version,
        run_state.schema_version,
        world_state.schema_version,
    }


def test_strict_public_models_reject_extra_fields(tmp_path):
    strict_cases = [
        (ResultEnvelope, {"success": True, "operation": "op", "service": "svc", "trace_id": "trace", "extra": True}),
        (ExecutionContract, {
            "contract_id": "ec_extra",
            "run_id": "run_extra",
            "workspace_id": "workspace",
            "user_id": "user",
            "request_summary": "x",
            "goal": "x",
            "deliverable": "x",
            "mode": AgentMode.answer,
            "acceptance_criteria": ["x"],
            "extra": True,
        }),
        (EvidenceManifest, {"manifest_id": "evm_extra", "run_id": "run_extra", "extra": True}),
        (type(request(tmp_path)), request(tmp_path).model_dump() | {"extra": True}),
    ]

    for model, payload in strict_cases:
        try:
            model(**payload)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"{model.__name__} accepted an unknown field")
