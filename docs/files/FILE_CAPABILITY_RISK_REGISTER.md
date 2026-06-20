# File Capability Risk Register

Status: active M34 documentation.
Current through: **v0.39.1**.

M34 adds no implementation capability. This register records the risks that
M35-M40 must mitigate before any broader file-review capability can be
accepted.

| Risk | Severity | Mitigation | Verifier/Gate Coverage | Next owner | Status |
| --- | --- | --- | --- | --- | --- |
| Raw-content leakage through packet/result fields | P0 | deny raw_content, full_file_content, unredacted_preview, raw absolute path, and secret-like metadata | documentation integrity, Foundation Gate, model_copy tests | M35 | open before implementation |
| Preview reconstruction through repeated calls | P1 | bind review packets to one bounded redacted preview result and avoid full-file output | M35 packet contract tests and M33 preview limits | M35 | open |
| Path traversal or encoded traversal | P0 | reuse M32/M33 relative path policy and safe-root refs only | existing M32/M33 path tests plus M35 packet provenance checks | M35 | mitigated for M33, must preserve |
| Symlink or safe-root bypass | P0 | deny symlinks and symlink safe roots before review packet creation | M33 gate and future M35 provenance checks | M35 | mitigated for M33, must preserve |
| Caller-selected arbitrary root | P0 | server-owned safe roots only; root_ref cannot carry arbitrary path authority | M33 gate and M35 boundary checks | M35 | mitigated for M33, must preserve |
| Redaction bypass | P0 | require redaction verification and redaction summary in review packets | M35 redaction verification tests | M35 | open |
| model_copy mutation bypass | P1 | evaluator boundaries revalidate current object fields, not constructor-only assumptions | M35 evaluator revalidation tests | M35 | open |
| approval_ref or approval_test_* misuse | P0 | approval refs are identifiers only; approval_test_* is never runtime authority | Approval Authority v2 tests and future file review gate | M35/M37 | mitigated generally, must preserve |
| UI copy/export/context-injection drift | P1 | M36 must omit copy-raw, export, approve-before-M37, inject, execute, upload, browse, file picker, and root selector controls | frontend safety verifier and browser smoke readiness | M36 | open |
| Backend route drift | P0 | OpenAPI path count must match the current generated contract; forbid raw-file/review/context/memory/tool execution routes | OpenAPI verifier and Foundation Gate | M35-M40 | active |
| Verifier brittleness | P2 | keep checks focused on active docs/source and exclude archive snapshots | documentation integrity tests | M34/M35 | active |

## Release Review Focus

Any future release that adds file-review contracts or UI must be reviewed for
raw-content ambiguity, approval authority ambiguity, context-injection
ambiguity, route drift, verifier weakness, and premature milestone leakage.
