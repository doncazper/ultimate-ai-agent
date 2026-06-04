# Redacted File Preview Policy

Status: active M33 documentation.
Current active baseline: **v0.38.2**

M33 preview policy enables only bounded redacted preview generation. Generic raw
content reads, full-file reads, content hashes, directory listing, recursive
traversal, symlink following, caller-selected roots, context injection, and file
mutation remain disabled.

Required policy posture:

| Policy field | M33 value |
|---|---|
| `redacted_preview_enabled` | `true` |
| `raw_content_enabled` | `false` |
| `full_file_read_enabled` | `false` |
| `content_hash_enabled` | `false` |
| `directory_listing_enabled` | `false` |
| `recursive_traversal_enabled` | `false` |
| `symlink_following_enabled` | `false` |
| `caller_selected_root_enabled` | `false` |
| `file_write_enabled` | `false` |
| `file_delete_enabled` | `false` |
| `filesystem_mutation_enabled` | `false` |
| `context_injection_enabled` | `false` |

Safe roots are server-owned or explicit test fixtures. Requests identify the
root by safe `root_ref`; callers cannot supply arbitrary absolute roots. Paths
must be relative and normalized through the M32 path policy. Absolute paths,
traversal, hidden paths, secret-like paths, private-key-like paths, directory
paths, symlinks, binary files, unsupported encodings, and oversized files are
denied before any result is created.

v0.37.1 additionally treats a safe-root path that is itself a symlink as
unsafe. The evaluator revalidates the current safe root, relative path, tool
ref, and disabled raw/full-read flags before it can return `preview_completed`;
constructor validation alone is not trusted.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. M35 remains planned/provisional for Safe File
Review Workflow Contracts.
