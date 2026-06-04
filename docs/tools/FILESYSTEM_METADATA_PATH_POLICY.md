# Filesystem Metadata Path Policy

Status: active M32 documentation.
Current active baseline: **v0.37.0**

M32 filesystem metadata lookup is limited to server-owned safe roots. Callers
may provide a safe root ref, but they may not provide arbitrary root paths or
absolute filesystem paths.

Denied by policy:

- caller-selected arbitrary root paths.
- absolute paths.
- `..` path traversal.
- encoded traversal such as `%2e%2e`.
- home-directory paths such as `~/...`.
- Windows drive paths such as `C:/...`.
- unsafe path separators such as backslashes or doubled slashes.
- empty paths.
- hidden path segments such as `.env` or `.git`.
- secret-like path segments such as `secret`, `token`, `password`, or
  `api_key`.
- private-key-like path segments such as `id_rsa` or `private.key`.
- glob patterns.
- recursive traversal requests.
- directory listing requests.
- symlink following requests.
- filesystem mutation requests.
- metadata alias flags that attempt to enable raw content, text previews,
  content hashes, directory listing, recursion, symlink following,
  caller-selected roots, or mutation.

The evaluator revalidates metadata requests at the runtime boundary, including
model_copy-mutated fields. Constructor validation alone is not authority.

No path denial message should echo raw secrets, raw local absolute paths, or
unsafe caller-provided content.
