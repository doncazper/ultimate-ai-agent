# Redacted File Preview Result Contract

Status: active M33 documentation.
Current active baseline: **v0.37.1**

M33 returns a `RedactedFilePreviewOutput` only after policy and redaction pass.
The result is non-authoritative and redacted-preview-only.

Result guarantees:

- includes `redacted_preview`.
- includes `redaction_summary`.
- includes `preview_truncated` and `preview_limit_bytes`.
- includes safe refs such as `safe_path_ref`, not raw absolute paths.
- sets `raw_content_returned=false`.
- sets `raw_content_stored=false`.
- sets `full_file_returned=false`.
- sets `content_hash_returned=false`.
- sets `directory_listing_returned=false`.
- sets `absolute_path_returned=false`.
- sets `mutation_performed=false`.
- sets `context_injection_performed=false`.
- has `side_effects_performed=[]`.

The result schema has no raw content field. Redacted previews are not full-file
read output, not source-of-truth authority, and not context injection.

v0.37.1 hardens the result boundary so `RedactedFilePreviewOutput` rejects
secret-like preview text such as API-key assignments, bearer tokens, password
assignments, private-key markers, or high-entropy-looking tokens. That check is
independent of the redaction pipeline so a directly constructed or
model_copy-mutated output cannot become an unredacted preview carrier.

M34 remains planned/provisional.
