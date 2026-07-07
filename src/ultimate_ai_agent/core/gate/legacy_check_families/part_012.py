from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart012Mixin:
    """Legacy checks from m50_roadmap_currentness through m54_roadmap_currentness."""
    def check_m50_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M50 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.54.0" not in text
            or "m50" not in text
            or "mobile approval audit hardening" not in text
        ):
            failures.append(
                "active docs do not identify v0.54.0/M50 Mobile Approval Audit Hardening"
            )
        if (
            "m50 is implemented/released" not in text
            and "v0.54.0 implements m50" not in text
        ):
            failures.append("active docs do not mark M50 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if (
                "m53 is implemented/released" not in text
                and "v0.57.0 implements m53" not in text
            ):
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif self._active_version_tuple() >= (0, 55, 0):
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif "m51-m60 remain planned/provisional" not in text:
            failures.append("M51-M60 must remain planned/provisional after M50")
        forbidden_fragments = [
            "mobile sensors are implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 55, 0):
            forbidden_fragments.extend(
                [
                    "m51 is implemented",
                    "v0.55.0 implements m51",
                    "openwebui bridge adapter pilot is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M50 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m51_openwebui_bridge_adapter_pilot(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/adapter.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_PILOT.md",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_POLICY.md",
            "docs/openwebui/OPENWEBUI_BRIDGE_ADAPTER_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/M51_TO_M52_BOUNDARY.md",
            "tests/test_m51_openwebui_bridge_adapter_pilot.py",
        ]
        failures = [
            f"missing M51 OpenWebUI adapter file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIBridgeAdapterRequest,
                OpenWebUIBridgeAdapterStatus,
                adapt_openwebui_bridge_request,
            )

            request = OpenWebUIBridgeAdapterRequest(
                adapter_request_ref="openwebui-bridge-adapter-request:m51-gate",
                session_ref="openwebui-session:m51-gate",
                message_ref="openwebui-message:m51-gate",
                safe_user_summary="User asked for a redacted governance summary.",
            )
            result = adapt_openwebui_bridge_request(request)
            if result.status != OpenWebUIBridgeAdapterStatus.safe_summary_ready:
                failures.append("M51 safe adapter result was not ready")
            for field_name in [
                "raw_prompt_returned",
                "raw_provider_payload_returned",
                "raw_content_returned",
                "model_output_authoritative",
                "openwebui_called",
                "provider_called",
                "tool_executed",
                "memory_written",
                "context_injected",
                "approval_granted",
            ]:
                if getattr(result, field_name):
                    failures.append(
                        f"M51 adapter result enabled forbidden field: {field_name}"
                    )
            if result.side_effects_performed:
                failures.append("M51 adapter result performed side effects")
            try:
                adapt_openwebui_bridge_request(
                    request.model_copy(update={"raw_prompt_present": True})
                )
                failures.append("M51 model_copy raw prompt mutation was not denied")
            except ValueError as exc:
                if "RAW_PROMPT_DENIED" not in str(exc):
                    failures.append(f"M51 raw prompt rejection reason drifted: {exc}")
            try:
                adapt_openwebui_bridge_request(
                    request.model_copy(
                        update={
                            "approval_ref": "approval:m51-gate",
                            "tool_execution_requested": True,
                        }
                    )
                )
                failures.append(
                    "M51 approval_ref/tool execution mutation was not denied"
                )
            except ValueError as exc:
                if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
                    failures.append(f"M51 approval-ref rejection reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M51 OpenWebUI adapter validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui bridge adapter pilot",
            "safe-summary-only",
            "agent core remains authority",
            "openwebui is not the agent brain",
            "no raw prompt",
            "no raw provider payload",
            "no provider call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "m52 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M51 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m51_openwebui_adapter_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_requested=True",
            "live_openwebui_connection_enabled=True",
            "openwebui_network_call_enabled=True",
            "provider_call_enabled=True",
            "provider_call_requested=True",
            "model_authority_enabled=True",
            "model_authority_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "raw_prompt_exposure_enabled=True",
            "raw_prompt_present=True",
            "raw_provider_payload_exposure_enabled=True",
            "raw_provider_payload_present=True",
            "raw_content_allowed=True",
            "raw_content_present=True",
            "openwebui_called=True",
            "provider_called=True",
            "tool_executed=True",
            "memory_written=True",
            "context_injected=True",
            "/openwebui/handoff",
            "/openwebui/runtime/call",
            "/openwebui/provider/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
            "import openwebui\n",
            "from openwebui",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "tests/test_m51_openwebui_bridge_adapter_pilot.py",
            "tests/test_m51_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8").lower()
                for fragment in forbidden_source_fragments:
                    if fragment.lower() in text:
                        failures.append(
                            f"M51 forbidden OpenWebUI adapter fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m51_openwebui_adapter_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m51_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M51 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m51_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M51 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.55.0" not in text
            or "m51" not in text
            or "openwebui bridge adapter pilot" not in text
        ):
            failures.append(
                "active docs do not identify v0.55.0/M51 OpenWebUI Bridge Adapter Pilot"
            )
        if (
            "m51 is implemented/released" not in text
            and "v0.55.0 implements m51" not in text
        ):
            failures.append("active docs do not mark M51 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if (
                "m53 is implemented/released" not in text
                and "v0.57.0 implements m53" not in text
            ):
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        elif self._active_version_tuple() >= (0, 56, 0):
            if (
                "m52 is implemented/released" not in text
                and "v0.56.0 implements m52" not in text
            ):
                failures.append("M52 must be implemented/released after v0.56.0")
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
        elif "m52-m60 remain planned/provisional" not in text:
            failures.append("M52-M60 must remain planned/provisional after M51")
        forbidden_fragments = [
            "openwebui tool execution is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 56, 0):
            forbidden_fragments.extend(
                [
                    "m52 is implemented",
                    "v0.56.0 implements m52",
                    "openwebui safe conversation surface is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M51 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m52_openwebui_safe_conversation_surface(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/openwebui_bridge/conversation.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_SURFACE.md",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_POLICY.md",
            "docs/openwebui/OPENWEBUI_SAFE_CONVERSATION_AUTHORITY_BOUNDARY.md",
            "docs/openwebui/M52_TO_M53_BOUNDARY.md",
            "tests/test_m52_openwebui_safe_conversation_surface.py",
        ]
        failures = [
            f"missing M52 OpenWebUI safe conversation file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.openwebui_bridge import (
                OpenWebUIMessageDirection,
                OpenWebUISafeConversationSurfaceStatus,
                OpenWebUISafeConversationTurn,
                build_openwebui_safe_conversation_surface,
            )

            turn = OpenWebUISafeConversationTurn(
                turn_ref="openwebui-conversation-turn:m52-gate",
                session_ref="openwebui-session:m52-gate",
                message_ref="openwebui-message:m52-gate",
                direction=OpenWebUIMessageDirection.user_to_agent_core_planned,
                safe_summary="User asked for a redacted OpenWebUI conversation summary.",
            )
            surface = build_openwebui_safe_conversation_surface(
                conversation_ref="openwebui-safe-conversation:m52-gate",
                session_ref="openwebui-session:m52-gate",
                safe_title="OpenWebUI safe conversation preview",
                turns=[turn],
            )
            if (
                surface.status
                != OpenWebUISafeConversationSurfaceStatus.safe_review_ready
            ):
                failures.append("M52 safe conversation surface was not ready")
            for field_name in [
                "openwebui_called",
                "provider_called",
                "model_called",
                "model_output_authoritative",
                "tool_executed",
                "memory_written",
                "context_injected",
                "approval_granted",
                "raw_prompt_returned",
                "raw_provider_payload_returned",
                "raw_content_returned",
            ]:
                if getattr(surface, field_name):
                    failures.append(
                        f"M52 surface enabled forbidden field: {field_name}"
                    )
            if surface.side_effects_performed:
                failures.append("M52 surface performed side effects")
            try:
                build_openwebui_safe_conversation_surface(
                    conversation_ref="openwebui-safe-conversation:m52-mutated",
                    session_ref="openwebui-session:m52-gate",
                    safe_title="Mutated unsafe conversation",
                    turns=[
                        turn.model_copy(update={"raw_provider_payload_present": True})
                    ],
                )
                failures.append(
                    "M52 model_copy raw provider payload mutation was not denied"
                )
            except ValueError as exc:
                if "RAW_PROVIDER_PAYLOAD_DENIED" not in str(exc):
                    failures.append(
                        f"M52 raw provider payload rejection reason drifted: {exc}"
                    )
            try:
                build_openwebui_safe_conversation_surface(
                    conversation_ref="openwebui-safe-conversation:m52-approval",
                    session_ref="openwebui-session:m52-gate",
                    safe_title="Approval refs are not authority",
                    turns=[
                        turn.model_copy(
                            update={
                                "approval_ref": "approval:m52-gate",
                                "tool_execution_requested": True,
                            }
                        )
                    ],
                )
                failures.append(
                    "M52 approval_ref/tool execution mutation was not denied"
                )
            except ValueError as exc:
                if "APPROVAL_REF_NOT_AUTHORITY" not in str(exc):
                    failures.append(f"M52 approval-ref rejection reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M52 OpenWebUI safe conversation validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "openwebui safe conversation surface",
            "safe-summary-only",
            "agent core remains authority",
            "openwebui is not the agent brain",
            "no raw prompt",
            "no raw provider payload",
            "no raw content",
            "no provider call",
            "no model call",
            "no model authority",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "m53 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M52 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m52_openwebui_safe_conversation_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "openwebui_runtime_call_requested=True",
            "live_openwebui_connection_enabled=True",
            "openwebui_network_call_enabled=True",
            "provider_call_enabled=True",
            "provider_call_requested=True",
            "model_call_enabled=True",
            "model_call_requested=True",
            "model_authority_enabled=True",
            "model_authority_requested=True",
            "tool_execution_enabled=True",
            "tool_execution_requested=True",
            "memory_write_enabled=True",
            "memory_write_requested=True",
            "context_injection_enabled=True",
            "context_injection_requested=True",
            "raw_prompt_exposure_enabled=True",
            "raw_prompt_present=True",
            "raw_provider_payload_exposure_enabled=True",
            "raw_provider_payload_present=True",
            "raw_content_allowed=True",
            "raw_content_present=True",
            "openwebui_called=True",
            "provider_called=True",
            "model_called=True",
            "tool_executed=True",
            "memory_written=True",
            "context_injected=True",
            "/openwebui/conversation",
            "/openwebui/runtime/call",
            "/openwebui/provider/call",
            "/openwebui/model/call",
            "/openwebui/tools/execute",
            "/openwebui/memory/write",
            "/openwebui/context/inject",
            "/openwebui/raw-payload",
            "/openwebui/raw-prompt",
            "import openwebui\n",
            "from openwebui",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/contracts.py",
            "src/ultimate_ai_agent/core/openwebui_bridge/validation.py",
            "tests/test_m52_openwebui_safe_conversation_surface.py",
            "tests/test_m52_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8").lower()
                for fragment in forbidden_source_fragments:
                    if fragment.lower() in text:
                        failures.append(
                            f"M52 forbidden OpenWebUI safe conversation fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m52_openwebui_safe_conversation_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m52_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M52 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m52_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M52 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.56.0" not in text
            or "m52" not in text
            or "openwebui safe conversation surface" not in text
        ):
            failures.append(
                "active docs do not identify v0.56.0/M52 OpenWebUI Safe Conversation Surface"
            )
        if (
            "m52 is implemented/released" not in text
            and "v0.56.0 implements m52" not in text
        ):
            failures.append("active docs do not mark M52 implemented/released")
        if self._active_version_tuple() >= (0, 57, 0):
            if (
                "m53 is implemented/released" not in text
                and "v0.57.0 implements m53" not in text
            ):
                failures.append("M53 must be implemented/released after v0.57.0")
            if (
                "m54-m60 remain planned/provisional" not in text
                and "m55-m60 remain planned/provisional" not in text
                and "m56-m60 remain planned/provisional" not in text
                and "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
                and "m59-m60 remain planned/provisional" not in text
                and not self._m60_currentness_marker_present(text)
            ):
                failures.append("M54-M60 must remain planned/provisional after M53")
        else:
            if "m53-m60 remain planned/provisional" not in text:
                failures.append("M53-M60 must remain planned/provisional after M52")
            for fragment in (
                "m53 is implemented",
                "v0.57.0 implements m53",
                "controlled tool expansion review is implemented",
            ):
                if fragment in text:
                    failures.append(
                        f"M52 docs imply forbidden/future capability: {fragment}"
                    )
        for fragment in (
            "openwebui tool execution is implemented",
            "provider call is implemented",
            "model authority is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ):
            if fragment in text:
                failures.append(
                    f"M52 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m53_controlled_tool_expansion_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/expansion_review.py",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_REVIEW.md",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_POLICY.md",
            "docs/tools/CONTROLLED_TOOL_EXPANSION_AUTHORITY_BOUNDARY.md",
            "docs/tools/M53_TO_M54_BOUNDARY.md",
            "tests/test_m53_controlled_tool_expansion_review.py",
            "tests/test_m53_gate_integration.py",
        ]
        failures = [
            f"missing M53 controlled tool expansion review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools import (
                ControlledToolExpansionCandidate,
                ControlledToolExpansionPolicy,
                ControlledToolExpansionReviewStatus,
                ToolExpansionCapabilityKind,
                evaluate_controlled_tool_expansion_candidate,
                validate_controlled_tool_expansion_candidate,
                validate_controlled_tool_expansion_policy,
            )

            candidate = ControlledToolExpansionCandidate(
                candidate_ref="tool-expansion-candidate:m53-gate",
                safe_name="Metadata-only review candidate",
                capability_kind=ToolExpansionCapabilityKind.safe_metadata_review,
                safe_summary="Review future tool capability metadata without enablement.",
            )
            decision = evaluate_controlled_tool_expansion_candidate(candidate)
            if decision.status != ControlledToolExpansionReviewStatus.review_ready:
                failures.append(
                    "M53 safe metadata review candidate was not review-ready"
                )
            if (
                not decision.review_allowed
                or decision.execution_allowed
                or decision.tool_enablement_allowed
            ):
                failures.append("M53 decision did not remain review-only")
            if decision.receipt_plan is None:
                failures.append("M53 decision did not create a no-enable receipt plan")
            elif (
                decision.receipt_plan.execution_performed
                or decision.receipt_plan.tool_enabled
                or decision.receipt_plan.side_effects_performed
            ):
                failures.append(
                    "M53 receipt plan performed execution, enablement, or side effects"
                )
            future_decision = evaluate_controlled_tool_expansion_candidate(
                ControlledToolExpansionCandidate(
                    candidate_ref="tool-expansion-candidate:m53-shell_execution",
                    safe_name="Future shell execution review",
                    capability_kind=ToolExpansionCapabilityKind.shell_execution,
                    safe_summary="Review a future tool capability without enabling it.",
                )
            )
            if (
                future_decision.status
                != ControlledToolExpansionReviewStatus.future_milestone
            ):
                failures.append(
                    "M53 effectful candidate did not require a future milestone"
                )
            for candidate_update, reason in [
                ({"execution_requested": True}, "TOOL_EXPANSION_EXECUTION_DENIED"),
                ({"tool_enablement_requested": True}, "TOOL_ENABLEMENT_DENIED"),
                (
                    {"contains_raw_provider_payload": True},
                    "RAW_PROVIDER_PAYLOAD_DENIED",
                ),
                ({"approval_ref": "approval:m53-gate"}, "APPROVAL_REF_NOT_AUTHORITY"),
            ]:
                try:
                    validate_controlled_tool_expansion_candidate(
                        candidate.model_copy(update=candidate_update)
                    )
                    failures.append(
                        f"M53 unsafe candidate mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M53 unsafe candidate reason drifted for {reason}: {exc}"
                        )
            try:
                validate_controlled_tool_expansion_policy(
                    ControlledToolExpansionPolicy(shell_execution_enabled=True)
                )
                failures.append("M53 unsafe policy flag was not denied")
            except ValueError as exc:
                if "SHELL_EXECUTION_DENIED" not in str(exc):
                    failures.append(f"M53 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M53 controlled tool expansion validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "controlled tool expansion review",
            "review-only",
            "planning-only",
            "no tool execution",
            "no tool enablement",
            "no shell execution",
            "no network tool",
            "no provider model call",
            "no browser automation execution",
            "no plugin enablement",
            "no mobile sensor access",
            "no remote execution",
            "no raw file browsing",
            "no raw file export",
            "no full-file read",
            "no memory write",
            "no context injection",
            "no backend route",
            "m54 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M53 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m53_controlled_tool_expansion_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "shell_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "unrestricted_network_tools_enabled=True",
            "provider_model_calls_enabled=True",
            "model_authority_enabled=True",
            "browser_automation_execution_enabled=True",
            "plugin_enablement_enabled=True",
            "mobile_sensor_access_enabled=True",
            "remote_execution_enabled=True",
            "raw_file_browsing_enabled=True",
            "raw_file_export_enabled=True",
            "full_file_read_enabled=True",
            "file_mutation_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "credentials_cookie_handling_enabled=True",
            "external_saas_analytics_sdk_enabled=True",
            "production_authority_enabled=True",
            "execution_allowed=True",
            "tool_enablement_allowed=True",
            "/tools/expand",
            "/tools/register",
            "/tools/enable",
            "/tools/run",
            "/tools/execute",
            "/shell/execute",
            "/network/request",
            "/provider/call",
            "/models/call",
            "/browser/click",
            "/plugins/enable",
            "/memory/write",
            "/context/inject",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/tools/expansion_review.py",
            "apps/control-center/src/App.test.tsx",
            "tests/test_m53_controlled_tool_expansion_review.py",
            "tests/test_m53_gate_integration.py",
        }
        source_roots = [
            self.root / "src" / "ultimate_ai_agent" / "core" / "beta_freeze",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M53 forbidden controlled tool expansion fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m53_controlled_tool_expansion_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m53_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M53 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m53_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M53 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.57.0" not in text
            or "m53" not in text
            or "controlled tool expansion review" not in text
        ):
            failures.append(
                "active docs do not identify v0.57.0/M53 Controlled Tool Expansion Review"
            )
        if (
            "m53 is implemented/released" not in text
            and "v0.57.0 implements m53" not in text
        ):
            failures.append("active docs do not mark M53 implemented/released")
        if (
            "m54-m60 remain planned/provisional" not in text
            and "m55-m60 remain planned/provisional" not in text
            and "m56-m60 remain planned/provisional" not in text
            and "m57-m60 remain planned/provisional" not in text
            and "m58-m60 remain planned/provisional" not in text
            and "m59-m60 remain planned/provisional" not in text
            and not self._m60_currentness_marker_present(text)
        ):
            failures.append("M54-M60 must remain planned/provisional after M53")
        forbidden_fragments = [
            "tool execution is implemented",
            "shell execution is implemented",
            "provider model call is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 58, 0):
            forbidden_fragments.extend(
                [
                    "m54 is implemented",
                    "v0.58.0 implements m54",
                    "safe media metadata inspector is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M53 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m54_safe_media_metadata_inspector(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/media/__init__.py",
            "src/ultimate_ai_agent/core/media/metadata.py",
            "docs/media/SAFE_MEDIA_METADATA_INSPECTOR.md",
            "docs/media/SAFE_MEDIA_METADATA_POLICY.md",
            "docs/media/SAFE_MEDIA_METADATA_AUTHORITY_BOUNDARY.md",
            "docs/media/M54_TO_M55_BOUNDARY.md",
            "tests/test_m54_safe_media_metadata_inspector.py",
            "tests/test_m54_gate_integration.py",
        ]
        failures = [
            f"missing M54 safe media metadata file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.media import (
                MediaInspectionKind,
                SafeMediaMetadataPolicy,
                SafeMediaMetadataRequest,
                SafeMediaMetadataStatus,
                inspect_safe_media_metadata,
                validate_safe_media_metadata_policy,
                validate_safe_media_metadata_request,
            )

            request = SafeMediaMetadataRequest(
                request_ref="media-metadata-request:m54-gate",
                media_ref="media:m54-gate",
                safe_path_ref="safe-path:m54-gate.jpg",
                inspection_kind=MediaInspectionKind.image_metadata,
                declared_media_type="image/jpeg",
                declared_byte_size=2048,
            )
            decision = inspect_safe_media_metadata(request)
            if (
                decision.status != SafeMediaMetadataStatus.metadata_ready
                or not decision.metadata_ready
            ):
                failures.append(
                    "M54 safe media metadata request was not metadata-ready"
                )
            if (
                decision.raw_media_returned
                or decision.raw_media_stored
                or decision.original_file_modified
                or decision.ocio_transform_performed
                or decision.ai_gamut_expansion_performed
                or decision.model_call_performed
                or decision.context_injection_performed
            ):
                failures.append(
                    "M54 decision performed raw media output, mutation, transform, model, or context side effect"
                )
            if decision.receipt_plan is None:
                failures.append(
                    "M54 decision did not create a metadata-only receipt plan"
                )
            elif (
                decision.receipt_plan.side_effects_performed
                or decision.receipt_plan.raw_media_stored
            ):
                failures.append(
                    "M54 receipt plan stored raw media or performed side effects"
                )
            denied = inspect_safe_media_metadata(
                request.model_copy(
                    update={
                        "request_ref": "media-metadata-request:m54-unsupported",
                        "declared_media_type": "application/octet-stream",
                    }
                )
            )
            if denied.status != SafeMediaMetadataStatus.denied:
                failures.append("M54 unsupported media type was not denied")
            for request_update, reason in [
                ({"raw_media_requested": True}, "RAW_MEDIA_EXPORT_DENIED"),
                ({"full_file_read_requested": True}, "FULL_FILE_READ_DENIED"),
                ({"ocio_transform_requested": True}, "OCIO_TRANSFORM_DENIED"),
                ({"ai_gamut_expansion_requested": True}, "AI_GAMUT_EXPANSION_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                (
                    {"contains_secret_like_metadata": True},
                    "SECRET_LIKE_METADATA_DENIED",
                ),
            ]:
                try:
                    validate_safe_media_metadata_request(
                        request.model_copy(update=request_update)
                    )
                    failures.append(
                        f"M54 unsafe request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M54 unsafe request reason drifted for {reason}: {exc}"
                        )
            try:
                validate_safe_media_metadata_policy(
                    SafeMediaMetadataPolicy(raw_media_export_enabled=True)
                )
                failures.append("M54 unsafe policy flag was not denied")
            except ValueError as exc:
                if "RAW_MEDIA_EXPORT_DENIED" not in str(exc):
                    failures.append(f"M54 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M54 safe media metadata validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "safe media metadata inspector",
            "metadata-only",
            "no raw media export",
            "no raw media storage",
            "no full-file read",
            "no file mutation",
            "no original overwrite",
            "no ocio transform",
            "no ai gamut expansion",
            "no model call",
            "no context injection",
            "no backend route",
            "m55 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M54 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m54_safe_media_metadata_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "raw_media_export_enabled=True",
            "raw_media_storage_enabled=True",
            "full_file_read_enabled=True",
            "file_mutation_enabled=True",
            "original_overwrite_enabled=True",
            "ocio_transform_enabled=True",
            "ai_gamut_expansion_enabled=True",
            "model_call_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "raw_media_returned=True",
            "raw_media_stored=True",
            "original_file_modified=True",
            "ocio_transform_performed=True",
            "ai_gamut_expansion_performed=True",
            "model_call_performed=True",
            "context_injection_performed=True",
            "/media/read/raw",
            "/media/export",
            "/media/transform/ocio",
            "/media/gamut/expand",
            "/models/call",
            "/provider/call",
            "/context/inject",
            "/memory/write",
            "/tools/execute",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/media/metadata.py",
            "tests/test_m54_safe_media_metadata_inspector.py",
            "tests/test_m54_gate_integration.py",
        }
        source_roots = [
            self.root / "src",
            self.root / "apps" / "control-center" / "src",
            self.root / "apps" / "ccc-ios",
        ]
        for root in source_roots:
            if not root.exists():
                continue
            candidate_files = []
            for pattern in (
                "*.py",
                "*.ts",
                "*.tsx",
                "*.js",
                "*.jsx",
                "*.swift",
                "*.yml",
                "*.yaml",
            ):
                candidate_files.extend(root.rglob(pattern))
            for path in sorted(candidate_files):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.root).as_posix()
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = path.read_text(encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        failures.append(
                            f"M54 forbidden media metadata fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m54_safe_media_metadata_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m54_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M54 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m54_roadmap_currentness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "README.md",
            "VERSION.md",
            "docs/canonical/09_roadmap.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/MILESTONE_CHARTERS.md",
        ]
        failures = [
            f"missing M54 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.58.0" not in text
            or "m54" not in text
            or "safe media metadata inspector" not in text
        ):
            failures.append(
                "active docs do not identify v0.58.0/M54 Safe Media Metadata Inspector"
            )
        if (
            "m54 is implemented/released" not in text
            and "v0.58.0 implements m54" not in text
        ):
            failures.append("active docs do not mark M54 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
            if (
                "m55 is implemented/released" not in text
                and "v0.59.0 implements m55" not in text
            ):
                failures.append("active docs do not mark M55 implemented/released")
            if (
                "m56 is implemented/released" not in text
                and "v0.60.0 implements m56" not in text
            ):
                failures.append("active docs do not mark M56 implemented/released")
            if (
                "m57 is implemented/released" not in text
                and "v0.61.0 implements m57" not in text
            ):
                failures.append("active docs do not mark M57 implemented/released")
            if (
                "m58 is implemented/released" not in text
                and "v0.62.0 implements m58" not in text
            ):
                failures.append("active docs do not mark M58 implemented/released")
            if (
                "m59 is implemented/released" not in text
                and "v0.63.0 implements m59" not in text
            ):
                failures.append("active docs do not mark M59 implemented/released")
            if not self._m60_currentness_marker_present(text):
                failures.append("M60 currentness marker is missing after M59")
        elif self._active_version_tuple() >= (0, 62, 0):
            if (
                "m55 is implemented/released" not in text
                and "v0.59.0 implements m55" not in text
            ):
                failures.append("active docs do not mark M55 implemented/released")
            if (
                "m56 is implemented/released" not in text
                and "v0.60.0 implements m56" not in text
            ):
                failures.append("active docs do not mark M56 implemented/released")
            if (
                "m57 is implemented/released" not in text
                and "v0.61.0 implements m57" not in text
            ):
                failures.append("active docs do not mark M57 implemented/released")
            if (
                "m58 is implemented/released" not in text
                and "v0.62.0 implements m58" not in text
            ):
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
        elif self._active_version_tuple() >= (0, 60, 0):
            if (
                "m55 is implemented/released" not in text
                and "v0.59.0 implements m55" not in text
            ):
                failures.append("active docs do not mark M55 implemented/released")
            if (
                "m56 is implemented/released" not in text
                and "v0.60.0 implements m56" not in text
            ):
                failures.append("active docs do not mark M56 implemented/released")
            if (
                "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
            ):
                failures.append("M57-M60 must remain planned/provisional after M56")
        elif self._active_version_tuple() >= (0, 59, 0):
            if (
                "m55 is implemented/released" not in text
                and "v0.59.0 implements m55" not in text
            ):
                failures.append("active docs do not mark M55 implemented/released")
            if "m56-m60 remain planned/provisional" not in text:
                failures.append("M56-M60 must remain planned/provisional after M55")
        elif "m55-m60 remain planned/provisional" not in text:
            failures.append("M55-M60 must remain planned/provisional after M54")
        forbidden_fragments = [
            "ocio deterministic transform preview is implemented",
            "ai gamut expansion is implemented",
            "raw media export is implemented",
            "model call is implemented",
            "context injection is implemented",
            "production authority is implemented",
        ]
        if self._active_version_tuple() < (0, 59, 0):
            forbidden_fragments.extend(
                [
                    "m55 is implemented",
                    "v0.59.0 implements m55",
                    "redacted observability export is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M54 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)
