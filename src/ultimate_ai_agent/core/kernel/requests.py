from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.consent.grants import ConsentGrant
from ultimate_ai_agent.core.files.validation import file_content_contains_secret, validate_safe_file_path
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.kernel.enums import KernelTaskType


MUTATING_TASKS = {
    KernelTaskType.create_dev_file,
    KernelTaskType.update_dev_file,
    KernelTaskType.rollback_dev_file,
}


class KernelTaskRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    run_id: Optional[str] = None
    actor_context: ActorContext
    user_id: str = Field(..., min_length=1)
    workspace_root: str = Field(..., min_length=1)
    task_type: KernelTaskType
    user_request: str = Field(..., min_length=1)
    target_path: Optional[str] = None
    new_content: Optional[str] = None
    purpose: str = Field(..., min_length=1)
    consent_grants: List[ConsentGrant] = Field(default_factory=list)
    approval_ref: Optional[str] = None
    idempotency_key: Optional[str] = None
    expected_existing_hash: Optional[str] = None
    data_classification: DataBoundary = DataBoundary.project_private
    tags: List[str] = Field(default_factory=list)
    dry_run: bool = False
    rollback_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_kernel_boundary(self):
        if not self.workspace_root.strip():
            raise ValueError("workspace_root must be explicit.")
        workspace = Path(self.workspace_root).expanduser()
        if not workspace.is_absolute():
            raise ValueError("workspace_root must be an explicit absolute path.")
        if file_content_contains_secret(self.user_request):
            raise ValueError("secret-like content is blocked in user_request.")

        if self.task_type in MUTATING_TASKS:
            if not self.idempotency_key:
                raise ValueError("idempotency_key is required for mutating kernel tasks.")

        if self.task_type in {KernelTaskType.create_dev_file, KernelTaskType.update_dev_file}:
            if not self.target_path:
                raise ValueError("target_path is required for create/update kernel tasks.")
            try:
                validate_safe_file_path(self.target_path)
            except ValueError as exc:
                raise ValueError(f"path blocked: {exc}") from exc
            if not self.dry_run and self.new_content is None:
                raise ValueError("new_content is required for create/update kernel tasks.")
            if self.new_content is not None and file_content_contains_secret(self.new_content):
                raise ValueError("secret-like content is blocked in new_content.")

        if self.task_type == KernelTaskType.rollback_dev_file and not self.rollback_ref:
            raise ValueError("rollback_ref is required for rollback_dev_file.")

        return self
