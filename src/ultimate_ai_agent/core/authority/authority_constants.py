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
