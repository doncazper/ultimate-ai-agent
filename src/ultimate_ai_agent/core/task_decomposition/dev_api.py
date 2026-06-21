from __future__ import annotations
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException

from ultimate_ai_agent.core.hygiene.envelopes import ErrorCategory, ErrorEnvelope, ResultEnvelope, Severity
from ultimate_ai_agent.core.task_decomposition.api_safety import (
    sanitize_task_decomposition_api_payload,
    task_decomposition_authority_error,
)
from ultimate_ai_agent.core.task_decomposition.runtime import (
    TaskCapabilityApprovalRequestPayload,
    TaskDecompositionRegisterRequest,
    TaskDecompositionRequest,
    TaskDecompositionRunRequest,
    TaskDecompositionService,
    TaskPlanExecutionRequest,
    TaskPlanValidationRequest,
)


def _require_local_authority(authorization: str | None = Header(default=None)) -> None:
    error = task_decomposition_authority_error(authorization)
    if error is not None:
        status_code, detail = error
        raise HTTPException(status_code=status_code, detail=detail)


def build_task_decomposition_dev_app(
    service: TaskDecompositionService | None = None,
) -> FastAPI:
    active_service = service or TaskDecompositionService.from_env()
    app = FastAPI(
        title="Ultimate AI Agent Task Decomposition Local Dev API",
        version="local-dev",
        description="Local-only task decomposer and capability registry test surface.",
        dependencies=[Depends(_require_local_authority)],
    )

    @app.get("/task-decomposition/catalog", response_model=ResultEnvelope)
    def get_catalog() -> Any:
        return ResultEnvelope(
            success=True,
            operation="task_decomposition_catalog",
            service="TaskDecompositionDevAPI",
            trace_id="local-dev",
            data=sanitize_task_decomposition_api_payload({"capabilities": active_service.catalog()}),
        )

    @app.post("/task-decomposition/examples/init", response_model=ResultEnvelope)
    def init_examples() -> Any:
        return ResultEnvelope(
            success=True,
            operation="task_decomposition_init_examples",
            service="TaskDecompositionDevAPI",
            trace_id="local-dev",
            data=sanitize_task_decomposition_api_payload({"capabilities": active_service.ensure_examples()}),
        )

    @app.post("/task-decomposition/capabilities/register", response_model=ResultEnvelope)
    def register_capability(request: TaskDecompositionRegisterRequest) -> Any:
        try:
            contract = active_service.register(request)
            return ResultEnvelope(
                success=True,
                operation="task_decomposition_register_capability",
                service="TaskDecompositionDevAPI",
                trace_id="local-dev",
                data=sanitize_task_decomposition_api_payload({"capability": contract}),
            )
        except Exception:
            return _error("task_decomposition_register_capability", "TASK_DECOMPOSITION_REGISTER_FAILED")

    @app.post("/task-decomposition/classify", response_model=ResultEnvelope)
    def classify(request: TaskDecompositionRequest) -> Any:
        intent = active_service.classify(request)
        return ResultEnvelope(
            success=True,
            operation="task_decomposition_classify",
            service="TaskDecompositionDevAPI",
            trace_id="local-dev",
            data=sanitize_task_decomposition_api_payload({"intent": intent}),
        )

    @app.post("/task-decomposition/decompose", response_model=ResultEnvelope)
    def decompose(request: TaskDecompositionRequest) -> Any:
        result = active_service.decompose(request)
        return ResultEnvelope(
            success=True,
            operation="task_decomposition_decompose",
            service="TaskDecompositionDevAPI",
            trace_id=result.plan.plan_id,
            data=sanitize_task_decomposition_api_payload(result),
        )

    @app.post("/task-decomposition/plans/validate", response_model=ResultEnvelope)
    def validate_plan(request: TaskPlanValidationRequest) -> Any:
        validation = active_service.validate_plan(request)
        return ResultEnvelope(
            success=validation.valid,
            operation="task_decomposition_validate_plan",
            service="TaskDecompositionDevAPI",
            trace_id=request.plan.plan_id,
            data=sanitize_task_decomposition_api_payload(validation),
        )

    @app.post("/task-decomposition/approval-request", response_model=ResultEnvelope)
    def approval_request(request: TaskCapabilityApprovalRequestPayload) -> Any:
        try:
            approval = active_service.build_approval_request(request)
            return ResultEnvelope(
                success=True,
                operation="task_decomposition_approval_request",
                service="TaskDecompositionDevAPI",
                trace_id=request.run_id,
                data=sanitize_task_decomposition_api_payload(approval),
            )
        except Exception:
            return _error("task_decomposition_approval_request", "TASK_DECOMPOSITION_APPROVAL_REQUEST_FAILED")

    @app.post("/task-decomposition/plans/execute", response_model=ResultEnvelope)
    async def execute_plan(request: TaskPlanExecutionRequest) -> Any:
        result = await active_service.execute_plan(request)
        return ResultEnvelope(
            success=result.status == "succeeded",
            operation="task_decomposition_execute_plan",
            service="TaskDecompositionDevAPI",
            trace_id=request.plan.plan_id,
            data=sanitize_task_decomposition_api_payload(result),
        )

    @app.post("/task-decomposition/run", response_model=ResultEnvelope)
    async def run(request: TaskDecompositionRunRequest) -> Any:
        result = await active_service.run(request)
        succeeded = result.execution is not None and result.execution.status == "succeeded"
        return ResultEnvelope(
            success=succeeded,
            operation="task_decomposition_run",
            service="TaskDecompositionDevAPI",
            trace_id=result.plan.plan_id,
            data=sanitize_task_decomposition_api_payload(result),
        )

    return app


def _error(operation: str, code: str) -> ResultEnvelope:
    return ResultEnvelope(
        success=False,
        operation=operation,
        service="TaskDecompositionDevAPI",
        trace_id="local-dev",
        error=ErrorEnvelope(
            code=code,
            category=ErrorCategory.validation_error,
            safe_message="Task decomposition local-dev request failed.",
            severity=Severity.medium,
            retryable=False,
            details_redacted=True,
            source="TaskDecompositionDevAPI",
        ),
    )


app = build_task_decomposition_dev_app()
