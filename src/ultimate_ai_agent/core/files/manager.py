import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ultimate_ai_agent.core.files.diffs import build_unified_diff, read_text_if_exists
from ultimate_ai_agent.core.files.enums import FileKind, FileOperation, FileOperationStatus, FileSensitivity
from ultimate_ai_agent.core.files.operations import (
    FileChange,
    FileReadPreview,
    FileReadRequest,
    FileWriteDecision,
    FileWriteProposal,
)
from ultimate_ai_agent.core.files.policies import FileManagerPolicy
from ultimate_ai_agent.core.files.refs import FileRef
from ultimate_ai_agent.core.files.rollback import RollbackPlan
from ultimate_ai_agent.core.files.snapshots import FileSnapshot
from ultimate_ai_agent.core.files.validation import (
    file_content_contains_secret,
    normalize_relative_path,
    validate_safe_file_path,
)
from ultimate_ai_agent.core.secrets.redaction import redact_secret_value


class LocalFileManager:
    """Local/dev workspace-only file manager."""

    def __init__(self, workspace_root: str | Path, policy: Optional[FileManagerPolicy] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.policy = policy or FileManagerPolicy()
        self._snapshots: Dict[str, str] = {}
        self._snapshot_meta: Dict[str, FileSnapshot] = {}
        self._rollback_plans: Dict[str, RollbackPlan] = {}

    def normalize_path(self, path: str) -> str:
        return normalize_relative_path(path)

    def validate_path(self, path: str) -> str:
        normalized = validate_safe_file_path(path)
        resolved = (self.workspace_root / normalized).resolve()
        if self.workspace_root not in [resolved, *resolved.parents]:
            raise ValueError("Path outside workspace root is rejected.")
        return normalized

    def build_file_ref(self, path: str) -> FileRef:
        normalized = self.validate_path(path)
        full_path = self.workspace_root / normalized
        content = full_path.read_bytes() if full_path.exists() else b""
        stat = full_path.stat() if full_path.exists() else None
        return FileRef(
            file_ref=f"file_{hashlib.sha256(normalized.encode()).hexdigest()[:12]}",
            path=normalized,
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
            content_hash=self._hash_bytes(content),
            size_bytes=len(content),
            created_at=datetime.fromtimestamp(stat.st_ctime) if stat else None,
            updated_at=datetime.fromtimestamp(stat.st_mtime) if stat else None,
        )

    def read_preview(self, request: FileReadRequest) -> FileReadPreview:
        path = request.path or request.file_ref
        if not path:
            raise ValueError("FileReadRequest requires path or file_ref.")
        normalized = self.validate_path(path)
        full_path = self.workspace_root / normalized
        content = full_path.read_text(encoding="utf-8") if full_path.exists() else ""
        redactions = []
        preview_text = content
        if file_content_contains_secret(content):
            preview_text = redact_secret_value(content)
            redactions.append("secret_value")
        truncated = len(preview_text.encode("utf-8")) > request.max_bytes
        if truncated:
            preview_text = preview_text.encode("utf-8")[: request.max_bytes].decode("utf-8", errors="ignore")
        return FileReadPreview(
            preview_id=f"frp_{uuid.uuid4().hex[:8]}",
            path=normalized,
            size_bytes=len(content.encode("utf-8")),
            content_hash=self._hash_text(content),
            text_preview=preview_text,
            redactions_applied=redactions,
            truncated=truncated,
            event_ref=request.event_ref,
        )

    def propose_write(self, proposal: FileWriteProposal) -> FileWriteDecision:
        reasons: List[str] = []
        redactions: List[str] = []
        try:
            normalized = self.validate_path(proposal.target_path)
        except ValueError:
            return self._blocked(proposal, ["FILE_PATH_BLOCKED"], "The target path is blocked or outside the workspace.")

        if not proposal.idempotency_key:
            reasons.append("IDEMPOTENCY_KEY_REQUIRED")
        if file_content_contains_secret(proposal.new_content):
            reasons.append("SECRET_CONTENT_BLOCKED")
            redactions.append("secret_value")
        if proposal.sensitivity == FileSensitivity.credential_secret:
            reasons.append("CREDENTIAL_SECRET_FILE_REJECTED")
        if self.policy.strict_contract_paths and normalized not in self.policy.allowed_update_paths:
            reasons.append("CONTRACT_FILE_NOT_ALLOWED")

        full_path = self.workspace_root / normalized
        existing_hash = self._hash_text(read_text_if_exists(full_path)) if full_path.exists() else None
        if full_path.exists():
            protected = proposal.file_kind in self.policy.protected_kinds
            if protected and not proposal.expected_existing_hash and not self.policy.allow_overwrite_without_hash:
                reasons.append("EXPECTED_HASH_REQUIRED")
            if proposal.expected_existing_hash and proposal.expected_existing_hash != existing_hash:
                reasons.append("EXPECTED_HASH_MISMATCH")

        if reasons:
            return self._blocked(proposal, reasons, "The file write proposal was blocked.", redactions)

        diff = self.diff_preview(proposal)
        return FileWriteDecision(
            decision_id=f"fwd_{uuid.uuid4().hex[:8]}",
            proposal_id=proposal.proposal_id,
            allowed=True,
            status=FileOperationStatus.proposed,
            reason_codes=["WRITE_PROPOSAL_ACCEPTED"],
            safe_message="File write proposal is safe to apply in this dev workspace.",
            diff_ref=f"diff_{hashlib.sha256(diff.encode()).hexdigest()[:12]}",
            rollback_ref=None,
            event_ref=proposal.event_ref,
        )

    def diff_preview(self, proposal: FileWriteProposal) -> str:
        normalized = self.validate_path(proposal.target_path)
        old_content = read_text_if_exists(self.workspace_root / normalized)
        return build_unified_diff(normalized, old_content, proposal.new_content)

    def apply_write(self, proposal: FileWriteProposal) -> FileChange:
        decision = self.propose_write(proposal)
        if not decision.allowed:
            raise ValueError(decision.safe_message)

        normalized = self.validate_path(proposal.target_path)
        full_path = self.workspace_root / normalized
        before_hash = self._hash_text(read_text_if_exists(full_path)) if full_path.exists() else None
        snapshot = self.snapshot(normalized)
        rollback_plan = RollbackPlan(
            rollback_ref=f"rb_{uuid.uuid4().hex[:10]}",
            target_path=normalized,
            snapshot_id=snapshot.snapshot_id,
            safe_message="Rollback restores the previous dev-workspace snapshot.",
        )
        self._rollback_plans[rollback_plan.rollback_ref] = rollback_plan

        full_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = full_path.with_name(f".{full_path.name}.{uuid.uuid4().hex}.tmp")
        temp_path.write_text(proposal.new_content, encoding="utf-8")
        os.replace(temp_path, full_path)

        after_hash = self._hash_text(proposal.new_content)
        return FileChange(
            change_id=f"chg_{uuid.uuid4().hex[:10]}",
            target_path=normalized,
            operation=FileOperation.apply_write,
            before_hash=before_hash,
            after_hash=after_hash,
            diff_summary=self.diff_preview(proposal),
            applied_at=datetime.utcnow(),
            rollback_ref=rollback_plan.rollback_ref,
        )

    def snapshot(self, path: str) -> FileSnapshot:
        normalized = self.validate_path(path)
        full_path = self.workspace_root / normalized
        content = read_text_if_exists(full_path)
        snapshot_id = f"snap_{uuid.uuid4().hex[:10]}"
        self._snapshots[snapshot_id] = content
        snapshot = FileSnapshot(
            snapshot_id=snapshot_id,
            path=normalized,
            content_hash=self._hash_text(content),
            content_ref=f"in_memory:{snapshot_id}",
        )
        self._snapshot_meta[snapshot_id] = snapshot
        return snapshot

    def rollback(self, rollback_plan: RollbackPlan) -> FileChange:
        if not rollback_plan.snapshot_id or rollback_plan.snapshot_id not in self._snapshots:
            raise ValueError("Rollback snapshot is unavailable.")
        normalized = self.validate_path(rollback_plan.target_path)
        full_path = self.workspace_root / normalized
        before_hash = self._hash_text(read_text_if_exists(full_path)) if full_path.exists() else None
        content = self._snapshots[rollback_plan.snapshot_id]
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return FileChange(
            change_id=f"chg_{uuid.uuid4().hex[:10]}",
            target_path=normalized,
            operation=FileOperation.rollback,
            before_hash=before_hash,
            after_hash=self._hash_text(content),
            diff_summary="Rollback restored a prior in-memory snapshot.",
            applied_at=datetime.utcnow(),
            rollback_ref=rollback_plan.rollback_ref,
        )

    def get_rollback_plan(self, rollback_ref: Optional[str]) -> RollbackPlan:
        if rollback_ref is None or rollback_ref not in self._rollback_plans:
            raise ValueError("Rollback plan is unavailable.")
        return self._rollback_plans[rollback_ref]

    def list_index(self, root: Optional[str] = None) -> List[FileRef]:
        normalized_root = self.validate_path(root) if root else ""
        base = self.workspace_root / normalized_root
        if not base.exists() or not base.is_dir():
            return []
        return [self.build_file_ref(str(path.relative_to(self.workspace_root))) for path in base.iterdir() if path.is_file()]

    def _blocked(
        self,
        proposal: FileWriteProposal,
        reason_codes: List[str],
        safe_message: str,
        redactions_applied: Optional[List[str]] = None,
    ) -> FileWriteDecision:
        return FileWriteDecision(
            decision_id=f"fwd_{uuid.uuid4().hex[:8]}",
            proposal_id=proposal.proposal_id,
            allowed=False,
            status=FileOperationStatus.blocked,
            reason_codes=reason_codes,
            safe_message=safe_message,
            redactions_applied=redactions_applied or [],
            event_ref=proposal.event_ref,
        )

    def _hash_text(self, content: str) -> str:
        return self._hash_bytes(content.encode("utf-8"))

    def _hash_bytes(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
