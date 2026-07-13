from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403
from ultimate_ai_agent.core.sandbox_calculation.static_safety import (
    is_exact_sealed_calculation_subprocess_site,
)


class FoundationGateLegacyChecksPart013Mixin:
    """Legacy checks from m55_redacted_observability_export through m58_dry_run_execution_route_boundary."""

    def check_m55_redacted_observability_export(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/observability/__init__.py",
            "src/ultimate_ai_agent/core/observability/export.py",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT.md",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md",
            "docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md",
            "docs/observability/M55_TO_M56_BOUNDARY.md",
            "tests/test_m55_redacted_observability_export.py",
            "tests/test_m55_gate_integration.py",
        ]
        failures = [
            f"missing M55 redacted observability export file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from datetime import UTC, datetime

            from ultimate_ai_agent.core.hygiene.actor_context import (
                ActorContext,
                ActorType,
                AuthoritySource,
            )
            from ultimate_ai_agent.core.hygiene.policies import (
                ClassificationValue,
                DataClassification,
            )
            from ultimate_ai_agent.core.hygiene.temporal_context import (
                FreshnessClass,
                StalenessPolicy,
                TemporalContext,
            )
            from ultimate_ai_agent.core.ledger import EventLedgerEvent, EventName
            from ultimate_ai_agent.core.observability import (
                ObservabilityExportFormat,
                RedactedObservabilityExportPolicy,
                RedactedObservabilityExportRequest,
                RedactedObservabilityExportStatus,
                build_redacted_observability_export,
                validate_redacted_observability_export_policy,
                validate_redacted_observability_export_request,
            )

            event = EventLedgerEvent(
                event_id="evt_m55_gate",
                event_type="run",
                event_name=EventName.run_completed,
                run_id="run_m55_gate",
                trace_id="trace_m55_gate",
                span_id="span_m55_gate",
                correlation_id="corr_m55_gate",
                actor_context=ActorContext(
                    actor_type=ActorType.orchestrator,
                    actor_id="m55-gate",
                    authority_source=AuthoritySource.explicit_user_request,
                    created_at=datetime.now(UTC),
                ),
                temporal_context=TemporalContext(
                    current_time_utc=datetime.now(UTC),
                    freshness_class=FreshnessClass.daily,
                    staleness_policy=StalenessPolicy.allow_with_label,
                ),
                data_classification=DataClassification(
                    classification=ClassificationValue.project_private,
                    source="m55-gate",
                ),
                event_source="ultimate-ai-agent",
                subject="M55 gate",
                action="summarize",
                outcome="completed",
                status="success",
                severity="info",
                redaction_summary={"status": "redacted"},
                metadata={"safe_summary": "M55 gate safe redacted summary."},
            )
            request = RedactedObservabilityExportRequest(
                request_ref="observability-export-request:m55-gate",
                run_ref="run:run_m55_gate",
                export_ref="observability-export:m55-gate",
                requested_formats=[ObservabilityExportFormat.internal_redacted_json],
                source_event_refs=["event:evt_m55_gate"],
                redaction_policy_ref="redaction-policy:m55-gate",
            )
            bundle = build_redacted_observability_export(request, [event])
            if (
                bundle.status != RedactedObservabilityExportStatus.ready
                or not bundle.items
            ):
                failures.append(
                    "M55 redacted observability export bundle was not ready"
                )
            if (
                bundle.export_performed
                or bundle.external_delivery_performed
                or bundle.raw_prompt_exported
                or bundle.raw_provider_payload_exported
                or bundle.secret_exported
                or bundle.network_call_performed
                or bundle.model_call_performed
                or bundle.memory_write_performed
                or bundle.context_injection_performed
            ):
                failures.append(
                    "M55 bundle performed export, raw leak, network/model/context/memory side effect"
                )
            if bundle.receipt_plan is None:
                failures.append(
                    "M55 bundle did not create a redacted no-effect receipt plan"
                )
            elif (
                bundle.receipt_plan.side_effects_performed
                or bundle.receipt_plan.export_performed
            ):
                failures.append("M55 receipt plan performed side effects or export")
            for request_update, reason in [
                ({"raw_prompt_export_requested": True}, "RAW_PROMPT_EXPORT_DENIED"),
                (
                    {"raw_provider_payload_export_requested": True},
                    "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED",
                ),
                ({"secret_export_requested": True}, "SECRET_EXPORT_DENIED"),
                (
                    {"external_saas_export_requested": True},
                    "EXTERNAL_SAAS_EXPORT_DENIED",
                ),
                ({"network_export_requested": True}, "NETWORK_EXPORT_DENIED"),
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                try:
                    validate_redacted_observability_export_request(
                        request.model_copy(update=request_update)
                    )
                    failures.append(
                        f"M55 unsafe request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M55 unsafe request reason drifted for {reason}: {exc}"
                        )
            try:
                validate_redacted_observability_export_policy(
                    RedactedObservabilityExportPolicy(external_saas_sdk_enabled=True)
                )
                failures.append("M55 unsafe policy flag was not denied")
            except ValueError as exc:
                if "EXTERNAL_SAAS_SDK_DENIED" not in str(exc):
                    failures.append(f"M55 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(
                f"M55 redacted observability export validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "redacted observability export",
            "redacted-only",
            "contract-only",
            "no external saas",
            "no network delivery",
            "no raw prompts",
            "no raw provider payloads",
            "no secrets",
            "no model call",
            "no memory write",
            "no context injection",
            "no backend route",
            "m56 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M55 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m55_observability_export_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "raw_prompt_export_enabled=True",
            "raw_provider_payload_export_enabled=True",
            "raw_private_content_export_enabled=True",
            "secret_export_enabled=True",
            "external_saas_sdk_enabled=True",
            "network_delivery_enabled=True",
            "forensic_trace_export_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "production_authority_enabled=True",
            "export_performed=True",
            "external_delivery_performed=True",
            "raw_prompt_exported=True",
            "raw_provider_payload_exported=True",
            "secret_exported=True",
            "network_call_performed=True",
            "/observability/export",
            "/observability/export/raw",
            "/observability/export/prompts",
            "/observability/export/provider-payloads",
            "/observability/export/saas",
            "/otel/export",
            "/analytics/export",
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
            "src/ultimate_ai_agent/core/observability/export.py",
            "tests/test_m55_redacted_observability_export.py",
            "tests/test_m55_gate_integration.py",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M55 forbidden observability export fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m55_observability_export_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m55_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M55 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m55_roadmap_currentness(
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
            f"missing M55 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.59.0" not in text
            or "m55" not in text
            or "redacted observability export" not in text
        ):
            failures.append(
                "active docs do not identify v0.59.0/M55 Redacted Observability Export"
            )
        if (
            "m55 is implemented/released" not in text
            and "v0.59.0 implements m55" not in text
        ):
            failures.append("active docs do not mark M55 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
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
                "m56 is implemented/released" not in text
                and "v0.60.0 implements m56" not in text
            ):
                failures.append("active docs do not mark M56 implemented/released")
            if (
                "m57-m60 remain planned/provisional" not in text
                and "m58-m60 remain planned/provisional" not in text
            ):
                failures.append("M57-M60 must remain planned/provisional after M56")
        elif "m56-m60 remain planned/provisional" not in text:
            failures.append("M56-M60 must remain planned/provisional after M55")
        forbidden_fragments = [
            "dry-run execution audit harness is implemented",
            "public github readiness is implemented",
            "production authority is implemented",
            "raw prompt export is implemented",
            "provider payload export is implemented",
        ]
        if self._active_version_tuple() >= (0, 63, 0):
            forbidden_fragments.remove("public github readiness is implemented")
        if self._active_version_tuple() < (0, 61, 0):
            forbidden_fragments.append("runtime sandbox architecture is implemented")
        if self._active_version_tuple() < (0, 60, 0):
            forbidden_fragments.extend(
                [
                    "m56 is implemented",
                    "v0.60.0 implements m56",
                    "agent eval regression harness is implemented",
                ]
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M55 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m56_agent_eval_regression_harness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/evals/__init__.py",
            "src/ultimate_ai_agent/core/evals/regression.py",
            "docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md",
            "docs/evals/AGENT_EVAL_REGRESSION_POLICY.md",
            "docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md",
            "docs/evals/M56_TO_M57_BOUNDARY.md",
            "tests/test_m56_agent_eval_regression_harness.py",
            "tests/test_m56_gate_integration.py",
        ]
        failures = [
            f"missing M56 agent eval regression harness file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.evals import (
                AgentEvalCase,
                AgentEvalCaseObservation,
                AgentEvalHarnessPolicy,
                AgentEvalRegressionRunRequest,
                AgentEvalRegressionStatus,
                AgentEvalSuite,
                build_agent_eval_regression_report,
                validate_agent_eval_harness_policy,
                validate_agent_eval_regression_request,
            )

            case = AgentEvalCase(
                case_ref="eval-case:m56-gate",
                suite_ref="eval-suite:m56-gate",
                scenario_ref="scenario:m56-gate",
                expected_outcome_ref="outcome:review-only",
                redacted_input_summary="Gate safe redacted eval case.",
                invariant_refs=[
                    "invariant:no-model-call",
                    "invariant:no-tool-execution",
                ],
                evidence_refs=["evidence:m56-gate"],
            )
            suite = AgentEvalSuite(
                suite_ref="eval-suite:m56-gate",
                baseline_ref="baseline:v0.59.0",
                case_refs=[case.case_ref],
                cases=[case],
                deterministic_seed_ref="seed:m56-gate",
            )
            request = AgentEvalRegressionRunRequest(
                request_ref="eval-request:m56-gate",
                run_ref="eval-run:m56-gate",
                suite_ref=suite.suite_ref,
                case_refs=[case.case_ref],
                baseline_ref=suite.baseline_ref,
            )
            report = build_agent_eval_regression_report(
                request,
                suite,
                [
                    AgentEvalCaseObservation(
                        case_ref=case.case_ref,
                        observed_outcome_ref=case.expected_outcome_ref,
                        safe_observation_summary="Gate safe explicit observation.",
                        evidence_refs=["evidence:m56-observation"],
                    )
                ],
            )
            if (
                report.status != AgentEvalRegressionStatus.passed
                or report.total_cases != 1
            ):
                failures.append(
                    "M56 eval regression report was not passed for matching safe refs"
                )
            if (
                report.model_call_performed
                or report.provider_call_performed
                or report.tool_execution_performed
                or report.network_call_performed
                or report.memory_write_performed
                or report.context_injection_performed
            ):
                failures.append(
                    "M56 eval regression report performed model/tool/network/memory/context side effect"
                )
            if report.receipt_plan is None:
                failures.append(
                    "M56 eval regression report did not include a no-effect receipt plan"
                )
            elif (
                report.receipt_plan.evaluation_performed
                or report.receipt_plan.side_effects_performed
            ):
                failures.append(
                    "M56 eval regression receipt performed evaluation or side effects"
                )
            for request_update, reason in [
                ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
                ({"provider_call_requested": True}, "PROVIDER_CALL_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"raw_prompt_capture_requested": True}, "RAW_PROMPT_CAPTURE_DENIED"),
            ]:
                try:
                    validate_agent_eval_regression_request(
                        request.model_copy(update=request_update)
                    )
                    failures.append(
                        f"M56 unsafe request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M56 unsafe request reason drifted for {reason}: {exc}"
                        )
            try:
                validate_agent_eval_harness_policy(
                    AgentEvalHarnessPolicy(model_call_enabled=True)
                )
                failures.append("M56 unsafe policy flag was not denied")
            except ValueError as exc:
                if "MODEL_CALL_DENIED" not in str(exc):
                    failures.append(f"M56 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M56 agent eval regression validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "agent eval regression harness",
            "deterministic",
            "contract-only",
            "no model call",
            "no provider call",
            "no tool execution",
            "no shell execution",
            "no browser automation",
            "no network access",
            "no memory write",
            "no context injection",
            "no raw prompt",
            "no raw provider payload",
            "no backend route",
            "m57 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M56 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m56_eval_regression_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "model_call_enabled=True",
            "provider_call_enabled=True",
            "tool_execution_enabled=True",
            "shell_execution_enabled=True",
            "browser_automation_enabled=True",
            "network_access_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "raw_prompt_capture_enabled=True",
            "raw_provider_payload_capture_enabled=True",
            "external_dataset_fetch_enabled=True",
            "score_authority_enabled=True",
            "production_authority_enabled=True",
            "evaluation_performed=True",
            "model_call_performed=True",
            "provider_call_performed=True",
            "tool_execution_performed=True",
            "network_call_performed=True",
            "memory_write_performed=True",
            "context_injection_performed=True",
            "/evals/run",
            "/evals/execute",
            "/evals/model-call",
            "/evals/provider-call",
            "/evals/export/raw",
            "/models/call",
            "/provider/call",
            "/context/inject",
            "/memory/write",
            "/tools/execute",
            "/shell/execute",
            "/browser/click",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/evals/regression.py",
            "tests/test_m56_agent_eval_regression_harness.py",
            "tests/test_m56_gate_integration.py",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text and not _is_web_hybrid_promoted_static_fragment(
                        rel, fragment, text
                    ):
                        failures.append(
                            f"M56 forbidden eval harness fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m56_eval_regression_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m56_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M56 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m56_roadmap_currentness(
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
            f"missing M56 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.60.0" not in text
            or "m56" not in text
            or "agent eval regression harness" not in text
        ):
            failures.append(
                "active docs do not identify v0.60.0/M56 Agent Eval Regression Harness"
            )
        if (
            "m56 is implemented/released" not in text
            and "v0.60.0 implements m56" not in text
        ):
            failures.append("active docs do not mark M56 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
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
        elif (
            "m57-m60 remain planned/provisional" not in text
            and "m58-m60 remain planned/provisional" not in text
        ):
            failures.append("M57-M60 must remain planned/provisional after M56")
        for fragment in (
            "m57 is implemented",
            "v0.61.0 implements m57",
            "runtime sandbox architecture is implemented",
            "dry-run execution audit harness is implemented",
            "public github readiness is implemented",
            "production authority is implemented",
            "eval execution api is implemented",
            "model evaluation calls are implemented",
        ):
            if self._active_version_tuple() >= (0, 61, 0) and fragment in {
                "m57 is implemented",
                "v0.61.0 implements m57",
                "runtime sandbox architecture is implemented",
            }:
                continue
            if (
                self._active_version_tuple() >= (0, 63, 0)
                and fragment == "public github readiness is implemented"
            ):
                continue
            if fragment in text:
                failures.append(
                    f"M56 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m57_runtime_sandbox_architecture_review(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/sandbox/__init__.py",
            "src/ultimate_ai_agent/core/sandbox/architecture.py",
            "docs/sandbox/RUNTIME_SANDBOX_ARCHITECTURE_REVIEW.md",
            "docs/sandbox/RUNTIME_SANDBOX_BOUNDARY_POLICY.md",
            "docs/sandbox/RUNTIME_SANDBOX_AUTHORITY_BOUNDARY.md",
            "docs/sandbox/M57_TO_M58_BOUNDARY.md",
            "tests/test_m57_runtime_sandbox_architecture_review.py",
            "tests/test_m57_gate_integration.py",
        ]
        failures = [
            f"missing M57 runtime sandbox architecture review file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.sandbox import (
                RuntimeSandboxArchitecturePolicy,
                RuntimeSandboxArchitectureRequest,
                RuntimeSandboxArchitectureStatus,
                build_runtime_sandbox_architecture_review,
                validate_runtime_sandbox_architecture_policy,
                validate_runtime_sandbox_architecture_request,
            )

            request = RuntimeSandboxArchitectureRequest(
                request_ref="sandbox-review-request:m57-gate",
                review_ref="sandbox-review:m57-gate",
                architecture_ref="sandbox-architecture:m57-gate",
                boundary_refs=["boundary:no-shell-execution", "boundary:no-subprocess"],
                threat_model_refs=[
                    "threat:process-spawn",
                    "threat:filesystem-mutation",
                ],
                audit_requirement_refs=["audit:dry-run-before-execution"],
                safe_summary="Gate safe runtime sandbox architecture review.",
            )
            review = build_runtime_sandbox_architecture_review(request)
            if review.status != RuntimeSandboxArchitectureStatus.reviewed:
                failures.append(
                    "M57 runtime sandbox architecture review did not return reviewed status"
                )
            if (
                not review.architecture_review_only
                or review.runtime_sandbox_enabled
                or review.execution_performed
                or review.subprocess_performed
                or review.shell_execution_performed
                or review.side_effects_performed
            ):
                failures.append(
                    "M57 runtime sandbox architecture review performed runtime side effects"
                )
            if review.receipt_plan is None:
                failures.append(
                    "M57 runtime sandbox architecture review did not include no-effect receipt plan"
                )
            elif (
                review.receipt_plan.side_effects_performed
                or review.receipt_plan.subprocess_performed
            ):
                failures.append("M57 runtime sandbox receipt performed side effects")
            for request_update, reason in [
                ({"sandbox_runtime_requested": True}, "SANDBOX_RUNTIME_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
                ({"m58_dry_run_harness_requested": True}, "M58_DRY_RUN_HARNESS_DENIED"),
            ]:
                try:
                    validate_runtime_sandbox_architecture_request(
                        request.model_copy(update=request_update)
                    )
                    failures.append(
                        f"M57 unsafe request mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M57 unsafe request reason drifted for {reason}: {exc}"
                        )
            try:
                validate_runtime_sandbox_architecture_policy(
                    RuntimeSandboxArchitecturePolicy(sandbox_runtime_enabled=True)
                )
                failures.append("M57 unsafe policy flag was not denied")
            except ValueError as exc:
                if "SANDBOX_RUNTIME_DENIED" not in str(exc):
                    failures.append(f"M57 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(
                f"M57 runtime sandbox architecture validation failed: {exc}"
            )

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "runtime sandbox architecture review",
            "architecture review only",
            "contract-only",
            "no sandbox execution",
            "no subprocess",
            "no shell execution",
            "no process spawn",
            "no file mutation",
            "no network access",
            "no tool execution",
            "no memory write",
            "no context injection",
            "no backend route",
            "no dependency",
            "no production authority",
            "m58 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M57 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m57_runtime_sandbox_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "sandbox_runtime_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "tool_execution_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "side_effects_enabled=True",
            "production_authority_enabled=True",
            "m58_dry_run_harness_enabled=True",
            "subprocess_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
            "/sandbox/run",
            "/sandbox/execute",
            "/process/spawn",
            "/subprocess/run",
            "/shell/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/context/inject",
            "/memory/write",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/sandbox/architecture.py",
            "tests/test_m57_runtime_sandbox_architecture_review.py",
            "tests/test_m57_gate_integration.py",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        if is_exact_sealed_calculation_subprocess_site(
                            rel_path=rel,
                            source=text,
                            fragment=fragment,
                        ):
                            continue
                        failures.append(
                            f"M57 forbidden runtime sandbox fragment in {rel}: {fragment}"
                        )
        required_proof_files = [
            "src/ultimate_ai_agent/core/sandbox_calculation/backend.py",
            "tests/test_sealed_calculation_isolation.py",
            "tests/test_sealed_calculation_mission.py",
            "docs/runtime/UAA_SEALED_CALCULATION_ADAPTER.md",
        ]
        failures.extend(
            f"missing exact sealed calculation proof file: {path}"
            for path in required_proof_files
            if not (self.root / path).exists()
        )
        return self._result(criterion, failures, required_proof_files)

    def check_m57_runtime_sandbox_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m57_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M57 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m57_roadmap_currentness(
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
            f"missing M57 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if (
            "v0.61.0" not in text
            or "m57" not in text
            or "runtime sandbox architecture review" not in text
        ):
            failures.append(
                "active docs do not identify v0.61.0/M57 Runtime Sandbox Architecture Review"
            )
        if (
            "m57 is implemented/released" not in text
            and "v0.61.0 implements m57" not in text
        ):
            failures.append("active docs do not mark M57 implemented/released")
        if self._active_version_tuple() >= (0, 63, 0):
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
            forbidden_fragments = (
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "production authority is implemented",
            )
        elif self._active_version_tuple() >= (0, 62, 0):
            if (
                "m58 is implemented/released" not in text
                and "v0.62.0 implements m58" not in text
            ):
                failures.append("active docs do not mark M58 implemented/released")
            if "m59-m60 remain planned/provisional" not in text:
                failures.append("M59-M60 must remain planned/provisional after M58")
            forbidden_fragments = (
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "public github readiness is implemented",
                "production authority is implemented",
            )
        else:
            if "m58-m60 remain planned/provisional" not in text:
                failures.append("M58-M60 must remain planned/provisional after M57")
            forbidden_fragments = (
                "m58 is implemented",
                "v0.62.0 implements m58",
                "dry-run execution audit harness is implemented",
                "shell execution is implemented",
                "subprocess execution is implemented",
                "process spawn is implemented",
                "public github readiness is implemented",
                "production authority is implemented",
            )
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(
                    f"M57 docs imply forbidden/future capability: {fragment}"
                )
        return self._result(criterion, failures, required_docs)

    def check_m58_dry_run_execution_audit_harness(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/dry_run_audit/__init__.py",
            "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_HARNESS.md",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUDIT_POLICY.md",
            "docs/dry_run_audit/DRY_RUN_EXECUTION_AUTHORITY_BOUNDARY.md",
            "docs/dry_run_audit/M58_TO_M59_BOUNDARY.md",
            "tests/test_m58_dry_run_execution_audit_harness.py",
            "tests/test_m58_gate_integration.py",
        ]
        failures = [
            f"missing M58 dry-run execution audit file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.dry_run_audit import (
                DryRunExecutionAuditIntent,
                DryRunExecutionAuditPolicy,
                DryRunExecutionAuditRequest,
                DryRunExecutionAuditStatus,
                build_dry_run_execution_audit_report,
                validate_dry_run_execution_audit_policy,
                validate_dry_run_execution_audit_request,
            )

            intent = DryRunExecutionAuditIntent(
                intent_ref="dry-run-intent:m58-gate",
                operation_ref="operation:gate-preview",
                target_ref="target:gate-contract",
                requested_capability_refs=[
                    "capability:preview-only",
                    "capability:no-side-effects",
                ],
                safe_summary="Gate safe dry-run audit intent.",
            )
            request = DryRunExecutionAuditRequest(
                request_ref="dry-run-audit-request:m58-gate",
                audit_ref="dry-run-audit:m58-gate",
                sandbox_review_ref="sandbox-review:m57-gate",
                intent_refs=[intent.intent_ref],
                intents=[intent],
                actor_ref="actor:gate-reviewer",
                replay_key_ref="replay-key:m58-gate",
            )
            report = build_dry_run_execution_audit_report(request)
            if report.status != DryRunExecutionAuditStatus.reviewed:
                failures.append(
                    "M58 dry-run audit report did not return reviewed status"
                )
            if (
                not report.dry_run_only
                or report.execution_performed
                or report.tool_execution_performed
                or report.subprocess_performed
                or report.shell_execution_performed
                or report.side_effects_performed
            ):
                failures.append(
                    "M58 dry-run audit report performed runtime side effects"
                )
            if report.receipt_plan is None:
                failures.append(
                    "M58 dry-run audit report did not include no-effect receipt plan"
                )
            elif (
                report.receipt_plan.execution_performed
                or report.receipt_plan.side_effects_performed
            ):
                failures.append("M58 dry-run audit receipt performed side effects")
            for intent_update, reason in [
                ({"execution_requested": True}, "EXECUTION_DENIED"),
                ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
                (
                    {"subprocess_execution_requested": True},
                    "SUBPROCESS_EXECUTION_DENIED",
                ),
                ({"shell_execution_requested": True}, "SHELL_EXECUTION_DENIED"),
                ({"process_spawn_requested": True}, "PROCESS_SPAWN_DENIED"),
                ({"filesystem_mutation_requested": True}, "FILESYSTEM_MUTATION_DENIED"),
                ({"network_access_requested": True}, "NETWORK_ACCESS_DENIED"),
                ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
                ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
            ]:
                mutated_request = request.model_copy(
                    update={"intents": [intent.model_copy(update=intent_update)]}
                )
                try:
                    validate_dry_run_execution_audit_request(mutated_request)
                    failures.append(
                        f"M58 unsafe dry-run intent mutation was not denied: {reason}"
                    )
                except ValueError as exc:
                    if reason not in str(exc):
                        failures.append(
                            f"M58 unsafe dry-run intent reason drifted for {reason}: {exc}"
                        )
            try:
                validate_dry_run_execution_audit_policy(
                    DryRunExecutionAuditPolicy(execution_enabled=True)
                )
                failures.append("M58 unsafe policy flag was not denied")
            except ValueError as exc:
                if "EXECUTION_DENIED" not in str(exc):
                    failures.append(f"M58 unsafe policy reason drifted: {exc}")
        except Exception as exc:
            failures.append(f"M58 dry-run execution audit validation failed: {exc}")

        docs_text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_files
            if path.startswith("docs/") and (self.root / path).exists()
        )
        for fragment in [
            "dry-run execution audit harness",
            "dry-run-only",
            "contract-only",
            "no real execution",
            "no tool execution",
            "no subprocess",
            "no shell execution",
            "no process spawn",
            "no file mutation",
            "no network access",
            "no memory write",
            "no context injection",
            "no backend route",
            "no dependency",
            "no production authority",
            "m59 remains future",
        ]:
            if fragment not in docs_text:
                failures.append(f"M58 docs missing safety fragment: {fragment}")
        return self._result(criterion, failures, required_files)

    def check_m58_dry_run_execution_static_safety(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        forbidden_source_fragments = [
            "execution_enabled=True",
            "tool_execution_enabled=True",
            "subprocess_execution_enabled=True",
            "shell_execution_enabled=True",
            "process_spawn_enabled=True",
            "filesystem_mutation_enabled=True",
            "network_access_enabled=True",
            "model_call_enabled=True",
            "memory_write_enabled=True",
            "context_injection_enabled=True",
            "browser_automation_enabled=True",
            "plugin_execution_enabled=True",
            "remote_execution_enabled=True",
            "side_effects_enabled=True",
            "production_authority_enabled=True",
            "m59_public_readiness_enabled=True",
            "execution_performed=True",
            "tool_execution_performed=True",
            "subprocess_performed=True",
            "shell_execution_performed=True",
            "process_spawn_performed=True",
            "filesystem_mutation_performed=True",
            "network_access_performed=True",
            "subprocess" + ".run(",
            "subprocess" + ".Popen(",
            "os.system(",
            "shell=True",
            "/dry-run/run",
            "/dry-run/execute",
            "/execution/audit/run",
            "/execution/audit/execute",
            "/process/spawn",
            "/subprocess/run",
            "/shell/execute",
            "/tools/execute",
            "/tool-runtime/execute",
            "/context/inject",
            "/memory/write",
        ]
        allowed_files = {
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/openapi.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/gate/evaluators.py",
            "src/ultimate_ai_agent/core/dry_run_audit/harness.py",
            "tests/test_m58_dry_run_execution_audit_harness.py",
            "tests/test_m58_gate_integration.py",
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
                candidate_files.extend(self._context.rglob(root, pattern))
            for path in sorted(candidate_files):
                if not self._context.is_file(path):
                    continue
                rel = self._context.relative_path(path)
                if _is_static_safety_scan_allowed_file(rel, allowed_files):
                    continue
                text = self._context.read_text(path, encoding="utf-8")
                for fragment in forbidden_source_fragments:
                    if fragment in text:
                        if sealed_fragment_allowed(rel, text, fragment):
                            continue
                        failures.append(
                            f"M58 forbidden dry-run execution fragment in {rel}: {fragment}"
                        )
        return self._result(criterion, failures, [])

    def check_m58_dry_run_execution_route_boundary(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m58_openapi_route_failures(self._openapi_paths()))
        except Exception as exc:
            failures.append(f"M58 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
