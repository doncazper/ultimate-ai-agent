AUTHORITY_STATE_LOCK_KEY = "authority-state"
AUTHORITY_BUDGET_RECEIPTS_FILE = "authority_budget_receipts.jsonl"
AUTHORITY_DISPATCH_RECEIPTS_FILE = "authority_dispatch_receipts.jsonl"
AUTHORITY_STATE_REDACTIONS = (
    "safe_refs_only",
    "bounded_summaries_only",
    "raw_prompt_omitted",
    "raw_response_omitted",
    "raw_log_omitted",
    "local_paths_omitted",
    "provider_payload_omitted",
    "credentials_omitted",
)

PORTABLE_EVIDENCE_SIGN_TOOL_REF = "tool-ref:portable-evidence-sign:v1"
PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF = "tool-ref:portable-evidence-key-create:v1"
PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF = "tool-ref:portable-evidence-key-rotate:v1"
PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF = "tool-ref:portable-evidence-key-revoke:v1"
PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF = (
    "tool-ref:portable-evidence-key-mark-lost:v1"
)
PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF = (
    "tool-ref:portable-evidence-key-material-cleanup:v1"
)
