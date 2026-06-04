# File Review Non-Goals

Status: active M35 contract documentation.
Current through: **v0.39.1**.

M35 does not add:

- Control Center file review UI.
- approval capture.
- approval persistence.
- raw file access.
- raw content.
- full-file reads.
- unredacted preview.
- context proposal.
- context injection.
- memory writes.
- export, download, or copy-raw behavior.
- execution, tool execution, action execution, or task execution.
- file writes, deletes, or filesystem mutation.
- backend raw-file, review-approval, context, memory, export, or execute
  routes.
- dependencies.
- production authority.

M35 also does not allow `review_packet_ref` alone to stand in for exact
approval binding. File/path mismatches are denied, including mismatched
`file_ref` or `safe_path_ref` values.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.
