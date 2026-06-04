# M31 to M32 Boundary

Status: active M32 documentation.
Current active baseline: **v0.36.1**

M31 is implemented/released as Real Tool Runtime Adapter, Single Safe No-Op
Tool. v0.35.1 hardens that boundary with allowlist validation, tool_ref/tool_name
consistency, dynamic dispatch denial, hidden side-effect denial, authority
boundary checks, evaluator revalidation, and replay protection.

v0.36.0 / M32 is implemented/released as Safe Local Filesystem Metadata Tool.
It adds exactly one metadata-only runtime tool:

```text
tool:filesystem_metadata.v1
```

M32 does not add arbitrary tool execution, raw file content reads, text
previews, content hashes, directory listing, recursive traversal, symlink
following, caller-selected roots, file mutation, shell/subprocess execution,
memory writes, network/model/provider calls, backend execution routes, Control
Center execute controls, dependencies, or production authority.

v0.37.4 supersedes the future roadmap and M34-M60 remain planned/provisional.
