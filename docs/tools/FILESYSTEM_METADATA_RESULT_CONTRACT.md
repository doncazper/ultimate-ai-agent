# Filesystem Metadata Result Contract

Status: active M32 documentation.
Current active baseline: **v0.37.0**

M32 filesystem metadata results are safe summary envelopes. They are
non-authoritative and metadata-only.

Result envelopes may include:

- `safe_path_ref`.
- `root_ref`.
- `exists`.
- `path_kind`.
- `size_bytes`.
- `extension`.
- `modified_time_ns`.
- safe reason codes.

Result envelopes must not include:

- raw file content.
- text preview.
- content hash.
- directory child listing.
- recursive traversal output.
- absolute local path.
- symlink target.
- shell command output.
- memory writes or Event Ledger mutations.

The receipt plan records a non-authoritative runtime receipt summary only. It
does not store raw input, raw output, file content, or side effects.
