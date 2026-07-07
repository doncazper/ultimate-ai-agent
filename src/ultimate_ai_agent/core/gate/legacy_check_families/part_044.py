from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart044Mixin:
    """Legacy checks from open_design_governance_docs_present through gate_route_request."""
    def check_open_design_governance_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/design/OPEN_DESIGN_SYSTEM.md",
            "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
            "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
            "docs/design/ACCESSIBILITY_BASELINE.md",
            "docs/design/DESIGN_TOOLING_POLICY.md",
            "docs/design/DESIGN_TOKEN_ROADMAP.md",
            "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
            "docs/design/DESIGN_ARTIFACT_GOVERNANCE.md",
            "docs/design/COMPONENT_TAXONOMY.md",
            "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
        ]
        failures = [
            f"missing design governance doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        design_text = "\n".join(
            self._read(self.root / path).lower() for path in required_docs
        )
        expectations = {
            "design docs missing no-tool-enable boundary": "no design tools are enabled",
            "design docs missing repo-owned source-of-truth boundary": "repo-owned source of truth",
            "design docs missing secret-free visual artifact boundary": (
                "screenshots and design artifacts must not contain secrets"
            ),
            "design docs missing no automatic design-to-code boundary": "no automatic design-to-code",
            "design docs missing no automatic design sync boundary": "no automatic design sync",
            "design docs missing no design SaaS authority boundary": "no design saas is authority",
        }
        for failure, fragment in expectations.items():
            if fragment not in design_text:
                failures.append(failure)

        control_center_docs = [
            "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
            "docs/control_center/FRONTEND_SAFETY_POLICY.md",
            "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE.md",
            "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md",
            "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
        ]
        control_center_text = "\n".join(
            self._read(self.root / path) for path in control_center_docs
        )
        linked_docs = [
            "docs/design/OPEN_DESIGN_SYSTEM.md",
            "docs/design/CONTROL_CENTER_DESIGN_LANGUAGE.md",
            "docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md",
            "docs/design/ACCESSIBILITY_BASELINE.md",
            "docs/design/UI_COPY_AND_ACTION_LANGUAGE.md",
            "docs/design/COMPONENT_TAXONOMY.md",
            "docs/design/RESPONSIVE_LAYOUT_BASELINE.md",
        ]
        failures.extend(
            f"Control Center docs missing design governance link: {path}"
            for path in linked_docs
            if path not in control_center_text
        )
        return self._result(criterion, failures, [*required_docs, *control_center_docs])

    def check_openwebui_ccc_strategy_docs_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/ui/OPENWEBUI_AND_CCC_STRATEGY.md",
            "docs/ui/CLIENT_SURFACE_ROLES.md",
            "docs/ui/OPENWEBUI_INTEGRATION_ROADMAP.md",
            "docs/ui/CCC_NATIVE_CLIENT_STRATEGY.md",
        ]
        failures = [
            f"missing OpenWebUI/CCC strategy doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        ui_text = "\n".join(
            self._read(self.root / path).lower() for path in required_docs
        )
        expectations = {
            "UI strategy docs missing OpenWebUI chat shell boundary": (
                "openwebui is a supported local/dev conversational shell"
            ),
            "UI strategy docs missing Control Center product UI boundary": (
                "first-party product ui path"
            ),
            "UI strategy docs missing OpenWebUI not-brain boundary": "openwebui is not the agent brain",
            "UI strategy docs missing CCC governance/control boundary": "ccc is the governance/control layer",
            "UI strategy docs missing Open Design relationship": "open design does not replace openwebui",
            "UI strategy docs missing no OpenWebUI integration boundary": "no openwebui integration is implemented",
            "UI strategy docs missing CCC Web definition": "ccc web is the current typescript web control center",
            "UI strategy docs missing CCC iOS definition": "ccc ios is a future native mobile control client",
            "UI strategy docs missing CCC Android definition": "ccc android is a future native mobile control client",
            "UI strategy docs missing CCC macOS definition": "ccc macos is a future desktop/local companion client",
            "UI strategy docs missing no native implementation boundary": "no ccc native implementation is added",
            "UI strategy docs missing no native build workflow boundary": "no native build workflow is added",
            "UI strategy docs missing no mobile sensor access boundary": "no mobile sensor access is added",
            "UI strategy docs missing no OS permission integration boundary": "no os permission integration is added",
        }
        for failure, fragment in expectations.items():
            if fragment not in ui_text:
                failures.append(failure)
        return self._result(criterion, failures, required_docs)

    def check_post_m20_roadmap_projection_present(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/CAPABILITY_LAYERING_STRATEGY.md",
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M34_M60_ROADMAP_SUPERSESSION.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/roadmap/ECOSYSTEM_WATCHLIST.md",
            "docs/roadmap/STANDARDS_ALIGNMENT_WATCHLIST.md",
        ]
        failures = [
            f"missing post-M20 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        roadmap_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        version_tuple = self._active_version_tuple()
        expectations = {
            "post-M20 docs missing M21": "m21",
            "post-M20 docs missing M40": "m40",
            "post-M20 docs missing planned/provisional boundary": "planned/provisional",
            "post-M20 docs missing OpenWebUI bridge charter": "openwebui bridge + chat shell integration contract",
            "post-M20 docs missing local model runtime charter": "local model runtime activation contract",
            "post-M20 docs missing first local LLM charter": "first real local llm call",
            "post-M20 docs missing memory charter": "memory provider abstraction",
            "post-M20 docs missing grounded recall charter": "grounded recall router + evidence-linked context pack builder",
            "post-M20 docs missing Tool Broker v2 charter": "tool broker v2 + safe tool intent contracts",
            "post-M20 docs missing M31 tool runtime charter": (
                "real tool runtime adapter, single safe no-op tool"
            ),
        }
        if version_tuple >= (0, 37, 4):
            expectations.update(
                {
                    "post-M20 docs missing M35 safe file review charter": (
                        "safe file review workflow contracts"
                    ),
                    "post-M20 docs missing M38 context proposal charter": (
                        "safe context proposal from approved review"
                    ),
                    "post-M20 docs missing M39 CCC context proposal charter": (
                        "ccc context proposal surface"
                    ),
                    "post-M20 docs missing M40 no-injection handoff charter": (
                        "context handoff approval, no injection"
                    ),
                    "post-M20 docs missing M60 beta freeze charter": (
                        "local developer beta freeze"
                    ),
                }
            )
            if version_tuple >= (0, 38, 0):
                expectations[
                    "post-M20 docs missing M34 broader file capability review release"
                ] = "m34 is implemented/released"
        else:
            expectations.update(
                {
                    "post-M20 docs missing Device Capability Broker charter": (
                        "device capability broker implementation, no sensors"
                    ),
                    "post-M20 docs missing browser automation no-execution charter": (
                        "browser automation contract, no execution"
                    ),
                    "post-M20 docs missing observability charter": "observability export adapters",
                    "post-M20 docs missing eval harness charter": "agent evaluation + regression harness",
                }
            )
        for failure, fragment in expectations.items():
            if fragment not in roadmap_text:
                failures.append(failure)
        if version_tuple >= (0, 44, 0):
            implemented_claim_start = 41
        elif version_tuple >= (0, 43, 0):
            implemented_claim_start = 40
        elif version_tuple >= (0, 42, 0):
            implemented_claim_start = 39
        elif version_tuple >= (0, 41, 0):
            implemented_claim_start = 38
        elif version_tuple >= (0, 40, 0):
            implemented_claim_start = 37
        elif version_tuple >= (0, 39, 0):
            implemented_claim_start = 36
        elif version_tuple >= (0, 38, 0):
            implemented_claim_start = 35
        elif version_tuple >= (0, 37, 0):
            implemented_claim_start = 34
        elif version_tuple >= (0, 36, 0):
            implemented_claim_start = 33
        elif version_tuple >= (0, 35, 0):
            implemented_claim_start = 32
        elif version_tuple >= (0, 34, 0):
            implemented_claim_start = 31
        elif version_tuple >= (0, 33, 0):
            implemented_claim_start = 30
        elif version_tuple >= (0, 32, 0):
            implemented_claim_start = 29
        elif version_tuple >= (0, 31, 0):
            implemented_claim_start = 28
        elif version_tuple >= (0, 30, 0):
            implemented_claim_start = 27
        elif version_tuple >= (0, 29, 0):
            implemented_claim_start = 26
        elif version_tuple >= (0, 28, 0):
            implemented_claim_start = 25
        elif version_tuple >= (0, 27, 0):
            implemented_claim_start = 24
        elif version_tuple >= (0, 26, 0):
            implemented_claim_start = 23
        else:
            implemented_claim_start = 22
        implemented_claims = [
            f"m{number} is implemented" for number in range(implemented_claim_start, 41)
        ]
        if version_tuple < (0, 44, 0):
            implemented_claims.extend(
                [
                    "m21-m40 are implemented",
                    "m21 through m40 are implemented",
                ]
            )
        implemented_claims.append("post-m20 capabilities are implemented")
        if any(claim in roadmap_text for claim in implemented_claims):
            failures.append(
                "post-M20 roadmap docs must not claim future milestone implementation"
            )
        return self._result(criterion, failures, required_docs)

    def _skipped(self, criterion: FoundationGateCriterion) -> FoundationGateResult:
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=FoundationGateStatus.skipped,
            safe_message="No evaluator registered for criterion.",
            warnings=["missing evaluator"],
        )

    def _result(
        self,
        criterion: FoundationGateCriterion,
        failures: List[str],
        evidence_refs: List[str],
        warnings: Optional[List[str]] = None,
    ) -> FoundationGateResult:
        status = (
            FoundationGateStatus.failed if failures else FoundationGateStatus.passed
        )
        return FoundationGateResult(
            criterion_id=criterion.criterion_id,
            status=status,
            safe_message=criterion.failure_message
            if failures
            else f"{criterion.name} passed.",
            evidence_refs=evidence_refs,
            failures=failures,
            warnings=warnings or [],
        )

    def _active_version(self) -> Optional[str]:
        return self._regex_first(
            self.root / "VERSION.md",
            r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?)\*\*",
        )

    def _version_key(self, version: str) -> str:
        return version.replace(".", "_").replace("-", "_")

    def _package_version(self, version: str) -> str:
        if version.endswith("-alpha"):
            return f"{version[:-6]}a0"
        return version

    def _active_version_tuple(self) -> tuple[int, int, int]:
        version = self._active_version() or "0.0.0"
        base_version = version.split("-", 1)[0]
        return tuple(int(part) for part in base_version.split("."))  # type: ignore[return-value]

    def _m60_currentness_marker_present(self, text: str) -> bool:
        if self._active_version_tuple() >= (0, 64, 0):
            return (
                "m60 is implemented/released" in text
                or "v0.64.0 implements m60" in text
            )
        return "m60 remains planned/provisional" in text

    def _append_post_m48_mobile_status_failures(
        self, text: str, failures: List[str]
    ) -> None:
        if self._active_version_tuple() >= (0, 57, 0):
            if (
                "m49 is implemented/released" not in text
                and "v0.53.0 implements m49" not in text
            ):
                failures.append("M49 must be implemented/released after v0.53.0")
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
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
                "m49 is implemented/released" not in text
                and "v0.53.0 implements m49" not in text
            ):
                failures.append("M49 must be implemented/released after v0.53.0")
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
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
                "m49 is implemented/released" not in text
                and "v0.53.0 implements m49" not in text
            ):
                failures.append("M49 must be implemented/released after v0.53.0")
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if (
                "m51 is implemented/released" not in text
                and "v0.55.0 implements m51" not in text
            ):
                failures.append("M51 must be implemented/released after v0.55.0")
            if "m52-m60 remain planned/provisional" not in text:
                failures.append("M52-M60 must remain planned/provisional after M51")
        elif self._active_version_tuple() >= (0, 54, 0):
            if (
                "m49 is implemented/released" not in text
                and "v0.53.0 implements m49" not in text
            ):
                failures.append("M49 must be implemented/released after v0.53.0")
            if (
                "m50 is implemented/released" not in text
                and "v0.54.0 implements m50" not in text
            ):
                failures.append("M50 must be implemented/released after v0.54.0")
            if "m51-m60 remain planned/provisional" not in text:
                failures.append("M51-M60 must remain planned/provisional after M50")
        elif self._active_version_tuple() >= (0, 53, 0):
            if (
                "m49 is implemented/released" not in text
                and "v0.53.0 implements m49" not in text
            ):
                failures.append("M49 must be implemented/released after v0.53.0")
            if "m50-m60 remain planned/provisional" not in text:
                failures.append("M50-M60 must remain planned/provisional after M49")
        elif "m49-m60 remain planned/provisional" not in text:
            failures.append("M49-M60 must remain planned/provisional after M48")

    def _regex_first(self, path: Path, pattern: str) -> Optional[str]:
        match = re.search(pattern, self._read(path))
        return match.group(1) if match else None

    def _openapi_schema(self) -> dict[str, Any]:
        return self._context.openapi_schema()

    def _openapi_paths(self) -> dict[str, Any]:
        return self._context.openapi_paths()

    def _verify_openapi_contract(self, candidate_app: Any | None = None) -> Any:
        return self._context.verify_openapi_contract(candidate_app)

    def _runtime_lines(self) -> Iterable[tuple[str, int, str]]:
        for rel_path in self._tracked_runtime_files():
            if _is_static_safety_scan_allowed_file(rel_path, ()):
                continue
            for line_no, line in enumerate(
                self._read(self.root / rel_path).splitlines(), start=1
            ):
                yield rel_path, line_no, line.strip()

    def _tracked_runtime_files(self) -> List[str]:
        if not self.src_root.exists():
            return []
        files = []
        for path in sorted(self._context.rglob(self.src_root, "*.py")):
            rel_path = str(path.relative_to(self.root))
            if "__pycache__" not in rel_path:
                files.append(rel_path)
        return files

    def _read(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        return self._context.read_text(path, encoding="utf-8")

    def _is_static_scanner_text(self, stripped: str) -> bool:
        return (
            stripped.startswith(('"', "'", "#"))
            or " = [" in stripped
            or " = (" in stripped
            or stripped.startswith(
                ("forbidden = ", "forbidden_starts = ", "forbidden_contains = ")
            )
            or stripped.startswith('if ".get(" in stripped')
        )

    def _m8_gate_manifest(self) -> dict:
        return {
            "adapter_id": "m8_gate_adapter",
            "runtime_kind": "simulated",
            "display_name": "M8 Gate Simulated Adapter",
            "description": "Deterministic simulated adapter for Foundation Gate checks.",
            "supported_provider_kinds": ["local_runtime"],
            "supported_capabilities": ["chat"],
            "safety_mode": "simulated",
            "accepts_model_profile_ids": ["m8_gate_profile"],
            "requires_credential_ref": False,
            "allowed_credential_refs": [],
            "supports_streaming": False,
            "supports_tools": False,
            "supports_json_mode": True,
            "supports_structured_output": True,
            "max_context_tokens": 8192,
            "max_input_tokens": 1024,
            "max_output_tokens": 512,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
            "enabled": True,
        }

    def _m8_gate_request(self) -> dict:
        return {
            "runtime_request_id": "m8_gate_request",
            "run_id": "run_foundation_gate",
            "model_profile_id": "m8_gate_profile",
            "model_id": "m8_gate_model",
            "adapter_id": "m8_gate_adapter",
            "actor_context": self._actor().model_dump(mode="json"),
            "prompt_summary": "Summarize referenced context safely.",
            "input_refs": ["context_pack:m8_gate"],
            "output_format": "text",
            "estimated_input_tokens": 10,
            "max_output_tokens": 10,
            "safety_mode": "simulated",
            "data_classification": {
                "classification": "project_private",
                "source": "foundation_gate",
            },
        }

    def _m85_gate_approval_request(self, subject_id: str = "m85_gate_subject") -> Any:
        from datetime import timedelta

        from ultimate_ai_agent.core.approvals import (
            ApprovalRequest,
            ApprovalRiskLevel,
            ApprovalSubjectType,
        )
        from ultimate_ai_agent.core.time import utc_now

        return ApprovalRequest(
            approval_request_id=f"areq_{subject_id}",
            run_id="run_foundation_gate",
            subject_type=ApprovalSubjectType.model_route,
            subject_id=subject_id,
            actor_context=self._actor(),
            requested_action="route_cloud_model",
            purpose="Foundation Gate approval authority check.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.sensitive_personal,
                source="foundation_gate",
            ),
            resource_refs=["m7_gate_cloud"],
            consent_refs=["consent_foundation_gate"],
            expires_at=utc_now() + timedelta(minutes=30),
        )

    def _m85_runtime_manifest(self) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeAdapterManifest,
            ModelRuntimeKind,
            ModelRuntimeSafetyMode,
        )

        return ModelRuntimeAdapterManifest(
            adapter_id="m85_gate_adapter",
            runtime_kind=ModelRuntimeKind.simulated,
            display_name="M8.5 Gate Simulated Adapter",
            description="Simulated adapter for M8.5 approval checks.",
            supported_provider_kinds=["cloud_provider", "local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.simulated,
            accepts_model_profile_ids=["m7_gate_cloud"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_loopback_endpoint(self) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            LoopbackRuntimeEndpoint,
            ModelRuntimeKind,
        )

        return LoopbackRuntimeEndpoint(
            endpoint_id="m9_gate_loopback",
            base_url="http" + "://127.0.0.1:11434/api/generate",
            allowed_hosts=["127.0.0.1", "localhost", "::1"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id="local_policy_model",
            enabled=True,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _m9_loopback_policy(self) -> Any:
        from ultimate_ai_agent.core.model_runtime import LoopbackRuntimePolicy

        return LoopbackRuntimePolicy(
            policy_id="m9_gate_policy",
            allow_real_loopback_execution=True,
            max_input_tokens=4096,
            max_output_tokens=1024,
        )

    def _m9_runtime_manifest(self) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeAdapterManifest,
            ModelRuntimeKind,
            ModelRuntimeSafetyMode,
        )

        return ModelRuntimeAdapterManifest(
            adapter_id="m9_gate_adapter",
            runtime_kind=ModelRuntimeKind.local_stub,
            display_name="M9 Gate Local Loopback Adapter",
            description="Local/dev loopback adapter for Foundation Gate checks.",
            supported_provider_kinds=["local_runtime"],
            supported_capabilities=["chat"],
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            accepts_model_profile_ids=["m7_gate_local"],
            requires_credential_ref=False,
            allowed_credential_refs=[],
            supports_streaming=False,
            supports_tools=False,
            supports_json_mode=True,
            supports_structured_output=True,
            max_context_tokens=8192,
            max_input_tokens=4096,
            max_output_tokens=1024,
            owner="foundation_gate",
            source="foundation_gate",
            version="0.0.0",
            enabled=True,
        )

    def _m9_runtime_request(self, approval_ref: Optional[str] = None) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            ModelRuntimeOutputFormat,
            ModelRuntimeRequest,
            ModelRuntimeSafetyMode,
        )

        return ModelRuntimeRequest(
            runtime_request_id="m9_gate_runtime_request",
            run_id="run_foundation_gate",
            route_decision_ref="m9_gate_selected_route",
            model_profile_id="m7_gate_local",
            model_id="local_policy_model",
            adapter_id="m9_gate_adapter",
            actor_context=self._actor(),
            prompt_summary="Foundation Gate local loopback metadata check.",
            input_refs=["context_pack:m9_gate"],
            output_format=ModelRuntimeOutputFormat.text,
            estimated_input_tokens=100,
            max_output_tokens=50,
            safety_mode=ModelRuntimeSafetyMode.local_loopback_dev,
            data_classification=DataClassification(
                classification=ClassificationValue.project_private,
                source="foundation_gate",
            ),
            consent_refs=["consent_foundation_gate"],
            approval_ref=approval_ref,
            secret_handle_refs=[],
            event_ref="evt_m9_gate",
            trace_id="trace_m9_gate",
            metadata={"route_reason_codes": ["SELECTED_PROFILE"]},
        )

    def _m10_smoke_endpoint(self, **overrides: Any) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            LoopbackRuntimeEndpoint,
            ModelRuntimeKind,
        )

        payload = {
            "endpoint_id": "m10_gate_smoke_endpoint",
            "base_url": "http" + "://127.0.0.1:11434/api/generate",
            "allowed_hosts": ["127.0.0.1", "localhost", "::1"],
            "runtime_kind": ModelRuntimeKind.local_stub,
            "model_id": "m10_gate_smoke_model",
            "enabled": True,
            "owner": "foundation_gate",
            "source": "foundation_gate",
            "version": "0.0.0",
        }
        payload.update(overrides)
        return LoopbackRuntimeEndpoint(**payload)

    def _m10_smoke_request(self, **overrides: Any) -> Any:
        from ultimate_ai_agent.core.model_runtime import (
            DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
            ManualLoopbackSmokePolicy,
            ManualLoopbackSmokeRequest,
        )

        payload = {
            "smoke_request_id": "m10_gate_smoke_request",
            "run_id": "run_foundation_gate",
            "endpoint": self._m10_smoke_endpoint(),
            "model_id": "m10_gate_smoke_model",
            "approval_ref": "approval_m10_gate",
            "fixed_prompt": DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
            "expected_marker": "UAA_LOCAL_SMOKE_OK",
            "policy": ManualLoopbackSmokePolicy(
                policy_id="m10_gate_smoke_policy", enable_manual_smoke=True
            ),
            "actor_context": self._actor(),
            "data_classification": DataClassification(
                classification=ClassificationValue.public, source="foundation_gate"
            ),
        }
        payload.update(overrides)
        return ManualLoopbackSmokeRequest(**payload)

    def _m105_node_registry(self) -> Any:
        from ultimate_ai_agent.core.remote_workers import (
            NodeCapabilitySet,
            NodeIdentity,
            RemoteNode,
            RemoteNodeRegistry,
            RemoteNodeStatus,
        )

        registry = RemoteNodeRegistry()
        registry.register_node(
            RemoteNode(
                node_id="mock_node",
                identity=NodeIdentity(
                    node_id="mock_node",
                    display_name="Mock Node",
                    owner="foundation_gate",
                    source="foundation_gate",
                    version="0.0.0",
                ),
                status=RemoteNodeStatus.mock_available,
                capabilities=NodeCapabilitySet(),
                allowed_transport_ids=["mock_metadata"],
            )
        )
        return registry

    def _m105_transport_registry(self) -> Any:
        from ultimate_ai_agent.core.remote_workers import (
            default_remote_transport_registry,
        )

        return default_remote_transport_registry()

    def _m105_remote_job(self, **overrides: Any) -> Any:
        from ultimate_ai_agent.core.remote_workers import (
            RemoteAuditContext,
            RemoteJobEnvelope,
            RemoteRiskLevel,
        )

        payload = {
            "job_id": "m105_gate_job",
            "correlation_id": "m105_gate_corr",
            "node_id": "mock_node",
            "transport_id": "mock_metadata",
            "task_summary": "Validate remote worker dry-run metadata.",
            "requested_capabilities": ["dry_run"],
            "risk_level": RemoteRiskLevel.low,
            "audit_context": RemoteAuditContext(
                run_id="run_foundation_gate",
                correlation_id="m105_gate_corr",
                actor_context=self._actor(),
            ),
        }
        payload.update(overrides)
        return RemoteJobEnvelope(**payload)

    def _actor(self) -> ActorContext:
        return ActorContext(
            actor_type=ActorType.system_worker,
            actor_id="foundation_gate",
            authority_source=AuthoritySource.system_policy,
        )

    def _gate_local_profile(
        self,
        cost_per_1k_input_tokens: Optional[float] = None,
        cost_per_1k_output_tokens: Optional[float] = None,
    ) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_local",
            provider_kind=ModelProviderKind.local_runtime,
            runtime_id="rt_gate",
            model_id="local_policy_model",
            display_name="Local Policy Model",
            capabilities=[ModelTaskCapability.chat, ModelTaskCapability.coding],
            privacy_class=ModelPrivacyClass.local_only,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=cost_per_1k_input_tokens,
            cost_per_1k_output_tokens=cost_per_1k_output_tokens,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_cloud_profile(self) -> ModelCapabilityProfile:
        return ModelCapabilityProfile(
            model_profile_id="m7_gate_cloud",
            provider_kind=ModelProviderKind.cloud_provider,
            provider_id="provider_gate",
            model_id="cloud_policy_model",
            display_name="Cloud Policy Model",
            capabilities=[ModelTaskCapability.chat],
            privacy_class=ModelPrivacyClass.cloud_allowed,
            max_context_tokens=8192,
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03,
            enabled=True,
            owner="core.gate",
            source="foundation_gate",
            version="0.0.0",
        )

    def _gate_route_request(
        self,
        profile: ModelCapabilityProfile,
        data_classification: ClassificationValue = ClassificationValue.project_private,
        approval_ref: Optional[str] = None,
        context_budget: Optional[ContextBudget] = None,
        policy: Optional[ModelRoutingPolicy] = None,
    ) -> ModelRouteRequest:
        return ModelRouteRequest(
            request_id="m7_gate_route_policy",
            run_id="run_foundation_gate",
            actor_context=self._actor(),
            task_class="coding",
            prompt_summary="Foundation Gate model routing metadata check.",
            data_classification=DataClassification(
                classification=data_classification, source="foundation_gate"
            ),
            required_capabilities=[ModelTaskCapability.chat],
            estimated_input_tokens=1000,
            estimated_output_tokens=500,
            context_budget=context_budget,
            routing_policy=policy
            or ModelRoutingPolicy(
                policy_id="m7_gate_route_policy",
                required_capabilities=[ModelTaskCapability.chat],
                prefer_local=True,
                allow_cloud=False,
                allow_paid=False,
            ),
            available_profiles=[profile],
            approval_ref=approval_ref,
        )
