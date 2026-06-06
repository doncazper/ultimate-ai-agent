import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M56_DOC_REFS = [
    "docs/evals/AGENT_EVAL_REGRESSION_HARNESS.md",
    "docs/evals/AGENT_EVAL_REGRESSION_POLICY.md",
    "docs/evals/AGENT_EVAL_REGRESSION_AUTHORITY_BOUNDARY.md",
    "docs/evals/M56_TO_M57_BOUNDARY.md",
]
M56_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class AgentEvalRegressionStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    denied = "denied"


class _M56EvalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AgentEvalHarnessPolicy(_M56EvalModel):
    policy_ref: str = "agent-eval-harness-policy:m56"
    baseline_version: str = "0.60.0"
    deterministic_only: bool = True
    contract_only: bool = True
    local_only: bool = True
    model_call_enabled: bool = False
    provider_call_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    network_access_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    raw_prompt_capture_enabled: bool = False
    raw_provider_payload_capture_enabled: bool = False
    external_dataset_fetch_enabled: bool = False
    score_authority_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    production_authority_enabled: bool = False
    m57_implemented: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M56_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M56", "version:v0.60.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self):
        _validate_m56_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m56_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class AgentEvalCase(_M56EvalModel):
    case_ref: str
    suite_ref: str
    scenario_ref: str
    expected_outcome_ref: str
    redacted_input_summary: str
    invariant_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False

    @model_validator(mode="after")
    def validate_case_shape(self):
        for value, field_name in [
            (self.case_ref, "case_ref"),
            (self.suite_ref, "suite_ref"),
            (self.scenario_ref, "scenario_ref"),
            (self.expected_outcome_ref, "expected_outcome_ref"),
        ]:
            _validate_m56_ref(value, field_name)
        _require_nonempty(self.redacted_input_summary, "redacted_input_summary")
        for ref in self.invariant_refs:
            _validate_m56_ref(ref, "invariant_ref")
        for ref in self.evidence_refs:
            _validate_m56_ref(ref, "evidence_ref")
        for ref in self.metadata_refs:
            _validate_m56_ref(ref, "metadata_ref")
        return self


class AgentEvalSuite(_M56EvalModel):
    suite_ref: str
    baseline_ref: str
    case_refs: list[str]
    cases: list[AgentEvalCase]
    deterministic_seed_ref: str
    metadata_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_suite_shape(self):
        _validate_m56_ref(self.suite_ref, "suite_ref")
        _validate_m56_ref(self.baseline_ref, "baseline_ref")
        _validate_m56_ref(self.deterministic_seed_ref, "deterministic_seed_ref")
        if not self.case_refs or not self.cases:
            raise ValueError("EVAL_CASES_REQUIRED")
        for ref in self.case_refs:
            _validate_m56_ref(ref, "case_ref")
        for ref in self.metadata_refs:
            _validate_m56_ref(ref, "metadata_ref")
        return self


class AgentEvalRegressionRunRequest(_M56EvalModel):
    request_ref: str
    run_ref: str
    suite_ref: str
    case_refs: list[str]
    baseline_ref: str
    model_call_requested: bool = False
    provider_call_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    browser_automation_requested: bool = False
    network_access_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    raw_prompt_capture_requested: bool = False
    raw_provider_payload_capture_requested: bool = False
    external_dataset_fetch_requested: bool = False
    score_authority_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.run_ref, "run_ref"),
            (self.suite_ref, "suite_ref"),
            (self.baseline_ref, "baseline_ref"),
        ]:
            _validate_m56_ref(value, field_name)
        if not self.case_refs:
            raise ValueError("EVAL_CASE_REFS_REQUIRED")
        for ref in self.case_refs:
            _validate_m56_ref(ref, "case_ref")
        for ref in self.metadata_refs:
            _validate_m56_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class AgentEvalCaseObservation(_M56EvalModel):
    case_ref: str
    observed_outcome_ref: str
    safe_observation_summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_secret: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observation_shape(self):
        _validate_m56_ref(self.case_ref, "case_ref")
        _validate_m56_ref(self.observed_outcome_ref, "observed_outcome_ref")
        _require_nonempty(self.safe_observation_summary, "safe_observation_summary")
        for ref in self.evidence_refs:
            _validate_m56_ref(ref, "evidence_ref")
        return self


