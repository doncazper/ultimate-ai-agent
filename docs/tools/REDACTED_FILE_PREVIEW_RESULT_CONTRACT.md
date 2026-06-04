# Redacted File Preview Result Contract

Status: active M33 documentation.
Current active baseline: **v0.37.0**

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

M34 remains planned/provisional.

