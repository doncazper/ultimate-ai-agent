from typing import Any
import asyncio

import pytest
from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent.core.capabilities import (
    CapabilityEvent,
    CapabilityPolicy,
    CapabilityRegistry,
    CapabilitySpec,
    RiskLevel,
    tool_capability,
)
from ultimate_ai_agent.core.capabilities.adapters import (
    capability_manifest_to_mcp_tool,
    capability_manifest_to_openai_tool,
    capability_to_mcp_tool,
    capability_to_openai_tool,
    capability_to_tool_manifest,
)
from ultimate_ai_agent.core.capabilities.enums import CapabilityKind, CoordinationMode, RiskLevel as CoordinationRiskLevel, SideEffectLevel
from ultimate_ai_agent.core.capabilities.models import CapabilityManifest
from ultimate_ai_agent.core.capabilities.adapters.langchain import capability_to_langchain_structured_tool
from ultimate_ai_agent.core.capabilities.adapters.pydantic_ai import capability_to_pydantic_ai_tool
from ultimate_ai_agent.core.capabilities.discovery import importlib_metadata
from ultimate_ai_agent.core.contracts import AgentMode, ContractStatus, ExecutionContract, validate_execution_contract


class _Sink:
    def __init__(self) -> None:
        self.events: list[CapabilityEvent] = []

    def emit(self, event: CapabilityEvent) -> None:
        self.events.append(event)


class ReadInput(BaseModel):
    path: str

    model_config = ConfigDict(extra="forbid")


class ReadOutput(BaseModel):
    text: str

    model_config = ConfigDict(extra="forbid")


def _spec(name: str = "files.read_text", **overrides: Any) -> CapabilitySpec:
    data = {
        "id": f"capability:{name}:1.0.0",
        "name": name,
        "version": "1.0.0",
        "title": "Read Text",
        "description": "Read a safe text reference.",
        "tags": {"files", "read"},
        "input_schema": ReadInput.model_json_schema(),
        "output_schema": ReadOutput.model_json_schema(),
        "policy": CapabilityPolicy(risk=RiskLevel.READ_ONLY),
        "source": "python",
        "metadata": {"owner": "tests"},
    }
    data.update(overrides)
    return CapabilitySpec(**data)


def test_register_get_list_and_duplicate_behavior() -> None:
    registry = CapabilityRegistry()
    spec = _spec()

    registry.register(spec)

    assert registry.get("files.read_text") == spec
    assert [item.name for item in registry.list()] == ["files.read_text"]
    with pytest.raises(ValueError, match="already registered"):
        registry.register(spec)

    replacement = spec.model_copy(update={"title": "Read Text V2"})
    registry.register(replacement, replace=True)
    assert registry.get("files.read_text").title == "Read Text V2"


def test_name_validation_is_conservative() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(ValueError, match="capability name"):
        registry.register(_spec("files read text"))

    with pytest.raises(ValueError, match="capability name"):
        registry.get("files read text")


def test_decorator_generates_pydantic_schemas_and_preserves_function_metadata() -> None:
    @tool_capability(
        name="math.add",
        title="Add",
        description="Add two integers.",
        input_model=ReadInput,
        output_model=ReadOutput,
        tags={"math"},
        policy=CapabilityPolicy(risk=RiskLevel.READ_ONLY),
    )
    async def decorated(ctx: Any, args: ReadInput) -> ReadOutput:
        """Original docstring."""
        return ReadOutput(text=args.path)

    spec = decorated.__capability_spec__

    assert decorated.__name__ == "decorated"
    assert decorated.__doc__ == "Original docstring."
    assert spec.input_schema["properties"]["path"]["type"] == "string"
    assert spec.output_schema["properties"]["text"]["type"] == "string"


def test_resolve_filters_by_agent_scope_tags_and_scores_query() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _spec(
            "files.read_text",
            policy=CapabilityPolicy(
                allowed_agents={"agent.alpha"},
                required_scopes={"files:read"},
                risk=RiskLevel.READ_ONLY,
            ),
        )
    )
    registry.register(
        _spec(
            "github.search_issues",
            title="Search Issues",
            description="Search issue summaries.",
            tags={"github", "read"},
            policy=CapabilityPolicy(required_scopes={"github:read"}),
        )
    )

    resolved = registry.resolve("agent.alpha", {"files:read", "github:read"}, query="github", tags={"read"})

    assert [spec.name for spec in resolved] == ["github.search_issues", "files.read_text"]
    assert registry.resolve("agent.beta", {"files:read"}, tags={"files"}) == []


