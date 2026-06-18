from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ultimate_ai_agent.core.capabilities.enums import CapabilityHealthStatus, CapabilityKind, CoordinationMode, RiskLevel, SideEffectLevel
from ultimate_ai_agent.core.capabilities.models import Artifact, CapabilityHealthReport, CapabilityManifest, RuntimePolicy, SafetyPolicy
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry
from ultimate_ai_agent.core.files import FileKind, FileManagerPolicy, FileReadRequest, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.model_runtime import run_local_model_call


LOCAL_FILE_METADATA_CAPABILITY_ID = "cap:live.local_file_metadata"
LOCAL_FILE_WRITE_CAPABILITY_ID = "cap:live.local_file_write"
DETERMINISTIC_WORKFLOW_CAPABILITY_ID = "cap:live.deterministic_workflow"
M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID = "cap:live.m23_model_loopback"
EXTERNAL_ACTION_GATE_CAPABILITY_ID = "cap:live.external_action_gate"


@dataclass(frozen=True)
class LiveLocalTestingRuntime:
    workspace_root: Path
    registry: CapabilityRegistry
    file_manager: LocalFileManager


class _LocalFileMetadataAdapter:
    def __init__(self, file_manager: LocalFileManager):
        self.file_manager = file_manager

    async def invoke(self, envelope: Any, context: dict[str, Any]) -> Artifact:
        path = str(context.get("path") or envelope.context.get("path") or "")
        include_preview = bool(context.get("include_preview", envelope.context.get("include_preview", False)))
        max_preview_bytes = int(context.get("max_preview_bytes", envelope.context.get("max_preview_bytes", 4096)))
        file_ref = self.file_manager.build_file_ref(path)
        content: dict[str, Any] = {"file_ref": file_ref.model_dump(mode="json")}
        if include_preview:
            preview = self.file_manager.read_preview(
                FileReadRequest(
                    request_id=f"live_read_{envelope.task_id}",
                    run_id=envelope.task_id,
                    actor_context=_actor_context(context),
                    path=path,
                    purpose="live local file metadata capability preview",
                    max_bytes=max_preview_bytes,
                )
            )
            content["preview"] = preview.model_dump(mode="json")
        return Artifact(
            producer_capability_id=LOCAL_FILE_METADATA_CAPABILITY_ID,
            kind="live_local.file_metadata",
            content=content,
            summary="Live local file metadata read completed within the configured workspace root.",
            side_effects_performed=["file_metadata_read"],
            confidence=1.0,
        )

    def health_check(self) -> CapabilityHealthReport:
        return _healthy(LOCAL_FILE_METADATA_CAPABILITY_ID)


class _LocalFileWriteAdapter:
    def __init__(self, file_manager: LocalFileManager):
        self.file_manager = file_manager

    async def invoke(self, envelope: Any, context: dict[str, Any]) -> Artifact:
        target_path = str(context.get("target_path") or envelope.context.get("target_path") or "")
        proposal = FileWriteProposal(
            proposal_id=f"live_write_{envelope.task_id}",
            run_id=envelope.task_id,
            actor_context=_actor_context(context),
            target_path=target_path,
            purpose="live local approved file write capability",
            new_content=str(context.get("new_content", envelope.context.get("new_content", ""))),
            expected_existing_hash=context.get("expected_existing_hash") or envelope.context.get("expected_existing_hash"),
            file_kind=FileKind.generated,
            sensitivity=FileSensitivity.project_private,
            idempotency_key=context.get("idempotency_key") or envelope.context.get("idempotency_key"),
            approval_ref=context.get("approval_ref") or envelope.context.get("approval_ref"),
        )
        decision = self.file_manager.propose_write(proposal)
        content: dict[str, Any] = {"decision": decision.model_dump(mode="json")}
        side_effects: list[str] = []
        kind = "live_local.file_write_proposal"
        summary = "Live local file write proposal completed without applying a change."
        if bool(context.get("apply_write", envelope.context.get("apply_write", False))) and decision.allowed:
            change = self.file_manager.apply_write(proposal)
            content["change"] = change.model_dump(mode="json")
            side_effects = ["file_write"]
            kind = "live_local.file_change"
            summary = "Live local approved file write was applied within the configured workspace root."
        return Artifact(
            producer_capability_id=LOCAL_FILE_WRITE_CAPABILITY_ID,
            kind=kind,
            content=content,
            summary=summary,
            side_effects_performed=side_effects,
            confidence=1.0 if decision.allowed else 0.5,
        )

    def health_check(self) -> CapabilityHealthReport:
        return _healthy(LOCAL_FILE_WRITE_CAPABILITY_ID)


