from __future__ import annotations

from ultimate_ai_agent.core.safe_refs import hash_bytes as hash_bytes
from ultimate_ai_agent.core.safe_refs import hash_text


def safe_file_ref(normalized_path: str) -> str:
    return f"file_{hash_text(normalized_path)[:12]}"


def safe_path_ref(normalized_path: str) -> str:
    return f"file_path_{hash_text(normalized_path)[:16]}"


def safe_snapshot_ref(snapshot_id: str | None) -> str:
    digest_source = snapshot_id or "missing"
    return f"file_snapshot_{hash_text(digest_source)[:16]}"


def content_state_ref(prefix: str, content_hash: str | None) -> str:
    digest_source = content_hash or "missing"
    return f"file_{prefix}_{hash_text(digest_source)[:16]}"


def receipt_ref(prefix: str, *parts: str) -> str:
    digest_source = "|".join(parts)
    return f"{prefix}_{hash_text(digest_source)[:16]}"


def diff_ref(diff: str) -> str:
    return f"diff_{hash_text(diff)[:12]}"


def patch_preview_ref(proposal_id: str, preview_summary: str) -> str:
    return f"patch_preview_{hash_text(proposal_id + preview_summary)[:12]}"


def patch_rollback_plan_ref(proposal_id: str, target_ref: str) -> str:
    return f"patch_rollback_plan_{hash_text(proposal_id + target_ref)[:12]}"


def patch_scope_ref(
    *,
    proposal_id: str,
    file_ref: str,
    target_ref: str,
    expected_existing_hash: str,
    idempotency_key: str,
) -> str:
    scope = "|".join(
        [
            proposal_id,
            file_ref,
            target_ref,
            expected_existing_hash,
            idempotency_key,
        ]
    )
    return f"file_patch_scope_{hash_text(scope)[:16]}"


def safe_tree_ref(normalized_path: str, *, entry_type: str) -> str:
    ref_source = f"{entry_type}:{normalized_path or '<workspace-root>'}"
    return f"file_tree_{hash_text(ref_source)[:16]}"


def safe_tree_label(normalized_path: str, *, entry_type: str) -> str:
    digest = hash_text(normalized_path)[:8]
    return f"{entry_type}_ref_{digest}"