def test_permission_denial_returns_structured_result() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _spec(policy=CapabilityPolicy(allowed_agents={"agent.alpha"}, risk=RiskLevel.READ_ONLY)),
        lambda ctx, args: ReadOutput(text="ok"),
        input_model=ReadInput,
        output_model=ReadOutput,
    )

    result = registry.execute_sync("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.beta"})

    assert result.ok is False
    assert "AGENT_NOT_ALLOWED" in result.error


def test_approval_required_denies_without_callback() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _spec(policy=CapabilityPolicy(risk=RiskLevel.WRITE, requires_approval=True)),
        lambda ctx, args: ReadOutput(text="ok"),
        input_model=ReadInput,
        output_model=ReadOutput,
    )

    result = registry.execute_sync("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.alpha"})

    assert result.ok is False
    assert result.error == "APPROVAL_REQUIRED"


def test_successful_async_execution_and_events() -> None:
    sink = _Sink()
    registry = CapabilityRegistry(event_sink=sink)

    async def read_text(ctx: Any, args: ReadInput) -> ReadOutput:
        return ReadOutput(text=f"read:{args.path}")

    registry.register(_spec(), read_text, input_model=ReadInput, output_model=ReadOutput)

    result = asyncio.run(registry.execute("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.alpha"}))

    assert result.ok is True
    assert result.structured_content == {"text": "read:a.txt"}
    assert "capability.call.started" in [event.event_type for event in sink.events]
    assert "capability.call.succeeded" in [event.event_type for event in sink.events]


def test_successful_sync_execution() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _spec(),
        lambda ctx, args: ReadOutput(text=args.path.upper()),
        input_model=ReadInput,
        output_model=ReadOutput,
    )

    result = registry.execute_sync("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.alpha"})

    assert result.ok is True
    assert result.structured_content == {"text": "A.TXT"}


def test_timeout_failure() -> None:
    registry = CapabilityRegistry()

    async def slow(ctx: Any, args: Any) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"text": "late"}

    registry.register(
        _spec(policy=CapabilityPolicy(timeout_s=0.01, risk=RiskLevel.READ_ONLY)),
        slow,
        input_model=ReadInput,
    )

    result = registry.execute_sync("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.alpha"})

    assert result.ok is False
    assert result.error == "CAPABILITY_TIMEOUT"


def test_input_validation_failure() -> None:
    registry = CapabilityRegistry()
    registry.register(_spec(), lambda ctx, args: ReadOutput(text=args.path), input_model=ReadInput, output_model=ReadOutput)

    result = registry.execute_sync("files.read_text", {"path": "a.txt", "extra": True}, {"agent_name": "agent.alpha"})

    assert result.ok is False
    assert result.metadata["error_code"] == "INPUT_VALIDATION_FAILED"


def test_output_validation_failure() -> None:
    registry = CapabilityRegistry()
    registry.register(_spec(), lambda ctx, args: {"text": 123}, input_model=ReadInput, output_model=ReadOutput)

    result = registry.execute_sync("files.read_text", {"path": "a.txt"}, {"agent_name": "agent.alpha"})

    assert result.ok is False
    assert result.metadata["error_code"] == "OUTPUT_VALIDATION_FAILED"


def test_openai_and_mcp_adapters_do_not_expose_callable_refs_or_metadata() -> None:
    spec = _spec(metadata={"secret": "not exported"}, callable_ref="module.fn", instructions="Use concise output.")

    openai_tool = capability_to_openai_tool(spec)
    mcp_tool = capability_to_mcp_tool(spec)

    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "files.read_text"
    assert openai_tool["function"]["parameters"]["properties"]["path"]["type"] == "string"
    assert "strict" in openai_tool["function"]
    assert "callable_ref" not in str(openai_tool)
    assert "not exported" not in str(openai_tool)
    assert mcp_tool["inputSchema"]["properties"]["path"]["type"] == "string"
    assert mcp_tool["outputSchema"]["properties"]["text"]["type"] == "string"
    assert "callable_ref" not in str(mcp_tool)


