from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart006Mixin:
    """Legacy checks from m26_grounded_recall_context_pack_safe through m28_m29_remains_future."""
    def check_m26_grounded_recall_context_pack_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/recall/__init__.py",
            "src/ultimate_ai_agent/core/recall/enums.py",
            "src/ultimate_ai_agent/core/recall/candidates.py",
            "src/ultimate_ai_agent/core/recall/router.py",
            "src/ultimate_ai_agent/core/recall/context_pack.py",
            "src/ultimate_ai_agent/core/recall/manifests.py",
            "src/ultimate_ai_agent/core/recall/policy.py",
            "src/ultimate_ai_agent/core/recall/validation.py",
            "tests/test_grounded_recall_contracts.py",
            "tests/test_grounded_recall_router.py",
            "tests/test_context_pack_builder.py",
            "tests/test_context_pack_no_injection.py",
            "tests/test_recall_source_priority.py",
            "tests/test_recall_no_raw_content.py",
            "tests/test_recall_no_vector_embeddings.py",
            "tests/test_recall_no_memory_writes.py",
            "tests/test_m26_gate_integration.py",
            "docs/recall/GROUNDED_RECALL_ROUTER.md",
            "docs/recall/CONTEXT_PACK_BUILDER.md",
            "docs/recall/RECALL_SOURCE_PRIORITY.md",
            "docs/recall/RECALL_CANDIDATE_POLICY.md",
            "docs/recall/CONTEXT_PACK_SAFETY.md",
            "docs/recall/RECALL_NON_GOALS.md",
            "docs/recall/M26_TO_M27_BOUNDARY.md",
        ]
        failures = [
            f"missing M26 recall/context-pack file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.recall import (
                ContextPackBuildRequest,
                GroundedRecallManifest,
                GroundedRecallRequest,
                RecallCandidate,
                RecallCandidateStatus,
                RecallDecisionStatus,
                RecallSourceKind,
                build_evidence_linked_context_pack,
                recall_source_priority_rank,
                route_grounded_recall,
            )

            manifest = GroundedRecallManifest(baseline_version="0.30.1")
            if manifest.context_injection_enabled:
                failures.append("M26 manifest enables context injection")
            if (
                manifest.vector_search_enabled
                or manifest.embeddings_enabled
                or manifest.semantic_search_enabled
            ):
                failures.append(
                    "M26 manifest enables vector, embedding, or semantic search"
                )
            if (
                manifest.external_retrieval_enabled
                or manifest.web_search_enabled
                or manifest.source_crawling_enabled
            ):
                failures.append(
                    "M26 manifest enables external retrieval, web search, or source crawling"
                )
            if manifest.automatic_memory_write_enabled:
                failures.append("M26 manifest enables automatic memory writes")
            if manifest.backend_routes_added:
                failures.append("M26 manifest adds backend routes")
            if manifest.model_provider_calls_enabled or manifest.tool_execution_enabled:
                failures.append(
                    "M26 manifest enables model/provider calls or tool execution"
                )

            request = GroundedRecallRequest(
                request_id="recall:req:m26-gate",
                query_summary="Need safe M26 context.",
                candidates=[
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.reviewed_memory,
                        safe_summary="Reviewed memory reminder.",
                        memory_refs=["memory:m26"],
                        token_estimate=6,
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:canonical",
                        source_ref="canonical:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Canonical M26 summary.",
                        evidence_refs=["evidence:m26"],
                        token_estimate=5,
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:random",
                        source_ref="random:m26",
                        source_kind=RecallSourceKind.unknown,
                        safe_summary="Unknown source summary.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:model",
                        source_ref="model:m26",
                        source_kind=RecallSourceKind.model_output,
                        safe_summary="Blocked model output summary.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory-as-canonical",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Memory source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:model-as-canonical",
                        source_ref="model:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Model output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:runtime-as-canonical",
                        source_ref="runtime:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Runtime output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:openwebui-as-canonical",
                        source_ref="openwebui:m26",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="OpenWebUI output source priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:memory-as-evidence",
                        source_ref="memory:m26",
                        source_kind=RecallSourceKind.evidence_manifest,
                        safe_summary="Memory evidence priority upgrade attempt.",
                    ),
                    RecallCandidate(
                        candidate_ref="recall:candidate:stale",
                        source_ref="canonical:stale",
                        source_kind=RecallSourceKind.canonical_document,
                        safe_summary="Stale source summary.",
                        status=RecallCandidateStatus.stale,
                    ),
                ],
                max_context_tokens=100,
            )
            decision = route_grounded_recall(request)
            if decision.status != RecallDecisionStatus.allowed:
                failures.append(
                    "M26 grounded recall did not allow safe selected candidates"
                )
            if [item.candidate_ref for item in decision.selected] != [
                "recall:candidate:canonical",
                "recall:candidate:memory",
            ]:
                failures.append(
                    "M26 grounded recall did not preserve source priority over memory"
                )
            excluded_reasons = {
                reason for item in decision.excluded for reason in item.reason_codes
            }
            for reason in [
                "UNKNOWN_SOURCE_KIND_DENIED",
                "ARBITRARY_SOURCE_REF_DENIED",
                "SOURCE_REF_KIND_MISMATCH_DENIED",
                "MEMORY_SOURCE_PRIORITY_UPGRADE_DENIED",
                "MODEL_OUTPUT_RECALL_DENIED",
                "RUNTIME_OUTPUT_RECALL_DENIED",
                "OPENWEBUI_OUTPUT_RECALL_DENIED",
                "MODEL_OUTPUT_EXCLUDED",
                "RUNTIME_OUTPUT_EXCLUDED",
                "OPENWEBUI_OUTPUT_EXCLUDED",
                "STALE_SOURCE_EXCLUDED",
            ]:
                if reason not in excluded_reasons:
                    failures.append(
                        f"M26 grounded recall missing exclusion reason: {reason}"
                    )
            excluded_refs = {item.candidate_ref for item in decision.excluded}
            for candidate_ref in [
                "recall:candidate:memory-as-canonical",
                "recall:candidate:model-as-canonical",
                "recall:candidate:runtime-as-canonical",
                "recall:candidate:openwebui-as-canonical",
                "recall:candidate:memory-as-evidence",
            ]:
                if candidate_ref not in excluded_refs:
                    failures.append(
                        f"M26 grounded recall selected mismatched source identity: {candidate_ref}"
                    )
            if not decision.no_memory_write_performed:
                failures.append("M26 grounded recall performed a memory write")
            if not decision.no_external_retrieval_performed:
                failures.append("M26 grounded recall performed external retrieval")
            if not decision.no_vector_search_performed:
                failures.append("M26 grounded recall performed vector search")
            if not decision.no_context_injection_performed:
                failures.append("M26 grounded recall performed context injection")

            pack = build_evidence_linked_context_pack(
                ContextPackBuildRequest(
                    pack_id="ctxpack:m26-gate",
                    request_id="ctxpack:req:m26-gate",
                    recall_decision=decision,
                    max_context_tokens=100,
                )
            )
            if (
                not pack.items
                or pack.context_injection_performed
                or pack.raw_content_included
            ):
                failures.append(
                    "M26 context pack is empty or includes forbidden runtime/raw behavior"
                )
            pack_refs = {item.candidate_ref for item in pack.items}
            if any(
                ref.endswith("as-canonical") or ref.endswith("as-evidence")
                for ref in pack_refs
            ):
                failures.append("M26 context pack included mismatched source identity")
            if pack.memory_write_performed or pack.external_retrieval_performed:
                failures.append(
                    "M26 context pack performed memory write or external retrieval"
                )
            if recall_source_priority_rank(
                RecallSourceKind.canonical_document
            ) >= recall_source_priority_rank(RecallSourceKind.reviewed_memory):
                failures.append(
                    "M26 source priority lets memory outrank canonical sources"
                )

            recall_source = "\n".join(
                self._read(path)
                for path in (
                    self.root / "src" / "ultimate_ai_agent" / "core" / "recall"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
                "import chromadb",
                "import faiss",
                "import pgvector",
                "import qdrant",
                "import weaviate",
                "import pinecone",
                "import tokenizers",
                "import tiktoken",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "localmemorystore",
                "memorywriterequest",
            )
            failures.extend(
                f"M26 recall module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in recall_source
            )
        except Exception as exc:
            failures.append(
                f"M26 grounded recall/context-pack validation failed: {exc}"
            )

        return self._result(criterion, failures, required_files)

    def check_m26_recall_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m26_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M26 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m26_m27_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
        ]
        failures = [
            f"missing M26 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.30.0" in text
            and "grounded recall router + evidence-linked context pack builder" in text
        ):
            if "implemented/released" not in text:
                failures.append("M26 docs do not mark v0.30.0 implemented/released")
        else:
            failures.append(
                "M26 docs do not mention v0.30.0 Grounded Recall Router + Evidence-Linked Context Pack Builder"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 32, 0):
            if (
                "v0.32.0" in text
                and "approval authority v2 + action policy expansion" in text
            ):
                if "implemented/released" not in text:
                    failures.append(
                        "M28 docs must mark v0.32.0 implemented/released after M28"
                    )
            else:
                failures.append(
                    "M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion"
                )
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        elif version_tuple >= (0, 31, 0):
            if (
                "v0.31.0" in text
                and "tool broker v2 + safe tool intent contracts" in text
            ):
                if "implemented/released" not in text:
                    failures.append(
                        "M27 docs must mark v0.31.0 implemented/released after M27"
                    )
            else:
                failures.append(
                    "M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts"
                )
        else:
            if "v0.31.0 | m27" in text and "planned/provisional" not in text:
                failures.append("M27 roadmap row is not planned/provisional")
            forbidden_m27_fragments = (
                "m27 is implemented",
                "v0.31.0 implements m27",
                "mcp runtime is implemented",
                "agent skills runtime is implemented",
                "agents.md runtime loading is implemented",
                "plugin enablement is implemented",
            )
            failures.extend(
                f"M26 docs imply M27 implementation: {fragment}"
                for fragment in forbidden_m27_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m27_tool_broker_v2_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/v2/__init__.py",
            "src/ultimate_ai_agent/core/tools/v2/enums.py",
            "src/ultimate_ai_agent/core/tools/v2/contracts.py",
            "src/ultimate_ai_agent/core/tools/v2/catalog.py",
            "src/ultimate_ai_agent/core/tools/v2/broker.py",
            "src/ultimate_ai_agent/core/tools/v2/validation.py",
            "tests/test_tool_broker_v2_contracts.py",
            "tests/test_m27_gate_integration.py",
            "docs/tools/TOOL_BROKER_V2.md",
            "docs/tools/SAFE_TOOL_INTENT_CONTRACTS.md",
            "docs/tools/TOOL_AUTHORITY_BOUNDARY.md",
            "docs/tools/TOOL_INTENT_RECEIPT_PLAN.md",
            "docs/tools/M27_TO_M28_BOUNDARY.md",
        ]
        failures = [
            f"missing M27 Tool Broker v2 file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from pydantic import ValidationError

            from ultimate_ai_agent.core.tools.v2 import (
                ToolApprovalRequirement,
                ToolAuthorityLevel,
                ToolBrokerV2Manifest,
                ToolCatalogEntry,
                ToolExecutionMode,
                ToolInputBoundary,
                ToolInputTrustLevel,
                ToolIntent,
                ToolIntentDecisionStatus,
                ToolRiskClass,
                ToolSideEffectKind,
                ToolTargetKind,
                ToolTargetRef,
                build_default_tool_catalog,
                evaluate_tool_intent,
            )

            manifest = ToolBrokerV2Manifest(baseline_version="0.31.0")
            if (
                manifest.tool_execution_enabled
                or manifest.backend_execution_routes_added
            ):
                failures.append("M27 manifest enables tool execution or backend routes")
            if (
                manifest.shell_execution_enabled
                or manifest.network_calls_enabled
                or manifest.browser_automation_enabled
            ):
                failures.append(
                    "M27 manifest enables shell, network, or browser automation"
                )
            if (
                manifest.plugin_enablement_enabled
                or manifest.memory_writes_enabled
                or manifest.event_ledger_mutation_enabled
            ):
                failures.append(
                    "M27 manifest enables plugin, memory, or Event Ledger mutation"
                )
            if (
                manifest.model_provider_calls_enabled
                or manifest.context_pack_authority_enabled
            ):
                failures.append(
                    "M27 manifest enables model calls or context-pack authority"
                )

            def safe_intent(**overrides: Any) -> Any:
                data = {
                    "intent_id": "tool-intent:m27-gate",
                    "tool_id": "file.metadata_preview",
                    "intent_summary": "Preview safe file metadata.",
                    "target": ToolTargetRef(
                        target_ref="file:m27", target_kind=ToolTargetKind.file_ref
                    ),
                    "input_boundary": ToolInputBoundary(
                        input_refs=["file:m27"],
                        input_trust_level=ToolInputTrustLevel.user_provided_refs,
                    ),
                    "requested_execution_mode": ToolExecutionMode.preview_only,
                    "declared_risk_class": ToolRiskClass.low,
                    "declared_side_effects": [ToolSideEffectKind.none],
                    "approval_requirement": ToolApprovalRequirement.not_required,
                    "authority_level": ToolAuthorityLevel.validation_only,
                }
                data.update(overrides)
                return ToolIntent(**data)

            safe_decision = evaluate_tool_intent(
                safe_intent(), catalog=build_default_tool_catalog()
            )
            if safe_decision.status != ToolIntentDecisionStatus.preview_allowed:
                failures.append(
                    "M27 safe metadata preview intent was not allowed for preview"
                )
            if (
                safe_decision.execution_allowed
                or not safe_decision.no_tool_execution_performed
            ):
                failures.append(
                    "M27 safe preview decision allowed or performed execution"
                )
            if (
                not safe_decision.receipt_plan
                or safe_decision.receipt_plan.execution_performed
            ):
                failures.append(
                    "M27 safe preview receipt plan is missing or executable"
                )

            side_effect_catalog = {
                "file.write_preview": ToolCatalogEntry(
                    tool_id="file.write_preview",
                    display_name="Write preview",
                    target_kind=ToolTargetKind.file_ref,
                    allowed_execution_modes=[ToolExecutionMode.preview_only],
                    risk_class=ToolRiskClass.high,
                    side_effects=[ToolSideEffectKind.file_write],
                    approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
                )
            }
            side_effect_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.high,
                    declared_side_effects=[ToolSideEffectKind.file_write],
                    approval_requirement=ToolApprovalRequirement.validated_local_approval_required,
                    approval_ref="approval_test_m27",
                ),
                catalog=side_effect_catalog,
            )
            for reason in ["TOOL_SIDE_EFFECTS_DENIED", "APPROVAL_REF_NOT_AUTHORITY"]:
                if reason not in side_effect_decision.reason_codes:
                    failures.append(f"M27 side-effect probe missing reason: {reason}")
            if (
                side_effect_decision.execution_allowed
                or side_effect_decision.status
                == ToolIntentDecisionStatus.preview_allowed
            ):
                failures.append("M27 side-effecting tool intent was allowed")

            context_pack_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.high,
                    declared_side_effects=[ToolSideEffectKind.file_write],
                    context_pack_refs=["context-pack:m26"],
                ),
                catalog=side_effect_catalog,
            )
            if "CONTEXT_PACK_NOT_AUTHORITY" not in context_pack_decision.reason_codes:
                failures.append(
                    "M27 context-pack authority probe did not deny context pack refs as authority"
                )

            mismatch_decision = evaluate_tool_intent(
                safe_intent(
                    target=ToolTargetRef(
                        target_ref="memory:m27", target_kind=ToolTargetKind.file_ref
                    )
                ),
                catalog=build_default_tool_catalog(),
            )
            if "TOOL_TARGET_KIND_MISMATCH_DENIED" not in mismatch_decision.reason_codes:
                failures.append(
                    "M27 target mismatch probe did not deny mismatched target ref/kind"
                )

            unknown_decision = evaluate_tool_intent(
                safe_intent(
                    target=ToolTargetRef(
                        target_ref="random:m27", target_kind=ToolTargetKind.unknown
                    )
                ),
                catalog=build_default_tool_catalog(),
            )
            if "UNKNOWN_TOOL_TARGET_DENIED" not in unknown_decision.reason_codes:
                failures.append("M27 unknown target probe did not deny unknown target")

            risk_decision = evaluate_tool_intent(
                safe_intent(
                    tool_id="file.write_preview",
                    declared_risk_class=ToolRiskClass.low,
                    declared_side_effects=[ToolSideEffectKind.none],
                ),
                catalog=side_effect_catalog,
            )
            for reason in [
                "TOOL_RISK_DOWNGRADE_DENIED",
                "TOOL_SIDE_EFFECTS_HIDDEN_DENIED",
            ]:
                if reason not in risk_decision.reason_codes:
                    failures.append(
                        f"M27 risk/side-effect downgrade probe missing reason: {reason}"
                    )

            try:
                ToolInputBoundary(input_refs=["file:m27"], contains_model_output=True)
                failures.append("M27 input boundary allowed model output")
            except ValidationError:
                pass

            v2_source = "\n".join(
                self._read(path)
                for path in (
                    self.root / "src" / "ultimate_ai_agent" / "core" / "tools" / "v2"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
                "subprocess",
                "os.system(",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M27 Tool Broker v2 module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in v2_source
            )
        except Exception as exc:
            failures.append(f"M27 Tool Broker v2 validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m27_tool_broker_v2_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m27_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M27 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m27_m28_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/tools/M27_TO_M28_BOUNDARY.md",
        ]
        failures = [
            f"missing M27 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.31.0" in text and "tool broker v2 + safe tool intent contracts" in text:
            if "implemented/released" not in text:
                failures.append("M27 docs do not mark v0.31.0 implemented/released")
        else:
            failures.append(
                "M27 docs do not mention v0.31.0 Tool Broker v2 + Safe Tool Intent Contracts"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 32, 0):
            if "approval authority v2 + action policy expansion" not in text:
                failures.append(
                    "M27 docs do not describe the M28 Approval Authority v2 handoff"
                )
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
        else:
            if "m28-m40 remain planned/provisional" not in text:
                failures.append("M28-M40 must remain planned/provisional after M27")
            forbidden_m28_fragments = (
                "m28 is implemented",
                "v0.32.0 implements m28",
                "real tool execution is implemented",
                "durable action registry runtime is implemented",
                "production tool authority is implemented",
            )
            failures.extend(
                f"M27 docs imply M28 implementation: {fragment}"
                for fragment in forbidden_m28_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m28_approval_authority_v2_action_policy_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/approvals/v2/__init__.py",
            "src/ultimate_ai_agent/core/approvals/v2/enums.py",
            "src/ultimate_ai_agent/core/approvals/v2/contracts.py",
            "src/ultimate_ai_agent/core/approvals/v2/policies.py",
            "src/ultimate_ai_agent/core/approvals/v2/validation.py",
            "tests/test_approval_authority_v2_contracts.py",
            "tests/test_m28_gate_integration.py",
            "docs/approvals/APPROVAL_AUTHORITY_V2.md",
            "docs/approvals/ACTION_POLICY.md",
            "docs/approvals/APPROVAL_GRANT_BINDING.md",
            "docs/approvals/APPROVAL_EXPIRY_REVOCATION_REPLAY.md",
            "docs/approvals/ACTION_RISK_AND_SIDE_EFFECT_POLICY.md",
            "docs/approvals/APPROVAL_REF_NOT_AUTHORITY.md",
            "docs/approvals/ACTION_POLICY_DECISION_ENVELOPE.md",
            "docs/approvals/APPROVAL_RECEIPT_PLAN.md",
            "docs/approvals/APPROVAL_AUTHORITY_V2_NON_GOALS.md",
            "docs/approvals/M28_TO_M29_BOUNDARY.md",
        ]
        failures = [
            f"missing M28 Approval Authority v2 file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import timedelta

            from ultimate_ai_agent.core.approvals.v2 import (
                ActionIntent,
                ActionKind,
                ActionRef,
                ActionRiskLevel,
                ActionSideEffectClass,
                ActorRef,
                ActorTrustLevel,
                ApprovalAuthorityV2Manifest,
                ApprovalDecisionStatus,
                ApprovalGrant,
                ApprovalGrantStatus,
                ApprovalScope,
                ApprovalScopeKind,
                ResourceRef,
                ResourceRefKind,
                ActionPolicy,
                build_approval_authority_v2_manifest,
                evaluate_action_policy,
            )
            from ultimate_ai_agent.core.time import utc_now

            manifest = build_approval_authority_v2_manifest(baseline_version="0.32.1")
            if not isinstance(manifest, ApprovalAuthorityV2Manifest):
                failures.append(
                    "M28 manifest builder did not return ApprovalAuthorityV2Manifest"
                )
            manifest_flags = [
                manifest.action_execution_enabled,
                manifest.execution_authorized,
                manifest.execution_performed,
                manifest.tool_execution_enabled,
                manifest.filesystem_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.network_action_enabled,
                manifest.browser_action_enabled,
                manifest.mobile_action_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enable_enabled,
                manifest.model_action_enabled,
                manifest.wildcard_approval_enabled,
                manifest.approval_test_refs_enabled,
                manifest.backend_execution_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.production_authority_enabled,
            ]
            if any(manifest_flags):
                failures.append(
                    "M28 manifest enables forbidden runtime/action authority"
                )

            actor = ActorRef(
                actor_ref="actor:gate-m28", trust_level=ActorTrustLevel.user
            )
            action = ActionRef(
                action_ref="action:gate-m28-read-metadata",
                action_kind=ActionKind.read_metadata,
                risk_level=ActionRiskLevel.low,
                side_effect_class=ActionSideEffectClass.read_only_metadata,
                safe_summary="Read metadata only.",
            )
            resource = ResourceRef(
                resource_ref="file_ref:gate-m28",
                resource_kind=ResourceRefKind.file_ref,
                safe_label="Gate metadata ref.",
            )
            expires_at = utc_now() + timedelta(minutes=15)
            scope = ApprovalScope(
                scope_ref="scope:gate-m28",
                scope_kind=ApprovalScopeKind.single_action,
                actor_ref=actor.actor_ref,
                action_ref=action.action_ref,
                resource_ref=resource.resource_ref,
                expires_at=expires_at,
                replay_nonce="nonce:gate-m28",
            )
            intent = ActionIntent(
                intent_id="action-intent:gate-m28",
                actor=actor,
                action=action,
                resource=resource,
                safe_summary="Evaluate a safe read-metadata action.",
                input_refs=["file_ref:gate-m28"],
            )
            grant = ApprovalGrant(
                grant_ref="approval:gate-m28",
                actor_ref=actor.actor_ref,
                action_ref=action.action_ref,
                resource_ref=resource.resource_ref,
                scope=scope,
                expires_at=expires_at,
                replay_nonce="nonce:gate-m28",
            )
            safe_decision = evaluate_action_policy(
                intent, grant=grant, replay_nonce="nonce:gate-m28"
            )
            if safe_decision.status != ApprovalDecisionStatus.allowed_for_policy:
                failures.append(
                    "M28 safe read-metadata action was not allowed for policy"
                )
            if not safe_decision.allowed_for_policy:
                failures.append(
                    "M28 safe read-metadata action did not return allowed_for_policy"
                )
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append("M28 safe decision authorized or performed execution")
            if (
                not safe_decision.receipt_plan
                or safe_decision.receipt_plan.execution_performed
            ):
                failures.append(
                    "M28 safe decision receipt plan is missing or executable"
                )

            def require_denial(decision: Any, required_reason: str, label: str) -> None:
                if (
                    decision.allowed_for_policy
                    or decision.execution_authorized
                    or decision.execution_performed
                ):
                    failures.append(f"M28 denied probe was allowed: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(
                        f"M28 denied probe missing {required_reason}: {label}"
                    )

            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"approval_ref": "approval:arbitrary"})
                ),
                "APPROVAL_REF_NOT_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"approval_ref": "approval_test_gate_m28"})
                ),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test_ ref",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"consent_ref": "consent:gate-m28"})
                ),
                "CONSENT_REF_NOT_AUTHORITY",
                "consent_ref alone",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"contains_raw_prompt": True}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "RAW_PROMPT_DENIED",
                "model_copy raw prompt revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"contains_raw_model_output": True}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "RAW_MODEL_OUTPUT_DENIED",
                "model_copy raw model output revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"metadata": {"token": "abc123"}}),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "SECRET_METADATA_DENIED",
                "model_copy secret metadata revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(
                        update={"grant_ref": "approval_test_gate_m28"}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_TEST_REF_DENIED",
                "model_copy approval_test grant revalidation",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant,
                    policy=ActionPolicy().model_copy(
                        update={"safe_summary": "contains token=abc123"}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "ACTION_POLICY_SECRET_CONTENT_DENIED",
                "model_copy action policy revalidation",
            )

            wildcard_scope = scope.model_copy(
                update={
                    "scope_kind": ApprovalScopeKind.blocked_wildcard,
                    "action_ref": "*",
                }
            )
            wildcard_grant = grant.model_copy(
                update={"scope": wildcard_scope, "action_ref": "*"}
            )
            require_denial(
                evaluate_action_policy(
                    intent, grant=wildcard_grant, replay_nonce="nonce:gate-m28"
                ),
                "WILDCARD_SCOPE_DENIED",
                "wildcard scope",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(
                        update={"expires_at": utc_now() - timedelta(minutes=1)}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_GRANT_EXPIRED",
                "expired grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(
                        update={"status": ApprovalGrantStatus.revoked}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_GRANT_REVOKED",
                "revoked grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(
                        update={"used_replay_nonces": ["nonce:gate-m28"]}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_REPLAY_DETECTED",
                "replayed grant",
            )
            require_denial(
                evaluate_action_policy(
                    intent,
                    grant=grant.model_copy(update={"actor_ref": "actor:gate-mismatch"}),
                    replay_nonce="nonce:gate-m28",
                ),
                "APPROVAL_ACTOR_MISMATCH",
                "actor mismatch",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="memory:gate-m28",
                                resource_kind=ResourceRefKind.memory_ref,
                                safe_label="Memory recall ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "MEMORY_REF_NOT_AUTHORITY",
                "memory ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="model:gate-m28",
                                resource_kind=ResourceRefKind.model_output_ref,
                                safe_label="Model output ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "MODEL_OUTPUT_NOT_AUTHORITY",
                "model output ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="context-pack:gate-m28",
                                resource_kind=ResourceRefKind.context_pack_ref,
                                safe_label="Context pack ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "CONTEXT_PACK_NOT_AUTHORITY",
                "context pack ref authority",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(
                        update={
                            "resource": ResourceRef(
                                resource_ref="tool-intent:gate-m27",
                                resource_kind=ResourceRefKind.tool_intent_ref,
                                safe_label="Tool intent ref.",
                            )
                        }
                    ),
                    grant=grant,
                    replay_nonce="nonce:gate-m28",
                ),
                "TOOL_INTENT_NOT_AUTHORITY",
                "tool intent ref authority",
            )
            write_action = ActionRef(
                action_ref="action:gate-m28-file-write",
                action_kind=ActionKind.file_write_planned,
                risk_level=ActionRiskLevel.high,
                side_effect_class=ActionSideEffectClass.local_mutation_blocked,
                safe_summary="Blocked file write plan.",
            )
            require_denial(
                evaluate_action_policy(
                    intent.model_copy(update={"action": write_action}),
                    grant=grant.model_copy(
                        update={"action_ref": write_action.action_ref}
                    ),
                    replay_nonce="nonce:gate-m28",
                ),
                "ACTION_KIND_DENIED",
                "effectful action",
            )
            try:
                ActionIntent(
                    intent_id="action-intent:gate-m28-raw",
                    actor=actor,
                    action=action,
                    resource=resource,
                    safe_summary="Raw action input probe.",
                    contains_raw_prompt=True,
                )
                failures.append("M28 action intent allowed raw prompt content")
            except ValidationError:
                pass
            try:
                ActionIntent(
                    intent_id="action-intent:gate-m28-secret",
                    actor=actor,
                    action=action,
                    resource=resource,
                    safe_summary="Secret input probe.",
                    metadata={"token": "abc123"},
                )
                failures.append("M28 action intent allowed secret-like metadata")
            except ValidationError:
                pass

            v2_source = "\n".join(
                self._read(path)
                for path in (
                    self.root
                    / "src"
                    / "ultimate_ai_agent"
                    / "core"
                    / "approvals"
                    / "v2"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
                "subprocess",
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M28 Approval Authority v2 module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in v2_source
            )
        except Exception as exc:
            failures.append(f"M28 Approval Authority v2 validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m28_action_policy_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m28_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M28 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m28_m29_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/approvals/M28_TO_M29_BOUNDARY.md",
        ]
        failures = [
            f"missing M28 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.32.0" in text
            and "approval authority v2 + action policy expansion" in text
        ):
            if "implemented/released" not in text:
                failures.append("M28 docs do not mark v0.32.0 implemented/released")
        else:
            failures.append(
                "M28 docs do not mention v0.32.0 Approval Authority v2 + Action Policy Expansion"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 35, 0):
            if "m29 agent task planning engine" not in text:
                failures.append(
                    "M28 docs do not describe the M29 Agent Task Planning Engine handoff"
                )
            if (
                "m30" not in text
                or "multi-step execution framework" not in text
                or "implemented/released" not in text
            ):
                failures.append("M28 docs do not acknowledge implemented v0.34.0 / M30")
            if (
                "m31" not in text
                or "real tool runtime adapter" not in text
                or "implemented/released" not in text
            ):
                failures.append("M28 docs do not acknowledge implemented v0.35.0 / M31")
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m32-m40 remain planned/provisional" not in text:
                failures.append("M32-M40 must remain planned/provisional after M31")
        elif version_tuple >= (0, 34, 0):
            if "m29 agent task planning engine" not in text:
                failures.append(
                    "M28 docs do not describe the M29 Agent Task Planning Engine handoff"
                )
            if (
                "m30" not in text
                or "multi-step execution framework" not in text
                or "implemented/released" not in text
            ):
                failures.append("M28 docs do not acknowledge implemented v0.34.0 / M30")
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
        elif version_tuple >= (0, 33, 0):
            if "m29 agent task planning engine" not in text:
                failures.append(
                    "M28 docs do not describe the M29 Agent Task Planning Engine handoff"
                )
            if "m30-m40 remain planned/provisional" not in text:
                failures.append("M30-M40 must remain planned/provisional after M29")
        else:
            if version_tuple >= (0, 38, 0):
                if "m36-m60 remain planned/provisional" not in text:
                    failures.append("M36-M60 must remain planned/provisional after M34")
            elif version_tuple >= (0, 37, 4):
                if "m34-m60 remain planned/provisional" not in text:
                    failures.append(
                        "M34-M60 must remain planned/provisional after v0.37.4"
                    )
            elif "m29-m40 remain planned/provisional" not in text:
                failures.append("M29-M40 must remain planned/provisional after M28")
            forbidden_m29_fragments = (
                "m29 is implemented",
                "v0.33.0 implements m29",
                "action execution is implemented",
                "tool execution is implemented",
                "production approval authority is implemented",
            )
            failures.extend(
                f"M28 docs imply M29 implementation: {fragment}"
                for fragment in forbidden_m29_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)
