from __future__ import annotations

from ultimate_ai_agent.core.gate.legacy_support import *  # noqa: F401,F403


class FoundationGateLegacyChecksPart007Mixin:
    """Legacy checks from m29_task_planning_engine_contract_safe through m31_tool_runtime_openapi_routes_unchanged."""
    def check_m29_task_planning_engine_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/planning/__init__.py",
            "src/ultimate_ai_agent/core/planning/enums.py",
            "src/ultimate_ai_agent/core/planning/contracts.py",
            "src/ultimate_ai_agent/core/planning/validation.py",
            "src/ultimate_ai_agent/core/planning/planner.py",
            "src/ultimate_ai_agent/core/planning/manifests.py",
            "tests/test_task_planning_contracts.py",
            "tests/test_task_plan_validation.py",
            "tests/test_task_plan_dependencies.py",
            "tests/test_task_plan_no_execution.py",
            "tests/test_m29_gate_integration.py",
            "docs/planning/TASK_PLANNING_ENGINE.md",
            "docs/planning/TASK_GOAL_STEP_PLAN_CONTRACTS.md",
            "docs/planning/TASK_DEPENDENCY_GRAPH.md",
            "docs/planning/TASK_INPUT_BOUNDARY.md",
            "docs/planning/TASK_RISK_AND_AUTHORITY_POLICY.md",
            "docs/planning/TASK_PLAN_DECISION_ENVELOPE.md",
            "docs/planning/TASK_PLAN_RECEIPT_PLAN.md",
            "docs/planning/TASK_PLANNING_NON_GOALS.md",
            "docs/planning/M29_TO_M30_BOUNDARY.md",
        ]
        failures = [
            f"missing M29 Task Planning Engine file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.planning import (
                PlanInputTrustLevel,
                TaskDependency,
                TaskGoal,
                TaskPlan,
                TaskPlanDecisionStatus,
                TaskPlanningManifest,
                TaskPlanningRequest,
                TaskRiskLevel,
                TaskStep,
                TaskStepInputBoundary,
                TaskStepKind,
                build_task_planning_manifest,
                evaluate_task_plan,
            )

            manifest = build_task_planning_manifest(baseline_version="0.33.0")
            if not isinstance(manifest, TaskPlanningManifest):
                failures.append(
                    "M29 manifest builder did not return TaskPlanningManifest"
                )
            manifest_flags = [
                manifest.task_execution_enabled,
                manifest.auto_run_enabled,
                manifest.scheduler_enabled,
                manifest.background_worker_enabled,
                manifest.tool_execution_enabled,
                manifest.action_execution_enabled,
                manifest.file_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.network_call_enabled,
                manifest.model_provider_call_enabled,
                manifest.browser_automation_enabled,
                manifest.mobile_device_access_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enablement_enabled,
                manifest.backend_task_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.context_injection_enabled,
                manifest.production_authority_enabled,
            ]
            if any(manifest_flags):
                failures.append(
                    "M29 manifest enables forbidden execution/runtime authority"
                )

            safe_step = TaskStep(
                step_id="step:gate-m29-review",
                step_kind=TaskStepKind.review_metadata,
                safe_summary="Review safe metadata refs.",
                input_boundary=TaskStepInputBoundary(input_refs=["canonical:gate-m29"]),
                declared_risk_level=TaskRiskLevel.low,
            )
            safe_plan = TaskPlan(
                plan_id="plan:gate-m29",
                goal=TaskGoal(
                    goal_id="goal:gate-m29", safe_summary="Plan a safe review workflow."
                ),
                steps=[safe_step],
                safe_summary="Review-only task plan.",
            )
            safe_decision = evaluate_task_plan(safe_plan)
            if safe_decision.status != TaskPlanDecisionStatus.valid_for_review:
                failures.append("M29 safe task plan was not valid for review")
            if not safe_decision.valid_for_review:
                failures.append("M29 safe task plan did not return valid_for_review")
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append("M29 safe task plan authorized or performed execution")
            if safe_decision.scheduler_registered:
                failures.append("M29 safe task plan registered a scheduler")
            if safe_decision.derived_plan_risk_level != TaskRiskLevel.low:
                failures.append(
                    "M29 safe task plan did not report trusted derived risk"
                )
            if (
                not safe_decision.receipt_plan
                or safe_decision.receipt_plan.execution_performed
            ):
                failures.append(
                    "M29 safe task plan receipt plan is missing or executable"
                )
            elif (
                safe_decision.receipt_plan.derived_plan_risk_level
                != safe_decision.derived_plan_risk_level
            ):
                failures.append("M29 receipt plan did not preserve derived plan risk")

            def require_denial(decision: Any, required_reason: str, label: str) -> None:
                if (
                    decision.valid_for_review
                    or decision.execution_authorized
                    or decision.execution_performed
                ):
                    failures.append(f"M29 denied probe was allowed: {label}")
                if decision.scheduler_registered:
                    failures.append(f"M29 denied probe registered a scheduler: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(
                        f"M29 denied probe missing {required_reason}: {label}"
                    )

            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={"approval_ref": "approval:m28-arbitrary"}
                    )
                ),
                "APPROVAL_REF_NOT_TASK_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={"approval_ref": "approval_test_gate_m29"}
                    )
                ),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test_ ref",
            )
            require_denial(
                evaluate_task_plan(
                    TaskPlanningRequest(plan=safe_plan).model_copy(
                        update={"execution_requested": True}
                    )
                ),
                "TASK_EXECUTION_REQUEST_DENIED",
                "execution requested",
            )
            require_denial(
                evaluate_task_plan(
                    TaskPlanningRequest(plan=safe_plan).model_copy(
                        update={"auto_run_requested": True}
                    )
                ),
                "TASK_AUTO_RUN_DENIED",
                "auto-run requested",
            )
            require_denial(
                evaluate_task_plan(
                    TaskPlanningRequest(plan=safe_plan).model_copy(
                        update={"schedule_requested": True}
                    )
                ),
                "TASK_SCHEDULER_DENIED",
                "scheduler requested",
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={"safe_summary": "contains token=abc123"}
                    )
                ),
                "TASK_PLAN_REVALIDATION_FAILED",
                "model_copy plan secret summary revalidation",
            )
            raw_boundary = safe_step.input_boundary.model_copy(
                update={"contains_raw_prompt": True}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={
                            "steps": [
                                safe_step.model_copy(
                                    update={"input_boundary": raw_boundary}
                                )
                            ]
                        }
                    )
                ),
                "RAW_PROMPT_DENIED",
                "model_copy raw prompt revalidation",
            )
            secret_boundary = safe_step.input_boundary.model_copy(
                update={"metadata": {"token": "abc123"}}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={
                            "steps": [
                                safe_step.model_copy(
                                    update={"input_boundary": secret_boundary}
                                )
                            ]
                        }
                    )
                ),
                "SECRET_METADATA_DENIED",
                "model_copy secret metadata revalidation",
            )
            for input_ref, trust_level, reason in [
                (
                    "model:gate-m29",
                    PlanInputTrustLevel.model_output_blocked,
                    "MODEL_OUTPUT_NOT_PLAN_AUTHORITY",
                ),
                (
                    "memory:gate-m29",
                    PlanInputTrustLevel.memory_ref,
                    "MEMORY_REF_NOT_PLAN_AUTHORITY",
                ),
                (
                    "context-pack:gate-m29",
                    PlanInputTrustLevel.context_pack_ref,
                    "CONTEXT_PACK_NOT_PLAN_AUTHORITY",
                ),
                (
                    "tool-intent:gate-m27",
                    PlanInputTrustLevel.tool_intent_ref,
                    "TOOL_INTENT_NOT_PLAN_AUTHORITY",
                ),
                (
                    "approval:gate-m28",
                    PlanInputTrustLevel.approval_ref,
                    "APPROVAL_REF_NOT_TASK_AUTHORITY",
                ),
                (
                    "openwebui:gate-m29",
                    PlanInputTrustLevel.openwebui_output_blocked,
                    "OPENWEBUI_OUTPUT_NOT_PLAN_AUTHORITY",
                ),
                (
                    "control-center:gate-m29",
                    PlanInputTrustLevel.unknown_blocked,
                    "UNKNOWN_INPUT_REF_DENIED",
                ),
            ]:
                blocked_boundary = TaskStepInputBoundary(
                    input_refs=[input_ref], input_trust_level=trust_level
                )
                require_denial(
                    evaluate_task_plan(
                        safe_plan.model_copy(
                            update={
                                "steps": [
                                    safe_step.model_copy(
                                        update={"input_boundary": blocked_boundary}
                                    )
                                ]
                            }
                        )
                    ),
                    reason,
                    f"non-authoritative input ref {input_ref}",
                )
            effectful_step = safe_step.model_copy(
                update={
                    "step_kind": TaskStepKind.tool_execution_planned,
                    "declared_risk_level": TaskRiskLevel.high,
                }
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [effectful_step]})
                ),
                "TASK_STEP_EXECUTION_DENIED",
                "effectful task step",
            )
            downgraded_step = safe_step.model_copy(
                update={
                    "step_kind": TaskStepKind.file_mutation_planned,
                    "declared_risk_level": TaskRiskLevel.low,
                }
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [downgraded_step]})
                ),
                "TASK_RISK_DOWNGRADE_DENIED",
                "risk downgrade",
            )
            hidden_side_effect_step = safe_step.model_copy(
                update={"metadata": {"side_effect": "file_write"}}
            )
            hidden_side_effect_decision = evaluate_task_plan(
                safe_plan.model_copy(update={"steps": [hidden_side_effect_step]})
            )
            require_denial(
                hidden_side_effect_decision,
                "TASK_HIDDEN_SIDE_EFFECT_DENIED",
                "hidden side effect metadata",
            )
            if (
                "TASK_RISK_DOWNGRADE_DENIED"
                not in hidden_side_effect_decision.reason_codes
            ):
                failures.append(
                    "M29 hidden side effect metadata did not deny risk downgrade"
                )
            duplicate_step = safe_step.model_copy(
                update={"safe_summary": "Duplicate step ref."}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [safe_step, duplicate_step]})
                ),
                "DUPLICATE_STEP_ID_DENIED",
                "duplicate step id",
            )
            missing_dependency_step = safe_step.model_copy(
                update={"depends_on": ["step:missing-m29"]}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [missing_dependency_step]})
                ),
                "MISSING_DEPENDENCY_STEP_DENIED",
                "missing dependency",
            )
            step_a = safe_step.model_copy(
                update={"step_id": "step:gate-m29-a", "depends_on": ["step:gate-m29-b"]}
            )
            step_b = safe_step.model_copy(
                update={"step_id": "step:gate-m29-b", "depends_on": ["step:gate-m29-a"]}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [step_a, step_b]})
                ),
                "DEPENDENCY_CYCLE_DENIED",
                "dependency cycle",
            )
            self_dep_step = safe_step.model_copy(
                update={"depends_on": [safe_step.step_id]}
            )
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(update={"steps": [self_dep_step]})
                ),
                "DEPENDENCY_CYCLE_DENIED",
                "self dependency cycle",
            )
            step_c = safe_step.model_copy(
                update={"step_id": "step:gate-m29-c", "depends_on": ["step:gate-m29-b"]}
            )
            indirect_a = step_a.model_copy(update={"depends_on": ["step:gate-m29-c"]})
            indirect_b = step_b.model_copy(update={"depends_on": ["step:gate-m29-a"]})
            require_denial(
                evaluate_task_plan(
                    safe_plan.model_copy(
                        update={"steps": [indirect_a, indirect_b, step_c]}
                    )
                ),
                "DEPENDENCY_CYCLE_DENIED",
                "indirect dependency cycle",
            )
            dependency_decision = evaluate_task_plan(
                safe_plan.model_copy(
                    update={
                        "steps": [
                            step_a.model_copy(update={"depends_on": []}),
                            step_b.model_copy(update={"depends_on": []}),
                        ],
                        "dependencies": [
                            TaskDependency(
                                dependency_id="dependency:gate-m29-a-before-b",
                                before_step_id="step:gate-m29-a",
                                after_step_id="step:gate-m29-b",
                            )
                        ],
                    }
                )
            )
            if not dependency_decision.valid_for_review:
                failures.append(
                    "M29 explicit acyclic dependency plan was not valid for review"
                )

            planning_source = "\n".join(
                self._read(path)
                for path in (
                    self.root / "src" / "ultimate_ai_agent" / "core" / "planning"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
                "import subprocess",
                "from subprocess import",
                "subprocess" + ".",
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
                f"M29 Task Planning Engine module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in planning_source
            )
        except Exception as exc:
            failures.append(f"M29 Task Planning Engine validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m29_task_planning_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m29_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M29 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m29_m30_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/planning/M29_TO_M30_BOUNDARY.md",
        ]
        failures = [
            f"missing M29 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.33.0" in text and "agent task planning engine" in text:
            if "implemented/released" not in text:
                failures.append("M29 docs do not mark v0.33.0 implemented/released")
        else:
            failures.append(
                "M29 docs do not mention v0.33.0 Agent Task Planning Engine"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 35, 0):
            if (
                "m30" not in text
                or "multi-step execution framework" not in text
                or "implemented/released" not in text
            ):
                failures.append(
                    "M29 boundary docs must acknowledge implemented v0.34.0 / M30"
                )
            if (
                "m31" not in text
                or "real tool runtime adapter" not in text
                or "implemented/released" not in text
            ):
                failures.append(
                    "M29 boundary docs must acknowledge implemented v0.35.0 / M31"
                )
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
            if (
                "m30" not in text
                or "multi-step execution framework" not in text
                or "implemented/released" not in text
            ):
                failures.append(
                    "M29 boundary docs must acknowledge implemented v0.34.0 / M30"
                )
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
        else:
            if "m30-m40 remain planned/provisional" not in text:
                failures.append("M30-M40 must remain planned/provisional after M29")
            forbidden_m30_fragments = (
                "m30 is implemented",
                "v0.34.0 implements m30",
                "approved local tool execution is implemented",
                "task execution is implemented",
                "scheduler runtime is implemented",
                "production task authority is implemented",
            )
            failures.extend(
                f"M29 docs imply M30 implementation: {fragment}"
                for fragment in forbidden_m30_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m30_execution_framework_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/execution/__init__.py",
            "src/ultimate_ai_agent/core/execution/enums.py",
            "src/ultimate_ai_agent/core/execution/runs.py",
            "src/ultimate_ai_agent/core/execution/steps.py",
            "src/ultimate_ai_agent/core/execution/transitions.py",
            "src/ultimate_ai_agent/core/execution/state_machine.py",
            "src/ultimate_ai_agent/core/execution/validation.py",
            "src/ultimate_ai_agent/core/execution/manifests.py",
            "src/ultimate_ai_agent/core/execution/receipts.py",
            "src/ultimate_ai_agent/core/execution/policy.py",
            "tests/test_execution_framework_contracts.py",
            "tests/test_execution_state_machine_safety.py",
            "tests/test_execution_dependency_progression.py",
            "tests/test_execution_receipt_plan.py",
            "tests/test_m30_gate_integration.py",
            "docs/execution/MULTI_STEP_EXECUTION_FRAMEWORK.md",
            "docs/execution/EXECUTION_STATE_MACHINE.md",
            "docs/execution/EXECUTION_STEP_CONTRACTS.md",
            "docs/execution/EXECUTION_DEPENDENCY_POLICY.md",
            "docs/execution/EXECUTION_TRANSITION_POLICY.md",
            "docs/execution/EXECUTION_INPUT_BOUNDARY.md",
            "docs/execution/EXECUTION_RECEIPT_PLAN.md",
            "docs/execution/EXECUTION_NON_GOALS.md",
            "docs/execution/M30_TO_M31_BOUNDARY.md",
        ]
        failures = [
            f"missing M30 Multi-Step Execution Framework file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.execution import (
                ExecutionInputTrustLevel,
                ExecutionRun,
                ExecutionStep,
                ExecutionStepInputBoundary,
                ExecutionStepMode,
                ExecutionStepStatus,
                ExecutionTransitionKind,
                ExecutionTransitionRequest,
                ExecutionTransitionStatus,
                build_execution_framework_manifest,
                evaluate_execution_transition,
            )

            manifest = build_execution_framework_manifest(baseline_version="0.34.0")
            manifest_flags = [
                manifest.real_task_execution_enabled,
                manifest.action_execution_enabled,
                manifest.tool_execution_enabled,
                manifest.file_mutation_enabled,
                manifest.memory_write_enabled,
                manifest.event_ledger_mutation_enabled,
                manifest.network_call_enabled,
                manifest.model_provider_call_enabled,
                manifest.browser_automation_enabled,
                manifest.mobile_device_access_enabled,
                manifest.remote_execution_enabled,
                manifest.plugin_enablement_enabled,
                manifest.scheduler_enabled,
                manifest.background_worker_enabled,
                manifest.autonomous_loop_enabled,
                manifest.context_injection_enabled,
                manifest.backend_execution_routes_added,
                manifest.control_center_execute_controls_enabled,
                manifest.production_authority_enabled,
            ]
            if not manifest.execution_state_machine_enabled or any(manifest_flags):
                failures.append(
                    "M30 manifest enables forbidden execution/runtime authority"
                )

            safe_step = ExecutionStep(
                step_id="execution-step:gate-m30-review",
                safe_summary="Validate safe metadata only.",
                mode=ExecutionStepMode.no_effect,
                status=ExecutionStepStatus.ready,
                input_boundary=ExecutionStepInputBoundary(
                    input_refs=["canonical:gate-m30"]
                ),
            )
            safe_run = ExecutionRun(
                run_id="execution-run:gate-m30",
                source_task_plan_ref="plan:gate-m30",
                steps=[safe_step],
                safe_summary="No-effect execution-state-machine run.",
            )
            safe_request = ExecutionTransitionRequest(
                run_id=safe_run.run_id,
                target_step_id=safe_step.step_id,
                transition_id="execution-transition:gate-m30",
                transition_kind=ExecutionTransitionKind.complete_no_effect_step,
                replay_key="replay:gate-m30",
                safe_summary="Complete a no-effect step.",
            )
            safe_decision = evaluate_execution_transition(safe_run, safe_request)
            if (
                safe_decision.status
                != ExecutionTransitionStatus.approved_no_effect_transition
            ):
                failures.append("M30 safe no-effect transition was not allowed")
            if safe_decision.execution_authorized or safe_decision.execution_performed:
                failures.append(
                    "M30 safe transition authorized or performed real execution"
                )
            if safe_decision.side_effects_performed:
                failures.append("M30 safe transition reported side effects")
            if (
                not safe_decision.receipt_plan
                or safe_decision.receipt_plan.execution_performed
            ):
                failures.append("M30 safe transition receipt is missing or executable")

            def require_denial(decision: Any, required_reason: str, label: str) -> None:
                if (
                    decision.status != ExecutionTransitionStatus.denied
                    or decision.execution_performed
                ):
                    failures.append(f"M30 denied probe was allowed: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(
                        f"M30 denied probe missing {required_reason}: {label}"
                    )

            request_with_execution = safe_request.model_copy(
                update={"execution_requested": True}
            )
            require_denial(
                evaluate_execution_transition(safe_run, request_with_execution),
                "EXECUTION_REQUEST_DENIED",
                "execution requested",
            )
            request_with_auto = safe_request.model_copy(
                update={
                    "auto_run_requested": True,
                    "schedule_requested": True,
                    "background_worker_requested": True,
                }
            )
            auto_decision = evaluate_execution_transition(safe_run, request_with_auto)
            require_denial(auto_decision, "AUTO_RUN_DENIED", "auto-run requested")
            if "SCHEDULE_DENIED" not in auto_decision.reason_codes:
                failures.append("M30 scheduler request was not denied")
            if "BACKGROUND_WORKER_DENIED" not in auto_decision.reason_codes:
                failures.append("M30 background worker request was not denied")
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(
                        update={"replay_keys_seen": ["replay:gate-m30"]}
                    ),
                    safe_request,
                ),
                "EXECUTION_REPLAY_DENIED",
                "replay key reuse",
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(
                        update={
                            "transition_ids_seen": ["execution-transition:gate-m30"]
                        }
                    ),
                    safe_request,
                ),
                "EXECUTION_TRANSITION_REPLAY_DENIED",
                "transition id reuse",
            )
            raw_boundary = safe_step.input_boundary.model_copy(
                update={"contains_raw_prompt": True}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(
                        update={
                            "steps": [
                                safe_step.model_copy(
                                    update={"input_boundary": raw_boundary}
                                )
                            ]
                        }
                    ),
                    safe_request,
                ),
                "RAW_PROMPT_DENIED",
                "raw prompt model_copy revalidation",
            )
            secret_boundary = safe_step.input_boundary.model_copy(
                update={"metadata": {"token": "abc123"}}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(
                        update={
                            "steps": [
                                safe_step.model_copy(
                                    update={"input_boundary": secret_boundary}
                                )
                            ]
                        }
                    ),
                    safe_request,
                ),
                "SECRET_METADATA_DENIED",
                "secret metadata model_copy revalidation",
            )
            effectful_step = safe_step.model_copy(
                update={"mode": ExecutionStepMode.tool_execution_blocked}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [effectful_step]}),
                    safe_request,
                ),
                "TOOL_EXECUTION_DENIED",
                "tool execution step mode",
            )
            hidden_effect_step = safe_step.model_copy(
                update={"metadata": {"derived_effect": "file_write"}}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [hidden_effect_step]}),
                    safe_request,
                ),
                "HIDDEN_SIDE_EFFECT_DENIED",
                "hidden side effect metadata",
            )
            for input_ref, trust_level, reason in [
                (
                    "model:gate-m30",
                    ExecutionInputTrustLevel.model_output_blocked,
                    "MODEL_OUTPUT_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "memory:gate-m30",
                    ExecutionInputTrustLevel.memory_ref,
                    "MEMORY_REF_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "context-pack:gate-m30",
                    ExecutionInputTrustLevel.context_pack_ref,
                    "CONTEXT_PACK_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "tool-intent:gate-m27",
                    ExecutionInputTrustLevel.tool_intent_ref,
                    "TOOL_INTENT_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "approval:gate-m28",
                    ExecutionInputTrustLevel.approval_ref,
                    "APPROVAL_REF_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "openwebui:gate-m30",
                    ExecutionInputTrustLevel.openwebui_output_blocked,
                    "OPENWEBUI_OUTPUT_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "control-center:gate-m30",
                    ExecutionInputTrustLevel.control_center_preview_blocked,
                    "CONTROL_CENTER_PREVIEW_NOT_EXECUTION_AUTHORITY",
                ),
                (
                    "random:gate-m30",
                    ExecutionInputTrustLevel.unknown_blocked,
                    "UNKNOWN_INPUT_REF_DENIED",
                ),
            ]:
                blocked_boundary = ExecutionStepInputBoundary(
                    input_refs=[input_ref], input_trust_level=trust_level
                )
                require_denial(
                    evaluate_execution_transition(
                        safe_run.model_copy(
                            update={
                                "steps": [
                                    safe_step.model_copy(
                                        update={"input_boundary": blocked_boundary}
                                    )
                                ]
                            }
                        ),
                        safe_request,
                    ),
                    reason,
                    f"non-authoritative execution ref {input_ref}",
                )
            missing_dep_step = safe_step.model_copy(
                update={"depends_on": ["execution-step:missing-m30"]}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [missing_dep_step]}),
                    safe_request,
                ),
                "MISSING_EXECUTION_DEPENDENCY_DENIED",
                "missing dependency",
            )
            step_a = safe_step.model_copy(
                update={
                    "step_id": "execution-step:gate-m30-a",
                    "depends_on": ["execution-step:gate-m30-b"],
                }
            )
            step_b = safe_step.model_copy(
                update={
                    "step_id": "execution-step:gate-m30-b",
                    "depends_on": ["execution-step:gate-m30-a"],
                }
            )
            cycle_request = safe_request.model_copy(
                update={"target_step_id": "execution-step:gate-m30-a"}
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run.model_copy(update={"steps": [step_a, step_b]}),
                    cycle_request,
                ),
                "EXECUTION_DEPENDENCY_CYCLE_DENIED",
                "dependency cycle",
            )
            completed_step = step_a.model_copy(
                update={
                    "status": ExecutionStepStatus.completed_no_effect,
                    "depends_on": [],
                }
            )
            dependent_step = step_b.model_copy(
                update={"depends_on": [completed_step.step_id]}
            )
            dependent_request = safe_request.model_copy(
                update={
                    "target_step_id": dependent_step.step_id,
                    "replay_key": "replay:gate-m30-dependent",
                    "transition_id": "execution-transition:gate-m30-dependent",
                }
            )
            dependent_decision = evaluate_execution_transition(
                safe_run.model_copy(update={"steps": [completed_step, dependent_step]}),
                dependent_request,
            )
            if (
                dependent_decision.status
                != ExecutionTransitionStatus.approved_no_effect_transition
            ):
                failures.append(
                    "M30 completed dependency did not allow no-effect dependent step"
                )

            final_request = safe_request.model_copy(
                update={
                    "target_step_id": None,
                    "replay_key": "replay:gate-m30-finalize",
                    "transition_id": "execution-transition:gate-m30-finalize",
                    "transition_kind": ExecutionTransitionKind.finalize_no_effect_run,
                }
            )
            final_decision = evaluate_execution_transition(
                safe_run.model_copy(
                    update={
                        "steps": [
                            safe_step.model_copy(
                                update={
                                    "status": ExecutionStepStatus.completed_no_effect
                                }
                            )
                        ]
                    }
                ),
                final_request,
            )
            if (
                final_decision.status
                != ExecutionTransitionStatus.approved_no_effect_transition
            ):
                failures.append(
                    "M30 completed run did not finalize without side effects"
                )
            require_denial(
                evaluate_execution_transition(safe_run, final_request),
                "EXECUTION_RUN_FINALIZE_INCOMPLETE_DENIED",
                "finalize incomplete run",
            )
            require_denial(
                evaluate_execution_transition(
                    safe_run,
                    safe_request.model_copy(
                        update={
                            "side_effect_execution_enabled": True,
                            "replay_key": "replay:gate-m30-side-effect",
                            "transition_id": "execution-transition:gate-m30-side-effect",
                        }
                    ),
                ),
                "SIDE_EFFECT_EXECUTION_DENIED",
                "side-effect execution flag",
            )

            execution_source = "\n".join(
                self._read(path)
                for path in (
                    self.root / "src" / "ultimate_ai_agent" / "core" / "execution"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
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
                f"M30 Multi-Step Execution Framework module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in execution_source
            )
        except Exception as exc:
            failures.append(
                f"M30 Multi-Step Execution Framework validation failed: {exc}"
            )
        return self._result(criterion, failures, required_files)

    def check_m30_execution_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m30_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M30 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])

    def check_m30_m31_remains_future(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_docs = [
            "docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md",
            "docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md",
            "docs/canonical/09_roadmap.md",
            "docs/execution/M30_TO_M31_BOUNDARY.md",
        ]
        failures = [
            f"missing M30 roadmap doc: {path}"
            for path in required_docs
            if not (self.root / path).exists()
        ]
        text = "\n".join(
            self._read(self.root / path).lower()
            for path in required_docs
            if (self.root / path).exists()
        )
        if "v0.34.0" in text and "multi-step execution framework" in text:
            if "implemented/released" not in text:
                failures.append("M30 docs do not mark v0.34.0 implemented/released")
        else:
            failures.append(
                "M30 docs do not mention v0.34.0 Multi-Step Execution Framework"
            )
        version_tuple = self._active_version_tuple()
        if version_tuple >= (0, 35, 0):
            if (
                "m31" not in text
                or "real tool runtime adapter" not in text
                or "implemented/released" not in text
            ):
                failures.append("M30 docs do not acknowledge implemented v0.35.0 / M31")
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
        else:
            if "m31-m40 remain planned/provisional" not in text:
                failures.append("M31-M40 must remain planned/provisional after M30")
            forbidden_m31_fragments = (
                "m31 is implemented",
                "v0.35.0 implements m31",
                "native client contract is implemented",
                "ccc ios is implemented",
                "ccc android is implemented",
                "ccc macos is implemented",
            )
            failures.extend(
                f"M30 docs imply M31 implementation: {fragment}"
                for fragment in forbidden_m31_fragments
                if fragment in text
            )
        return self._result(criterion, failures, required_docs)

    def check_m31_tool_runtime_noop_contract_safe(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        required_files = [
            "src/ultimate_ai_agent/core/tools/runtime/__init__.py",
            "src/ultimate_ai_agent/core/tools/runtime/adapters.py",
            "src/ultimate_ai_agent/core/tools/runtime/contracts.py",
            "src/ultimate_ai_agent/core/tools/runtime/enums.py",
            "src/ultimate_ai_agent/core/tools/runtime/invocation.py",
            "src/ultimate_ai_agent/core/tools/runtime/manifests.py",
            "src/ultimate_ai_agent/core/tools/runtime/noop.py",
            "src/ultimate_ai_agent/core/tools/runtime/policy.py",
            "src/ultimate_ai_agent/core/tools/runtime/receipts.py",
            "src/ultimate_ai_agent/core/tools/runtime/validation.py",
            "tests/test_tool_runtime_contracts.py",
            "tests/test_tool_runtime_noop_invocation.py",
            "tests/test_tool_runtime_no_side_effects.py",
            "tests/test_tool_runtime_authority_boundaries.py",
            "tests/test_tool_runtime_replay_protection.py",
            "tests/test_tool_runtime_no_dynamic_dispatch.py",
            "tests/test_m31_gate_integration.py",
            "docs/tools/TOOL_RUNTIME_ADAPTER.md",
            "docs/tools/NOOP_TOOL_RUNTIME.md",
            "docs/tools/TOOL_RUNTIME_INVOCATION_CONTRACT.md",
            "docs/tools/TOOL_RUNTIME_AUTHORITY_BOUNDARY.md",
            "docs/tools/TOOL_RUNTIME_REPLAY_POLICY.md",
            "docs/tools/TOOL_RUNTIME_RECEIPT_PLAN.md",
            "docs/tools/TOOL_RUNTIME_NON_GOALS.md",
            "docs/tools/M31_TO_M32_BOUNDARY.md",
        ]
        failures = [
            f"missing M31 Tool Runtime file: {path}"
            for path in required_files
            if not (self.root / path).exists()
        ]
        try:
            from ultimate_ai_agent.core.tools.runtime import (
                NOOP_TOOL_NAME,
                NOOP_TOOL_REF,
                ToolInvocationRequest,
                ToolInvocationStatus,
                ToolRuntimeAdapter,
                build_tool_runtime_manifest,
                evaluate_tool_invocation,
            )

            manifest = build_tool_runtime_manifest(baseline_version="0.35.1")
            policy = manifest.policy
            forbidden_flags = [
                policy.arbitrary_tool_execution_enabled,
                policy.side_effecting_tools_enabled,
                policy.shell_tools_enabled,
                policy.file_tools_enabled,
                policy.memory_write_tools_enabled,
                policy.network_tools_enabled,
                policy.model_tools_enabled,
                policy.browser_tools_enabled,
                policy.mobile_tools_enabled,
                policy.remote_tools_enabled,
                policy.plugin_tools_enabled,
                policy.dynamic_tool_registration_enabled,
                policy.backend_execute_routes_enabled,
                policy.control_center_execute_controls_enabled,
                policy.production_authority_enabled,
            ]
            if (
                not policy.tool_runtime_enabled
                or not policy.noop_tool_enabled
                or any(forbidden_flags)
            ):
                failures.append("M31 manifest enables forbidden runtime tool authority")
            if NOOP_TOOL_REF not in manifest.allowlisted_tool_refs:
                failures.append("M31 manifest no longer allowlists the no-op tool")

            safe_request = ToolInvocationRequest(
                invocation_id="tool-runtime-invocation:gate-m31",
                tool_ref=NOOP_TOOL_REF,
                tool_name=NOOP_TOOL_NAME,
                replay_key="tool-runtime-replay:gate-m31",
                safe_summary="Run deterministic no-op tool.",
                input_refs=["canonical:gate-m31"],
            )
            safe_decision = ToolRuntimeAdapter().invoke(safe_request)
            if safe_decision.status != ToolInvocationStatus.noop_completed:
                failures.append("M31 no-op runtime invocation did not complete")
            if (
                not safe_decision.execution_performed
                or not safe_decision.invocation_allowed
            ):
                failures.append(
                    "M31 no-op runtime invocation did not report the no-op invocation"
                )
            if safe_decision.side_effects_performed:
                failures.append("M31 no-op runtime reported side effects")
            if (
                not safe_decision.result
                or safe_decision.result.output.safe_message != "NOOP_TOOL_COMPLETED"
            ):
                failures.append(
                    "M31 no-op runtime result envelope is missing or non-deterministic"
                )
            if safe_decision.result and (
                safe_decision.result.output.raw_input_echoed
                or safe_decision.result.raw_content_stored
            ):
                failures.append("M31 no-op runtime echoed or stored raw content")

            def require_denial(decision: Any, required_reason: str, label: str) -> None:
                if (
                    decision.status == ToolInvocationStatus.noop_completed
                    or decision.execution_performed
                ):
                    failures.append(f"M31 denied probe was allowed: {label}")
                if decision.side_effects_performed:
                    failures.append(f"M31 denied probe reported side effects: {label}")
                if required_reason not in decision.reason_codes:
                    failures.append(
                        f"M31 denied probe missing {required_reason}: {label}"
                    )

            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(update={"tool_ref": "tool:file_write.v1"})
                ),
                "TOOL_NOT_ALLOWLISTED_DENIED",
                "file tool ref",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(update={"tool_name": "module.callable"})
                ),
                "DYNAMIC_DISPATCH_DENIED",
                "dynamic dispatch tool name",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"module_path": "tool_plugins.file_writer"}
                    )
                ),
                "DYNAMIC_DISPATCH_DENIED",
                "model_copy module path",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"metadata": {"callable_name": "run_noop"}}
                    )
                ),
                "DYNAMIC_DISPATCH_DENIED",
                "metadata callable name",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"side_effects_performed": ["file:write"]}
                    )
                ),
                "SIDE_EFFECT_ATTEMPT_DENIED",
                "model_copy side effect field",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"metadata": {"file_write_requested": True}}
                    )
                ),
                "SIDE_EFFECT_ATTEMPT_DENIED",
                "metadata side effect field",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"approval_ref": "approval:gate-m31"}
                    )
                ),
                "APPROVAL_REF_NOT_AUTHORITY",
                "approval_ref alone",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(
                        update={"approval_ref": "approval_test_gate_m31"}
                    )
                ),
                "APPROVAL_TEST_REF_DENIED",
                "approval_test ref",
            )
            for authority_ref in [
                "task-plan:gate-m31",
                "context-pack:gate-m31",
                "memory:gate-m31",
                "tool-intent:gate-m31",
                "approval:gate-m31",
                "model:gate-m31",
            ]:
                require_denial(
                    evaluate_tool_invocation(
                        safe_request.model_copy(
                            update={"authority_refs": [authority_ref]}
                        )
                    ),
                    "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY",
                    f"authority ref {authority_ref}",
                )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(update={"contains_raw_prompt": True})
                ),
                "RAW_PROMPT_DENIED",
                "raw prompt model_copy revalidation",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request.model_copy(update={"metadata": {"token": "abc123"}})
                ),
                "SECRET_CONTENT_DENIED",
                "secret metadata model_copy revalidation",
            )
            require_denial(
                evaluate_tool_invocation(
                    safe_request, replay_keys_seen=["tool-runtime-replay:gate-m31"]
                ),
                "TOOL_RUNTIME_REPLAY_DETECTED",
                "replay key reuse",
            )

            runtime_source = "\n".join(
                self._read(path)
                for path in (
                    self.root
                    / "src"
                    / "ultimate_ai_agent"
                    / "core"
                    / "tools"
                    / "runtime"
                ).glob("*.py")
            ).lower()
            forbidden_fragments = (
                "os.system(",
                "popen(",
                "shell=true",
                "requests.get(",
                "requests.post(",
                "httpx.get(",
                "httpx.post(",
                "urllib.request.urlopen(",
                "socket",
                "websocket",
                "write_memory(",
                ".write_memory(",
                "put_record(",
                ".put_record(",
                "append_event(",
                "mutate_event(",
                "importlib",
                "getattr(",
                "chat.completions.create(",
                "import " + "openai",
                "import " + "anthropic",
                "import " + "ollama",
            )
            failures.extend(
                f"M31 Tool Runtime module contains forbidden fragment: {fragment}"
                for fragment in forbidden_fragments
                if fragment in runtime_source
            )
        except Exception as exc:
            failures.append(f"M31 Tool Runtime validation failed: {exc}")
        return self._result(criterion, failures, required_files)

    def check_m31_tool_runtime_openapi_routes_unchanged(
        self, criterion: FoundationGateCriterion
    ) -> FoundationGateResult:
        failures: List[str] = []
        try:
            from ultimate_ai_agent.api.app import app

            failures.extend(m31_openapi_route_failures(app.openapi().get("paths", {})))
        except Exception as exc:
            failures.append(f"M31 OpenAPI route validation failed: {exc}")
        return self._result(criterion, failures, [])
