# Ultimate AI Agent Version

Current active baseline: **v0.36.0**

v0.36.0 implements M32 Safe Tool Runtime Expansion as one safe local
filesystem metadata tool. It extends the governed tool runtime allowlist from
the deterministic no-op tool to exactly one metadata-only filesystem tool over
server-owned safe roots. It returns safe refs, existence, kind, size,
extension, and modified-time metadata only; denies arbitrary roots,
absolute/traversal/hidden/secret-like/glob paths, symlinks, raw content,
text previews, content hashes, directory listings, recursive traversal, and
filesystem mutation; and adds tests, static verification, documentation, and
Foundation Gate coverage. It adds no arbitrary tool execution, file content
read, file preview, content hashing, directory listing, recursive traversal,
symlink following, file mutation, shell execution, memory writes, network
calls, model/provider calls, backend execution routes, Control Center execute
controls, dependencies, M33 work, or production authority.