def test_manifest_static_schema_exports_include_uaa_authority_metadata_without_dispatch() -> None:
    manifest = CapabilityManifest(
        id="cap:agent_runtime_export",
        version="1.0.0",
        kind=CapabilityKind.agent,
        name="Agent Runtime Export",
        description="Static schema export for a contract-only agent runtime.",
        tags=["agent-runtime"],
        examples=["Use for static schema export only."],
        anti_examples=["Do not use as live dispatch authority."],
        input_schema={"type": "object", "properties": {"task_ref": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"safe_output_ref": {"type": "string"}}},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.read,
        risk_level=CoordinationRiskLevel.low,
        allowed_coordination_modes=[CoordinationMode.agent_as_tool],
        concurrency_safe=True,
    )

    openai_tool = capability_manifest_to_openai_tool(manifest)
    mcp_tool = capability_manifest_to_mcp_tool(manifest)

    openai_authority = openai_tool["function"]["x-uaa-authority"]
    mcp_authority = mcp_tool["annotations"]["x-uaa-authority"]
    assert openai_authority["capability_id"] == manifest.id
    assert openai_authority["dispatch_authorized"] is False
    assert openai_authority["memory_write_allowed"] is False
    assert openai_authority["context_injection_allowed"] is False
    assert openai_authority["provider_runtime_allowed"] is False
    assert mcp_authority == openai_authority


def test_model_facing_instructions_reject_secret_like_values() -> None:
    with pytest.raises(ValueError, match="instructions"):
        _spec(instructions="api_key='abc12345678901234567890'")


def test_executable_framework_adapters_are_disabled() -> None:
    spec = _spec()

    with pytest.raises(RuntimeError, match="LangChain tool export is disabled"):
        capability_to_langchain_structured_tool(spec)
    with pytest.raises(RuntimeError, match="Pydantic AI tool export is disabled"):
        capability_to_pydantic_ai_tool(spec)


def test_tool_manifest_adapter_matches_existing_registry_contract() -> None:
    manifest = capability_to_tool_manifest(_spec(policy=CapabilityPolicy(risk=RiskLevel.WRITE)))

    assert manifest.tool_id == "files.read_text"
    assert manifest.permission_manifest.required_permissions == manifest.permissions_required


def test_entry_point_discovery_registers_specs(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = _spec("plugins.echo")
    loaded = False

    class FakeEntryPoint:
        def load(self) -> Any:
            nonlocal loaded
            loaded = True
            return lambda: [spec]

    class FakeEntryPoints(list):
        def select(self, group: Any) -> Any:
            assert group == "ultimate_ai_agent.capabilities"
            return self

    monkeypatch.setattr(importlib_metadata, "entry_points", lambda: FakeEntryPoints([FakeEntryPoint()]))
    registry = CapabilityRegistry()

    count = registry.discover_entry_points()

    assert count == 0
    assert loaded is False

    count = registry.discover_entry_points(allow_runtime_imports=True)

    assert count == 1
    assert registry.get("plugins.echo").name == "plugins.echo"


def test_execution_contract_uses_capability_registry_for_blocked_flags() -> None:
    registry = CapabilityRegistry()
    registry.register(
        _spec(
            "custom.blocked",
            tags={"blocked"},
            metadata={"foundation_gate_blocked": True, "enabled": False},
        )
    )
    contract = ExecutionContract(
        contract_id="ec_capability_registry_001",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Try blocked capability",
        goal="Use blocked capability",
        deliverable="No execution",
        mode=AgentMode.answer,
        capability_flags_required=["custom.blocked"],
        acceptance_criteria=["Denied"],
        status=ContractStatus.draft,
    )

    result = validate_execution_contract(contract, capability_registry=registry)

    assert result.success is False
    assert result.error.code == "BLOCKED_CAPABILITY"


def test_execution_contract_keeps_default_blocked_flags_with_custom_registry() -> None:
    registry = CapabilityRegistry()
    contract = ExecutionContract(
        contract_id="ec_capability_registry_002",
        run_id="run_123",
        workspace_id="ws_1",
        user_id="usr_alice",
        request_summary="Try blocked capability",
        goal="Use blocked capability",
        deliverable="No execution",
        mode=AgentMode.answer,
        capability_flags_required=["reddit_scanner"],
        acceptance_criteria=["Denied"],
        status=ContractStatus.draft,
    )

    result = validate_execution_contract(contract, capability_registry=registry)

    assert result.success is False
    assert result.error.code == "BLOCKED_CAPABILITY"
