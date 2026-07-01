from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Type

from pydantic import BaseModel

from ultimate_ai_agent.core.adapters import UAAA2AAgentCardMetadataImport
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityHealthStatus,
    CapabilityKind,
    CoordinationMode,
    RiskLevel as CoordinationRiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.executor import ApprovalCallback, CapabilityExecutor
from ultimate_ai_agent.core.capabilities.models import (
    CAPABILITY_NAME_PATTERN,
    CapabilityCatalogEntry,
    CapabilityHealthReport,
    CapabilityManifest,
    CapabilityRegistration,
    CapabilityResult,
    CapabilitySearchFilters,
    CapabilitySpec,
    is_read_only_side_effect,
    risk_rank,
    side_effect_rank,
)
from ultimate_ai_agent.core.capabilities.observability import CapabilityEvent, CapabilityEventSink, NoopCapabilityEventSink
from ultimate_ai_agent.core.capabilities.policy import normalize_run_context
from ultimate_ai_agent.core.capabilities.resolver import resolve_capabilities


class CapabilityRegistry:
    def __init__(
        self,
        *,
        approval_callback: ApprovalCallback | None = None,
        event_sink: CapabilityEventSink | None = None,
    ) -> None:
        self._capabilities: dict[str, CapabilityRegistration] = {}
        self._manifests: dict[str, CapabilityManifest] = {}
        self._adapters: dict[str, Any] = {}
        self._health_overrides: dict[str, CapabilityHealthStatus] = {}
        self.event_sink = event_sink or NoopCapabilityEventSink()
        self.executor = CapabilityExecutor(approval_callback=approval_callback, event_sink=self.event_sink)

    def register(
        self,
        spec: CapabilitySpec | CapabilityManifest,
        fn: Callable[..., Any] | Any | None = None,
        *,
        replace: bool = False,
        input_model: Type[BaseModel] | None = None,
        output_model: Type[BaseModel] | None = None,
    ) -> CapabilitySpec | CapabilityManifest:
        if isinstance(spec, CapabilityManifest):
            if fn is None:
                raise ValueError("CapabilityManifest registration requires an adapter.")
            return self._register_manifest(spec, fn, replace=replace)
        self._validate_name(spec.name)
        if spec.name in self._capabilities and not replace:
            raise ValueError(f"capability '{spec.name}' is already registered")
        registration = CapabilityRegistration(spec=spec, fn=fn, input_model=input_model, output_model=output_model)
        self._capabilities[spec.name] = registration
        self.event_sink.emit(
            CapabilityEvent(
                "capability.registered",
                capability_name=spec.name,
                status="registered",
                metadata={"source": spec.source, "tags": sorted(spec.tags), "replace": replace},
            )
        )
        return spec

    def register_many(self, registrations: Iterable[CapabilityRegistration | CapabilitySpec], *, replace: bool = False) -> None:
        for item in registrations:
            if isinstance(item, CapabilityRegistration):
                self.register(
                    item.spec,
                    item.fn,
                    replace=replace,
                    input_model=item.input_model,
                    output_model=item.output_model,
                )
            else:
                self.register(item, replace=replace)

    def unregister(self, name: str) -> None:
        if name in self._manifests:
            self._manifests.pop(name, None)
            self._adapters.pop(name, None)
            self._health_overrides.pop(name, None)
            return
        self._validate_name(name)
        self._capabilities.pop(name, None)

    def get(self, name: str) -> CapabilitySpec | CapabilityManifest | None:
        if name in self._manifests:
            return self._manifests.get(name)
        self._validate_name(name)
        registration = self._capabilities.get(name)
        return registration.spec if registration is not None else None

    def list(self) -> list[CapabilitySpec]:
        return [registration.spec for _, registration in sorted(self._capabilities.items())]

    def resolve(
        self,
        agent_name: str,
        user_scopes: set[str],
        query: str | None = None,
        tags: set[str] | None = None,
        max_tools: int = 20,
    ) -> list[CapabilitySpec]:
        resolved = resolve_capabilities(
            self.list(),
            agent_name=agent_name,
            user_scopes=set(user_scopes),
            query=query,
            tags=tags,
            max_tools=max_tools,
        )
        self.event_sink.emit(
            CapabilityEvent(
                "capability.resolved",
                agent_name=agent_name,
                status="resolved",
                metadata={
                    "count": len(resolved),
                    "query_present": bool(query),
                    "tags": sorted(tags or set()),
                },
            )
        )
        return resolved

    async def execute(self, capability_name: str, arguments: Any, run_context: Any) -> CapabilityResult:
        self._validate_name(capability_name)
        return await self.executor.execute(self._capabilities.get(capability_name), capability_name, arguments, run_context)

    def execute_sync(self, capability_name: str, arguments: Any, run_context: Any) -> CapabilityResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.execute(capability_name, arguments, run_context))
        raise RuntimeError("execute_sync cannot be used from a running event loop")

    def resolve_for_run(
        self,
        run_context: Any,
        *,
        query: str | None = None,
        tags: set[str] | None = None,
        max_tools: int = 20,
    ) -> list[CapabilitySpec]:
        context = normalize_run_context(run_context)
        return self.resolve(context.agent_name, context.user_scopes, query=query, tags=tags, max_tools=max_tools)

    def discover_entry_points(
        self,
        group: str = "ultimate_ai_agent.capabilities",
        *,
        allow_runtime_imports: bool = False,
    ) -> int:
        from ultimate_ai_agent.core.capabilities.discovery import discover_entry_points

        return discover_entry_points(self, group=group, allow_runtime_imports=allow_runtime_imports)

    def load_manifest(self, capability_id: str) -> CapabilityManifest:
        manifest = self._manifests.get(capability_id)
        if manifest is None:
            raise KeyError(f"Capability '{capability_id}' is not registered.")
        return manifest

    def validate_manifest(self, manifest: CapabilityManifest) -> CapabilityManifest:
        return CapabilityManifest.model_validate(manifest.model_dump())

    def resolve_adapter(self, capability_id: str) -> Any:
        adapter = self._adapters.get(capability_id)
        if adapter is None:
            raise KeyError(f"Capability adapter '{capability_id}' is not registered.")
        return adapter

    def list_catalog(self, context: dict[str, Any] | None = None) -> list[CapabilityCatalogEntry]:
        filters = CapabilitySearchFilters(
            required_auth_scopes=list((context or {}).get("auth_scopes", [])),
            tenant_id=(context or {}).get("tenant_id"),
            user_id=(context or {}).get("user_id"),
        )
        return self.search("", context or {}, filters)

    def search(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        filters: CapabilitySearchFilters | None = None,
    ) -> list[CapabilityCatalogEntry]:
        context = context or {}
        active_filters = filters or CapabilitySearchFilters(
            required_auth_scopes=list(context.get("auth_scopes", [])),
            tenant_id=context.get("tenant_id"),
            user_id=context.get("user_id"),
        )
        entries: list[CapabilityCatalogEntry] = []
        for manifest in self._manifests.values():
            include, reasons = self._passes_filters(manifest, context, active_filters)
            if not include:
                continue
            score, score_reasons = self._score_manifest(query, manifest)
            entries.append(
                CapabilityCatalogEntry.from_manifest(
                    manifest,
                    health_status=self._health_status(manifest.id),
                    score=score,
                    reason_codes=[*reasons, *score_reasons],
                )
            )
        entries.sort(key=lambda entry: (-entry.score, risk_rank(entry.risk_level), entry.id))
        return entries[: active_filters.limit]

    def health_check(self, capability_id: str | None = None) -> CapabilityHealthReport | dict[str, CapabilityHealthReport]:
        if capability_id is not None:
            return self._health_report(capability_id)
        return {capability_id: self._health_report(capability_id) for capability_id in sorted(self._manifests)}

    def set_health_override(self, capability_id: str, status: CapabilityHealthStatus) -> None:
        if capability_id not in self._manifests:
            raise KeyError(f"Capability '{capability_id}' is not registered.")
        self._health_overrides[capability_id] = status

    def export_manifest_json(self, capability_id: str, *, indent: int | None = 2) -> str:
        manifest = self.load_manifest(capability_id)
        return json.dumps(manifest.model_dump(mode="json"), indent=indent, sort_keys=True)

    def export_all_manifests_json(self, *, indent: int | None = 2) -> str:
        payload = [self._manifests[key].model_dump(mode="json") for key in sorted(self._manifests)]
        return json.dumps(payload, indent=indent, sort_keys=True)

    def import_manifest_json(
        self,
        manifest_json: str | bytes | Mapping[str, Any],
        adapter: Any | None = None,
    ) -> CapabilityManifest:
        payload = json.loads(manifest_json) if isinstance(manifest_json, (str, bytes)) else dict(manifest_json)
        manifest = self.validate_manifest(CapabilityManifest.model_validate(payload))
        if adapter is not None:
            self.register(manifest, adapter)
        return manifest

    def import_manifest_file(self, path: str | Path, adapter: Any | None = None) -> CapabilityManifest:
        return self.import_manifest_json(Path(path).read_text(encoding="utf-8"), adapter)

    def manifest_from_tool_manifest(
        self,
        tool: Any,
        *,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        examples: list[str] | None = None,
        anti_examples: list[str] | None = None,
    ) -> CapabilityManifest:
        side_effects = _side_effects_from_tool(tool)
        risk_level = CoordinationRiskLevel(tool.risk_level.value)
        return CapabilityManifest(
            id=tool.tool_id,
            version=tool.version,
            kind=CapabilityKind.tool,
            name=tool.display_name,
            description=tool.description,
            owner=tool.owner,
            tags=[tool.category.value, tool.execution_mode.value],
            examples=examples or [f"Use {tool.tool_id} when the request exactly matches its tool contract."],
            anti_examples=anti_examples
            or [f"Do not use {tool.tool_id} for unrelated work or broader authority than its manifest allows."],
            input_schema=input_schema or {"type": "object"},
            output_schema=output_schema or {"type": "object"},
            input_modes=["structured_ref"],
            output_modes=["artifact"],
            side_effects=side_effects,
            risk_level=risk_level,
            approval_required=tool.requires_approval or None,
            auth_scopes=[permission.value for permission in tool.permissions_required],
            data_classes=[boundary.value for boundary in tool.data_boundaries],
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            concurrency_safe=side_effects in {SideEffectLevel.none, SideEffectLevel.read},
            single_writer_required=side_effects not in {SideEffectLevel.none, SideEffectLevel.read},
            safety={
                "allow_parallel": side_effects in {SideEffectLevel.none, SideEffectLevel.read},
                "require_single_writer": side_effects not in {SideEffectLevel.none, SideEffectLevel.read},
                "approval_required": tool.requires_approval,
                "max_risk_level": risk_level,
                "max_side_effect_level": side_effects,
            },
            metadata={"source": tool.source, "capability_flag": tool.capability_flag},
        )

    def manifest_from_a2a_agent_card(
        self,
        card: UAAA2AAgentCardMetadataImport,
        *,
        examples: list[str] | None = None,
        anti_examples: list[str] | None = None,
    ) -> CapabilityManifest:
        from ultimate_ai_agent.core.capabilities.a2a_gateway import (
            a2a_agent_card_to_metadata,
            a2a_agent_metadata_to_capability_candidate,
        )

        metadata = a2a_agent_card_to_metadata(card)
        manifest = a2a_agent_metadata_to_capability_candidate(metadata)
        return manifest.model_copy(
            update={
                "examples": examples or manifest.examples,
                "anti_examples": anti_examples or manifest.anti_examples,
                "tags": ["a2a", "gateway-foundation", "metadata-only", *card.declared_capabilities],
            }
        )

    def manifest_from_mcp_tool_spec(
        self,
        spec: Mapping[str, Any],
        *,
        capability_id: str | None = None,
        examples: list[str] | None = None,
        anti_examples: list[str] | None = None,
    ) -> CapabilityManifest:
        from ultimate_ai_agent.core.capabilities.mcp_gateway import (
            McpAuthPosture,
            McpDiscoveryToolMetadata,
            McpTransportPosture,
            mcp_tool_metadata_to_capability_candidate,
        )

        name = str(spec.get("name") or capability_id or "mcp_tool")
        safe_name = re.sub(r"[^A-Za-z0-9_.:-]+", "-", name).strip("-") or "mcp_tool"
        metadata = McpDiscoveryToolMetadata(
            server_ref=str(spec.get("server_ref") or "mcp-server-ref:unknown"),
            tool_ref=str(spec.get("tool_ref") or f"mcp-tool-ref:{safe_name}"),
            name=name,
            description=str(spec.get("description") or "MCP tool spec metadata import."),
            input_schema=dict(spec.get("inputSchema") or spec.get("input_schema") or {"type": "object"}),
            output_schema=dict(spec.get("outputSchema") or spec.get("output_schema") or {"type": "object"}),
            provenance_ref=str(spec.get("provenance_ref") or "provenance-ref:mcp:unreviewed"),
            transport_posture=McpTransportPosture.unknown_blocked,
            auth_posture=McpAuthPosture.unknown_blocked,
            audit_ref=str(spec.get("audit_ref") or "audit-ref:mcp:unreviewed"),
            replay_ref=str(spec.get("replay_ref") or "replay-ref:mcp:unreviewed"),
            revocation_ref=str(spec.get("revocation_ref") or "revocation-ref:mcp:unreviewed"),
            safe_disable_ref=str(spec.get("safe_disable_ref") or "safe-disable-ref:mcp:unreviewed"),
            expected_receipt_ref=str(spec.get("expected_receipt_ref") or "receipt-ref:mcp:blocked-unreviewed"),
        )
        manifest = mcp_tool_metadata_to_capability_candidate(metadata, capability_id=capability_id)
        return manifest.model_copy(
            update={
                "examples": examples or manifest.examples,
                "anti_examples": anti_examples or manifest.anti_examples,
                "tags": ["mcp", "gateway-foundation", "metadata-only", *list(spec.get("tags") or [])],
            }
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not CAPABILITY_NAME_PATTERN.fullmatch(name):
            raise ValueError("capability name must use letters, numbers, underscore, hyphen, or dot")

    def _register_manifest(
        self,
        manifest: CapabilityManifest,
        adapter: Any,
        *,
        replace: bool = False,
    ) -> CapabilityManifest:
        validated = self.validate_manifest(manifest)
        if validated.id in self._manifests and not replace:
            raise ValueError(f"capability manifest '{validated.id}' is already registered")
        self._manifests[validated.id] = validated
        self._adapters[validated.id] = adapter
        self.event_sink.emit(
            CapabilityEvent(
                "capability_manifest.registered",
                capability_name=validated.id,
                status="registered",
                metadata={"kind": validated.kind.value, "replace": replace},
            )
        )
        return validated

    def _passes_filters(
        self,
        manifest: CapabilityManifest,
        context: dict[str, Any],
        filters: CapabilitySearchFilters,
    ) -> tuple[bool, list[str]]:
        reasons = ["CATALOG_ENTRY_ELIGIBLE"]
        if filters.kinds and manifest.kind not in filters.kinds:
            return False, ["KIND_FILTERED"]
        if filters.input_modes and not set(filters.input_modes).intersection(manifest.input_modes):
            return False, ["INPUT_MODE_FILTERED"]
        if filters.output_modes and not set(filters.output_modes).intersection(manifest.output_modes):
            return False, ["OUTPUT_MODE_FILTERED"]
        if filters.allowed_coordination_modes and not set(filters.allowed_coordination_modes).intersection(
            manifest.allowed_coordination_modes
        ):
            return False, ["COORDINATION_MODE_FILTERED"]
        context_auth_scopes = set(context.get("auth_scopes", [])) | set(filters.required_auth_scopes)
        missing_auth = set(manifest.auth_scopes) - context_auth_scopes
        if missing_auth:
            return False, ["AUTH_SCOPE_MISSING"]
        if side_effect_rank(manifest.side_effects) > side_effect_rank(filters.max_side_effects):
            return False, ["SIDE_EFFECT_FILTERED"]
        if risk_rank(manifest.risk_level) > risk_rank(filters.max_risk_level):
            return False, ["RISK_FILTERED"]
        if filters.require_concurrency_safe and not manifest.concurrency_safe:
            return False, ["CONCURRENCY_FILTERED"]
        if filters.require_read_only and not is_read_only_side_effect(manifest.side_effects):
            return False, ["READ_ONLY_FILTERED"]
        health_status = self._health_status(manifest.id)
        if not filters.include_unhealthy and health_status == CapabilityHealthStatus.unhealthy:
            return False, ["UNHEALTHY_FILTERED"]
        if not filters.include_deprecated and manifest.quality.deprecated:
            return False, ["DEPRECATED_FILTERED"]
        tenant_ids = set(manifest.metadata.get("tenant_ids") or [])
        user_ids = set(manifest.metadata.get("user_ids") or [])
        tenant_id = filters.tenant_id or context.get("tenant_id")
        user_id = filters.user_id or context.get("user_id")
        if tenant_ids and tenant_id not in tenant_ids:
            return False, ["TENANT_FILTERED"]
        if user_ids and user_id not in user_ids:
            return False, ["USER_FILTERED"]
        return True, reasons

    def _score_manifest(self, query: str, manifest: CapabilityManifest) -> tuple[float, list[str]]:
        if not query.strip():
            return 0.0, ["NO_QUERY_SCORE"]
        terms = {term.strip().lower() for term in query.replace("/", " ").replace("_", " ").split() if term.strip()}
        haystack = " ".join(
            [
                manifest.id,
                manifest.name,
                manifest.description,
                manifest.long_description or "",
                " ".join(manifest.tags),
                " ".join(manifest.examples),
            ]
        ).lower()
        anti_haystack = " ".join(manifest.anti_examples).lower()
        matches = sum(1 for term in terms if term in haystack)
        anti_matches = sum(1 for term in terms if term in anti_haystack)
        score = float(matches * 10 - anti_matches * 5)
        if manifest.quality.confidence_score is not None:
            score += manifest.quality.confidence_score
        reason = "QUERY_MATCHED" if matches else "QUERY_NOT_MATCHED"
        return score, [reason]

    def _health_status(self, capability_id: str) -> CapabilityHealthStatus:
        if capability_id in self._health_overrides:
            return self._health_overrides[capability_id]
        manifest = self._manifests.get(capability_id)
        if manifest is None:
            return CapabilityHealthStatus.unknown
        metadata_status = manifest.metadata.get("health_status")
        if metadata_status:
            return CapabilityHealthStatus(metadata_status)
        return CapabilityHealthStatus.healthy

    def _health_report(self, capability_id: str) -> CapabilityHealthReport:
        if capability_id not in self._manifests:
            raise KeyError(f"Capability '{capability_id}' is not registered.")
        adapter = self._adapters.get(capability_id)
        if adapter is None:
            return CapabilityHealthReport(
                capability_id=capability_id,
                status=CapabilityHealthStatus.unhealthy,
                reason_codes=["ADAPTER_MISSING"],
            )
        start = time.perf_counter()
        try:
            report = adapter.health_check()
        except Exception:
            return CapabilityHealthReport(
                capability_id=capability_id,
                status=CapabilityHealthStatus.unhealthy,
                reason_codes=["ADAPTER_HEALTH_CHECK_FAILED"],
            )
        latency_ms = (time.perf_counter() - start) * 1000
        status = self._health_overrides.get(capability_id, report.status)
        return report.model_copy(update={"status": status, "latency_ms": latency_ms})


def _side_effects_from_tool(tool: Any) -> SideEffectLevel:
    permissions = {permission.value for permission in tool.permissions_required}
    if {"filesystem_write", "memory_write", "notification", "external_send", "external_publish"} & permissions:
        return SideEffectLevel.external if {"notification", "external_send", "external_publish"} & permissions else SideEffectLevel.write
    if {"shell", "code_execution", "browser", "network", "credential"} & permissions:
        return SideEffectLevel.external
    if {"filesystem_read", "memory_read"} & permissions:
        return SideEffectLevel.read
    return SideEffectLevel.none