class _DeterministicWorkflowAdapter:
    async def invoke(self, envelope: Any, context: dict[str, Any]) -> Artifact:
        workflow_inputs = dict(context.get("workflow_inputs") or envelope.context.get("workflow_inputs") or {})
        input_keys = sorted(str(key) for key in workflow_inputs)
        digest_source = "|".join(f"{key}={workflow_inputs[key]!r}" for key in input_keys)
        digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
        return Artifact(
            producer_capability_id=DETERMINISTIC_WORKFLOW_CAPABILITY_ID,
            kind="live_local.deterministic_workflow",
            content={"input_keys": input_keys, "deterministic_digest": digest},
            summary="Deterministic workflow artifact produced from structured inputs.",
            side_effects_performed=[],
            confidence=1.0,
        )

    def health_check(self) -> CapabilityHealthReport:
        return _healthy(DETERMINISTIC_WORKFLOW_CAPABILITY_ID)


class _M23LocalModelLoopbackAdapter:
    async def invoke(self, envelope: Any, context: dict[str, Any]) -> Artifact:
        del envelope
        result = run_local_model_call(
            context["local_model_request"],
            transport=context["local_model_transport"],
            approval_decision=context.get("local_model_approval_decision"),
        )
        side_effects = ["loopback_local_model_call"] if result.transport_result.call_performed else []
        return Artifact(
            producer_capability_id=M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID,
            kind="live_local.m23_model_loopback",
            content=result.model_dump(mode="json"),
            summary="M23 local loopback model smoke call returned a redacted non-authoritative receipt.",
            side_effects_performed=side_effects,
            confidence=1.0 if result.decision.allowed else 0.5,
        )

    def health_check(self) -> CapabilityHealthReport:
        return _healthy(M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID)


class _ExternalActionGateAdapter:
    async def invoke(self, envelope: Any, context: dict[str, Any]) -> Artifact:
        requested_action = str(context.get("requested_external_action") or envelope.context.get("requested_external_action") or "external_action")
        return Artifact(
            producer_capability_id=EXTERNAL_ACTION_GATE_CAPABILITY_ID,
            kind="live_local.external_action_denial",
            content={
                "requested_external_action": requested_action,
                "allowed": False,
                "reason_codes": ["EXTERNAL_AUTHORITY_NOT_GRANTED", "REVIEWED_ADAPTER_REQUIRED"],
            },
            summary="External action request was denied because no reviewed production adapter authority was granted.",
            side_effects_performed=[],
            confidence=1.0,
        )

    def health_check(self) -> CapabilityHealthReport:
        return _healthy(EXTERNAL_ACTION_GATE_CAPABILITY_ID)


def build_live_local_testing_runtime(workspace_root: str | Path) -> LiveLocalTestingRuntime:
    root = Path(workspace_root).resolve()
    file_manager = LocalFileManager(
        root,
        policy=FileManagerPolicy(allow_overwrite_without_hash=True),
    )
    registry = CapabilityRegistry()
    registry.register(_file_metadata_manifest(), _LocalFileMetadataAdapter(file_manager))
    registry.register(_file_write_manifest(), _LocalFileWriteAdapter(file_manager))
    registry.register(_deterministic_workflow_manifest(), _DeterministicWorkflowAdapter())
    registry.register(_m23_model_loopback_manifest(), _M23LocalModelLoopbackAdapter())
    registry.register(_external_action_gate_manifest(), _ExternalActionGateAdapter())
    return LiveLocalTestingRuntime(workspace_root=root, registry=registry, file_manager=file_manager)


def build_live_local_testing_registry(workspace_root: str | Path) -> CapabilityRegistry:
    return build_live_local_testing_runtime(workspace_root).registry


