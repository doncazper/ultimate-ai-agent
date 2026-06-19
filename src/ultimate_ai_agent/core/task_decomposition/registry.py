from __future__ import annotations

import asyncio
import inspect
import json
import time
from collections.abc import Callable
from typing import Any, Iterable, Optional

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.approvals.enums import ApprovalDecisionStatus, ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.task_decomposition.contracts import (
    SAFE_EXECUTION_MODES,
    CapabilityCallContext,
    CapabilityCallResult,
    CapabilityCallStatus,
    CapabilityCallValidationResult,
    CapabilityContract,
    CapabilityOutcomeMetrics,
    CapabilityOutcomeRecord,
    CapabilityOutcomeStatus,
    CapabilityRoutingCard,
    DataSensitivity,
    ExecutionMode,
    RiskLevel,
    permission_requires_approval,
    risk_rank,
    sensitivity_rank,
)
from ultimate_ai_agent.core.task_decomposition.enums import CapabilityKind, CostHint


Handler = Callable[[dict[str, Any], CapabilityCallContext], Any]


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _tokenize(value: str) -> set[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in value)
    return {part for part in cleaned.split() if part}


def _type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _validate_json_like_schema(value: Any, schema: dict[str, Any] | None, path: str = "$") -> list[str]:
    if not schema:
        return []
    reasons: list[str] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        if not any(_type_matches(value, item) for item in expected_type):
            reasons.append(f"SCHEMA_TYPE_MISMATCH:{path}")
            return reasons
    elif isinstance(expected_type, str) and not _type_matches(value, expected_type):
        reasons.append(f"SCHEMA_TYPE_MISMATCH:{path}")
        return reasons

    if schema.get("enum") is not None and value not in schema["enum"]:
        reasons.append(f"SCHEMA_ENUM_MISMATCH:{path}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                reasons.append(f"SCHEMA_REQUIRED_MISSING:{path}.{key}")
        properties = schema.get("properties", {})
        for key, nested_schema in properties.items():
            if key in value:
                reasons.extend(_validate_json_like_schema(value[key], nested_schema, f"{path}.{key}"))
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in value:
                if key not in allowed:
                    reasons.append(f"SCHEMA_ADDITIONAL_PROPERTY_DENIED:{path}.{key}")

    if isinstance(value, list) and schema.get("items"):
        item_schema = schema["items"]
        for index, item in enumerate(value):
            reasons.extend(_validate_json_like_schema(item, item_schema, f"{path}[{index}]"))

    return reasons


class CapabilityRegistry:
    def __init__(self, approval_authority: LocalApprovalAuthority | None = None):
        self._contracts: dict[str, CapabilityContract] = {}
        self._handlers: dict[str, Handler] = {}
        self._outcomes: dict[str, list[CapabilityOutcomeRecord]] = {}
        self.approval_authority = approval_authority

    def register(self, contract: CapabilityContract, handler: Optional[Handler] = None) -> CapabilityContract:
        validated = CapabilityContract.model_validate(contract.model_dump())
        capability_id = validated.card.id
        self._contracts[capability_id] = validated
        if handler is not None:
            self.register_handler(capability_id, handler)
        return validated

    def register_handler(self, capability_id: str, handler: Handler) -> None:
        if capability_id not in self._contracts:
            raise KeyError(f"Capability '{capability_id}' is not registered.")
        self._handlers[capability_id] = handler

    def get(self, capability_id: str) -> Optional[CapabilityContract]:
        return self._contracts.get(capability_id)

    def cards(self) -> list[CapabilityRoutingCard]:
        return [contract.card for contract in self._contracts.values()]

    def search(
        self,
        query: str,
        kind: CapabilityKind | None = None,
        risk_max: RiskLevel | None = None,
        top_k: int = 8,
    ) -> list[CapabilityRoutingCard]:
        query_tokens = _tokenize(query)
        cards: list[tuple[float, CapabilityRoutingCard]] = []
        for contract in self._contracts.values():
            card = contract.card
            if kind is not None and card.kind != kind:
                continue
            if risk_max is not None and risk_rank(card.risk_level) > risk_rank(risk_max):
                continue
            haystack = " ".join(
                [
                    card.name,
                    card.summary,
                    *card.use_when,
                    *card.do_not_use_when,
                    *card.domains,
                    *card.tags,
                    *card.input_hints,
                    *card.output_hints,
                ]
            )
            haystack_tokens = _tokenize(haystack)
            overlap = len(query_tokens & haystack_tokens)
            score = overlap + card.reliability_score
            if overlap or not query_tokens:
                cards.append((score, card))
        cards.sort(key=lambda item: (-item[0], item[1].id))
        return [card for _score, card in cards[:top_k]]

    def rank_for_task(self, task_intent, candidates: list[CapabilityRoutingCard]) -> list[CapabilityRoutingCard]:
        from ultimate_ai_agent.core.task_decomposition.ranker import CapabilityRanker

        ranker = CapabilityRanker(outcome_metrics=self.metrics())
        scored = [
            (
                ranker.score(task_intent, self._contracts[candidate.id]),
                candidate,
            )
            for candidate in candidates
            if candidate.id in self._contracts
        ]
        scored.sort(key=lambda item: (-item[0].total_score, item[1].id))
        return [candidate for _score, candidate in scored]

    def validate_call(
        self,
        capability_id: str,
        args: dict[str, Any],
        context: CapabilityCallContext | None = None,
    ) -> CapabilityCallValidationResult:
        active_context = context or CapabilityCallContext()
        contract = self.get(capability_id)
        if contract is None:
            return CapabilityCallValidationResult(
                capability_id=capability_id,
                valid=False,
                status=CapabilityCallStatus.unavailable,
                reason_codes=["CAPABILITY_NOT_REGISTERED"],
                safe_message="Capability is not registered.",
            )

        reasons: list[str] = []
        approval_required = False
        capability_approved = self._capability_approved(contract, active_context)
        if contract.execution_mode not in SAFE_EXECUTION_MODES:
            reasons.append("CAPABILITY_EXECUTION_MODE_UNSUPPORTED")

        if risk_rank(contract.card.risk_level) > risk_rank(active_context.max_risk_level) and not capability_approved:
            reasons.append("CAPABILITY_RISK_EXCEEDS_CONTEXT")

        dangerous_permissions = [
            permission for permission in contract.required_permissions if permission_requires_approval(permission)
        ]
        missing_permissions = [
            permission
            for permission in contract.required_permissions
            if permission not in active_context.allowed_permissions and permission not in dangerous_permissions
        ]
        if missing_permissions:
            reasons.append("CAPABILITY_PERMISSION_NOT_ALLOWED")

        if contract.card.requires_approval or dangerous_permissions:
            if not capability_approved:
                reasons.append("CAPABILITY_APPROVAL_REQUIRED")
                approval_required = True

        if sensitivity_rank(contract.data_sensitivity) > sensitivity_rank(active_context.data_sensitivity_ceiling):
            if contract.data_sensitivity in {DataSensitivity.private, DataSensitivity.secret} and not capability_approved:
                reasons.append("CAPABILITY_PRIVATE_DATA_APPROVAL_REQUIRED")
                approval_required = True
            else:
                reasons.append("CAPABILITY_DATA_SENSITIVITY_EXCEEDS_CONTEXT")

        schema_reasons = _validate_json_like_schema(args, contract.input_schema)
        if schema_reasons:
            reasons.extend(schema_reasons)

        reasons = _dedupe(reasons)
        if reasons:
            status = CapabilityCallStatus.approval_required if approval_required else CapabilityCallStatus.validation_failed
            return CapabilityCallValidationResult(
                capability_id=capability_id,
                valid=False,
                status=status,
                reason_codes=reasons,
                safe_message="Capability call failed preflight validation.",
                approval_required=approval_required,
            )

        return CapabilityCallValidationResult(
            capability_id=capability_id,
            valid=True,
            status=CapabilityCallStatus.succeeded,
            reason_codes=["CAPABILITY_CALL_VALIDATED"],
            safe_message="Capability call passed preflight validation.",
        )

    def _capability_approved(self, contract: CapabilityContract, context: CapabilityCallContext) -> bool:
        capability_id = contract.card.id
        if context.is_approved(capability_id):
            return True
        approval_ref = context.approval_refs.get(capability_id)
        if not approval_ref or self.approval_authority is None:
            return False
        decision = self.approval_authority.validate(
            ApprovalValidationRequest(
                approval_ref=approval_ref,
                run_id=context.run_id,
                subject_type=ApprovalSubjectType.tool_request,
                subject_id=capability_id,
                requested_action="invoke_capability",
                actor_context=ActorContext(
                    actor_type=ActorType.orchestrator,
                    actor_id=context.actor_id,
                    authority_source=AuthoritySource.explicit_user_request,
                ),
                resource_refs=[capability_id],
                risk_level=ApprovalRiskLevel(contract.card.risk_level.value),
                data_classification=self._approval_data_classification(contract.data_sensitivity),
                purpose=f"Approve local task decomposition capability {capability_id}.",
            )
        )
        return bool(decision.allowed and decision.status == ApprovalDecisionStatus.approved)

    def _approval_data_classification(self, sensitivity: DataSensitivity) -> DataClassification:
        mapping = {
            DataSensitivity.public: ClassificationValue.public,
            DataSensitivity.internal: ClassificationValue.system_internal,
            DataSensitivity.private: ClassificationValue.project_private,
            DataSensitivity.secret: ClassificationValue.credential_secret,
        }
        return DataClassification(
            classification=mapping[DataSensitivity(sensitivity)],
            source="task_decomposition_capability",
            requires_consent=DataSensitivity(sensitivity) in {DataSensitivity.private, DataSensitivity.secret},
        )

    async def invoke(
        self,
        capability_id: str,
        args: dict[str, Any],
        context: CapabilityCallContext | None = None,
    ) -> CapabilityCallResult:
        active_context = context or CapabilityCallContext()
        validation = self.validate_call(capability_id, args, active_context)
        if not validation.valid:
            status = validation.status
            self.record_outcome(
                capability_id,
                CapabilityOutcomeRecord(
                    capability_id=capability_id,
                    status=CapabilityOutcomeStatus.approval_required
                    if status == CapabilityCallStatus.approval_required
                    else CapabilityOutcomeStatus.validation_failed,
                    safe_summary=validation.safe_message,
                    reason_codes=validation.reason_codes,
                ),
            )
            return CapabilityCallResult(
                capability_id=capability_id,
                status=status,
                reason_codes=validation.reason_codes,
                safe_summary=validation.safe_message,
                attempts=0,
            )

        contract = self._contracts[capability_id]
        handler = self._handlers.get(capability_id)
        if handler is None:
            return CapabilityCallResult(
                capability_id=capability_id,
                status=CapabilityCallStatus.unavailable,
                reason_codes=["CAPABILITY_HANDLER_NOT_REGISTERED"],
                safe_summary="Capability has no registered local handler.",
                attempts=0,
            )

        started = time.perf_counter()
        try:
            value = handler(args, active_context)
            if inspect.isawaitable(value):
                value = await asyncio.wait_for(value, timeout=contract.timeout_s)
            else:
                # Yield once so sync handlers do not starve parallel scheduling in tests.
                await asyncio.sleep(0)
            output = value if isinstance(value, dict) else {"value": value}
            output_reasons = _validate_json_like_schema(output, contract.output_schema)
            if output_reasons:
                status = CapabilityCallStatus.validation_failed
                reason_codes = output_reasons
                safe_summary = "Capability output failed schema validation."
            else:
                status = CapabilityCallStatus.succeeded
                reason_codes = ["CAPABILITY_INVOKED"]
                safe_summary = "Capability invocation completed."
        except TimeoutError:
            output = {}
            status = CapabilityCallStatus.failed
            reason_codes = ["CAPABILITY_TIMEOUT"]
            safe_summary = "Capability invocation timed out."
        except Exception:
            output = {}
            status = CapabilityCallStatus.failed
            reason_codes = ["CAPABILITY_HANDLER_FAILED"]
            safe_summary = "Capability invocation failed without storing private details."

        latency_ms = (time.perf_counter() - started) * 1000
        outcome_status = (
            CapabilityOutcomeStatus.succeeded
            if status == CapabilityCallStatus.succeeded
            else CapabilityOutcomeStatus.validation_failed
            if status == CapabilityCallStatus.validation_failed
            else CapabilityOutcomeStatus.failed
        )
        self.record_outcome(
            capability_id,
            CapabilityOutcomeRecord(
                capability_id=capability_id,
                status=outcome_status,
                latency_ms=latency_ms,
                safe_summary=safe_summary,
                reason_codes=reason_codes,
            ),
        )
        return CapabilityCallResult(
            capability_id=capability_id,
            status=status,
            output=output,
            observations=[safe_summary],
            reason_codes=reason_codes,
            safe_summary=safe_summary,
            attempts=1,
            latency_ms=latency_ms,
        )

    def record_outcome(self, capability_id: str, outcome: CapabilityOutcomeRecord) -> None:
        self._outcomes.setdefault(capability_id, []).append(outcome)

    def metrics(self) -> dict[str, CapabilityOutcomeMetrics]:
        summaries: dict[str, CapabilityOutcomeMetrics] = {}
        for capability_id, records in self._outcomes.items():
            metrics = CapabilityOutcomeMetrics(capability_id=capability_id)
            latencies: list[float] = []
            for record in records:
                metrics.total_calls += 1
                if record.status == CapabilityOutcomeStatus.succeeded:
                    metrics.succeeded += 1
                elif record.status == CapabilityOutcomeStatus.approval_required:
                    metrics.approval_required += 1
                elif record.status == CapabilityOutcomeStatus.validation_failed:
                    metrics.validation_failed += 1
                else:
                    metrics.failed += 1
                if record.latency_ms is not None:
                    latencies.append(record.latency_ms)
                metrics.last_summary = record.safe_summary
            if latencies:
                metrics.average_latency_ms = sum(latencies) / len(latencies)
            summaries[capability_id] = metrics
        return summaries

    def export_json(self, *, indent: int | None = 2) -> str:
        payload = [contract.model_dump(mode="json") for contract in self._contracts.values()]
        return json.dumps(payload, indent=indent, sort_keys=True)

    def import_json(self, data: str) -> None:
        payload = json.loads(data)
        if not isinstance(payload, list):
            raise ValueError("CAPABILITY_REGISTRY_JSON_LIST_REQUIRED")
        for item in payload:
            self.register(CapabilityContract.model_validate(item))

    @classmethod
    def from_json(cls, data: str) -> "CapabilityRegistry":
        registry = cls()
        registry.import_json(data)
        return registry

    def register_tool_manifest(self, manifest) -> CapabilityContract:
        risk_value = getattr(getattr(manifest, "risk_level", None), "value", str(getattr(manifest, "risk_level", "low")))
        mapped_risk = RiskLevel.low if risk_value in {"safe", "low"} else RiskLevel.medium
        if risk_value in {"high", "critical"}:
            mapped_risk = RiskLevel(risk_value)
        contract = CapabilityContract(
            card=CapabilityRoutingCard(
                id=manifest.tool_id,
                name=manifest.display_name,
                version=manifest.version,
                kind=CapabilityKind.tool,
                summary=manifest.description,
                use_when=[manifest.description],
                domains=[str(getattr(manifest, "category", "tool"))],
                tags=["tool-manifest-adapter", str(getattr(manifest, "capability_flag", ""))],
                input_hints=[str(getattr(manifest, "input_schema_ref", "") or "tool request")],
                output_hints=[str(getattr(manifest, "output_schema_ref", "") or "tool result")],
                risk_level=mapped_risk,
                requires_approval=bool(getattr(manifest, "requires_approval", False))
                or mapped_risk in {RiskLevel.high, RiskLevel.critical},
                cost_hint=CostHint.free,
                reliability_score=0.8,
            ),
            input_schema={},
            output_schema={},
            limitations=["Adapter exposes manifest metadata only; handler registration is separate."],
            required_permissions=[str(permission) for permission in getattr(manifest, "permissions_required", [])],
            execution_mode=ExecutionMode.python_callable,
            handler_ref=None,
            timeout_s=30,
            concurrency_limit=1,
        )
        return self.register(contract)