class AgentEvalCaseResult(_M56EvalModel):
    case_ref: str
    expected_outcome_ref: str
    observed_outcome_ref: str
    passed: bool
    safe_summary: str
    reason_codes: list[str]
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_shape(self):
        for value, field_name in [
            (self.case_ref, "case_ref"),
            (self.expected_outcome_ref, "expected_outcome_ref"),
            (self.observed_outcome_ref, "observed_outcome_ref"),
        ]:
            _validate_m56_ref(value, field_name)
        validate_safe_tool_payload(self.safe_summary, "safe_summary")
        for reason in self.reason_codes:
            _require_nonempty(reason, "reason_code")
        for ref in self.evidence_refs:
            _validate_m56_ref(ref, "evidence_ref")
        return self


class AgentEvalRegressionReceiptPlan(_M56EvalModel):
    receipt_plan_ref: str
    run_ref: str
    evaluation_performed: bool = False
    model_call_performed: bool = False
    provider_call_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    network_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    raw_prompt_captured: bool = False
    raw_provider_payload_captured: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M56 agent eval regression receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self):
        _validate_m56_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m56_ref(self.run_ref, "run_ref")
        for field_name, reason in [
            ("evaluation_performed", "EVAL_EXECUTION_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("provider_call_performed", "PROVIDER_CALL_DENIED"),
            ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
            ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
            ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
            ("network_call_performed", "NETWORK_ACCESS_DENIED"),
            ("memory_write_performed", "MEMORY_WRITE_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
            ("raw_prompt_captured", "RAW_PROMPT_CAPTURE_DENIED"),
            ("raw_provider_payload_captured", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        validate_safe_tool_payload(self.safe_summary, "safe_summary")
        return self


class AgentEvalRegressionReport(_M56EvalModel):
    report_ref: str
    request_ref: str
    run_ref: str
    suite_ref: str
    baseline_ref: str
    status: AgentEvalRegressionStatus
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[AgentEvalCaseResult]
    receipt_plan: AgentEvalRegressionReceiptPlan | None = None
    reason_codes: list[str] = Field(default_factory=list)
    model_call_performed: bool = False
    provider_call_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    network_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    raw_prompt_captured: bool = False
    raw_provider_payload_captured: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M56_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M56", "version:v0.60.0"])

    @model_validator(mode="after")
    def validate_report(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.request_ref, "request_ref"),
            (self.run_ref, "run_ref"),
            (self.suite_ref, "suite_ref"),
            (self.baseline_ref, "baseline_ref"),
        ]:
            _validate_m56_ref(value, field_name)
        if self.total_cases != len(self.results):
            raise ValueError("EVAL_RESULT_COUNT_MISMATCH")
        if self.passed_cases + self.failed_cases != self.total_cases:
            raise ValueError("EVAL_RESULT_SUMMARY_MISMATCH")
        for field_name, reason in [
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("provider_call_performed", "PROVIDER_CALL_DENIED"),
            ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
            ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
            ("browser_automation_performed", "BROWSER_AUTOMATION_DENIED"),
            ("network_call_performed", "NETWORK_ACCESS_DENIED"),
            ("memory_write_performed", "MEMORY_WRITE_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
            ("raw_prompt_captured", "RAW_PROMPT_CAPTURE_DENIED"),
            ("raw_provider_payload_captured", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


def validate_agent_eval_harness_policy(policy: AgentEvalHarnessPolicy) -> AgentEvalHarnessPolicy:
    validated = AgentEvalHarnessPolicy.model_validate(policy.model_dump())
    if not validated.deterministic_only or not validated.contract_only or not validated.local_only:
        raise ValueError("M56_EVAL_HARNESS_CONTRACT_REQUIRED")
    for field_name, reason in [
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("provider_call_enabled", "PROVIDER_CALL_DENIED"),
        ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
        ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
        ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("raw_prompt_capture_enabled", "RAW_PROMPT_CAPTURE_DENIED"),
        ("raw_provider_payload_capture_enabled", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("external_dataset_fetch_enabled", "EXTERNAL_DATASET_FETCH_DENIED"),
        ("score_authority_enabled", "SCORE_AUTHORITY_DENIED"),
        ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("m57_implemented", "M57_IMPLEMENTATION_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_agent_eval_regression_request(
    request: AgentEvalRegressionRunRequest,
) -> AgentEvalRegressionRunRequest:
    validated = AgentEvalRegressionRunRequest.model_validate(request.model_dump())
    for field_name, reason in [
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("provider_call_requested", "PROVIDER_CALL_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("network_access_requested", "NETWORK_ACCESS_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("raw_prompt_capture_requested", "RAW_PROMPT_CAPTURE_DENIED"),
        ("raw_provider_payload_capture_requested", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("external_dataset_fetch_requested", "EXTERNAL_DATASET_FETCH_DENIED"),
        ("score_authority_requested", "SCORE_AUTHORITY_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_CAPTURE_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED"),
        ("contains_secret", "SECRET_LIKE_EVAL_CONTENT_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_agent_eval_regression_report(
    request: AgentEvalRegressionRunRequest,
    suite: AgentEvalSuite,
    observations: list[AgentEvalCaseObservation],
    policy: AgentEvalHarnessPolicy | None = None,
) -> AgentEvalRegressionReport:
    active_policy = validate_agent_eval_harness_policy(policy or AgentEvalHarnessPolicy())
    active_request = validate_agent_eval_regression_request(request)
    _validate_suite_for_run(active_request, suite)

    observation_by_case_ref: dict[str, AgentEvalCaseObservation] = {}
    for observation in observations:
        _validate_observation_for_run(observation)
        if observation.case_ref in observation_by_case_ref:
            raise ValueError("EVAL_OBSERVATION_REF_DUPLICATE")
        observation_by_case_ref[observation.case_ref] = observation

    case_by_ref = {case.case_ref: case for case in suite.cases}
    missing_observations = [
        case_ref for case_ref in active_request.case_refs if case_ref not in observation_by_case_ref
    ]
    if missing_observations:
        raise ValueError("EVAL_OBSERVATION_MISSING")

    results = [
        _case_result(case_by_ref[case_ref], observation_by_case_ref[case_ref])
        for case_ref in active_request.case_refs
    ]
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    status = AgentEvalRegressionStatus.passed if failed == 0 else AgentEvalRegressionStatus.failed
    return AgentEvalRegressionReport(
        report_ref=f"eval-regression-report:{_ref_suffix(active_request.run_ref)}",
        request_ref=active_request.request_ref,
        run_ref=active_request.run_ref,
        suite_ref=suite.suite_ref,
        baseline_ref=active_request.baseline_ref,
        status=status,
        total_cases=len(results),
        passed_cases=passed,
        failed_cases=failed,
        results=results,
        receipt_plan=AgentEvalRegressionReceiptPlan(
            receipt_plan_ref=f"eval-regression-receipt:{_ref_suffix(active_request.run_ref)}",
            run_ref=active_request.run_ref,
            safe_summary="M56 compares explicit safe eval observations only; no agent run is performed.",
        ),
        reason_codes=["M56_EVAL_REGRESSION_CONTRACT_ONLY"],
        metadata_refs=[
            *active_policy.metadata_refs,
            active_request.request_ref,
            active_request.run_ref,
        ],
    )


def _validate_suite_for_run(request: AgentEvalRegressionRunRequest, suite: AgentEvalSuite) -> None:
    validated_suite = AgentEvalSuite.model_validate(suite.model_dump())
    if validated_suite.suite_ref != request.suite_ref:
        raise ValueError("EVAL_SUITE_REF_MISMATCH")
    if validated_suite.baseline_ref != request.baseline_ref:
        raise ValueError("EVAL_BASELINE_REF_MISMATCH")
    if len(set(validated_suite.case_refs)) != len(validated_suite.case_refs):
        raise ValueError("EVAL_CASE_REF_DUPLICATE")
    case_refs = [case.case_ref for case in validated_suite.cases]
    if len(set(case_refs)) != len(case_refs):
        raise ValueError("EVAL_CASE_REF_DUPLICATE")
    if set(case_refs) != set(validated_suite.case_refs):
        raise ValueError("EVAL_SUITE_CASE_REF_MISMATCH")
    if len(set(request.case_refs)) != len(request.case_refs):
        raise ValueError("EVAL_CASE_REF_DUPLICATE")
    for case_ref in request.case_refs:
        if case_ref not in validated_suite.case_refs:
            raise ValueError("EVAL_CASE_REF_MISSING")
    for case in validated_suite.cases:
        _validate_case_for_run(case)


def _validate_case_for_run(case: AgentEvalCase) -> None:
    if case.contains_raw_prompt:
        raise ValueError("RAW_PROMPT_CAPTURE_DENIED")
    if case.contains_raw_provider_payload:
        raise ValueError("RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED")
    if case.contains_secret:
        raise ValueError("SECRET_LIKE_EVAL_CONTENT_DENIED")
    for field_name, value in [
        ("redacted_input_summary", case.redacted_input_summary),
        ("metadata", case.metadata),
        ("metadata_refs", case.metadata_refs),
        ("evidence_refs", case.evidence_refs),
        ("invariant_refs", case.invariant_refs),
    ]:
        try:
            validate_safe_tool_payload(value, field_name)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_EVAL_CONTENT_DENIED") from exc


def _validate_observation_for_run(observation: AgentEvalCaseObservation) -> None:
    if observation.contains_raw_prompt:
        raise ValueError("RAW_PROMPT_CAPTURE_DENIED")
    if observation.contains_raw_provider_payload:
        raise ValueError("RAW_PROVIDER_PAYLOAD_CAPTURE_DENIED")
    if observation.contains_secret:
        raise ValueError("SECRET_LIKE_EVAL_CONTENT_DENIED")
    for field_name, value in [
        ("safe_observation_summary", observation.safe_observation_summary),
        ("metadata", observation.metadata),
        ("evidence_refs", observation.evidence_refs),
    ]:
        try:
            validate_safe_tool_payload(value, field_name)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_EVAL_CONTENT_DENIED") from exc


def _case_result(case: AgentEvalCase, observation: AgentEvalCaseObservation) -> AgentEvalCaseResult:
    passed = case.expected_outcome_ref == observation.observed_outcome_ref
    return AgentEvalCaseResult(
        case_ref=case.case_ref,
        expected_outcome_ref=case.expected_outcome_ref,
        observed_outcome_ref=observation.observed_outcome_ref,
        passed=passed,
        safe_summary=(
            "Expected safe outcome matched explicit observation."
            if passed
            else "Expected safe outcome did not match explicit observation."
        ),
        reason_codes=[
            "M56_EXPECTED_OUTCOME_MATCHED" if passed else "M56_EXPECTED_OUTCOME_MISMATCH"
        ],
        evidence_refs=[*case.evidence_refs, *observation.evidence_refs],
    )


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_m56_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M56_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _ref_suffix(value: str) -> str:
    return value.split(":", 1)[1].replace("/", "-").replace("@", "-")
