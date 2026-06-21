from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

from ultimate_ai_agent.core.execution.enums import ExecutionFrameworkStatus


class ExecutionFrameworkManifest(BaseModel):
    baseline_version: str = "0.34.0"
    contract_version: str = "m30-multi-step-execution-framework"
    status: ExecutionFrameworkStatus = ExecutionFrameworkStatus.state_machine_only
    execution_state_machine_enabled: bool = True
    real_task_execution_enabled: bool = False
    action_execution_enabled: bool = False
    tool_execution_enabled: bool = False
    file_mutation_enabled: bool = False
    memory_write_enabled: bool = False
    event_ledger_mutation_enabled: bool = False
    network_call_enabled: bool = False
    model_provider_call_enabled: bool = False
    browser_automation_enabled: bool = False
    mobile_device_access_enabled: bool = False
    remote_execution_enabled: bool = False
    plugin_enablement_enabled: bool = False
    scheduler_enabled: bool = False
    background_worker_enabled: bool = False
    autonomous_loop_enabled: bool = False
    context_injection_enabled: bool = False
    backend_execution_routes_added: bool = False
    control_center_execute_controls_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manifest(self) -> Any:
        blocked_true_fields = [
            "real_task_execution_enabled",
            "action_execution_enabled",
            "tool_execution_enabled",
            "file_mutation_enabled",
            "memory_write_enabled",
            "event_ledger_mutation_enabled",
            "network_call_enabled",
            "model_provider_call_enabled",
            "browser_automation_enabled",
            "mobile_device_access_enabled",
            "remote_execution_enabled",
            "plugin_enablement_enabled",
            "scheduler_enabled",
            "background_worker_enabled",
            "autonomous_loop_enabled",
            "context_injection_enabled",
            "backend_execution_routes_added",
            "control_center_execute_controls_enabled",
            "production_authority_enabled",
        ]
        for field_name in blocked_true_fields:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must be False in M30")
        return self


def build_execution_framework_manifest(baseline_version: str = "0.34.0") -> ExecutionFrameworkManifest:
    return ExecutionFrameworkManifest(baseline_version=baseline_version)

