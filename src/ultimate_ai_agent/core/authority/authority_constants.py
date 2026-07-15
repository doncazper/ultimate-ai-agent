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

MATRIX_HARNESS_INSPECT_TOOL_REF = "tool-ref:matrix-harness-inspect:v1"
MATRIX_HARNESS_SMOKE_TOOL_REF = "tool-ref:matrix-harness-smoke:v1"
MATRIX_HARNESS_START_TOOL_REF = "tool-ref:matrix-harness-start:v1"
MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF = "tool-ref:matrix-harness-fixture-seed:v1"
MATRIX_HARNESS_STOP_TOOL_REF = "tool-ref:matrix-harness-stop:v1"
MATRIX_HARNESS_RESET_TOOL_REF = "tool-ref:matrix-harness-reset:v1"

# Exact lane bindings accepted by the generic AuthorityLease store. Keeping
# these bindings in the authority package prevents the coarse ``messages``
# domain from becoming a standing grant for future connector or send lanes.
MATRIX_HARNESS_EXACT_AUTHORITY_BINDINGS = (
    (
        "read",
        "authority-lane-ref:matrix-harness-inspect",
        "authority-capability-ref:matrix-harness-inspect-v1",
        "authority-adapter-ref:matrix-harness-inspect-v1",
        MATRIX_HARNESS_INSPECT_TOOL_REF,
    ),
    (
        "read",
        "authority-lane-ref:matrix-harness-smoke",
        "authority-capability-ref:matrix-harness-smoke-v1",
        "authority-adapter-ref:matrix-harness-smoke-v1",
        MATRIX_HARNESS_SMOKE_TOOL_REF,
    ),
    (
        "execute",
        "authority-lane-ref:matrix-harness-start",
        "authority-capability-ref:matrix-harness-start-v1",
        "authority-adapter-ref:matrix-harness-start-v1",
        MATRIX_HARNESS_START_TOOL_REF,
    ),
    (
        "mutate",
        "authority-lane-ref:matrix-harness-fixture-seed",
        "authority-capability-ref:matrix-harness-fixture-seed-v1",
        "authority-adapter-ref:matrix-harness-fixture-seed-v1",
        MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF,
    ),
    (
        "execute",
        "authority-lane-ref:matrix-harness-stop",
        "authority-capability-ref:matrix-harness-stop-v1",
        "authority-adapter-ref:matrix-harness-stop-v1",
        MATRIX_HARNESS_STOP_TOOL_REF,
    ),
    (
        "mutate",
        "authority-lane-ref:matrix-harness-reset",
        "authority-capability-ref:matrix-harness-reset-v1",
        "authority-adapter-ref:matrix-harness-reset-v1",
        MATRIX_HARNESS_RESET_TOOL_REF,
    ),
)
