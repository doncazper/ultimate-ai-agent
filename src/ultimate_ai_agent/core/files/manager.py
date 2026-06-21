import hashlib
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel as CapabilityRiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.files.diffs import build_redacted_diff_summary, build_unified_diff, read_text_if_exists
from ultimate_ai_agent.core.files.enums import FileKind, FileOperationStatus, FileSensitivity
from ultimate_ai_agent.core.files.hash_refs import (
    content_state_ref,
    diff_ref as build_diff_ref,
    hash_text,
    patch_preview_ref,
    patch_rollback_plan_ref,
    patch_scope_ref,
    receipt_ref,
    safe_file_ref,
    safe_path_ref,
    safe_snapshot_ref,
    safe_tree_label,
    safe_tree_ref,
)
from ultimate_ai_agent.core.files.operations import (
    FileChange,
    FilePatchApplyResult,
    FilePatchMutationReceipt,
    FilePatchProposal,
    FilePatchProposalDecision,
    FilePatchRollbackReceipt,
    FileReadPreview,
    FileReadRequest,
    FileTreeEntry,
    FileTreePreview,
    FileTreePreviewRequest,
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
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.time import utc_now
from ultimate_ai_agent.core.secrets.redaction import redact_secret_value


_PREVIEW_REDACTION_LOOKAHEAD_BYTES = 4096
_TEXT_HASH_CHUNK_CHARS = 1024 * 1024


class LocalFileManager:
    """Local/dev workspace-only file manager."""

    def __init__(self, workspace_root: str | Path, policy: Optional[FileManagerPolicy] = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.policy = policy or FileManagerPolicy()
        self._snapshots: Dict[str, str] = {}
        self._snapshot_meta: Dict[str, FileSnapshot] = {}
        self._rollback_plans: Dict[str, RollbackPlan] = {}
        self._patch_apply_idempotency_keys: set[str] = set()
        self._patch_apply_receipts: Dict[str, FilePatchMutationReceipt] = {}
        self._rollback_idempotency_keys: set[str] = set()
        self._rollback_receipts: Dict[str, FilePatchRollbackReceipt] = {}

    def normalize_path(self, path: str) -> str:
        return normalize_relative_path(path)

    def validate_path(self, path: str) -> str:
        normalized = validate_safe_file_path(path)
        resolved = (self.workspace_root / normalized).resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError("Path outside workspace root is rejected.")
        return normalized

    def build_file_ref(self, path: str) -> FileRef:
        normalized = self.validate_path(path)
        full_path = self.workspace_root / normalized
        stat = full_path.stat() if full_path.exists() else None
        return FileRef(
            file_ref=safe_file_ref(normalized),
            path=normalized,
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
            content_hash=self._hash_text_file(full_path) if stat else hash_text(""),
            size_bytes=stat.st_size if stat else 0,
            created_at=datetime.fromtimestamp(stat.st_ctime) if stat else None,
            updated_at=datetime.fromtimestamp(stat.st_mtime) if stat else None,
        )

    def read_preview(self, request: FileReadRequest) -> FileReadPreview:
        path = request.path or request.file_ref
        if not path:
            raise ValueError("FileReadRequest requires path or file_ref.")
        normalized = self.validate_path(path)
        full_path = self.workspace_root / normalized
        stat = full_path.stat() if full_path.exists() else None
        content = self._read_preview_window(full_path, request.max_bytes) if stat else ""
        redactions = []
        preview_text = content
        if file_content_contains_secret(content):
            preview_text = redact_secret_value(content)
            redactions.append("secret_value")
        truncated = (stat.st_size if stat else 0) > request.max_bytes
        truncated = truncated or len(preview_text.encode("utf-8")) > request.max_bytes
        if truncated:
            preview_text = preview_text.encode("utf-8")[: request.max_bytes].decode("utf-8", errors="ignore")
        return FileReadPreview(
            preview_id=f"frp_{uuid.uuid4().hex[:8]}",
            path=normalized,
            size_bytes=stat.st_size if stat else 0,
            content_hash=self._hash_text_file(full_path) if stat else hash_text(""),
            text_preview=preview_text,
            redactions_applied=redactions,
            truncated=truncated,
            event_ref=request.event_ref,
        )

    def preview_tree(self, request: FileTreePreviewRequest) -> FileTreePreview:
        normalized_root = self.validate_path(request.root_path) if request.root_path else ""
        base = self.workspace_root / normalized_root if normalized_root else self.workspace_root
        root_ref = safe_tree_ref(normalized_root, entry_type="directory")
        entries: List[FileTreeEntry] = []
        blocked_entry_count = 0
        scanned_entry_count = 0
        truncated = False

        if not base.exists() or not base.is_dir() or request.max_depth == 0:
            return FileTreePreview(
                preview_id=f"ftp_{uuid.uuid4().hex[:8]}",
                root_ref=root_ref,
                entries=entries,
                max_depth=request.max_depth,
                max_entries=request.max_entries,
                truncated=False,
                blocked_entry_count=0,
                redactions_applied=["raw_paths_omitted", "safe_refs_only"],
                event_ref=request.event_ref,
            )

        pending = [(base.iterdir(), 1, root_ref)]
        while pending and len(entries) < request.max_entries and scanned_entry_count < request.max_entries:
            iterator, depth, parent_ref = pending[-1]
            try:
                candidate = next(iterator)
            except StopIteration:
                pending.pop()
                continue

            scanned_entry_count += 1
            try:
                entry = self._build_tree_entry(candidate, parent_ref=parent_ref)
            except (OSError, ValueError):
                blocked_entry_count += 1
                continue

            entries.append(entry)
            if entry.entry_type == "directory" and depth < request.max_depth:
                try:
                    pending.append((candidate.iterdir(), depth + 1, entry.entry_ref))
                except OSError:
                    blocked_entry_count += 1

        if pending:
            truncated = True

        redactions = ["raw_paths_omitted", "safe_refs_only"]
        if blocked_entry_count:
            redactions.append("blocked_unsafe_entries")
        return FileTreePreview(
            preview_id=f"ftp_{uuid.uuid4().hex[:8]}",
            root_ref=root_ref,
            entries=entries,
            max_depth=request.max_depth,
            max_entries=request.max_entries,
            truncated=truncated,
            blocked_entry_count=blocked_entry_count,
            redactions_applied=redactions,
            event_ref=request.event_ref,
        )

    def propose_patch(
        self,
        proposal: FilePatchProposal,
        *,
        current_time: datetime | None = None,
    ) -> FilePatchProposalDecision:
        reasons: List[str] = []
        redactions = ["raw_diff_omitted", "safe_refs_only"]
        normalized: str | None = None
        target_ref = safe_path_ref("blocked")
        old_content = ""

        try:
            normalized = self.validate_path(proposal.target_path)
            target_ref = safe_path_ref(normalized)
        except ValueError:
            reasons.append("FILE_PATH_BLOCKED")

        if not proposal.idempotency_key:
            reasons.append("IDEMPOTENCY_KEY_REQUIRED")
        if not proposal.audit_ref:
            reasons.append("AUDIT_REF_REQUIRED")
        if proposal.expires_at is not None:
            now = self._as_utc(current_time or utc_now())
            if self._as_utc(proposal.expires_at) <= now:
                reasons.append("PATCH_PROPOSAL_EXPIRED")
        diff_contains_secret = file_content_contains_secret(proposal.new_content)
        if diff_contains_secret:
            reasons.append("PATCH_DIFF_CONTENT_BLOCKED")
            redactions.append("secret_value")
        if proposal.sensitivity == FileSensitivity.credential_secret:
            reasons.append("CREDENTIAL_SECRET_FILE_REJECTED")

        if normalized is not None:
            full_path = self.workspace_root / normalized
            expected_file_ref = self.build_file_ref(normalized).file_ref
            if proposal.file_ref != expected_file_ref:
                reasons.append("FILE_REF_PATH_BINDING_MISMATCH")
            current_hash = self._hash_text_file(full_path) if full_path.exists() else hash_text("")
            if proposal.expected_existing_hash != current_hash:
                reasons.append("PATCH_PROPOSAL_STALE")
            old_content = read_text_if_exists(full_path)
            if file_content_contains_secret(old_content) and "PATCH_DIFF_CONTENT_BLOCKED" not in reasons:
                diff_contains_secret = True
                reasons.append("PATCH_DIFF_CONTENT_BLOCKED")
                redactions.append("secret_value")

        preview_summary = None
        preview_ref = None
        rollback_plan_ref = None
        if normalized is not None:
            preview_summary = build_redacted_diff_summary(normalized, old_content, proposal.new_content)
        if normalized is not None and not diff_contains_secret:
            preview_ref = patch_preview_ref(proposal.proposal_id, preview_summary)
            rollback_plan_ref = patch_rollback_plan_ref(proposal.proposal_id, target_ref)

        allowed = not reasons
        return FilePatchProposalDecision(
            decision_id=f"fpd_{uuid.uuid4().hex[:8]}",
            proposal_id=proposal.proposal_id,
            allowed=allowed,
            status=FileOperationStatus.proposed if allowed else FileOperationStatus.blocked,
            reason_codes=["PATCH_PROPOSAL_ACCEPTED"] if allowed else reasons,
            safe_message="Patch proposal is safe for exact approval review."
            if allowed
            else "Patch proposal was blocked safely.",
            file_ref=proposal.file_ref,
            target_ref=target_ref,
            expected_existing_hash=proposal.expected_existing_hash,
            preview_ref=preview_ref if allowed else None,
            preview_summary=preview_summary if allowed or diff_contains_secret else None,
            risk_class=ApprovalRiskLevel(proposal.risk_class),
            rollback_plan_ref=rollback_plan_ref if allowed else None,
            idempotency_key=proposal.idempotency_key,
            audit_ref=proposal.audit_ref,
            approval_ref=proposal.approval_ref,
            expires_at=proposal.expires_at,
            redactions_applied=redactions,
            event_ref=proposal.event_ref,
        )

    def approval_request_for_patch(self, proposal: FilePatchProposal) -> ApprovalRequest:
        decision = self.propose_patch(proposal)
        if not decision.allowed:
            raise ValueError("Patch proposal is blocked and cannot be submitted for approval.")
        normalized = self.validate_path(proposal.target_path)
        scope_ref = patch_scope_ref(
            proposal_id=proposal.proposal_id,
            file_ref=proposal.file_ref,
            target_ref=safe_path_ref(normalized),
            expected_existing_hash=proposal.expected_existing_hash,
            idempotency_key=proposal.idempotency_key,
        )
        return ApprovalRequest(
            approval_request_id=f"areq_{proposal.proposal_id}",
            run_id=proposal.run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=proposal.proposal_id,
            actor_context=proposal.actor_context,
            requested_action="apply_file_patch",
            purpose=proposal.purpose,
            risk_level=ApprovalRiskLevel(proposal.risk_class),
            data_classification=self._data_classification_for_sensitivity(proposal.sensitivity),
            resource_refs=[proposal.file_ref, safe_path_ref(normalized), scope_ref],
            file_ref=proposal.file_ref,
            event_ref=proposal.event_ref,
            trace_id=proposal.proposal_id,
            expires_at=proposal.expires_at,
            metadata={"patch_scope_ref": scope_ref},
        )

    def apply_patch_proposal(
        self,
        proposal: FilePatchProposal,
        *,
        approval_authority: LocalApprovalAuthority | None = None,
        current_time: datetime | None = None,
    ) -> FilePatchApplyResult:
        target_ref = self._target_ref_for_proposal(proposal)
        if proposal.idempotency_key in self._patch_apply_idempotency_keys:
            return self._blocked_patch_apply(
                proposal,
                target_ref=target_ref,
                reason_codes=["PATCH_IDEMPOTENCY_REPLAY_BLOCKED"],
                safe_message="Patch apply was blocked as a duplicate idempotency replay.",
            )

        decision = self.propose_patch(proposal, current_time=current_time)
        if not decision.allowed:
            return self._blocked_patch_apply(
                proposal,
                target_ref=decision.target_ref,
                reason_codes=decision.reason_codes,
                safe_message=decision.safe_message,
                redactions_applied=decision.redactions_applied,
            )
        policy_reasons = self._workspace_mutation_policy_denials(
            operation="apply_file_patch",
            target_ref=decision.target_ref,
            idempotency_key=proposal.idempotency_key,
            audit_ref=proposal.audit_ref,
            task_id=proposal.proposal_id,
        )
        if policy_reasons:
            return self._blocked_patch_apply(
                proposal,
                target_ref=decision.target_ref,
                reason_codes=policy_reasons,
                safe_message="Workspace mutation policy denied the patch apply request.",
            )
        if not proposal.approval_ref or approval_authority is None:
            return self._blocked_patch_apply(
                proposal,
                target_ref=decision.target_ref,
                reason_codes=["PATCH_APPROVAL_REQUIRED"],
                safe_message="Patch apply requires an exact local approval grant.",
            )
        if proposal.approval_ref.startswith("approval_test_"):
            return self._blocked_patch_apply(
                proposal,
                target_ref=decision.target_ref,
                reason_codes=["PATCH_APPROVAL_TEST_REF_DENIED"],
                safe_message="Patch apply rejects test approval refs.",
            )

        approval_request = self.approval_request_for_patch(proposal)
        approval_validation = approval_authority.validate(
            approval_request.to_validation_request(proposal.approval_ref).model_copy(
                update={"current_time": current_time}
            )
        )
        if not approval_validation.allowed:
            return self._blocked_patch_apply(
                proposal,
                target_ref=decision.target_ref,
                reason_codes=["PATCH_APPROVAL_DENIED", *approval_validation.reason_codes],
                safe_message="Patch apply approval validation failed safely.",
            )

        normalized = self.validate_path(proposal.target_path)
        full_path = self.workspace_root / normalized
        old_content = read_text_if_exists(full_path)
        before_hash = hash_text(old_content) if full_path.exists() else None
        preimage_ref = content_state_ref("preimage", before_hash)
        snapshot = self.snapshot(normalized)
        rollback_plan = RollbackPlan(
            rollback_ref=f"rb_{uuid.uuid4().hex[:10]}",
            target_path=normalized,
            snapshot_id=snapshot.snapshot_id,
            safe_message="Rollback restores the previous dev-workspace snapshot.",
        )
        self._rollback_plans[rollback_plan.rollback_ref] = rollback_plan

        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._atomic_write_text(full_path, proposal.new_content)
        except Exception:
            failure_receipt = self._build_patch_mutation_receipt(
                proposal,
                status=FileOperationStatus.failed,
                target_ref=decision.target_ref,
                preimage_ref=preimage_ref,
                postimage_ref=content_state_ref("postimage", before_hash),
                rollback_ref=rollback_plan.rollback_ref,
                reason_codes=["PATCH_APPLY_FAILED"],
                safe_message="Patch apply failed before replacement completed; previous content remains inspectable.",
                mutation_performed=False,
            )
            self._patch_apply_receipts[failure_receipt.receipt_ref] = failure_receipt
            return FilePatchApplyResult(
                change_id=f"chg_{uuid.uuid4().hex[:10]}",
                proposal_id=proposal.proposal_id,
                status=FileOperationStatus.failed,
                allowed=False,
                reason_codes=["PATCH_APPLY_FAILED"],
                safe_message=failure_receipt.safe_message,
                file_ref=proposal.file_ref,
                target_ref=decision.target_ref,
                before_hash=before_hash,
                after_hash=before_hash,
                rollback_ref=rollback_plan.rollback_ref,
                receipt_ref=failure_receipt.receipt_ref,
                preimage_ref=preimage_ref,
                postimage_ref=failure_receipt.postimage_ref,
                idempotency_key=proposal.idempotency_key,
                audit_ref=proposal.audit_ref,
                approval_ref=proposal.approval_ref,
                redactions_applied=failure_receipt.redactions_applied,
                receipt=failure_receipt,
            )
        after_hash = hash_text(proposal.new_content)
        postimage_ref = content_state_ref("postimage", after_hash)
        self._patch_apply_idempotency_keys.add(proposal.idempotency_key)
        receipt = self._build_patch_mutation_receipt(
            proposal,
            status=FileOperationStatus.applied,
            target_ref=decision.target_ref,
            preimage_ref=preimage_ref,
            postimage_ref=postimage_ref,
            rollback_ref=rollback_plan.rollback_ref,
            reason_codes=["PATCH_APPLIED"],
            safe_message="Patch applied atomically with rollback evidence captured.",
            mutation_performed=True,
        )
        self._patch_apply_receipts[receipt.receipt_ref] = receipt
        return FilePatchApplyResult(
            change_id=f"chg_{uuid.uuid4().hex[:10]}",
            proposal_id=proposal.proposal_id,
            status=FileOperationStatus.applied,
            allowed=True,
            reason_codes=["PATCH_APPLIED"],
            safe_message="Patch applied with exact approval and rollback captured.",
            file_ref=proposal.file_ref,
            target_ref=decision.target_ref,
            before_hash=before_hash,
            after_hash=after_hash,
            rollback_ref=rollback_plan.rollback_ref,
            receipt_ref=receipt.receipt_ref,
            preimage_ref=preimage_ref,
            postimage_ref=postimage_ref,
            idempotency_key=proposal.idempotency_key,
            audit_ref=proposal.audit_ref,
            approval_ref=proposal.approval_ref,
            applied_at=utc_now(),
            redactions_applied=receipt.redactions_applied,
            receipt=receipt,
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
        existing_hash = hash_text(read_text_if_exists(full_path)) if full_path.exists() else None
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
            diff_ref=build_diff_ref(diff),
            rollback_ref=None,
            event_ref=proposal.event_ref,
        )

    def diff_preview(self, proposal: FileWriteProposal) -> str:
        normalized = self.validate_path(proposal.target_path)
        old_content = read_text_if_exists(self.workspace_root / normalized)
        return build_unified_diff(normalized, old_content, proposal.new_content)

    def redacted_diff_summary(self, proposal: FileWriteProposal) -> str:
        normalized = self.validate_path(proposal.target_path)
        old_content = read_text_if_exists(self.workspace_root / normalized)
        return build_redacted_diff_summary(normalized, old_content, proposal.new_content)

    def apply_write(self, proposal: FileWriteProposal) -> FileChange:
        raise PermissionError(
            "Workspace mutation requires exact patch proposal approval through "
            "apply_patch_proposal; shell and subprocess mutation paths are unavailable."
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
            content_hash=hash_text(content),
            content_ref=f"in_memory:{snapshot_id}",
        )
        self._snapshot_meta[snapshot_id] = snapshot
        return snapshot

    def rollback(self, rollback_plan: RollbackPlan) -> FileChange:
        raise PermissionError(
            "Workspace rollback requires exact rollback approval through "
            "rollback_with_receipt; shell and subprocess mutation paths are unavailable."
        )

    def approval_request_for_rollback(
        self,
        rollback_plan: RollbackPlan,
        *,
        run_id: str,
        actor_context: Any,
        purpose: str = "Approve rollback for an approval-bound workspace mutation.",
        event_ref: str | None = None,
    ) -> ApprovalRequest:
        target_ref = self._target_ref_for_rollback(rollback_plan)
        snapshot_ref = safe_snapshot_ref(rollback_plan.snapshot_id)
        return ApprovalRequest(
            approval_request_id=f"areq_{rollback_plan.rollback_ref}",
            run_id=run_id,
            subject_type=ApprovalSubjectType.file_write,
            subject_id=rollback_plan.rollback_ref,
            actor_context=actor_context,
            requested_action="rollback_file_patch",
            purpose=purpose,
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.project_private,
                source="file_rollback",
                requires_redaction=True,
            ),
            resource_refs=[rollback_plan.rollback_ref, target_ref, snapshot_ref],
            event_ref=event_ref,
            trace_id=rollback_plan.rollback_ref,
            metadata={"target_ref": target_ref, "snapshot_ref": snapshot_ref},
        )

    def rollback_with_receipt(
        self,
        rollback_plan: RollbackPlan,
        *,
        audit_ref: str,
        idempotency_key: str,
        approval_ref: str | None = None,
        approval_authority: LocalApprovalAuthority | None = None,
        run_id: str | None = None,
        actor_context: Any | None = None,
        purpose: str = "Approve rollback for an approval-bound workspace mutation.",
    ) -> FilePatchRollbackReceipt:
        if idempotency_key in self._rollback_idempotency_keys:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.blocked,
                target_ref=self._target_ref_for_rollback(rollback_plan),
                preimage_ref=None,
                restored_image_ref=None,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=["ROLLBACK_IDEMPOTENCY_REPLAY_BLOCKED"],
                safe_message="Rollback was blocked as a duplicate idempotency replay.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt
        target_ref = self._target_ref_for_rollback(rollback_plan)
        policy_reasons = self._workspace_mutation_policy_denials(
            operation="rollback_file_patch",
            target_ref=target_ref,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            task_id=rollback_plan.rollback_ref,
        )
        if policy_reasons:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.blocked,
                target_ref=target_ref,
                preimage_ref=None,
                restored_image_ref=None,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=policy_reasons,
                safe_message="Workspace mutation policy denied the rollback request.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt
        if not approval_ref or approval_authority is None or run_id is None or actor_context is None:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.blocked,
                target_ref=target_ref,
                preimage_ref=None,
                restored_image_ref=None,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=["ROLLBACK_APPROVAL_REQUIRED"],
                safe_message="Rollback requires an exact local approval grant.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt
        rollback_approval = self.approval_request_for_rollback(
            rollback_plan,
            run_id=run_id,
            actor_context=actor_context,
            purpose=purpose,
        )
        approval_validation = approval_authority.validate(rollback_approval.to_validation_request(approval_ref))
        if not approval_validation.allowed:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.blocked,
                target_ref=target_ref,
                preimage_ref=None,
                restored_image_ref=None,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=["ROLLBACK_APPROVAL_DENIED", *approval_validation.reason_codes],
                safe_message="Rollback approval validation failed safely.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt
        if not rollback_plan.snapshot_id or rollback_plan.snapshot_id not in self._snapshots:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.failed,
                target_ref=target_ref,
                preimage_ref=None,
                restored_image_ref=None,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=["ROLLBACK_SNAPSHOT_UNAVAILABLE"],
                safe_message="Rollback snapshot is unavailable.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt

        normalized = self.validate_path(rollback_plan.target_path)
        target_ref = safe_path_ref(normalized)
        full_path = self.workspace_root / normalized
        before_hash = hash_text(read_text_if_exists(full_path)) if full_path.exists() else None
        preimage_ref = content_state_ref("rollback_preimage", before_hash)
        content = self._snapshots[rollback_plan.snapshot_id]
        restored_ref = content_state_ref("rollback_restored", hash_text(content))
        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._atomic_write_text(full_path, content)
        except Exception:
            receipt = self._build_rollback_receipt(
                rollback_ref=rollback_plan.rollback_ref,
                status=FileOperationStatus.failed,
                target_ref=target_ref,
                preimage_ref=preimage_ref,
                restored_image_ref=preimage_ref,
                idempotency_key=idempotency_key,
                audit_ref=audit_ref,
                approval_ref=approval_ref,
                reason_codes=["ROLLBACK_APPLY_FAILED"],
                safe_message="Rollback failed before replacement completed; current content remains inspectable.",
                rollback_performed=False,
            )
            self._rollback_receipts[receipt.receipt_ref] = receipt
            return receipt

        self._rollback_idempotency_keys.add(idempotency_key)
        receipt = self._build_rollback_receipt(
            rollback_ref=rollback_plan.rollback_ref,
            status=FileOperationStatus.rolled_back,
            target_ref=target_ref,
            preimage_ref=preimage_ref,
            restored_image_ref=restored_ref,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            approval_ref=approval_ref,
            reason_codes=["ROLLBACK_APPLIED"],
            safe_message="Rollback restored the prior snapshot atomically.",
            rollback_performed=True,
        )
        self._rollback_receipts[receipt.receipt_ref] = receipt
        return receipt

    def get_patch_apply_receipt(self, receipt_ref: str) -> FilePatchMutationReceipt:
        if receipt_ref not in self._patch_apply_receipts:
            raise ValueError("Patch apply receipt is unavailable.")
        return self._patch_apply_receipts[receipt_ref]

    def get_rollback_receipt(self, receipt_ref: str) -> FilePatchRollbackReceipt:
        if receipt_ref not in self._rollback_receipts:
            raise ValueError("Rollback receipt is unavailable.")
        return self._rollback_receipts[receipt_ref]

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

    def _build_tree_entry(self, path: Path, *, parent_ref: str) -> FileTreeEntry:
        if path.is_symlink():
            raise ValueError("Symlink entries are blocked from safe tree previews.")
        resolved = path.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError("Tree entry outside workspace root is rejected.") from exc
        normalized = self.validate_path(str(path.relative_to(self.workspace_root)))
        is_directory = path.is_dir()
        entry_type = "directory" if is_directory else "file"
        stat = path.stat()
        entry_ref = safe_tree_ref(normalized, entry_type=entry_type)
        return FileTreeEntry(
            entry_ref=entry_ref,
            parent_ref=parent_ref,
            entry_type=entry_type,
            safe_label=safe_tree_label(normalized, entry_type=entry_type),
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
            size_bytes=0 if is_directory else stat.st_size,
            child_count=0,
            preview_available=not is_directory,
            redactions_applied=["raw_path_omitted"],
        )

    def _target_ref_for_proposal(self, proposal: FilePatchProposal) -> str:
        try:
            return safe_path_ref(self.validate_path(proposal.target_path))
        except ValueError:
            return safe_path_ref("blocked")

    def _target_ref_for_rollback(self, rollback_plan: RollbackPlan) -> str:
        try:
            return safe_path_ref(self.validate_path(rollback_plan.target_path))
        except ValueError:
            return safe_path_ref("blocked")

    def _workspace_mutation_policy_denials(
        self,
        *,
        operation: str,
        target_ref: str,
        idempotency_key: str,
        audit_ref: str,
        task_id: str,
    ) -> List[str]:
        manifest = self._workspace_mutation_manifest(operation)
        task = TaskEnvelope(
            task_id=f"workspace-mutation-policy:{task_id}",
            user_request=f"Evaluate approval-bound workspace mutation policy for {operation}.",
            objective="Require exact approval before any local workspace mutation.",
            selected_capability_ids=[manifest.id],
            allowed_tool_ids=[manifest.id],
            context={
                "idempotency_key": idempotency_key,
                "target_ref": target_ref,
                "audit_ref": audit_ref,
            },
        )
        decision = PolicyEngine(default_max_risk=CapabilityRiskLevel.high).can_execute(
            manifest,
            task,
            {
                "max_risk_level": CapabilityRiskLevel.high.value,
                "idempotency_key": idempotency_key,
            },
        )
        if decision.status == PolicyDecisionStatus.approval_required and decision.requires_approval:
            return []
        return ["WORKSPACE_MUTATION_POLICY_DENIED", *decision.reason_codes]

    def _workspace_mutation_manifest(self, operation: str) -> CapabilityManifest:
        return CapabilityManifest(
            id=f"workspace.file.{operation}",
            version="p1-037",
            kind=CapabilityKind.tool,
            name=f"workspace.file.{operation}",
            description="Policy gate for approval-bound local workspace file mutation.",
            owner="core.files",
            tags=["workspace", "file", "approval"],
            examples=["Apply an exact-approved workspace patch using safe refs."],
            anti_examples=["Direct file mutation, shell mutation, subprocess mutation, or unapproved rollback."],
            input_schema={
                "type": "object",
                "required": ["target_ref", "idempotency_key", "audit_ref"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "required": ["approval_required"],
                "additionalProperties": True,
            },
            input_modes=["safe_ref", "redacted_summary"],
            output_modes=["policy_decision"],
            side_effects=SideEffectLevel.write,
            risk_level=CapabilityRiskLevel.high,
            approval_required=True,
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            single_writer_required=True,
            safety=SafetyPolicy(
                require_single_writer=True,
                approval_required=True,
                max_risk_level=CapabilityRiskLevel.high,
                max_side_effect_level=SideEffectLevel.write,
            ),
        )

    def _build_patch_mutation_receipt(
        self,
        proposal: FilePatchProposal,
        *,
        status: FileOperationStatus,
        target_ref: str,
        preimage_ref: Optional[str],
        postimage_ref: Optional[str],
        rollback_ref: Optional[str],
        reason_codes: List[str],
        safe_message: str,
        mutation_performed: bool,
    ) -> FilePatchMutationReceipt:
        mutation_receipt_ref = receipt_ref(
            "file_patch_receipt",
            proposal.proposal_id,
            proposal.idempotency_key,
            str(status),
            uuid.uuid4().hex[:8],
        )
        return FilePatchMutationReceipt(
            receipt_ref=mutation_receipt_ref,
            proposal_id=proposal.proposal_id,
            status=status,
            file_ref=proposal.file_ref,
            target_ref=target_ref,
            preimage_ref=preimage_ref,
            postimage_ref=postimage_ref,
            rollback_ref=rollback_ref,
            idempotency_key=proposal.idempotency_key,
            audit_ref=proposal.audit_ref,
            approval_ref=proposal.approval_ref,
            reason_codes=reason_codes,
            safe_message=safe_message,
            mutation_performed=mutation_performed,
            redactions_applied=["raw_content_omitted", "raw_path_omitted", "safe_refs_only"],
        )

    def _build_rollback_receipt(
        self,
        *,
        rollback_ref: str,
        status: FileOperationStatus,
        target_ref: str,
        preimage_ref: Optional[str],
        restored_image_ref: Optional[str],
        idempotency_key: str,
        audit_ref: str,
        approval_ref: Optional[str],
        reason_codes: List[str],
        safe_message: str,
        rollback_performed: bool,
    ) -> FilePatchRollbackReceipt:
        rollback_receipt_ref = receipt_ref(
            "file_rollback_receipt",
            rollback_ref,
            idempotency_key,
            str(status),
            uuid.uuid4().hex[:8],
        )
        return FilePatchRollbackReceipt(
            receipt_ref=rollback_receipt_ref,
            rollback_ref=rollback_ref,
            status=status,
            target_ref=target_ref,
            preimage_ref=preimage_ref,
            restored_image_ref=restored_image_ref,
            idempotency_key=idempotency_key,
            audit_ref=audit_ref,
            approval_ref=approval_ref,
            reason_codes=reason_codes,
            safe_message=safe_message,
            rollback_performed=rollback_performed,
            redactions_applied=["raw_content_omitted", "raw_path_omitted", "safe_refs_only"],
        )

    def _blocked_patch_apply(
        self,
        proposal: FilePatchProposal,
        *,
        target_ref: str,
        reason_codes: List[str],
        safe_message: str,
        redactions_applied: Optional[List[str]] = None,
    ) -> FilePatchApplyResult:
        return FilePatchApplyResult(
            change_id=f"chg_{uuid.uuid4().hex[:10]}",
            proposal_id=proposal.proposal_id,
            status=FileOperationStatus.blocked,
            allowed=False,
            reason_codes=reason_codes,
            safe_message=safe_message,
            file_ref=proposal.file_ref,
            target_ref=target_ref,
            rollback_ref=None,
            idempotency_key=proposal.idempotency_key,
            audit_ref=proposal.audit_ref,
            approval_ref=proposal.approval_ref,
            redactions_applied=redactions_applied or ["raw_diff_omitted", "safe_refs_only"],
        )

    def _data_classification_for_sensitivity(self, sensitivity: FileSensitivity) -> DataClassification:
        mapping = {
            FileSensitivity.public: ClassificationValue.public,
            FileSensitivity.project_private: ClassificationValue.project_private,
            FileSensitivity.user_private: ClassificationValue.user_private,
            FileSensitivity.sensitive_personal: ClassificationValue.sensitive_personal,
            FileSensitivity.credential_secret: ClassificationValue.credential_secret,
            FileSensitivity.regulated: ClassificationValue.regulated,
            FileSensitivity.system_internal: ClassificationValue.system_internal,
            FileSensitivity.tcb_protected: ClassificationValue.tcb_protected,
        }
        return DataClassification(
            classification=mapping.get(FileSensitivity(sensitivity), ClassificationValue.project_private),
            source="file_patch_proposal",
            requires_redaction=True,
        )

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

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

    def _hash_text_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("r", encoding="utf-8", errors="ignore", newline=None) as handle:
            for chunk in iter(lambda: handle.read(_TEXT_HASH_CHUNK_CHARS), ""):
                digest.update(chunk.encode("utf-8"))
        return digest.hexdigest()

    def _read_preview_window(self, path: Path, max_bytes: int) -> str:
        window_bytes = max_bytes + _PREVIEW_REDACTION_LOOKAHEAD_BYTES
        with path.open("rb") as handle:
            content = handle.read(window_bytes)
        return content.decode("utf-8", errors="ignore")

    def _atomic_write_text(self, path: Path, content: str) -> None:
        temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            os.replace(temp_path, path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