def _file_metadata_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=LOCAL_FILE_METADATA_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="live-local-file-metadata",
        description="Reads bounded local file metadata and optional preview from the configured workspace root.",
        tags=["live-local", "file", "metadata"],
        examples=["Use to inspect a declared workspace-relative file path during live local tests."],
        anti_examples=["Do not use to scan arbitrary directories or read outside the configured workspace root."],
        input_schema={"type": "object", "required": ["path"]},
        output_schema={"type": "object"},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.low,
        allowed_coordination_modes=[CoordinationMode.direct_tool, CoordinationMode.parallel_read_fanout],
        concurrency_safe=True,
        safety=SafetyPolicy(allow_parallel=True, max_risk_level=RiskLevel.low, max_side_effect_level=SideEffectLevel.read),
        runtime_policy=RuntimePolicy(deterministic=True),
    )


def _file_write_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=LOCAL_FILE_WRITE_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="live-local-file-write",
        description="Applies one approved local file write within the configured workspace root.",
        tags=["live-local", "file", "write"],
        examples=["Use with an approval ref, idempotency key, and workspace-relative target path."],
        anti_examples=["Do not use for multiple writers, external paths, credentials, or unapproved writes."],
        input_schema={"type": "object", "required": ["target_path", "new_content", "idempotency_key"]},
        output_schema={"type": "object"},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.write,
        risk_level=RiskLevel.medium,
        approval_required=True,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        single_writer_required=True,
        safety=SafetyPolicy(
            require_single_writer=True,
            approval_required=True,
            max_risk_level=RiskLevel.medium,
            max_side_effect_level=SideEffectLevel.write,
        ),
        runtime_policy=RuntimePolicy(deterministic=False),
    )


def _deterministic_workflow_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=DETERMINISTIC_WORKFLOW_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.workflow,
        name="live-local-deterministic-workflow",
        description="Produces a deterministic digest from structured workflow inputs.",
        tags=["live-local", "workflow", "deterministic"],
        examples=["Use for read-only deterministic composition during parallel fan-out tests."],
        anti_examples=["Do not use for external calls, file writes, or model/provider execution."],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.none,
        risk_level=RiskLevel.safe,
        allowed_coordination_modes=[CoordinationMode.workflow_node, CoordinationMode.parallel_read_fanout],
        concurrency_safe=True,
        safety=SafetyPolicy(allow_parallel=True, max_risk_level=RiskLevel.safe, max_side_effect_level=SideEffectLevel.none),
        runtime_policy=RuntimePolicy(deterministic=True),
    )


def _m23_model_loopback_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=M23_LOCAL_MODEL_LOOPBACK_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="live-local-m23-model-loopback",
        description="Runs the existing M23 fixed-prompt loopback local model call under approval policy.",
        tags=["live-local", "m23", "loopback", "model"],
        examples=["Use with an M23 request, approval decision, and loopback transport during live local tests."],
        anti_examples=["Do not use for arbitrary prompts, tools, memory writes, provider calls, or remote model calls."],
        input_schema={"type": "object", "required": ["local_model_request", "local_model_transport"]},
        output_schema={"type": "object"},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.external,
        risk_level=RiskLevel.high,
        approval_required=True,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        single_writer_required=True,
        safety=SafetyPolicy(
            require_single_writer=True,
            approval_required=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.external,
        ),
        runtime_policy=RuntimePolicy(deterministic=False),
    )


def _external_action_gate_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=EXTERNAL_ACTION_GATE_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.human_gate,
        name="live-local-external-action-gate",
        description="Returns a structured denial for external action requests that lack reviewed adapter authority.",
        tags=["live-local", "external-action", "gate"],
        examples=["Use to prove denied external action planning remains side-effect free."],
        anti_examples=["Do not use to execute network, provider, browser, shell, plugin, or remote actions."],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.none,
        risk_level=RiskLevel.safe,
        allowed_coordination_modes=[CoordinationMode.human_gate, CoordinationMode.direct_tool],
        concurrency_safe=True,
        safety=SafetyPolicy(max_risk_level=RiskLevel.safe, max_side_effect_level=SideEffectLevel.none),
        runtime_policy=RuntimePolicy(deterministic=True),
    )


def _actor_context(context: dict[str, Any]) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id=str(context.get("actor_id") or "live-local-test-actor"),
        authority_source=AuthoritySource.explicit_user_request,
        approval_ref=context.get("approval_ref"),
    )


def _healthy(capability_id: str) -> CapabilityHealthReport:
    return CapabilityHealthReport(
        capability_id=capability_id,
        status=CapabilityHealthStatus.healthy,
        reason_codes=["LIVE_LOCAL_ADAPTER_READY"],
    )
